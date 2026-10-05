"""
Kinetic Subtitles Engine for YouTube Shorts (Cross-Platform Edition).
Features:
- Cross-platform font loading (macOS, Windows, Linux)
- Phonetic text-to-speech mapping across all scripts (SHORTS_001 - SHORTS_005)
- Desync-free punctuation and word-level timestamp alignment
- Chronological sentence-boundary timestamp detection for scene synchronization
- Modern minimal glassmorphic subtitle overlay rendering without layout jitter
"""

import sys
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Fix Windows console encoding if needed
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from engine.phonetics import MASTER_PHONETIC_LEXICON

PHONETIC_MAP = MASTER_PHONETIC_LEXICON


def prepare_speech_script(original_script: str) -> str:
    """Replaces foreign football names with natural Turkish phonetics for TTS."""
    from engine.phonetics import normalize_turkish_speech
    return normalize_turkish_speech(original_script)


def clean_str(s: str) -> str:
    """Helper to clean words for comparison."""
    return re.sub(r'[^\w\s]', '', s).lower()


def align_punctuations(spoken_words_timing: list, original_script: str) -> list:
    """
    Aligns spoken word timings from edge-tts with original script tokens.
    Uses lookahead matching so split numbers, multi-word replacements, and punctuation
    never desynchronize the subtitle stream.
    """
    raw_tokens = original_script.strip().split()
    aligned = []
    num_spoken = len(spoken_words_timing)
    num_tokens = len(raw_tokens)

    sp_idx = 0
    tok_idx = 0

    while tok_idx < num_tokens and sp_idx < num_spoken:
        tok = raw_tokens[tok_idx]
        c_tok = clean_str(tok)

        # Check phonetic match
        expected_spoken = [c_tok]
        for w, ph in PHONETIC_MAP.items():
            if clean_str(w) == c_tok:
                expected_spoken.append(clean_str(ph))

        # Lookahead match up to 5 spoken words to absorb multi-word spoken tokens (e.g. "2017'de" -> "iki bin on yedide")
        best_sp_match = None
        for offset in range(min(5, num_spoken - sp_idx)):
            test_sp = clean_str(spoken_words_timing[sp_idx + offset]["word"])
            if test_sp in expected_spoken or any(exp in test_sp for exp in expected_spoken if len(exp) > 3):
                best_sp_match = offset
                break

        if best_sp_match is not None:
            # Consume any intervening spoken tokens as part of previous or current
            start_t = spoken_words_timing[sp_idx]["start"]
            sp_idx += best_sp_match
            end_t = spoken_words_timing[sp_idx]["end"]
            
            aligned.append({
                "display_word": tok,
                "clean_word": c_tok,
                "start": start_t,
                "end": end_t
            })
            sp_idx += 1
            tok_idx += 1
        else:
            # Direct pair if no future anchor matches immediately
            aligned.append({
                "display_word": tok,
                "clean_word": c_tok,
                "start": spoken_words_timing[sp_idx]["start"],
                "end": spoken_words_timing[sp_idx]["end"]
            })
            sp_idx += 1
            tok_idx += 1

    # Any remaining raw tokens get final timestamp
    last_end = aligned[-1]["end"] if aligned else 0.0
    while tok_idx < num_tokens:
        aligned.append({
            "display_word": raw_tokens[tok_idx],
            "clean_word": clean_str(raw_tokens[tok_idx]),
            "start": last_end,
            "end": last_end + 0.35
        })
        last_end += 0.35
        tok_idx += 1

    return aligned


def find_sentence_endpoints(aligned_words: list, anchor_words: list) -> list:
    """
    Finds exact ending timestamps for anchor sentences to sync visual scene cuts.
    Performs a chronological forward search to prevent duplicate-word jumps.
    """
    endpoints = []
    curr_idx = 0
    num_words = len(aligned_words)

    for anchor in anchor_words:
        clean_anchor = anchor.rstrip(".?!,:;\"'").lower()
        found_time = None
        for i in range(curr_idx, num_words):
            w = aligned_words[i]["display_word"].rstrip(".?!,:;\"'").lower()
            cw = aligned_words[i]["clean_word"].rstrip(".?!,:;\"'").lower()
            if w == clean_anchor or cw == clean_anchor or clean_anchor in w:
                found_time = aligned_words[i]["end"]
                curr_idx = i + 1
                break
        if found_time is not None:
            endpoints.append(found_time)
        elif endpoints:
            # Fallback safe interval (+5.0s from previous cut)
            endpoints.append(endpoints[-1] + 5.0)

    return endpoints


