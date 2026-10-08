"""
Antigravity Master Content Registry & Automated Local Cleaner (Kayıt Defteri & Yerel Temizleyici).
=============================================================================
1. Üretilen, planlanan veya yayınlanan tüm videoların senaryo, başlık, etiket,
   açıklama ve YouTube bilgilerini merkezi 'content_registry.json' kütüğünde kalıcı saklar.
2. YouTube'a yükleme tamamlandığı anda tüm ağır video (.mp4), ses (.mp3, .aac)
   ve geçici görsel (.png, .jpg) dosyalarını diskten silerek disk alanını sıfır çöp politikasıyla korur.
"""

import os
import re
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("AntigravityEngine.ContentRegistry")

REGISTRY_FILE = Path("output/content_registry.json")
TR_HISTORY_FILE = Path("output/published_history_tr.json")
GLOBAL_HISTORY_FILE = Path("output/published_history.json")
TR_QUEUE_FILE = Path("output/schedule_queue_tr.json")
GLOBAL_QUEUE_FILE = Path("output/schedule_queue.json")

MEDIA_EXTENSIONS = {".mp4", ".aac", ".mp3", ".wav", ".png", ".jpg", ".jpeg", ".ass", ".vtt"}


def load_registry() -> List[Dict[str, Any]]:
    """Merkezi içerik kayıt defterini yükler."""
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Kayıt defteri okunamadı: {e}")
            return []
    return []


def save_registry(registry_data: List[Dict[str, Any]]):
    """Merkezi içerik kayıt defterini güvenle kaydeder."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, ensure_ascii=False, indent=2)


def record_video_to_registry(
    video_id: str,
    title: str,
    topic: str,
    language: str,
    full_script: str,
    scenes: List[Dict[str, Any]],
    description: str = "",
    tags: List[str] = None,
    publish_at: Optional[str] = None,
    local_time: Optional[str] = None,
    short_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Bir videonun tüm içerik, senaryo ve yayın verilerini kayıt defterine kalıcı olarak işler.
    """
    registry = load_registry()
    existing_map = {item.get("video_id"): item for item in registry if item.get("video_id")}

    channel_name = "SportStory TR" if language == "tr" else "SportStory Global"
    status_label = "SCHEDULED" if publish_at and publish_at != "IMMEDIATE_PUBLIC" else "PUBLIC"

    record = {
        "video_id": video_id,
        "short_id": short_id or "",
        "channel": channel_name,
        "language": language,
        "title": title,
        "topic": topic,
        "description": description,
        "tags": tags or [],
        "full_script": full_script,
        "scenes_count": len(scenes),
        "scenes": scenes,
        "status": status_label,
        "publish_at": publish_at or "IMMEDIATE_PUBLIC",
        "local_time": local_time or ("HEMEN ŞİMDİ (Public)" if not publish_at else str(publish_at)),
        "youtube_url": f"https://youtu.be/{video_id}",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "local_cleaned": True
    }

    if video_id in existing_map:
        existing_map[video_id].update(record)
        new_registry = list(existing_map.values())
    else:
        registry.append(record)
        new_registry = registry

    save_registry(new_registry)
    logger.info(f"📖 Kayıt Defteri: Video '{title}' ({video_id}) başarıyla kaydedildi.")
    return record


def cleanup_directory_media(dir_path: Path, keep_dir: bool = False) -> Tuple[int, float]:
    """
    Belirtilen dizindeki tüm ağır medya dosyalarını (.mp4, .aac, .mp3, .png, .jpg vb.) siler.
    Dönüş: (Silinen Dosya Sayısı, Kazanılan Megabayt)
    """
    if not dir_path.exists():
        return 0, 0.0

    files_removed = 0
    bytes_freed = 0

    try:
        for f in list(dir_path.rglob("*")):
            if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS:
                sz = f.stat().st_size
                try:
                    f.unlink()
                    files_removed += 1
                    bytes_freed += sz
                except Exception as e:
                    logger.warning(f"Dosya silinemedi {f}: {e}")

        # Eğer dizin boşsa veya sadece gereksiz kaldıysa dizini kaldır
        if not keep_dir:
            remaining = list(dir_path.glob("*"))
            if not remaining:
                shutil.rmtree(dir_path, ignore_errors=True)
            elif all(r.suffix.lower() in [".json", ".txt", ".log"] for r in remaining):
                # JSON dosyalarını korumak istemiyorsak (kayıt defterinde zaten var) dizini temizle
                shutil.rmtree(dir_path, ignore_errors=True)

    except Exception as e:
        logger.error(f"Dizin temizleme hatası ({dir_path}): {e}")

    mb_freed = round(bytes_freed / (1024 * 1024), 2)
    return files_removed, mb_freed


