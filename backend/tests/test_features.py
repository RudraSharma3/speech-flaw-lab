"""
Unit tests for acoustic feature extraction, normalization, and scoring.
"""

import numpy as np
from backend.pipeline.features import extract_frame_features_praat, extract_spectral_features_librosa, count_syllables
from backend.pipeline.normalize import compute_robust_z
from backend.pipeline.scoring import evaluate_piecewise_linear, evaluate_sigmoid_symmetric


def test_syllable_counter():
    assert count_syllables("moon") == 1
    assert count_syllables("decade") == 2
    assert count_syllables("organize") == 3
    assert count_syllables("energies") == 3


def test_robust_z_calculation():
    # z = (x - median) / (1.4826 * MAD)
    # If x = median, z = 0.0
    assert compute_robust_z(5.0, 5.0, 1.0) == 0.0
    # If x = median + 1.4826, z = 1.0
    z = compute_robust_z(6.4826, 5.0, 1.0)
    assert abs(z - 1.0) < 1e-4


def test_scoring_curves():
    # Test piecewise linear
    points = [[-4.0, 10.0], [-2.0, 45.0], [0.0, 100.0]]
    assert evaluate_piecewise_linear(0.0, points) == 100.0
    assert evaluate_piecewise_linear(-4.0, points) == 10.0
    assert evaluate_piecewise_linear(-3.0, points) == 27.5

    # Test sigmoid symmetric
    score_ideal = evaluate_sigmoid_symmetric(0.0)
    assert score_ideal > 80.0
    score_flawed = evaluate_sigmoid_symmetric(3.5)
    assert score_flawed < 30.0


def test_praat_feature_extraction():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    # 150 Hz harmonic tone
    audio = 0.6 * np.sin(2 * np.pi * 150.0 * t)
    
    feats = extract_frame_features_praat(audio, sr=sr)
    assert "times" in feats
    assert "f0_hz" in feats
    assert "speaker_median_f0_hz" in feats
    assert abs(feats["speaker_median_f0_hz"] - 150.0) < 15.0
