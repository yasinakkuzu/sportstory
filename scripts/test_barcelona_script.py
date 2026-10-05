import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")
topic = "FC Barcelona: A Reckless Empires Descent into Billion-Euro Ruin"

prompt = f"""
You are a senior investigative sports finance documentary writer for 'SportStory'.
Write a gripping, COMPLETE 5-scene YouTube Shorts documentary script about: "{topic}".

REQUIREMENTS:
- Exactly 5 scenes.
- Total narration across all 5 scenes MUST be between 70 and 95 words (approx. 32-40 seconds of natural speech).
- The story must be 100% COMPLETE with a clear narrative arc:
  * Scene 1 (Hook): Name the club and the mind-blowing contrast (glory vs hidden disaster).
  * Scene 2 (The Waste): Specific transfer wastes (Coutinho, Griezmann), astronomical wage bill, and real numbers.
  * Scene 3 (The Crash): Debt exploding past 1.3 Billion euros and inability to meet wage caps.
  * Scene 4 (The Consequence): Lionel Messi leaving in tears and mortgaging future TV rights with economic levers.
  * Scene 5 (Climax/Debate): Provocative question for comments.
- Do NOT make it short or 3-word fragments. Write natural, dramatic, high-energy documentary sentences (14-18 words per scene).
- Language: English narration ('text_en'). Provide Turkish translation ('text_tr').

OUTPUT ONLY VALID JSON with schema:
{{
  "title_en": "Sensational YouTube Title with emojis and #shorts #football",
  "description_en": "Compelling 3-4 sentence English description with context and hashtags",
  "tags_en": ["shorts", "football", "soccer", "barcelona", "messi", "sports finance"],
  "scenes": [
    {{
      "scene_idx": 1,
      "text_en": "English spoken voiceover",
      "text_tr": "Turkish spoken voiceover",
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
    if raw.startswith("```json"): raw = raw[7:]
    if raw.startswith("```"): raw = raw[3:]
    if raw.endswith("```"): raw = raw[:-3]
    d = json.loads(raw.strip())
    print("Title:", d.get("title_en"))
    print("Description:", d.get("description_en"))
    total_w = 0
    for s in d.get("scenes", []):
        w_cnt = len(s["text_en"].split())
        total_w += w_cnt
        print(f"  [{s['scene_idx']}] ({w_cnt} words): {s['text_en']}")
    print("Total words:", total_w)
else:
    print("Error:", res.status_code, res.text)
