"""
Antigravity TrendScoutAgent
=============================================================================
Otonom Araştırma Ajanı: Spor finansı, skandallar ve krizler için gündem tarar.
Kanal diline göre (EN veya TR) çarpıcı ve yüksek etkileşimli konular keşfeder.
ContentGuard entegrasyonu ile kulüp soğuma süresi (cooldown) ve
mükerrer içerik engellemesini garanti altına alır.
"""

import os
import random
import logging
import requests
from typing import Optional, List
from engine.guards.content_guard import get_content_guard

logger = logging.getLogger("AntigravityEngine.TrendScout")

TRENDING_SCANDALS_EN = [
    # --- Pillar 1: Absurd Football Contracts & Clauses ---
    "Stefan Schwarz: The Space Flight Ban Contract Clause",
    "Dennis Bergkamp: The Non-Flying Dutchman Contract Clause",
    "Neil Ruddock: The 99.8kg Weight Limit Penalty Clause",
    "Giuseppe Reina: The Free Lego House Every Year Clause",
    "Ronaldinho: The Two Nights Clubbing Per Week Clause",
    "Roberto Firmino: The Anti-Arsenal 82M Release Clause",
    "Ali Dia: The 53-Minute Premier League Con Artist",

    # --- Pillar 2: Club Crises & Financial Scandals ---
    "Manchester City: The 115 Charges Trial That Could Relegate a Giant",
    "Barcelona: How FC Barcelona Lost One Billion Euros",
    "Lyon: John Textor's 500M Debt Crisis & Ligue 1 Relegation Threat",
    "Inter Milan: Oaktree Capital's Takeover From Suning Over 400M Debt",
    "Aston Villa: PSR Red Line & Unai Emery's 100M Emergency Fire Sale",
    "Juventus: The Plusvalenza Artificial Capital Gains Scandal & 15-Point Penalty",
    "Chelsea: The £1 Billion 8-Year Contract Loophole",
    "Everton: 777 Partners Takeover Collapse & Double Points Deduction Disaster",
    "AC Milan: RedBird Capital 600M Debt Trap & Elliott Management Control",
    "Leeds United: Borrowed Millions, Goldfish Bowls, and Football's Most Infamous Meltdown",
    "Parma: Calisto Tanzi's Parmalat 14B Fraud That Destroyed a Serie A Giant",
    "Portsmouth: Four Owners in One Season & The Historic Bankruptcy Freefall",
    "Valencia: The Nou Mestalla Ghost Stadium & Peter Lim's Ruin",
    "Rangers FC: The 2012 Liquidation Scandal & Fourth Tier Rebirth",
    "Paris Saint-Germain: The Billion-Euro Financial Fair Play Dodging Machine",
    "Bordeaux: American Private Equity Collapse & Division 4 Relegation",
    "Schalke 04: From Champions League Semi-Finals to Massive Debt Crisis",
    "Malaga CF: Sheikh Al-Thani's Vanishing Millions & Judicial Administration",
    "Anzhi Makhachkala: Suleyman Kerimov's Billion-Dollar Fire Sale Disaster",
    "Deportivo La Coruna: The €160M Super Depor Debt Hangover",
    "Boavista: The Portuguese Giant's Rapid Crash From Champions League",

    # --- Pillar 3: Wealth & Crazy Salaries ---
    "Cristiano Ronaldo: The $7 Per Second Al Nassr Fortune",
    "Neymar: The Private Jet Fleet & Saudi Palace Demands",
    "Lionel Messi: The Apple TV Revenue Share & Inter Miami Stake",
    "Kylian Mbappe: The 150M Real Madrid Signing Bonus Breakdown",
    "Erling Haaland: The €1 Million Per Goal Scoring Machine",
    "Vinicius Jr: The $1 Billion Saudi Dilemma & Real Madrid Future"
]

