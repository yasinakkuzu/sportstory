"""
Markdown Script Parser & Pydantic Payload Adapter for Antigravity Engine.
Parses structured metadata, narration voiceover, beat breakdown, and YouTube SEO packages
directly into validated VideoPipelinePayload instances.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from engine.schemas import ScenePlan, VideoPipelinePayload

logger = logging.getLogger("AntigravityEngine.ScriptParser")


def parse_script_markdown(filepath: Path) -> Dict[str, Any]:
    """Parses a markdown script into a raw structured dictionary."""
    if not filepath.exists():
        raise FileNotFoundError(f"Script dosyası bulunamadı: {filepath}")

    content = filepath.read_text(encoding="utf-8")

    # 1. Başlık
    title_match = re.search(r'^#\s+(?:SHORTS_\d+:\s*)?(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else filepath.stem

    # 2. Metadata
    parts = filepath.stem.split("_")
    short_id = f"{parts[0]}_{parts[1]}" if len(parts) >= 2 else filepath.stem
    id_match = re.search(r'-\s+\*\*ID\*\*:\s*(\w+)', content)
    if id_match:
        short_id = id_match.group(1).strip()

    topic_match = re.search(r'-\s+\*\*Topic\*\*:\s*(.+)', content)
    topic = topic_match.group(1).strip() if topic_match else ""

    duration_match = re.search(r'-\s+\*\*Target Duration\*\*:\s*(.+)', content)
    target_duration = duration_match.group(1).strip() if duration_match else ""

    # 3. Türkçe Seslendirme Bloğu
    tr_vo = ""
    tr_section_match = re.search(
        r'##\s+📋\s+CapCut Raw Voiceover Copy-Paste Block \(Turkish\)\s*\n(?:>[^\n]*\n+)?(.*?)(?=\n---|\n##|\Z)',
        content,
        re.DOTALL
    )
    if tr_section_match:
        tr_vo = tr_section_match.group(1).strip()
        tr_vo = re.sub(r'^>\s*', '', tr_vo, flags=re.MULTILINE).strip()

    # 4. İngilizce Seslendirme Bloğu
    en_vo = ""
    en_section_match = re.search(
        r'##\s+🌐\s+CapCut Raw Voiceover Copy-Paste Block \(English Global Alternative\)\s*\n(?:>[^\n]*\n+)?(.*?)(?=\n---|\n##|\Z)',
        content,
        re.DOTALL
    )
    if en_section_match:
        en_vo = en_section_match.group(1).strip()
        en_vo = re.sub(r'^>\s*', '', en_vo, flags=re.MULTILINE).strip()

    # 5. Beat Breakdown Tablosu
    beats = []
    table_match = re.search(
        r'##\s+🎬\s+Beat-by-Beat Production Breakdown\s*\n+(.*?)(?=\n---|\n##|\Z)',
        content,
        re.DOTALL
    )
    if table_match:
        table_text = table_match.group(1).strip()
        lines = [line.strip() for line in table_text.splitlines() if line.strip().startswith('|')]
        data_lines = [l for l in lines if not re.match(r'\|\s*:?-+:?\s*\|', l)][1:]

        for line in data_lines:
            cols = [c.strip() for c in line.split('|')[1:-1]]
            if len(cols) >= 5:
                time_range = cols[0].replace('**', '').strip()
                segment = cols[1].replace('**', '').strip()
                snippet = cols[2].strip().replace('"', '')
                b_roll = cols[3].strip()
                on_screen = cols[4].replace('**', '').strip()
                sfx = cols[5].strip() if len(cols) > 5 else ""

                beats.append({
                    "time": time_range,
                    "segment": segment,
                    "snippet": snippet,
                    "b_roll": b_roll,
                    "on_screen_text": on_screen,
                    "sfx": sfx
                })

    # 6. YouTube SEO Paketi
    seo = {}
    seo_match = re.search(
        r'##\s+🚀\s+YouTube SEO & Publishing Package\s*\n+(.*?)(?=\Z)',
        content,
        re.DOTALL
    )
    if seo_match:
        seo_text = seo_match.group(1).strip()
        yt_title_m = re.search(r'-\s+\*\*Title\*\*:\s*(.+)', seo_text)
        seo["title"] = yt_title_m.group(1).strip() if yt_title_m else title

        yt_desc_m = re.search(r'-\s+\*\*Description\*\*:\s*\n?(.*?)(?=-\s+\*\*Tags\*\*|\Z)', seo_text, re.DOTALL)
        seo["description"] = yt_desc_m.group(1).strip() if yt_desc_m else ""

        yt_tags_m = re.search(r'-\s+\*\*Tags\*\*:\s*(.+)', seo_text)
        if yt_tags_m:
            raw_tags = yt_tags_m.group(1).replace('`', '').split(',')
            seo["tags"] = [t.strip() for t in raw_tags if t.strip()]
        else:
            seo["tags"] = []

        yt_comm_m = re.search(r'-\s+\*\*Pinned Comment[^:]*\*\*:\s*\n?(.*)', seo_text)
        seo["pinned_comment"] = yt_comm_m.group(1).strip() if yt_comm_m else ""

    return {
        "id": short_id,
        "title": title,
        "topic": topic,
        "target_duration": target_duration,
        "voiceover_tr": tr_vo,
        "voiceover_en": en_vo,
        "beats": beats,
        "seo": seo,
        "file": str(filepath)
    }


SEGMENT_TRANSLATIONS = {
    "The Hook": "GİRİŞ ANALİZİ",
    "Hook": "GİRİŞ ANALİZİ",
    "The Escalation": "KRİZ DERİNLEŞİYOR",
    "Escalation": "KRİZ DERİNLEŞİYOR",
    "The Breakdown": "FİNANSAL TABLO",
    "Breakdown": "FİNANSAL TABLO",
    "The Climax": "DÖNÜM NOKTASI",
    "Climax": "DÖNÜM NOKTASI",
    "The CTA": "TARTIŞMA & YORUM",
    "CTA": "TARTIŞMA & YORUM"
}

SEGMENT_TRANSLATIONS_EN = {
    "Giriş Analizi": "INTRO ANALYSIS",
    "Kriz Derinleşiyor": "CRISIS ESCALATION",
    "Finansal Tablo": "FINANCIAL BREAKDOWN",
    "Dönüm Noktası": "THE TURNING POINT",
    "Tartışma & Yorum": "DEBATE & DISCUSSION",
    "GİRİŞ ANALİZİ": "INTRO ANALYSIS",
    "KRİZ DERİNLEŞİYOR": "CRISIS ESCALATION",
    "FİNANSAL TABLO": "FINANCIAL BREAKDOWN",
    "DÖNÜM NOKTASI": "THE TURNING POINT",
    "TARTIŞMA & YORUM": "DEBATE & DISCUSSION",
    "The Hook": "INTRO ANALYSIS",
    "The Escalation": "CRISIS ESCALATION",
    "The Breakdown": "FINANCIAL BREAKDOWN",
    "The Climax": "THE TURNING POINT",
    "The CTA": "DEBATE & DISCUSSION"
}

ENGLISH_METADATA = {
    "SHORTS_001": {
        "title": "Barcelona's $1B Disaster That Destroyed a Giant! 💸😱 #shorts #football",
        "description": "How Barcelona turned €222M from the Neymar sale into a staggering €1.35 billion debt mountain. The Coutinho, Dembélé, and Griezmann collapse explained!",
        "tags": ["barcelona", "neymar transfer", "messi tears", "coutinho transfer", "football finance", "barca debt", "football analysis", "champions league"],
        "pinned_comment": "👉 Which panic buy was Barcelona's biggest financial mistake: Coutinho, Dembélé, or Griezmann? Drop your thoughts below!",
        "beats": [
            {
                "headline": "BARCELONA NEYMAR SALE",
                "metric": "€222,000,000 RECORD INCOME",
                "insight": "In 2017, Barcelona received a staggering 222 million euros for Neymar."
            },
            {
                "headline": "ON THE BRINK OF RUIN",
                "metric": "€1,350,000,000 DEBT CRISIS",
                "insight": "Just four years later, they were drowning in 1.35 billion euros of debt."
            },
            {
                "headline": "PANIC TRANSFERS",
                "metric": "€390,000,000 WASTED CAPITAL",
                "insight": "They burned 135M on Coutinho, 135M on Dembélé, and 120M on Griezmann."
            },
            {
                "headline": "WAGE BILL DISASTER: 115%",
                "metric": "MESSI FORCED TO LEAVE",
                "insight": "Unable to register players, they were forced into an emotional farewell to Lionel Messi."
            },
            {
                "headline": "DROP YOUR THOUGHTS BELOW!",
                "metric": "JOIN THE DEBATE",
                "insight": "Can Barcelona ever dominate Europe again? Drop your thoughts below!"
            }
        ]
    },
    "SHORTS_002": {
        "title": "How Chelsea Bypassed Financial Fair Play! 🤯💰 #shorts #chelsea #football",
        "description": "Todd Boehly's 8.5-year contract loophole explained. How Chelsea spent €1 Billion using amortization before UEFA banned it!",
        "tags": ["chelsea", "todd boehly", "amortization", "enzo fernandez", "football finance", "chelsea ffp", "premier league", "football shorts"],
        "pinned_comment": "👉 Is Todd Boehly a financial genius or did he trap Chelsea in a wage nightmare until 2031? Drop your thoughts below!",
        "beats": [
            {
                "headline": "CHELSEA RECORD SPENDING",
                "metric": "€1,000,000,000 TRANSFER SPREE",
                "insight": "Chelsea spent over 1 billion euros on transfers in just two seasons without FFP sanctions."
            },
            {
                "headline": "BOEHLY'S LOOPHOLE",
                "metric": "8.5-YEAR AMORTIZATION",
                "insight": "Instead of standard 5-year deals, Chelsea handed players unprecedented 8.5-year contracts."
            },
            {
                "headline": "ENZO FERNÁNDEZ BALANCE",
                "metric": "STANDARD: €24M / CHELSEA: €14M",
                "insight": "Split over 8.5 years, Enzo's annual book cost dropped from 24 million to just 14 million."
            },
            {
                "headline": "UEFA CLOSES THE LOOPHOLE",
                "metric": "5-YEAR CONTRACT CAP ENFORCED",
                "insight": "UEFA quickly stepped in and capped amortization at 5 years to stop other clubs."
            },
            {
                "headline": "DROP YOUR THOUGHTS BELOW!",
                "metric": "JOIN THE DEBATE",
                "insight": "Is Todd Boehly a financial genius or did he trap Chelsea in a nightmare? Drop your thoughts below!"
            }
        ]
    },
    "SHORTS_003": {
        "title": "Manchester City's 115 Charges Explained in 40s! ⚖️🚨 #shorts #mancity #football",
        "description": "What did Manchester City actually do? Offshore shell sponsorships, Roberto Mancini's secret salary, and potential relegation! Premier League's trial of the century.",
        "tags": ["manchester city 115", "man city trial", "premier league charges", "pep guardiola", "roberto mancini secret salary", "ffp breaches", "city relegation"],
        "pinned_comment": "👉 Will the Premier League actually relegate Manchester City or will money win again? Drop your thoughts below!",
        "beats": [
            {
                "headline": "PREMIER LEAGUE HISTORIC TRIAL",
                "metric": "115 FINANCIAL CHARGES",
                "insight": "The biggest trial in Premier League history: Manchester City faces 115 financial charges."
            },
            {
                "headline": "SECRET MONEY TRANSFERS",
                "metric": "PHANTOM SPONSORSHIPS",
                "insight": "Leaks allege the owners funneled hundreds of millions disguised as independent corporate sponsors."
            },
            {
                "headline": "SUSPICIOUS CONTRACTS",
                "metric": "MANCINI: SHADOW SALARY",
                "insight": "Roberto Mancini allegedly received double his wage through a shadow consultancy firm in Abu Dhabi."
            },
            {
                "headline": "HISTORIC PUNISHMENTS",
                "metric": "RELEGATION & -60 POINTS",
                "insight": "Punishments range from massive point deductions to having league titles stripped, or expulsion."
            },
            {
                "headline": "DROP YOUR THOUGHTS BELOW!",
                "metric": "JOIN THE DEBATE",
                "insight": "Will Manchester City actually face real consequences, or will money triumph once again? Drop your thoughts below!"
            }
        ]
    },
    "SHORTS_004": {
        "title": "PSG's €500M Mbappé Nightmare! 💸😱 #shorts #mbappe #football",
        "description": "PSG spent €500 million trying to keep Kylian Mbappé, only to lose him to Real Madrid for €0! The worst contract and loyalty bonus disaster in sports history.",
        "tags": ["mbappe transfer", "psg mbappe contract", "real madrid mbappe", "mbappe salary", "football finance", "nasser al khelaifi", "worst football contracts"],
        "pinned_comment": "👉 How many world-class players could PSG have bought with that €500M to win the UCL? Drop your thoughts below!",
        "beats": [
            {
                "headline": "MOST EXPENSIVE MISTAKE",
                "metric": "€500,000,000 DISASTER",
                "insight": "PSG made the most expensive mistake in football history just to keep Kylian Mbappé."
            },
            {
                "headline": "ASTRONOMICAL CONTRACT",
                "metric": "€72M SALARY + €80M BONUS",
                "insight": "They offered a 72M annual salary, an 80M loyalty bonus, and team veto power."
            },
            {
                "headline": "LOST YEARS",
                "metric": "0 UCL & 2 SUPERSTARS GONE",
                "insight": "Zero Champions League trophies, Messi and Neymar left, and the club became a hostage."
            },
            {
                "headline": "FREE TRANSFER EXIT",
                "metric": "REAL MADRID: €0 FEE",
                "insight": "After pocketing half a billion euros, Mbappé walked into Real Madrid for zero transfer fee."
            },
            {
                "headline": "DROP YOUR THOUGHTS BELOW!",
                "metric": "JOIN THE DEBATE",
                "insight": "Is this the worst contract in sporting history? Drop your thoughts below!"
            }
        ]
    },
    "SHORTS_005": {
        "title": "How Real Madrid Became Football's €1 Billion Machine! 🏟️💸 #shorts #realmadrid #football",
        "description": "Without oil billionaires or state wealth funds, how did fan-owned Real Madrid break the €1B revenue barrier? The Bernabéu's underground pitch engineering!",
        "tags": ["real madrid bernabeu", "florentino perez", "bernabeu underground greenhouse", "football economics", "real madrid 1 billion revenue", "richest football club"],
        "pinned_comment": "👉 Is Florentino Pérez the greatest club president in football history? Drop your thoughts below!",
        "beats": [
            {
                "headline": "HISTORIC REVENUE BARRIER",
                "metric": "€1,000,000,000 RECORD REVENUE",
                "insight": "Fan-owned Real Madrid became the first club in history to surpass 1 billion euros in annual revenue."
            },
            {
                "headline": "ENGINEERING MARVEL",
                "metric": "30-METER UNDERGROUND GREENHOUSE",
                "insight": "Using an underground 6-story greenhouse 30 meters deep, the pitch retracts automatically."
            },
            {
                "headline": "MONEY PRINTING STADIUM",
                "metric": "365 DAYS COMMERCIAL REVENUE",
                "insight": "The Bernabéu hosts NFL games, concerts, and events, printing money 365 days a year."
            },
            {
                "headline": "NO STATE MONEY REQUIRED",
                "metric": "PURE BUSINESS GENIUS",
                "insight": "Without billionaire or state funding, Florentino Pérez kept Real Madrid at the top of world football."
            },
            {
                "headline": "DROP YOUR THOUGHTS BELOW!",
                "metric": "JOIN THE DEBATE",
                "insight": "Is Florentino Pérez the greatest president in sports history? Drop your thoughts below!"
            }
        ]
    }
}


def convert_script_to_pipeline_payload(
    filepath: Path,
    language: str = "tr",
    output_dir: str = "./output"
) -> VideoPipelinePayload:
    """
    Markdown dosyasını doğrudan doğrulanmış VideoPipelinePayload Pydantic nesnesine dönüştürür.
    Dil seçeneğine göre (TR/EN) sıfır dil sızıntısıyla tam yerel editoryal içerik üretir.
    """
    raw = parse_script_markdown(filepath)
    short_id = raw["id"].upper()
    beats = raw["beats"]
    is_en = (language == "en")

    # Cümleleri veya beat parçalarını eşleştir
    script_text = raw["voiceover_en"] if is_en else raw["voiceover_tr"]
    sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', script_text) if s.strip()]

    # Cümleleri sahnelere orantısal ve editoryal olarak dağıt
    total_beats = len(beats)
    scene_sentences = [[] for _ in range(total_beats)]

    cta_markers = ["drop your thoughts", "comment", "thoughts", "below"] if is_en else ["fikrini", "yorum"]

    if len(sentences) >= total_beats:
        if any(any(m in s.lower() for m in cta_markers) for s in sentences[-2:]):
            body_sents = sentences[:-2]
            cta_sents = sentences[-2:]
        else:
            body_sents = sentences[:-1]
            cta_sents = sentences[-1:]

        num_body_scenes = max(1, total_beats - 1)
        for s_idx, sent in enumerate(body_sents):
            t_idx = min(num_body_scenes - 1, int((s_idx / len(body_sents)) * num_body_scenes))
            scene_sentences[t_idx].append(sent)
        scene_sentences[-1] = cta_sents
    elif sentences:
        for s_idx, sent in enumerate(sentences):
            t_idx = min(total_beats - 1, s_idx)
            scene_sentences[t_idx].append(sent)
    else:
        for idx, b in enumerate(beats):
            scene_sentences[idx].append(b.get("snippet", ""))

    en_pkg = ENGLISH_METADATA.get(short_id, {})
    en_beats = en_pkg.get("beats", [])

    scenes: List[ScenePlan] = []

    for idx, b in enumerate(beats):
        dur = 10.0

        if is_en and idx < len(en_beats):
            eb = en_beats[idx]
            headline = eb["headline"]
            metric = eb["metric"]
            clean_insight = eb["insight"]
        else:
            # Başlık ve Metrik ayrıştırma (Türkçe)
            raw_on_screen = b.get("on_screen_text", "FİNANSAL ANALİZ").replace("<br>", "\n")
            lines = [l.strip() for l in raw_on_screen.split("\n") if l.strip()]

            headline = lines[0] if lines else "FİNANSAL ANALİZ"
            metric = "\n".join(lines[1:]) if len(lines) > 1 else ""
            if not metric and any(char.isdigit() or char in "€$%" for char in headline):
                metric = headline
                headline = "ÖZEL SPOR ANALİZİ"

            raw_insight = b.get("snippet", "").strip().strip('"').strip("'")
            clean_insight = re.sub(r'^\.\.\.?\s*', '', raw_insight)
            clean_insight = re.sub(r'\s*\.\.\.?$', '', clean_insight).strip()

        vo_script = " ".join(scene_sentences[idx]).strip()
        if not vo_script:
            vo_script = clean_insight

        # Son sahnede CTA garantisi
        if idx == total_beats - 1:
            if is_en:
                if not any(m in vo_script.lower() for m in ["drop your thoughts", "comment", "thoughts", "below"]):
                    vo_script = (vo_script.rstrip(".! ") + ". Drop your thoughts below!").strip()
                headline = "DROP YOUR THOUGHTS BELOW!"
                metric = "JOIN THE DEBATE"
                if not clean_insight:
                    clean_insight = "Drop your thoughts in the comments below!"
            else:
                if "fikrini yorumlara yaz" not in vo_script.lower():
                    vo_script = (vo_script.rstrip(".! ") + ". Fikrini yorumlara yaz!").strip()
                headline = "FİKRİNİ YORUMLARA YAZ!"
                metric = "YORUMLARDA TARTIŞALIM"
                if not clean_insight:
                    clean_insight = scene_sentences[-1][0] if len(scene_sentences[-1]) > 1 else "Görüşlerinizi yorumlarda belirtin."

        raw_segment = b.get("segment", f"Bölüm {idx+1}")
        if is_en:
            clean_segment = SEGMENT_TRANSLATIONS_EN.get(raw_segment, raw_segment)
        else:
            clean_segment = SEGMENT_TRANSLATIONS.get(raw_segment, raw_segment)

        scenes.append(ScenePlan(
            scene_id=idx + 1,
            segment_name=clean_segment,
            duration_seconds=dur,
            visual_headline=headline,
            visual_metric=metric,
            visual_insight=clean_insight,
            voiceover_script=vo_script,
            camera_motion="zoom_in" if idx % 2 == 0 else "zoom_out"
        ))

    # Sahne sürelerini kelime yoğunluğuna göre orantıla (toplam 50.0 sn bazında)
    word_counts = [max(1, len(s.voiceover_script.split())) for s in scenes]
    tot_words = sum(word_counts)
    for s, wc in zip(scenes, word_counts):
        s.duration_seconds = round(max(4.0, (wc / tot_words) * 50.0), 1)

    # Toplam süreyi tam 50.0 saniyeye sabitle
    diff = 50.0 - sum(s.duration_seconds for s in scenes)
    scenes[-1].duration_seconds = round(scenes[-1].duration_seconds + diff, 1)

    if is_en and en_pkg:
        title = en_pkg.get("title", raw["title"])
        desc = en_pkg.get("description", raw["topic"])
        tags = en_pkg.get("tags", ["football", "shorts", "sports"])
        pinned = en_pkg.get("pinned_comment", "Drop your thoughts below!")
    else:
        seo = raw.get("seo", {})
        title = seo.get("title", raw["title"])
        desc = seo.get("description", raw["topic"])
        tags = seo.get("tags", ["futbol", "shorts", "spor"])
        pinned = seo.get("pinned_comment", "Fikrini yorumlara yaz!")

    payload = VideoPipelinePayload(
        video_id=raw["id"],
        title=title,
        description=desc,
        tags=tags,
        pinned_comment=pinned,
        scenes=scenes,
        output_dir=output_dir,
        language=language
    )
    return payload


def list_available_scripts(scripts_dir: Path) -> List[Dict[str, Any]]:
    """scripts/ dizinindeki tüm senaryoları keşfeder."""
    files = sorted(scripts_dir.glob("SHORTS_*.md"))
    results = []
    for f in files:
        try:
            parsed = parse_script_markdown(f)
            results.append(parsed)
        except Exception as e:
            logger.warning(f"Uyarı: {f.name} okunamadı: {e}")
    return results
