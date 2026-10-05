"""
Antigravity Sports & Finance Phonetic Intelligence Engine.
Otonom Telaffuz Denetleyicisi ve Fonetik Ön-İşlemci (v3.0 Pro Sports Edition).

Felsefe & İlkeler:
1. "AŞIRI FONETİK BOZULMA" (Over-Phoneticization) ENGELLENDİ:
   - Türk spor yayıncılığı (TRT Spor, beIN Sports, S Sport) ekolüne sadık kalınır.
   - Türkçede doğal okunan isimler ASLA Kiril/Rusça veya yapay İngiliz aksanına çevrilmez:
     * Guardiola -> Guardiola (Gvardiyola DEĞİL!)
     * Arsenal -> Arsenal (Arsınıl DEĞİL!)
     * Liverpool -> Liverpool (Livırpul DEĞİL!)
     * Bayern Münih -> Bayern Münih (Bayörn DEĞİL!)
     * Aston Villa -> Aston Villa (Astın DEĞİL!)
     * Erling Haaland -> Erling Holand (Örling DEĞİL!)
     * Virgil van Dijk -> Virjil Van Dayk (Vörsıl DEĞİL!)
     * Klopp -> Klopp (Kılop DEĞİL!)

2. GERÇEKTEN GEREKLİ FONETİK DÜZELTMELER:
   - Türkçede başlangıcı imkansız sesler: Mbappé -> Embappe
   - Türkçede 'c' harfinin [dʒ] olmasından kaynaklanan bozulmalar: Vinicius -> Vinisyus
   - Yabancı diftong ve sessiz harfler: De Bruyne -> De Broyne, Todd Boehly -> Tod Boli, Coutinho -> Kutinyo
   - Slav ve Latin diyakritikleri: Džeko -> Ceko, Tadić -> Tadiç, Livaković -> Livakoviç
   - Finansal semboller ve kısaltmalar: €100M -> 100 milyon euro, PSR -> Pe-Se-Re, FFP -> Fe-Fe-Pe
"""

import re
import logging
from typing import Dict

logger = logging.getLogger("AntigravityEngine.Phonetics")

