"""
Acoustic feature extraction module.
Integrates Parselmouth (Praat), Librosa, and Scipy for mathematically rigorous frame and word-level features.
"""

import os
import yaml
import numpy as np
import parselmouth
from parselmouth.praat import call
import librosa
from scipy.signal import find_peaks
from typing import Dict, Any, List, Optional, Tuple

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "thresholds.yaml")


def load_features_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
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
) -> Dict[str, Any]:
    """
    Extracts frame-level F0, intensity, and HNR using Parselmouth (Praat C engine).
    Implements a two-pass speaker-adaptive pitch floor/ceiling calculation.
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

    # Construct unified frame time series (10ms grid)
    num_frames = int(total_dur / hop_s)
    times = [i * hop_s for i in range(num_frames)]
    
    f0_hz_arr = []
    intensity_db_arr = []
    hnr_db_arr = []

    for t in times:
        # F0
        f0_val = pitch_pass2.get_value_at_time(t)
        if f0_val is None or np.isnan(f0_val) or f0_val <= 0:
            f0_hz_arr.append(None)
        else:
            f0_hz_arr.append(float(f0_val))

        # Intensity
        int_val = intensity_obj.get_value(t)
        if int_val is None or np.isnan(int_val):
            intensity_db_arr.append(30.0)
        else:
            intensity_db_arr.append(float(int_val))

        # HNR
        if harmonicity_obj:
            hnr_val = harmonicity_obj.get_value(t)
            if hnr_val is None or np.isnan(hnr_val):
                hnr_db_arr.append(15.0)
            else:
                hnr_db_arr.append(float(hnr_val))
        else:
            hnr_db_arr.append(15.0)

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
        "jitter_local": float(local_jitter) if not np.isnan(local_jitter) else 0.015,
        "shimmer_local": float(local_shimmer) if not np.isnan(local_shimmer) else 0.035,
    }


def extract_spectral_features_librosa(
    audio_arr: np.ndarray, sr: int = 16000
) -> Dict[str, Any]:
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
    """Estimates syllable count using vowel nuclei heuristic."""
    clean = word_text.lower().strip(".,!?:;\"'()[]")
    if not clean:
        return 1
    # Vowel group regex
    import re
    vowel_runs = re.findall(r"[aeiouy]+", clean)
    count = len(vowel_runs)
    # Silent 'e' at end
    if clean.endswith("e") and not clean.endswith("le") and count > 1:
        count -= 1
    return max(1, count)


def aggregate_word_level_features(
    words: List[Dict[str, Any]],
    praat_feats: Dict[str, Any],
    median_f0_hz: float,
    median_intensity_db: float,
) -> List[Dict[str, Any]]:
    """
    Aggregates frame features across exact aligned word boundaries:
    - F0 in semitones re speaker median: 12 * log2(F0 / median_f0)
    - F0 range P90 - P10 (semitones)
    - Mean F0 slope (semitones/sec)
    - Mean & peak intensity (dB re speaker median)
    - Articulation rate (syllables / sec)
    - Pause before & after (sec)
    """
    times = np.array(praat_feats["times"])
    f0_arr = np.array([f if f is not None else np.nan for f in praat_feats["f0_hz"]])
    int_arr = np.array(praat_feats["intensity_db"])
    hnr_arr = np.array(praat_feats["hnr_db"])

    # Convert F0 to semitones re median
    f0_st_arr = np.where(
        np.isnan(f0_arr) | (f0_arr <= 0),
        np.nan,
        12.0 * np.log2(np.maximum(f0_arr, 1.0) / median_f0_hz),
    )

    aggregated_words = []
    num_words = len(words)

    for i, w in enumerate(words):
        start_t = w["start"]
        end_t = w["end"]
        dur = max(end_t - start_t, 0.05)

        # Slice frame indices
        mask = (times >= start_t) & (times <= end_t)
        
        # Word F0 stats
        w_f0_st = f0_st_arr[mask]
        voiced = w_f0_st[~np.isnan(w_f0_st)]

        if len(voiced) >= 2:
            f0_mean_st = float(np.mean(voiced))
            f0_range_st = float(np.percentile(voiced, 90) - np.percentile(voiced, 10))
            # Linear slope
            t_voiced = times[mask][~np.isnan(w_f0_st)]
            slope = float(np.polyfit(t_voiced - start_t, voiced, 1)[0]) if len(voiced) >= 3 else 0.0
        elif len(voiced) == 1:
            f0_mean_st = float(voiced[0])
            f0_range_st = 0.5
            slope = 0.0
        else:
            f0_mean_st = 0.0
            f0_range_st = 0.0
            slope = 0.0

        # Word Intensity stats
        w_int = int_arr[mask]
        if len(w_int) > 0:
            int_mean = float(np.mean(w_int))
            int_peak = float(np.max(w_int))
            int_mean_re_median = float(int_mean - median_intensity_db)
        else:
            int_mean = median_intensity_db
            int_peak = median_intensity_db
            int_mean_re_median = 0.0

        # Word HNR
        w_hnr = hnr_arr[mask]
        hnr_mean = float(np.mean(w_hnr)) if len(w_hnr) > 0 else 15.0

        # Articulation rate
        syllables = count_syllables(w["text"])
        rate = syllables / dur

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
            "syllable_count": syllables,
            "f0_mean_st": round(f0_mean_st, 2),
            "f0_range_st": round(f0_range_st, 2),
            "f0_slope_st_per_s": round(slope, 2),
            "energy_mean_db": round(int_mean_re_median, 2),
            "energy_peak_db": round(int_peak - median_intensity_db, 2),
            "hnr_mean_db": round(hnr_mean, 2),
            "articulation_rate": round(rate, 2),
            "pause_before_s": max(0.0, pause_before),
            "pause_after_s": max(0.0, pause_after),
        })

    return aggregated_words
