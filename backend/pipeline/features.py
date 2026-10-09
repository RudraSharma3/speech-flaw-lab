"""
Acoustic feature extraction module.
Integrates Parselmouth (Praat), Librosa, and Scipy for mathematically rigorous frame and word-level features.
Filters HNR strictly to voiced frames and computes speech rate excluding pauses >= 250ms.
"""

import os
import re
from typing import Any

import librosa
import numpy as np
import parselmouth
import yaml
from parselmouth.praat import call

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "thresholds.yaml")


def load_features_config() -> dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f).get("features", {})
    return {
        "frame_step_s": 0.010,
        "frame_length_s": 0.025,
        "f0_praat": {"floor_hz": 75.0, "ceiling_hz": 500.0, "time_step_s": 0.010},
        "intensity": {"floor_db": 30.0, "time_step_s": 0.010},
        "mfcc": {"n_mfcc": 13, "n_mels": 40, "n_fft": 512, "hop_length": 160},
    }


def extract_frame_features_praat(
    audio_arr: np.ndarray, sr: int = 16000
) -> dict[str, Any]:
    """
    Extracts frame-level F0, intensity, and HNR using Parselmouth (Praat C engine).
    Implements a two-pass speaker-adaptive pitch floor/ceiling calculation.
    Filters HNR strictly to voiced frames (excludes Praat -200 dB / undefined).
    """
    cfg = load_features_config()
    hop_s = cfg.get("frame_step_s", 0.010)
    total_dur = len(audio_arr) / sr

    # Create Parselmouth Sound
    sound = parselmouth.Sound(audio_arr, sampling_frequency=sr)

    # Pass 1: Broad pitch tracking to find speaker median and percentiles
    init_floor = cfg.get("f0_praat", {}).get("floor_hz", 75.0)
    init_ceil = cfg.get("f0_praat", {}).get("ceiling_hz", 500.0)
    
    pitch_pass1 = sound.to_pitch_ac(
        time_step=hop_s,
        pitch_floor=init_floor,
        pitch_ceiling=init_ceil,
        very_accurate=True
    )
    
    p1_vals = pitch_pass1.selected_array["frequency"]
    voiced_p1 = p1_vals[p1_vals > 0]

    if len(voiced_p1) >= 5:
        p5 = float(np.percentile(voiced_p1, 5.0))
        p95 = float(np.percentile(voiced_p1, 95.0))
        median_f0_hz = float(np.median(voiced_p1))
        # Adaptive floor & ceiling: 0.75 * P5, 1.5 * P95
        adaptive_floor = max(50.0, p5 * 0.75)
        adaptive_ceiling = min(600.0, p95 * 1.5)
    else:
        median_f0_hz = 120.0
        adaptive_floor = init_floor
        adaptive_ceiling = init_ceil

    # Pass 2: Speaker-adaptive pitch extraction
    pitch_pass2 = sound.to_pitch_ac(
        time_step=hop_s,
        pitch_floor=adaptive_floor,
        pitch_ceiling=adaptive_ceiling,
        very_accurate=True
    )

    # Intensity extraction
    intensity_obj = sound.to_intensity(
        minimum_pitch=adaptive_floor,
        time_step=hop_s,
        subtract_mean=True
    )

    # Harmonicity (HNR) extraction
    try:
        harmonicity_obj = sound.to_harmonicity_ac(
            time_step=hop_s,
            minimum_pitch=adaptive_floor,
            silence_threshold=0.1,
            periods_per_window=4.5
        )
    except Exception:
        harmonicity_obj = None

    # Construct unified frame time series (10ms grid) via fast vectorized interpolation
    num_frames = int(total_dur / hop_s)
    times = [i * hop_s for i in range(num_frames)]
    times_np = np.asarray(times, dtype=np.float64)
    
    # Vectorized F0 interpolation
    p_xs = pitch_pass2.xs()
    p_freqs = pitch_pass2.selected_array["frequency"]
    if len(p_xs) > 0 and len(p_freqs) > 0:
        f0_interp = np.interp(times_np, p_xs, p_freqs, left=0.0, right=0.0)
        f0_hz_arr = [float(f) if f > 0 else None for f in f0_interp]
    else:
        f0_hz_arr = [None] * num_frames

    # Vectorized Intensity interpolation
    i_xs = intensity_obj.xs()
    i_vals = intensity_obj.values[0]
    if len(i_xs) > 0 and len(i_vals) > 0:
        int_interp = np.interp(times_np, i_xs, i_vals, left=30.0, right=30.0)
        intensity_db_arr = [float(val) for val in int_interp]
    else:
        intensity_db_arr = [30.0] * num_frames

    # Vectorized HNR interpolation (voiced frames only; exclude unvoiced / Praat -200 dB)
    if harmonicity_obj is not None:
        h_xs = harmonicity_obj.xs()
        h_vals = harmonicity_obj.values[0]
        if len(h_xs) > 0 and len(h_vals) > 0:
            hnr_interp = np.interp(times_np, h_xs, h_vals, left=-100.0, right=-100.0)
            hnr_db_arr = [
                float(h) if (f is not None and h > -50.0) else None
                for f, h in zip(f0_hz_arr, hnr_interp, strict=True)
            ]
        else:
            hnr_db_arr = [None] * num_frames
    else:
        hnr_db_arr = [None] * num_frames

    # Calculate voiced frame metrics
    voiced_frame_count = sum(1 for f in f0_hz_arr if f is not None)
    voiced_frame_fraction = voiced_frame_count / max(len(times), 1)
    
    valid_hnrs = [h for h in hnr_db_arr if h is not None]
    speaker_median_hnr_db = float(np.median(valid_hnrs)) if valid_hnrs else 15.0
    speaker_mean_hnr_db = float(np.mean(valid_hnrs)) if valid_hnrs else 15.0

    # Global voice quality metrics (Jitter & Shimmer)
    try:
        point_process = call(sound, "To PointProcess (periodic, cc)...", adaptive_floor, adaptive_ceiling)
        local_jitter = call(point_process, "Get jitter (local)...", 0, 0, 0.0001, 0.02, 1.3)
        local_shimmer = call([sound, point_process], "Get shimmer (local)...", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    except Exception:
        local_jitter = 0.015
        local_shimmer = 0.035

    return {
        "times": times,
        "f0_hz": f0_hz_arr,
        "intensity_db": intensity_db_arr,
        "hnr_db": hnr_db_arr,
        "speaker_median_f0_hz": median_f0_hz,
        "speaker_median_intensity_db": float(np.median(intensity_db_arr)),
        "speaker_median_hnr_db": speaker_median_hnr_db,
        "speaker_mean_hnr_db": speaker_mean_hnr_db,
        "voiced_frame_fraction": round(float(voiced_frame_fraction), 3),
        "jitter_local": float(local_jitter) if not np.isnan(local_jitter) else 0.015,
        "shimmer_local": float(local_shimmer) if not np.isnan(local_shimmer) else 0.035,
    }


def extract_spectral_features_librosa(
    audio_arr: np.ndarray, sr: int = 16000
) -> dict[str, Any]:
    """
    Extracts MFCCs (13 coeffs), spectral centroid, and spectral flux using Librosa.
    """
    cfg = load_features_config()
    hop_length = cfg.get("mfcc", {}).get("hop_length", 160)
    n_mfcc = cfg.get("mfcc", {}).get("n_mfcc", 13)

    # Mel-spectrogram
    melspec = librosa.feature.melspectrogram(y=audio_arr, sr=sr, n_mels=40, hop_length=hop_length)
    melspec_db = librosa.power_to_db(melspec, ref=np.max)

    # MFCC
    mfcc = librosa.feature.mfcc(y=audio_arr, sr=sr, n_mfcc=n_mfcc, hop_length=hop_length)
    mfcc_delta = librosa.feature.delta(mfcc)

    # Spectral centroid & flux (onset strength)
    centroid = librosa.feature.spectral_centroid(y=audio_arr, sr=sr, hop_length=hop_length)[0]
    spectral_flux = librosa.onset.onset_strength(y=audio_arr, sr=sr, hop_length=hop_length)

    times = librosa.frames_to_time(np.arange(mfcc.shape[1]), sr=sr, hop_length=hop_length)

    return {
        "melspec_db": melspec_db,
        "mfcc": mfcc,
        "mfcc_delta": mfcc_delta,
        "spectral_centroid": centroid,
        "spectral_flux": spectral_flux,
        "times": times.tolist(),
    }


def count_syllables(word_text: str) -> int:
    """
    Estimates syllable count using vowel nuclei heuristic with English orthographic rules.
    """
    clean = re.sub(r"[^a-z]", "", word_text.lower())
    if not clean:
        return 1
    if len(clean) <= 3:
        return 1
    
    vowels = "aeiouy"
    count = 0
    prev_is_vowel = False
    for char in clean:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
        
    # Orthographic adjustments
    if clean.endswith("e") and not clean.endswith("le") and count > 1:
        if not clean.endswith("ee"):
            count -= 1
    elif clean.endswith("ed") and count > 1:
        if not (clean.endswith("ted") or clean.endswith("ded")):
            count -= 1
    elif clean.endswith("es") and count > 1:
        if clean.endswith("ies"):
            pass  # 'ies' retains the syllabic nucleus from '-y' (e.g. energies, categories)
        elif not (clean.endswith("ses") or clean.endswith("zes") or clean.endswith("ches") or clean.endswith("shes") or clean.endswith("ges")):
            count -= 1
        
    return max(1, count)


def compute_speech_rate_excluding_pauses(
    words: list[dict[str, Any]],
    pause_threshold_s: float = 0.250,
) -> dict[str, Any]:
    """
    Calculates overall articulation / speech rate as:
    total_syllables / active_speech_time
    where active_speech_time excludes all rhetorical pauses >= 250ms.
    """
    if not words:
        return {"total_syllables": 0, "active_speech_time_s": 0.0, "speech_rate_syl_per_s": 0.0}
    
    total_syllables = sum(count_syllables(w["text"]) for w in words)
    active_speech_time = sum(w["end"] - w["start"] for w in words)
    for i in range(len(words) - 1):
        gap = words[i + 1]["start"] - words[i]["end"]
        if 0 < gap < pause_threshold_s:
            active_speech_time += gap
            
    rate = total_syllables / max(active_speech_time, 0.1)
    return {
        "total_syllables": total_syllables,
        "active_speech_time_s": round(active_speech_time, 3),
        "speech_rate_syl_per_s": round(rate, 2),
    }


def aggregate_word_level_features(
    words: list[dict[str, Any]],
    praat_feats: dict[str, Any],
    median_f0_hz: float,
    median_intensity_db: float,
) -> list[dict[str, Any]]:
    """
    Aggregates frame features across exact aligned word boundaries:
    - F0 in semitones re speaker median: 12 * log2(F0 / median_f0)
    - F0 range P90 - P10 (semitones) requiring min 4 voiced frames, else None/NaN
    - Mean & peak intensity (dB re speaker median)
    - Articulation rate (syllables / sec) computed over a sliding window (>= 5 words / ~1s)
    - Pause before & after (sec)
    - HNR (mean of voiced frames only)
    """
    times = np.array(praat_feats["times"])
    f0_arr = np.array([f if f is not None else np.nan for f in praat_feats["f0_hz"]])
    int_arr = np.array(praat_feats["intensity_db"])
    hnr_arr = np.array([h if h is not None else np.nan for h in praat_feats["hnr_db"]])

    # Convert F0 to semitones re median
    f0_st_arr = np.where(
        np.isnan(f0_arr) | (f0_arr <= 0),
        np.nan,
        12.0 * np.log2(np.maximum(f0_arr, 1.0) / median_f0_hz),
    )

    num_words = len(words)
    syllable_counts = [count_syllables(w["text"]) for w in words]
    word_durs = [max(w["end"] - w["start"], 0.03) for w in words]

    # Precompute sliding window articulation rate (window of +/- 2 words, total 5 words)
    sliding_rates = []
    for i in range(num_words):
        w_start_idx = max(0, i - 2)
        w_end_idx = min(num_words, i + 3)
        total_syl = sum(syllable_counts[w_start_idx:w_end_idx])
        total_active_dur = sum(word_durs[w_start_idx:w_end_idx])
        rate_window = total_syl / max(total_active_dur, 0.2)
        sliding_rates.append(rate_window)

    # Precompute sliding phrase-window F0 metrics (at least 1.5s window or +/- 3 words)
    sliding_f0_ranges = []
    sliding_f0_stds = []
    for i in range(num_words):
        l_idx = i
        r_idx = i
        while (l_idx > 0 or r_idx < num_words - 1) and (words[r_idx]["end"] - words[l_idx]["start"] < 1.5):
            if l_idx > 0:
                l_idx -= 1
            if r_idx < num_words - 1:
                r_idx += 1
        
        win_start_t = words[l_idx]["start"]
        win_end_t = words[r_idx]["end"]
        win_mask = (times >= win_start_t) & (times <= win_end_t)
        win_f0 = f0_st_arr[win_mask]
        win_voiced = win_f0[~np.isnan(win_f0)]
        
        if len(win_voiced) >= 6:
            p90 = float(np.percentile(win_voiced, 90))
            p10 = float(np.percentile(win_voiced, 10))
            win_range = p90 - p10
            win_std = float(np.std(win_voiced))
        else:
            win_range = None
            win_std = None
            
        sliding_f0_ranges.append(win_range)
        sliding_f0_stds.append(win_std)

    aggregated_words = []

    for i, w in enumerate(words):
        start_t = w["start"]
        end_t = w["end"]
        dur = word_durs[i]

        # Slice frame indices
        mask = (times >= start_t) & (times <= end_t)
        
        # Word F0 stats
        w_f0_st = f0_st_arr[mask]
        voiced = w_f0_st[~np.isnan(w_f0_st)]

        if len(voiced) >= 4:
            f0_mean_st = float(np.mean(voiced))
            t_voiced = times[mask][~np.isnan(w_f0_st)]
            slope = float(np.polyfit(t_voiced - start_t, voiced, 1)[0])
        else:
            f0_mean_st = None
            slope = 0.0

        # Assign phrase-window F0 range & std
        f0_range_st = sliding_f0_ranges[i]
        f0_std_st = sliding_f0_stds[i]

        # Word Intensity stats
        w_int = int_arr[mask]
        if len(w_int) > 0:
            int_mean = float(np.mean(w_int))
            int_peak = float(np.max(w_int))
            int_mean_re_median = float(int_mean - median_intensity_db)
        else:
            int_mean_re_median = 0.0
            int_peak = median_intensity_db

        # Word HNR (voiced frames only)
        w_hnr = hnr_arr[mask]
        w_hnr_valid = w_hnr[~np.isnan(w_hnr)]
        if len(w_hnr_valid) > 0:
            hnr_mean = float(np.mean(w_hnr_valid))
        else:
            hnr_mean = praat_feats.get("speaker_median_hnr_db", 15.0)

        # Articulation rate from sliding window
        rate = sliding_rates[i]

        # Pauses
        pause_before = round(start_t - words[i - 1]["end"], 3) if i > 0 else 0.0
        pause_after = round(words[i + 1]["start"] - end_t, 3) if i < num_words - 1 else 0.0

        aggregated_words.append({
            "index": i,
            "text": w["text"],
            "start": round(start_t, 3),
            "end": round(end_t, 3),
            "duration": round(dur, 3),
            "punctuation": w.get("punctuation", ""),
            "has_punctuation": w.get("has_punctuation", False),
            "syllable_count": syllable_counts[i],
            "f0_mean_st": round(f0_mean_st, 2) if f0_mean_st is not None else None,
            "f0_range_st": round(f0_range_st, 2) if f0_range_st is not None else None,
            "f0_std_st": round(f0_std_st, 2) if f0_std_st is not None else None,
            "f0_slope_st_per_s": round(slope, 2),
            "energy_mean_db": round(int_mean_re_median, 2),
            "energy_peak_db": round(int_peak - median_intensity_db, 2),
            "hnr_mean_db": round(hnr_mean, 2),
            "articulation_rate": round(rate, 2),
            "pause_before_s": max(0.0, pause_before),
            "pause_after_s": max(0.0, pause_after),
        })

    return aggregated_words

