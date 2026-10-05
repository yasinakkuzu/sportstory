# SportStory - Otonom YouTube Shorts Çoklu Ajan Üretim Motoru 🎬⚡

> **İki Kanallı (Türkçe & Global English) Uçtan Uca YouTube Shorts Otomasyon Fabrikası**

Bu repo, spor finansı ve transfer skandallarına odaklanan profesyonel 9:16 dikey videoların (YouTube Shorts) **senaryodan nihai MP4 montajına kadar sıfır insan müdahalesiyle** üretilmesini sağlayan çoklu ajan mimarisine sahip bir otomasyon motorudur.

Yapay zeka asistanları (Claude, Cursor, ChatGPT, Antigravity vb.) için hazırlanmış eksiksiz teknik mimari ve kurallar dokümanı için:
👉 **[AGENTS.md](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/AGENTS.md)**

---

## 🌟 Öne Çıkan Özellikler

- **Çift Kanal Desteği (Dual-Channel Architecture):**
  - 🇹🇷 **Türkçe Kanal (`--lang tr`):** `tr-TR-AhmetNeural` spikeri, `TurkishVoiceAuditAgent` telaffuz denetleyicisi, Türkçe kinetik altyazılar ve yerli editoryal tasarım.
  - 🌐 **Global İngilizce Kanal (`--lang en`):** `en-US-ChristopherNeural` spikeri, sıfır Türkçe sızıntısı, bileşik blok ayrıştırması ile milisaniyelik kusursuz altyazı senkronizasyonu.
- **Otonom Türkçe Spiker Ajanı (`TurkishVoiceAuditAgent`):**
  - Yabancı futbolcu isimlerini (`Mbappé -> Embappe`, `Santiago Bernabéu -> Santiyago Bernabeu`) otomatik Türk spor spikeri fonetiğine çevirir.
  - Yabancı Latin diyakritiklerini (`é, á, ó, ú, ñ`) temizler.
  - Bağırma ve tonlama sıçramalarını yumuşatır, yeni yabancı isimleri hafızaya alır (`learned_phonetics.json`).
  - Her videoda WPM (konuşma hızı) ve hece uzama testini yapıp `voice_audit_report.json` üretir.
- **VerticalFlowLayout 3.0 (Görsel Mizanpaj):**
  - Kulüplere özel atmosferik karanlık fonlar (Barcelona, Chelsea, Man City, PSG, Real Madrid).
  - Tam ortalı rozetler ve kilit analiz kutusu (Slayt sayacı kaldırılmıştır).
  - Yalnızca son tartışma sahnesinde beliren parlayan etkileşim butonu (CTA).
  - Sağ alt köşede kurumsal `[ 🛡️ SPORTSTORY ]` The Bullish Shield cam zeminli filigran logosu (Sky Sports / Bleacher Report tarzı saydam ikon).
- **Sidechain Audio Ducking:**
  - Spiker konuştuğunda arka plan modern spor beat ritmi otomatik olarak -20 dB kısılır, cümle aralarında ve outro CTA'da yükselir.
- **YouTube SEO Fabrikası:**
  - Başlık, açıklama, 15+ etiket ve sabitlenmiş etkileşim yorumu `_metadata.json` olarak otomatik hazır hale getirilir.

---

## 🚀 Hızlı Başlangıç (Quick Start)

### 1. Kurulum
```bash
# Sanal ortamı etkinleştirin
source .venv/bin/activate

# Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt
```

### 2. Video Üretimi
```bash
# 🤖 Tam Otonom AI Üretimi (Gündem Araştırması + Senaryo + Render):
python generate_short.py --auto --lang tr
python generate_short.py --auto --lang en

# 📋 Tekil Küratörlü Senaryo Üret (Örn: Real Madrid):
python generate_short.py --id SHORTS_005 --lang tr
python generate_short.py --id SHORTS_001 --lang en

# 🎬 Tüm Arşivi Sırayla Üret:
python generate_short.py --all --lang tr
python generate_short.py --all --lang en
```

---

## 📁 Üretilen Çıktılar Matrisi

Tüm çıktılar `output/` dizininde toplanır:

| ID | Kulüp / Konu | Türkçe Video | İngilizce Video | Kapak Görseli | YouTube SEO Paketi |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SHORTS_001** | Barcelona (1 Milyar $ Borç) | [Video TR](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/output/SHORTS_001_final_short.mp4) | [Video EN](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/output/SHORTS_001_EN_final_short.mp4) | `shorts_001_cover.png` | `shorts_001_metadata.json` |
| **SHORTS_002** | Chelsea (8 Yıllık FFP Hilesi) | [Video TR](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/output/SHORTS_002_final_short.mp4) | [Video EN](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/output/SHORTS_002_EN_final_short.mp4) | `shorts_002_cover.png` | `shorts_002_metadata.json` |
| **SHORTS_003** | Man City (115 Kural İhlali) | [Video TR](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/output/SHORTS_003_final_short.mp4) | [Video EN](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/output/SHORTS_003_EN_final_short.mp4) | `shorts_003_cover.png` | `shorts_003_metadata.json` |
| **SHORTS_004** | PSG (500M€ Mbappé Fiyaskosu) | [Video TR](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/output/SHORTS_004_final_short.mp4) | [Video EN](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/output/SHORTS_004_EN_final_short.mp4) | `shorts_004_cover.png` | `shorts_004_metadata.json` |
| **SHORTS_005** | Real Madrid (Bernabéu Gelir Çarkı) | [Video TR](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/output/SHORTS_005_final_short.mp4) | [Video EN](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/output/SHORTS_005_EN_final_short.mp4) | `shorts_005_cover.png` | `shorts_005_metadata.json` |

---

## 📖 Sistem Mimarisi & Ajan Dokümantasyonu

Projenin teknik detayları, ajan rolleri ve tasarım kuralları **[AGENTS.md](file:///Users/yasinakkuzu/Desktop/SportStory/sports-shorts-pipeline/AGENTS.md)** dosyasında açıklanmıştır.
