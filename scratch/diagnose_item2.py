import json
import os
import sys
import numpy as np
import soundfile as sf
import parselmouth
from parselmouth.praat import call as praat_call
import librosa

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, ".")
from backend.pipeline.orchestrator import run_speech_pipeline
from backend.pipeline.align import align_audio_with_transcript

REAL_MANIFEST_PATH = "data/manifests/real_speech_manifest.json"
INJECTED_DIR = "data/injected"
PROCESSED_DIR = "data/processed"

with open(REAL_MANIFEST_PATH, "r", encoding="utf-8") as f:
    real_manifest = json.load(f)

print("=" * 80)
print("ITEM 2 DIAGNOSTIC: FULL INJECTOR CHAIN AT IDENTITY")
print("=" * 80)

# 1. Build and run FULL-CHAIN identity audio for each speech:
# - Praat pitch tier resynthesis (rate=1.0, shift=0.0)
# - Time stretch at rate=1.0
# - Volume gain at 0.0 dB
# - Audio write and reload via soundfile

full_chain_null_flaws = {}

for sp in real_manifest:
    s_id = sp["speech_id"]
    transcript = sp["transcript"]
    raw_path = os.path.join(PROCESSED_DIR, sp["processed_file"])
    audio_orig, sr = sf.read(raw_path)
    if audio_orig.ndim > 1:
        audio_orig = audio_orig.mean(axis=1)
    audio_orig = audio_orig.astype(np.float32)

    # 1. Praat identity resynthesis
    snd = parselmouth.Sound(audio_orig, sampling_frequency=sr)
    manip = praat_call(snd, "To Manipulation...", 0.01, 75.0, 500.0)
    pitch_tier = praat_call(manip, "Extract pitch tier")
    praat_call(pitch_tier, "Multiply frequencies...", snd.xmin, snd.xmax, 1.0)
    praat_call(pitch_tier, "Shift frequencies...", snd.xmin, snd.xmax, 0.0, "Hertz")
    praat_call([pitch_tier, manip], "Replace pitch tier")
    res_sound = praat_call(manip, "Get resynthesis (overlap-add)")
    praat_audio = res_sound.values[0].astype(np.float32)
    if len(praat_audio) < len(audio_orig):
        praat_audio = np.pad(praat_audio, (0, len(audio_orig) - len(praat_audio)))
    else:
        praat_audio = praat_audio[:len(audio_orig)]

    # 2. Rubberband / librosa time stretch at 1.0
    stretched = librosa.effects.time_stretch(y=praat_audio, rate=1.0)
    if len(stretched) < len(audio_orig):
        stretched = np.pad(stretched, (0, len(audio_orig) - len(stretched)))
    else:
        stretched = stretched[:len(audio_orig)]

    # 3. Gain at 0 dB
    gain_scale = 10.0 ** (0.0 / 20.0)
    final_null_audio = (stretched * gain_scale).astype(np.float32)

    # 4. Write & reload
    null_path = f"scratch/full_chain_null_{s_id}.wav"
    os.makedirs("scratch", exist_ok=True)
    sf.write(null_path, final_null_audio, sr)

    # Baseline run
    base_res = run_speech_pipeline(raw_path, transcript, filename=sp["processed_file"])
    null_res = run_speech_pipeline(
        null_path, transcript, filename=f"null_{s_id}.wav",
        reference_words=base_res["words"],
        reference_id=f"{s_id}_ideal"
    )

    flaws = null_res["flaws"]
    full_chain_null_flaws[s_id] = flaws
    print(f"[{s_id}] Full-chain null control: {len(flaws)} flags | score={null_res['scores']['overall']:.1f}")
    for f in flaws:
        print(f"    -> {f['flaw_type']} [{f['start_s']:.2f}-{f['end_s']:.2f}s] z={f.get('z_score', 0):.2f}")

print("\n" + "=" * 80)
print("AUDITING THE 33 FAR-FROM-GT DETECTIONS")
print("=" * 80)

# We load the 33 detections from the benchmark
# The 33 detections breakdown:
# - 23 breathy_unclear (Reagan Challenger s1: 11, Reagan Challenger s2: 10, Reagan Challenger s2 L0: 1, Reagan Mourning L0: 1)
# - 5 missing_pause (JFK We Choose: 5 at 0.80s)
# - 4 drag_slow (JFK Moon: L0, L2 s1, L2 s2, L0 s2)
# - 1 drag_slow (FDR L0 s2 at 37.22-39.45s)

# Test scoring against ANOTHER seed's level 4:
# For each speech, level_4 exists with seed 0, seed 1, seed 2.
# We will test scoring against seed 1 or seed 2 level 4!

for s_id in ["reagan_challenger_1986", "jfk_we_choose_1962", "jfk_moon_1962"]:
    sp = next(s for s in real_manifest if s["speech_id"] == s_id)
    transcript = sp["transcript"]
    # Run reference for seed 0 and seed 1
    l4_s0_path = os.path.join(INJECTED_DIR, f"{s_id}_level_4.wav")
    l4_s1_path = os.path.join(INJECTED_DIR, f"{s_id}_level_4_s1.wav")
    
    res_l4_s0 = run_speech_pipeline(l4_s0_path, transcript, filename=f"{s_id}_l4_s0.wav")
    res_l4_s1 = run_speech_pipeline(l4_s1_path, transcript, filename=f"{s_id}_l4_s1.wav")
    
    # Check if cross-scoring L4 seed 1 against L4 seed 0 produces flags
    cross_res = run_speech_pipeline(
        l4_s1_path, transcript, filename=f"{s_id}_cross.wav",
        reference_words=res_l4_s0["words"],
        reference_id=f"{s_id}_l4_s0"
    )
    print(f"[{s_id}] L4_s1 scored against L4_s0: {len(cross_res['flaws'])} flags")
    for f in cross_res["flaws"]:
        print(f"    -> {f['flaw_type']} [{f['start_s']:.2f}-{f['end_s']:.2f}s] z={f.get('z_score', 0):.2f}")
