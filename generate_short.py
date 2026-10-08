import argparse
import os
import re
import time
import random
import subprocess
import json
from pathlib import Path
from PIL import Image, ImageDraw
import imageio_ffmpeg

from engine.agents.trend_scout_agent import TrendScoutAgent
from engine.agents.scriptweaver_agent import ScriptWeaverAgent
from engine.agents.auto_deploy_agent import AutoDeployAgent
from engine.agents.voice_audit_agent import TurkishVoiceAuditAgent
from engine.guards.content_guard import get_content_guard

try:
    from engine.workers.audio_worker import AudioWorker
    from engine.subtitles import KineticSubtitleRenderer, get_subtitle_font
    WORKERS_READY = True
except ImportError as e:
    WORKERS_READY = False
    print(f"Uyarı: İşçiler yüklenemedi. Hata: {e}")

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


def create_channel_branding_badge(width=1080, height=1920, lang: str = "en") -> Image.Image:
    """
    Renders the official SportStory Bullish Shield glass badge in the top-left safe zone.
    Guarantees crisp brand presence on every frame of the video.
    """
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    icon_path = Path("assets/branding/brand_icon_clean.png")
    if not icon_path.exists():
        icon_path = Path("assets/branding/brand_icon_transparent_hd.png")

    x1, y1 = 64, 110
    badge_h = 56
    icon_size = 38

    font = get_subtitle_font(size=24, bold=True)
    text = "SPORTSTORY TR" if lang == "tr" else "SPORTSTORY"
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]

    badge_w = icon_size + tw + 48
    x2 = x1 + badge_w
    y2 = y1 + badge_h

    # Luxury Glass Pill: Dark obsidian with soft luminous border
    draw.rounded_rectangle([x1, y1, x2, y2], radius=28, fill=(11, 17, 32, 195), outline=(255, 255, 255, 60), width=2)

    if icon_path.exists():
        try:
            icon_img = Image.open(icon_path).convert("RGBA")
            icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            r, g, b, a = icon_img.split()
            a = a.point(lambda p: int(p * 0.95))
            icon_img.putalpha(a)
            icon_x = x1 + 12
            icon_y = y1 + (badge_h - icon_size) // 2
            overlay.paste(icon_img, (icon_x, icon_y), icon_img)
            text_x = icon_x + icon_size + 10
        except Exception:
            text_x = x1 + 20
    else:
        text_x = x1 + 20

    text_y = y1 + (badge_h // 2)
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 250), anchor="lm")

    # Golden accent dot
    dot_x = text_x + tw + 10
    draw.ellipse([dot_x - 3, text_y - 3, dot_x + 3, text_y + 3], fill=(250, 204, 21, 255))

    return overlay


