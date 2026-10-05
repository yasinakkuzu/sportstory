"""
SportStory Content Guard & Deduplication Engine
=============================================================================
Tekrarlanan ve mükerrer içeriklerin YouTube'a yüklenmesini engelleyen
merkezi denetim motoru:
1. Kulüp Soğuma Süresi (Club Cooldown): Aynı kulüp belirlenen aralık içinde tekrar işlenemez.
2. Senaryo Mükerrerlik Denetimi (Script Deduplication): SHA256 ve Bulanık (Fuzzy) benzerlik analizi.
3. Başlık Benzersizlik Denetimi (Title Uniqueness): Mevcut ve planlanmış başlıklarla karşılaştırma.
4. Merkezi Yayın Geçmişi (Published History): output/published_history.json veritabanı.
"""

import os
import re
import json
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Tuple, Optional, Dict, Any, Union

logger = logging.getLogger("SportStory.ContentGuard")

HISTORY_FILE = Path("output/published_history.json")
QUEUE_FILE = Path("output/schedule_queue.json")

# Tanınan kulüpler ve eşanlamlıları
KNOWN_CLUBS_MAP = {
    "barcelona": ["barcelona", "barca", "barça", "blaugrana", "camp nou"],
    "everton": ["everton", "toffees", "goodison", "777 partners", "moshiri"],
    "juventus": ["juventus", "juve", "bianconeri", "plusvalenza", "agnelli"],
    "chelsea": ["chelsea", "boehly", "stamford bridge", "blues"],
    "leeds": ["leeds", "leeds united", "elland road", "ridsdale"],
    "ac milan": ["ac milan", "milan", "rossoneri", "redbird", "cardinale", "san siro"],
    "inter milan": ["inter milan", "inter", "nerazzurri", "suning", "zhang"],
    "lyon": ["lyon", "olympique lyonnais", "textor", "dncg"],
    "parma": ["parma", "parma calcio", "parma fc", "parmalat", "tanzi"],
    "rangers": ["rangers", "rangers fc", "ibrox", "craig whyte"],
    "portsmouth": ["portsmouth", "portsmouth fc", "pompey", "fratton park"],
    "valencia": ["valencia", "valencia cf", "peter lim", "mestalla"],
    "psg": ["psg", "paris saint-germain", "paris sg", "parc des princes", "qsi", "al-khelaifi"],
    "manchester city": ["manchester city", "man city", "cityzens", "etihad", "115 charges"],
    "manchester united": ["manchester united", "man united", "man utd", "glazers", "old trafford"],
    "real madrid": ["real madrid", "bernabeu", "florentino", "galacticos"],
    "arsenal": ["arsenal", "gunners", "emirates", "arteta"],
    "liverpool": ["liverpool", "anfield", "klopp", "fenway"],
    "aston villa": ["aston villa", "villa", "unai emery"],
    "roma": ["as roma", "roma", "giallorossi"],
    "napoli": ["napoli", "partenopei", "de laurentiis"],
    "galatasaray": ["galatasaray", "cimbom"],
    "fenerbahce": ["fenerbahce", "fenerbahçe", "kanarya"],
    "besiktas": ["besiktas", "beşiktaş", "kara kartal"],
    "trabzonspor": ["trabzonspor"],
    "dortmund": ["borussia dortmund", "dortmund", "bvb"],
    "bayern": ["bayern munich", "bayern münih", "bayern"],
    "atletico madrid": ["atletico madrid", "atlético madrid", "atletico"],
    "schalke": ["schalke", "schalke 04"],
    "bordeaux": ["bordeaux", "girondins"],
    "malaga": ["malaga", "málaga"],
    "anzhi": ["anzhi", "anzhi makhachkala", "kerimov"],
}


