# SPORTSTORY: Autonomous YouTube Shorts Multi-Agent Engine
> **AI Instruction & Master Architecture Blueprint (AGENTS.md)**
> Bu dosya, projeyi devralan herhangi bir Yapay Zeka (AI / Agentic Assistant) için sistemin tüm mimarisini, kurallarını, ajan rollerini ve çalıştırma standartlarını eksiksiz aktarmak üzere hazırlanmıştır.

---

## 📌 1. Proje Amacı & Temel Vizyon

**SportStory**, spor finansı, transfer skandalları ve kulüp krizlerini (Barcelona borcu, Chelsea FFP hilesi, Manchester City 115 suçlaması, PSG Mbappé fiyaskosu, Real Madrid Bernabéu gelir çarkı) yüksek etkili 9:16 dikey videolara (YouTube Shorts) dönüştüren **tam otonom, uçtan uca (headless) bir üretim motorudur**.

Sistem aynı senaryo üzerinden **iki bağımsız kanala** içerik üretir:
1. **🇹🇷 Kanal 1 (Türkiye Pazarı):** Türkçe editoryal dil, `tr-TR-AhmetNeural` spikeri ve otonom telaffuz denetimi (`--lang tr`).
2. **🌐 Kanal 2 (Global Pazar):** İngilizce editoryal dil, `en-US-ChristopherNeural` spikeri ve sıfır Türkçe sızıntısı (`--lang en`).

---

## 🏛️ 2. Çoklu Ajan Mimarisi (Agentic Roles & Hierarchy)

Tüm iş akışı `generate_short.py` içerisindeki **`MasterOrchestrator`** tarafından yönetilir. Orkestratör bünyesinde 6 uzman ajan görev yapar:

```
                          ┌─────────────────────────────┐
                          │     MasterOrchestrator      │
                          │     (generate_short.py)     │
                          └──────────────┬──────────────┘
                                         │
        ┌───────────────────┬────────────┴───────┬────────────────────┐
        ▼                   ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ VoiceAudit   │    │ AudioWorker  │     │ AssetWorker  │     │ Subtitle     │
│ Agent        │    │              │     │              │     │ Worker       │
│(phonetics.py)│    │ (sidechain)  │     │(FlowLayout)  │     │(Kinetic ASS) │
└──────────────┘    └──────────────┘     └──────────────┘     └──────────────┘
                                                 │                    │
                                                 └─────────┬──────────┘
                                                           ▼
                                                 ┌──────────────────┐
                                                 │ RenderCompiler & │
                                                 │ PublisherWorker  │
                                                 └──────────────────┘
```

### 1. `TurkishVoiceAuditAgent` (`engine/agents/voice_audit_agent.py`)
- **Giriş Denetimi (Pre-Synthesis):** Metindeki yabancı futbolcu/kulüp/stadyum isimlerini tarar (`MASTER_PHONETIC_LEXICON`), yabancı aksanları (`é, á, ó, ú, ñ -> e, a, o, u, n`) temizler, spikerin bağırmasını ve hece uzatmasını önlemek için noktalama tonlamasını (`! -> .`, `; -> ,`) sakinleştirir.
- **Otonom Öğrenme:** Bilinmeyen yabancı harf öbeklerini (`eau -> o`, `sch -> ş`, `ph -> f`, `th -> t`, `sz -> s`, `w -> v`, `x -> ks`) otonom heceleyerek `engine/learned_phonetics.json` dosyasına işler.
- **Akustik QA (Post-Synthesis):** Konuşma hızını (WPM) ölçer (hedef: 110-165 WPM), anormal hece uzamalarını (>1.4s) ve yutulan kelimeleri (<0.07s) denetler; `voice_audit_report.json` raporu üretir.

### 2. `AudioWorker` (`engine/workers/audio_worker.py`)
- Microsoft Edge-TTS entegrasyonu ile stüdyo seslendirmesi üretir.
- **Bileşik Blok Ayrıştırıcı:** Edge-TTS İngilizce modelinin `"In 2017"`, `"222 million euros"` gibi bileşik zamanlama bloklarını kelime uzunluklarına göre milisaniyelik oranlarla bağımsız kelimelere böler (İngilizce senkron kaymasını sıfırlar).
- **Sidechain Audio Ducking:** Spiker konuştuğunda arka plan spor beat ritmini otomatik olarak -20 dB kısar, cümle aralarında ve outro CTA'da ritmi yükseltir.
- **Yayın Seviyesi Mastering:** `acompressor` ve EBU R128 `loudnorm` (-16 LUFS, True Peak -1.5) uygular.

