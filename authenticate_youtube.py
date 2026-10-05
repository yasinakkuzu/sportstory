#!/usr/bin/env python3
"""
SportStory Multi-Channel YouTube Authentication & Setup Wizard.
=============================================================================
Tek Google hesabı üzerinden hem SportStory Türkçe hem de SportStory Global
kanallarını bağımsız olarak yetkilendirir ve kalıcı token dosyalarını oluşturur:
- token_tr.pickle ➡️ SportStory Türkçe Kanalı
- token_en.pickle ➡️ SportStory Global (İngilizce) Kanalı
"""

import os
import sys
import pickle
import argparse
from pathlib import Path
from engine.agents.auto_deploy_agent import AutoDeployAgent


def get_authenticated_channel_info(token_file: str):
    """Token dosyasından bağlı YouTube kanalının adını ve ID'sini sorgular."""
    if not os.path.exists(token_file):
        return None
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        with open(token_file, "rb") as f:
            creds = pickle.load(f)
        if creds:
            if not creds.valid and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_file, "wb") as f:
                    pickle.dump(creds, f)
            if creds.valid:
                service = build("youtube", "v3", credentials=creds)
                res = service.channels().list(mine=True, part="snippet,statistics").execute()
                items = res.get("items", [])
                if items:
                    snippet = items[0]["snippet"]
                    stats = items[0].get("statistics", {})
                    return {
                        "title": snippet.get("title", "Bilinmeyen Kanal"),
                        "id": items[0].get("id"),
                        "subscribers": stats.get("subscriberCount", "0")
                    }
    except Exception:
        pass
    return None


def authenticate_channel(lang: str):
    """Belirtilen dil için kanalı yetkilendirir."""
    lang = lang.lower()
    label = "🇹🇷 SPORTSTORY TÜRKÇE" if lang == "tr" else "🌐 SPORTSTORY GLOBAL (EN)"
    token_target = f"token_{lang}.pickle"

    print("\n" + "=" * 65)
    print(f"🔐 {label} YETKİLENDİRME ADIMI")
    print("=" * 65)
    print(f"📁 Hedef Yetki Dosyası: {token_target}")
    print("\n👉 ÖNEMLİ ADIMLAR:")
    print(" 1. Tarayıcınızda Google oturum açma sayfası açılacak.")
    print(" 2. Mevcut Google hesabınızı seçin.")
    if lang == "tr":
        print(" 3. ⚠️ Çıkan kanal listesinden 'SportStory Türkçe' (veya açtığınız Türkçe marka kanalını) seçin!")
    else:
        print(" 3. ⚠️ Çıkan kanal listesinden 'SportStory Global' kanalını seçin!")
    print(" 4. 'Devam Et' ve 'İzin Ver' butonlarına tıklayın.\n")
    print("🌐 Tarayıcı açılıyor, lütfen bekleyin...")

    agent = AutoDeployAgent(lang=lang)
    try:
        service = agent.authenticate(lang=lang)
        if service:
            info = get_authenticated_channel_info(token_target)
            print("\n" + "=" * 65)
            print(f"🎉 TEBRİKLER! {label} BAĞLANTISI BAŞARILI!")
            if info:
                print(f"📺 Bağlanan YouTube Kanalı: {info['title']} (ID: {info['id']})")
                print(f"👥 Abone Sayısı: {info['subscribers']}")
            print(f"💾 Kalıcı Yetki Dosyası: {token_target} kaydedildi.")
            print("=" * 65 + "\n")
            return True
    except Exception as e:
        print(f"\n❌ Yetkilendirme sırasında hata oluştu: {e}\n")
        return False


def show_status():
    """Mevcut token durumlarını listeler."""
    print("\n📊 MEVCUT YOUTUBE KANAL BAĞLANTI DURUMU:")
    print("-" * 55)
    for lang, name in [("tr", "SportStory Türkçe"), ("en", "SportStory Global")]:
        token_file = f"token_{lang}.pickle"
        info = get_authenticated_channel_info(token_file)
        if info:
            print(f"  ✅ {name.ljust(22)}: BAĞLI ({info['title']}) [{token_file}]")
        else:
            print(f"  ❌ {name.ljust(22)}: BAĞLI DEĞİL [{token_file} eksik]")
    print("-" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser(description="SportStory Multi-Channel YouTube Yetkilendirme Sihirbazı")
    parser.add_argument("--lang", type=str, choices=["tr", "en"], help="Yetkilendirilecek kanal dili ('tr' veya 'en')")
    parser.add_argument("--all", action="store_true", help="Hem Türkçe hem İngilizce kanalı sırayla bağla")
    parser.add_argument("--status", action="store_true", help="Mevcut kanalların bağlantı durumunu göster")
    args = parser.parse_args()

    print("=" * 65)
    print("🎬 SPORTSTORY - ÇİFT KANALLI YOUTUBE YETKİLENDİRME SİHİRBAZI")
    print("=" * 65)

    secrets_file = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
    if not os.path.exists(secrets_file):
        print(f"\n❌ HATA: '{secrets_file}' bulunamadı!")
        print("Lütfen Google Cloud Console'dan indirdiğiniz Desktop App OAuth dosyasını bu dizine koyun.\n")
        sys.exit(1)

    if args.status:
        show_status()
        return

    if args.lang:
        authenticate_channel(args.lang)
        show_status()
        return

    if args.all:
        authenticate_channel("tr")
        authenticate_channel("en")
        show_status()
        return

    # Etkileşimli Menü
    show_status()
    print("Lütfen yapmak istediğiniz işlemi seçin:")
    print("  1) 🇹🇷 SportStory Türkçe Kanalını Bağla / Güncelle (token_tr.pickle)")
    print("  2) 🌐 SportStory Global Kanalını Bağla / Güncelle (token_en.pickle)")
    print("  3) 🚀 Her İki Kanalı Sırayla Bağla (TR & EN)")
    print("  4) 🚪 Çıkış")

    try:
        choice = input("\nSeçiminiz (1/2/3/4): ").strip()
        if choice == "1":
            authenticate_channel("tr")
        elif choice == "2":
            authenticate_channel("en")
        elif choice == "3":
            authenticate_channel("tr")
            authenticate_channel("en")
        elif choice == "4":
            print("Çıkış yapıldı.")
            return
        else:
            print("Geçersiz seçim.")
    except (KeyboardInterrupt, EOFError):
        print("\nİşlem iptal edildi.")

    show_status()


if __name__ == "__main__":
    main()
