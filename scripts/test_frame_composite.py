import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
import imageio_ffmpeg
from engine.subtitles import KineticSubtitleRenderer, get_subtitle_font
from scripts.test_branding_overlay import create_channel_branding_badge

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# Extract 1 test frame from master_bg.mp4
test_bg_img = Path("output/test_bg_frame.jpg")
subprocess.run([
    FFMPEG_EXE, "-y", "-ss", "120", "-i", "master_bg.mp4",
    "-vf", "crop=ih*(9/16):ih,scale=1080:1920", "-vframes", "1", str(test_bg_img)
], check=True)

bg = Image.open(test_bg_img).convert("RGBA")

# Create test subtitle words
aligned_words = [
    {"display_word": "LEEDS", "clean_word": "leeds", "start": 0.0, "end": 0.3},
    {"display_word": "UNITED", "clean_word": "united", "start": 0.3, "end": 0.65},
    {"display_word": "CHAMPIONS", "clean_word": "champions", "start": 0.65, "end": 1.0},
    {"display_word": "LEAGUE", "clean_word": "league", "start": 1.0, "end": 1.35},
    {"display_word": "COLLAPSE", "clean_word": "collapse", "start": 1.35, "end": 1.8},
]

sub_renderer = KineticSubtitleRenderer(aligned_words, width=1080, height=1920)
# Subtitle overlay at time 0.1s (LEEDS UNITED active)
sub_overlay = sub_renderer.render_overlay(0.1)

# Branding badge overlay
badge_overlay = create_channel_branding_badge(1080, 1920)

# Composite
composite = Image.alpha_composite(bg, badge_overlay)
composite = Image.alpha_composite(composite, sub_overlay)

out_preview = Path("output/test_full_composite.jpg")
composite.convert("RGB").save(out_preview, quality=95)
print("Composite saved to:", out_preview)
