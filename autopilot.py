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


QUEUE_FILE = Path("output/schedule_queue.json")


def load_schedule_queue() -> list:
    if QUEUE_FILE.exists():
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def record_scheduled_video(video_id: str, publish_at_iso: str, local_time_str: str):
    queue = load_schedule_queue()
    queue.append({
        "id": video_id,
        "publish_at": publish_at_iso,
        "local_time": local_time_str
    })
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)


def get_next_publish_time(interval_hours: float = 12.0) -> datetime:
    """
    Kuyruktaki en son planlanmış videonun zamanını bulur ve ondan 'interval_hours' saat sonrasını döndürür.
    Eğer kuyruk boşsa veya tüm planlar geçmişte kalmışsa, şimdiki zamandan 'interval_hours' sonrasını döndürür.
    """
    queue = load_schedule_queue()
    now_utc = datetime.now(timezone.utc)
    max_time = now_utc

    for item in queue:
        try:
            p_time = datetime.fromisoformat(item["publish_at"].replace("Z", "+00:00"))
            if p_time > max_time:
                max_time = p_time
        except Exception:
            pass

    return max_time + timedelta(hours=interval_hours)


def run_batch_schedule(video_count: int = 10, interval_hours: float = 12.0, lang: str = "en", watch: bool = True, topics: list = None):
    """
    Bilgisayar açıkken YouTube günlük video kotasını dolduracak şekilde videoları arka arkaya üretir,
    yükler ve YouTube üzerinde 12 saat arayla otomatik yayınlanacak şekilde PLANLAR (Schedule).
    watch=True verildiğinde kotaya takılınca kapanmaz; 30 dakikada bir kontrol ederek kota açıldıkça sıradaki videoları yükler.
    Böylece bilgisayar kapansa bile YouTube videoları saatinde (12 saatte bir) kendiliğinden yayına alır!
    """
    logger.info("=" * 65)
    logger.info("📦 SPORTSTORY TOPLU PLANLANMIŞ ÜRETİM (BATCH SCHEDULER)")
    logger.info(f"🎯 Hedef Video Sayısı: {video_count}")
    logger.info(f"⏱️ Yayın Aralığı: Her {interval_hours} Saatte Bir")
    logger.info(f"🌐 Dil: {lang.upper()} (SportStory Global)")
    if watch:
        logger.info("👀 Nöbetçi Modu (Watch): AKTİF (Kota dolduğunda nöbette bekler)")
    logger.info("=" * 65)

    orchestrator = MasterOrchestrator()
    successful_uploads = []
    produced_count = 0

    while produced_count < video_count:
        target_time = get_next_publish_time(interval_hours)
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
                record_scheduled_video(vid_id, publish_at_iso, local_time_str)
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
    parser.add_argument("--now", action="store_true", help="Hemen şimdi 1 otonom video üretir ve YouTube'a yükler")
    parser.add_argument("--topic", type=str, default=None, help="Belirli bir kriz/gündem konusu")
    parser.add_argument("--loop", type=float, metavar="HOURS", help="Sürekli otonom döngüyü başlatır (Örn: --loop 4)")
    parser.add_argument("--batch-schedule", type=int, metavar="COUNT", help="Kota dolana kadar N adet video üretip aralıklı olarak YouTube'a planlar (Örn: --batch-schedule 4)")
    parser.add_argument("--interval", type=float, default=12.0, help="Planlanan videolar arası saat aralığı (Varsayılan: 12.0)")
    parser.add_argument("--watch", action="store_true", default=True, help="Kotaya takılınca kapanmaz; bilgisayar açıkken kotada yer açıldıkça yüklemeye devam eder")
    parser.add_argument("--publish-curated", action="store_true", help="Küratörlü 5 başyapıt videoyu YouTube'a aktarır")
    parser.add_argument("--lang", type=str, choices=["en", "tr"], default="en", help="Yayın dili (Varsayılan: en)")
    args = parser.parse_args()

    if args.now:
        run_single_production(args.lang, topic=args.topic)
    elif args.batch_schedule:
        curated_batch_topics = [
            "Vinicius Jr: The $1 Billion Saudi Dilemma & Real Madrid Future",
            "Lyon: John Textor's 500M Debt Crisis & Ligue 1 Relegation Threat",
            "Inter Milan: Oaktree Capital's Takeover From Suning Over 400M Debt",
            "Aston Villa: PSR Red Line & Unai Emery's 100M Emergency Fire Sale",
            "Anzhi Makhachkala: Suleyman Kerimov's Billion-Dollar Fire Sale Disaster",
            "Deportivo La Coruna: The €160M Super Depor Debt Hangover",
            "Boavista: The Portuguese Giant's Rapid Crash From Champions League"
        ] if args.lang == "en" else [
            "Manchester City: 115 Kural İhlali ve Küme Düşme Davası",
            "Vinicius Jr: 1 Milyar Dolarlık Suudi Teklifi ve Real Madrid İkilemi",
            "Lyon: John Textor'ın 500 Milyon Euroluk Borcu ve Küme Düşme Tehlikesi",
            "Inter Milan: Suning'in 400 Milyonluk Borcu ve Oaktree Fonunun Kulübe El Koyması",
            "Aston Villa: 100 Milyonluk Finansal Kural Çıkmazı ve Acil Oyuncu Satışı",
            "Anzhi: Bir Milyar Dolarlık Rüyanın Sonu ve Dağıstan Fiyaskosu",
            "Deportivo La Coruna: Şampiyonlar Ligi Yarı Finalinden 3. Lige Çöküş"
        ]
        run_batch_schedule(args.batch_schedule, args.interval, args.lang, watch=args.watch, topics=curated_batch_topics)
    elif args.loop:
        run_continuous_loop(args.loop, args.lang)
    elif args.publish_curated:
        publish_curated_archive(args.lang)
    else:
        print("\n" + "=" * 65)
        print("🤖 SPORTSTORY OTONOM ÜRETİM VE YAYIN KONTROL PANELİ (TR & EN)")
        print("=" * 65)
        print("Kullanım Seçenekleri:")
        print("  1. Hemen Şimdi 1 Türkçe Video Üret & Yayınla:")
        print("     python autopilot.py --now --lang tr")
        print()
        print("  2. Hemen Şimdi 1 Global (EN) Video Üret & Yayınla:")
        print("     python autopilot.py --now --lang en")
        print()
        print("  3. Türkçe Kanal İçin Toplu Planlama (Örn: 4 video, 12 saatte bir):")
        print("     python autopilot.py --batch-schedule 4 --interval 12 --lang tr")
        print()
        print("  4. Global Kanal İçin Toplu Planlama:")
        print("     python autopilot.py --batch-schedule 4 --interval 12 --lang en")
        print()
        print("  5. Sürekli Otonom Döngü (Örn: Her 12 Saatte Bir):")
        print("     python autopilot.py --loop 12 --lang tr")
        print()
        print("  6. YouTube Kanallarını Yetkilendir (TR & EN):")
        print("     python authenticate_youtube.py --status")
        print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
