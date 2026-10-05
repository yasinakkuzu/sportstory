"""
RenderCompilerWorker: FFmpeg Tabanlı Montaj, Ken-Burns Hareketi, Cross-Dissolve ve Canlı Altyazı Motoru.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Optional
from PIL import Image, ImageDraw

import imageio_ffmpeg
import numpy as np

from engine.compositor import WIDTH, HEIGHT
from engine.subtitles import KineticSubtitleRenderer

logger = logging.getLogger("AntigravityEngine.RenderCompilerWorker")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class RenderCompilerWorker:
    """FFmpeg Tabanlı Montaj, Dinamik Ken-Burns Hareketi ve Altyazı Render Motoru"""

    @staticmethod
    def render_final_short(
        image_paths: List[str],
        scene_durations: List[float],
        audio_path: str,
        subtitle_renderer: KineticSubtitleRenderer,
        output_path: str,
        total_duration: float
    ) -> str:
        """
        Sahneleri Ken-Burns yakınlaşması, akıcı cross-dissolve geçişleri,
        YouTube Safe-Zone altyazı katmanı ve canlı ilerleme çubuğuyla 1080x1920 MP4 olarak derler.
        """
        p_out = Path(output_path)
        p_out.parent.mkdir(parents=True, exist_ok=True)
        temp_video = p_out.parent / f"temp_{p_out.stem}_video.mp4"
        stderr_log = p_out.parent / f"ffmpeg_{p_out.stem}_stderr.log"

        fps = 30
        ffmpeg_cmd = [
            FFMPEG_EXE,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{WIDTH}x{HEIGHT}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "faster",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            str(temp_video)
        ]

        logger.info(f"🎬 9:16 Video Render Başlatılıyor ({len(image_paths)} sahne, {total_duration:.1f}s)...")

        scenes = [Image.open(p).convert("RGB") for p in image_paths]
        num_scenes = len(scenes)

        with open(stderr_log, "wb") as err_f:
            proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=err_f)
            try:
                current_time = 0.0
                for scene_idx, (scene_img, dur) in enumerate(zip(scenes, scene_durations)):
                    num_frames = int(dur * fps)
                    scene_np = np.array(scene_img)

                    next_scene_np = None
                    if scene_idx < num_scenes - 1:
                        next_scene_np = np.array(scenes[scene_idx + 1])

                    zoom_in = (scene_idx % 2 == 0)
                    start_scale = 1.00 if zoom_in else 1.04
                    end_scale = 1.04 if zoom_in else 1.00
                    pil_source = Image.fromarray(scene_np)
                    fade_frames = 6 # 0.2s akıcı geçiş

                    for frame_idx in range(num_frames):
                        progress = frame_idx / float(max(1, num_frames - 1))
                        scale = start_scale + (end_scale - start_scale) * progress

                        cw = int(WIDTH / scale)
                        ch = int(HEIGHT / scale)
                        left = (WIDTH - cw) // 2
                        top = (HEIGHT - ch) // 2
                        cropped = pil_source.crop((left, top, left + cw, top + ch))
                        frame_img = cropped.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)

                        # Sonraki sahneye yumuşak geçiş
                        if next_scene_np is not None and frame_idx >= (num_frames - fade_frames):
                            alpha = (frame_idx - (num_frames - fade_frames) + 1) / float(fade_frames + 1)
                            frame_img = Image.blend(frame_img, Image.fromarray(next_scene_np), alpha=alpha)

                        frame_rgba = frame_img.convert("RGBA")

                        # Üst İlerleme Çubuğu (Canlı Progress Bar)
                        bar_draw = ImageDraw.Draw(frame_rgba)
                        global_prog = min(1.0, current_time / float(total_duration))
                        bar_w = int(WIDTH * global_prog)
                        bar_draw.rectangle([0, 0, WIDTH, 8], fill=(30, 41, 59, 180))
                        if bar_w > 0:
                            bar_draw.rectangle([0, 0, bar_w, 8], fill=(56, 189, 248, 255))

                        # Safe-Zone Kinetik Altyazı Katmanı
                        sub_overlay = subtitle_renderer.render_overlay(current_time)
                        final_frame = Image.alpha_composite(frame_rgba, sub_overlay).convert("RGB")

                        proc.stdin.write(final_frame.tobytes())
                        current_time += (1.0 / fps)

                proc.stdin.close()
                proc.wait()

                if proc.returncode != 0:
                    with open(stderr_log, "r", encoding="utf-8", errors="ignore") as rf:
                        err_text = rf.read()
                    raise RuntimeError(f"FFmpeg render hatası ({proc.returncode}): {err_text}")

            except Exception as e:
                if proc.poll() is None:
                    proc.kill()
                raise e
            finally:
                if stderr_log.exists():
                    try:
                        stderr_log.unlink()
                    except Exception:
                        pass

        # Nihai Muxing (Görüntü + Ducked Stereo Ses)
        logger.info("📦 Video ve Audio Muxing Yapılıyor...")
        mux_cmd = [
            FFMPEG_EXE, "-y",
            "-nostdin",
            "-i", str(temp_video),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(p_out)
        ]
        subprocess.run(mux_cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        if not p_out.exists() or p_out.stat().st_size < 100000:
            raise RuntimeError(f"Nihai video renderı başarısız veya bozuk: {p_out} (Boyut: {p_out.stat().st_size if p_out.exists() else 0} bytes)")

        if temp_video.exists():
            try:
                temp_video.unlink()
            except Exception:
                pass

        logger.info(f"🏆 Nihai 9:16 Shorts Videosu Hazır: {p_out}")
        return str(p_out)
