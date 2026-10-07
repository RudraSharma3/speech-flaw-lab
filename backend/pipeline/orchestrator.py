"""
Master Pipeline Orchestrator.
Executes the deterministic contrastive speech analytics pipeline end-to-end.
"""

import os
import datetime
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

from backend.pipeline.audio import load_and_preprocess_audio, save_canonical_wav
from backend.pipeline.vad import detect_speech_and_pauses
from backend.pipeline.align import align_audio_with_transcript
from backend.pipeline.features import (
    extract_frame_features_praat,
    extract_spectral_features_librosa,
    aggregate_word_level_features,
)
from backend.pipeline.normalize import normalize_words_against_baseline
from backend.pipeline.grounding import ground_flaw_regions
from backend.pipeline.explain import load_flaw_rules, generate_causal_explanations
from backend.pipeline.scoring import calculate_overall_scores


def run_speech_pipeline(
    audio_source: Any,
    transcript: str,
    filename: str = "uploaded_speech.wav",
    reference_words: Optional[List[Dict[str, Any]]] = None,
    reference_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the full pipeline:
    1. Preprocess audio (16kHz mono, LUFS)
    2. VAD & pause segmentation
    3. Forced alignment (MFA / torchaudio)
    4. Frame & word acoustic feature extraction (Praat + Librosa)
    5. Normalization & robust z-score calculation
    6. Grounding flaw regions snapped to word boundaries
    7. Generating causal explanations
    8. Scoring rubric dimensions
    9. Packaging time-series overlays
    """
    # 1. Load & preprocess
    audio_arr, sr, sha256_hash, audio_meta = load_and_preprocess_audio(audio_source)
    duration_s = audio_meta["duration_s"]

    # 2. VAD
    speech_segs, pause_segs, pause_mask = detect_speech_and_pauses(audio_arr, sr=sr)

    # 3. Forced alignment
    alignment = align_audio_with_transcript(
        audio_arr, transcript, sr=sr, audio_duration_s=duration_s, speech_segments=speech_segs
    )
    raw_words = alignment.words

    # 4. Feature extraction
    praat_feats = extract_frame_features_praat(audio_arr, sr=sr)
    spectral_feats = extract_spectral_features_librosa(audio_arr, sr=sr)

    med_f0 = praat_feats["speaker_median_f0_hz"]
    med_int = praat_feats["speaker_median_intensity_db"]

    word_feats = aggregate_word_level_features(raw_words, praat_feats, med_f0, med_int)

    # 5. Normalization & Z-scores
    normalized_words, ref_type = normalize_words_against_baseline(word_feats, reference_words)

    # 6. Temporal Flaw Grounding
    flaw_rules = load_flaw_rules()
    raw_grounded = ground_flaw_regions(normalized_words, flaw_rules)

    # 7. Causal Explanations
    flaws = generate_causal_explanations(raw_grounded)

    # 8. Scoring
    scores = calculate_overall_scores(normalized_words, flaws)

    # 9. Time Series Packaging (10ms grid)
    hop_s = 0.010
    num_frames = len(praat_feats["times"])
    times = praat_feats["times"]
    
    f0_hz_arr = praat_feats["f0_hz"]
    f0_st = [
        round(12.0 * np.log2(f / med_f0), 2) if (f is not None and f > 0) else None
        for f in f0_hz_arr
    ]
    
    # Baseline F0 curve estimation
    f0_base_st = []
    f0_mad_upper = []
    f0_mad_lower = []
    for f_val in f0_st:
        if f_val is not None:
            f0_base_st.append(0.0)
            f0_mad_upper.append(1.8)
            f0_mad_lower.append(-1.8)
        else:
            f0_base_st.append(None)
            f0_mad_upper.append(None)
            f0_mad_lower.append(None)

    energy_db = [round(e - med_int, 2) for e in praat_feats["intensity_db"]]
    energy_base_db = [0.0 if p == 0 else -15.0 for p in pause_mask[:num_frames]]

    # Word rate mapped to frame time
    rate_arr = []
    for t in times:
        matching_w = next((w for w in normalized_words if w["start"] <= t <= w["end"]), None)
        rate_arr.append(matching_w["articulation_rate"] if matching_w else 0.0)

    # Quality flags
    quality_flags = []
    if audio_meta["clipping_fraction"] > 0.01:
        quality_flags.append({
            "code": "HIGH_CLIPPING",
            "severity": "WARNING",
            "message": f"High audio clipping detected ({audio_meta['clipping_fraction']*100:.1f}% samples clipped).",
            "metric_value": audio_meta["clipping_fraction"],
        })
    if praat_feats["jitter_local"] > 0.03:
        quality_flags.append({
            "code": "HIGH_JITTER",
            "severity": "WARNING",
            "message": f"Elevated vocal jitter ({praat_feats['jitter_local']*100:.1f}%) may indicate rough vocal quality or room resonance.",
            "metric_value": praat_feats["jitter_local"],
        })

    analysis_id = f"analysis_{sha256_hash[:16]}"

    result_payload = {
        "meta": {
            "analysis_id": analysis_id,
            "audio_sha256": sha256_hash,
            "filename": filename,
            "duration_s": round(duration_s, 3),
            "sample_rate": sr,
            "speaker_f0_median_hz": round(med_f0, 1),
            "speaker_energy_median_db": round(med_int, 1),
            "reference_id": reference_id,
            "reference_type": ref_type,
            "alignment_engine": alignment.engine_used,
            "processed_at": datetime.datetime.utcnow().isoformat() + "Z",
        },
        "words": normalized_words,
        "series": {
            "t": [round(t, 3) for t in times],
            "f0_st": f0_st,
            "f0_base_st": f0_base_st,
            "f0_mad_upper_st": f0_mad_upper,
            "f0_mad_lower_st": f0_mad_lower,
            "energy_db": energy_db,
            "energy_base_db": energy_base_db,
            "rate": [round(r, 2) for r in rate_arr],
            "pause_mask": [int(p) for p in pause_mask[:num_frames]],
        },
        "flaws": flaws,
        "scores": scores,
        "quality_flags": quality_flags,
    }

    return result_payload