### 3. `AssetWorker` (`engine/workers/asset_worker.py`)
- Her video için kulüp renk paletine (Barcelona Blaugrana, Chelsea Royal Blue, Man City Sky Blue, PSG Navy/Crimson, Real Madrid Royal Gold) uygun 1080x1920 derin karanlık fonlar üretir.
- **Mizanpaj Standartları:**
  - Slayt sayacı (`1 / 5`) bulunmaz.
  - Üst kategori rozeti (`GİRİŞ ANALİZİ` / `INTRO ANALYSIS`) tam ortalıdır.
  - Kilit analiz kutusu (`KİLİT ANALİZ` / `KEY INSIGHT`) başlık, çizgi ve analiz metni kartın içinde ortalanmıştır.
  - **Erken CTA Kuralı:** `"Fikrini yorumlara yaz!"` / `"Drop your thoughts below!"` butonu ilk 4 sahnede ASLA görünmez. Yalnızca 5. sahnedeki tartışma sorusuyla beraber ekrana gelir.
  - **Markalama:** Sağ alt köşede (Y: 1750, safe-zone) kurumsal cam zeminli `[ 🛡️ SPORTSTORY ]` The Bullish Shield rozeti yer alır (saydam %85 ikon entegrasyonu).

### 4. `SubtitleWorker` & `KineticSubtitleRenderer` (`engine/subtitles.py`)
- Sözcük seviyesinde milisaniyelik zamanlamalarla YouTube Shorts Safe-Zone (Y: 1450) kinetik altyazısı basar.
- Aktif kelime parlayan neon sarı (`#FACC15`), diğer kelimeler yarı saydam beyazdır.
- Titreme (jitter) yapmayan sabit aralıklı metin ölçümü kullanır.

### 5. `RenderCompilerWorker` (`engine/workers/render_worker.py`)
- FFmpeg tabanlı 60 FPS / 1080x1920 dikey video montajı yapar.
- Sahneler arası yumuşak Cross-Dissolve geçişler, Ken Burns dinamik zoom ve üstte ince ilerleme çubuğu (progress bar) ekler.

### 6. `PublisherWorker` (`engine/workers/publisher_worker.py`)
- YouTube Algoritması için optimize edilmiş başlık, açıklama, 15+ etiket ve sabitlenmiş etkileşim yorumunu `shorts_XXX_metadata.json` olarak ihraç eder.

---

## 📂 3. Dosya ve Klasör Yapısı

```
sports-shorts-pipeline/
├── AGENTS.md                   # 👈 Bu dosya: Yapay zekalar için ana operasyon kılavuzu
├── README.md                   # Proje tanıtımı, kurulum ve hızlı başlangıç rehberi
├── project_manifest.json       # Senaryo ve video üretim durum matrisi
├── generate_short.py           # Orkestratör ana çalıştırma betiği (CLI)
├── requirements.txt            # Python bağımlılıkları (edge-tts, pillow, numpy, ffmpeg)
│
├── engine/                     # Çekirdek motor modülleri
│   ├── phonetics.py            # MASTER_PHONETIC_LEXICON ve diyakritik temizleyici
│   ├── subtitles.py            # Kinetik altyazı motoru ve zamanlama eşleştirici
│   ├── compositor.py           # Grafik ve cam kart (glassmorphism) çizici
│   ├── audio_mixer.py          # Prosedürel spor ritmi sentezleyici ve WAV araçları
│   ├── script_parser.py        # Markdown senaryolarını Pydantic nesnesine çeviren ayrıştırıcı
│   ├── schemas.py              # Pydantic veri modelleri (ScenePlan, VideoPipelinePayload)
│   │
│   ├── agents/                 # Akıllı Ajanlar
│   │   ├── __init__.py
│   │   └── voice_audit_agent.py # TurkishVoiceAuditAgent (Pre-synthesis & Post-synthesis QA)
│   │
│   └── workers/                # İcracı İşçiler
│       ├── __init__.py
│       ├── asset_worker.py     # Görsel kart render motoru
│       ├── audio_worker.py     # TTS, ducking ve bileşik blok ayrıştırma
│       ├── render_worker.py    # FFmpeg derleme ve montaj
│       ├── subtitle_worker.py  # ASS altyazı üretimi
│       └── publisher_worker.py # YouTube SEO JSON ihracı
│
├── scripts/                    # Markdown formatında modüler senaryolar
│   ├── SHORTS_001_barcelona_mistake.md
│   ├── SHORTS_002_chelsea_amortization.md
│   ├── SHORTS_003_mancity_115_charges.md
│   ├── SHORTS_004_psg_mbappe_nightmare.md
│   └── SHORTS_005_realmadrid_money_machine.md
│
└── output/                     # Üretilen nihai videolar, kapaklar ve SEO paketleri
    ├── SHORTS_001_final_short.mp4       # Türkçe nihai video
    ├── SHORTS_001_EN_final_short.mp4    # İngilizce nihai video
    ├── shorts_001_cover.png             # 1080x1920 kapak
    ├── shorts_001_metadata.json         # YouTube SEO paketi
    └── shorts_001/                      # Çalışma ara dosyaları ve voice_audit_report.json
```

