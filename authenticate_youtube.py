import os
import sys
from pathlib import Path
from engine.agents.auto_deploy_agent import AutoDeployAgent

def main():
    print("=" * 60)
    print("🔐 SportStory - YouTube Yetkilendirme & Bağlantı Sihirbazı")
    print("=" * 60)

    secrets_file = "client_secrets.json"
    if not os.path.exists(secrets_file):
        print(f"\n❌ HATA: '{secrets_file}' bulunamadı!")
        print("Lütfen Google Cloud Console'dan indirdiğiniz Desktop App OAuth dosyasını bu dizine koyun.\n")
        sys.exit(1)

    print(f"\n✅ '{secrets_file}' doğrulandı.")
    print("🌐 Tarayıcınız otomatik olarak açılacak ve Google giriş ekranı gelecek...")
    print("👉 İlgili YouTube kanalınızın bağlı olduğu Google hesabını seçip 'İzin Ver' / 'Continue' deyin.\n")

    agent = AutoDeployAgent()
    try:
        service = agent.authenticate()
        if service:
            # Kanal adını test etmek için API çağrısı yapalım
            channels_response = service.channels().list(mine=True, part="snippet").execute()
            items = channels_response.get("items", [])
            if items:
                channel_title = items[0]["snippet"]["title"]
                print("\n" + "=" * 60)
                print(f"🎉 TEBRİKLER! BAĞLANTI BAŞARILI!")
                print(f"📺 Bağlanan YouTube Kanalı: {channel_title}")
                print(f"💾 Kalıcı Yetki Dosyası: token.pickle (Oluşturuldu)")
                print("=" * 60)
                print("\n🚀 Artık tüm Shorts üretimleri kanalınıza %100 otomatik yüklenecek!\n")
            else:
                print("\n✅ Yetkilendirme başarılı! (token.pickle kaydedildi)")
    except Exception as e:
        print(f"\n❌ Yetkilendirme sırasında bir hata oluştu: {e}\n")

if __name__ == "__main__":
    main()
