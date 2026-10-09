"""
Master Pipeline Orchestrator.
Executes the deterministic contrastive speech analytics pipeline end-to-end.
"""

import datetime
from typing import Any

import numpy as np
from backend.pipeline.align import align_audio_with_transcript
from backend.pipeline.audio import load_and_preprocess_audio
from backend.pipeline.explain import generate_causal_explanations, load_flaw_rules
from backend.pipeline.features import (
    aggregate_word_level_features,
    extract_frame_features_praat,
    extract_spectral_features_librosa,
)
from backend.pipeline.grounding import ground_flaw_regions
from backend.pipeline.normalize import normalize_words_against_baseline
from backend.pipeline.scoring import calculate_overall_scores
from backend.pipeline.vad import detect_speech_and_pauses


def run_speech_pipeline(
    audio_source: Any,
    transcript: str,
    filename: str = "uploaded_speech.wav",
    reference_words: list[dict[str, Any]] | None = None,
    reference_id: str | None = None,
    cached_context: dict[str, Any] | None = None,
    progress_callback: Any = None,
) -> dict[str, Any]:
    """
    Executes the full pipeline with stage-wise progress callback support.
    """
    def _report(p: float, stage: str, msg: str):
        if callable(progress_callback):
            try:
                progress_callback(p, stage, msg)
            except Exception:
                pass

    if cached_context is not None:
        _report(0.2, "Cache Retrieval", "Loading precomputed acoustic features...")
        audio_arr = cached_context["audio_arr"]
        sr = cached_context["sr"]
        sha256_hash = cached_context["sha256_hash"]
        audio_meta = cached_context["audio_meta"]
        duration_s = audio_meta["duration_s"]
        speech_segs = cached_context["speech_segs"]
        pause_mask = cached_context["pause_mask"]
        raw_words = cached_context["raw_words"]
        praat_feats = cached_context["praat_feats"]
        med_f0 = cached_context["med_f0"]
        med_int = cached_context["med_int"]
        word_feats = cached_context["word_feats"]
        alignment_engine = cached_context.get("alignment_engine", "torchaudio_mms_fa")
    else:
        # 1. Load & preprocess
        _report(0.10, "Audio Ingestion", "Preprocessing audio and LUFS normalization...")
        audio_arr, sr, sha256_hash, audio_meta = load_and_preprocess_audio(audio_source)
        duration_s = audio_meta["duration_s"]

        # 2. VAD
        _report(0.25, "VAD Segmentation", "Detecting speech and silence pauses...")
        speech_segs, _, pause_mask = detect_speech_and_pauses(audio_arr, sr=sr)

        # 3. Forced alignment
        _report(0.40, "Forced Alignment", "Running Torchaudio MMS_FA forced alignment...")
        alignment = align_audio_with_transcript(
            audio_arr, transcript, sr=sr, audio_duration_s=duration_s, speech_segments=speech_segs
        )
        raw_words = alignment.words
        alignment_engine = alignment.engine_used

        # 4. Feature extraction
        _report(0.70, "Feature Extraction", "Extracting Parselmouth Praat F0 & spectral features...")
        praat_feats = extract_frame_features_praat(audio_arr, sr=sr)
        _ = extract_spectral_features_librosa(audio_arr, sr=sr)

        med_f0 = praat_feats["speaker_median_f0_hz"]
        med_int = praat_feats["speaker_median_intensity_db"]

        word_feats = aggregate_word_level_features(raw_words, praat_feats, med_f0, med_int)

    # 5. Normalization & Z-scores
    _report(0.85, "Statistical Grounding", "Normalizing words against baseline and grounding flaws...")
    normalized_words, ref_type = normalize_words_against_baseline(word_feats, reference_words)

    # STRICT ASSERTION: Pipeline result words must match alignment single source of truth
    assert len(normalized_words) == len(raw_words), (
        f"Word count mismatch: result has {len(normalized_words)}, alignment has {len(raw_words)}"
    )
    for i, (w_norm, w_align) in enumerate(zip(normalized_words, raw_words, strict=True)):
        assert w_norm["start"] == w_align["start"], (
            f"Word #{i} ({w_norm['text']}) start mismatch: result {w_norm['start']} vs alignment {w_align['start']}"
        )
        assert w_norm["end"] == w_align["end"], (
            f"Word #{i} ({w_norm['text']}) end mismatch: result {w_norm['end']} vs alignment {w_align['end']}"
        )
        assert w_norm["text"] == w_align["text"], (
            f"Word #{i} text mismatch: result '{w_norm['text']}' vs alignment '{w_align['text']}'"
        )

    # 6. Temporal Flaw Grounding
    flaw_rules = load_flaw_rules()
    raw_grounded = ground_flaw_regions(normalized_words, flaw_rules, reference_type=ref_type)

    # 7. Causal Explanations
    flaws = generate_causal_explanations(raw_grounded)

    # 8. Scoring
    _report(0.95, "Rubric Scoring", "Computing calibrated 0-100 rubric dimensions...")
    scores = calculate_overall_scores(normalized_words, flaws, reference_type=ref_type)

    # 9. Time Series Packaging (10ms grid)
    times = praat_feats["times"]
    num_frames = len(times)
    
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
    rate_arr = [0.0] * num_frames
    for w in normalized_words:
        s_idx = max(0, int(w["start"] / 0.01))
        e_idx = min(num_frames, int(w["end"] / 0.01) + 1)
        for idx in range(s_idx, e_idx):
            rate_arr[idx] = round(w["articulation_rate"], 2)

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
            "alignment_engine": alignment_engine,
            "processed_at": datetime.datetime.now(datetime.UTC).isoformat(),
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
        "_cached_context": {
            "audio_arr": audio_arr,
            "sr": sr,
            "sha256_hash": sha256_hash,
            "audio_meta": audio_meta,
            "speech_segs": speech_segs,
            "pause_mask": pause_mask,
            "raw_words": raw_words,
            "praat_feats": praat_feats,
            "med_f0": med_f0,
            "med_int": med_int,
            "word_feats": word_feats,
            "alignment_engine": alignment_engine,
        },
    }

    return result_payload
