#!/usr/bin/env python3
"""Generate speech audio files from Sarvam API for Indian languages and voices.

Supports voices like `shubh` and `ishita` with script input from CLI or file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

DEFAULT_TTS_URL = "https://api.sarvam.ai/text-to-speech"
DEFAULT_SAMPLE_RATE = 22050


def parse_script_map(raw: str) -> Dict[str, str]:
    """Parse a JSON object mapping language code to script text."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for --scripts-json: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("--scripts-json must be a JSON object (language -> text)")

    parsed: Dict[str, str] = {}
    for language, text in data.items():
        if not isinstance(language, str) or not isinstance(text, str):
            raise ValueError("All language keys and script values must be strings")
        parsed[language.strip()] = text.strip()

    if not parsed:
        raise ValueError("No scripts provided in --scripts-json")

    return parsed


def parse_script_file(path: Path) -> Dict[str, str]:
    """Parse `language|text` lines from file."""
    scripts: Dict[str, str] = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "|" not in stripped:
            raise ValueError(
                f"Invalid line {line_no} in {path}: expected 'language|text'"
            )
        language, text = stripped.split("|", 1)
        language = language.strip()
        text = text.strip()
        if not language or not text:
            raise ValueError(
                f"Invalid line {line_no} in {path}: language/text must be non-empty"
            )
        scripts[language] = text

    if not scripts:
        raise ValueError(f"No scripts found in {path}")

    return scripts


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip().lower())
    return slug.strip("_") or "audio"


def build_payload(text: str, language: str, speaker: str, sample_rate: int) -> Dict[str, object]:
    return {
        "text": text,
        "target_language_code": language,
        "speaker": speaker,
        "sample_rate": sample_rate,
    }


def save_audio_from_response(
    response_json: Dict[str, object], output_path: Path
) -> None:
    """Save audio content from Sarvam response.

    Expected key `audios` as list with first element base64-encoded audio,
    or `audio` containing base64.
    """
    import base64

    b64_audio = None

    if isinstance(response_json.get("audios"), list) and response_json["audios"]:
        b64_audio = response_json["audios"][0]
    elif isinstance(response_json.get("audio"), str):
        b64_audio = response_json["audio"]

    if not isinstance(b64_audio, str):
        raise ValueError(
            "Could not find audio data in API response. Expected 'audios[0]' or 'audio'."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(b64_audio))


def synthesize(
    api_key: str,
    tts_url: str,
    scripts_by_language: Dict[str, str],
    speakers: Iterable[str],
    output_dir: Path,
    sample_rate: int,
    audio_ext: str,
) -> List[Tuple[str, str, Path]]:
    results: List[Tuple[str, str, Path]] = []

    for language, text in scripts_by_language.items():
        for speaker in speakers:
            payload = build_payload(
                text=text,
                language=language,
                speaker=speaker,
                sample_rate=sample_rate,
            )
            body = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                tts_url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "api-subscription-key": api_key,
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(request) as response:
                    raw = response.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                details = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"Sarvam API request failed for language={language}, speaker={speaker}. "
                    f"HTTP {exc.code}: {details}"
                ) from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"Network error calling Sarvam API: {exc}") from exc

            try:
                response_json = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON response from Sarvam API: {raw[:200]}") from exc

            filename = f"{slugify(language)}_{slugify(speaker)}.{audio_ext.lstrip('.')}"
            output_path = output_dir / filename
            save_audio_from_response(response_json, output_path)
            results.append((language, speaker, output_path))

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create audio in different Indian languages using Sarvam TTS voices "
            "(e.g., shubh and ishita)."
        )
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("SARVAM_API_KEY"),
        help="Sarvam API key. Defaults to SARVAM_API_KEY environment variable.",
    )
    parser.add_argument(
        "--tts-url",
        default=os.getenv("SARVAM_TTS_URL", DEFAULT_TTS_URL),
        help=f"TTS endpoint URL (default: {DEFAULT_TTS_URL}).",
    )
    parser.add_argument(
        "--scripts-json",
        help='JSON object of language->text. Example: {"hi-IN":"नमस्ते", "ta-IN":"வணக்கம்"}',
    )
    parser.add_argument(
        "--scripts-file",
        type=Path,
        help="Path to UTF-8 file with lines in format language|text.",
    )
    parser.add_argument(
        "--speakers",
        default="shubh,ishita",
        help="Comma-separated speaker names (default: shubh,ishita).",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        help=f"Audio sample rate sent to API (default: {DEFAULT_SAMPLE_RATE}).",
    )
    parser.add_argument(
        "--audio-ext",
        default="wav",
        help="Output file extension (default: wav).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output_audio"),
        help="Directory to save generated audio files (default: output_audio).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.api_key:
        print("Error: Provide --api-key or set SARVAM_API_KEY", file=sys.stderr)
        return 1

    if not args.scripts_json and not args.scripts_file:
        print(
            "Error: Provide either --scripts-json or --scripts-file",
            file=sys.stderr,
        )
        return 1

    try:
        scripts: Dict[str, str] = {}
        if args.scripts_json:
            scripts.update(parse_script_map(args.scripts_json))
        if args.scripts_file:
            scripts.update(parse_script_file(args.scripts_file))

        speakers = [item.strip() for item in args.speakers.split(",") if item.strip()]
        if not speakers:
            raise ValueError("No valid speakers provided")

        results = synthesize(
            api_key=args.api_key,
            tts_url=args.tts_url,
            scripts_by_language=scripts,
            speakers=speakers,
            output_dir=args.output_dir,
            sample_rate=args.sample_rate,
            audio_ext=args.audio_ext,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Generated audio files:")
    for language, speaker, path in results:
        print(f" - {language} / {speaker}: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
