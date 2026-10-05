"""
SubtitleWorker: YouTube Shorts Safe-Zone (MarginV=520) & ASS Karaoke Altyazı Motoru.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("AntigravityEngine.SubtitleWorker")


class SubtitleWorker:
    """Whisper / Edge-TTS Kelime Senkronizasyonu & YouTube Shorts Safe Zone Altyazı Stili"""

    def __init__(self):
        pass

    @staticmethod
    def _format_ass_timestamp(seconds: float) -> str:
        """Saniyeyi ASS altyazı zaman formatına (H:MM:SS.cs) çevirir."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        csecs = int(round((seconds - int(seconds)) * 100))
        if csecs >= 100:
            secs += 1
            csecs = 0
        return f"{hrs}:{mins:02d}:{secs:02d}.{csecs:02d}"

    def generate_safe_zone_ass(self, aligned_words: List[Dict[str, Any]], output_ass_path: str):
        """
        YouTube Shorts Safe Zone (MarginV=520) için profesyonel ASS altyazı dosyası üretir.
        Kelimeleri 2-3'lü bloklar halinde gruplar ve konuşulan kelimeyi Canlı Neon Sarı ile vurgular.
        """
        p_out = Path(output_ass_path)
        p_out.parent.mkdir(parents=True, exist_ok=True)

        # YouTube Shorts Safe Zone: Altyazı YouTube UI butonlarının üzerinde (MarginV=520)
        # ASS BGR Renkleri: Beyaz=&H00FFFFFF&, Neon Sarı=&H0015CCFA&
        ass_header = """[Script Info]
Title: Antigravity Shorts Safe-Zone Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortsSafeZone,Arial,64,&H00FFFFFF,&H0015CCFA,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,5,2,2,60,60,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        # Kelimeleri 2-3 kelimelik anlamlı bloklara kümele
        chunks = []
        curr_chunk = []
        for w in aligned_words:
            curr_chunk.append(w)
            has_punct = bool(re.search(r'[.?!,]', w["display_word"]))
            if len(curr_chunk) >= 3 or has_punct:
                chunks.append(curr_chunk)
                curr_chunk = []
        if curr_chunk:
            chunks.append(curr_chunk)

        events = []
        for chunk in chunks:
            if not chunk:
                continue
            # Her kelimenin aktif olduğu an için bir olay üret
            for active_idx, target_word in enumerate(chunk):
                start_ts = self._format_ass_timestamp(target_word["start"])
                end_ts = self._format_ass_timestamp(target_word["end"] + 0.05)

                formatted_words = []
                for idx, w in enumerate(chunk):
                    text = w["display_word"]
                    if idx == active_idx:
                        # Aktif kelime: Neon Sarı Vurgu
                        formatted_words.append(r"{\c&H0015CCFA&}" + text + r"{\c&H00FFFFFF&}")
                    else:
                        formatted_words.append(text)

                line_text = " ".join(formatted_words)
                event_line = f"Dialogue: 0,{start_ts},{end_ts},ShortsSafeZone,,0,0,0,,{line_text}\n"
                events.append(event_line)

        with open(p_out, "w", encoding="utf-8") as f:
            f.write(ass_header)
            f.writelines(events)

        logger.info(f"✅ Safe-Zone ASS altyazı dosyası üretildi (MarginV=520): {p_out.name}")
        return str(p_out)
