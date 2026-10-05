#!/usr/bin/env python3
"""
SportStory - Low View Videos Auto-Deleter
Deletes the 10 videos with < 10 views via YouTube API.
"""
import os
import sys
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

TARGET_VIDEOS = [
    ("o3rNzQXYKaM", "AC Milan: The €600M RedBird Debt Trap!"),
    ("gsNwP3erIbo", "How Valencia CF Built a Ghost Stadium..."),
    ("HlV-ZuWlItY", "How Chelsea Bypassed Financial Fair Play!"),
    ("vnpkNvHG7fs", "The $14B Scam That Killed Italian Football (Parma)"),
    ("UdKxzlAuoQM", "FC Barcelona's 1.3 Billion Euro Debt Timebomb!"),
    ("dN47nn3TLy4", "From Premier League To Prison! (Portsmouth)"),
    ("zXYWQOtdisM", "PSG's €500M Mbappé Nightmare!"),
    ("jOvtVfRFaWM", "Juventus: The Plusvalenza Secret Book Sc"),
    ("vErXcQxXIWk", "Everton: The 777 Partners Disaster!"),
    ("H4whMMk28W8", "When Parma's Billion-Dollar Dairy Empire Collapsed")
]

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def main():
    print("=" * 65)
    print("🗑️ SPORTSTORY 10 ADET DÜŞÜK İZLENMELİ VİDEO SİLME ARACI")
    print("=" * 65)

    client_secrets = "client_secrets.json"
    if not os.path.exists(client_secrets):
        print(f"❌ '{client_secrets}' bulunamadı!")
        sys.exit(1)

    print("\n🔐 YouTube silme yetkisi için Google onay ekranı açılıyor...")
    print("👉 Lütfen tarayıcınızda açılan ekranda SportStory kanalınızın hesabını seçip 'İzin Ver' / 'Continue' deyin.\n")

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
    creds = flow.run_local_server(port=8080, open_browser=True)

    with open("token.pickle", "wb") as f:
        pickle.dump(creds, f)
    print("✅ Silme yetkisi başarıyla alındı ve token.pickle güncellendi!\n")

    youtube = build("youtube", "v3", credentials=creds)

    print("🚀 VİDEOLAR SİLİNİYOR:")
    deleted_count = 0
    for vid_id, title in TARGET_VIDEOS:
        try:
            youtube.videos().delete(id=vid_id).execute()
            print(f"  ✅ Silindi: [{vid_id}] {title}")
            deleted_count += 1
        except Exception as e:
            err = str(e)
            if "videoNotFound" in err:
                print(f"  ℹ️ Zaten silinmiş: [{vid_id}] {title}")
            else:
                print(f"  ⚠️ Hata ({vid_id}): {err}")

    print("\n" + "=" * 65)
    print(f"🎉 İŞLEM TAMAMLANDI! Toplam {deleted_count} video YouTube kanalınızdan silindi.")
    print("=" * 65)

if __name__ == "__main__":
    main()
