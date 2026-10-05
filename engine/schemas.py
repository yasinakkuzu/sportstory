"""
Antigravity YouTube Shorts Automation Engine - Data Schemas & Safety Shield
Enforces validation rules, duration constraints, banned-word shields, and CTA standards.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ScenePlan(BaseModel):
    scene_id: int
    segment_name: str = Field(default="BÖLÜM", description="The Hook, The Escalation, The Breakdown, The Climax, The CTA")
    duration_seconds: float = Field(ge=2.5, le=25.0, description="Her sahne 2.5 - 25.0 saniye arasında olmalıdır")
    visual_headline: str = Field(default="", description="Ekran kartındaki büyük saf Türkçe manşet")
    visual_metric: str = Field(default="", description="Büyük finansal rakam veya çarpıcı istatistik (Örn: €222.000.000)")
    visual_insight: str = Field(default="", description="1-2 satırlık temiz Türkçe editoryal analiz")
    voiceover_script: str
    camera_motion: str = Field(default="zoom_in", description="zoom_in, zoom_out, pan_left, pan_right")

    @field_validator("voiceover_script")
    @classmethod
    def check_banned_words(cls, v: str) -> str:
        banned = ["tıklayın", "link profilde", "abone olun hemen", "bahis", "kumar", "şans oyunları"]
        for b in banned:
            if b in v.lower():
                raise ValueError(f"Kara listedeki spam/yasaklı kelime tespit edildi: '{b}'")
        return v


class VideoPipelinePayload(BaseModel):
    video_id: str
    title: str = Field(max_length=100)
    description: str
    tags: List[str]
    pinned_comment: str = Field(default="")
    scenes: List[ScenePlan]
    bgm_path: Optional[str] = None
    output_dir: str = "./output"
    language: str = Field(default="tr", description="'tr' (Türkçe) veya 'en' (İngilizce)")

    @field_validator("scenes")
    @classmethod
    def validate_total_duration(cls, v: List[ScenePlan]) -> List[ScenePlan]:
        total_time = sum(s.duration_seconds for s in v)
        if not (42.0 <= total_time <= 60.0):
            raise ValueError(f"Shorts için toplam süre 42-60 sn arasında olmalı. Hesaplanan: {total_time:.1f}s")
        return v

    @field_validator("scenes")
    @classmethod
    def validate_cta_ending(cls, v: List[ScenePlan]) -> List[ScenePlan]:
        if v:
            last_script = v[-1].voiceover_script.strip().lower()
            allowed = ["fikrini yorumlara yaz", "yorum", "drop your thoughts", "comment", "thoughts", "below"]
            if not any(a in last_script for a in allowed):
                raise ValueError("Son sahne CTA çağrısı ('Fikrini yorumlara yaz!' veya 'Drop your thoughts below!') ile sonlanmalıdır!")
        return v


# --- YENI OTONOM AJAN SEMALARI ---
from pydantic import BaseModel, Field
from typing import List, Optional

class AutoScenePlan(BaseModel):
    scene_idx: int
    text_tr: str
    text_en: str
    visual_prompt: str = Field(description="B-Roll")
    visual_headline_tr: str = ""
    visual_headline_en: str = ""
    visual_metric_tr: str = ""
    visual_metric_en: str = ""
    visual_headline: str = ""
    visual_metric: str = ""
    is_hook: bool = False
    is_cta: bool = False

class AutoScriptPayload(BaseModel):
    id: str
    topic: str
    scenes: List[AutoScenePlan]
    title_en: Optional[str] = None
    description_en: Optional[str] = None
    tags_en: Optional[List[str]] = None
    title_tr: Optional[str] = None
    description_tr: Optional[str] = None
    tags_tr: Optional[List[str]] = None
