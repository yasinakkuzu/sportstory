"""
SportStory Visual Card Overlay Engine (Dinamik Görsel & Fotoğraf Kartı Katmanı).
=============================================================================
Konuşulan kişi, futbolcu, başkan veya kulübe ait yüksek çözünürlüklü resmi portreyi
Wikimedia Commons / spor arşivlerinden otomatik çeker, lüks cam efektli bir karta dönüştürür
ve videonun ilgili sahnelerinde (altyazıları boğmadan) ekrana yansıtır.
"""

import os
import re
import requests
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

CACHE_DIR = Path("assets/cache/images")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_card_font(size: int = 24, bold: bool = True) -> ImageFont.ImageFont:
    """Kart üzerindeki isim etiketi için font yükler."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def fetch_entity_image(entity_name: str) -> Optional[Path]:
    """
    Kişi veya kulüp adıyla Wikipedia/Wikimedia API'sinden resmi görseli çeker ve önbelleğe alır.
    """
    clean_name = entity_name.strip()
    # Cache kontrolü
    safe_slug = re.sub(r'[\W_]+', '_', clean_name.lower()).strip('_')
    cached_file = CACHE_DIR / f"{safe_slug}.jpg"
    if cached_file.exists() and cached_file.stat().st_size > 5000:
        return cached_file

    try:
        # 1. Wikipedia API arama
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={requests.utils.quote(clean_name)}&prop=pageimages&format=json&pithumbsize=900"
        headers = {"User-Agent": "SportStoryDocumentary/2.0 (contact@sportstory.com)"}
        res = requests.get(url, headers=headers, timeout=6).json()
        pages = res.get("query", {}).get("pages", {})

        img_url = None
        for pid, pdata in pages.items():
            if "thumbnail" in pdata:
                img_url = pdata["thumbnail"]["source"]
                break

        # Bulunamadıysa genel arama dene
        if not img_url:
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(clean_name)}&format=json"
            s_res = requests.get(search_url, headers=headers, timeout=6).json()
            search_items = s_res.get("query", {}).get("search", [])
            if search_items:
                first_title = search_items[0]["title"]
                u2 = f"https://en.wikipedia.org/w/api.php?action=query&titles={requests.utils.quote(first_title)}&prop=pageimages&format=json&pithumbsize=900"
                r2 = requests.get(u2, headers=headers, timeout=6).json()
                for pid, pdata in r2.get("query", {}).get("pages", {}).items():
                    if "thumbnail" in pdata:
                        img_url = pdata["thumbnail"]["source"]
                        break

        if img_url:
            img_res = requests.get(img_url, headers=headers, timeout=8)
            if img_res.status_code == 200:
                with open(cached_file, "wb") as f:
                    f.write(img_res.content)
                return cached_file

    except Exception as e:
        print(f"⚠️ [VisualCardOverlay] Görsel arama hatası ({entity_name}): {e}")

    return None


class VisualCardRenderer:
    """
    Belirli bir kişi veya kulübün görsel kartını lüks cam ve gölge çerçevesiyle oluşturur
    ve video karelerine zamanlamaya göre alpha-composite ile uygular.
    """
    def __init__(
        self,
        entity_name: str,
        image_path: Path,
        card_width: int = 580,
        card_height: int = 420,
        y_position: int = 340
    ):
        self.entity_name = entity_name.upper()
        self.image_path = image_path
        self.card_w = card_width
        self.card_h = card_height
        self.pos_x = (1080 - card_width) // 2
        self.pos_y = y_position
        self.prebuilt_card = self._build_card()

    def _build_card(self) -> Image.Image:
        """Lüks kavisli çerçeve, fotoğraf ve isim etiketini tek bir RGBA katmanında birleştirir."""
        card_full_w = self.card_w + 30
        card_full_h = self.card_h + 30
        container = Image.new("RGBA", (card_full_w, card_full_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(container)

        # 1. Yumuşak Drop Shadow (Gölge)
        for offset in range(8, 0, -2):
            alpha = int(25 * (offset / 8))
            draw.rounded_rectangle(
                [15 - offset, 15 - offset + 6, 15 + self.card_w + offset, 15 + self.card_h + offset + 6],
                radius=28 + offset,
                fill=(0, 0, 0, alpha)
            )

        # 2. Fotoğrafı Kırp ve Köşeleri Yuvarla
        try:
            raw_img = Image.open(self.image_path).convert("RGBA")
            target_ratio = self.card_w / self.card_h
            current_ratio = raw_img.width / raw_img.height

            if current_ratio > target_ratio:
                new_w = int(raw_img.height * target_ratio)
                left = (raw_img.width - new_w) // 2
                raw_img = raw_img.crop((left, 0, left + new_w, raw_img.height))
            else:
                new_h = int(raw_img.width / target_ratio)
                top = (raw_img.height - new_h) // 2
                raw_img = raw_img.crop((0, top, raw_img.width, top + new_h))

            resized = raw_img.resize((self.card_w, self.card_h), Image.Resampling.LANCZOS)

            mask = Image.new("L", (self.card_w, self.card_h), 0)
            draw_m = ImageDraw.Draw(mask)
            draw_m.rounded_rectangle([0, 0, self.card_w, self.card_h], radius=24, fill=255)

            container.paste(resized, (15, 15), mask)

        except Exception as e:
            print(f"⚠️ Kart görseli işlenemedi: {e}")
            return container

        # 3. İnce Lüks Çerçeve (Glass Gold/White Border)
        draw.rounded_rectangle(
            [15, 15, 15 + self.card_w, 15 + self.card_h],
            radius=24,
            outline=(255, 255, 255, 200),
            width=3
        )

        # 4. Alt Bilgi Etiketi (Pill Badge)
        font = get_card_font(size=20, bold=True)
        bbox = font.getbbox(self.entity_name)
        text_w = bbox[2] - bbox[0]
        pill_w = text_w + 36
        pill_h = 40
        pill_x = 15 + (self.card_w - pill_w) // 2
        pill_y = 15 + self.card_h - pill_h - 14

        draw.rounded_rectangle(
            [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
            radius=20,
            fill=(11, 17, 32, 225),
            outline=(255, 215, 0, 160),  # Gold rim
            width=2
        )
        draw.text(
            (pill_x + 18, pill_y + 8),
            self.entity_name,
            font=font,
            fill=(255, 255, 255, 255)
        )

        return container

    def render_overlay(
        self,
        current_time: float,
        start_time: float,
        duration: float = 5.0
    ) -> Optional[Tuple[Image.Image, Tuple[int, int]]]:
        """
        Zamanlamaya göre kartı yumuşak bir fade-in / fade-out efektiyle döndürür.
        """
        if current_time < start_time or current_time > (start_time + duration):
            return None

        # Opaklık hesaplama (0.3s giriş ve çıkış yumuşatması)
        fade_duration = 0.35
        rel_time = current_time - start_time
        time_left = (start_time + duration) - current_time

        if rel_time < fade_duration:
            alpha_factor = rel_time / fade_duration
        elif time_left < fade_duration:
            alpha_factor = time_left / fade_duration
        else:
            alpha_factor = 1.0

        if alpha_factor <= 0.05:
            return None

        if alpha_factor >= 0.98:
            return self.prebuilt_card, (self.pos_x - 15, self.pos_y - 15)

        # Yumuşak geçiş için alpha kanalı ayarla
        faded = self.prebuilt_card.copy()
        r, g, b, a = faded.split()
        a = a.point(lambda p: int(p * alpha_factor))
        faded.putalpha(a)
        return faded, (self.pos_x - 15, self.pos_y - 15)


def detect_featured_entity(topic: str, script_text: str = "") -> Optional[str]:
    """
    Konu başlığından veya senaryo metninden öne çıkan futbolcu, yönetici veya kulübü tespit eder.
    Örnekler:
    - 'Stefan Schwarz: Uzaya Gitmesi Yasaklanan Futbolcu' -> 'Stefan Schwarz'
    - 'Cristiano Ronaldo: Saniyede 7 Dolar Kazanan Servet Makinesi' -> 'Cristiano Ronaldo'
    - 'Manchester City: 115 Kural İhlali' -> 'Manchester City'
    """
    if not topic:
        return None

    # 1. Başlıkta ':' ayracı varsa ilk kısmı al
    if ":" in topic:
        cand = topic.split(":", 1)[0].strip()
        cand = re.sub(r'(\bFC\b|\bCF\b|\bCalcio\b)', '', cand, flags=re.IGNORECASE).strip()
        if len(cand) >= 3:
            return cand

    # 2. Tanınan bilinen ikon isimleri
    KNOWN_ENTITIES = [
        "Stefan Schwarz", "Dennis Bergkamp", "Neil Ruddock", "Spencer Prior",
        "Giuseppe Reina", "Ronaldinho", "Roberto Firmino", "Ali Dia",
        "Cristiano Ronaldo", "Lionel Messi", "Neymar", "Kylian Mbappe",
        "Erling Haaland", "Vinicius Jr", "Samuel Eto'o", "Roberto Carlos",
        "Pep Guardiola", "Todd Boehly", "John Textor", "Peter Lim",
        "Unai Emery", "Suleyman Kerimov", "Peter Ridsdale", "Gianluigi Buffon",
        "Fabio Cannavaro", "Rio Ferdinand", "Arthur Melo", "Miralem Pjanic"
    ]
    combined_search = f"{topic} {script_text}".lower()
    for ent in KNOWN_ENTITIES:
        if ent.lower() in combined_search:
            return ent

    # 3. İlk 2 kelimeyi al
    words = topic.split()
    if len(words) >= 2:
        return " ".join(words[:2])

    return None


def select_background_for_topic(topic: str) -> str:
    """
    3 temel içerik sütununa göre en uygun arka plan videosunu seçer:
    - Pillar 1: Absürt Sözleşmeler & Trivia & Sahtekarlar -> bg_minecraft.mp4 (Dual Stimulation)
    - Pillar 2: Kulüp Krizleri & Skandallar & 115 Kural -> bg_pes_retro.mp4 / bg_pes_milan.mp4 (Retro Futbol)
    - Pillar 3: Saniyede Servetler & Finansal İllüzyonlar -> bg_asmr.mp4 (Hipnotik ASMR)
    """
    t = (topic or "").lower()

    # Pillar 1: Absürt Sözleşmeler & Trivia & Sahtekarlar
    p1_keywords = [
        "madde", "sözleşme", "clause", "contract", "lego", "uzay", "space", "uçak",
        "flying", "kilo", "weight", "gece kulübü", "nightclub", "sahtekar", "con artist",
        "yalan", "ali dia", "schwarz", "bergkamp", "ruddock", "reina", "firmino", "prior", "testis"
    ]
    # Pillar 3: Servetler & Saniyede Gelirler & Lüks
    p3_keywords = [
        "maaş", "servet", "saniye", "para", "dolar", "milyon", "kazanç", "salary",
        "wealth", "second", "earnings", "wage", "jet", "bonus", "gelir", "ronaldo",
        "neymar", "haaland", "mbappe", "apple", "hakem"
    ]

    if any(k in t for k in p1_keywords):
        if os.path.exists("bg_minecraft.mp4"):
            return "bg_minecraft.mp4"

    if any(k in t for k in p3_keywords):
        if os.path.exists("bg_asmr.mp4"):
            return "bg_asmr.mp4"

    # Pillar 2 veya varsayılan: Retro PES 6 / Milan
    retro_bgs = ["bg_pes_retro.mp4", "bg_pes_milan.mp4"]
    for bg in retro_bgs:
        if os.path.exists(bg):
            return bg

    all_bgs = ["bg_pes_retro.mp4", "bg_pes_milan.mp4", "bg_minecraft.mp4", "bg_asmr.mp4"]
    for bg in all_bgs:
        if os.path.exists(bg):
            return bg

    return "bg_pes_retro.mp4"


def create_card_renderer(topic: str, script_text: str = "") -> Optional[VisualCardRenderer]:
    """
    Konu ve metinden entity tespit edip görselini çeker ve hazır kart render nesnesi döndürür.
    Hata durumunda None döndürerek pipeline akışını asla bozmaz.
    """
    try:
        entity = detect_featured_entity(topic, script_text)
        if not entity:
            return None
        img_path = fetch_entity_image(entity)
        if not img_path or not img_path.exists():
            return None
        return VisualCardRenderer(entity_name=entity, image_path=img_path)
    except Exception as e:
        print(f"⚠️ [VisualCardOverlay] Kart oluşturma atlandı: {e}")
        return None

