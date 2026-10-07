"""
Pydantic v2 schemas for Contrastive Speech Analytics API.
Enforces strict typing, JSON serialization, and API contract fidelity.
"""

from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field


class WordMetric(BaseModel):
    index: int
    text: str
    start: float
    end: float
    duration: float
    f0_mean_st: Optional[float] = None
    f0_range_st: Optional[float] = None
    energy_mean_db: Optional[float] = None
    articulation_rate: Optional[float] = None
    pause_before_s: float = 0.0
    pause_after_s: float = 0.0
    z_by_feature: Dict[str, float] = Field(default_factory=dict)
    is_flawed: bool = False


class TimeSeriesData(BaseModel):
    t: List[float] = Field(description="Time steps in seconds (10ms hop)")
    f0_st: List[Optional[float]] = Field(description="Observed F0 in semitones re speaker median (null for unvoiced)")
    f0_base_st: List[Optional[float]] = Field(description="Baseline reference F0 in semitones")
    f0_mad_upper_st: Optional[List[Optional[float]]] = Field(default=None, description="Upper +1.5 MAD envelope")
    f0_mad_lower_st: Optional[List[Optional[float]]] = Field(default=None, description="Lower -1.5 MAD envelope")
    energy_db: List[float] = Field(description="Observed energy in dB re speaker median")
    energy_base_db: List[float] = Field(description="Baseline reference energy in dB")
    rate: List[float] = Field(description="Instantaneous articulation rate (syllables/s)")
    pause_mask: List[int] = Field(description="1 for pause/silence, 0 for active speech")
    spectrogram: Optional[Dict[str, Any]] = Field(default=None, description="Mel-spectrogram heatmap matrix & freqs")
    mfcc: Optional[Dict[str, Any]] = Field(default=None, description="MFCC coefficient matrix")


class GroundedFlaw(BaseModel):
    region_id: str
    start_s: float
    end_s: float
    start_word_idx: int
    end_word_idx: int
    words: str
    flaw_type: Literal[
        "monotone",
        "rushed",
        "drag_slow",
        "inappropriate_pause",
        "missing_pause",
        "volume_drop",
        "breathy_unclear",
    ]
    feature: str
    baseline_value: float
    observed_value: float
    delta: float
    unit: str
    z_score: float
    severity: float = Field(description="Deterministic severity = duration_s * |z| * type_weight")
    rationale_text: str
    why_it_hurts: str


class ScoreDimension(BaseModel):
    id: str
    name: str
    score: float = Field(ge=0.0, le=100.0)
    weight: float
    weighted_score: float
    metric_raw: float
    metric_z: float
    summary: str


class OverallScores(BaseModel):
    overall: float = Field(ge=0.0, le=100.0, description="Weighted composite rubric score (0-100)")
    grade: str = Field(description="Letter grade (A+, A, B, C, D, F)")
    quality_level_est: int = Field(ge=0, le=4, description="Estimated quality tier (0=egregious to 4=ideal)")
    dimensions: List[ScoreDimension]


class QualityFlag(BaseModel):
    code: str
    severity: Literal["INFO", "WARNING", "ERROR"]
    message: str
    metric_value: Optional[float] = None


class AnalysisMeta(BaseModel):
    analysis_id: str
    audio_sha256: str
    filename: str
    duration_s: float
    sample_rate: int
    speaker_f0_median_hz: float
    speaker_energy_median_db: float
    reference_id: Optional[str] = None
    reference_type: Literal["ideal_take", "population_prior"]
    alignment_engine: Literal["mfa_arpa", "torchaudio_fallback"]
    processed_at: str


class AnalysisResult(BaseModel):
    meta: AnalysisMeta
    words: List[WordMetric]
    series: TimeSeriesData
    flaws: List[GroundedFlaw]
    scores: OverallScores
    quality_flags: List[QualityFlag] = Field(default_factory=list)


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: float = Field(ge=0.0, le=1.0)
    message: str
    result_id: Optional[str] = None
    error: Optional[str] = None


class SampleRecording(BaseModel):
    sample_id: str
    title: str
    speech_name: str
    quality_level: int
    quality_label: str
    speaker_name: str
    duration_s: float
    description: str
    flaws_count: int
    audio_url: str
    transcript: str
