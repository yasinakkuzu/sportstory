"""
SportStory Turkish NLP & Orthography Intelligence Engine
=========================================================
Türkçe shorts içerikleri için profesyonel dilbilgisi, doğru yazım (TDK),
fonetik seslendirme metni ayrımı ve sayı/para birimi açılım motoru.

Özellikler:
1. Çift Hatlı Metin Ayrımı (Dual-Track Script):
   - Görsel Altyazı (Display Script): TDK kurallarına uygun, doğru kesme işaretli,
     orijinal futbolcu/kulüp isimleriyle tertemiz ekrana basılan metin (Örn: "1999'da", "Stefan Schwarz", "%115").
   - Spiker Metni (Speech Script): Türkçe Edge-TTS'in (AhmetNeural) takılmadan,
     tam telaffuzla ve kekelemeden okuyacağı fonetik ve kelime açılımlı metin
     (Örn: "bin dokuz yüz doksan dokuzda", "Ştefan Şvars", "yüzde yüz on beş").

2. Eksiksiz Sayı & Finansal Açılım Motoru:
   - Yıllar ve Ekler (1999'da -> bin dokuz yüz doksan dokuzda, 2004'ten -> iki bin dörtten)
   - Para Birimleri (€500M -> beş yüz milyon euro, 1.35 milyar euro -> bir milyar üç yüz elli milyon euro)
   - Sıra Sayıları (20. -> yirminci, 1. -> birinci, 3. -> üçüncü)
   - Ondalıklar ve Yüzdeler (99.8 -> doksan dokuz nokta sekiz, %115 -> yüzde yüz on beş)

3. Türkçe İmla ve Yazım Denetimi (TDK Standardı):
   - Özel isimlere gelen eklerde kesme işareti denetimi (Schwarz'ın, City'nin, Real Madrid'e)
   - Soru eki (mı/mi/mu/mü) ayrımı
   - Bağlaç olan da/de ayrımı
"""

import re
from typing import Tuple, List, Dict, Any

# Temel Türkçe Sayı Kelimeleri
UNITS = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
TENS = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]


