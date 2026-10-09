/**
 * TypeScript API definitions mirroring backend Pydantic schemas.
 */

export type FlawType =
  | 'monotone'
  | 'rushed'
  | 'drag_slow'
  | 'inappropriate_pause'
  | 'missing_pause'
  | 'volume_drop'
  | 'breathy_unclear';

export interface WordMetric {
  index: number;
  text: string;
  start: number;
  end: number;
  duration: number;
  punctuation?: string;
  has_punctuation?: boolean;
  f0_mean_st?: number | null;
  f0_range_st?: number | null;
  energy_mean_db?: number | null;
  articulation_rate?: number | null;
  pause_before_s: number;
  pause_after_s: number;
  z_by_feature: Record<string, number>;
  is_flawed: boolean;
}

export interface TimeSeriesData {
  t: number[];
  f0_st: (number | null)[];
  f0_base_st: (number | null)[];
  f0_mad_upper_st?: (number | null)[];
  f0_mad_lower_st?: (number | null)[];
  energy_db: number[];
  energy_base_db: number[];
  rate: number[];
  pause_mask: number[];
  spectrogram?: {
    matrix: number[][];
    times: number[];
    freqs: number[];
  } | null;
  mfcc?: {
    matrix: number[][];
    times: number[];
    coefficients: number[];
  } | null;
}

export interface GroundedFlaw {
  region_id: string;
  start_s: number;
  end_s: number;
  start_word_idx: number;
  end_word_idx: number;
  words: string;
  flaw_type: FlawType;
  feature: string;
  baseline_value: number;
  observed_value: number;
  delta: number;
  unit: string;
  z_score: number;
  severity: number;
  rationale_text: string;
  why_it_hurts: string;
  secondary_types?: Array<{ flaw_type: string; z_score: number }>;
}

export interface ScoreDimension {
  id: string;
  name: string;
  score: number;
  weight: number;
  weighted_score: number;
  metric_raw: number;
  metric_z: number;
  summary: string;
}

export interface OverallScores {
  overall: number;
  raw_overall?: number;
  grade: string;
  quality_level_est: number;
  dimensions: ScoreDimension[];
}

export interface QualityFlag {
  code: string;
  severity: 'INFO' | 'WARNING' | 'ERROR';
  message: string;
  metric_value?: number | null;
}

export interface AnalysisMeta {
  analysis_id: string;
  audio_sha256: string;
  filename: string;
  duration_s: number;
  sample_rate: number;
  speaker_f0_median_hz: number;
  speaker_energy_median_db: number;
  reference_id?: string | null;
  reference_type: 'ideal_take' | 'population_prior';
  alignment_engine: 'mfa_arpa' | 'torchaudio_ctc' | 'torchaudio_fallback';
  processed_at: string;
}

export interface GroundTruthEvalRow {
  status: 'MATCHED' | 'FALSE_POSITIVE' | 'MISSED_GT';
  detected_id?: string | null;
  detected_type?: string | null;
  detected_span?: [number, number] | null;
  detected_words?: string | null;
  gt_id?: string | null;
  gt_type?: string | null;
  gt_span?: [number, number] | null;
  gt_words?: string | null;
  iou: number;
  start_error_ms?: number | null;
  end_error_ms?: number | null;
  type_match: boolean;
}

export interface AnalysisResult {
  meta: AnalysisMeta;
  words: WordMetric[];
  series: TimeSeriesData;
  flaws: GroundedFlaw[];
  scores: OverallScores;
  quality_flags: QualityFlag[];
  ground_truth_flaws?: any[];
  ground_truth_eval?: GroundTruthEvalRow[];
}

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  stage?: string | null;
  message: string;
  result_id?: string | null;
  error?: string | null;
}

export interface SampleRecording {
  sample_id: string;
  title: string;
  speech_name: string;
  quality_level: number;
  quality_label: string;
  speaker_name: string;
  duration_s: number;
  description: string;
  flaws_count: number;
  audio_url: string;
  transcript: string;
}

export interface ReferenceSpeech {
  reference_id: string;
  name: string;
  speaker: string;
  transcript: string;
}