def normalize_text_for_comparison(text: str) -> str:
    """Metni noktalama, emoji ve fazlalık boşluklardan arındırarak normalize eder."""
    if not text:
        return ""
    text = text.lower()
    # Emojileri ve özel sembolleri temizle
    text = re.sub(r'[^\w\s]', ' ', text)
    # Birden fazla boşluğu teke indir
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def compute_text_similarity(text1: str, text2: str) -> float:
    """İki metin arasındaki benzerlik oranını 0.0 - 1.0 aralığında hesaplar."""
    n1 = normalize_text_for_comparison(text1)
    n2 = normalize_text_for_comparison(text2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    return SequenceMatcher(None, n1, n2).ratio()


class ContentGuard:
    def __init__(self, history_file: Path = HISTORY_FILE):
        self.history_file = history_file
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history = self._load_history()
        # Eğer geçmiş dosyası boşsa, mevcut diskteki klasörlerden otomatik doldur (backfill)
        if not self.history:
            self.backfill_from_existing()

    def _load_history(self) -> List[Dict[str, Any]]:
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception as e:
                logger.error(f"Geçmiş dosyası yüklenirken hata: {e}")
        return []

    def _save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Geçmiş dosyası kaydedilirken hata: {e}")

    def extract_club(self, text: str) -> str:
        """Verilen başlıktan veya konudan kulüp adını tespit eder."""
        if not text:
            return "General Football"
        
        lower_text = text.lower()
        
        # 1. Sözlükteki bilinen kulüpleri kontrol et
        for standard_name, aliases in KNOWN_CLUBS_MAP.items():
            for alias in aliases:
                # Kelime sınırı ile eşle
                if re.search(r'\b' + re.escape(alias) + r'\b', lower_text):
                    return standard_name.title()

        # 2. "Club Name: Subtitle" formatından ayrıştır
        if ":" in text:
            prefix = text.split(":", 1)[0].strip()
            if 2 < len(prefix) < 30:
                return prefix

        # 3. Bulunamazsa ilk 2 kelime
        words = text.split()
        return " ".join(words[:2]) if words else "Unknown"

    def get_recent_clubs(self, limit: int = 10) -> List[str]:
        """Son 'limit' videoda işlenen kulüpleri sırasıyla döndürür."""
        clubs = []
        for item in reversed(self.history):
            c = item.get("club")
            if c and c not in clubs:
                clubs.append(c)
            if len(clubs) >= limit:
                break
        return clubs

    def get_recent_topics(self, limit: int = 20) -> List[str]:
        """Son 'limit' videonun konularını döndürür."""
        topics = []
        for item in reversed(self.history):
            t = item.get("topic")
            if t and t not in topics:
                topics.append(t)
            if len(topics) >= limit:
                break
        return topics

    def is_club_on_cooldown(self, topic_or_club: str, cooldown_count: int = 8) -> Tuple[bool, str]:
        """
        Kulübün soğuma süresinde olup olmadığını denetler.
        Son 'cooldown_count' videoda aynı kulüp işlenmişse True döner.
        """
        club = self.extract_club(topic_or_club)
        if not club or club in ["General Football", "Unknown"]:
            return False, ""

        recent_slice = self.history[-cooldown_count:] if len(self.history) >= cooldown_count else self.history
        for idx, item in enumerate(reversed(recent_slice)):
            past_club = item.get("club", "")
            if club.lower() == past_club.lower():
                dist = idx + 1
                return True, f"'{club}' kulübü soğuma süresinde! ({dist} video önce işlendi, sınır: {cooldown_count})"
        
        return False, ""

    def check_script_duplicate(self, script_text: str, threshold: float = 0.70) -> Tuple[bool, str, float]:
        """
        Senaryo metninin geçmişteki videolarla birebir veya benzer olup olmadığını denetler.
        Returns: (is_duplicate: bool, reason: str, max_similarity: float)
        """
        norm_text = normalize_text_for_comparison(script_text)
        if not norm_text or len(norm_text) < 30:
            return False, "Metin çok kısa, doğrulanamadı", 0.0

        script_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()

        max_sim = 0.0
        matching_item = None

        for item in reversed(self.history):
            past_hash = item.get("script_hash")
            if past_hash and past_hash == script_hash:
                return True, f"Birebir aynı senaryo bulundu! (Video ID: {item.get('video_id', 'Bilinmiyor')}, Başlık: {item.get('title')})", 1.0

            past_text = item.get("full_script", "")
            sim = compute_text_similarity(norm_text, past_text)
            if sim > max_sim:
                max_sim = sim
                matching_item = item

        if max_sim >= threshold:
            vid = matching_item.get("video_id", "Kayıtlı")
            tit = matching_item.get("title", "")
            return True, f"Senaryo mevcut bir video ile %{max_sim*100:.1f} benzer! (Video: {vid}, Başlık: {tit})", max_sim

        return False, f"Senaryo benzersiz (En yüksek benzerlik: %{max_sim*100:.1f})", max_sim

    def check_title_duplicate(self, title: str, threshold: float = 0.75) -> Tuple[bool, str, float]:
        """
        Başlığın geçmişteki veya kuyruktaki başlıklarla benzerliğini denetler.
        Returns: (is_duplicate: bool, reason: str, max_similarity: float)
        """
        norm_title = normalize_text_for_comparison(title.replace("#shorts", "").replace("#football", ""))
        if not norm_title:
            return False, "Başlık boş", 0.0

        max_sim = 0.0
        matching_title = ""

        # Geçmiş kayıtları kontrol et
        for item in reversed(self.history):
            past_t = item.get("title", "").replace("#shorts", "").replace("#football", "")
            sim = compute_text_similarity(norm_title, past_t)
            if sim > max_sim:
                max_sim = sim
                matching_title = item.get("title", "")

        if max_sim >= threshold:
            return True, f"Başlık mevcut bir video ile %{max_sim*100:.1f} benzer! ('{matching_title}')", max_sim

        return False, f"Başlık benzersiz (En yüksek benzerlik: %{max_sim*100:.1f})", max_sim

    def can_upload_to_youtube(self, title: str, script_text: str) -> Tuple[bool, str]:
        """
        YouTube'a yükleme öncesi son ve en katı kapı kontrolü (Master Gatekeeper).
        Senaryo veya başlık mükerrerse yüklemeyi KESİNLİKLE reddeder.
        """
        # 1. Senaryo kontrolü
        is_dup_script, reason_script, sim_script = self.check_script_duplicate(script_text, threshold=0.70)
        if is_dup_script:
            logger.error(f"🛑 [ContentGuard REDDİ]: {reason_script}")
            return False, reason_script

        # 2. Başlık kontrolü
        is_dup_title, reason_title, sim_title = self.check_title_duplicate(title, threshold=0.75)
        if is_dup_title:
            logger.error(f"🛑 [ContentGuard REDDİ]: {reason_title}")
            return False, reason_title

        return True, "Onaylandı: İçerik tamamen benzersiz."

    def record_video(self, video_id: str, topic: str, title: str, script_text: str, scenes: list = None):
        """Yeni üretilen veya yüklenen videoyu geçmiş veritabanına kaydeder."""
        norm_text = normalize_text_for_comparison(script_text)
        script_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
        club = self.extract_club(topic if topic else title)

        record = {
            "video_id": video_id,
            "topic": topic,
            "club": club,
            "title": title,
            "script_hash": script_hash,
            "full_script": script_text,
            "scenes_count": len(scenes) if scenes else 5,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        # Eğer video_id zaten varsa güncelle, yoksa ekle
        existing_idx = next((i for i, item in enumerate(self.history) if item.get("video_id") == video_id), -1)
        if existing_idx >= 0:
            self.history[existing_idx] = record
        else:
            self.history.append(record)

        self._save_history()
        logger.info(f"🛡️ [ContentGuard] Yeni video geçmişe kaydedildi: {title} (Kulüp: {club}, ID: {video_id})")

    def backfill_from_existing(self):
        """Mevcut output klasöründeki videoları tarayarak geçmiş veritabanını doldurur."""
        logger.info("🛡️ [ContentGuard] Mevcut video klasörleri geçmiş veritabanına taranıyor...")
        output_dir = Path("output")
        if not output_dir.exists():
            return

        # Kuyruktaki ID'leri oku
        queue_map = {}
        if QUEUE_FILE.exists():
            try:
                with open(QUEUE_FILE, "r", encoding="utf-8") as qf:
                    for q in json.load(qf):
                        queue_map[q.get("id")] = q
            except Exception:
                pass

        count = 0
        for folder in sorted(output_dir.glob("AUTO_SHORTS_*")):
            if not folder.is_dir():
                continue

            script_file = folder / "script.json"
            meta_file = folder / "final_short_en_metadata.json"
            
            if not script_file.exists():
                continue

            try:
                with open(script_file, "r", encoding="utf-8") as sf:
                    sdata = json.load(sf)
                
                topic = sdata.get("topic", "")
                scenes = sdata.get("scenes", [])
                full_text = " ".join([s.get("text_en", "") for s in scenes if isinstance(s, dict)])
                
                title = ""
                vid_id = folder.name
                
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as mf:
                            mdata = json.load(mf)
                            title = mdata.get("title", "")
                            if mdata.get("id"):
                                vid_id = mdata.get("id")
                    except Exception:
                        pass

                if not title:
                    title = sdata.get("title_en", topic)

                if full_text:
                    norm_text = normalize_text_for_comparison(full_text)
                    script_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
                    club = self.extract_club(topic if topic else title)
                    
                    self.history.append({
                        "video_id": vid_id,
                        "folder": folder.name,
                        "topic": topic,
                        "club": club,
                        "title": title,
                        "script_hash": script_hash,
                        "full_script": full_text,
                        "scenes_count": len(scenes),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                    count += 1
            except Exception as e:
                logger.debug(f"Klasör taranırken atlandı {folder.name}: {e}")

        self._save_history()
        logger.info(f"✅ [ContentGuard] Toplam {count} adet geçmiş video veritabanına aktarıldı.")


_instance: Optional[ContentGuard] = None

def get_content_guard() -> ContentGuard:
    global _instance
    if _instance is None:
        _instance = ContentGuard()
    return _instance