---

## ⚡ 4. Çalıştırma Komutları (CLI Cheatsheet)

Tüm üretim işlemleri `.venv` ortamındaki Python ile yürütülür:

```bash
# 1. Tam Otonom AI ile Sıfırdan Üretim (TrendScout + ScriptWeaver + Render):
.venv/bin/python generate_short.py --auto --lang tr
.venv/bin/python generate_short.py --auto --lang en

# 2. Tekil Küratörlü Senaryo Üretimi:
.venv/bin/python generate_short.py --id SHORTS_005 --lang tr
.venv/bin/python generate_short.py --id SHORTS_005 --lang en

# 3. Tüm Küratörlü Arşivi Sırayla Üretme:
.venv/bin/python generate_short.py --all --lang tr
.venv/bin/python generate_short.py --all --lang en

# 4. Mevcut Senaryoları Listeleme:
.venv/bin/python generate_short.py --list
```

---

## 🚨 5. Yapay Zekalar İçin Kritik Kodlama ve Tasarım Kuralları (KIRILMAZ KURALLAR)

Projeyi devralan herhangi bir AI geliştirici şu kurallara **kesinlikle uymak zorundadır**:

1. **Erken CTA Yasağı:** Sahne 1, 2, 3 ve 4 içinde kesinlikle "Yorumlara yaz" butonu çizilemez. Buton sadece son sahnede (`scene_idx == 4`) çizilir.
2. **Slayt Numarası Yasağı:** Ekranın sağ üstüne `"1 / 5"` gibi sayaç metinleri eklenemez.
3. **Simetri Kuralı:** Üstteki kategori rozeti ve alttaki Kilit Analiz kutusu her zaman ekran genişliğinde (`WIDTH // 2`) yatay olarak ortalanmalıdır.
4. **Türkçe Fonetik Sözlük Bütünlüğü:**
   - Yeni bir futbolcu ismi ekleneceğinde `MASTER_PHONETIC_LEXICON` içine kelime sınırı (`\b`) destekleyecek şekilde yazılmalıdır.
   - Doğrudan `Mbappé` yazılmamalı, `Embappe` olarak okunması sağlanmalıdır.
   - `Bernabéu` için daima diyakritikler temizlenmeli ve `Santiyago Bernabeu` standartı korunmalıdır.
5. **İngilizce Altyazı Senkronizasyonu:**
   - Edge-TTS WordBoundary'den dönen metin birden fazla kelime içeriyorsa (`In 2017`, `222 million euros`), kesinlikle karakter uzunluğu oranında bağımsız kelimelere bölünmelidir. Aksi halde altyazılar konuşmadan kopar.
6. **Türkçe Büyük Harf Uyumluluğu:**
   - Standart Python `.upper()` fonksiyonu `'i'` harfini İngilizce `'I'` yapar (noktasız). Türkçe başlıklar ve rozetler için daima `turkish_upper()` fonksiyonu (`'i' -> 'İ'`, `'ı' -> 'I'`) kullanılmalıdır.
7. **Markalama:** Sağ alt köşedeki `[ 🛡️ SPORTSTORY ]` The Bullish Shield rozeti silinmemeli veya koordinatları güvenli alanın dışına taşınmamalıdır.
8. **Retro Futbol Modu Standartı:** Arka plan videoları için genel/jenerik oyunlar (GTA, Minecraft vb.) yerine kanalın spor kimliğine ve nostaljik belgesel ruhuna uygun nostaljik futbol oyunları (`bg_pes_retro.mp4`, `bg_pes_milan.mp4`, PES 6, Winning Eleven 2000) standart olarak kullanılır. Çim renginin altyazıları boğmaması için %35 kontrast cam perde uygulanır.
9. **Mükerrer İçerik Denetimi (ContentGuard):** Yapay zeka ve orkestratör `engine.guards.content_guard` kurallarına uymak zorundadır. Aynı kulüp en az 7 video boyunca tekrar işlenemez ve senaryo/başlık benzerliği %70'i aşamaz. Kopya video üretimi ve yüklemesi kesinlikle engellenir.
10. **12 Saatlik Yayın Sıklığı Standardı (12-Hour Scheduling Cadence):** YouTube Shorts algoritmasının yeni kanallarda spam filtrelerine takılmaması, her videonun organik gösterim döngüsünü tamamlaması için videolar en az 12 saat arayla (günde 2 video) planlanır. Sistem açıkken `--batch` modu günlük kota dolana kadar videoları üretir ve YouTube üzerinde `publishAt` ile 12'şer saat arayla sıraya dizer.


