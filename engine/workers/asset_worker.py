"""
AssetWorker: Görsel Üretim, Dikey Akış Motoru (VerticalFlowLayout), Sıfır Sızıntı & Kapak Tasarımı.
"""

import re
import os
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from engine.compositor import (
    create_modern_backdrop,
    draw_glass_card,
    get_font,
    WIDTH,
    HEIGHT
)

logger = logging.getLogger("AntigravityEngine.AssetWorker")


def sanitize_turkish_text(text: str) -> str:
    """Emojileri ve fontlarda boş kare □ oluşturan sembolleri temizler."""
    emoji_pattern = re.compile(
        r'[\U00010000-\U0010ffff]'
        r'|[\u2600-\u27bf]'
        r'|[\u2300-\u23ff]'
        r'|[\u2b50-\u2b55]'
        , flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub('', text)
    cleaned = cleaned.replace("<br>", "\n").replace('"', '')
    return re.sub(r' +', ' ', cleaned).strip()


ENGLISH_LEAK_MAP = {
    "BÜYÜK FİNANSAL KRİZ": "MASSIVE FINANCIAL COLLAPSE",
    "ŞÜPHELİ TRANSFER HİLELERİ": "SUSPICIOUS TRANSFER DEALS",
    "GİZLİ HESAPLAR AÇIKLANDI": "SHADOW ACCOUNTS REVEALED",
    "TARİHİ CEZALAR KAPIDA": "HISTORIC SANCTIONS LOOMING",
    "SENİN GÖRÜŞÜN NE?": "WHAT IS YOUR TAKE?",
    "GİZLİ ZARAR": "HIDDEN LOSSES",
    "SİLİNME TEHLİKESİ": "DEDUCTION RISK",
    "MAAŞ / GELİR ORANI": "WAGE TO REVENUE RATIO",
    "MAAŞ": "WAGES",
    "GELİR": "REVENUE",
    "KÜME DÜŞME & CEZALAR": "RELEGATION & PENALTIES",
    "KÜME DÜŞME": "RELEGATION RISK",
    "TARTIŞMAYA KATIL": "JOIN THE DEBATE",
    "FİKRİNİ YORUMLARA YAZ!": "DROP YOUR THOUGHTS BELOW!",
    "KİLİT ANALİZ": "KEY INSIGHT",
    "ÖNEMLİ GELİŞME": "CRITICAL DEVELOPMENT",
    "REKOR CEZA": "RECORD PENALTY",
    "GİRİŞ ANALİZİ": "INTRO ANALYSIS",
    "KRİZ DERİNLEŞİYOR": "CRISIS DEEPENS",
    "FİNANSAL TABLO": "FINANCIAL BREAKDOWN",
    "DÖNÜM NOKTASI": "TURNING POINT",
    "SONUÇ VE TARTIŞMA": "DEBATE CORNER",
    "PUAN": "POINTS",
    "ZARAR": "LOSSES",
    "CEZA": "PENALTY",
    "KURAL HİLESİ Mİ?": "RULE LOOPHOLE?",
    "ZEKİCE HAMLE Mİ?": "MASTERCLASS?",
    "BORÇ": "DEBT",
    "GİZLİ": "HIDDEN",
    "ŞÜPHELİ": "SUSPICIOUS",
    "ORANI": "RATIO",
}


def sanitize_english_text(text: str) -> str:
    """İngilizce videolarda kesinlikle Türkçe sızıntısı kalmamasını sağlayan kurumsal filtre."""
    if not text:
        return text
    clean = text
    for tr_w, en_w in sorted(ENGLISH_LEAK_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        clean = re.sub(re.escape(tr_w), en_w, clean, flags=re.IGNORECASE)
    # Türkçe özel harfleri (ç, ğ, ı, ö, ş, ü) İngilizce karşılıklarına dönüştür
    tr_trans = str.maketrans("çÇğĞıİöÖşŞüÜ", "cCgGiIoOsSuU")
    return clean.translate(tr_trans).strip()


def wrap_text_to_width(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    """Metni verilen piksel genişliğini asla aşmayacak şekilde satırlara böler."""
    words = text.split()
    lines = []
    curr_line = []
    for w in words:
        test_line = " ".join(curr_line + [w])
        bbox = font.getbbox(test_line)
        w_px = bbox[2] - bbox[0]
        if w_px <= max_width or not curr_line:
            curr_line.append(w)
        else:
            lines.append(" ".join(curr_line))
            curr_line = [w]
    if curr_line:
        lines.append(" ".join(curr_line))
    return lines


def get_fitted_font(text: str, max_size: int, max_width: int, bold: bool = True) -> ImageFont.ImageFont:
    """Metin genişliğini max_width piksele sığdıracak şekilde font boyutunu otomatik düşürür."""
    for s in range(max_size, 18, -2):
        f = get_font(s, bold=bold)
        bbox = f.getbbox(text)
        if (bbox[2] - bbox[0]) <= max_width:
            return f
    return get_font(18, bold=bold)


def create_club_backdrop(theme: dict) -> Image.Image:
    """Kulüp renk paletine uygun, derin ve atmosferik karanlık fon oluşturur."""
    img = Image.new("RGB", (WIDTH, HEIGHT), theme["bg_base"])
    draw = ImageDraw.Draw(img, "RGBA")
    
    # 1. Üst atmosferik kulüp ışıması
    glow1 = theme["glow_color"]
    for r in range(520, 0, -25):
        alpha = int(35 * (1 - r / 520))
        box = [WIDTH // 2 - r * 2, -160 - r, WIDTH // 2 + r * 2, -160 + r * 2]
        draw.ellipse(box, fill=(glow1[0], glow1[1], glow1[2], alpha))
        
    # 2. Alt destekleyici ikincil renk ışıması
    glow2 = theme["glow_color_sec"]
    for r in range(380, 0, -25):
        alpha = int(18 * (1 - r / 380))
        box = [WIDTH // 2 - r * 2, HEIGHT - 350 - r, WIDTH // 2 + r * 2, HEIGHT - 350 + r * 2]
        draw.ellipse(box, fill=(glow2[0], glow2[1], glow2[2], alpha))
        
    # 3. İnce mimari grid çizgileri (Çok hafif %3 opaklık)
    grid_color = (255, 255, 255, 6)
    grid_img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grid_img)
    for gy in range(0, HEIGHT, 80):
        g_draw.line([(0, gy), (WIDTH, gy)], fill=grid_color, width=1)
    for gx in range(0, WIDTH, 80):
        g_draw.line([(gx, 0), (gx, HEIGHT)], fill=grid_color, width=1)

    combined = Image.alpha_composite(img.convert("RGBA"), grid_img)
    return combined.convert("RGB")


def turkish_upper(text: str) -> str:
    """Türkçe İ ve I harflerini doğru büyüten fonksiyon."""
    mapping = {"i": "İ", "ı": "I"}
    return "".join(mapping.get(c, c.upper()) for c in text)


class AssetWorker:
    """Görsel Üretim ve Standardizasyon Motoru (9:16 Shorts Entegrasyonu)"""

    CLUB_THEMES = {
        "SHORTS_001": {  # FC Barcelona (Blaugrana & Altın)
            "club_name": "FC BARCELONA",
            "bg_base": (8, 12, 24),
            "glow_color": (165, 0, 68),       # Katalan Bordosu
            "glow_color_sec": (0, 77, 152),   # Barça Laciverti
            "primary_accent": (250, 204, 21), # Şampiyonluk Altını
            "secondary_accent": (225, 29, 72),
            "card_surface": (14, 20, 36),
            "card_border": (45, 55, 75),
            "text_primary": (248, 250, 252),
            "text_muted": (148, 163, 184),
            "metric_bg": (18, 26, 48),
            "badge_bg": (14, 20, 36)
        },
        "SHORTS_002": {  # Chelsea FC (Stamford Kraliyet Mavisi & Buz Mavisi)
            "club_name": "CHELSEA FC",
            "bg_base": (6, 12, 28),
            "glow_color": (3, 70, 148),       # Chelsea Mavisi
            "glow_color_sec": (56, 189, 248), # Buz Mavisi
            "primary_accent": (56, 189, 248), # Elektrik Buz Mavisi
            "secondary_accent": (96, 165, 250),
            "card_surface": (10, 19, 42),
            "card_border": (30, 58, 138),
            "text_primary": (248, 250, 252),
            "text_muted": (147, 197, 253),
            "metric_bg": (14, 28, 62),
            "badge_bg": (10, 19, 42)
        },
        "SHORTS_003": {  # Manchester City (Etihad Gökyüzü Mavisi & Uyarı Kehribarı)
            "club_name": "MANCHESTER CITY",
            "bg_base": (8, 14, 26),
            "glow_color": (108, 171, 221),    # City Gökyüzü Mavisi
            "glow_color_sec": (245, 158, 11), # Ceza / Hukuk Uyarı Kehribarı
            "primary_accent": (56, 189, 248),
            "secondary_accent": (245, 158, 11),
            "card_surface": (12, 22, 38),
            "card_border": (40, 60, 85),
            "text_primary": (248, 250, 252),
            "text_muted": (148, 163, 184),
            "metric_bg": (16, 29, 50),
            "badge_bg": (12, 22, 38)
        },
        "SHORTS_004": {  # Paris Saint-Germain (Parc des Princes Laciverti & Paris Kırmızısı)
            "club_name": "PARIS SAINT-GERMAIN",
            "bg_base": (7, 10, 22),
            "glow_color": (218, 41, 28),      # Paris Kırmızısı
            "glow_color_sec": (0, 65, 130),   # Fransız Kraliyet Mavisi
            "primary_accent": (239, 68, 68),
            "secondary_accent": (250, 204, 21),
            "card_surface": (13, 17, 34),
            "card_border": (51, 65, 85),
            "text_primary": (248, 250, 252),
            "text_muted": (148, 163, 184),
            "metric_bg": (18, 23, 44),
            "badge_bg": (13, 17, 34)
        },
        "SHORTS_005": {  # Real Madrid (Kraliyet Beyazı & Şampiyonluk Altını)
            "club_name": "REAL MADRID",
            "bg_base": (8, 11, 24),
            "glow_color": (195, 158, 92),     # Madrid Altını
            "glow_color_sec": (99, 102, 241), # Kraliyet Mor Işıltısı
            "primary_accent": (234, 179, 8),
            "secondary_accent": (255, 255, 255),
            "card_surface": (14, 19, 36),
            "card_border": (71, 85, 105),
            "text_primary": (255, 255, 255),
            "text_muted": (203, 213, 225),
            "metric_bg": (20, 27, 48),
            "badge_bg": (14, 19, 36)
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        self.openai_api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    def render_flow_scene(
        self,
        segment_name: str,
        headline: str,
        metric: str,
        insight: str,
        scene_idx: int,
        total_scenes: int,
        target_path: str,
        video_id: str = "SHORTS_001",
        language: str = "tr"
    ) -> str:
        """
        Kulüp Temalı Genişletilmiş Dikey Akış Motoru (VerticalFlowLayout 3.0).
        Boş alanları tamamen ortadan kaldırır; 52-56pt editoryal büyük tipografi uygular.
        Boş metrik kutusu oluşmasını engeller ve çoklu dil (TR/EN) UI etiketlerini kusursuz işler.
        """
        theme = self.CLUB_THEMES.get(video_id.upper(), self.CLUB_THEMES["SHORTS_001"])
        accent = theme["primary_accent"]

        # Kulübe özel atmosferik karanlık fon
        img = create_club_backdrop(theme)
        draw = ImageDraw.Draw(img)

        is_en = (language == "en")

        # 1. Üst Kategori Rozeti (Pill) - Ortalanmış ve Slayt Numarasız
        if is_en:
            pill_text = segment_name.upper()
        else:
            pill_text = turkish_upper(sanitize_turkish_text(segment_name))

        pill_font = get_font(28 if len(pill_text) > 18 else 30, bold=True)
        bbox = draw.textbbox((0, 0), pill_text, font=pill_font)
        pill_w = max(360, (bbox[2] - bbox[0]) + 80)
        pill_x1 = (WIDTH - pill_w) // 2
        pill_x2 = (WIDTH + pill_w) // 2

        draw.rounded_rectangle([pill_x1, 100, pill_x2, 172], radius=36, fill=theme["badge_bg"], outline=accent, width=2)
        draw.text((WIDTH // 2, 136), pill_text, font=pill_font, fill=accent, anchor="mm")

        # 2. Ana Dış Cam Kart (y=195'ten y=1345'e kadar ekranı doldurur)
        card_x1, card_y1, card_x2, card_y2 = 60, 195, WIDTH - 60, 1345
        draw_glass_card(draw, [card_x1, card_y1, card_x2, card_y2], fill=theme["card_surface"], outline=theme["card_border"], radius=36, width=2)
        draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y1 + 10], radius=5, fill=accent)

        if is_en:
            clean_hl = sanitize_english_text(headline).upper().strip()
            clean_metric = sanitize_english_text(metric).upper().strip()
            clean_ins = sanitize_english_text(insight).strip()
            default_hl = f"{theme['club_name']} FINANCIAL ANALYSIS"
            cta_btn_text = "DROP YOUR THOUGHTS BELOW!"
            debate_header = "DEBATE CORNER"
            opinion_prompt = "WHAT'S YOUR TAKE?"
            binary_tag = "Masterstroke or Rule Abuse?"
            key_insight_tag = "KEY INSIGHT"
            important_dev_tag = "KEY DEVELOPMENTS"
        else:
            clean_hl = turkish_upper(sanitize_turkish_text(headline))
            clean_metric = turkish_upper(sanitize_turkish_text(metric))
            clean_ins = sanitize_turkish_text(insight)
            default_hl = f"{theme['club_name']} FİNANSAL ANALİZİ"
            cta_btn_text = "FİKRİNİ YORUMLARA YAZ!"
            debate_header = "TARTIŞMA KÖŞESİ"
            opinion_prompt = "SENİN GÖRÜŞÜN NE?"
            binary_tag = "Zekice Hamle mi? • Kural Hilesi mi?"
            key_insight_tag = "KİLİT ANALİZ"
            important_dev_tag = "ÖNEMLİ GELİŞME"

        if not clean_hl or clean_hl in ["ÖZEL SPOR ANALİZİ", "SPECIAL SPORTS ANALYSIS"]:
            clean_hl = default_hl

        is_cta = (scene_idx == total_scenes - 1)

        if is_cta:
            # SAHNE 5: TARTIŞMA & YORUM (YÜKSEK ETKİLEŞİM DÜZENİ - CTA BUTONU SADECE BURADA GÖRÜNÜR)
            draw.text((WIDTH // 2, 270), debate_header, font=get_font(44, bold=True), fill=accent, anchor="mm")
            draw.line([(140, 320), (WIDTH - 140, 320)], fill=theme["card_border"], width=1)

            # Soru Kartı
            q_box = [90, 345, WIDTH - 90, 1160]
            draw_glass_card(draw, q_box, fill=theme["metric_bg"], outline=accent, radius=28, width=2)
            draw.text((WIDTH // 2, 420), opinion_prompt, font=get_font(34, bold=True), fill=accent, anchor="mm")
            draw.line([(160, 470), (WIDTH - 160, 470)], fill=theme["card_border"], width=1)

            # Büyük Soru Metni (54pt bold, merkezli)
            q_font = get_font(54, bold=True)
            q_lines = wrap_text_to_width(clean_ins, q_font, 820)
            q_y = 560
            for ql in q_lines:
                draw.text((WIDTH // 2, q_y), ql, font=q_font, fill=theme["text_primary"], anchor="mm")
                q_y += 85

            # İkili Tartışma Seçenek Rozeti
            draw.rounded_rectangle([140, q_y + 50, WIDTH - 140, q_y + 150], radius=24, fill=theme["card_surface"], outline=theme["card_border"], width=1)
            draw.text((WIDTH // 2, q_y + 100), binary_tag, font=get_font(34, bold=True), fill=theme["text_muted"], anchor="mm")

            # Parlayan Alt CTA Butonu (SADECE SON GÖRSELLE BERABER ORTAYA ÇIKAR)
            cta_box = [95, 1195, WIDTH - 95, 1315]
            draw.rounded_rectangle(cta_box, radius=26, fill=accent)
            draw.text((WIDTH // 2, 1255), cta_btn_text, font=get_font(40 if is_en else 42, bold=True), fill=(8, 12, 24), anchor="mm")

        elif clean_metric:
            # METRİKLİ SAHNE: Başlık + Metrik Kutusu + Büyük 52pt Editoryal İçgörü
            hl_font = get_fitted_font(clean_hl, 42, 860, bold=True)
            draw.text((WIDTH // 2, 265), clean_hl, font=hl_font, fill=theme["text_primary"], anchor="mm")
            draw.line([(140, 315), (WIDTH - 140, 315)], fill=theme["card_border"], width=1)

            # Metrik Hero Kutusu
            stat_box = [90, 335, WIDTH - 90, 625]
            draw_glass_card(draw, stat_box, fill=theme["metric_bg"], outline=accent, radius=26, width=2)
            
            # / işaretlerini otomatik satır sonuna çevir
            norm_metric = clean_metric.replace(" / ", "\n").replace(" /", "\n").replace("/ ", "\n")
            m_lines = [l.strip() for l in norm_metric.split("\n") if l.strip()]

            if len(m_lines) >= 2:
                f_top = get_fitted_font(m_lines[0], 46, 800, bold=True)
                f_bot = get_fitted_font(m_lines[1], 48, 800, bold=True)
                draw.text((WIDTH // 2, 420), m_lines[0], font=f_top, fill=theme["text_primary"], anchor="mm")
                draw.text((WIDTH // 2, 535), m_lines[1], font=f_bot, fill=accent, anchor="mm")
            elif len(m_lines) == 1:
                tokens = m_lines[0].split()
                num_part = tokens[0] if any(c.isdigit() or c in "€$%" for c in tokens[0]) else ""
                rest_part = " ".join(tokens[1:]) if num_part else m_lines[0]
                if num_part and rest_part:
                    f_num = get_fitted_font(num_part, 88, 800, bold=True)
                    f_rest = get_fitted_font(rest_part, 40, 800, bold=True)
                    draw.text((WIDTH // 2, 430), num_part, font=f_num, fill=accent, anchor="mm")
                    draw.text((WIDTH // 2, 538), rest_part, font=f_rest, fill=theme["text_muted"], anchor="mm")
                else:
                    f_single = get_fitted_font(m_lines[0], 54, 800, bold=True)
                    draw.text((WIDTH // 2, 480), m_lines[0], font=f_single, fill=accent, anchor="mm")

            # Editoryal Analiz / Kilit Bilgi Kutusu (HER ŞEY ORTALI)
            ins_box = [90, 655, WIDTH - 90, 1285]
            draw_glass_card(draw, ins_box, fill=theme["card_surface"], outline=theme["card_border"], radius=26, width=1)
            draw.text((WIDTH // 2, 705), key_insight_tag, font=get_font(32, bold=True), fill=accent, anchor="mm")
            draw.line([(WIDTH // 2 - 130, 742), (WIDTH // 2 + 130, 742)], fill=theme["card_border"], width=1)

            ins_font = get_font(52, bold=True)
            ins_lines = wrap_text_to_width(clean_ins, ins_font, 800)
            content_top = 760
            content_bottom = 1260
            total_text_h = len(ins_lines) * 82
            start_y = content_top + max(15, (content_bottom - content_top - total_text_h) // 2)

            for inl in ins_lines:
                draw.text((WIDTH // 2, start_y), inl, font=ins_font, fill=theme["text_primary"], anchor="mm")
                start_y += 82

        else:
            # METRİKSİZ SAHNE: Tam Boy Hero Editoryal Kart (HER ŞEY ORTALI)
            hl_font = get_font(42 if len(clean_hl) < 32 else 36, bold=True)
            draw.text((WIDTH // 2, 265), clean_hl, font=hl_font, fill=theme["text_primary"], anchor="mm")
            draw.line([(140, 315), (WIDTH - 140, 315)], fill=theme["card_border"], width=1)

            ins_box = [90, 345, WIDTH - 90, 1285]
            draw_glass_card(draw, ins_box, fill=theme["metric_bg"], outline=accent, radius=28, width=2)
            draw.text((WIDTH // 2, 420), important_dev_tag, font=get_font(34, bold=True), fill=accent, anchor="mm")
            draw.line([(WIDTH // 2 - 140, 465), (WIDTH // 2 + 140, 465)], fill=theme["card_border"], width=1)

            ins_font = get_font(56, bold=True)
            ins_lines = wrap_text_to_width(clean_ins, ins_font, 800)
            total_text_h = len(ins_lines) * 86
            start_y = 510 + max(20, (700 - total_text_h) // 2)
            for inl in ins_lines:
                draw.text((WIDTH // 2, start_y), inl, font=ins_font, fill=theme["text_primary"], anchor="mm")
                start_y += 86

        # 3. Sağ Alt Köşe: SportStory Marka Logosu & Rozeti
        self.draw_channel_watermark(draw, theme, position="bottom_right", canvas_img=img)

        # Kaydet
        p_target = Path(target_path)
        p_target.parent.mkdir(parents=True, exist_ok=True)
        img.save(p_target, quality=95)
        return str(p_target)

    def draw_channel_watermark(self, draw: ImageDraw.ImageDraw, theme: dict, position: str = "bottom_right", canvas_img: Optional[Image.Image] = None):
        """
        Sağ alt köşeye The Bullish Shield marka ikonu ve kurumsal SportStory logosunu çizer.
        YouTube Shorts UI safe zone standartlarına uygun (Y: 1750, X: safe-zone) konumlandırılmıştır.
        Sky Sports / Bleacher Report / Bloomberg investigative sports network estetiğindedir.
        """
        badge_text = "SPORTSTORY"
        f_badge = get_font(24, bold=True)
        bbox = f_badge.getbbox(badge_text)
        tw = bbox[2] - bbox[0]

        # İkon ölçüleri ve cam rozet hesaplaması
        icon_w, icon_h = 30, 30
        bw = tw + icon_w + 42
        bh = 46

        if position == "bottom_left":
            x1 = 70
            x2 = x1 + bw
        else:  # bottom_right
            x2 = WIDTH - 70
            x1 = x2 - bw

        y1 = 1750
        y2 = y1 + bh
        badge_box = [x1, y1, x2, y2]

        # Cam zemin ve ince ışıma çerçevesi
        draw.rounded_rectangle(badge_box, radius=14, fill=(10, 16, 28, 220), outline=(255, 255, 255, 45), width=1)

        # Alternatif 1: The Bullish Shield / Hexagon saydam marka ikonu
        icon_pasted = False
        icon_path = Path("assets/branding/brand_icon_clean.png")
        if not icon_path.exists():
            icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "branding" / "brand_icon_clean.png"

        if canvas_img is not None and icon_path.exists():
            try:
                b_icon = Image.open(icon_path).convert("RGBA")
                b_icon = b_icon.resize((icon_w, icon_h), Image.Resampling.LANCZOS)
                # Opacity %80 (Bleacher Report / Sky Sports tarzı zarif saydamlık)
                r, g, b, a = b_icon.split()
                a = a.point(lambda p: int(p * 0.85))
                b_icon.putalpha(a)

                icon_x = x1 + 14
                icon_y = y1 + (bh - icon_h) // 2
                canvas_img.paste(b_icon, (icon_x, icon_y), b_icon)
                icon_pasted = True
            except Exception as e:
                logger.warning(f"Watermark ikon yüklenemedi: {e}")

        # Eğer ikon yüklenemediyse fallback olarak accent noktası koy
        if not icon_pasted:
            accent = theme.get("primary_accent", (250, 204, 21))
            dot_x = x1 + 20
            dot_y = y1 + (bh // 2)
            draw.ellipse([dot_x - 4, dot_y - 4, dot_x + 4, dot_y + 4], fill=accent)
            text_x = dot_x + 12
        else:
            text_x = x1 + 14 + icon_w + 8

        # SportStory Tipografisi
        draw.text((text_x, y1 + (bh // 2)), badge_text, font=f_badge, fill=(255, 255, 255, 240), anchor="lm")

    def extract_cover_thumbnail(self, first_scene_path: str, cover_path: str) -> str:
        """Kullanıcının Shorts akışında göreceği yüksek etkili 1080x1920 kapak görselini kaydeder."""
        p_src = Path(first_scene_path)
        p_dst = Path(cover_path)
        p_dst.parent.mkdir(parents=True, exist_ok=True)

        if p_src.exists():
            img = Image.open(p_src)
            img.save(p_dst, quality=98)
            logger.info(f"📸 YouTube Shorts Kapak Görseli Hazırlandı: {p_dst.name}")
        return str(p_dst)
