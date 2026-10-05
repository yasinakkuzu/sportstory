import os
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
