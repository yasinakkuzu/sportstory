"""
Modern Ultra-Clean Visual Compositor for YouTube Shorts.
2026 Editorial Sports Aesthetic:
- Obsidian dark mode with fine micro-grid and subtle ambient lighting
- Translucent frosted glass cards with 1px luminous borders (Glassmorphism)
- Clean typography hierarchy and modern pill tags
- Smooth cross-dissolve frame transitions between scenes
- Live top progress bar
"""

import sys
import re
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import numpy as np

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WIDTH = 1080
HEIGHT = 1920


def turkish_upper(text: str) -> str:
    """Türkçe İ ve I harflerini doğru büyüten fonksiyon."""
    mapping = {"i": "İ", "ı": "I"}
    return "".join(mapping.get(c, c.upper()) for c in text)


def get_font(size=48, bold=False):
    """Loads appropriate modern typography across macOS, Windows, and Linux."""
    candidates = [
        # macOS
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        # Windows
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for fn in candidates:
        p = Path(fn)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()



def create_modern_backdrop(accent_color=(56, 189, 248)):
    """
    Creates an obsidian dark backdrop (#090D16) with subtle ambient glow,
    fine architectural grid lines, and film texture.
    """
    # Base dark gradient
    img = Image.new("RGB", (WIDTH, HEIGHT), (9, 13, 22))
    draw = ImageDraw.Draw(img)

    # Soft ambient atmospheric glow at top
    for r in range(450, 0, -25):
        alpha = int(35 * (1 - r / 450))
        box = [WIDTH // 2 - r * 2, -150 - r, WIDTH // 2 + r * 2, -150 + r * 2]
        draw.ellipse(box, fill=(accent_color[0] // 4, accent_color[1] // 4, accent_color[2] // 4))

    # Fine minimalist grid (subtle 70px pitch)
    grid_color = (255, 255, 255, 8)
    grid_img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grid_img)
    for gy in range(0, HEIGHT, 70):
        g_draw.line([(0, gy), (WIDTH, gy)], fill=grid_color, width=1)
    for gx in range(0, WIDTH, 70):
        g_draw.line([(gx, 0), (gx, HEIGHT)], fill=grid_color, width=1)

    img = Image.alpha_composite(img.convert("RGBA"), grid_img).convert("RGB")

    # Gentle film grain texture
    noise = np.random.normal(0, 6, (HEIGHT, WIDTH, 3)).astype(np.int16)
    base_np = np.array(img, dtype=np.int16)
    blended = np.clip(base_np + noise, 0, 255).astype(np.uint8)

    return Image.fromarray(blended)


def draw_glass_card(draw, box, fill=(16, 23, 38, 210), outline=(255, 255, 255, 45), radius=28, width=1):
    """Draws a modern frosted glassmorphic card."""
    draw.rounded_rectangle(box, radius=radius, fill=fill)
    draw.rounded_rectangle(box, radius=radius, outline=outline, width=width)


class BroadcastSceneBuilder:
    """Builds ultra-clean editorial scenes for SHORTS_001."""

    @staticmethod
    def build_scene_1_neymar():
        """Scene 1: Neymar 222M € record transfer."""
        bg = create_modern_backdrop(accent_color=(34, 197, 94))
        draw = ImageDraw.Draw(bg)

        # Header tag pill
        draw.rounded_rectangle([70, 130, 420, 190], radius=30, fill=(15, 23, 42), outline=(34, 197, 94), width=2)
        draw.text((245, 160), "TRANSFER REKORU", font=get_font(26, bold=True), fill=(34, 197, 94), anchor="mm")
        draw.text((WIDTH - 180, 160), "AĞUSTOS 2017", font=get_font(26, bold=False), fill=(148, 163, 184), anchor="mm")

        # Main Central Frosted Card
        card_box = [65, 240, WIDTH - 65, 1340]
        draw_glass_card(draw, card_box, fill=(17, 24, 39), outline=(55, 65, 81), radius=32, width=2)

        # Clean Accent Top Border
        draw.rounded_rectangle([65, 240, WIDTH - 65, 250], radius=5, fill=(34, 197, 94))

        # Title
        draw.text((WIDTH // 2, 320), "FUTBOL TARİHİNİN EN BÜYÜK ÇEKİ", font=get_font(38, bold=True), fill=(241, 245, 249), anchor="mm")
        draw.text((WIDTH // 2, 375), "Paris Saint-Germain Serbest Kalma Bedelini Ödedi", font=get_font(26, bold=False), fill=(148, 163, 184), anchor="mm")

        # Big Stat Box
        stat_box = [100, 430, WIDTH - 100, 710]
        draw_glass_card(draw, stat_box, fill=(15, 23, 42), outline=(34, 197, 94), radius=24, width=2)

        draw.text((WIDTH // 2, 490), "BARCELONA KASASINA GİREN NAKİT", font=get_font(30, bold=True), fill=(148, 163, 184), anchor="mm")
        draw.text((WIDTH // 2, 595), "€222.000.000", font=get_font(80, bold=True), fill=(34, 197, 94), anchor="mm")

        # Editorial Data Breakdown Card
        data_box = [100, 760, WIDTH - 100, 1140]
        draw_glass_card(draw, data_box, fill=(24, 33, 50), outline=(255, 255, 255, 30), radius=20, width=1)

        draw.text((140, 810), "KULÜP TARİHİNİN EN ZENGİN DÖNEMİ", font=get_font(28, bold=True), fill=(250, 204, 21))
        draw.line([(140, 850), (WIDTH - 140, 850)], fill=(55, 65, 81), width=1)

        points = [
            "• Kasada 222 Milyon Euro hazır nakit para vardı",
            "• Tüm dünya Barcelona'nın hamlesini bekliyordu",
            "• Ama doğru planlama yerine panik başladı..."
        ]
        y_pt = 900
        for pt in points:
            draw.text((140, y_pt), pt, font=get_font(28, bold=False), fill=(226, 232, 240))
            y_pt += 65

        # Bottom Quote Card
        quote_box = [100, 1180, WIDTH - 100, 1280]
        draw_glass_card(draw, quote_box, fill=(15, 23, 42), outline=(56, 189, 248), radius=16, width=1)
        draw.text((WIDTH // 2, 1230), '"Büyük para, disiplin yoksa felakettir."', font=get_font(30, bold=False), fill=(56, 189, 248), anchor="mm")

        return bg

    @staticmethod
    def build_scene_2_debt():
        """Scene 2: 1.35 Billion Debt Collapse."""
        bg = create_modern_backdrop(accent_color=(239, 68, 68))
        draw = ImageDraw.Draw(bg)

        # Header tag pill
        draw.rounded_rectangle([70, 130, 420, 190], radius=30, fill=(15, 23, 42), outline=(239, 68, 68), width=2)
        draw.text((245, 160), "BİLANÇO ÇÖKÜŞÜ", font=get_font(26, bold=True), fill=(239, 68, 68), anchor="mm")
        draw.text((WIDTH - 180, 160), "2017 ➔ 2021", font=get_font(26, bold=True), fill=(239, 68, 68), anchor="mm")

        # Main Card
        card_box = [65, 240, WIDTH - 65, 1340]
        draw_glass_card(draw, card_box, fill=(24, 15, 22), outline=(153, 27, 27), radius=32, width=2)
        draw.rounded_rectangle([65, 240, WIDTH - 65, 250], radius=5, fill=(239, 68, 68))

        # Title
        draw.text((WIDTH // 2, 320), "SADECE 4 YILDA İFLASIN EŞİĞİ", font=get_font(38, bold=True), fill=(254, 202, 202), anchor="mm")
        draw.text((WIDTH // 2, 375), "Tarihin En Hızlı Finansal Çöküşlerinden Biri", font=get_font(26, bold=False), fill=(148, 163, 184), anchor="mm")

        # Big Debt Box
        stat_box = [100, 430, WIDTH - 100, 710]
        draw_glass_card(draw, stat_box, fill=(35, 12, 18), outline=(239, 68, 68), radius=24, width=2)

        draw.text((WIDTH // 2, 490), "TOPLAM KULÜP BORCU", font=get_font(30, bold=True), fill=(252, 165, 165), anchor="mm")
        draw.text((WIDTH // 2, 595), "€1.350.000.000", font=get_font(80, bold=True), fill=(248, 113, 113), anchor="mm")

        # Minimalist Comparison Bars
        comp_box = [100, 760, WIDTH - 100, 1130]
        draw_glass_card(draw, comp_box, fill=(18, 22, 34), outline=(255, 255, 255, 30), radius=20, width=1)

        draw.text((140, 805), "BORÇ DEĞİŞİM GRAFİĞİ", font=get_font(26, bold=True), fill=(148, 163, 184))

        # 2017 Bar
        draw.text((140, 865), "2017:", font=get_font(28, bold=False), fill=(148, 163, 184))
        draw.rounded_rectangle([250, 860, 470, 900], radius=10, fill=(34, 197, 94))
        draw.text((500, 865), "€280 Milyon", font=get_font(26, bold=True), fill=(34, 197, 94))

        # 2021 Bar
        draw.text((140, 945), "2021:", font=get_font(28, bold=False), fill=(248, 113, 113))
        draw.rounded_rectangle([250, 940, 870, 980], radius=10, fill=(239, 68, 68))
        draw.text((885, 945), "€1.35 Milyar 📈", font=get_font(26, bold=True), fill=(239, 68, 68))

        draw.line([(140, 1020), (WIDTH - 140, 1020)], fill=(55, 65, 81), width=1)
        draw.text((WIDTH // 2, 1070), "Sebep: Panik Alımları ve Kontrolsüz Maaşlar", font=get_font(30, bold=True), fill=(250, 204, 21), anchor="mm")

        # Bottom Alert Pill
        alert_box = [100, 1180, WIDTH - 100, 1280]
        draw_glass_card(draw, alert_box, fill=(40, 15, 20), outline=(239, 68, 68), radius=16, width=1)
        draw.text((WIDTH // 2, 1230), "⚠️ Kulüp iflas koruma eşiğine sürüklendi.", font=get_font(28, bold=True), fill=(254, 202, 202), anchor="mm")

        return bg

    @staticmethod
    def build_scene_3_signings():
        """Scene 3: The 3 Panic Signings (Coutinho, Dembele, Griezmann)."""
        bg = create_modern_backdrop(accent_color=(234, 179, 8))
        draw = ImageDraw.Draw(bg)

        # Header tag pill
        draw.rounded_rectangle([70, 130, 440, 190], radius=30, fill=(15, 23, 42), outline=(234, 179, 8), width=2)
        draw.text((255, 160), "PANİK TRANSFERLERİ", font=get_font(26, bold=True), fill=(234, 179, 8), anchor="mm")
        draw.text((WIDTH - 180, 160), "3 OYUNCU", font=get_font(26, bold=True), fill=(255, 255, 255), anchor="mm")

        # Main Card
        card_box = [65, 240, WIDTH - 65, 1340]
        draw_glass_card(draw, card_box, fill=(17, 24, 39), outline=(55, 65, 81), radius=32, width=2)
        draw.rounded_rectangle([65, 240, WIDTH - 65, 250], radius=5, fill=(234, 179, 8))

        # Title
        draw.text((WIDTH // 2, 315), "NEYMAR'IN YERİNE ALINAN 3 İSİM", font=get_font(38, bold=True), fill=(255, 255, 255), anchor="mm")

        # 3 Transfer Cards
        signings = [
            {"name": "Philippe Coutinho", "from": "Liverpool", "fee": "€135.000.000", "status": "Beklentilerin çok altında kaldı"},
            {"name": "Ousmane Dembélé", "from": "Dortmund", "fee": "€135.000.000", "status": "Kronik sakatlıklar ve form düşüşü"},
            {"name": "Antoine Griezmann", "from": "Atlético Madrid", "fee": "€120.000.000", "status": "Sistem uyuşmazlığı ve erken ayrılık"}
        ]

        y_pos = 380
        for s in signings:
            box = [100, y_pos, WIDTH - 100, y_pos + 220]
            draw_glass_card(draw, box, fill=(24, 33, 50), outline=(255, 255, 255, 35), radius=20, width=1)

            # Name and Fee
            draw.text((135, y_pos + 40), s["name"], font=get_font(34, bold=True), fill=(255, 255, 255))
            draw.text((WIDTH - 135, y_pos + 40), s["fee"], font=get_font(36, bold=True), fill=(250, 204, 21), anchor="ra")

            # Route
            draw.text((135, y_pos + 95), f"Kulüp: {s['from']} ➔ Barcelona", font=get_font(26, bold=False), fill=(148, 163, 184))

            # Status pill
            draw.rounded_rectangle([135, y_pos + 145, WIDTH - 135, y_pos + 195], radius=10, fill=(239, 68, 68, 35))
            draw.text((150, y_pos + 158), f"• {s['status']}", font=get_font(24, bold=True), fill=(252, 165, 165))

            y_pos += 250

        # Total Spent Box
        tot_box = [100, 1170, WIDTH - 100, 1280]
        draw_glass_card(draw, tot_box, fill=(35, 15, 20), outline=(239, 68, 68), radius=20, width=2)
        draw.text((WIDTH // 2, 1205), "3 OYUNCUYA HARCANAN TOPLAM BONSERVİS", font=get_font(24, bold=True), fill=(252, 165, 165), anchor="mm")
        draw.text((WIDTH // 2, 1250), "TAM €390.000.000", font=get_font(46, bold=True), fill=(255, 255, 255), anchor="mm")

        return bg

    @staticmethod
    def build_scene_4_messi():
        """Scene 4: The 115% Wage Crisis & Messi's Farewell."""
        bg = create_modern_backdrop(accent_color=(168, 85, 247))
        draw = ImageDraw.Draw(bg)

        # Header tag pill
        draw.rounded_rectangle([70, 130, 440, 190], radius=30, fill=(15, 23, 42), outline=(168, 85, 247), width=2)
        draw.text((255, 160), "TARİHİ KIRILMA", font=get_font(26, bold=True), fill=(168, 85, 247), anchor="mm")
        draw.text((WIDTH - 180, 160), "AĞUSTOS 2021", font=get_font(26, bold=True), fill=(255, 255, 255), anchor="mm")

        # Main Card
        card_box = [65, 240, WIDTH - 65, 1340]
        draw_glass_card(draw, card_box, fill=(17, 24, 39), outline=(55, 65, 81), radius=32, width=2)
        draw.rounded_rectangle([65, 240, WIDTH - 65, 250], radius=5, fill=(168, 85, 247))

        # Title
        draw.text((WIDTH // 2, 315), "MAAŞ BÜTÇESİ %115'E ULAŞTI!", font=get_font(38, bold=True), fill=(255, 255, 255), anchor="mm")

        # Big Stat Box
        stat_box = [100, 390, WIDTH - 100, 680]
        draw_glass_card(draw, stat_box, fill=(28, 15, 35), outline=(168, 85, 247), radius=24, width=2)

        draw.text((WIDTH // 2, 450), "OYUNCU MAAŞLARI / TOPLAM GELİR", font=get_font(28, bold=True), fill=(216, 180, 254), anchor="mm")
        draw.text((WIDTH // 2, 550), "%115", font=get_font(90, bold=True), fill=(239, 68, 68), anchor="mm")
        draw.text((WIDTH // 2, 635), "La Liga Kuralı: Maaş Yükü Maksimum %70 Olmalı!", font=get_font(24, bold=False), fill=(250, 204, 21), anchor="mm")

        # Messi's Farewell Section
        messi_box = [100, 730, WIDTH - 100, 1130]
        draw_glass_card(draw, messi_box, fill=(20, 25, 40), outline=(255, 255, 255, 35), radius=22, width=1)

        draw.text((WIDTH // 2, 790), "KULÜP EFSANESİNE LİSANS ÇIKARILAMADI", font=get_font(28, bold=True), fill=(148, 163, 184), anchor="mm")
        draw.text((WIDTH // 2, 870), "LIONEL MESSI", font=get_font(64, bold=True), fill=(255, 255, 255), anchor="mm")
        draw.text((WIDTH // 2, 940), "Gözyaşları İçinde Veda Etti", font=get_font(32, bold=False), fill=(252, 165, 165), anchor="mm")

        # Clean Professional Badge (User feedback: No "0 euro bedavaya")
        draw.rounded_rectangle([150, 1000, WIDTH - 150, 1080], radius=18, fill=(239, 68, 68))
        draw.text((WIDTH // 2, 1040), "Bedavaya Paris'e Gitti!", font=get_font(34, bold=True), fill=(255, 255, 255), anchor="mm")

        # Bottom Lesson
        quote_box = [100, 1180, WIDTH - 100, 1280]
        draw_glass_card(draw, quote_box, fill=(15, 23, 42), outline=(55, 65, 81), radius=16, width=1)
        draw.text((WIDTH // 2, 1230), "Parayı yönetemeyen bir devin çöküşü işte böyle oldu.", font=get_font(28, bold=False), fill=(203, 213, 225), anchor="mm")

        return bg

    @staticmethod
    def build_scene_5_cta():
        """Scene 5: CTA / Recovery question."""
        bg = create_modern_backdrop(accent_color=(56, 189, 248))
        draw = ImageDraw.Draw(bg)

        # Header tag pill
        draw.rounded_rectangle([70, 130, 420, 190], radius=30, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
        draw.text((245, 160), "TARTIŞMA & ANALİZ", font=get_font(26, bold=True), fill=(56, 189, 248), anchor="mm")

        # Main Card
        card_box = [65, 240, WIDTH - 65, 1340]
        draw_glass_card(draw, card_box, fill=(17, 24, 39), outline=(55, 65, 81), radius=32, width=2)
        draw.rounded_rectangle([65, 240, WIDTH - 65, 250], radius=5, fill=(56, 189, 248))

        # Title
        draw.text((WIDTH // 2, 320), "SENİN GÖRÜŞÜN NE?", font=get_font(42, bold=True), fill=(255, 255, 255), anchor="mm")

        # Big Question Box
        q_box = [100, 400, WIDTH - 100, 780]
        draw_glass_card(draw, q_box, fill=(15, 23, 42), outline=(56, 189, 248), radius=24, width=2)

        draw.text((WIDTH // 2, 470), "BARCELONA ESKİ GÜCÜNE", font=get_font(36, bold=True), fill=(148, 163, 184), anchor="mm")
        draw.text((WIDTH // 2, 570), "DÖNEBİLİR Mİ?", font=get_font(72, bold=True), fill=(250, 204, 21), anchor="mm")
        draw.text((WIDTH // 2, 680), "Yeni Camp Nou ve Genç Yıldızlar Yeterli mi?", font=get_font(26, bold=False), fill=(203, 213, 225), anchor="mm")

        # Interactive Options for Comments
        opt1_box = [100, 830, WIDTH - 100, 940]
        draw_glass_card(draw, opt1_box, fill=(24, 33, 50), outline=(34, 197, 94), radius=18, width=1)
        draw.text((WIDTH // 2, 885), "1️⃣ Evet, yeni yapılanmayla zirveye döner", font=get_font(30, bold=True), fill=(34, 197, 94), anchor="mm")

        opt2_box = [100, 970, WIDTH - 100, 1080]
        draw_glass_card(draw, opt2_box, fill=(24, 33, 50), outline=(239, 68, 68), radius=18, width=1)
        draw.text((WIDTH // 2, 1025), "2️⃣ Hayır, borç yükü kulübü uzun yıllar kilitler", font=get_font(30, bold=True), fill=(248, 113, 113), anchor="mm")

        # CTA Arrow Box (User feedback: exact parallel "Yorumlarda tartışalım!")
        cta_box = [100, 1150, WIDTH - 100, 1280]
        draw.rounded_rectangle(cta_box, radius=22, fill=(250, 204, 21))
        draw.text((WIDTH // 2, 1215), "YORUMLARDA TARTIŞALIM! 👇", font=get_font(40, bold=True), fill=(15, 23, 42), anchor="mm")

        return bg


def sanitize_display_text(text: str) -> str:
    """Removes unsupported emoji glyphs that would render as empty square boxes in standard fonts."""
    emoji_pattern = re.compile(
        r'[\U00010000-\U0010ffff]'
        r'|[\u2600-\u27bf]'
        r'|[\u2300-\u23ff]'
        r'|[\u2b50-\u2b55]'
        , flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub('', text)
    return re.sub(r' +', ' ', cleaned).strip()


class GenericSceneBuilder:
    """Builds clean, modern 2026 editorial scenes dynamically from beat metadata."""

    SEGMENT_ACCENTS = {
        "The Hook": (239, 68, 68),       # Red / Alert
        "The Escalation": (249, 115, 22), # Orange / Fire
        "The Breakdown": (56, 189, 248),  # Sky Blue / Analytical
        "The Climax": (168, 85, 247),     # Violet / Drama
        "The CTA": (250, 204, 21),        # Yellow / Action
    }

    @classmethod
    def build_scene_from_beat(cls, beat: dict, scene_idx: int, total_scenes: int, topic: str = "") -> Image.Image:
        segment = beat.get("segment", f"Bölüm {scene_idx + 1}")
        accent = cls.SEGMENT_ACCENTS.get(segment, (56, 189, 248))
        bg = create_modern_backdrop(accent_color=accent)
        draw = ImageDraw.Draw(bg)

        # 1. Header tag pill
        pill_text = turkish_upper(segment)
        draw.rounded_rectangle([70, 130, 440, 190], radius=30, fill=(15, 23, 42), outline=accent, width=2)
        draw.text((255, 160), pill_text, font=get_font(26, bold=True), fill=accent, anchor="mm")
        draw.text((WIDTH - 180, 160), f"{scene_idx + 1} / {total_scenes}", font=get_font(26, bold=False), fill=(148, 163, 184), anchor="mm")

        # 2. Main Central Frosted Card
        card_box = [65, 240, WIDTH - 65, 1340]
        draw_glass_card(draw, card_box, fill=(17, 24, 39), outline=(55, 65, 81), radius=32, width=2)
        draw.rounded_rectangle([65, 240, WIDTH - 65, 250], radius=5, fill=accent)

        # 3. Main Headline / Stat
        raw_headline = beat.get("on_screen_text", "FİNANSAL ANALİZ").replace("<br>", "\n")
        lines = [sanitize_display_text(line) for line in raw_headline.split("\n") if sanitize_display_text(line)]

        y_headline = 350
        if lines:
            main_line = lines[0]
            f_size = 40 if len(main_line) <= 24 else 34
            draw.text((WIDTH // 2, y_headline), main_line, font=get_font(f_size, bold=True), fill=(248, 250, 252), anchor="mm")
            y_headline += 65
            for sub in lines[1:]:
                sub_f_size = 32 if len(sub) <= 28 else 26
                draw.text((WIDTH // 2, y_headline), sub, font=get_font(sub_f_size, bold=True), fill=accent, anchor="mm")
                y_headline += 55

        # 4. Focal Stat / Feature Box
        stat_top = max(y_headline + 25, 490)
        stat_box = [100, stat_top, WIDTH - 100, stat_top + 260]
        draw_glass_card(draw, stat_box, fill=(15, 23, 42), outline=accent, radius=24, width=2)

        # Clean and safely truncate topic header to prevent box overflow
        display_topic = sanitize_display_text(turkish_upper(topic)) if topic else "ÖZEL SPOR ANALİZİ"
        if len(display_topic) > 42:
            display_topic = display_topic[:39] + "..."
        draw.text((WIDTH // 2, stat_top + 45), display_topic, font=get_font(24, bold=True), fill=(148, 163, 184), anchor="mm")

        snippet = beat.get("snippet", "")
        clean_snippet = sanitize_display_text(snippet.replace('"', '').replace("...", "")).strip()
        if len(clean_snippet) > 55:
            clean_snippet = clean_snippet[:52] + "..."
        draw.text((WIDTH // 2, stat_top + 130), f'"{clean_snippet}"', font=get_font(28, bold=True), fill=accent, anchor="mm")

        # 5. Detail Bullet Points from B-Roll or notes
        broll = beat.get("b_roll", "")
        broll_items = [sanitize_display_text(item) for item in broll.split(",") if sanitize_display_text(item)]
        if broll_items:
            data_top = stat_top + 290
            data_box = [100, data_top, WIDTH - 100, min(1160, data_top + 240)]
            draw_glass_card(draw, data_box, fill=(24, 33, 50), outline=(255, 255, 255, 30), radius=20, width=1)
            draw.text((140, data_top + 45), "ÖNEMLİ DETAYLAR", font=get_font(26, bold=True), fill=(250, 204, 21))
            draw.line([(140, data_top + 80), (WIDTH - 140, data_top + 80)], fill=(55, 65, 81), width=1)

            y_pt = data_top + 120
            for item in broll_items[:3]:
                draw.text((140, y_pt), f"• {item.capitalize()}", font=get_font(26, bold=False), fill=(226, 232, 240))
                y_pt += 50

        # 6. Bottom Interaction Card
        cta_box = [100, 1180, WIDTH - 100, 1280]
        if "CTA" in segment.upper():
            draw.rounded_rectangle(cta_box, radius=22, fill=(250, 204, 21))
            draw.text((WIDTH // 2, 1230), "YORUMLARDA BULUŞALIM! 👇", font=get_font(38, bold=True), fill=(15, 23, 42), anchor="mm")
        else:
            draw_glass_card(draw, cta_box, fill=(15, 23, 42), outline=accent, radius=16, width=1)
            draw.text((WIDTH // 2, 1230), "Sizce bu kararın perde arkası neydi?", font=get_font(28, bold=False), fill=(226, 232, 240), anchor="mm")

        return bg



def render_modern_video_stream(scenes, durations, total_duration, subtitle_renderer, output_video_path, ffmpeg_exe):
    """
    Renders the composite video stream with:
    - Smooth subtle cross-dissolve transitions between scenes (6 frames)
    - Modern dynamic Ken Burns zoom
    - Live top progress bar
    - Kinetic subtitle overlay
    - Deadlock-free stderr file logging
    """
    import subprocess

    fps = 30
    ffmpeg_cmd = [
        ffmpeg_exe,
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
        str(output_video_path)
    ]

    stderr_log_path = output_video_path.parent / f"ffmpeg_{output_video_path.stem}.log"

    with open(stderr_log_path, "wb") as stderr_file:
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=stderr_file)

        try:
            current_time = 0.0
            num_scenes = len(scenes)

            for scene_idx, (scene_img, dur) in enumerate(zip(scenes, durations)):
                num_frames = int(dur * fps)
                scene_np = np.array(scene_img.convert("RGB"))

                # Next scene for cross-fade if not last
                next_scene_np = None
                if scene_idx < num_scenes - 1:
                    next_scene_np = np.array(scenes[scene_idx + 1].convert("RGB"))

                # Gentle, refined zoom
                zoom_in = (scene_idx % 2 == 0)
                start_scale = 1.00 if zoom_in else 1.04
                end_scale = 1.04 if zoom_in else 1.00

                pil_source = Image.fromarray(scene_np)
                fade_frames = 6 # 0.2s cross-dissolve

                for frame_idx in range(num_frames):
                    frame_progress = frame_idx / float(max(1, num_frames - 1))
                    scale = start_scale + (end_scale - start_scale) * frame_progress

                    # Center crop for Ken Burns
                    cw = int(WIDTH / scale)
                    ch = int(HEIGHT / scale)
                    left = (WIDTH - cw) // 2
                    top = (HEIGHT - ch) // 2
                    cropped = pil_source.crop((left, top, left + cw, top + ch))
                    frame_img = cropped.resize((WIDTH, HEIGHT), Image.Resampling.BILINEAR)

                    # Cross-dissolve into next scene in the last few frames
                    if next_scene_np is not None and frame_idx >= (num_frames - fade_frames):
                        alpha = (frame_idx - (num_frames - fade_frames) + 1) / float(fade_frames + 1)
                        next_pil = Image.fromarray(next_scene_np)
                        frame_img = Image.blend(frame_img, next_pil, alpha=alpha)

                    frame_rgba = frame_img.convert("RGBA")

                    # Top Live Progress Bar
                    bar_draw = ImageDraw.Draw(frame_rgba)
                    global_progress = min(1.0, current_time / float(total_duration))
                    bar_w = int(WIDTH * global_progress)
                    bar_draw.rectangle([0, 0, WIDTH, 8], fill=(30, 41, 59, 180))
                    if bar_w > 0:
                        bar_draw.rectangle([0, 0, bar_w, 8], fill=(56, 189, 248, 255))

                    # Kinetic Subtitle Overlay
                    sub_overlay = subtitle_renderer.render_overlay(current_time)
                    composite_frame = Image.alpha_composite(frame_rgba, sub_overlay).convert("RGB")

                    proc.stdin.write(composite_frame.tobytes())
                    current_time += (1.0 / fps)

            proc.stdin.close()
            proc.wait()

            if proc.returncode != 0:
                with open(stderr_log_path, "r", encoding="utf-8", errors="ignore") as log_r:
                    err_msg = log_r.read()
                print("FFmpeg Hatası:", err_msg)
                raise RuntimeError(f"Video render hatası: {proc.returncode}")

        except Exception as e:
            if proc.poll() is None:
                proc.kill()
            raise e
        finally:
            if stderr_log_path.exists():
                try:
                    stderr_log_path.unlink()
                except Exception:
                    pass

