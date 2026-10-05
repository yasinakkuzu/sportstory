import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from engine.subtitles import get_subtitle_font

def create_channel_branding_badge(width=1080, height=1920):
    """
    Creates a pre-rendered RGBA overlay containing the premium SportStory branding watermark.
    Positioned in the safe zone (Top-Left X:60, Y:110 or Top-Right X:800, Y:110).
    """
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Let's inspect the icon
    icon_path = Path("assets/branding/brand_icon_clean.png")
    if not icon_path.exists():
        icon_path = Path("assets/branding/brand_icon_transparent_hd.png")

    # Dimensions for sleek top glass badge
    # Position: Top Left (X: 64, Y: 110)
    # YouTube Shorts UI on mobile leaves X: 60-350, Y: 100-200 completely clean!
    x1, y1 = 64, 110
    badge_h = 56
    icon_size = 38
    
    font = get_subtitle_font(size=24, bold=True)
    text = "SPORTSTORY"
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    
    badge_w = icon_size + tw + 48
    x2 = x1 + badge_w
    y2 = y1 + badge_h

    # Luxury Glass Pill Background: dark slate with 65% opacity & delicate border
    draw.rounded_rectangle([x1, y1, x2, y2], radius=28, fill=(11, 17, 32, 195), outline=(255, 255, 255, 60), width=2)

    # Paste Brand Icon
    if icon_path.exists():
        icon_img = Image.open(icon_path).convert("RGBA")
        icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        # Apply clean opacity
        r, g, b, a = icon_img.split()
        a = a.point(lambda p: int(p * 0.95))
        icon_img.putalpha(a)
        
        icon_x = x1 + 12
        icon_y = y1 + (badge_h - icon_size) // 2
        overlay.paste(icon_img, (icon_x, icon_y), icon_img)
        text_x = icon_x + icon_size + 10
    else:
        text_x = x1 + 20

    # Draw Brand Name with crisp white typography
    text_y = y1 + (badge_h // 2)
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 250), anchor="lm")
    
    # Golden accent dot at the end
    dot_x = text_x + tw + 10
    draw.ellipse([dot_x - 3, text_y - 3, dot_x + 3, text_y + 3], fill=(250, 204, 21, 255))

    return overlay

if __name__ == "__main__":
    # Create test canvas
    canvas = Image.new("RGBA", (1080, 1920), (30, 40, 60, 255))
    badge = create_channel_branding_badge(1080, 1920)
    combined = Image.alpha_composite(canvas, badge)
    out_path = Path("output/test_branding_preview.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.save(out_path)
    print("Branding badge preview saved to:", out_path)
