import os
import re

print("==================================================")
print("🌍 SPORTSTORY: %100 GLOBAL ENGLISH & ZERO-PAUSE VOICE")
print("==================================================")

print("1/4: Senarist Ajan SADECE İNGİLİZCE düşünmeye programlanıyor...")
scriptweaver_code = """import os
import json
import requests
from dotenv import load_dotenv
from engine.schemas import AutoScriptPayload, AutoScenePlan

load_dotenv()

class ScriptWeaverAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

    def generate_script(self, topic: str, short_id: str) -> AutoScriptPayload:
        print(f"[ScriptWeaver] ✍️ Generating 100% ENGLISH FAST-PACED script for: {topic}...")
        
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return self._create_dummy_script(topic, short_id)
            
        system_prompt = "You are the screenwriter of a viral YouTube Shorts channel. Write a 5-scene script. UNBREAKABLE RULES: 1. You MUST mention who or which team the story is about in the VERY FIRST SCENE. 2. Exactly 5 scenes. 3. NEVER write long sentences. Each scene must be MAXIMUM 3-5 WORDS (Fast, punchy, brain-rot style). 4. NEVER use a Call to Action (CTA) in scenes 1,2,3,4. 5. The output MUST be ONLY a valid JSON written ENTIRELY IN ENGLISH. SCHEMA: {\\"scenes\\": [{\\"scene_idx\\": 1, \\"text_tr\\": \\"-\\", \\"text_en\\": \\"English text here\\", \\"visual_prompt\\": \\"gameplay\\", \\"is_hook\\": true, \\"is_cta\\": false}]}"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": f"{system_prompt}\\n\\nTopic: {topic}"}]}]}
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                if raw_text.startswith("```json"): raw_text = raw_text[7:]
                if raw_text.startswith("```"): raw_text = raw_text[3:]
                if raw_text.endswith("```"): raw_text = raw_text[:-3]
                script_data = json.loads(raw_text.strip())
                scenes = [AutoScenePlan(**s) for s in script_data.get("scenes", [])]
                return AutoScriptPayload(id=short_id, topic=topic, scenes=scenes)
            else:
                return self._create_dummy_script(topic, short_id)
        except Exception:
            return self._create_dummy_script(topic, short_id)

    def _create_dummy_script(self, topic: str, short_id: str) -> AutoScriptPayload:
        return AutoScriptPayload(id=short_id, topic=topic, scenes=[
            AutoScenePlan(scene_idx=1, text_tr="-", text_en="The biggest football scandal.", visual_prompt="gameplay", is_hook=True, is_cta=False),
            AutoScenePlan(scene_idx=2, text_tr="-", text_en="Millions vanished overnight.", visual_prompt="gameplay", is_hook=False, is_cta=False),
            AutoScenePlan(scene_idx=3, text_tr="-", text_en="The empire collapsed completely.", visual_prompt="gameplay", is_hook=False, is_cta=False),
            AutoScenePlan(scene_idx=4, text_tr="-", text_en="UEFA was totally shocked.", visual_prompt="gameplay", is_hook=False, is_cta=False),
            AutoScenePlan(scene_idx=5, text_tr="-", text_en="Is it fair? Comment below!", visual_prompt="gameplay", is_hook=False, is_cta=True)
        ])
"""
with open("engine/agents/scriptweaver_agent.py", "w", encoding="utf-8") as f:
    f.write(scriptweaver_code)

print("2/4: Ses Motorundan TÜM DURAKSAMALAR (Noktalamalar) Siliniyor...")
audio_path = "engine/workers/audio_worker.py"
with open(audio_path, "r", encoding="utf-8") as f:
    audio = f.read()

new_soften = """def soften_tts_punctuation(script: str) -> str:
    # Kesintisiz (Zero-Gap) okuma icin tum duraksama isaretleri siliniyor
    s = script.replace(";", " ").replace("!", " ").replace("...", " ").replace(".", " ").replace(",", " ").replace("?", " ").replace("-", " ")
    import re
    return re.sub(r'\\s+', ' ', s).strip()"""

audio = re.sub(r'def soften_tts_punctuation\(.*?\).*?return s', new_soften, audio, flags=re.DOTALL)
with open(audio_path, "w", encoding="utf-8") as f:
    f.write(audio)

print("3/4: Orkestratör İngilizce 'Steffan' Sesine ve +25% Hıza Ayarlanıyor...")
gen_path = "generate_short.py"
with open(gen_path, "r", encoding="utf-8") as f:
    gen = f.read()

# Eski metin birleştiriciyi sadece text_en alacak şekilde zorla
gen = re.sub(r'texts\s*=\s*\[.*?for s in script.scenes\]', 'texts = [s.text_en for s in script.scenes]', gen)

# Ses fonksiyonunu Steffan ve +25% hıza zorla
gen = re.sub(
    r'self\.audio_worker\.generate_voiceover\(.*?\)', 
    'self.audio_worker.generate_voiceover(script=full_text, target_path=str(raw_voice_path), language="en", voice="en-US-SteffanNeural", rate="+25%")', 
    gen
)
# Default dil en oldu
gen = gen.replace("default='tr'", "default='en'")
with open(gen_path, "w", encoding="utf-8") as f:
    f.write(gen)

print("4/4: YouTube SEO Bilgileri İngilizceye Kilitleniyor...")
dep_path = "engine/agents/auto_deploy_agent.py"
with open(dep_path, "r", encoding="utf-8") as f:
    dep = f.read()

dep = re.sub(r'title\s*=\s*".*?".*', 'title = "Shocking Football Scandal �� #shorts #football"', dep)
dep = re.sub(r'description\s*=\s*".*?".*', 'description = "What do you think? Drop your thoughts below! 👇\\n\\n#football #soccer #scandal"', dep)
dep = re.sub(r'tags\s*=\s*\[.*?\].*', 'tags = ["football", "soccer", "shorts", "scandal"]', dep)

with open(dep_path, "w", encoding="utf-8") as f:
    f.write(dep)

print("\n✅ SİSTEM BAŞARIYLA %100 İNGİLİZCE (GLOBAL) VE AKICI SESE GEÇİRİLDİ!")
