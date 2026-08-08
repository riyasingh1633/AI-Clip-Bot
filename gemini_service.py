import os
import json
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing in .env")

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-2.5-flash"


def find_best_clips(segments, max_clips=5):

    transcript = ""

    for i, segment in enumerate(segments):
        transcript += (
            f"[{segment['start']:.2f} - {segment['end']:.2f}] "
            f"{segment['text']}\n"
        )

    prompt = f"""
You are an expert viral short-form video editor.

Analyze this timestamped transcript and find the {max_clips} strongest
moments for Instagram Reels, YouTube Shorts and TikTok.

Choose moments that have:
- strong hooks
- emotional reactions
- arguments
- surprising statements
- controversial statements
- funny moments
- useful information
- storytelling
- tension
- reveals
- cliffhangers
- strong questions
- moments that make viewers want to continue watching

IMPORTANT:
Do NOT simply select consecutive 6-8 second sections.

Each clip should normally be between 15 and 60 seconds.

Start slightly before the important sentence when necessary.
End after the payoff/reaction.

Avoid:
- greetings
- silence
- boring explanations
- repeated sentences
- incomplete thoughts
- clips without a payoff

Return ONLY valid JSON.

Format:

[
  {{
    "start": 12.5,
    "end": 42.8,
    "reason": "Short explanation of why this moment is highly engaging",
    "hook": "Short hook/title for the clip"
  }}
]

Timestamped transcript:

{transcript}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    text = response.text.strip()

    # Remove markdown fences if Gemini adds them
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    # Find JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)

    if not match:
        raise ValueError("Gemini did not return valid clip JSON.")

    clips = json.loads(match.group(0))

    cleaned = []

    for clip in clips:

        try:
            start = float(clip["start"])
            end = float(clip["end"])

            if end <= start:
                continue

            duration = end - start

            # Keep clips in a useful short-form range
            if duration < 10:
                end = start + 15

            if end - start > 60:
                end = start + 60

            cleaned.append({
                "start": start,
                "end": end,
                "reason": str(clip.get("reason", "")),
                "hook": str(clip.get("hook", ""))
            })

        except (KeyError, ValueError, TypeError):
            continue

    return cleaned[:max_clips]