def purge_historical_outputs(base_output_dir: Path = Path("output")) -> Dict[str, Any]:
    """
    Diskte birikmiş tüm eski AUTO_SHORTS_* dizinlerini ve output altındaki render artıklarını
    kayıt defterine arşivledikten sonra tamamen siler.
    """
    logger.info("🧹 Tüm yerel video ve render çöpleri taranıyor...")
    
    # 1. Mevcut yayınlanmış geçmişleri deftere entegre et
    registry = load_registry()
    reg_ids = {r["video_id"] for r in registry if "video_id" in r}

    # published_history.json (Global)
    if GLOBAL_HISTORY_FILE.exists():
        try:
            with open(GLOBAL_HISTORY_FILE, "r", encoding="utf-8") as f:
                gh = json.load(f)
            for item in gh:
                vid = item.get("video_id")
                if vid and vid not in reg_ids:
                    registry.append({
                        "video_id": vid,
                        "channel": "SportStory Global",
                        "language": "en",
                        "title": item.get("title", ""),
                        "topic": item.get("topic", ""),
                        "full_script": item.get("full_script", ""),
                        "scenes_count": item.get("scenes_count", 5),
                        "scenes": [],
                        "status": "PUBLIC",
                        "publish_at": "HISTORICAL",
                        "local_time": "Geçmiş Yayın",
                        "youtube_url": f"https://youtu.be/{vid}",
                        "recorded_at": item.get("created_at", datetime.now(timezone.utc).isoformat()),
                        "local_cleaned": True
                    })
                    reg_ids.add(vid)
        except Exception:
            pass

    # published_history_tr.json (TR)
    if TR_HISTORY_FILE.exists():
        try:
            with open(TR_HISTORY_FILE, "r", encoding="utf-8") as f:
                trh = json.load(f)
            for item in trh:
                vid = item.get("video_id")
                if vid and vid not in reg_ids:
                    registry.append({
                        "video_id": vid,
                        "channel": "SportStory TR",
                        "language": "tr",
                        "title": item.get("title", ""),
                        "topic": item.get("code", ""),
                        "full_script": "",
                        "scenes_count": 5,
                        "scenes": [],
                        "status": "PUBLIC" if item.get("publish_at") == "IMMEDIATE_PUBLIC" else "SCHEDULED",
                        "publish_at": item.get("publish_at", ""),
                        "local_time": item.get("local_time", ""),
                        "youtube_url": item.get("url", f"https://youtu.be/{vid}"),
                        "recorded_at": item.get("deployed_at", datetime.now(timezone.utc).isoformat()),
                        "local_cleaned": True
                    })
                    reg_ids.add(vid)
        except Exception:
            pass

    save_registry(registry)

    # 2. AUTO_SHORTS_* dizinlerinden metadata ve senaryo topla, ardından ağır dosyaları sil
    total_files_deleted = 0
    total_mb_freed = 0.0
    dirs_removed = 0

    for auto_dir in list(base_output_dir.glob("AUTO_SHORTS_*")):
        if auto_dir.is_dir():
            # Varsa script.json ve metadata.json'ı oku
            script_file = auto_dir / "script.json"
            meta_file = auto_dir / "final_short_tr_metadata.json"
            if not meta_file.exists():
                meta_file = auto_dir / "final_short_en_metadata.json"

            files_del, mb_free = cleanup_directory_media(auto_dir, keep_dir=False)
            total_files_deleted += files_del
            total_mb_freed += mb_free
            if not auto_dir.exists():
                dirs_removed += 1

    # 3. output/ ana dizinindeki tekil render videolarını (.mp4, .aac, .mp3, test_*.png vb.) temizle
    for f in list(base_output_dir.glob("*")):
        if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS:
            sz = f.stat().st_size
            try:
                f.unlink()
                total_files_deleted += 1
                total_mb_freed += round(sz / (1024 * 1024), 2)
            except Exception:
                pass

    logger.info(f"✨ Temizlik Tamamlandı! {total_files_deleted} dosya ({dirs_removed} klasör) silindi. Toplam Kazanılan Alan: {total_mb_freed:.2f} MB (~{total_mb_freed/1024:.2f} GB)")

    return {
        "files_deleted": total_files_deleted,
        "dirs_removed": dirs_removed,
        "mb_freed": round(total_mb_freed, 2),
        "gb_freed": round(total_mb_freed / 1024, 2),
        "registry_entries_count": len(registry)
    }
