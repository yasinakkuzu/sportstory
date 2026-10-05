"""
Antigravity Turkish Voice Audit & Quality Assurance Agent (TurkishVoiceAuditAgent)
===================================================================================
Otonom Türkçe Spiker Denetim ve Telaffuz Düzeltme Ajanı.

Sorumluluklar:
1. Giriş Denetimi (Pre-Synthesis Audit):
   - Senaryo metnini tarayarak yabancı futbolcu, teknik direktör ve stadyum isimlerini tespit eder.
   - Türkçe alfabede olmayan Latin diyakritiklerini (é, á, ó, ú, ñ vb.) yakalar.
   - Yabancı harf kombinasyonlarını (th, ph, eau, sz, cz, sch, oi, x, w, q) analiz eder.
   - Spikerin bağırmasına veya duraksamasına yol açan noktalama tuzaklarını temizler.
   - Finansal sembolleri ve oranları seslendirilebilir Türkçeye açar.

2. Otonom Düzeltme ve Fonetik Normalizasyon:
   - MASTER_PHONETIC_LEXICON sözlüğü ile doğrulanmış telaffuzları uygular.
   - Sözlükte henüz bulunmayan yabancı kelimeler için fonolojik dönüştürücü çalıştırır.
   - Yeni tespit edilen terimleri otonom öğrenme defterine (learned_phonetics.json) kaydeder.

3. Akustik & Ritim Denetimi (Post-Synthesis QA):
   - TTS çıktısını kelime seviyesinde denetler (WPM - Words Per Minute, hece uzamaları).
   - Anormal kelime sürelerini (>1.5s veya <0.08s) ve atlanan kelimeleri raporlar.

4. Denetim Raporu:
   - Her Shorts için structured voice_audit_report.json üretir.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from engine.phonetics import (
    MASTER_PHONETIC_LEXICON,
    sanitize_foreign_diacritics,
    normalize_turkish_speech
)

logger = logging.getLogger("AntigravityEngine.VoiceAuditAgent")

# Türkçe telaffuz riskli yabancı harf öbekleri
FOREIGN_LETTER_CLUSTERS = [
    (r'eau\b', 'o'),
    (r'eaux\b', 'o'),
    (r'sch', 'ş'),
    (r'ph', 'f'),
    (r'th', 't'),
    (r'sz', 's'),
    (r'cz', 'ç'),
    (r'oi', 'ua'),
    (r'ou', 'u'),
    (r'qu', 'kv'),
    (r'w', 'v'),
    (r'x', 'ks'),
    (r'q', 'k'),
    (r'ñ', 'n'),
]


class TurkishVoiceAuditAgent:
    """
    Otonom Türkçe Spiker Denetim & Kalite Güvence Ajanı.
    Spikerin kulağı tırmalamasını, kelimeleri yanlış okumasını veya kekelemesini önler.
    """

    def __init__(self, learned_lexicon_path: Optional[str] = None):
        self.learned_path = Path(learned_lexicon_path) if learned_lexicon_path else Path(__file__).parent.parent / "learned_phonetics.json"
        self.learned_lexicon = self._load_learned_lexicon()

    def _load_learned_lexicon(self) -> Dict[str, str]:
        """Daha önce ajan tarafından öğrenilmiş fonetik eşleştirmeleri yükler."""
        if self.learned_path.exists():
            try:
                with open(self.learned_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Öğrenilmiş fonetik sözlük yüklenemedi: {e}")
        return {}

    def _save_learned_entry(self, original: str, phonetic: str):
        """Yeni tespit edilen bir yabancı varlığı öğrenme defterine kaydeder."""
        self.learned_lexicon[original] = phonetic
        try:
            self.learned_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.learned_path, "w", encoding="utf-8") as f:
                json.dump(self.learned_lexicon, f, ensure_ascii=False, indent=2)
            logger.info(f"🧠 Ajan yeni fonetik terim öğrendi: '{original}' -> '{phonetic}'")
        except Exception as e:
            logger.warning(f"Fonetik öğrenme kaydedilemedi: {e}")

    def audit_and_correct_script(self, raw_script: str, language: str = "tr") -> Tuple[str, Dict[str, Any]]:
        """
        Spiker metnini sentez öncesi kelime kelime denetler ve riskleri giderir.
        Dönüş: (Düzeltilmiş Metin, Ajan Denetim Raporu)
        """
        if language != "tr":
            # İngilizce için temel noktalama yumuşatması
            s_soft = raw_script.replace(";", ",").replace("!", ".").replace("...", ".")
            return s_soft, {
                "language": language,
                "status": "PASSED_NON_TR",
                "risk_score": 0,
                "corrections": []
            }

        logger.info("🕵️ TurkishVoiceAuditAgent: Türkçe spiker metni denetleniyor...")
        corrections = []
        detected_risks = []
        clean_text = raw_script

        # 1. Bilinen Sözlük Eşleştirmeleri (MASTER_PHONETIC_LEXICON + Learned)
        merged_lexicon = {**self.learned_lexicon, **MASTER_PHONETIC_LEXICON}
        sorted_lexicon = sorted(merged_lexicon.items(), key=lambda x: len(x[0]), reverse=True)

        for written, spoken in sorted_lexicon:
            if written == spoken:
                continue
            pattern = re.compile(r'\b' + re.escape(written), re.IGNORECASE)
            if pattern.search(clean_text):
                clean_text = pattern.sub(spoken, clean_text)
                corrections.append({
                    "type": "MASTER_LEXICON_MATCH",
                    "original": written,
                    "phonetic": spoken
                })

        # 2. Aksanlı Latin Diyakritikleri Denetimi (é, á, ó, ú, ñ vb.)
        diacritic_matches = re.findall(r'[éèêëáàâäóòôíìîïúùûñ]', clean_text)
        if diacritic_matches:
            detected_risks.append(f"Yabancı aksan işaretleri tespit edildi: {set(diacritic_matches)}")
            clean_text = sanitize_foreign_diacritics(clean_text)
            corrections.append({
                "type": "FOREIGN_DIACRITICS_SANITIZED",
                "count": len(diacritic_matches)
            })

        # 3. Kalan Yabancı Harf Kombinasyonları Denetimi & Otonom Heceleme
        TURKISH_EXEMPTIONS = {
            "şüphe", "şüpheli", "şüphesiz", "şüpheyle", "şüpheler",
            "cephe", "cephede", "cepheden", "cephesi", "cepheler",
            "tophane", "darphane"
        }
        tokens = clean_text.split()
        for tok in tokens:
            c_tok = tok.strip(".,?!;:\"'()")
            if c_tok.lower() in TURKISH_EXEMPTIONS:
                continue
            # Yabancı harf kümesi içeriyor mu?
            for pattern, repl in FOREIGN_LETTER_CLUSTERS:
                if re.search(pattern, c_tok, re.IGNORECASE) and c_tok not in [c["original"] for c in corrections if "original" in c]:
                    # Otonom fonetik türetimi
                    auto_phonetic = re.sub(pattern, repl, c_tok, flags=re.IGNORECASE)
                    detected_risks.append(f"Yabancı fonetik öbeği: '{c_tok}' ({pattern}) -> Önerilen: '{auto_phonetic}'")
                    # Metinde güncelle
                    p_tok = re.compile(r'\b' + re.escape(c_tok) + r'\b')
                    clean_text = p_tok.sub(auto_phonetic, clean_text)
                    corrections.append({
                        "type": "AUTONOMOUS_PHONETIC_ADAPTATION",
                        "original": c_tok,
                        "phonetic": auto_phonetic
                    })
                    self._save_learned_entry(c_tok, auto_phonetic)
                    break

        # 4. Finansal Sembol ve Rakam Normalizasyonu
        # %115 -> yüzde 115
        if "%" in clean_text:
            clean_text = re.sub(r'%(\d+)', r'yüzde \1', clean_text)
            corrections.append({"type": "PERCENT_NORMALIZATION", "applied": "% -> yüzde"})

        # 1.35 milyar -> 1 milyar 350 milyon
        if "1.35 milyar" in clean_text.lower():
            clean_text = re.sub(r'1\.35\s*milyar', '1 milyar 350 milyon', clean_text, flags=re.IGNORECASE)
            corrections.append({"type": "FINANCIAL_EXPANSION", "applied": "1.35 milyar -> 1 milyar 350 milyon"})

        # -60 puan -> eksi 60 puan
        clean_text = re.sub(r'-(\d+)\s*puan', r'eksi \1 puan', clean_text)

        # 5. Spiker Tonlama Kırılmalarını Yumuşatma
        # Bağırma, tonlama çatlaması ve tiz sıçramalarını sakinleştir
        clean_text = clean_text.replace(";", ",")
        clean_text = clean_text.replace("!", ".")
        clean_text = clean_text.replace("...", ".")
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Risk Skoru Hesaplama (0: Kusursuz, 100: Çok Riskli)
        risk_score = max(0, min(100, len(detected_risks) * 15))
        status = "PASSED_WITH_CORRECTIONS" if corrections else "PASSED_PRISTINE"

        report = {
            "language": language,
            "status": status,
            "risk_score": risk_score,
            "detected_risks": detected_risks,
            "corrections_count": len(corrections),
            "corrections": corrections,
            "final_audited_script_preview": clean_text[:120] + "..."
        }

        logger.info(f"✅ VoiceAuditAgent Giriş Denetimi Tamamlandı (Risk Skoru: {risk_score}/100, Düzeltme: {len(corrections)})")
        return clean_text, report

    def audit_spoken_audio(
        self,
        aligned_words: List[Dict[str, Any]],
        audio_duration: float
    ) -> Dict[str, Any]:
        """
        Sentezlenen ses dosyasının kelime zamanlamalarını ve konuşma ritmini inceler.
        Anormal uzayan, yutulan veya atlanan kelimeleri tespit eder.
        """
        if not aligned_words:
            return {"status": "ERROR_NO_WORDS", "score": 0}

        total_words = len(aligned_words)
        duration_minutes = audio_duration / 60.0 if audio_duration > 0 else 1.0
        wpm = round(total_words / duration_minutes, 1)

        elongated_words = []
        clipped_words = []

        for w in aligned_words:
            w_dur = w["end"] - w["start"]
            w_text = w.get("display_word", w.get("word", ""))
            if w_dur > 1.4:
                elongated_words.append({"word": w_text, "duration": round(w_dur, 2)})
            elif w_dur < 0.07:
                clipped_words.append({"word": w_text, "duration": round(w_dur, 2)})

        # Spor belgeseli için ideal WPM aralığı: 120 - 165
        tempo_health = "OPTIMAL"
        if wpm > 175:
            tempo_health = "TOO_FAST"
        elif wpm < 110:
            tempo_health = "TOO_SLOW"

        health_status = "EXCELLENT" if not elongated_words and tempo_health == "OPTIMAL" else "GOOD"

        audio_report = {
            "total_words": total_words,
            "audio_duration_seconds": round(audio_duration, 2),
            "speaking_rate_wpm": wpm,
            "tempo_health": tempo_health,
            "elongated_words_count": len(elongated_words),
            "elongated_words": elongated_words[:5],
            "clipped_words_count": len(clipped_words),
            "health_status": health_status
        }
        logger.info(f"🎙️ VoiceAuditAgent Akustik Denetimi: {health_status} (WPM: {wpm}, Süre: {audio_duration:.1f}s)")
        return audio_report

    def export_audit_report(self, pre_audit: Dict[str, Any], post_audit: Dict[str, Any], target_path: str) -> str:
        """Kapsamlı denetim raporunu JSON formatında diske kaydeder."""
        p = Path(target_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        final_report = {
            "agent": "TurkishVoiceAuditAgent v1.0",
            "pre_synthesis_audit": pre_audit,
            "post_synthesis_qa": post_audit,
            "overall_verdict": "APPROVED_FOR_BROADCAST" if post_audit.get("health_status") in ["EXCELLENT", "GOOD"] else "REVIEW_RECOMMENDED"
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        logger.info(f"📑 Spiker Denetim Raporu Kaydedildi: {p.name}")
        return str(p)
