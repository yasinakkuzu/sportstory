#!/usr/bin/env python3
"""
SportStory Autopilot Engine
=============================================================================
7/24 Tam Otonom YouTube Shorts Fabrikası:
- Gemini 3.6 Flash / Knowledge Base ile dinamik kriz ve skandal keşfi
- Pexels B-Roll & Edge-TTS stüdyo seslendirme
- Kinetik altyazı & The Bullish Shield rozet renderı
- YouTube Studio'ya doğrudan 'Public' veya 'Planlanmış' (Scheduled) otomatik yükleme
"""

import os
import sys
import time
import json
import argparse
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from generate_short import MasterOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("SportStory.Autopilot")


def run_single_production(lang: str = "en", publish_at: str = None, topic: str = None):
    logger.info(f"🚀 Otonom Üretim Başlatılıyor (Hedef Dil: {lang.upper()})...")
    orchestrator = MasterOrchestrator()
    vid_id = orchestrator.run_autonomous_pipeline(lang, publish_at=publish_at, topic=topic)
    logger.info("✨ Video üretimi ve YouTube yükleme döngüsü tamamlandı!")
    return vid_id


def run_continuous_loop(interval_hours: float, lang: str = "en"):
    interval_seconds = int(interval_hours * 3600)
    logger.info("=" * 65)
    logger.info(f"🤖 SPORTSTORY 7/24 AUTOPILOT AKTİF EDİLDİ!")
    logger.info(f"⏱️ Üretim Aralığı: Her {interval_hours} Saatte Bir")
    logger.info(f"🌐 Yayın Dili: {lang.upper()} (SportStory Global)")
    logger.info(f"📢 YouTube Durumu: PUBLIC (Herkese Açık)")
    logger.info("=" * 65)

    iteration = 1
    while True:
        logger.info(f"\n🎬 DÖNGÜ #{iteration} BAŞLIYOR... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        try:
            run_single_production(lang)
        except Exception as e:
            logger.error(f"❌ Döngü sırasında hata oluştu: {e}")
        
        logger.info(f"⏳ Bir sonraki üretim {interval_hours} saat sonra ({datetime.fromtimestamp(time.time() + interval_seconds).strftime('%H:%M:%S')}). Bekleniyor...")
        iteration += 1
        time.sleep(interval_seconds)


def get_queue_file(lang: str = "en") -> Path:
    if str(lang).lower() == "tr":
        return Path("output/schedule_queue_tr.json")
    return Path("output/schedule_queue.json")


def load_schedule_queue(lang: str = "en") -> list:
    q_file = get_queue_file(lang)
    if q_file.exists():
        try:
            with open(q_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def record_scheduled_video(video_id: str, publish_at_iso: str, local_time_str: str, lang: str = "en"):
    queue = load_schedule_queue(lang)
    queue.append({
        "id": video_id,
        "publish_at": publish_at_iso,
        "local_time": local_time_str
    })
    q_file = get_queue_file(lang)
    q_file.parent.mkdir(parents=True, exist_ok=True)
    with open(q_file, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

    try:
        from engine.content_registry import load_registry, save_registry
        reg = load_registry()
        for item in reg:
            if item.get("video_id") == video_id:
                item["publish_at"] = publish_at_iso
                item["local_time"] = local_time_str
                item["status"] = "SCHEDULED"
        save_registry(reg)
    except Exception:
        pass


def get_next_publish_time(interval_hours: float = 12.0, lang: str = "en") -> datetime:
    """
    Kuyruktaki en son planlanmış videonun zamanını bulur ve ondan 'interval_hours' saat sonrasını döndürür.
    Eğer kuyruk boşsa veya tüm planlar geçmişte kalmışsa:
    Hedef ülkenin en yüksek izlenme saatine (Akşam 20:00 veya Sabah 08:00 prime-time) hizalar.
    """
    queue = load_schedule_queue(lang)
    now_utc = datetime.now(timezone.utc)
    max_time = None

    for item in queue:
        try:
            p_time = datetime.fromisoformat(item["publish_at"].replace("Z", "+00:00"))
            if max_time is None or p_time > max_time:
                max_time = p_time
        except Exception:
            pass

    if max_time is not None and max_time > now_utc:
        return max_time + timedelta(hours=interval_hours)

    # Kuyruk boşsa veya geçmişte kalmışsa en yakın prime-time slotunu hedefle (20:00 veya 08:00)
    local_tz = timezone(timedelta(hours=3))
    now_local = datetime.now(local_tz)

    slot_evening = now_local.replace(hour=20, minute=0, second=0, microsecond=0)
    slot_morning = (now_local + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)

    if now_local < slot_evening - timedelta(hours=1):
        target = slot_evening
    else:
        target = slot_morning

    return target.astimezone(timezone.utc)


def run_batch_schedule(video_count: int = 10, interval_hours: float = 12.0, lang: str = "en", watch: bool = True, topics: list = None):
    """
    Bilgisayar açıkken YouTube günlük video kotasını dolduracak şekilde videoları arka arkaya üretir,
    yükler ve YouTube üzerinde 12 saat arayla otomatik yayınlanacak şekilde PLANLAR (Schedule).
    watch=True verildiğinde kotaya takılınca kapanmaz; 30 dakikada bir kontrol ederek kota açıldıkça sıradaki videoları yükler.
    Böylece bilgisayar kapansa bile YouTube videoları saatinde (12 saatte bir) kendiliğinden yayına alır!
    """
    channel_name = "SportStory TR" if lang == "tr" else "SportStory Global"
    logger.info("=" * 65)
    logger.info("📦 SPORTSTORY TOPLU PLANLANMIŞ ÜRETİM (BATCH SCHEDULER)")
    logger.info(f"🎯 Hedef Video Sayısı: {video_count}")
    logger.info(f"⏱️ Yayın Aralığı: Her {interval_hours} Saatte Bir")
    logger.info(f"🌐 Dil: {lang.upper()} ({channel_name})")
    if watch:
        logger.info("👀 Nöbetçi Modu (Watch): AKTİF (Kota dolduğunda nöbette bekler)")
    logger.info("=" * 65)

    orchestrator = MasterOrchestrator()
    successful_uploads = []
    produced_count = 0

    while produced_count < video_count:
        target_time = get_next_publish_time(interval_hours, lang=lang)
        publish_at_iso = target_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        local_time_str = target_time.astimezone().strftime("%Y-%m-%d %H:%M")

        video_idx = produced_count + 1
        current_topic = topics[produced_count] if topics and produced_count < len(topics) else None
        logger.info(f"\n=======================================================")
        logger.info(f"🎬 BATCH VİDEO #{video_idx}/{video_count} ÜRETİLİYOR... {f'({current_topic})' if current_topic else ''}")
        logger.info(f"📅 Planlanan YouTube Yayın Zamanı: {local_time_str} ({publish_at_iso})")
        logger.info(f"=======================================================")

        try:
            vid_id = orchestrator.run_autonomous_pipeline(lang, publish_at=publish_at_iso, topic=current_topic)
            if vid_id:
                record_scheduled_video(vid_id, publish_at_iso, local_time_str, lang=lang)
                successful_uploads.append({
                    "id": vid_id,
                    "schedule": local_time_str,
                    "publish_at": publish_at_iso
                })
                produced_count += 1
                logger.info(f"✅ Video #{video_idx} YouTube'a yüklendi ve planlandı! ID: {vid_id}")
            else:
                logger.warning(f"⚠️ Video #{video_idx} üretilemedi veya ContentGuard mükerrerlik filtresine takıldı. Yeniden deneniyor...")
                time.sleep(2)
        except Exception as e:
            err_str = str(e)
            if "quotaExceeded" in err_str or "uploadLimitExceeded" in err_str or "dailyLimitExceeded" in err_str:
                logger.warning(f"🛑 YouTube günlük yükleme kotasına ulaşıldı: {err_str}")
                if watch:
                    logger.info("⏳ NÖBET MODU: Bilgisayarınız açık olduğu sürece arka planda kotanın açılması bekleniyor...")
                    logger.info("30 dakika sonra kota tekrar denenecek. Yer açıldığında sıradaki video yüklenip planlanacaktır.")
                    time.sleep(1800)
                    logger.info("🔄 Kota yeniden kontrol ediliyor...")
                    continue
                else:
                    logger.info("Mevcut kotanın tamamı dolduruldu. Toplu üretim durduruluyor.")
                    break
            else:
                logger.error(f"❌ Video #{video_idx} üretilirken hata oluştu: {e}")
                if watch:
                    time.sleep(60)
                    continue
                else:
                    break

    logger.info("\n" + "=" * 65)
    logger.info("🏆 TOPLU PLANLAMA TAMAMLANDI!")
    logger.info(f"📊 Başarıyla Planlanan Toplam Video: {len(successful_uploads)}")
    for idx, item in enumerate(successful_uploads, 1):
        logger.info(f"  {idx}. https://youtu.be/{item['id']} ➡️ Yayın: {item['schedule']}")
    logger.info("\n💤 ARTIK BİLGİSAYARINIZI GÜVENLE KAPATABİLİRSİNİZ.")
    logger.info("YouTube sunucuları belirlenen saatler geldiğinde videoları otomatik olarak Herkese Açık (Public) yapacaktır!")
    logger.info("=" * 65 + "\n")
    return successful_uploads


CURATED_UNIFIED_PILLARS_TOPICS = [
    # --- Pillar 1: Absurd Contracts & Con Artists ---
    {
        "pillar": "Pillar 1: Absurd Contracts",
        "tr": "Stefan Schwarz: Uzaya Gitmesi Yasaklanan Futbolcu",
        "en": "Stefan Schwarz: The Space Flight Ban Contract Clause"
    },
    {
        "pillar": "Pillar 3: Real-Time Wealth",
        "tr": "Cristiano Ronaldo: Saniyede 7 Dolar Kazanan Servet Makinesi",
        "en": "Cristiano Ronaldo: The $7 Per Second Al Nassr Fortune"
    },
    {
        "pillar": "Pillar 1: Absurd Contracts",
        "tr": "Dennis Bergkamp: Uçak Korkusu ve Uçamayan Hollandalı Maddesi",
        "en": "Dennis Bergkamp: The Non-Flying Dutchman Contract Clause"
    },
    {
        "pillar": "Pillar 3: Real-Time Wealth",
        "tr": "Neymar: Özel Jet Filosu ve Suudi Sarayı Talepleri",
        "en": "Neymar: The Private Jet Fleet & Saudi Palace Demands"
    },
    {
        "pillar": "Pillar 1: Absurd Contracts",
        "tr": "Giuseppe Reina: Her Yıl Ücretsiz Lego Ev Maddesi",
        "en": "Giuseppe Reina: The Free Lego House Every Year Clause"
    },
    {
        "pillar": "Pillar 3: Real-Time Wealth",
        "tr": "Lionel Messi: Apple TV Gelir Ortaklığı ve Inter Miami Hisseleri",
        "en": "Lionel Messi: The Apple TV Revenue Share & Inter Miami Stake"
    },
    {
        "pillar": "Pillar 1: Absurd Contracts",
        "tr": "Neil Ruddock: 99.8 Kilo Sınırı ve Kilo Başına Para Cezası",
        "en": "Neil Ruddock: The 99.8kg Weight Limit Penalty Clause"
    },
    {
        "pillar": "Pillar 3: Real-Time Wealth",
        "tr": "Kylian Mbappe: Real Madrid'den 150 Milyon Euroluk İmza Primi",
        "en": "Kylian Mbappe: The 150M Real Madrid Signing Bonus Breakdown"
    },
    {
        "pillar": "Pillar 1: Absurd Contracts",
        "tr": "Ali Dia: Premier Lig'i Dolandıran 53 Dakikalık Sahte Futbolcu",
        "en": "Ali Dia: The 53-Minute Premier League Con Artist"
    },
    # --- Pillar 2: Club Crises & Scandals ---
    {
        "pillar": "Pillar 2: Club Crises",
        "tr": "Manchester City: 115 Kural İhlali ve Küme Düşme Davası",
        "en": "Manchester City: The 115 Charges Trial That Could Relegate a Giant"
    },
    {
        "pillar": "Pillar 2: Club Crises",
        "tr": "Barcelona: 1.35 Milyar Euroluk Borç Bataklığı ve Messi'nin Vedası",
        "en": "Barcelona: How FC Barcelona Lost One Billion Euros"
    },
    {
        "pillar": "Pillar 2: Club Crises",
        "tr": "Chelsea: 1 Milyar Sterlinlik Harcama ve 8 Yıllık Kontrat Hilesi",
        "en": "Chelsea: The £1 Billion 8-Year Contract Loophole"
    },
    {
        "pillar": "Pillar 2: Club Crises",
        "tr": "Lyon: John Textor'ın 500 Milyon Euroluk Borcu ve Küme Düşme Tehlikesi",
        "en": "Lyon: John Textor's 500M Debt Crisis & Ligue 1 Relegation Threat"
    },
    {
        "pillar": "Pillar 2: Club Crises",
        "tr": "Inter Milan: Suning'in 400 Milyonluk Borcu ve Oaktree Fonunun Kulübe El Koyması",
        "en": "Inter Milan: Oaktree Capital's Takeover From Suning Over 400M Debt"
    },
    {
        "pillar": "Pillar 2: Club Crises",
        "tr": "Aston Villa: 100 Milyonluk Finansal Kural Çıkmazı ve Acil Oyuncu Satışı",
        "en": "Aston Villa: PSR Red Line & Unai Emery's 100M Emergency Fire Sale"
    }
]


def run_dual_channel_production(topic_tr: str = None, topic_en: str = None, interval_hours: float = 12.0) -> dict:
    """
    Aynı konuyu hem TÜRKÇE hem İNGİLİZCE üreterek 2 kanala birden planlar:
    - SportStory TR (token_tr.pickle)
    - SportStory Global (token_en.pickle)
    """
    logger.info("=" * 65)
    logger.info("🌍 SPORTSTORY ÇİFT KANALLI ÜRETİM (TR & GLOBAL EN)")
    logger.info("=" * 65)

    # Otomatik Eşleştirme: Eksik dil varsa havuzdan veya birbirine denk konulardan eşle
    if not topic_tr and not topic_en:
        from engine.guards.content_guard import get_content_guard
        guard = get_content_guard()
        available = [t for t in CURATED_UNIFIED_PILLARS_TOPICS if not guard.is_club_on_cooldown(t["tr"], cooldown_count=4)[0]]
        picked = available[0] if available else CURATED_UNIFIED_PILLARS_TOPICS[0]
        topic_tr = picked["tr"]
        topic_en = picked["en"]
    elif topic_tr and not topic_en:
        for t in CURATED_UNIFIED_PILLARS_TOPICS:
            if t["tr"].lower() in topic_tr.lower() or topic_tr.lower() in t["tr"].lower():
                topic_en = t["en"]
                break
        if not topic_en:
            topic_en = topic_tr
    elif topic_en and not topic_tr:
        for t in CURATED_UNIFIED_PILLARS_TOPICS:
            if t["en"].lower() in topic_en.lower() or topic_en.lower() in t["en"].lower():
                topic_tr = t["tr"]
                break
        if not topic_tr:
            topic_tr = topic_en

    logger.info(f"📌 Hedef Konu (TR) : {topic_tr}")
    logger.info(f"📌 Hedef Konu (EN) : {topic_en}")

    orchestrator = MasterOrchestrator()
    results = {}

    # 1. TÜRKÇE KANAL (SportStory TR)
    time_tr = get_next_publish_time(interval_hours, lang="tr")
    iso_tr = time_tr.strftime("%Y-%m-%dT%H:%M:%SZ")
    local_tr = time_tr.astimezone().strftime("%Y-%m-%d %H:%M")
    logger.info(f"\n🇹🇷 [1/2] SPORTSTORY TR ÜRETİMİ BAŞLIYOR... Hedef Yayın: {local_tr}")
    try:
        vid_tr = orchestrator.run_autonomous_pipeline(lang="tr", publish_at=iso_tr, topic=topic_tr)
        if vid_tr:
            record_scheduled_video(vid_tr, iso_tr, local_tr, lang="tr")
            results["tr"] = {"id": vid_tr, "schedule": local_tr, "publish_at": iso_tr}
            logger.info(f"✅ SportStory TR Videosu Başarıyla Planlandı: https://youtu.be/{vid_tr}")
    except Exception as e:
        err_str = str(e)
        if "uploadLimitExceeded" in err_str or "quotaExceeded" in err_str:
            logger.warning("🛑 [SportStory TR] Günlük YouTube yükleme sınırına (uploadLimitExceeded) ulaşıldı!")
            logger.info("ℹ️ YouTube yeni ve standart kanallara 24 saatte maksimum 5-10 video yükleme hakkı tanır.")
            logger.info("ℹ️ SportStory TR kanalında önümüzdeki 3 gün boyunca saatinde yayına girecek 5 video hazır durumdadır.")
            results["tr"] = {"status": "DAILY_LIMIT_REACHED", "error": "uploadLimitExceeded"}
        else:
            raise e

    # 2. GLOBAL KANAL (SportStory Global)
    time_en = get_next_publish_time(interval_hours, lang="en")
    iso_en = time_en.strftime("%Y-%m-%dT%H:%M:%SZ")
    local_en = time_en.astimezone().strftime("%Y-%m-%d %H:%M")
    logger.info(f"\n🌐 [2/2] SPORTSTORY GLOBAL (EN) ÜRETİMİ BAŞLIYOR... Hedef Yayın: {local_en}")
    try:
        vid_en = orchestrator.run_autonomous_pipeline(lang="en", publish_at=iso_en, topic=topic_en)
        if vid_en:
            record_scheduled_video(vid_en, iso_en, local_en, lang="en")
            results["en"] = {"id": vid_en, "schedule": local_en, "publish_at": iso_en}
            logger.info(f"✅ SportStory Global Videosu Başarıyla Planlandı: https://youtu.be/{vid_en}")
    except Exception as e:
        err_str = str(e)
        if "uploadLimitExceeded" in err_str or "quotaExceeded" in err_str:
            logger.warning("🛑 [SportStory Global] Günlük YouTube yükleme sınırına (uploadLimitExceeded) ulaşıldı!")
            results["en"] = {"status": "DAILY_LIMIT_REACHED", "error": "uploadLimitExceeded"}
        else:
            raise e

    return results


def run_dual_batch_schedule(video_count: int = 4, interval_hours: float = 12.0, watch: bool = True):
    """
    Her iki kanal (SportStory TR ve Global) için N adet videoyu sırayla üretir ve planlar.
    Pillar 1, Pillar 2 ve Pillar 3 konularını dengeli harmanlar.
    """
    logger.info("=" * 65)
    logger.info(f"🚀 SPORTSTORY ÇİFT KANALLI TOPLU PLANLAMA: {video_count} Konu (Toplam {video_count * 2} Video)")
    logger.info(f"⏱️ Planlama Aralığı: {interval_hours} saat")
    logger.info("=" * 65)

    completed_pairs = []
    for idx in range(video_count):
        topic_info = CURATED_UNIFIED_PILLARS_TOPICS[idx % len(CURATED_UNIFIED_PILLARS_TOPICS)]
        pillar = topic_info.get("pillar", "General")
        logger.info(f"\n=======================================================")
        logger.info(f"📦 ÇİFT KANAL PAKET #{idx + 1}/{video_count} [{pillar}]")
        logger.info(f"🇹🇷 TR Konu : {topic_info['tr']}")
        logger.info(f"🌐 EN Konu : {topic_info['en']}")
        logger.info(f"=======================================================")

        res = run_dual_channel_production(topic_tr=topic_info["tr"], topic_en=topic_info["en"], interval_hours=interval_hours)
        completed_pairs.append({
            "pillar": pillar,
            "topic_tr": topic_info["tr"],
            "topic_en": topic_info["en"],
            "results": res
        })

        tr_res = res.get("tr", {})
        en_res = res.get("en", {})
        if tr_res.get("status") == "DAILY_LIMIT_REACHED" and en_res.get("status") == "DAILY_LIMIT_REACHED":
            logger.warning("\n🛑 Her iki kanalın da günlük YouTube yükleme limiti doldu.")
            if watch:
                logger.info("⏳ NÖBET MODU: 1 saat sonra YouTube limitleri tekrar kontrol edilecek...")
                time.sleep(3600)
                continue
            else:
                logger.info("Mevcut günlük limit dolduruldu. Yarın limit sıfırlandığında devam edebilirsiniz.")
                break

    logger.info("\n" + "=" * 65)
    logger.info("🏆 ÇİFT KANALLI TÜM VİDEOLAR BAŞARIYLA YAYINA PLANLANDI!")
    logger.info("=" * 65)
    for i, p in enumerate(completed_pairs, 1):
        tr_id = p["results"].get("tr", {}).get("id", "LIMIT DOLDU")
        tr_time = p["results"].get("tr", {}).get("schedule", "-")
        en_id = p["results"].get("en", {}).get("id", "LIMIT DOLDU")
        en_time = p["results"].get("en", {}).get("schedule", "-")
        logger.info(f"{i}. [{p['pillar']}]")
        logger.info(f"   🇹🇷 TR : {'https://youtu.be/' + tr_id if tr_id != 'LIMIT DOLDU' else 'Günlük Limit Doldu'} ({tr_time})")
        logger.info(f"   🌐 EN : {'https://youtu.be/' + en_id if en_id != 'LIMIT DOLDU' else 'Günlük Limit Doldu'} ({en_time})")
    return completed_pairs


def publish_curated_archive(lang: str = "en"):
    from engine.agents.auto_deploy_agent import AutoDeployAgent
    deployer = AutoDeployAgent()
    curated_ids = ["SHORTS_001", "SHORTS_002", "SHORTS_003", "SHORTS_004", "SHORTS_005"]
    logger.info(f"📦 Küratörlü 5 Başyapıt Arşivi YouTube'a Yükleniyor ({lang.upper()})...")
    
    for cid in curated_ids:
        vid_path = Path("output") / (f"{cid.upper()}_EN_final_short.mp4" if lang == "en" else f"{cid.upper()}_final_short.mp4")
        meta_path = Path("output") / f"{cid.lower()}_{lang}_metadata.json"
        
        if vid_path.exists() and meta_path.exists():
            logger.info(f"\n🚀 {cid} doğrudan YouTube'a yükleniyor (Hazır video)...")
            deployer.deploy(str(vid_path), lang, metadata_path=str(meta_path))
        else:
            logger.info(f"\n🎬 {cid} henüz derlenmemiş, pipeline baştan derlenip yüklenecek...")
            orchestrator = MasterOrchestrator()
            orchestrator.run_manual_pipeline(cid, lang)


def main():
    parser = argparse.ArgumentParser(description="SportStory 7/24 Autopilot Production Engine")
    parser.add_argument("--now", action="store_true", help="Hemen şimdi otonom video üretir ve YouTube'a yükler")
    parser.add_argument("--topic", type=str, default=None, help="Belirli bir kriz/gündem konusu")
    parser.add_argument("--loop", type=float, metavar="HOURS", help="Sürekli otonom döngüyü başlatır (Örn: --loop 4)")
    parser.add_argument("--batch-schedule", type=int, metavar="COUNT", help="N adet videoyu aralıklı olarak YouTube'a planlar (Örn: --batch-schedule 4)")
    parser.add_argument("--interval", type=float, default=12.0, help="Planlanan videolar arası saat aralığı (Varsayılan: 12.0)")
    parser.add_argument("--watch", action="store_true", default=True, help="Kotaya takılınca kapanmaz; kotada yer açıldıkça yüklemeye devam eder")
    parser.add_argument("--publish-curated", action="store_true", help="Küratörlü 5 başyapıt videoyu YouTube'a aktarır")
    parser.add_argument("--lang", type=str, choices=["en", "tr", "both"], default="both", help="Yayın dili (Varsayılan: both)")
    parser.add_argument("--dual", action="store_true", help="Her iki kanala (TR & Global EN) eşzamanlı üret ve planla")
    args = parser.parse_args()

    is_dual = args.dual or args.lang == "both"

    if args.now:
        if is_dual:
            run_dual_channel_production(topic_tr=args.topic, topic_en=args.topic, interval_hours=args.interval)
        else:
            run_single_production(args.lang, topic=args.topic)
    elif args.batch_schedule:
        if is_dual:
            run_dual_batch_schedule(video_count=args.batch_schedule, interval_hours=args.interval, watch=args.watch)
        else:
            curated_batch_topics = [
                t["en"] for t in CURATED_UNIFIED_PILLARS_TOPICS
            ] if args.lang == "en" else [
                t["tr"] for t in CURATED_UNIFIED_PILLARS_TOPICS
            ]
            run_batch_schedule(args.batch_schedule, args.interval, args.lang, watch=args.watch, topics=curated_batch_topics)
    elif args.loop:
        run_continuous_loop(args.loop, args.lang)
    elif args.publish_curated:
        publish_curated_archive(args.lang)
    else:
        print("\n" + "=" * 65)
        print("🤖 SPORTSTORY ÇİFT KANALLI OTONOM ÜRETİM PANELİ (TR & EN)")
        print("=" * 65)
        print("Kullanım Seçenekleri:")
        print("  1. İki Kanala da Eşzamanlı 1'er Video Üret & Planla (Varsayılan):")
        print("     python autopilot.py --now --dual")
        print()
        print("  2. İki Kanal İçin Toplu Planlama (Örn: 3'er adet = 6 video, 12 saatte bir):")
        print("     python autopilot.py --batch-schedule 3 --dual --interval 12")
        print()
        print("  3. Sadece Türkçe Kanal İçin 1 Video:")
        print("     python autopilot.py --now --lang tr")
        print()
        print("  4. Sadece Global (EN) Kanal İçin 1 Video:")
        print("     python autopilot.py --now --lang en")
        print()
        print("  5. YouTube Kanallarını Yetkilendir / Durum:")
        print("     python authenticate_youtube.py --status")
        print("=" * 65 + "\n")


if __name__ == "__main__":
    main()