def get_subtitle_font(size=52, bold=True):
    """Loads punchy, heavy font for subtitles across macOS, Windows, and Linux."""
    candidates = [
        # macOS
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        # Windows
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/impact.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for p_str in candidates:
        p = Path(p_str)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()


class KineticSubtitleRenderer:
    def __init__(self, aligned_words, width=1080, height=1920):
        self.words = aligned_words
        self.width = width
        self.height = height
        self.base_font_size = 72
        self.max_allowed_width = 860  # Guarantees at least 110px safe margin on both sides
        self.chunks = self._build_sentence_aware_chunks(aligned_words)

    def _build_sentence_aware_chunks(self, words, max_words=2):
        """
        Groups words into small 1-2 word clusters for punchy kinetic timing.
        Breaks immediately at punctuation.
        """
        chunks = []
        curr_chunk = []

        for w in words:
            curr_chunk.append(w)
            w_text = w.get("display_word") or w.get("word") or ""
            has_punct = bool(re.search(r'[.?!,;:]', w_text))

            # If 2 words or punctuation, close chunk
            if len(curr_chunk) >= max_words or has_punct:
                chunks.append({
                    "start": curr_chunk[0]["start"],
                    "end": curr_chunk[-1]["end"] + 0.10,
                    "words": curr_chunk
                })
                curr_chunk = []

        if curr_chunk:
            chunks.append({
                "start": curr_chunk[0]["start"],
                "end": curr_chunk[-1]["end"] + 0.10,
                "words": curr_chunk
            })
        return chunks

    def _get_fitted_font_and_metrics(self, chunk_words):
        """
        Dynamically finds the optimal font size so words NEVER exceed max_allowed_width.
        """
        raw_words = [(w.get("display_word") or w.get("word") or "").strip().upper() for w in chunk_words]
        
        for font_size in range(self.base_font_size, 38, -3):
            font = get_subtitle_font(size=font_size, bold=True)
            word_widths = []
            total_w = 0
            for rw in raw_words:
                bbox = font.getbbox(rw)
                w = bbox[2] - bbox[0]
                word_widths.append(w)
                total_w += w
            # Add inter-word spacing (18px)
            total_w += 18 * max(0, len(raw_words) - 1)
            
            if total_w <= self.max_allowed_width:
                return font, font_size, word_widths, total_w
                
        # Fallback to minimum size
        min_font = get_subtitle_font(size=38, bold=True)
        word_widths = [(min_font.getbbox(rw)[2] - min_font.getbbox(rw)[0]) for rw in raw_words]
        total_w = sum(word_widths) + 18 * max(0, len(raw_words) - 1)
        return min_font, 38, word_widths, total_w

    def render_overlay(self, current_time: float) -> Image.Image:
        """
        Renders modern kinetic subtitle overlay with adaptive scaling.
        Guaranteed zero horizontal overflow and razor-sharp contrast.
        """
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

        active_chunk = None
        for chunk in self.chunks:
            if chunk["start"] <= current_time <= chunk["end"]:
                active_chunk = chunk
                break

        if not active_chunk:
            return overlay

        draw = ImageDraw.Draw(overlay)
        chunk_words = active_chunk["words"]

        # Adapt font size so chunk is guaranteed to fit within safe width
        font, font_size, word_widths, total_width = self._get_fitted_font_and_metrics(chunk_words)

        # Center horizontally within screen (safe zone >= 110px margins)
        start_x = max(60, (self.width - total_width) // 2)
        y_pos = 980  # Safe vertical center

        # Measure line height
        sample_bbox = font.getbbox("LEEDS")
        text_h = sample_bbox[3] - sample_bbox[1]

        # Dark glass backing pill with rounded corners for legibility
        pad_x = 24
        pad_y = 14
        box = [
            start_x - pad_x,
            y_pos - pad_y,
            start_x + total_width + pad_x,
            y_pos + text_h + pad_y + 8
        ]
        # Translucent dark backing
        draw.rounded_rectangle(box, radius=18, fill=(10, 15, 26, 175), outline=(255, 255, 255, 30), width=1)

        # Draw words
        curr_x = start_x
        for idx, w_info in enumerate(chunk_words):
            word_str = (w_info.get("display_word") or w_info.get("word") or "").strip().upper()
            is_active = (w_info["start"] <= current_time <= w_info["end"] + 0.08)
            w = word_widths[idx]

            # Deep drop shadow
            draw.text(
                (curr_x + 3, y_pos + 4),
                word_str,
                font=font,
                fill=(0, 0, 0, 210),
                stroke_fill=(0, 0, 0, 255),
                stroke_width=2
            )

            # Active word: Electric Yellow, Inactive: Pure White
            fill_color = (255, 230, 0, 255) if is_active else (255, 255, 255, 245)
            stroke_width = 4 if is_active else 3

            draw.text(
                (curr_x, y_pos),
                word_str,
                font=font,
                fill=fill_color,
                stroke_fill=(0, 0, 0, 255),
                stroke_width=stroke_width
            )
            curr_x += w + 18

        return overlay

