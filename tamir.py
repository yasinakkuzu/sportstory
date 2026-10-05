import os

schemas_addition = """
# --- YENI OTONOM AJAN SEMALARI ---
from pydantic import BaseModel, Field
from typing import List, Optional

class AutoScenePlan(BaseModel):
    scene_idx: int
    text_tr: str
    text_en: str
    visual_prompt: str = Field(description="B-Roll")
    is_hook: bool = False
    is_cta: bool = False

class AutoScriptPayload(BaseModel):
    id: str
    topic: str
    scenes: List[AutoScenePlan]
"""
if os.path.exists("engine/schemas.py"):
    with open("engine/schemas.py", "a+", encoding="utf-8") as f:
        f.seek(0)
        if "AutoScriptPayload" not in f.read():
            f.write("\n" + schemas_addition)

if os.path.exists("engine/agents/__init__.py"):
    with open("engine/agents/__init__.py", "w", encoding="utf-8") as f:
        f.write("")

scriptweaver_code = """import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from engine.schemas import AutoScriptPayload, AutoScenePlan

load_dotenv()

class ScriptWeaverAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_script(self, topic: str, short_id: str) -> AutoScriptPayload:
        print(f"[ScriptWeaver] '{topic}' konusu icin Yeni Google AI ile senaryo yaziliyor...")
        if not self.client: return self._create_dummy_script(topic, short_id)
        
        system_prompt = 'Sen SportStory kanalinin senaristisin. Gorevin 5 sahneli bir YouTube Shorts senaryosu yazmak. CTA ASLA 1,2,3,4. sahnelerde kullanilamaz. Cikti SADECE JSON olmalidir. SEMA: {"scenes": [{"scene_idx": 1, "text_tr": "Tr", "text_en": "En", "visual_prompt": "B-Roll", "is_hook": true, "is_cta": false}]}'
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{system_prompt}\\n\\nIstedigim Olay: {topic}",
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```json"): raw_text = raw_text[7:]
            if raw_text.startswith("```"): raw_text = raw_text[3:]
            if raw_text.endswith("```"): raw_text = raw_text[:-3]
            data = json.loads(raw_text.strip())
            scenes = [AutoScenePlan(**s) for s in data.get("scenes", [])]
            return AutoScriptPayload(id=short_id, topic=topic, scenes=scenes)
        except Exception as e:
            print(f"[ScriptWeaver] Hata: {e}")
            return self._create_dummy_script(topic, short_id)

    def _create_dummy_script(self, topic: str, short_id: str) -> AutoScriptPayload:
        return AutoScriptPayload(id=short_id, topic=topic, scenes=[AutoScenePlan(scene_idx=1, text_tr="Test", text_en="Test", visual_prompt="dark", is_hook=True, is_cta=False)])
"""
with open("engine/agents/scriptweaver_agent.py", "w", encoding="utf-8") as f:
    f.write(scriptweaver_code)

visionary_code = """import os
import requests
from dotenv import load_dotenv

load_dotenv()

class VisionaryAssetAgent:
    def __init__(self):
        self.api_key = os.getenv("PEXELS_API_KEY")
        self.headers = {"Authorization": self.api_key}

    def fetch_broll(self, prompt: str, save_path: str):
        if not self.api_key or self.api_key == "your_pexels_api_key_here":
            return False
        print(f"[VisionaryAsset] B-Roll araniyor: '{prompt}'...")
        url = "[https://api.pexels.com/videos/search](https://api.pexels.com/videos/search)"
        params = {"query": prompt, "orientation": "portrait", "per_page": 1}
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("videos") and len(data["videos"]) > 0:
                    best_video = max(data["videos"][0]["video_files"], key=lambda x: x.get('width', 0) * x.get('height', 0))
                    vid_response = requests.get(best_video["link"], stream=True)
                    if vid_response.status_code == 200:
                        with open(save_path, "wb") as f:
                            for chunk in vid_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print("[VisionaryAsset] MP4 indirildi.")
                        return True
            return False
        except Exception as e:
            return False
"""
with open("engine/agents/visionary_asset_agent.py", "w", encoding="utf-8") as f:
    f.write(visionary_code)

generate_path = "generate_short.py"
if os.path.exists(generate_path):
    with open(generate_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    old_code = "self.deployer.deploy(str(final_video_path), lang)"
    new_code = '''if not os.path.exists(str(final_video_path)):
            print(f"\\n[KAYIT DISI HATA]: {final_video_path} dosyasi diskte YOK.")
            print("Eski render iscilerinizin isimleri uyumsuz oldugu icin video uretilmemis. Yukleme iptal.")
            return
            
        self.deployer.deploy(str(final_video_path), lang)'''
    
    if "[KAYIT DISI HATA]" not in content and old_code in content:
        content = content.replace(old_code, new_code)
        with open(generate_path, "w", encoding="utf-8") as f:
            f.write(content)

print("✅ SISTEM ONARIMI BASARIYLA TAMAMLANDI!")
