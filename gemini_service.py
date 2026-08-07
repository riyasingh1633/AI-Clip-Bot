import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def find_best_clips(transcript):
    prompt = f"""
You are an expert viral short-form video editor.

Analyze the transcript below.

Choose the BEST 5 moments that would perform well as YouTube Shorts, Instagram Reels, or TikTok.

Return ONLY valid JSON.

Format:

[
  {{
    "start":"00:00:00",
    "end":"00:00:30",
    "reason":"Why this clip is viral"
  }}
]

Transcript:

{transcript}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    text = response.text.strip()

    # Remove Markdown code fences if Gemini wraps JSON
    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini returned invalid JSON:\n{text}"
        ) from e
