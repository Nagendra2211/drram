# drram

## Generate audio using Sarvam API (Shubh + Ishita)

This repo now includes `sarvam_tts.py` to generate audio from input scripts in different Indian languages using Sarvam TTS voices like **shubh** and **ishita**.

### 1) Set API key

```bash
export SARVAM_API_KEY="your_api_key_here"
```

### 2) Provide scripts

You can provide scripts either as JSON or as a file.

#### Option A: JSON input

```bash
python3 sarvam_tts.py \
  --scripts-json '{"hi-IN":"नमस्ते! यह एक डेमो है।","ta-IN":"வணக்கம்! இது ஒரு டெமோ."}'
```

#### Option B: File input (`language|text`)

Create `scripts.txt`:

```txt
hi-IN|नमस्ते! यह हिंदी स्क्रिप्ट है।
bn-IN|নমস্কার! এটি বাংলা স্ক্রিপ্ট।
mr-IN|नमस्कार! ही मराठी स्क्रिप्ट आहे.
```

Run:

```bash
python3 sarvam_tts.py --scripts-file scripts.txt
```

### 3) Choose speakers

By default it uses both speakers:

- `shubh`
- `ishita`

Override with:

```bash
python3 sarvam_tts.py --scripts-file scripts.txt --speakers "shubh,ishita"
```

### 4) Output

Generated files are saved in `output_audio/` by default, one file per `(language, speaker)`.

Example:

- `output_audio/hi-in_shubh.wav`
- `output_audio/hi-in_ishita.wav`

### Optional flags

- `--output-dir custom_folder`
- `--audio-ext mp3`
- `--sample-rate 24000`
- `--tts-url https://api.sarvam.ai/text-to-speech`

### Notes

- Keep UTF-8 encoding in script files for Indian language text.
- If Sarvam changes payload/response format, adjust `build_payload()` / `save_audio_from_response()` in `sarvam_tts.py`.
