import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
topic = "Leeds United: Borrowed Millions, Goldfish Bowls, and Football's Most Infamous Meltdown"

prompt = f"""
You are a senior investigative sports finance documentary writer for 'SportStory' channel.
Write a gripping 5-scene YouTube Shorts documentary script about: "{topic}".
REQUIREMENTS:
- Exactly 5 scenes.
- Total narration must be 70 to 95 words (approx 35-45 seconds of natural speech).
- Scene 1 (Hook): Shocking opening with club name and contrast.
- Scene 2 (The Gamble): Exact figures, boardroom recklessness, loans.
- Scene 3 (The Crash): What triggered the collapse.
- Scene 4 (Rock Bottom): Relegation, asset sales, disaster.
- Scene 5 (Climax / Question): Provocative question for comments.
- Both English and Turkish must be provided for every scene.

OUTPUT ONLY VALID JSON with schema:
{{
  "title_en": "YouTube Title with emojis and #shorts #football",
  "description_en": "Full English YouTube Description (3-4 sentences) with hashtags",
  "tags_en": ["shorts", "football", "soccer", "finance", "leeds united"],
  "scenes": [
    {{
      "scene_idx": 1,
      "text_en": "English spoken text",
      "text_tr": "Turkish spoken text",
      "visual_prompt": "cinematic football",
      "is_hook": true,
      "is_cta": false
    }}
  ]
}}
"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={key}"
res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
print("Status:", res.status_code)
if res.status_code == 200:
    raw = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    data = json.loads(raw.strip())
    print("Title EN:", data.get("title_en"))
    print("Description EN:", data.get("description_en")[:100] + "...")
    print("Tags EN:", data.get("tags_en"))
    print("\nScenes:")
    for s in data.get("scenes", []):
        print(f"[{s['scene_idx']}] EN ({len(s['text_en'].split())} w): {s['text_en']}")
else:
    print("Error:", res.status_code, res.text)