def integer_to_turkish_words(n: int) -> str:
    """Tam sayıları Türkçe okunuşlarına çevirir (0 - 999 milyar)."""
    if n == 0:
        return "sıfır"
    if n < 0:
        return f"eksi {integer_to_turkish_words(abs(n))}"

    parts = []

    # Milyar
    if n >= 1_000_000_000:
        b = n // 1_000_000_000
        parts.append("bir milyar" if b == 1 else f"{integer_to_turkish_words(b)} milyar")
        n %= 1_000_000_000

    # Milyon
    if n >= 1_000_000:
        m = n // 1_000_000
        parts.append("bir milyon" if m == 1 else f"{integer_to_turkish_words(m)} milyon")
        n %= 1_000_000

    # Bin
    if n >= 1_000:
        th = n // 1_000
        parts.append("bin" if th == 1 else f"{integer_to_turkish_words(th)} bin")
        n %= 1_000

    # Yüz
    if n >= 100:
        h = n // 100
        parts.append("yüz" if h == 1 else f"{UNITS[h]} yüz")
        n %= 100

    # Onluk
    if n >= 10:
        parts.append(TENS[n // 10])
        n %= 10

    # Birlik
    if n > 0:
        parts.append(UNITS[n])

    return " ".join(parts).strip()


def number_with_suffix_to_turkish(num_str: str, suffix: str) -> str:
    """
    Ek almış sayıları Türkçedeki ünlü/ünsüz uyumuna ve sertleşmeye göre seslendirir.
    Örnekler:
    - 1999'da -> bin dokuz yüz doksan dokuzda
    - 2004'ten -> iki bin dörtten
    - 2015'te -> iki bin on beşte
    - 2031'e -> iki bin otuz bire
    - 2000'de -> iki binde
    """
    try:
        n = int(num_str)
        words = integer_to_turkish_words(n)
    except ValueError:
        return f"{num_str}{suffix}"

    clean_suf = suffix.lstrip("'").strip().lower()

    # Sayının son kelimesine göre ekin uyarlanması
    last_word = words.split()[-1] if words else ""

    # Türkçedeki son ses ünlüleri ve sert ünsüzler
    # Sert ünsüzle bitenler (f, s, t, k, ç, ş, h, p): üç, dört, beş, kırk, yetmiş, yüz
    is_sert = last_word in ["üç", "dört", "beş", "kırk", "yetmiş", "yüz"]
    
    # Kalın ünlülüler (a, ı, o, u): altı, dokuz, on, otuz, kırk, altmış, doksan, bin, milyon, milyar
    is_kalin = last_word in ["altı", "dokuz", "on", "otuz", "kırk", "altmış", "doksan", "bin", "milyon", "milyar"]
    # İnce ünlülüler (e, i, ö, ü): bir, iki, üç, dört, beş, yedi, sekiz, yirmi, elli, yetmiş, yüz

    # Ek dönüşümleri (de/da, te/ta, den/dan, ten/tan, e/a, ye/ya)
    if clean_suf in ["de", "da", "te", "ta"]:
        if is_sert:
            adapted = "ta" if is_kalin else "te"
        else:
            adapted = "da" if is_kalin else "de"
    elif clean_suf in ["den", "dan", "ten", "tan"]:
        if is_sert:
            adapted = "tan" if is_kalin else "ten"
        else:
            adapted = "dan" if is_kalin else "den"
    elif clean_suf in ["e", "a", "ye", "ya"]:
        if last_word in ["iki", "altı", "yedi"]:
            adapted = "ya" if is_kalin else "ye"
        else:
            adapted = "a" if is_kalin else "e"
    elif clean_suf in ["i", "ı", "u", "ü", "yi", "yı", "yu", "yü"]:
        if last_word in ["iki", "altı", "yedi"]:
            adapted = "yı" if is_kalin else "yi"
        else:
            adapted = "ı" if is_kalin else "i"
    elif clean_suf in ["in", "ın", "un", "ün", "nin", "nın", "nun", "nün"]:
        if last_word in ["iki", "altı", "yedi"]:
            adapted = "nın" if is_kalin else "nin"
        else:
            adapted = "ın" if is_kalin else "in"
    else:
        adapted = clean_suf

    return f"{words}{adapted}"


def ordinal_to_turkish_words(num_str: str) -> str:
    """Sıra sayılarını kelimeye çevirir (20. -> yirminci, 1. -> birinci)."""
    try:
        n = int(num_str)
    except ValueError:
        return num_str

    base = integer_to_turkish_words(n)
    last = base.split()[-1]

    # Sıra eki eşleştirmeleri
    ORD_MAP = {
        "bir": "birinci", "iki": "ikinci", "üç": "üçüncü", "dört": "dördüncü",
        "beş": "beşinci", "altı": "altıncı", "yedi": "yedinci", "sekiz": "sekizinci",
        "dokuz": "dokuzuncu", "on": "onuncu", "yirmi": "yirminci", "otuz": "otuzuncu",
        "kırk": "kırkıncı", "elli": "ellinci", "altmış": "altmışıncı", "yetmiş": "yetmişinci",
        "seksen": "sekseninci", "doksan": "doksanıncı", "yüz": "yüzüncü", "bin": "bininci",
        "milyon": "milyonuncu", "milyar": "milyarıncı"
    }
    ord_word = ORD_MAP.get(last, f"{last}inci")
    parts = base.split()[:-1] + [ord_word]
    return " ".join(parts)


def expand_all_turkish_numbers_and_currency(text: str) -> str:
    """
    Metindeki tüm sayısal ifadeleri, para birimlerini ve kısaltmaları
    Türkçe spikerin (AhmetNeural) kusursuz okuyacağı kelimelere dönüştürür.
    """
    s = text

    # 1. Finansal Birleşik İfadeler (Milyar / Milyon / Para Birimleri)
    s = re.sub(r'1[.,]35\s*milyar\s*euro', 'bir milyar üç yüz elli milyon euro', s, flags=re.IGNORECASE)
    s = re.sub(r'1[.,]35\s*milyar', 'bir milyar üç yüz elli milyon', s, flags=re.IGNORECASE)
    s = re.sub(r'1[.,]5\s*milyar\s*euro', 'bir buçuk milyar euro', s, flags=re.IGNORECASE)
    s = re.sub(r'1[.,]5\s*milyar', 'bir buçuk milyar', s, flags=re.IGNORECASE)
    s = re.sub(r'2[.,]5\s*milyar', 'iki buçuk milyar', s, flags=re.IGNORECASE)
    s = re.sub(r'1[.,]5\s*milyon', 'bir buçuk milyon', s, flags=re.IGNORECASE)

    # € / $ / £ sembollü ifadeler
    s = re.sub(r'€\s*(\d+(?:[.,]\d+)?)\s*(?:M|milyon)\b', r'\1 milyon euro', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:M|milyon)\s*€(?!\w)', r'\1 milyon euro', s, flags=re.IGNORECASE)
    s = re.sub(r'€\s*(\d+(?:[.,]\d+)?)\s*(?:B|milyar)\b', r'\1 milyar euro', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:B|milyar)\s*€(?!\w)', r'\1 milyar euro', s, flags=re.IGNORECASE)
    s = re.sub(r'€\s*(\d+)\b', r'\1 euro', s)
    s = re.sub(r'\b(\d+)\s*€(?!\w)', r'\1 euro', s)

    s = re.sub(r'\$\s*(\d+(?:[.,]\d+)?)\s*(?:B|milyar)\b', r'\1 milyar dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:B|milyar)\s*\$(?!\w)', r'\1 milyar dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'\$\s*(\d+(?:[.,]\d+)?)\s*(?:M|milyon)\b', r'\1 milyon dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:M|milyon)\s*\$(?!\w)', r'\1 milyon dolar', s, flags=re.IGNORECASE)
    s = re.sub(r'\$\s*(\d+)\b', r'\1 dolar', s)
    s = re.sub(r'\b(\d+)\s*\$(?!\w)', r'\1 dolar', s)

    s = re.sub(r'£\s*(\d+(?:[.,]\d+)?)\s*(?:M|milyon)\b', r'\1 milyon sterlin', s, flags=re.IGNORECASE)
    s = re.sub(r'(\d+(?:[.,]\d+)?)\s*(?:M|milyon)\s*£(?!\w)', r'\1 milyon sterlin', s, flags=re.IGNORECASE)
    s = re.sub(r'£\s*(\d+)\b', r'\1 sterlin', s)
    s = re.sub(r'\b(\d+)\s*£(?!\w)', r'\1 sterlin', s)

    # 2. Yüzdeler ve Oranlar
    s = re.sub(r'%(\d+)', lambda m: f"yüzde {integer_to_turkish_words(int(m.group(1)))}", s)
    s = re.sub(r'\b7/24\b', 'yedi yirmi dört', s)
    s = re.sub(r'-(\d+)\s*puan', lambda m: f"eksi {integer_to_turkish_words(int(m.group(1)))} puan", s)

    # 3. Ondalık Sayılar (Örn: 99.8 -> doksan dokuz nokta sekiz)
    s = re.sub(
        r'\b(\d+)[.,](\d+)\b',
        lambda m: f"{integer_to_turkish_words(int(m.group(1)))} nokta {integer_to_turkish_words(int(m.group(2)))}",
        s
    )

    # 4. Sıra Sayıları (Örn: 20. -> yirminci, 1. -> birinci)
    s = re.sub(r'\b(\d+)\.', lambda m: ordinal_to_turkish_words(m.group(1)), s)

    # 5. Ekli Yıllar ve Sayılar (Örn: 1999'da -> bin dokuz yüz doksan dokuzda, 2004'ten -> iki bin dörtten)
    s = re.sub(
        r"\b(\d{1,4})'([a-zA-ZçğıöşüÇĞİÖŞÜ]+)\b",
        lambda m: number_with_suffix_to_turkish(m.group(1), m.group(2)),
        s
    )

    # 6. Kalan Yalın Sayılar (Örn: 115 -> yüz on beş, 600 -> altı yüz)
    s = re.sub(
        r'\b(\d+)\b',
        lambda m: integer_to_turkish_words(int(m.group(1))),
        s
    )

    return s


def audit_turkish_orthography(text: str) -> Tuple[str, List[str]]:
    """
    Türkçe altyazı metnini imla, noktalama ve TDK standartlarına göre denetler ve düzeltir.
    Görsel altyazının (display text) ekranda profesyonelce durmasını sağlar.
    """
    clean = text
    fixes = []

    # 1. Fazla ve Bozuk Boşlukları Düzelt
    clean = re.sub(r'\s+([,.:;?!])', r'\1', clean)  # Noktalamadan önceki boşluğu kaldır
    clean = re.sub(r'([,.:;?!])([^\s\d])', r'\1 \2', clean)  # Noktalamadan sonra boşluk ekle
    clean = re.sub(r'\s+', ' ', clean).strip()

    # 2. Soru Eki Ayrımı (mi / mı / mu / mü)
    # Örn: "düşer miydi", "mümkün mü", "ceza mıydı"
    soru_patterns = [
        (r'\b(\w+)(miyim|misin|miyiz|siniz|miydi|miş|midir)\b', r'\1 \2'),
        (r'\b(\w+)(mıyım|mısın|mıyız|sınız|mıydı|mış|mıdır)\b', r'\1 \2'),
        (r'\b(\w+)(muyum|musun|muyuz|sunuz|muydu|muş|mudur)\b', r'\1 \2'),
        (r'\b(\w+)(müyüm|müsün|müyüz|sünüz|müydü|müş|müdür)\b', r'\1 \2'),
    ]
    for pat, rep in soru_patterns:
        if re.search(pat, clean):
            clean = re.sub(pat, rep, clean)
            fixes.append(f"Soru eki ayrıldı: {pat}")

    # 3. Kesme İşareti Kontrolü (Özel İsimler)
    # Kulüp ve kişi isimlerine gelen ekler kesmeyle ayrılmalı
    PROPER_NAMES_WITH_SUFFIXES = [
        (r'\bSchwarzın\b', "Schwarz'ın"),
        (r'\bSchwarza\b', "Schwarz'a"),
        (r'\bSchwarzı\b', "Schwarz'ı"),
        (r'\bSchwarzda\b', "Schwarz'da"),
        (r'\bCitynin\b', "City'nin"),
        (r'\bCityye\b', "City'ye"),
        (r'\bMessinin\b', "Messi'nin"),
        (r'\bMessiye\b', "Messi'ye"),
        (r'\bRonaldonun\b', "Ronaldo'nun"),
        (r'\bRinaldoya\b', "Ronaldo'ya"),
        (r'\bSunderlandin\b', "Sunderland'in"),
        (r'\bSunderlande\b', "Sunderland'e"),
        (r'\bBarcelonanın\b', "Barcelona'nın"),
        (r'\bBarcelonaya\b', "Barcelona'ya"),
        (r'\bChelseanin\b', "Chelsea'nin"),
        (r'\bMilana\b', "Milan'a"),
        (r'\bInterin\b', "Inter'in"),
    ]
    for wrong, right in PROPER_NAMES_WITH_SUFFIXES:
        if re.search(wrong, clean, re.IGNORECASE):
            clean = re.sub(wrong, right, clean, flags=re.IGNORECASE)
            fixes.append(f"Kesme işareti düzeltildi: {right}")

    # 4. Çift ve Hatalı Noktalama İşaretlerini Sadeleştir
    clean = re.sub(r'\?{2,}', '?', clean)
    clean = re.sub(r'!{2,}', '!', clean)
    clean = re.sub(r'\.{4,}', '...', clean)

    return clean, fixes
