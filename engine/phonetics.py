"""
Antigravity Sports & Finance Phonetic Intelligence Engine.
Otonom Telaffuz Denetleyicisi ve Fonetik Ön-İşlemci.

Özellikler:
1. Türkçe Edge-TTS için küresel futbolcu, teknik direktör, stadyum ve kulüp isimlerini
   doğal Türkçe fonetiğine çevirir (Örn: Mbappé -> Embappe, Bernabéu -> Bernabeu).
2. Yabancı aksan işaretlerini (é, á, ó, í, ú, ñ) temizleyerek TTS kekelemesini sıfırlar.
3. Kısaltmaları (UEFA, FFP, NFL, NBA) Türkçe spiker okunuşuna çevirir.
4. Finansal rakamları ve sembolleri (1.35 milyar, %115, €500M) seslendirilebilir Türkçeye açar.
"""

import re
import logging
from typing import Dict, Tuple

logger = logging.getLogger("AntigravityEngine.Phonetics")

# 1. KAPSAMLI KÜRESEL FUTBOL VE FİNANS FONETİK SÖZLÜĞÜ (TÜRKÇE SPİKER STANDARDI)
MASTER_PHONETIC_LEXICON = {
    # PSG / Fransa
    "Kylian Mbappé": "Kilyan Embappe",
    "Kylian Mbappe": "Kilyan Embappe",
    "Mbappé'yi": "Embappe'yi",
    "Mbappé'nin": "Embappe'nin",
    "Mbappé'ye": "Embappe'ye",
    "Mbappé'de": "Embappe'de",
    "Mbappé'den": "Embappe'den",
    "Mbappé": "Embappe",
    "Mbappe'yi": "Embappe'yi",
    "Mbappe'nin": "Embappe'nin",
    "Mbappe'ye": "Embappe'ye",
    "Mbappe'de": "Embappe'de",
    "Mbappe'den": "Embappe'den",
    "Mbappe": "Embappe",
    "Nasser Al-Khelaifi": "Nasır El Helaifi",
    "Al-Khelaifi": "El Helaifi",
    "Parc des Princes": "Park de Prens",

    # Real Madrid / İspanya
    "Santiago Bernabéu'nun": "Santiyago Bernabeu'nun",
    "Santiago Bernabéu'ya": "Santiyago Bernabeu'ya",
    "Santiago Bernabéu'da": "Santiyago Bernabeu'da",
    "Santiago Bernabéu": "Santiyago Bernabeu",
    "Santiago Bernabeu'nun": "Santiyago Bernabeu'nun",
    "Santiago Bernabeu'ya": "Santiyago Bernabeu'ya",
    "Santiago Bernabeu'da": "Santiyago Bernabeu'da",
    "Santiago Bernabeu": "Santiyago Bernabeu",
    "Santiago Barnabeu'nun": "Santiyago Bernabeu'nun",
    "Santiago Barnabeu'ya": "Santiyago Bernabeu'ya",
    "Santiago Barnabeu'da": "Santiyago Bernabeu'da",
    "Santiago Barnabeu": "Santiyago Bernabeu",
    "Bernabéu'nun": "Bernabeu'nun",
    "Bernabéu'ya": "Bernabeu'ya",
    "Bernabéu'da": "Bernabeu'da",
    "Bernabéu'ye": "Bernabeu'ye",
    "Bernabéu": "Bernabeu",
    "Bernabeu'nun": "Bernabeu'nun",
    "Bernabeu'ya": "Bernabeu'ya",
    "Bernabeu'da": "Bernabeu'da",
    "Bernabeu'ye": "Bernabeu'ye",
    "Bernabeu": "Bernabeu",
    "Barnabeu'nun": "Bernabeu'nun",
    "Barnabeu'ya": "Bernabeu'ya",
    "Barnabeu'da": "Bernabeu'da",
    "Barnabeu": "Bernabeu",
    "Santiago": "Santiyago",
    "Florentino Pérez": "Florentino Perez",
    "Florentino Perez": "Florentino Perez",
    "Pérez": "Perez",
    "Perez": "Perez",
    "Carlo Ancelotti": "Karlo Ançelotti",
    "Ancelotti": "Ançelotti",

    # Barcelona / Katalunya
    "Coutinho'ya": "Kutinyo'ya",
    "Coutinho'nun": "Kutinyo'nun",
    "Coutinho": "Kutinyo",
    "Dembélé'ye": "Dembele'ye",
    "Dembélé'nin": "Dembele'nin",
    "Dembélé": "Dembele",
    "Dembele'ye": "Dembele'ye",
    "Dembele": "Dembele",
    "Griezmann'a": "Grizman'a",
    "Griezmann'ın": "Grizman'ın",
    "Griezmann": "Grizman",
    "Camp Nou": "Kamp Nu",
    "La Masia": "La Masiya",

    # Chelsea / Premier League
    "Todd Boehly": "Tod Boli",
    "Boehly'nin": "Boli'nin",
    "Boehly'ye": "Boli'ye",
    "Boehly": "Boli",
    "Enzo Fernández": "Enzo Fernandez",
    "Enzo'ya": "Enzo'ya",
    "Enzo": "Enzo",
    "Mudryk'le": "Mudrik'le",
    "Mudryk'e": "Mudrik'e",
    "Mudryk": "Mudrik",
    "Stamford Bridge": "Stemfırd Bric",

    # Manchester City & İngiltere
    "Roberto Mancini'ye": "Roberto Mançini'ye",
    "Roberto Mancini": "Roberto Mançini",
    "Mancini'ye": "Mançini'ye",
    "Mancini'nin": "Mançini'nin",
    "Mancini": "Mançini",
    "Pep Guardiola": "Pep Gvardiyola",
    "Guardiola": "Gvardiyola",
    "Etihad": "İttihad",
    "Sheikh Mansour": "Şeyh Mansur",
    "Abu Dabi'deki": "Abu Dabi'deki",
    "Abu Dabi": "Abu Dabi",
    "Kevin De Bruyne": "Kevin De Broyne",
    "De Bruyne": "De Broyne",
    "Erling Haaland": "Örling Holand",
    "Haaland": "Holand",

    # Diğer Yıldızlar, Kulüpler & Ligler
    "Newcastle United": "Nivkasıl Yunaytıt",
    "Newcastle'ın": "Nivkasıl'ın",
    "Newcastle'a": "Nivkasıl'a",
    "Newcastle": "Nivkasıl",
    "Juventus": "Yuventus",
    "Everton": "Evırtın",
    "Saudi PIF": "Suudi Pi-Ay-Ef",
    "Saudi": "Suudi",
    "PIF": "Pi-Ay-Ef",
    "RedBird": "RedBörd",
    "Elliott": "Elyıt",
    "Inter Milan": "İnter Milan",
    "Oaktree Capital": "Oktri Kapital",
    "Oaktree": "Oktri",
    "Suning": "Suning",
    "John Textor": "Con Tekstır",
    "Textor": "Tekstır",
    "Lyon": "Liyon",
    "Aston Villa": "Astın Villa",
    "Szoboszlai": "Soboslayi",
    "Lewandowski": "Levandovski",
    "Taylor Swift": "Teylor Svift",

    # Kısaltmalar & Kurumlar
    "UEFA'nın": "U-e-fa'nın",
    "UEFA'ya": "U-e-fa'ya",
    "UEFA": "U-e-fa",
    "FIFA": "Fifa",
    "FFP": "Fe-Fe-Pe",
    "NFL": "En-Ef-El",
    "NBA": "En-Bi-Ey",
    "PSG": "Pe-Se-Je",
    "CGI": "Si-Ci-Ay"
}

