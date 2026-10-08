#!/usr/bin/env python3
"""
SportStory TR Launch Deployer:
Diskte hazır bekleyen 5 Türkçe Master Video'yu SportStory TR kanalına yükler:
- 1. Video (Barcelona) ➡️ HEMEN ŞİMDİ (Public / Herkese Açık)
- 2. Video (Chelsea)   ➡️ Bugün 20:00 (Planlanmış)
- 3. Video (Man City)  ➡️ Yarın 08:00 (Planlanmış)
- 4. Video (PSG)       ➡️ Yarın 20:00 (Planlanmış)
- 5. Video (Real)      ➡️ Cumartesi 08:00 (Planlanmış)
"""

import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from engine.agents.auto_deploy_agent import AutoDeployAgent

LAUNCH_PLAN = [
    {
        "code": "SHORTS_001",
        "video_path": "output/SHORTS_001_final_short.mp4",
        "meta_path": "output/shorts_001_metadata.json",
        "publish_at": None,
        "local_label": "HEMEN ŞİMDİ (Public / Herkese Açık)"
    },
    {
        "code": "SHORTS_002",
        "video_path": "output/SHORTS_002_final_short.mp4",
        "meta_path": "output/shorts_002_metadata.json",
        "publish_at": "2026-10-08T17:00:00Z",
        "local_label": "Bugün (8 Ekim) 20:00"
    },
    {
        "code": "SHORTS_003",
        "video_path": "output/SHORTS_003_final_short.mp4",
        "meta_path": "output/shorts_003_metadata.json",
        "publish_at": "2026-10-09T05:00:00Z",
        "local_label": "Yarın (9 Ekim) 08:00"
    },
    {
        "code": "SHORTS_004",
        "video_path": "output/SHORTS_004_final_short.mp4",
        "meta_path": "output/shorts_004_metadata.json",
        "publish_at": "2026-10-09T17:00:00Z",
        "local_label": "Yarın (9 Ekim) 20:00"
    },
    {
        "code": "SHORTS_005",
        "video_path": "output/SHORTS_005_final_short.mp4",
        "meta_path": "output/shorts_005_metadata.json",
        "publish_at": "2026-10-10T05:00:00Z",
        "local_label": "Cumartesi (10 Ekim) 08:00"
    }
]

QUEUE_TR_FILE = Path("output/schedule_queue_tr.json")
HISTORY_TR_FILE = Path("output/published_history_tr.json")


def load_json(p: Path):
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 65)
    print("🚀 SPORTSTORY TÜRKÇE (TR) KANAL LANSMANI BAŞLIYOR!")
    print("=" * 65)

    agent = AutoDeployAgent(lang="tr")
    queue_data = load_json(QUEUE_TR_FILE)
    history_data = load_json(HISTORY_TR_FILE)

    deployed_count = 0
    results = []

    for idx, item in enumerate(LAUNCH_PLAN, 1):
        v_path = item["video_path"]
        m_path = item["meta_path"]
        publish_at = item["publish_at"]
        local_label = item["local_label"]

        with open(m_path, "r", encoding="utf-8") as mf:
            mjson = json.load(mf)
        title = mjson.get("snippet", {}).get("title", item["code"])

        print(f"\n🎬 [{idx}/5] Yükleniyor: {title}")
        print(f"⏱️ Plan: {local_label}")

        try:
            yt_id = agent.deploy(
                video_path=v_path,
                lang="tr",
                metadata_path=m_path,
                publish_at=publish_at
            )

            if yt_id:
                deployed_count += 1
                record = {
                    "video_id": yt_id,
                    "code": item["code"],
                    "title": title,
                    "publish_at": publish_at or "IMMEDIATE_PUBLIC",
                    "local_time": local_label,
                    "url": f"https://youtu.be/{yt_id}",
                    "deployed_at": datetime.now(timezone.utc).isoformat()
                }
                results.append(record)

                if publish_at:
                    queue_data.append({
                        "id": yt_id,
                        "title": title,
                        "publish_at": publish_at,
                        "local_time": local_label
                    })
                history_data.append(record)

                save_json(QUEUE_TR_FILE, queue_data)
                save_json(HISTORY_TR_FILE, history_data)
                print(f"✅ Başarılı! Link: https://youtu.be/{yt_id}")

            # Küçük bir nefes payı (API flood engelleme)
            time.sleep(3)

        except Exception as e:
            print(f"❌ Video yüklenirken hata oluştu: {e}")
            break

    print("\n" + "=" * 65)
    print(f"🎉 LANSMAN TAMAMLANDI: {deployed_count}/{len(LAUNCH_PLAN)} Video Yüklendi!")
    print("=" * 65)
    for r in results:
        status_txt = "🔴 CANLI (Public)" if r["publish_at"] == "IMMEDIATE_PUBLIC" else f"📅 {r['local_time']}"
        print(f" - [{status_txt}] {r['title']}")
        print(f"   Link: {r['url']}")
    print("=" * 65)


if __name__ == "__main__":
    main()
