"""
PublisherWorker: YouTube Data API v3 Yükleme Motoru & SEO Metadata JSON Exporter.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials
except ImportError:
    build = None

logger = logging.getLogger("AntigravityEngine.PublisherWorker")


class PublisherWorker:
    """YouTube Data API v3 Yükleme Motoru & SEO Metadata Paketi"""

    def __init__(self, token_file: str = "token.json"):
        self.token_file = token_file

    def export_seo_metadata(
        self,
        video_id: str,
        title: str,
        description: str,
        tags: List[str],
        pinned_comment: str,
        output_dir: str,
        language: str = "tr"
    ) -> str:
        """Her video için YouTube API veya manuel yükleme uyumlu hazır JSON metadata paketi oluşturur."""
        suffix = "_en" if language == "en" else ""
        out_path = Path(output_dir) / f"{video_id.lower()}{suffix}_metadata.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        extra_tags = ["shorts", "football", "soccer", "footballfinance"] if language == "en" else ["shorts", "futbol", "sporfinansı", "transfer"]
        desc_suffix = "\n\n#shorts #football #soccer" if language == "en" else "\n\n#shorts #futbol #spor"

        payload = {
            "video_id": f"{video_id.upper()}{suffix.upper()}",
            "snippet": {
                "title": title[:100],
                "description": f"{description}{desc_suffix}",
                "tags": tags + extra_tags,
                "categoryId": "17", # Spor Kategorisi
                "defaultLanguage": language,
                "defaultAudioLanguage": language
            },
            "status": {
                "privacyStatus": "private", # Güvenlik gereği ilk yükleme gizli/taslak
                "selfDeclaredMadeForKids": False
            },
            "community": {
                "pinned_comment": pinned_comment
            }
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        logger.info(f"📋 YouTube SEO & Dağıtım Paketi Kaydedildi: {out_path.name}")
        return str(out_path)

    def upload_short(self, video_path: str, title: str, description: str, tags: List[str]) -> str:
        """YouTube Data API v3 ile videoyu yükler."""
        if not os.path.exists(self.token_file) or build is None:
            logger.info("ℹ️ YouTube token.json tanımlanmadı. Video yerel olarak hazırlandı, _metadata.json oluşturuldu.")
            return "LOCAL_READY_FOR_UPLOAD"

        try:
            creds = Credentials.from_authorized_user_file(self.token_file, ["https://www.googleapis.com/auth/youtube.upload"])
            youtube = build("youtube", "v3", credentials=creds)

            body = {
                "snippet": {
                    "title": title[:100],
                    "description": f"{description}\n\n#shorts #futbol",
                    "tags": tags + ["shorts", "spor"],
                    "categoryId": "17"
                },
                "status": {
                    "privacyStatus": "private",
                    "selfDeclaredMadeForKids": False
                }
            }
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
            req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

            response = None
            while response is None:
                status, response = req.next_chunk()
                if status:
                    logger.info(f"YouTube Yükleme İlerlemesi: %{int(status.progress() * 100)}")

            vid_id = response.get("id", "UPLOADED")
            logger.info(f"🎉 Video Başarıyla YouTube'a Yüklendi! Video ID: {vid_id}")
            return vid_id

        except Exception as e:
            logger.error(f"YouTube Yükleme Hatası: {e}")
            return f"UPLOAD_ERROR: {e}"
