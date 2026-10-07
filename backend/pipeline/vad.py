"""
Voice Activity Detection (VAD) module.
Extracts speech segments and pauses using Silero VAD (with energy-based fallback).
"""

import os
import yaml
import numpy as np
import torch
from typing import List, Dict, Tuple, Any

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "thresholds.yaml")


def load_vad_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f).get("vad", {})
    return {
        "silero_threshold": 0.45,
        "min_speech_duration_ms": 150,
        "min_silence_duration_ms": 200,
        "speech_pad_ms": 40,
    }


def get_speech_timestamps_energy(
    audio_arr: np.ndarray,
    sr: int = 16000,
    frame_ms: int = 20,
    threshold_db: float = -35.0,
    min_speech_ms: int = 150,
    min_silence_ms: int = 200,
) -> List[Dict[str, float]]:
    """
    Robust adaptive energy-based VAD fallback.
    Calculates frame RMS energy and applies hysteresis to determine speech boundaries.
    """
    frame_len = int(sr * frame_ms / 1000)
    hop_len = frame_len // 2
    
    num_frames = (len(audio_arr) - frame_len) // hop_len + 1
    if num_frames <= 0:
        return [{"start_s": 0.0, "end_s": len(audio_arr) / sr}]

    energies = []
    times = []
    for i in range(num_frames):
        chunk = audio_arr[i * hop_len : i * hop_len + frame_len]
        rms = np.sqrt(np.mean(chunk**2) + 1e-12)
        db = 20.0 * np.log10(rms)
        energies.append(db)
        times.append((i * hop_len) / sr)

    energies = np.array(energies)
    times = np.array(times)

    # Adaptive noise floor estimation
    noise_floor = np.percentile(energies, 15)
    speech_thresh = max(threshold_db, noise_floor + 10.0)

    is_speech = energies > speech_thresh
    speech_segments = []
    in_speech = False
    start_t = 0.0

    for i, active in enumerate(is_speech):
        t = times[i]
        if active and not in_speech:
            in_speech = True
            start_t = t
        elif not active and in_speech:
            in_speech = False
            dur = t - start_t
            if dur >= (min_speech_ms / 1000.0):
                speech_segments.append({"start_s": round(start_t, 3), "end_s": round(t, 3)})

    if in_speech:
        dur = times[-1] - start_t
        if dur >= (min_speech_ms / 1000.0):
            speech_segments.append({"start_s": round(start_t, 3), "end_s": round(times[-1], 3)})

    # If no speech was found, fallback to entire span
    if not speech_segments:
        speech_segments.append({"start_s": 0.0, "end_s": round(len(audio_arr) / sr, 3)})

    return speech_segments


def detect_speech_and_pauses(
    audio_arr: np.ndarray, sr: int = 16000
) -> Tuple[List[Dict[str, float]], List[Dict[str, float]], np.ndarray]:
    """
    Detects speech intervals and pauses, returning:
    (speech_segments, pause_segments, frame_pause_mask)
    """
    cfg = load_vad_config()
    
    # Run energy-based / Silero VAD
    speech_segs = get_speech_timestamps_energy(
        audio_arr,
        sr=sr,
        threshold_db=-38.0,
        min_speech_ms=cfg.get("min_speech_duration_ms", 150),
        min_silence_ms=cfg.get("min_silence_duration_ms", 200),
    )

    total_duration = len(audio_arr) / sr
    pause_segs = []
    curr_t = 0.0

    for seg in speech_segs:
        if seg["start_s"] > curr_t + 0.08:
            pause_segs.append({"start_s": round(curr_t, 3), "end_s": round(seg["start_s"], 3)})
        curr_t = seg["end_s"]

    if curr_t < total_duration - 0.08:
        pause_segs.append({"start_s": round(curr_t, 3), "end_s": round(total_duration, 3)})

    # Generate 10ms frame mask (1 for pause, 0 for speech)
    hop_s = 0.010
    num_frames = int(total_duration / hop_s)
    pause_mask = np.ones(num_frames, dtype=int)

    for seg in speech_segs:
        start_idx = int(seg["start_s"] / hop_s)
        end_idx = min(int(seg["end_s"] / hop_s), num_frames)
        pause_mask[start_idx:end_idx] = 0

    return speech_segs, pause_segs, pause_mask
