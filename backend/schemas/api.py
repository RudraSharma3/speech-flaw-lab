"""
Pydantic v2 schemas for Contrastive Speech Analytics API.
Enforces strict typing, JSON serialization, and API contract fidelity.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class WordMetric(BaseModel):
    index: int
    text: str
    start: float
    end: float
    duration: float
    punctuation: str = ""
    has_punctuation: bool = False
    f0_mean_st: float | None = None
    f0_range_st: float | None = None
    energy_mean_db: float | None = None
    hnr_mean_db: float | None = None
    articulation_rate: float | None = None
    pause_before_s: float = 0.0
    pause_after_s: float = 0.0
    z_by_feature: dict[str, float] = Field(default_factory=dict)
    is_flawed: bool = False


class TimeSeriesData(BaseModel):
    t: list[float] = Field(description="Time steps in seconds (10ms hop)")
    f0_st: list[float | None] = Field(description="Observed F0 in semitones re speaker median (null for unvoiced)")
    f0_base_st: list[float | None] = Field(description="Baseline reference F0 in semitones")
    f0_mad_upper_st: list[float | None] | None = Field(default=None, description="Upper +1.5 MAD envelope")
    f0_mad_lower_st: list[float | None] | None = Field(default=None, description="Lower -1.5 MAD envelope")
    energy_db: list[float] = Field(description="Observed energy in dB re speaker median")
    energy_base_db: list[float] = Field(description="Baseline reference energy in dB")
    rate: list[float] = Field(description="Instantaneous articulation rate (syllables/s)")
    pause_mask: list[int] = Field(description="1 for pause/silence, 0 for active speech")
    spectrogram: dict[str, Any] | None = Field(default=None, description="Mel-spectrogram heatmap matrix & freqs")
    mfcc: dict[str, Any] | None = Field(default=None, description="MFCC coefficient matrix")


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
    secondary_types: list[dict[str, Any]] = Field(default_factory=list)


class ScoreDimension(BaseModel):
    id: str
    name: str
    score: float | None = Field(default=None, ge=0.0, le=100.0)
    weight: float
    weighted_score: float
    metric_raw: float
    metric_z: float
    summary: str


class OverallScores(BaseModel):
    overall: float = Field(ge=0.0, le=100.0, description="Weighted composite rubric score (0-100)")
    grade: str = Field(description="Letter grade (A+, A, B, C, D, F)")
    quality_level_est: int = Field(ge=0, le=4, description="Estimated quality tier (0=egregious to 4=ideal)")
    dimensions: list[ScoreDimension]


class QualityFlag(BaseModel):
    code: str
    severity: Literal["INFO", "WARNING", "ERROR"]
    message: str
    metric_value: float | None = None


class AnalysisMeta(BaseModel):
    analysis_id: str
    audio_sha256: str
    filename: str
    duration_s: float
    sample_rate: int
    speaker_f0_median_hz: float
    speaker_energy_median_db: float
    reference_id: str | None = None
    reference_type: Literal["ideal_take", "population_prior"]
    alignment_engine: Literal["mfa_arpa", "torchaudio_ctc", "torchaudio_fallback", "torchaudio_mms_fa"]
    processed_at: str


class AnalysisResult(BaseModel):
    meta: AnalysisMeta
    words: list[WordMetric]
    series: TimeSeriesData
    flaws: list[GroundedFlaw]
    scores: OverallScores
    quality_flags: list[QualityFlag] = Field(default_factory=list)
    ground_truth_flaws: list[dict[str, Any]] = Field(default_factory=list)
    ground_truth_eval: list[dict[str, Any]] = Field(default_factory=list)


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: float = Field(ge=0.0, le=1.0)
    stage: str | None = Field(default=None, description="Active processing stage")
    message: str
    result_id: str | None = None
    error: str | None = None


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
