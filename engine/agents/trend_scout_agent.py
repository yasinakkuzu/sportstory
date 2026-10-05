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
    "Manchester City: The 115 Charges Trial That Could Relegate a Giant",
    "Vinicius Jr: The $1 Billion Saudi Dilemma & Real Madrid Future",
    "Lyon: John Textor's 500M Debt Crisis & Ligue 1 Relegation Threat",
    "Inter Milan: Oaktree Capital's Takeover From Suning Over 400M Debt",
    "Aston Villa: PSR Red Line & Unai Emery's 100M Emergency Fire Sale",
    "Anzhi Makhachkala: Suleyman Kerimov's Billion-Dollar Fire Sale Disaster",
    "Deportivo La Coruna: The €160M Super Depor Debt Hangover",
    "Leeds United: Borrowed Millions, Goldfish Bowls, and Football's Most Infamous Meltdown",
    "Juventus: The Plusvalenza Artificial Capital Gains Scandal & 15-Point Penalty",
    "Everton: 777 Partners Takeover Collapse & Double Points Deduction Disaster",
    "AC Milan: RedBird Capital 600M Debt Trap & Elliott Management Control",
    "Lyon: John Textor's 500M Debt Crisis & Ligue 1 Relegation Threat",
    "Aston Villa: PSR Red Line & Unai Emery's 100M Emergency Fire Sale",
    "Parma: Calisto Tanzi's Parmalat 14B Fraud That Destroyed a Serie A Giant",
    "Portsmouth: Four Owners in One Season & The Historic Bankruptcy Freefall",
    "Valencia: The Nou Mestalla Ghost Stadium & Peter Lim's Ruin",
    "Rangers FC: The 2012 Liquidation Scandal & Fourth Tier Rebirth",
    "Paris Saint-Germain: The Billion-Euro Financial Fair Play Dodging Machine",
    "Bordeaux: American Private Equity Collapse & Division 4 Relegation",
    "Schalke 04: From Champions League Semi-Finals to Massive Debt Crisis",
    "Malaga CF: Sheikh Al-Thani's Vanishing Millions & Judicial Administration",
    "Anzhi Makhachkala: Suleyman Kerimov's Billion-Dollar Fire Sale Disaster",
    "Inter Milan: Oaktree Capital's Takeover From Suning Over 400M Debt",
    "Boavista: The Portuguese Giant's Rapid Crash From Champions League",
    "Deportivo La Coruna: The €160M Super Depor Debt Hangover"
]

TRENDING_SCANDALS_TR = [
    "Leeds United: Akvaryum Balıklarından İflasa Futbol Tarihinin En Büyük Çöküşü",
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
    "Inter Milan: Suning'in 400 Milyonluk Borcu ve Oaktree Fonunun Kulübe El Koyması"
]


class TrendScoutAgent:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.guard = get_content_guard()

    def find_latest_scandal(self, lang: str = "en") -> str:
        """Kanal diline uygun, soğuma süresine takılmayan benzersiz bir kriz konusunu seçer."""
        logger.info(f"🔍 TrendScoutAgent: Spor finansı kriz gündemi taranıyor (Dil: {lang.upper()})...")
        
        recent_clubs = self.guard.get_recent_clubs(limit=8)
        recent_topics = self.guard.get_recent_topics(limit=15)
        forbidden_str = ", ".join(f"'{c}'" for c in recent_clubs) if recent_clubs else "None"

        # 1. Gemini REST API ile dinamik ve benzersiz kriz konusu üretmeyi dene
        if self.gemini_key and self.gemini_key != "your_gemini_api_key_here":
            for attempt in range(3):
                try:
                    lang_prompt = (
                        f"Suggest ONE sensational European football club financial scandal or insolvency crisis in ENGLISH. "
                        f"CRITICAL RULE: DO NOT use these recently covered clubs/topics: [{forbidden_str}]. "
                        f"Choose a DIFFERENT club (e.g. Bordeaux, Schalke, Malaga, Inter Milan, Anzhi, Aston Villa, Boavista, etc.). "
                        f"Format: 'Club Name: Sensational Subtitle'. Max 75 chars. No quotes, just the headline."
                        if lang == "en" else
                        f"Avrupa futbolunda yaşanmış çarpıcı ve sansasyonel bir finans/borç/iflas krizini TÜRKÇE olarak öner. "
                        f"KESİN KURAL: Şu yakın zamanda işlenmiş kulüpleri KESİNLİKLE önerme: [{forbidden_str}]. "
                        f"Farklı bir kulüp seç (Örn: Bordeaux, Schalke, Malaga, Inter Milan, Anzhi, Boavista vb.). "
                        f"Format: 'Kulüp Adı: Sansasyonel Alt Başlık'. Maksimum 75 karakter. Tırnaksız sadece başlık."
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