class MasterOrchestrator:
    def __init__(self):
        self.scout = TrendScoutAgent()
        self.weaver = ScriptWeaverAgent()
        self.deployer = AutoDeployAgent()
        self.guard = get_content_guard()
        self.voice_auditor = TurkishVoiceAuditAgent()

        if WORKERS_READY:
            self.audio_worker = AudioWorker()

    def run_autonomous_pipeline(self, lang: str = "en", publish_at: str = None, topic: str = None) -> str:
        print("\n" + "="*65)
        print(f"🎬 SPORTSTORY VİRAL OTONOM MOTOR BAŞLADI | DİL: {lang.upper()}")
        print("="*65)
        
        # Retro Futbol Modu (Özel PES 6 Nostalji Futbol Oyunları)
        retro_bgs = ["bg_pes_retro.mp4", "bg_pes_milan.mp4"]
        valid_retro_bgs = [bg for bg in retro_bgs if os.path.exists(bg)]
        master_bg = random.choice(valid_retro_bgs) if valid_retro_bgs else "bg_pes_retro.mp4"

        if not os.path.exists(master_bg):
            print(f"❌ HATA: Arka plan videosu bulunamadı! {master_bg} eksik.")
            return None

        # [Deduplication Guard] Mükerrer olmayan benzersiz konu ve senaryo üret
        chosen_topic = None
        script = None
        full_text = ""
        short_id = None
        max_attempts = 5

        for attempt in range(1, max_attempts + 1):
            cand_topic = topic if topic else self.scout.find_latest_scandal(lang=lang)
            cand_short_id = f"AUTO_SHORTS_{int(time.time())}"
            print(f"\n[1/6] 🔍 Araştırma Tamamlandı (Deneme #{attempt}): {cand_topic}")
            
            cand_script = self.weaver.generate_script(cand_topic, cand_short_id)
            texts = [s.text_en if lang == 'en' else s.text_tr for s in cand_script.scenes]
            cand_full_text = " ".join(texts)

            # Senaryo mükerrerlik denetimi
            is_dup, reason, sim = self.guard.check_script_duplicate(cand_full_text, threshold=0.70)
            if is_dup and not topic:
                print(f"⚠️ [ContentGuard]: Senaryo mükerrer ({reason})! Yeni konu aranıyor (Deneme {attempt}/{max_attempts})...")
                time.sleep(1)
                continue

            chosen_topic = cand_topic
            script = cand_script
            full_text = cand_full_text
            short_id = cand_short_id
            break

        topic = chosen_topic
        if not script:
            print(f"❌ HATA: {max_attempts} denemede benzersiz bir senaryo üretilemedi. İşlem durduruldu.")
            return None

        output_dir = Path(f"output/{short_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"[2/6] ✍️ Derinlikli Belgesel Senaryosu Hazırlandı ({len(script.scenes)} Sahne).")
        with open(output_dir / "script.json", "w", encoding="utf-8") as sf:
            json.dump(script.dict(), sf, ensure_ascii=False, indent=2)
        
        print("\n[3/6] ⚙️ Viral Render Süreci Başlıyor...")
        
        final_video_path = output_dir / f"final_short_{lang}.mp4"
        raw_voice_path = output_dir / f"raw_voice_{lang}.mp3"
        master_audio_path = output_dir / f"master_audio_{lang}.aac"
        bg_video_path = output_dir / "bg_gameplay.mp4"
        
        if WORKERS_READY:
            try:
                print("🎧 [AudioWorker] Ses ve Sidechain çalışıyor...")
                texts = [s.text_en if lang == 'en' else s.text_tr for s in script.scenes]
                raw_script_text = " ".join(texts)

                # Türkçe Spiker Denetimi ve Fonetik Normalizasyon (TurkishVoiceAuditAgent)
                if lang == "tr":
                    print("🕵️ [TurkishVoiceAuditAgent] Türkçe spiker metni denetleniyor ve fonetik uyarlama yapılıyor...")
                    audited_speech_text, pre_report = self.voice_auditor.audit_and_correct_script(raw_script_text, language="tr")
                    speech_to_synthesize = audited_speech_text
                    print(f"✅ [TurkishVoiceAuditAgent] Giriş Denetimi Tamamlandı! Risk Skoru: {pre_report.get('risk_score')}/100, Düzeltme: {pre_report.get('corrections_count')}")
                else:
                    speech_to_synthesize = raw_script_text
                    pre_report = {"language": "en", "status": "PASSED_NON_TR"}

                voice_name = "en-US-ChristopherNeural" if lang == "en" else "tr-TR-AhmetNeural"
                rate_val = "+0%" if lang == "en" else "+3%"
                _, aligned_words = self.audio_worker.generate_voiceover(
                    script=speech_to_synthesize,
                    target_path=str(raw_voice_path),
                    voice=voice_name,
                    rate=rate_val,
                    language=lang
                )
                self.audio_worker.mix_with_ducking(str(raw_voice_path), None, str(master_audio_path))

                total_duration = aligned_words[-1]["end"] + 1.2 if aligned_words else 15.0

                # Türkçe Akustik & Ritim QA Denetimi
                if lang == "tr":
                    post_report = self.voice_auditor.audit_spoken_audio(aligned_words, total_duration)
                    audit_report_path = output_dir / "voice_audit_report.json"
                    self.voice_auditor.export_audit_report(pre_report, post_report, str(audit_report_path))
                
                is_retro = any(tag in master_bg.lower() for tag in ["pes", "we", "retro", "fifa", "football"])
                game_title = "PES 6 / Winning Eleven Nostalji Maçı" if is_retro else "Arka Plan Videosu"
                print(f"⚽ [RetroFootballEngine] {game_title} Fonundan ({master_bg}) {total_duration:.1f}s Rastgele Kesim Yapılıyor...")
                
                # Video süresini dinamik hesapla
                def get_video_duration(path_str):
                    try:
                        probe_cmd = [
                            "ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", path_str
                        ]
                        return float(subprocess.check_output(probe_cmd, stderr=subprocess.DEVNULL).decode().strip())
                    except Exception:
                        return 500.0

                total_bg_len = get_video_duration(master_bg)
                max_start = max(10, int(total_bg_len - total_duration - 15))
                random_start = random.randint(15, min(max_start, 500))
                
                cut_cmd = [
                    FFMPEG_EXE, "-y", "-nostdin", "-ss", str(random_start), "-t", str(total_duration), "-i", master_bg,
                    "-vf", "crop=ih*(9/16):ih,scale=1080:1920", "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", str(bg_video_path)
                ]
                subprocess.run(cut_cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                print("📝 [SubtitleWorker] Kinetik ASS altyazılar işleniyor...")
                subtitle_renderer = KineticSubtitleRenderer(aligned_words, width=1080, height=1920)
                branding_overlay = create_channel_branding_badge(width=1080, height=1920, lang=lang)

                print("🎞️ [RenderCompiler] Tam Ekran FFmpeg Montajlanıyor...")
                fps = 30
                
                read_cmd = [FFMPEG_EXE, "-nostdin", "-i", str(bg_video_path), "-f", "image2pipe", "-pix_fmt", "rgb24", "-vcodec", "rawvideo", "-"]
                write_cmd = [
                    FFMPEG_EXE, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-s", "1080x1920", "-pix_fmt", "rgb24", "-r", str(fps),
                    "-i", "-", "-i", str(master_audio_path),
                    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest",
                    str(final_video_path)
                ]
                
                reader = subprocess.Popen(read_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                writer = subprocess.Popen(write_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
                
                frame_size = 1080 * 1920 * 3
                current_time = 0.0
                
                while True:
                    raw_frame = reader.stdout.read(frame_size)
                    if len(raw_frame) < frame_size:
                        break
                        
                    frame_img = Image.frombytes("RGB", (1080, 1920), raw_frame).convert("RGBA")
                    # 1. Overlay Channel Branding Watermark
                    frame_img = Image.alpha_composite(frame_img, branding_overlay)
                    # 2. Overlay Kinetic Subtitles
                    sub_overlay = subtitle_renderer.render_overlay(current_time)
                    # Retro oyun çim renginin altyazıları boğmaması için %35 kontrast cam perde
                    dark_overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 85))
                    frame_img = Image.alpha_composite(frame_img, dark_overlay)
                    final_frame = Image.alpha_composite(frame_img, sub_overlay).convert("RGB")
                    
                    try:
                        writer.stdin.write(final_frame.tobytes())
                    except (BrokenPipeError, OSError):
                        break
                    current_time += 1.0 / fps
                    
                try:
                    reader.stdout.close()
                except Exception:
                    pass
                try:
                    writer.stdin.close()
                except Exception:
                    pass
                writer.wait()
                reader.wait()
                print(f"✅ Render başarıyla tamamlandı: {final_video_path.name}")
                
            except Exception as e:
                print(f"❌ Render işçileri çalışırken bir hata oluştu: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n[6/6] 🚀 YouTube Yayın Süreci Başlıyor...")
        if not os.path.exists(str(final_video_path)) or os.path.getsize(str(final_video_path)) < 100000:
            print(f"\n[KAYIT DIŞI HATA]: {final_video_path} dosyası diskte YOK veya geçersiz/boş. Yükleme iptal.")
            return None
            
        # YouTube Metadata Dosyası (Dil & Viral SEO Garantili)
        meta_file = output_dir / f"final_short_{lang}_metadata.json"
        def smart_short_title(raw_text: str, lang_code: str) -> str:
            # Temizleme: Mevcut hashtag'leri çıkar
            clean = re.sub(r'#\w+', '', raw_text).strip()
            clean = re.sub(r'\s+', ' ', clean).strip()
            suffix = " #shorts"
            target_max = 50
            if len(clean) + len(suffix) <= target_max:
                return f"{clean}{suffix}"
            # Kelime sınırından böl
            cut = clean[:target_max - len(suffix)]
            if " " in cut:
                cut = cut.rsplit(" ", 1)[0]
            cut = cut.rstrip(" .,!?:;-")
            emoji = " 💸" if "💸" not in cut and "🚨" not in cut else ""
            return f"{cut}{emoji}{suffix}"

        if lang == 'en':
            raw_title = getattr(script, 'title_en', None) or f"{topic} | Scandal 😱 #shorts"
            video_title = smart_short_title(raw_title, 'en')

            base_desc = getattr(script, 'description_en', None) or f"{topic}\n\nThe untold financial collapse and secret debts behind the headlines."
            if "Subscribe to" not in base_desc:
                video_desc = (
                    f"{base_desc.strip()}\n\n"
                    f"💬 What do you think about this? Drop your thoughts below! 👇\n\n"
                    f"🔔 Subscribe to @SportStory for daily football finance & scandal stories.\n\n"
                    f"#shorts #football #soccer #sportsfinance #scandal #championsleague"
                )
            else:
                video_desc = base_desc

            script_tags = getattr(script, 'tags_en', None) or []
            fallback_tags = [
                "shorts", "football", "soccer", "sports finance", "football scandal",
                "financial fair play", "football debt", "uefa ffp", "soccer stories",
                "sportstory", "premier league", "champions league", "viral shorts"
            ]
            video_tags = list(dict.fromkeys(script_tags + fallback_tags))[:20]
        else:
            raw_title = getattr(script, 'title_tr', None) or f"{topic} 😱💸 #shorts"
            video_title = smart_short_title(raw_title, 'tr')
            base_desc = getattr(script, 'description_tr', None) or f"{topic}\n\nKulüplerin arka plandaki mali çöküşleri ve skandalları."
            if "abone" not in base_desc.lower():
                video_desc = (
                    f"{base_desc.strip()}\n\n"
                    f"💬 Sen bu konu hakkında ne düşünüyorsun? Yorumlara yaz! 👇\n\n"
                    f"🔔 Futbol skandalları ve kulüp krizleri için @SportStoryTR kanalına abone olun.\n\n"
                    f"#shorts #futbol #spor #skandal #finans #transfer"
                )
            else:
                video_desc = base_desc

            script_tags = getattr(script, 'tags_tr', None) or []
            fallback_tags = [
                "shorts", "futbol", "spor", "skandal", "finans", "transfer",
                "sportstory", "şampiyonlarligi", "premierlig", "viral"
            ]
            video_tags = list(dict.fromkeys(script_tags + fallback_tags))[:20]

        with open(meta_file, "w", encoding="utf-8") as mf:
            json.dump({
                "title": video_title,
                "description": video_desc,
                "tags": video_tags
            }, mf, ensure_ascii=False, indent=2)

        # ContentGuard Yükleme Öncesi Kesin Kapı Kontrolü (Master Gatekeeper)
        can_upload, guard_reason = self.guard.can_upload_to_youtube(video_title, full_text)
        if not can_upload:
            print(f"\n🛑 [ContentGuard REDDİ]: YouTube yüklemesi durduruldu! Sebep: {guard_reason}")
            return None

        vid_id = self.deployer.deploy(str(final_video_path), lang, metadata_path=str(meta_file), publish_at=publish_at)
        if vid_id:
            self.guard.record_video(
                video_id=vid_id,
                topic=topic,
                title=video_title,
                script_text=full_text,
                scenes=[s.dict() for s in script.scenes]
            )
            print("\n🎉 VİRAL GÖREV BAŞARILI!\n")
            return vid_id
        else:
            print("\n⚠️ Yükleme tamamlanamadı veya reddedildi.\n")
            return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SportStory Short Generator")
    parser.add_argument("--auto", action="store_true", help="Tek bir otonom video üretir ve yükler")
    parser.add_argument("--topic", type=str, default=None, help="Belirli bir kriz/gündem konusu")
    parser.add_argument("--batch", type=int, default=None, help="N adet videoyu aralıklı planlayarak YouTube'a yükler (Örn: --batch 10)")
    parser.add_argument("--interval", type=float, default=12.0, help="Planlanan videolar arasındaki saat aralığı (Varsayılan: 12.0)")
    parser.add_argument("--watch", action="store_true", default=True, help="Kotaya takılınca kapanmaz; bilgisayar açıkken kotada yer açıldıkça yüklemeye devam eder")
    parser.add_argument("--publish-at", type=str, default=None, help="Belirli bir UTC ISO zamanı (YYYY-MM-DDTHH:MM:SSZ)")
    parser.add_argument("--lang", type=str, choices=['tr', 'en'], default='en')
    args = parser.parse_args()

    if args.batch:
        from autopilot import run_batch_schedule
        run_batch_schedule(video_count=args.batch, interval_hours=args.interval, lang=args.lang, watch=args.watch)
    elif args.auto:
        MasterOrchestrator().run_autonomous_pipeline(args.lang, publish_at=args.publish_at, topic=args.topic)


