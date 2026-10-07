"""
Unit tests for audio loading, 16 kHz resampling, and LUFS normalization.
"""

import os
import numpy as np
import soundfile as sf
import tempfile
from backend.pipeline.audio import load_and_preprocess_audio, save_canonical_wav


def test_audio_preprocessing_pipeline():
    # Create 2 seconds of 44.1kHz sine wave test audio
    sr_orig = 44100
    t = np.linspace(0, 2.0, sr_orig * 2, endpoint=False)
    sine = 0.5 * np.sin(2 * np.pi * 440 * t)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, sine, sr_orig)
        tmp_path = f.name

    try:
        audio_arr, sr, sha256_hash, meta = load_and_preprocess_audio(tmp_path)
        
        assert sr == 16000, f"Expected canonical sample rate 16000, got {sr}"
        assert len(audio_arr) == 32000, f"Expected 32000 samples for 2 seconds, got {len(audio_arr)}"
        assert meta["duration_s"] == 2.0
        assert len(sha256_hash) == 64
        assert np.max(np.abs(audio_arr)) <= 1.0, "Normalized audio should not clip"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
