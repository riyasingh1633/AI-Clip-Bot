import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


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

    return response.text
