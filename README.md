# AI Math Coach Mobile App (Camera + GPT-4o Vision)

This project describes how to build a **mobile app** where a student takes a photo of a math problem they are solving, the image is sent to the ChatGPT API, and the app returns:

1. A clear understanding of the full math problem
2. A step-by-step analysis of the student’s current work
3. Gentle hints for the **next step** (instead of just giving the final answer)

---

## 1) Product goal

Create a tutor-style experience for math students:

- Student opens app and takes/chooses a photo.
- AI reads handwritten or printed equations.
- AI explains what the question asks.
- AI checks where the student might be stuck.
- AI suggests the **next step** and asks the student to continue.

This keeps students learning actively instead of copying answers.

---

## 2) Recommended architecture

Use a **mobile client + secure backend** pattern.

```text
Mobile App (iOS/Android)
  └── uploads photo + optional student notes
        └── Backend API (Node.js/FastAPI)
              └── OpenAI Responses API (vision model)
                    └── returns structured coaching output
```

### Why backend is required

Do **not** call OpenAI directly from the app with a secret key.

- Protect API keys
- Add rate limiting and abuse controls
- Log requests safely for debugging
- Apply tutoring rules and safety checks before showing output

---

## 3) App flow

1. Student captures photo of notebook/worksheet.
2. App compresses image (for speed/cost).
3. App uploads image to backend.
4. Backend builds a tutoring prompt and calls OpenAI vision model.
5. Backend returns structured JSON:
   - `problem_summary`
   - `student_progress_assessment`
   - `next_hint`
   - `common_mistake_watchout`
   - `confidence`
6. App displays hints in stages:
   - Hint 1: small nudge
   - Hint 2: stronger guidance
   - Hint 3: fully worked solution (optional with guardian/teacher settings)

---

## 4) Prompting strategy (important)

Use a strict “coach, not answer-bot” system prompt.

### Example system prompt

```txt
You are a supportive math tutor for school students.
Rules:
- First identify the math topic and restate the problem clearly.
- Analyze the student's visible work before giving advice.
- Prefer hints and next steps over final answers.
- If the student asks for the final answer, still provide at least one learning hint first.
- Keep explanations short, clear, and age-appropriate.
- If the image is unreadable, ask for a clearer photo and explain how to retake it.
Return JSON with keys:
problem_summary, student_progress_assessment, next_hint, optional_full_solution, confidence.
```

---

## 5) Backend example (Node.js/Express)

> Note: endpoint/SDK signatures can evolve over time; check OpenAI docs for the exact current syntax.

```js
import express from "express";
import OpenAI from "openai";

const app = express();
app.use(express.json({ limit: "15mb" }));

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

app.post("/analyze-math", async (req, res) => {
  try {
    const { imageBase64, studentNote } = req.body;

    const response = await client.responses.create({
      model: "gpt-4o-mini",
      input: [
        {
          role: "system",
          content: [
            {
              type: "input_text",
              text:
                "You are a supportive math tutor. Give hints first, not just final answers. Return valid JSON only.",
            },
          ],
        },
        {
          role: "user",
          content: [
            {
              type: "input_text",
              text: `Student note: ${studentNote || "none"}`,
            },
            {
              type: "input_image",
              image_url: `data:image/jpeg;base64,${imageBase64}`,
            },
            {
              type: "input_text",
              text:
                "Analyze the problem and student work. Return JSON keys: problem_summary, student_progress_assessment, next_hint, optional_full_solution, confidence.",
            },
          ],
        },
      ],
    });

    res.json({ result: response.output_text });
  } catch (error) {
    res.status(500).json({ error: "analysis_failed", details: String(error) });
  }
});

app.listen(3000, () => console.log("API running on :3000"));
```

---

## 6) Mobile app example flow (React Native)

- Use `react-native-vision-camera` or Expo image picker/camera.
- Resize image before upload.
- Show loading state: “Analyzing your steps…”
- Render AI output in cards:
  - “What the problem is asking”
  - “How your work looks so far”
  - “Your next step”

Pseudo-client request:

```ts
const response = await fetch("https://your-backend.com/analyze-math", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ imageBase64, studentNote }),
});
```

---

## 7) Safety and quality checks

For student-focused education apps, add these controls:

- **Age-appropriate language** in responses
- **No harmful or insulting feedback**
- Detect low-quality images and request a retake
- Prevent hallucinated certainty:
  - include confidence score
  - say “I may be wrong” when confidence is low
- Keep tutoring style consistent (hint-first)

---

## 8) Cost/performance tips

- Resize/compress images to reasonable dimensions
- Cache repeated attempts of same image hash
- Use smaller vision model for first pass, larger model only when needed
- Add per-user/day quota limits

---

## 9) MVP checklist

- [ ] Camera capture and image preview
- [ ] Secure backend API with hidden OpenAI key
- [ ] Vision analysis endpoint
- [ ] Structured JSON output parser
- [ ] Hint-first UI
- [ ] Error handling for blurry/unreadable images
- [ ] Analytics (latency, cost, completion)

---

## 10) Next expansion ideas

- Multi-photo mode (question + student rough work)
- Voice mode: read hints aloud
- Whiteboard overlay: draw next algebra step on top of image
- Teacher dashboard to view class-level misconception trends

---

If you want, the next step can be a production-ready starter with:

- React Native (Expo) app
- Node.js backend
- Auth + rate limiting
- Complete prompt templates
- JSON schema validation for model output
