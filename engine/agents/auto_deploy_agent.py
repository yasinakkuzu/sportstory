import os
import pickle
import json
from typing import Optional
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class AutoDeployAgent:
    def __init__(self, lang: str = "en"):
        # YouTube yükleme ve kanal doğrulama yetkileri (token_tr.pickle ve token_en.pickle destekli)
        self.scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly"
        ]
        self.client_secrets_file = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
        self.lang = lang
        self.credentials_file = self.resolve_token_file(lang)

    def resolve_token_file(self, lang: Optional[str] = None) -> str:
        """Kanal diline göre (TR veya EN) ilgili token dosyasını belirler."""
        l = (lang or self.lang or "en").lower()
        lang_token = f"token_{l}.pickle"
        if os.path.exists(lang_token):
            return lang_token
        # Sadece Global İngilizce için geriye dönük uyumluluk (token_en yoksa token.pickle kullan)
        if l == "en" and os.path.exists("token.pickle"):
            return "token.pickle"
        return lang_token

    def authenticate(self, lang: Optional[str] = None):
        target_token_file = self.resolve_token_file(lang) if lang else self.credentials_file
        creds = None
        # Daha önce giriş yapılmışsa token'ı yükle
        if os.path.exists(target_token_file):
            with open(target_token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Token yoksa veya süresi dolmuşsa yeniden giriş yap
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                import requests
                from requests.adapters import HTTPAdapter
                session = requests.Session()
                session.mount("https://", HTTPAdapter(max_retries=3))
                req = Request(session=session)
                creds.refresh(req)
                with open(target_token_file, 'wb') as token:
                    pickle.dump(creds, token)
            else:
                if not os.path.exists(self.client_secrets_file):
                    print(f"\n[AutoDeploy] ⚠️ HATA: '{self.client_secrets_file}' bulunamadı!")
                    print("[AutoDeploy] Lütfen Google Cloud'dan 'Masaüstü Uygulaması' (Desktop App) JSON dosyasını indirip ana dizine koyun.")
                    return None
                
                lang_label = "TÜRKÇE KANAL" if (lang or self.lang) == "tr" else "GLOBAL KANAL"
                print(f"\n[AutoDeploy] 🔐 YOUTUBE {lang_label} İÇİN İLK GİRİŞ İZNİ GEREKİYOR...")
                print(f"[AutoDeploy] 🌐 Tarayıcınız açılıyor. Lütfen ilgili {lang_label} hesabınızı/kanalınızı seçin...")
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, self.scopes)
                creds = flow.run_local_server(port=8080, open_browser=True)
            
            # Başarılı girişten sonra yetkiyi kaydet (bir daha sormaması için)
            with open(target_token_file, 'wb') as token:
                pickle.dump(creds, token)
            print(f"[AutoDeploy] 💾 Yetki başarıyla kaydedildi: {target_token_file}")
                
        return build("youtube", "v3", credentials=creds)

    def delete_video(self, video_id: str) -> bool:
        youtube = self.authenticate()
        if not youtube:
            return False
        try:
            youtube.videos().delete(id=video_id).execute()
            print(f"[AutoDeploy] 🗑️ Video başarıyla silindi: {video_id}")
            return True
        except Exception as e:
            print(f"[AutoDeploy] ❌ Video silinirken hata: {e}")
            return False

    def update_video_title(self, video_id: str, new_title: str) -> bool:
        youtube = self.authenticate()
        if not youtube:
            return False
        try:
            res = youtube.videos().list(id=video_id, part="snippet").execute()
            items = res.get("items", [])
            if not items:
                print(f"[AutoDeploy] ⚠️ Video bulunamadı: {video_id}")
                return False
            snippet = items[0]["snippet"]
            old_title = snippet.get("title", "")
            snippet["title"] = new_title
            youtube.videos().update(
                part="snippet",
                body={"id": video_id, "snippet": snippet}
            ).execute()
            print(f"[AutoDeploy] ✏️ Başlık güncellendi ({video_id}):\n   Eski: {old_title}\n   Yeni: {new_title}")
            return True
        except Exception as e:
            print(f"[AutoDeploy] ❌ Başlık güncellenirken hata: {e}")
            return False

    def deploy(self, video_path: str, lang: str, metadata_path: Optional[str] = None, publish_at: Optional[str] = None) -> Optional[str]:
        print(f"\n[AutoDeploy] 🚀 Yükleme başlatılıyor: {video_path} (Kanal Dili: {lang.upper()})")
        youtube = self.authenticate(lang=lang)
        if not youtube:
            print("[AutoDeploy] ❌ YouTube API bağlantısı sağlanamadı. Yükleme iptal.")
            return None

        p_vid = Path(video_path)
        video_dir = p_vid.parent
        
        # SEO ve Etiket ayarları (Metadata yoksa default kullanılır)
        title = "Futbolda Büyük Skandal 🤯 #shorts #futbol" if lang == 'tr' else "Shocking Football Scandal 🤯 #shorts #football"
        description = "Sen bu konu hakkında ne düşünüyorsun? Yorumlara yaz! 👇\n\n#futbol #transfer #skandal" if lang == 'tr' else "What do you think? Drop your thoughts below! 👇\n\n#football #soccer #scandal"
        tags = ["futbol", "spor", "shorts", "skandal"] if lang == 'tr' else ["football", "soccer", "shorts", "scandal"]

        target_meta_file = None
        if metadata_path and os.path.exists(metadata_path):
            target_meta_file = metadata_path
        else:
            stem = p_vid.stem.lower()
            clean_stem = stem.replace("_final_short", "").replace("final_short_", "")
            candidates = [
                video_dir / f"{clean_stem}_metadata.json",
                video_dir / f"{clean_stem}_{lang}_metadata.json",
            ]
            for cand in candidates:
                if cand.exists():
                    target_meta_file = str(cand)
                    break

        if target_meta_file and os.path.exists(target_meta_file):
            try:
                with open(target_meta_file, "r", encoding="utf-8") as mj:
                    mdata = json.load(mj)
                    snippet = mdata.get("snippet", {})
                    candidate_title = snippet.get("title") or mdata.get("title", "")
                    candidate_desc = snippet.get("description") or mdata.get("description", "")
                    
                    if lang == 'en' and any(c in candidate_title for c in "çÇğĞıİöÖşŞüÜ"):
                        print(f"[AutoDeploy] ⚠️ UYARI: Metadata dosyasında Türkçe tespit edildi, temizleniyor.")
                        candidate_title = ""

                    if candidate_title:
                        title = candidate_title
                    if candidate_desc:
                        description = candidate_desc
                    tags = snippet.get("tags") or mdata.get("tags", tags)
                print(f"[AutoDeploy] 📄 Metadata başarıyla okundu: {Path(target_meta_file).name}")
            except Exception as e:
                print(f"[AutoDeploy] ⚠️ Metadata okuma hatası: {e}")

        print(f"[AutoDeploy] 📝 Başlık: {title}")

        # ContentGuard Başlık ve Mükerrerlik Denetimi (Yükleme Öncesi Kesin Engel)
        try:
            from engine.guards.content_guard import get_content_guard
            guard = get_content_guard()
            is_dup, reason, sim = guard.check_title_duplicate(title, threshold=0.80)
            if is_dup:
                print(f"\n[AutoDeploy] 🛑 RED: Bu başlık zaten kanalda veya kuyrukta mevcut ({reason})! Mükerrer yükleme iptal edildi.")
                return None
        except Exception as ge:
            print(f"[AutoDeploy] Guard kontrolünde hata (atlandı): {ge}")
        privacy_status = os.getenv("YOUTUBE_PRIVACY_STATUS", "public")
        
        status_dict = {
            "selfDeclaredMadeForKids": False
        }
        if publish_at:
            # YouTube API kuralı: Zamanlanmış yayın için gizlilik 'private' olmalıdır
            status_dict["privacyStatus"] = "private"
            status_dict["publishAt"] = publish_at
            print(f"[AutoDeploy] ⏱️ YOUTUBE PLANLANMIŞ YAYIN ZAMANI: {publish_at}")
        else:
            status_dict["privacyStatus"] = privacy_status
            print(f"[AutoDeploy] 📢 Yayın Durumu: {privacy_status.upper()}")

        request_body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags[:15],
                "categoryId": "17" # 17 = Sports
            },
            "status": status_dict
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        print("[AutoDeploy] ⏳ YouTube'a yükleniyor... (Bu işlem dosya boyutuna göre sürebilir)")
        try:
            request = youtube.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=media
            )
            response = request.execute()
            print(f"\n[AutoDeploy] ✅ YÜKLEME BAŞARILI!")
            print(f"[AutoDeploy] 🔗 Video Linki: https://youtu.be/{response['id']}")
            if publish_at:
                print(f"[AutoDeploy] 📅 Video YouTube tarafından {publish_at} tarihinde otomatik HERKESE AÇIK (Public) yapılacaktır!")
            else:
                print(f"[AutoDeploy] 📢 Yayın Durumu: {privacy_status.upper()} (Kanalınızda yayında!)")
            return response['id']
        except Exception as e:
            print(f"\n[AutoDeploy] ❌ Yükleme sırasında hata oluştu: {e}")
            raise e
