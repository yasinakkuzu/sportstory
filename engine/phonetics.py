"""
Antigravity Sports & Finance Phonetic Intelligence Engine.
Otonom Telaffuz Denetleyicisi ve Fonetik Ön-İşlemci (v2.0 Master Edition).

Özellikler:
1. Türkçe Edge-TTS için küresel futbolcu, teknik direktör, stadyum ve kulüp isimlerini
   doğal Türkçe spiker fonetiğine çevirir (Örn: Mbappé -> Embappe, Bernabéu -> Bernabeu, Vinicius -> Vinisyus).
2. Yabancı aksan işaretlerini (é, á, ó, í, ú, ñ, è, ê, ä, ö, ü) temizleyerek TTS kekelemesini sıfırlar.
3. Finansal sembolleri ve kısaltmaları (€100M, $1B, £60M, %115, PSR, FFP, UEFA, CAS) seslendirilebilir Türkçeye açar.
4. Spikerin nefes kontrolünü ve tonlamasını bozan noktalama işaretlerini belgesel ritmine göre yumuşatır.
"""

import re
import logging
from typing import Dict, Tuple

logger = logging.getLogger("AntigravityEngine.Phonetics")

# 1. KAPSAMLI KÜRESEL FUTBOL VE FİNANS FONETİK SÖZLÜĞÜ (TÜRKÇE SPİKER STANDARDI)
MASTER_PHONETIC_LEXICON: Dict[str, str] = {
    # --- YILDIZ FUTBOLCULAR & EFSANELER ---
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

    "Vinicius Junior": "Vinisyus Cunyır",
    "Vinícius Júnior": "Vinisyus Cunyır",
    "Vinicius Jr": "Vinisyus Cunyır",
    "Vinícius Jr": "Vinisyus Cunyır",
    "Vinicius'a": "Vinisyus'a",
    "Vinicius'un": "Vinisyus'un",
    "Vinicius": "Vinisyus",
    "Vinícius": "Vinisyus",

    "Jude Bellingham": "Cud Belinghem",
    "Bellingham'ın": "Belinghem'in",
    "Bellingham'a": "Belinghem'e",
    "Bellingham": "Belinghem",

    "Erling Haaland": "Örling Holand",
    "Haaland'ın": "Holand'ın",
    "Haaland'a": "Holand'a",
    "Haaland": "Holand",

    "Kevin De Bruyne": "Kevin De Broyne",
    "De Bruyne'nin": "De Broyne'nin",
    "De Bruyne'ye": "De Broyne'ye",
    "De Bruyne": "De Broyne",

    "Phil Foden": "Fil Fodın",
    "Foden'ın": "Fodın'ın",
    "Foden": "Fil Fodın",

    "Lamine Yamal": "Lamin Yamal",
    "Yamal'ın": "Yamal'ın",
    "Yamal": "Lamin Yamal",

    "Robert Lewandowski": "Robert Levandovski",
    "Lewandowski'nin": "Levandovski'nin",
    "Lewandowski'ye": "Levandovski'ye",
    "Lewandowski": "Levandovski",

    "Mohamed Salah": "Muhammed Salah",
    "Mo Salah": "Muhammed Salah",
    "Salah'ın": "Salah'ın",
    "Salah": "Muhammed Salah",

    "Virgil van Dijk": "Vörsıl Van Dayk",
    "Van Dijk'ın": "Van Dayk'ın",
    "Van Dijk": "Van Dayk",

    "Darwin Núñez": "Darvin Nunyez",
    "Darwin Nunez": "Darvin Nunyez",
    "Núñez": "Nunyez",
    "Nunez": "Nunyez",

    "Cole Palmer": "Kol Palmır",
    "Palmer'ın": "Palmır'ın",
    "Palmer": "Kol Palmır",

    "Enzo Fernández": "Enzo Fernandez",
    "Enzo Fernandez": "Enzo Fernandez",
    "Enzo'ya": "Enzo'ya",
    "Enzo'nun": "Enzo'nun",
    "Enzo": "Enzo",

    "Mykhailo Mudryk": "Mihaylo Mudrik",
    "Mudryk'le": "Mudrik'le",
    "Mudryk'e": "Mudrik'e",
    "Mudryk": "Mudrik",

    "Douglas Luiz": "Daglıs Luiz",
    "Luiz'in": "Luiz'in",
    "Luiz": "Luiz",

    "Victor Osimhen": "Viktor Osimen",
    "Osimhen'in": "Osimen'in",
    "Osimhen": "Osimen",

    "Mauro Icardi": "Mauro İkardi",
    "Icardi'nin": "İkardi'nin",
    "Icardi": "İkardi",

    "Dries Mertens": "Dris Mertens",
    "Mertens": "Mertens",

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

    "Ciro Immobile": "Çiro İmmobile",
    "Immobile": "İmmobile",

    "Rafa Silva": "Rafa Silva",

    "Harry Kane": "Heri Keyn",
    "Kane'in": "Keyn'in",
    "Kane": "Keyn",

    "Jamal Musiala": "Camal Musiyala",
    "Musiala": "Musiyala",

    "Florian Wirtz": "Floriyan Virts",
    "Wirtz": "Virts",

    "Philippe Coutinho": "Filip Kutinyo",
    "Coutinho'ya": "Kutinyo'ya",
    "Coutinho'nun": "Kutinyo'nun",
    "Coutinho": "Kutinyo",

    "Ousmane Dembélé": "Usman Dembele",
    "Ousmane Dembele": "Usman Dembele",
    "Dembélé'ye": "Dembele'ye",
    "Dembélé'nin": "Dembele'nin",
    "Dembélé": "Dembele",
    "Dembele'ye": "Dembele'ye",
    "Dembele": "Dembele",

    "Antoine Griezmann": "Antuvan Grizman",
    "Griezmann'a": "Grizman'a",
    "Griezmann'ın": "Grizman'ın",
    "Griezmann": "Grizman",

    "Neymar Jr": "Neymar Cunyır",
    "Neymar'ın": "Neymar'ın",
    "Neymar'a": "Neymar'a",
    "Neymar": "Neymar",

    "Lionel Messi": "Liyonel Messi",
    "Messi'nin": "Messi'nin",
    "Messi'ye": "Messi'ye",
    "Messi": "Messi",

    "Cristiano Ronaldo": "Kristiyano Ronaldo",
    "Ronaldo'nun": "Ronaldo'nun",
    "Ronaldo'ya": "Ronaldo'ya",
    "Ronaldo": "Ronaldo",

    "Samuel Eto'o": "Samuel Eto",
    "Eto'o'ya": "Eto'ya",
    "Eto'o": "Samuel Eto",

    "Roberto Carlos": "Roberto Karlos",

    "Szoboszlai": "Soboslayi",
    "Taylor Swift": "Teylor Svift",

    # --- TEKNİK DİREKTÖRLER & YÖNETİCİLER ---
    "Pep Guardiola": "Pep Gvardiyola",
    "Guardiola'nın": "Gvardiyola'nın",
    "Guardiola'ya": "Gvardiyola'ya",
    "Guardiola": "Gvardiyola",

    "Carlo Ancelotti": "Karlo Ançelotti",
    "Ancelotti'nin": "Ançelotti'nin",
    "Ancelotti": "Ançelotti",

    "José Mourinho": "Joze Morinyo",
    "Jose Mourinho": "Joze Morinyo",
    "Mourinho": "Morinyo",

    "Jürgen Klopp": "Yürgen Kılop",
    "Jurgen Klopp": "Yürgen Kılop",
    "Klopp": "Kılop",

    "Mikel Arteta": "Mikel Arteta",
    "Arteta": "Arteta",

    "Unai Emery": "Unay Emeri",
    "Emery'nin": "Emeri'nin",
    "Emery": "Emeri",

    "Diego Simeone": "Diyego Simeone",
    "Simeone": "Simeone",

    "Erik ten Hag": "Erik ten Hag",
    "Ten Hag": "Ten Hag",

    "Roberto Mancini": "Roberto Mançini",
    "Mancini'ye": "Mançini'ye",
    "Mancini'nin": "Mançini'nin",
    "Mancini": "Mançini",

    "Todd Boehly": "Tod Boli",
    "Boehly'nin": "Boli'nin",
    "Boehly'ye": "Boli'ye",
    "Boehly": "Boli",

    "Nasser Al-Khelaifi": "Nasır El Helaifi",
    "Al-Khelaifi'nin": "El Helaifi'nin",
    "Al-Khelaifi": "El Helaifi",

    "Florentino Pérez": "Florentino Perez",
    "Florentino Perez": "Florentino Perez",
    "Pérez": "Perez",
    "Perez": "Perez",

    "Joan Laporta": "Joan Laporta",
    "Laporta": "Laporta",

    "Sheikh Mansour": "Şeyh Mansur",
    "Mansour": "Şeyh Mansur",

    "Suleyman Kerimov": "Süleyman Kerimov",
    "Kerimov": "Süleyman Kerimov",

    "John Textor": "Con Tekstır",
    "Textor'ın": "Tekstır'ın",
    "Textor": "Tekstır",

    "Peter Lim": "Pitır Lim",
    "Lim'in": "Lim'in",
    "Lim": "Pitır Lim",

    "Calisto Tanzi": "Kalisto Tanzi",
    "Tanzi": "Tanzi",

    "Sheikh Al-Thani": "Şeyh El Sani",
    "Al-Thani": "El Sani",

    # --- KULÜPLER, STADYUMLAR & FONLAR ---
    "Santiago Bernabéu": "Santiyago Bernabeu",
    "Santiago Bernabeu": "Santiyago Bernabeu",
    "Santiago Barnabeu": "Santiyago Bernabeu",
    "Bernabéu'da": "Bernabeu'da",
    "Bernabéu'ya": "Bernabeu'ya",
    "Bernabéu'nun": "Bernabeu'nun",
    "Bernabéu": "Bernabeu",
    "Bernabeu'da": "Bernabeu'da",
    "Bernabeu'ya": "Bernabeu'ya",
    "Bernabeu'nun": "Bernabeu'nun",
    "Bernabeu": "Bernabeu",
    "Santiago": "Santiyago",

    "Parc des Princes": "Park de Prens",
    "Camp Nou": "Kamp Nu",
    "Nou Mestalla": "Nou Mestaya",
    "Mestalla": "Mestaya",
    "Stamford Bridge": "Stemfırd Bric",
    "Etihad": "İttihad",
    "Old Trafford": "Old Trafırd",
    "Anfield": "Enfild",
    "San Siro": "San Siro",
    "La Masia": "La Masiya",

    "Manchester City": "Mançestır Siti",
    "Man City": "Mançestır Siti",
    "Manchester United": "Mançestır Yunaytıt",
    "Man United": "Mançestır Yunaytıt",
    "Newcastle United": "Nivkasıl Yunaytıt",
    "Newcastle'ın": "Nivkasıl'ın",
    "Newcastle'a": "Nivkasıl'a",
    "Newcastle": "Nivkasıl",
    "Aston Villa": "Astın Villa",
    "Villa'yı": "Villa'yı",
    "Tottenham": "Totnım",
    "Liverpool": "Livırpul",
    "Arsenal": "Arsınıl",
    "Chelsea": "Çelsi",
    "Chelsea'nin": "Çelsi'nin",
    "Everton": "Evırtın",
    "Leeds United": "Lids Yunaytıt",
    "Leeds": "Lids",
    "Portsmouth": "Portsmıs",

    "Paris Saint-Germain": "Paris Sen Jermen",
    "PSG": "Pe-Se-Je",
    "Lyon": "Liyon",
    "Bordeaux": "Bordo",

    "Barcelona": "Barselona",
    "Real Madrid": "Real Madrid",
    "Atlético Madrid": "Atletiko Madrid",
    "Atletico Madrid": "Atletiko Madrid",
    "Valencia": "Valensiya",
    "Deportivo La Coruña": "Deportivo La Korunya",
    "Deportivo La Coruna": "Deportivo La Korunya",
    "Deportivo": "Deportivo",
    "Super Depor": "Süper Depor",
    "Malaga CF": "Malaga",
    "Malaga": "Malaga",

    "Bayern Münih": "Bayörn Münih",
    "Bayern Munich": "Bayörn Münih",
    "Borussia Dortmund": "Borusiya Dortmund",
    "Dortmund": "Dortmund",
    "Schalke 04": "Şalke",
    "Schalke": "Şalke",
    "Bayer Leverkusen": "Bayır Levırkuzın",

    "Juventus": "Yuventus",
    "Inter Milan": "İnter Milan",
    "Inter": "İnter",
    "AC Milan": "Milan",
    "Parma": "Parma",
    "Napoli": "Napoli",

    "Rangers FC": "Rencırs",
    "Rangers": "Rencırs",
    "Celtic": "Seltik",
    "Boavista": "Boavişta",
    "Anzhi Makhachkala": "Anji Mahaçkale",
    "Anzhi": "Anji",

    "Saudi PIF": "Suudi Pi-Ay-Ef",
    "Saudi": "Suudi",
    "PIF": "Pi-Ay-Ef",
    "RedBird": "RedBörd",
    "Elliott": "Elyıt",
    "Oaktree Capital": "Oktri Kapital",
    "Oaktree": "Oktri",
    "Suning": "Suning",
    "777 Partners": "Yedi Yedi Yedi Partnırs",
    "Abu Dabi'deki": "Abu Dabi'deki",
    "Abu Dabi": "Abu Dabi",

    # --- KISALTMALAR & TERİMLER ---
    "PSR": "Pe-Se-Re",
    "FFP": "Fe-Fe-Pe",
    "UEFA'nın": "U-e-fa'nın",
    "UEFA'ya": "U-e-fa'ya",
    "UEFA": "U-e-fa",
    "FIFA": "Fifa",
    "TFF": "Te-Fe-Fe",
    "CAS": "Kas",
    "VAR": "Var",
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
    s = re.sub(r'€\s*(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\b', r'\1 milyon euro', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\s*€\b', r'\1 milyon euro', s, flags=re.IGNORECASE)
    s = re.sub(r'€\s*(\d+(?:[.,]\d+)?)\s*(?:B|milyar|b)\b', r'\1 milyar euro', s, flags=re.IGNORECASE)
    s = re.sub(r'€\s*(\d+)\b', r'\1 euro', s)

    # Dolar ($) dönüşümleri
    s = re.sub(r'\$\s*(\d+(?:[.,]\d+)?)\s*(?:B|milyar|b)\b', r'\1 milyar dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:B|milyar|b)\s*\$\b', r'\1 milyar dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'\$\s*(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\b', r'\1 milyon dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'\$\s*(\d+)\b', r'\1 dolar', s)

    # Sterlin (£) dönüşümleri
    s = re.sub(r'£\s*(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\b', r'\1 milyon sterlin', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:M|milyon|m)\s*£\b', r'\1 milyon sterlin', s, flags=re.IGNORECASE)
    s = re.sub(r'£\s*(\d+)\b', r'\1 sterlin', s)

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
        pattern = re.compile(r'\b' + re.escape(written), re.IGNORECASE)
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
