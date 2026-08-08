import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing in .env")

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-2.5-flash"


def find_best_clips(
    segments,
    max_clips=5,
    target_duration=30,
    style="viral"
):

    if not segments:
        raise ValueError("No Whisper segments received.")

    # Build timestamped transcript
    transcript = ""

    for segment in segments:
        transcript += (
            f"[{segment['start']:.2f} - "
            f"{segment['end']:.2f}] "
            f"{segment['text']}\n"
        )

    style_instructions = {
        "viral": """
Prioritize strong hooks, shocking statements, conflict,
surprising moments, curiosity gaps, strong reactions,
controversial opinions and moments likely to retain viewers.
""",

        "emotional": """
Prioritize emotional conversations, vulnerable moments,
family, relationships, powerful reactions and emotional payoffs.
""",

        "funny": """
Prioritize jokes, funny reactions, unexpected moments,
awkward situations and entertaining dialogue.
""",

        "storytelling": """
Prioritize complete mini-stories with a setup, development
and satisfying payoff.
""",

        "best": """
Choose the strongest and most engaging moments overall.
""",
    }

    style_instruction = style_instructions.get(
        style,
        style_instructions["viral"]
    )

    prompt = f"""
You are an expert short-form video editor.

Analyze the timestamped transcript below.

Find the BEST {max_clips} moments for short-form video.

TARGET CLIP DURATION:
Approximately {target_duration} seconds.

STYLE:
{style_instruction}

IMPORTANT RULES:

1. Do NOT simply divide the video into equal chunks.
2. Select moments based on actual content quality.
3. Each clip should have a strong beginning.
4. Prefer a complete thought or conversation.
5. Include the payoff/reaction when possible.
6. Avoid greetings and introductions.
7. Avoid silence.
8. Avoid repetitive dialogue.
9. Avoid incomplete sentences.
10. Avoid clips with no interesting event.
11. Do not invent timestamps.
12. Use ONLY timestamps present in the transcript.
13. Clips may be slightly shorter or longer than the target duration
    if that produces a much better moment.
14. Never make a clip longer than 60 seconds.
15. Try to avoid overlapping clips.

For each clip return:

start:
The starting timestamp in seconds.

end:
The ending timestamp in seconds.

reason:
Why this is a strong short-form moment.

hook:
A short attention-grabbing title/hook.

Return ONLY JSON.

Timestamped transcript:

{transcript}
"""

    schema = {
        "type": "object",
        "properties": {
            "clips": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "number"
                        },
                        "end": {
                            "type": "number"
                        },
                        "reason": {
                            "type": "string"
                        },
                        "hook": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "start",
                        "end",
                        "reason",
                        "hook"
                    ]
                }
            }
        },
        "required": ["clips"]
    }

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        )
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Gemini returned invalid JSON: {e}"
        )

    clips = data.get("clips", [])

    if not isinstance(clips, list):
        raise RuntimeError(
            "Gemini response does not contain a clips list."
        )

    # -----------------------------------------
    # Determine actual transcript boundaries
    # -----------------------------------------

    video_end = max(
        float(segment["end"])
        for segment in segments
    )

    cleaned = []

    for clip in clips:

        try:

            start = float(clip["start"])
            end = float(clip["end"])

            start = max(0.0, start)
            end = min(video_end, end)

            if end <= start:
                continue

            duration = end - start

            # If Gemini selected a very short moment,
            # try to extend it toward requested duration.
            if duration < target_duration * 0.60:

                desired_end = start + target_duration

                if desired_end <= video_end:
                    end = desired_end

            # Never exceed 60 seconds
            if end - start > 60:
                end = start + 60

            end = min(end, video_end)

            if end - start < 3:
                continue

            cleaned.append({
                "start":
