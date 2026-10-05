#!/usr/bin/env python3
"""
SportStory - YouTube Channel Cleanup & Title Fixer
Fixes truncated titles and deletes zero-view videos using AutoDeployAgent.
"""
import sys
from engine.agents.auto_deploy_agent import AutoDeployAgent

# 2 Videos with truncated titles to fix
TITLES_TO_FIX = {
    "W8_pHKfo_8I": "Leeds United: The £60M Goldfish Bowl! 💸 #shorts",
    "vErXcQxXIWk": "Everton: The 777 Partners Disaster! 📉 #shorts"
}

# Zero-view old videos to remove
VIDEOS_TO_DELETE = [
    ("Qx5Kv6-X1xY", "FC Barcelona: The 1.3 Billion Euro Ruin"),
    ("qQRy1g8L5HI", "AC Milan's Shady Billion-Dollar Sale"),
    ("o3rNzQXYKaM", "AC Milan: The €600M RedBird Debt Trap"),
    ("jOvtVfRFaWM", "Juventus: Plusvalenza Secret Book"),
    ("YWNvXkax5L0", "Barca: $1.4B Debt & Lever Nightmare"),
    ("H4whMMk28W8", "Parma: Parmalat Diary Bankruptcy (if exists)")
]

def main():
    print("=" * 65)
    print("🧹 SPORTSTORY YOUTUBE KANAL TEMİZLİK VE BAŞLIK DÜZELTME ARACI")
    print("=" * 65)

    agent = AutoDeployAgent()
    service = agent.authenticate()
    if not service:
        print("❌ Yetkilendirme sağlanamadı.")
        sys.exit(1)

    print("\n1️⃣ EKSİK / KESİLMİŞ BAŞLIKLAR DÜZELTİLİYOR...")
    for vid_id, new_title in TITLES_TO_FIX.items():
        print(f"👉 Güncelleniyor: {vid_id} -> {new_title}")
        agent.update_video_title(vid_id, new_title)

    print("\n2️⃣ SIFIR GÖRÜNTÜLENMELİ ESKİ VİDEOLAR SİLİNİYOR...")
    for vid_id, desc in VIDEOS_TO_DELETE:
        print(f"👉 Siliniyor: {vid_id} ({desc})")
        agent.delete_video(vid_id)

    print("\n" + "=" * 65)
    print("✅ TÜM KANAL TEMİZLİĞİ VE BAŞLIK GÜNCELLEMELERİ TAMAMLANDI!")
    print("=" * 65)

if __name__ == "__main__":
    main()