TRENDING_SCANDALS_TR = [
    # --- Pillar 1: Absürt Sözleşme Maddeleri & Futbolun Sahtekarları ---
    "Stefan Schwarz: Uzaya Gitmesi Yasaklanan Futbolcu",
    "Dennis Bergkamp: Uçak Korkusu ve Uçamayan Hollandalı Maddesi",
    "Neil Ruddock: 99.8 Kilo Sınırı ve Kilo Başına Para Cezası",
    "Giuseppe Reina: Her Yıl Ücretsiz Lego Ev Maddesi",
    "Ronaldinho: Haftada 2 Gece Kulübü Serbestliği Maddesi",
    "Roberto Firmino: Arsenal'a Satılamaz Maddesi",
    "Ali Dia: Premier Lig'i Dolandıran 53 Dakikalık Sahte Futbolcu",

    # --- Pillar 2: Kulüp Krizleri & Skandallar & 115 Kural ---
    "Manchester City: 115 Kural İhlali ve Küme Düşme Davası",
    "Barcelona: 1.35 Milyar Euroluk Borç Bataklığı ve Messi'nin Vedası",
    "Chelsea: 1 Milyar Sterlinlik Harcama ve 8 Yıllık Kontrat Hilesi",
    "Aston Villa: 100 Milyonluk Finansal Kural Çıkmazı ve Acil Oyuncu Satışı",
    "Juventus: Sahte Sermaye Skandalı ve 15 Puan Silme Felaketi",
    "Everton: 777 Partners Fiyaskosu ve Arka Arkaya Puan Silme Cezaları",
    "AC Milan: RedBird ve Elliott Fonu Arasındaki 600 Milyonluk Borç Kıskacı",
    "Lyon: John Textor'ın 500 Milyon Euroluk Borcu ve Küme Düşme Tehlikesi",
    "Parma: Parmalat'ın 14 Milyar Euroluk Batışı ve Bir Devi Yok Eden İflas",
    "Portsmouth: 1 Yılda 4 Sahip Değiştiren İngiliz Devinin Trajik İflası",
    "Valencia: Nou Mestalla Hayalet Stadyumu ve Peter Lim'in Yıkımı",
    "Rangers FC: 2012 Tasfiye Felaketi ve 4. Ligden Yeniden Doğuş",
    "Paris Saint-Germain: 1.5 Milyar Euroluk UEFA FFP Hile Çarkı",
    "Bordeaux: Amerikan Fonunun İflası ve 4. Lige Düşürülme Skandalı",
    "Schalke 04: Şampiyonlar Ligi Yarı Finalinden Devasa Borç Batağına",
    "Malaga CF: Katarlı Şeyhin Kaybolan Milyonları ve Kayyum Dönemi",
    "Inter Milan: Suning'in 400 Milyonluk Borcu ve Oaktree Fonunun Kulübe El Koyması",
    "Anzhi: Bir Milyar Dolarlık Rüyanın Sonu ve Dağıstan Fiyaskosu",
    "Deportivo La Coruna: Şampiyonlar Ligi Yarı Finalinden 3. Lige Çöküş",
    "Leeds United: Akvaryum Balıklarından İflasa Futbol Tarihinin En Büyük Çöküşü",

    # --- Pillar 3: Saniyede Kazanılan Servetler & Maaşlar ---
    "Cristiano Ronaldo: Saniyede 7 Dolar Kazanan Servet Makinesi",
    "Neymar: Özel Jet Filosu ve Suudi Sarayı Talepleri",
    "Lionel Messi: Apple TV Gelir Ortaklığı ve Inter Miami Hisseleri",
    "Kylian Mbappe: Real Madrid'den 150 Milyon Euroluk İmza Primi",
    "Erling Haaland: Gol Başına 1 Milyon Euroluk Kazanç Çarkı",
    "Vinicius Jr: 1 Milyar Dolarlık Suudi Teklifi ve Real Madrid İkilemi"
]


class TrendScoutAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.guard = get_content_guard()

    def find_latest_scandal(self, lang: str = "en") -> str:
        """Kanal diline uygun, soğuma süresine takılmayan benzersiz bir kriz konusunu seçer."""
        logger.info(f"🔍 TrendScoutAgent: Spor finansı ve viral konular taranıyor (Dil: {lang.upper()})...")
        
        recent_clubs = self.guard.get_recent_clubs(limit=8)
        recent_topics = self.guard.get_recent_topics(limit=15)
        forbidden_str = ", ".join(f"'{c}'" for c in recent_clubs) if recent_clubs else "None"

        # 1. Gemini REST API ile dinamik ve benzersiz kriz / absürt sözleşme / servet konusu üretmeyi dene
        if self.gemini_key and self.gemini_key != "your_gemini_api_key_here":
            for attempt in range(3):
                try:
                    lang_prompt = (
                        f"Suggest ONE sensational football story in ENGLISH from one of these 3 pillars: "
                        f"1) Absurd player contract clauses / con artists, "
                        f"2) Club financial scandals / debt collapse / FFP trials, "
                        f"3) Shocking real-time player wealth and second-by-second earnings. "
                        f"CRITICAL RULE: DO NOT use these recently covered subjects: [{forbidden_str}]. "
                        f"Format: 'Entity or Club: Sensational Subtitle'. Max 75 chars. No quotes, just headline."
                        if lang == "en" else
                        f"Futboldan şu 3 alandan birinde sansasyonel ve merak uyandırıcı bir TÜRKÇE konu öner: "
                        f"1) Absürt sözleşme maddeleri ve futbol sahtekarları, "
                        f"2) Kulüp finansal krizleri, iflaslar ve 115 kural davaları, "
                        f"3) Futbolcuların saniyelik kazançları ve akıl almaz servetleri. "
                        f"KESİN KURAL: Şu yakın zamanda işlenmiş konuları KESİNLİKLE önerme: [{forbidden_str}]. "
                        f"Format: 'Kişi veya Kulüp: Sansasyonel Alt Başlık'. Maksimum 75 karakter. Tırnaksız sadece başlık."
                    )
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={self.gemini_key}"
                    res = requests.post(
                        url,
                        json={"contents": [{"parts": [{"text": lang_prompt}]}]},
                        headers={"Content-Type": "application/json"},
                        timeout=14
                    )
                    if res.status_code == 200:
                        text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        text = text.replace('"', '').replace("'", "").strip()
                        
                        # Soğuma ve mükerrerlik denetimi
                        is_cooldown, reason = self.guard.is_club_on_cooldown(text, cooldown_count=7)
                        if is_cooldown:
                            logger.warning(f"⚠️ Gemini önerisi reddedildi ({reason}). Yeniden deneniyor...")
                            continue
                            
                        if 15 < len(text) < 100:
                            logger.info(f"✅ Gemini ile benzersiz kriz konusu onaylandı: {text}")
                            return text
                except Exception as e:
                    logger.warning(f"Dinamik trend taraması denemesinde hata: {e}")

        # 2. Küratörlü Havuzdan Seç (Soğuma süresindeki kulüpleri filtrele)
        scandals = TRENDING_SCANDALS_EN if lang == "en" else TRENDING_SCANDALS_TR
        available = [s for s in scandals if not self.guard.is_club_on_cooldown(s, cooldown_count=6)[0]]
        
        # Eğer hepsi soğumadaysa sınırı 3'e düşür
        if not available:
            available = [s for s in scandals if not self.guard.is_club_on_cooldown(s, cooldown_count=3)[0]]
        if not available:
            available = scandals

        chosen = random.choice(available)
        logger.info(f"✅ TrendScout kriz konusunu belirledi (Havuzdan): {chosen}")
        return chosen
