"""
Audio ingestion, normalization, and quality validation module.
Enforces canonical 16 kHz mono WAV 16-bit format, LUFS normalization, and clipping checks.
"""

import os
import io
import hashlib
import numpy as np
import soundfile as sf
import librosa
import pyloudnorm as pyln
import yaml
from typing import Tuple, Dict, Any, Optional

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "thresholds.yaml")


def load_audio_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f).get("audio", {})
    return {
        "canonical_sample_rate": 16000,
        "channels": 1,
        "target_lufs": -20.0,
        "clipping_threshold_dbfs": -0.5,
        "min_audio_duration_s": 3.0,
        "max_audio_duration_s": 300.0,
    }


def compute_sha256(audio_bytes: bytes) -> str:
    return hashlib.sha256(audio_bytes).hexdigest()


def load_and_preprocess_audio(
    audio_source: Any, target_sr: int = 16000, target_lufs: float = -20.0
) -> Tuple[np.ndarray, int, str, Dict[str, Any]]:
    """
    Loads any input audio (bytes, file-like, or path), converts to mono,
    resamples to 16kHz, performs BS.1770 LUFS loudness normalization,
    and returns (audio_array, sample_rate, sha256_hash, metadata_dict).
    """
    cfg = load_audio_config()
    target_sr = cfg.get("canonical_sample_rate", target_sr)
    target_lufs = cfg.get("target_lufs", target_lufs)

    if isinstance(audio_source, bytes):
        raw_bytes = audio_source
        bio = io.BytesIO(raw_bytes)
        y, sr = sf.read(bio)
    elif isinstance(audio_source, str) and os.path.exists(audio_source):
        with open(audio_source, "rb") as f:
            raw_bytes = f.read()
        y, sr = sf.read(audio_source)
    else:
        # File-like object
        raw_bytes = audio_source.read()
        bio = io.BytesIO(raw_bytes)
        y, sr = sf.read(bio)

    sha256_hash = compute_sha256(raw_bytes)

    # Convert to mono if multi-channel
    if y.ndim > 1:
        y = np.mean(y, axis=1)

    # Resample to 16kHz if necessary
    if sr != target_sr:
        y = librosa.resample(y.astype(np.float32), orig_sr=sr, target_sr=target_sr)
        sr = target_sr

    duration_s = float(len(y)) / sr

    # Quality metrics: clipping detection
    clipping_thresh = 10.0 ** (cfg.get("clipping_threshold_dbfs", -0.5) / 20.0)
    clipping_count = np.sum(np.abs(y) >= clipping_thresh)
    clipping_fraction = float(clipping_count) / max(len(y), 1)

    # LUFS Loudness normalization
    meter = pyln.Meter(sr)
    try:
        current_lufs = meter.integrated_loudness(y)
        if not np.isinf(current_lufs) and not np.isnan(current_lufs):
            y_norm = pyln.normalize.loudness(y, current_lufs, target_lufs)
            # Peak preventer to avoid hard digital clipping
            peak = np.max(np.abs(y_norm))
            if peak > 0.99:
                y_norm = y_norm / peak * 0.99
            y = y_norm
        else:
            current_lufs = -30.0
    except Exception:
        # Fallback to peak/RMS scaling if loudness meter fails on very short audio
        current_lufs = -20.0
        peak = np.max(np.abs(y))
        if peak > 0:
            y = y / peak * 0.85

    meta = {
        "duration_s": round(duration_s, 3),
        "sample_rate": sr,
        "initial_lufs": round(float(current_lufs), 2),
        "clipping_fraction": round(clipping_fraction, 4),
        "num_samples": len(y),
    }

    return y.astype(np.float32), sr, sha256_hash, meta


def save_canonical_wav(audio_arr: np.ndarray, sr: int, output_path: str) -> str:
    """Saves normalized 16-bit 16kHz mono WAV to output_path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Scale float32 in [-1, 1] to int16
    int16_arr = np.clip(audio_arr * 32767.0, -32768, 32767).astype(np.int16)
    sf.write(output_path, int16_arr, sr, subtype="PCM_16")
    return output_path