# 1. KAPSAMLI KÜRESEL FUTBOL VE FİNANS FONETİK SÖZLÜĞÜ (DOĞAL TÜRK SPOR YAYINCILIĞI STANDARDI)
MASTER_PHONETIC_LEXICON: Dict[str, str] = {
    # --- YILDIZ FUTBOLCULAR & EFSANELER ---
    # Mbappé: Türkçede 'Mb' ile kelime başlayamayacağı için ön-ses türemesi [E] zorunludur
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

    # Vinícius: Türkçede 'c' [dʒ] sesidir; düzeltilmezse 'Viniciyus' okunur
    "Vinicius Junior": "Vinisyus Cunyır",
    "Vinícius Júnior": "Vinisyus Cunyır",
    "Vinicius Jr": "Vinisyus Cunyır",
    "Vinícius Jr": "Vinisyus Cunyır",
    "Vinicius'a": "Vinisyus'a",
    "Vinicius'un": "Vinisyus'un",
    "Vinicius": "Vinisyus",
    "Vinícius": "Vinisyus",

    # Haaland: İskandinav 'aa' 'o' sesidir, spikerler 'Erling Holand' der
    "Erling Haaland": "Erling Holand",
    "Haaland'ın": "Holand'ın",
    "Haaland'a": "Holand'a",
    "Haaland": "Holand",

    # Kevin De Bruyne: Flaman 'uy' diftongu
    "Kevin De Bruyne": "Kevin De Broyne",
    "De Bruyne'nin": "De Broyne'nin",
    "De Bruyne'ye": "De Broyne'ye",
    "De Bruyne": "De Broyne",

    # Virgil van Dijk: Hollandaca 'van Dijk' -> 'Van Dayk', 'Virgil' -> 'Virjil'
    "Virgil van Dijk": "Virjil Van Dayk",
    "van Dijk": "Van Dayk",
    "Van Dijk'ın": "Van Dayk'ın",
    "Van Dijk": "Van Dayk",

    # Bellingham, Foden, Palmer
    "Jude Bellingham": "Cud Belinghem",
    "Bellingham'ın": "Belinghem'in",
    "Bellingham": "Belinghem",
    "Phil Foden": "Fil Fodın",
    "Cole Palmer": "Kol Palmır",

    # Lamine Yamal, Lewandowski
    "Lamine Yamal": "Lamin Yamal",
    "Robert Lewandowski": "Robert Levandovski",
    "Lewandowski'nin": "Levandovski'nin",
    "Lewandowski": "Levandovski",

    # Núñez
    "Darwin Núñez": "Darvin Nunyez",
    "Darwin Nunez": "Darvin Nunyez",
    "Núñez": "Nunyez",
    "Nunez": "Nunyez",

    # Mudryk, Luiz, Osimhen
    "Mykhailo Mudryk": "Mihaylo Mudrik",
    "Mudryk'le": "Mudrik'le",
    "Mudryk'e": "Mudrik'e",
    "Mudryk": "Mudrik",
    "Douglas Luiz": "Daglıs Luiz",
    "Victor Osimhen": "Viktor Osimen",
    "Osimhen'in": "Osimen'in",
    "Osimhen": "Osimen",

    # Slav İsimleri (ž -> c, ć -> ç)
    "Edin Džeko": "Edin Ceko",
    "Edin Dzeko": "Edin Ceko",
    "Džeko": "Ceko",
    "Dzeko": "Ceko",
    "Dušan Tadić": "Duşan Tadiç",
    "Dusan Tadic": "Duşan Tadiç",
    "Tadić": "Tadiç",
    "Tadic": "Tadiç",
    "Sebastian Szymański": "Sebastiyan Şimanski",
    "Sebastian Szymanski": "Sebastiyan Şimanski",
    "Szymański": "Şimanski",
    "Szymanski": "Şimanski",
    "Dominik Livaković": "Dominik Livakoviç",
    "Dominik Livakovic": "Dominik Livakoviç",
    "Livaković": "Livakoviç",
    "Livakovic": "Livakoviç",

    # Latin & Fransız İsimleri
    "Philippe Coutinho": "Filip Kutinyo",
    "Coutinho'ya": "Kutinyo'ya",
    "Coutinho'nun": "Kutinyo'nun",
    "Coutinho": "Kutinyo",
    "Ousmane Dembélé": "Usman Dembele",
    "Ousmane Dembele": "Usman Dembele",
    "Dembélé": "Dembele",
    "Dembele": "Dembele",
    "Antoine Griezmann": "Antuvan Grizman",
    "Griezmann": "Grizman",
    "Szoboszlai": "Soboslayi",
    "Samuel Eto'o": "Samuel Eto",
    "Eto'o": "Samuel Eto",

    # --- TEKNİK DİREKTÖRLER & YÖNETİCİLER ---
    # NOT: Guardiola DOĞRUDAN 'Guardiola' olarak okunur; asla Gvardiyola yapılmaz!
    "Carlo Ancelotti": "Karlo Ançelotti",
    "Ancelotti": "Ançelotti",
    "José Mourinho": "Jose Morinyo",
    "Jose Mourinho": "Jose Morinyo",
    "Mourinho": "Morinyo",
    "Unai Emery": "Unay Emeri",
    "Emery": "Emeri",
    "Todd Boehly": "Tod Boli",
    "Boehly'nin": "Boli'nin",
    "Boehly": "Boli",
    "Nasser Al-Khelaifi": "Nasır El Helaifi",
    "Al-Khelaifi": "El Helaifi",
    "John Textor": "Con Tekstır",
    "Textor": "Tekstır",
    "Peter Lim": "Pitır Lim",
    "Sheikh Mansour": "Şeyh Mansur",
    "Mansour": "Şeyh Mansur",
    "Suleyman Kerimov": "Süleyman Kerimov",
    "Kerimov": "Süleyman Kerimov",

    # --- STADYUMLAR & ÖZEL YERLER ---
    "Santiago Bernabéu": "Santiago Bernabeu",
    "Santiago Bernabeu": "Santiago Bernabeu",
    "Bernabéu'da": "Bernabeu'da",
    "Bernabéu'ya": "Bernabeu'ya",
    "Bernabéu'nun": "Bernabeu'nun",
    "Bernabéu": "Bernabeu",
    "Bernabeu'da": "Bernabeu'da",
    "Bernabeu'ya": "Bernabeu'ya",
    "Bernabeu'nun": "Bernabeu'nun",
    "Bernabeu": "Bernabeu",

    "Parc des Princes": "Park de Prens",
    "Camp Nou": "Kamp Nu",
    "Nou Mestalla": "Nou Mestaya",
    "Mestalla": "Mestaya",
    "Stamford Bridge": "Stemfırd Bric",
    "Old Trafford": "Old Trafırd",
    "Etihad": "İttihad",

    # --- KULÜPLER (Sadece okunuşu zor olanlar) ---
    "Manchester City": "Mançestır Siti",
    "Man City": "Mançestır Siti",
    "Manchester United": "Mançestır Yunaytıt",
    "Man United": "Mançestır Yunaytıt",
    "Newcastle United": "Nivkasıl Yunaytıt",
    "Newcastle": "Nivkasıl",
    "Tottenham": "Totnım",
    "Chelsea": "Çelsi",
    "Chelsea'nin": "Çelsi'nin",
    "Leeds United": "Lids Yunaytıt",
    "Leeds": "Lids",
    "Portsmouth": "Portsmıs",
    "Paris Saint-Germain": "Paris Sen Jermen",
    "PSG": "Pe-Se-Je",
    "Bordeaux": "Bordo",
    "Schalke 04": "Şalke",
    "Schalke": "Şalke",
    "Rangers FC": "Rencırs",
    "Rangers": "Rencırs",
    "Celtic": "Seltik",
    "Boavista": "Boavişta",
    "Anzhi Makhachkala": "Anji Mahaçkale",
    "Anzhi": "Anji",
    "Super Depor": "Süper Depor",
    "Saudi PIF": "Suudi Pi-Ay-Ef",
    "PIF": "Pi-Ay-Ef",
    "RedBird": "RedBörd",
    "Elliott": "Elyıt",
    "Oaktree Capital": "Oktri Kapital",
    "Oaktree": "Oktri",
    "777 Partners": "Yedi Yedi Yedi Partnırs",

    # --- KISALTMALAR & TERİMLER ---
    "PSR": "Pe-Se-Re",
    "FFP": "Fe-Fe-Pe",
    "UEFA'nın": "U-e-fa'nın",
    "UEFA'ya": "U-e-fa'ya",
    "UEFA": "U-e-fa",
    "FIFA": "Fifa",
    "TFF": "Te-Fe-Fe",
    "CAS": "Kas",
    "CEO": "Si-i-o",
    "CGI": "Si-Ci-Ay",
    "NFL": "En-Ef-El",
    "NBA": "En-Bi-Ey",
    "MLS": "Em-El-Es",
    "Ballon d'Or": "Balon Dor",
    "Ballon D'or": "Balon Dor",
    "Ballon Dor": "Balon Dor"
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


def expand_financial_notations(text: str) -> str:
    """
    Spikerin takılmasını önlemek için para birimi ve finansal gösterimleri Türkçe tam metne açar:
    - €100M / 100M€ -> 100 milyon euro
    - $1B / 1B$ -> 1 milyar dolar
    - £60M / 60M£ -> 60 milyon sterlin
    - 1.35 milyar -> 1 milyar 350 milyon
    - 1.5 milyar -> 1 buçuk milyar
    - %115 -> yüzde 115
    - -15 puan -> eksi 15 puan
    """
    s = text

    # Euro (€) dönüşümleri
    s = re.sub(r'€\s*(\d+(?:[.,]\d+)?)\s*(?:B|milyar|b)\b', r'\1 milyar euro', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:B|milyar|b)\s*€(?!\w)', r'\1 milyar euro', s, flags=re.IGNORECASE)
    s = re.sub(r'€\s*(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\b', r'\1 milyon euro', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\s*€(?!\w)', r'\1 milyon euro', s, flags=re.IGNORECASE)
    s = re.sub(r'€\s*(\d+)\b', r'\1 euro', s)
    s = re.sub(r'\b(\d+)\s*€(?!\w)', r'\1 euro', s)

    # Dolar ($) dönüşümleri
    s = re.sub(r'\$\s*(\d+(?:[.,]\d+)?)\s*(?:B|milyar|b)\b', r'\1 milyar dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:B|milyar|b)\s*\$(?!\w)', r'\1 milyar dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'\$\s*(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\b', r'\1 milyon dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\s*\$(?!\w)', r'\1 milyon dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'\$\s*(\d+)\b', r'\1 dolar', s)
    s = re.sub(r'\b(\d+)\s*\$(?!\w)', r'\1 dolar', s)

    # Sterlin (£) dönüşümleri
    s = re.sub(r'£\s*(\d+(?:[.,]\d+)?)\s*(?:B|milyar|b)\b', r'\1 milyar sterlin', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:B|milyar|b)\s*£(?!\w)', r'\1 milyar sterlin', s, flags=re.IGNORECASE)
    s = re.sub(r'£\s*(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\b', r'\1 milyon sterlin', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\s*£(?!\w)', r'\1 milyon sterlin', s, flags=re.IGNORECASE)
    s = re.sub(r'£\s*(\d+)\b', r'\1 sterlin', s)
    s = re.sub(r'\b(\d+)\s*£(?!\w)', r'\1 sterlin', s)

    # Ondalık sayılar & Özel Milyar İfadeleri
    s = re.sub(r'1[.,]35\s*milyar', '1 milyar 350 milyon', s, flags=re.IGNORECASE)
    s = re.sub(r'1[.,]5\s*milyar', '1 buçuk milyar', s, flags=re.IGNORECASE)
    s = re.sub(r'2[.,]5\s*milyar', '2 buçuk milyar', s, flags=re.IGNORECASE)
    s = re.sub(r'1[.,]5\s*milyon', '1 buçuk milyon', s, flags=re.IGNORECASE)

    # Yüzde ve Eksi puanlar
    s = re.sub(r'%(\d+)', r'yüzde \1', s)
    s = re.sub(r'-(\d+)\s*puan', r'eksi \1 puan', s)

    return s


def normalize_turkish_speech(script: str) -> str:
    """
    Spiker metnini TTS motoruna göndermeden önce otonom olarak optimize eder:
    - İsimleri fonetik sözlükten geçirir (kelime sınırları ile tekil ve güvenli eşleştirme).
    - Finansal sembolleri genişletir (€100M -> 100 milyon euro).
    - Yabancı aksanları temizler (é, á, ó).
    - Belgesel akışını bozan noktalama işaretlerini yumuşatır.
    """
    spoken = script

    # 1. Finansal Semboller ve Rakamları Genişlet
    spoken = expand_financial_notations(spoken)

    # 2. Sözlükteki uzun ifadeler önce çalışacak şekilde sırala ve kelime sınırı (\b) uygula
    sorted_lexicon = sorted(MASTER_PHONETIC_LEXICON.items(), key=lambda x: len(x[0]), reverse=True)
    for written, phonetic in sorted_lexicon:
        # Kısaltmalar (FFP, PSR, TFF vb.) için büyük/küçük harf duyarlı, diğerleri için duyarsız eşleşme
        if written.isupper() and len(written) <= 4:
            pattern = re.compile(r'\b' + re.escape(written) + r'\b')
        else:
            pattern = re.compile(r'\b' + re.escape(written) + r'\b', re.IGNORECASE)
        spoken = pattern.sub(phonetic, spoken)

    # 3. Kalan yabancı diyakritikleri temizle
    spoken = sanitize_foreign_diacritics(spoken)

    # 4. Spiker tonlama yumuşatması (ani tizleşme, bağırma ve kekelemeyi önler)
    spoken = spoken.replace(";", ",")
    spoken = spoken.replace("!", ".")
    spoken = spoken.replace("...", ".")
    spoken = spoken.replace('"', '')
    spoken = spoken.replace("'", "'")
    spoken = re.sub(r'--+', ' - ', spoken)
    spoken = re.sub(r'\s+', ' ', spoken).strip()

    return spoken