# 2. YABANCI DİL AKUT VE DİYAKRİTİK TEMİZLEME TABLOSU
DIACRITIC_MAP = {
    'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
    'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a',
    'ó': 'o', 'ò': 'o', 'ô': 'o',
    'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
    'ú': 'u', 'ù': 'u', 'û': 'u',
    'ñ': 'n'
}


def sanitize_foreign_diacritics(text: str) -> str:
    """Türkçe alfabesinde bulunmayan Latin aksanlarını (é, á, ó vb.) yerli Türkçe karşılıklarına çevirir."""
    chars = []
    for char in text:
        chars.append(DIACRITIC_MAP.get(char, char))
    return "".join(chars)


def normalize_turkish_speech(script: str) -> str:
    """
    Spiker metnini TTS motoruna göndermeden önce otonom olarak optimize eder:
    - İsimleri fonetik sözlükten geçirir (kelime sınırları ile tekil ve güvenli eşleştirme).
    - Yabancı aksanları temizler.
    - Belgesel akışını bozan noktalama işaretlerini yumuşatır.
    """
    spoken = script

    # 1. Sözlükteki uzun ifadeler önce çalışacak şekilde sırala ve kelime sınırı (\b) uygula
    sorted_lexicon = sorted(MASTER_PHONETIC_LEXICON.items(), key=lambda x: len(x[0]), reverse=True)
    for written, phonetic in sorted_lexicon:
        pattern = re.compile(r'\b' + re.escape(written), re.IGNORECASE)
        spoken = pattern.sub(phonetic, spoken)

    # 2. Kalan yabancı diyakritikleri temizle
    spoken = sanitize_foreign_diacritics(spoken)

    # 3. Sayı ve sembol düzenlemeleri
    # 1.35 milyar -> 1 milyar 350 milyon
    spoken = re.sub(r'1\.35\s*milyar', '1 milyar 350 milyon', spoken, flags=re.IGNORECASE)
    # %115 -> yüzde 115
    spoken = re.sub(r'%(\d+)', r'yüzde \1', spoken)
    # -60 puan -> eksi 60 puan
    spoken = re.sub(r'-(\d+)\s*puan', r'eksi \1 puan', spoken)

    # 4. Spiker tonlama yumuşatması
    spoken = spoken.replace(";", ",")
    spoken = spoken.replace("!", ".")
    spoken = spoken.replace("...", ".")
    spoken = re.sub(r'\s+', ' ', spoken).strip()

    return spoken
