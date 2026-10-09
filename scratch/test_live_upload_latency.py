"""
Benchmark Live Upload Latency Stage-by-Stage on a 60s Audio Clip.
Verifies MMS_FA optimization with torch.inference_mode and CPU threads = os.cpu_count().
"""

import os
import sys
import time
import soundfile as sf
import torch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.pipeline.align import warmup_mms_fa, get_mms_fa_model, align_audio_with_transcript
from backend.pipeline.audio import load_and_preprocess_audio
from backend.pipeline.vad import detect_speech_and_pauses
from backend.pipeline.features import extract_frame_features_praat, extract_spectral_features_librosa, aggregate_word_level_features
from backend.pipeline.normalize import normalize_words_against_baseline
from backend.pipeline.grounding import ground_flaw_regions
from backend.pipeline.explain import generate_causal_explanations, load_flaw_rules
from backend.pipeline.scoring import calculate_overall_scores

# Ensure model is warmed up as it would be at startup
print(f"CPU core count: {os.cpu_count()}")
print(f"Torch threads set: {torch.get_num_threads()}")
t_warm_0 = time.perf_counter()
warmup_mms_fa()
t_warm_1 = time.perf_counter()
print(f"Startup warmup completed in {t_warm_1 - t_warm_0:.2f}s")

# Load 60s speech clip (e.g. jfk_we_choose_excerpt_real.wav or jfk_moon 60s slice)
audio_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "jfk_we_choose_excerpt_real.wav")
if not os.path.exists(audio_path):
    audio_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "reagan_challenger_excerpt_real.wav")

transcript = "things, not because they are easy, but because they are hard, because that goal will serve to organize and measure the best of our energies and skills, because that challenge is one that we're willing to accept, one we are unwilling to postpone, and one we intend to win, and the others too. It is, for these reasons, that I regard the decision last year to shift our efforts in space from low to high gear as among the most important decisions that will be made during my incumbency in the Office of the Presidency."

print(f"\nProcessing audio file: {os.path.basename(audio_path)}")
total_t0 = time.perf_counter()

# Stage 1: Load and Preprocess
s1_t0 = time.perf_counter()
audio_arr, sr, sha256, audio_meta = load_and_preprocess_audio(audio_path)
s1_t1 = time.perf_counter()
dur_s = audio_meta["duration_s"]
print(f"Stage 1 (Ingestion & LUFS)     : {s1_t1 - s1_t0:.3f} s (Duration: {dur_s:.1f} s)")

# Stage 2: VAD
s2_t0 = time.perf_counter()
speech_segs, _, pause_mask = detect_speech_and_pauses(audio_arr, sr=sr)
s2_t1 = time.perf_counter()
print(f"Stage 2 (VAD Segmentation)      : {s2_t1 - s2_t0:.3f} s")

# Stage 3: Forced Alignment (MMS_FA)
s3_t0 = time.perf_counter()
alignment = align_audio_with_transcript(audio_arr, transcript, sr=sr, audio_duration_s=dur_s, speech_segments=speech_segs)
s3_t1 = time.perf_counter()
print(f"Stage 3 (MMS_FA Alignment)      : {s3_t1 - s3_t0:.3f} s")

# Stage 4: Feature Extraction (Praat + Librosa)
s4_t0 = time.perf_counter()
praat_feats = extract_frame_features_praat(audio_arr, sr=sr)
_ = extract_spectral_features_librosa(audio_arr, sr=sr)
med_f0 = praat_feats["speaker_median_f0_hz"]
med_int = praat_feats["speaker_median_intensity_db"]
word_feats = aggregate_word_level_features(alignment.words, praat_feats, med_f0, med_int)
s4_t1 = time.perf_counter()
print(f"Stage 4 (Acoustic Features)     : {s4_t1 - s4_t0:.3f} s")

# Stage 5: Grounding & Scoring
s5_t0 = time.perf_counter()
normalized_words, ref_type = normalize_words_against_baseline(word_feats, None)
flaw_rules = load_flaw_rules()
raw_grounded = ground_flaw_regions(normalized_words, flaw_rules, reference_type=ref_type)
flaws = generate_causal_explanations(raw_grounded)
scores = calculate_overall_scores(normalized_words, flaws, reference_type=ref_type)
s5_t1 = time.perf_counter()
print(f"Stage 5 (Grounding & Scoring)   : {s5_t1 - s5_t0:.3f} s")

total_t1 = time.perf_counter()
total_latency = total_t1 - total_t0
print("--------------------------------------------------------------------------------")
print(f"Total Pipeline Latency for {dur_s:.1f}s Audio : {total_latency:.2f} s")
print(f"Target Under 60s               : {'PASS' if total_latency < 60.0 else 'FAIL'}")
print("--------------------------------------------------------------------------------")
