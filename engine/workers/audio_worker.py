"""
AudioWorker: Seslendirme, TTS Punctuation Softening, ve Dinamik Sidechain Audio Ducking Motoru.
"""

import os
import re
import sys
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import edge_tts
import imageio_ffmpeg
import numpy as np

from engine.subtitles import prepare_speech_script, align_punctuations
from engine.audio_mixer import generate_modern_sports_beat, save_wav

logger = logging.getLogger("AntigravityEngine.AudioWorker")
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


def soften_tts_punctuation(script: str) -> str:
    """
    Spikerin ani tizleşmesini, bağırmasını veya heceleri gereksiz uzatmasını önlemek için
    noktalama işaretlerini sakin belgesel tonuna göre yumuşatır.
    - ';' -> ',' (uzun duraklama ve tonlama kırılmasını önler)
    - '!' -> '.' (çığlık atmasını ve aşırı perde sıçramasını önler)
    - '...' -> '.'
    """
    s = script.replace(";", ",")
    s = s.replace("!", ".")
    s = s.replace("...", ".")
    s = re.sub(r'\s+', ' ', s).strip()
    return s


class AudioWorker:
    """Seslendirme, TTS ve Dinamik Audio Ducking Motoru"""

    def __init__(self, api_key: Optional[str] = None):
        self.eleven_api_key = api_key or os.getenv("ELEVEN_API_KEY", "")

    async def _generate_edge_tts(
        self,
        original_script: str,
        target_path: Path,
        voice: Optional[str] = None,
        rate: str = "+0%",
        language: str = "tr"
    ) -> List[Dict[str, Any]]:
        """Edge-TTS ile fonetik uyarlamalı ve yumuşatılmış ses üretir."""
        if not voice:
            voice = "en-US-ChristopherNeural" if language == "en" else "tr-TR-AhmetNeural"

        if language == "tr":
            phonetic_script = prepare_speech_script(original_script)
        else:
            phonetic_script = original_script

        softened_script = soften_tts_punctuation(phonetic_script)

        logger.info(f"🎙️ Edge-TTS Seslendirme Üretiliyor ({voice}, Dil: {language}, Hız: {rate}, Yumuşatılmış Ton)...")
        comm = edge_tts.Communicate(softened_script, voice, rate=rate, boundary="WordBoundary")

        spoken_words = []
        raw_temp = target_path.parent / f"raw_{target_path.name}"

        with open(raw_temp, "wb") as af:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    af.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start_sec = chunk["offset"] / 10000000.0
                    dur_sec = chunk["duration"] / 10000000.0
                    text = chunk["text"].strip()
                    parts = text.split()
                    if len(parts) <= 1:
                        spoken_words.append({
                            "word": text,
                            "start": start_sec,
                            "end": start_sec + dur_sec
                        })
                    else:
                        total_len = sum(len(p) for p in parts)
                        cur_t = start_sec
                        for p in parts:
                            p_dur = dur_sec * (len(p) / total_len)
                            spoken_words.append({
                                "word": p,
                                "start": cur_t,
                                "end": cur_t + p_dur
                            })
                            cur_t += p_dur

        # Altyazı için orijinal yazılış ve noktalama ile eşleştirme
        aligned_words = align_punctuations(spoken_words, original_script)

        # Spiker sesini yayın seviyesinde normalize et (acompressor + loudnorm)
        filter_voice = (
            "aformat=sample_rates=44100:channel_layouts=stereo,"
            "acompressor=threshold=-18dB:ratio=3:attack=15:release=120,"
            "loudnorm=I=-16:TP=-1.5:LRA=7,"
            "apad=pad_dur=1.2"
        )
        cmd_norm = [
            FFMPEG_EXE, "-y",
            "-nostdin",
            "-i", str(raw_temp),
            "-af", filter_voice,
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(target_path)
        ]
        subprocess.run(cmd_norm, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        if raw_temp.exists():
            try:
                raw_temp.unlink()
            except Exception:
                pass

        logger.info(f"✅ Spiker sesi stüdyo seviyesinde hazırlandı: {target_path.name}")
        return aligned_words

    def generate_voiceover(
        self,
        script: str,
        target_path: str,
        voice: Optional[str] = None,
        rate: str = "+0%",
        language: str = "tr"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Senkron arayüz üzerinden ses ve kelime zamanlamalarını üretir."""
        p_target = Path(target_path)
        p_target.parent.mkdir(parents=True, exist_ok=True)

        aligned_words = asyncio.run(self._generate_edge_tts(script, p_target, voice=voice, rate=rate, language=language))
        return str(p_target), aligned_words

    def mix_with_ducking(self, voice_path: str, bgm_path: Optional[str], output_path: str) -> str:
        """
        FFmpeg Sidechain Compression Audio Ducking:
        Konuşma başladığında arka plan müziğini -20 dB seviyesine kısar,
        cümle aralarında ve CTA finalinde müziğin ritmini yükseltir.
        """
        p_voice = Path(voice_path)
        p_out = Path(output_path)
        p_out.parent.mkdir(parents=True, exist_ok=True)

        # Arka plan müziği yoksa dinamik modern spor ritmi sentezle
        if not bgm_path or not Path(bgm_path).exists():
            dur_cmd = [FFMPEG_EXE, "-nostdin", "-i", str(p_voice)]
            res = subprocess.run(dur_cmd, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            v_dur = 50.0
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
                    v_dur = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                    break

            temp_bgm = p_out.parent / "temp_sports_beat.wav"
            bgm_samples = generate_modern_sports_beat(total_duration=v_dur + 3.0, bpm=92.0)
            save_wav(temp_bgm, bgm_samples)
            bgm_file = str(temp_bgm)
        else:
            bgm_file = bgm_path

        filter_complex = (
            "[0:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.0[voice];"
            "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=0.22[bgm];"
            "[bgm][voice]sidechaincompress=threshold=0.10:ratio=4:attack=10:release=350[ducked];"
            "[voice][ducked]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )

        cmd = [
            FFMPEG_EXE, "-y",
            "-nostdin",
            "-i", str(p_voice),
            "-i", bgm_file,
            "-filter_complex", filter_complex,
            "-map", "[outa]",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-ac", "2",
            str(p_out)
        ]
        subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info(f"✅ Sidechain Audio Ducking ile stereo ses miksi hazırlandı: {p_out.name}")

        # Geçici sentezlenen ritmi temizle
        if not bgm_path and Path(bgm_file).exists():
            try:
                Path(bgm_file).unlink()
            except Exception:
                pass

        return str(p_out)
