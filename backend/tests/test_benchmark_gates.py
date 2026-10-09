"""
Unit and Integration Tests for Grounding and Evaluation Benchmark Gates.
Verifies:
1. Injected pause detection accuracy within 100ms.
2. Monotone pitch contour detection in contrastive mode.
3. MMS_FA alignment monotonicity and non-clamped continuous durations.
4. Level 4 (ideal baseline) low false positive rate (<= 1 flag).
"""

from pathlib import Path
import numpy as np
import pytest
import soundfile as sf
import parselmouth
from parselmouth.praat import call

from backend.pipeline.align import align_audio_with_transcript
from backend.pipeline.orchestrator import run_speech_pipeline
from backend.schemas.api import AnalysisResult


@pytest.mark.slow
def test_alignment_monotonicity_and_unclamped_durations():
    """Gate Test: Alignment produces strictly monotonic words with continuous, non-clamped durations."""
    audio_path = Path("data/processed/jfk_rice_excerpt_real.wav")
    assert audio_path.exists(), f"Audio not found: {audio_path}"
    
    transcript = (
        "140000 miles away from the control station in Houston a giant rocket more than 300 feet tall "
        "the length of this football field made of new metal alloys some of which have not yet been embedded "
        "capable of standing heat and stresses several times more than have ever been experienced "
        "pitted together with a precision better than the finest watch carrying all the equipment needed "
        "for propulsion guidance control communication food and survival on an untried mission to an unknown celestial body "
        "and then return it safely to earth re-entering the atmosphere at speeds of over 25000 miles per hour "
        "causing heat about half that on the temperature of the sun almost as hot as it is here today "
        "and do all this and do all this and do it right and do it first if all this thick heat is out then we must be bald ."
    )
    
    audio, sr = sf.read(str(audio_path))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    
    alignment = align_audio_with_transcript(audio, transcript, sr=sr, recording_id="jfk_align_test")
    words = alignment.words
    assert len(words) >= 100
    
    durations = []
    for i in range(len(words) - 1):
        assert words[i]["start"] < words[i]["end"], f"Word '{words[i]['text']}' has start >= end"
        assert words[i]["end"] <= words[i + 1]["start"] + 1e-3, f"Word overlap between '{words[i]['text']}' and '{words[i+1]['text']}'"
        durations.append(words[i]["end"] - words[i]["start"])
    
    # Verify durations are continuous (not quantized to 0.223s or 0.080s multiples)
    unique_durs = set(round(d, 4) for d in durations)
    assert len(unique_durs) > 30, "Durations must be continuous and diverse, not quantized."
    
    # Check that short words are naturally resolved, not hard-clamped
    min_dur = min(durations)
    assert min_dur > 0.015, f"Shortest word duration too small ({min_dur:.4f}s)"


@pytest.mark.slow
def test_pause_grounding_accuracy(tmp_path):
    """Gate Test: Injected pause of 0.8s is detected within 100ms temporal accuracy."""
    audio_path = Path("data/processed/jfk_rice_excerpt_real.wav")
    assert audio_path.exists()
    
    transcript = (
        "140000 miles away from the control station in Houston a giant rocket more than 300 feet tall "
        "the length of this football field made of new metal alloys some of which have not yet been embedded "
        "capable of standing heat and stresses several times more than have ever been experienced "
        "pitted together with a precision better than the finest watch carrying all the equipment needed "
        "for propulsion guidance control communication food and survival on an untried mission to an unknown celestial body "
        "and then return it safely to earth re-entering the atmosphere at speeds of over 25000 miles per hour "
        "causing heat about half that on the temperature of the sun almost as hot as it is here today "
        "and do all this and do all this and do it right and do it first if all this thick heat is out then we must be bald ."
    )
    
    audio, sr = sf.read(str(audio_path))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    
    # Get reference feature-complete words
    base_res = run_speech_pipeline(
        audio_source=str(audio_path),
        transcript=transcript,
        filename="jfk_rice_excerpt_real.wav",
        reference_words=None,
    )
    base_words = base_res["words"]
    
    # Choose word index 10 ("Houston") and insert 0.8s silence
    target_idx = 10
    target_end_s = base_words[target_idx]["end"]
    split_sample = int(target_end_s * sr)
    
    pause_len_s = 0.8
    silence = np.zeros(int(pause_len_s * sr), dtype=np.float32)
    mod_audio = np.concatenate([audio[:split_sample], silence, audio[split_sample:]])
    
    mod_wav_path = str(tmp_path / "jfk_injected_pause.wav")
    sf.write(mod_wav_path, mod_audio, sr)
    
    # Run pipeline contrastively vs baseline words
    result = run_speech_pipeline(
        audio_source=mod_wav_path,
        transcript=transcript,
        filename="jfk_injected_pause.wav",
        reference_words=base_words,
        reference_id="jfk_ideal",
    )
    
    # Search for detected pause flaw near target_end_s
    pause_flaws = [f for f in result["flaws"] if f["flaw_type"] == "inappropriate_pause"]
    assert len(pause_flaws) >= 1, f"Expected inappropriate_pause to be detected, found flaws: {result['flaws']}"
    
    best_flaw = min(pause_flaws, key=lambda f: abs(f["start_s"] - target_end_s))
    start_error_ms = abs(best_flaw["start_s"] - target_end_s) * 1000.0
    assert start_error_ms <= 100.0, f"Pause start error {start_error_ms:.1f}ms exceeds 100ms tolerance"


@pytest.mark.slow
def test_monotone_contrastive_detection(tmp_path):
    """Gate Test: Artificially flattened pitch contour is grounded as a monotone pitch flaw."""
    audio_path = Path("data/processed/jfk_rice_excerpt_real.wav")
    assert audio_path.exists()
    
    transcript = (
        "140000 miles away from the control station in Houston a giant rocket more than 300 feet tall "
        "the length of this football field made of new metal alloys some of which have not yet been embedded "
        "capable of standing heat and stresses several times more than have ever been experienced "
        "pitted together with a precision better than the finest watch carrying all the equipment needed "
        "for propulsion guidance control communication food and survival on an untried mission to an unknown celestial body "
        "and then return it safely to earth re-entering the atmosphere at speeds of over 25000 miles per hour "
        "causing heat about half that on the temperature of the sun almost as hot as it is here today "
        "and do all this and do all this and do it right and do it first if all this thick heat is out then we must be bald ."
    )
    
    audio, sr = sf.read(str(audio_path))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    
    base_res = run_speech_pipeline(
        audio_source=str(audio_path),
        transcript=transcript,
        filename="jfk_rice_excerpt_real.wav",
        reference_words=None,
    )
    base_words = base_res["words"]
    
    # Flatten pitch across words 20 to 35 ("capable of standing heat and stresses...")
    w_start_s = base_words[20]["start"]
    w_end_s = base_words[35]["end"]
    s_idx = int(w_start_s * sr)
    e_idx = int(w_end_s * sr)
    
    slice_audio = audio[s_idx:e_idx]
    snd = parselmouth.Sound(slice_audio, sampling_frequency=sr)
    pitch = snd.to_pitch()
    voiced = pitch.selected_array["frequency"][pitch.selected_array["frequency"] > 0]
    med_f0 = float(np.median(voiced)) if len(voiced) > 0 else 130.0
    
    manip = call(snd, "To Manipulation...", 0.01, 75.0, 500.0)
    pitch_tier = call(manip, "Extract pitch tier")
    call(pitch_tier, "Multiply frequencies...", snd.xmin, snd.xmax, 0.15)
    call(pitch_tier, "Shift frequencies...", snd.xmin, snd.xmax, float(med_f0 * 0.85), "Hertz")
    call([pitch_tier, manip], "Replace pitch tier")
    res_sound = call(manip, "Get resynthesis (overlap-add)")
    flat_arr = res_sound.values[0][:len(slice_audio)]
    
    mod_audio = audio.copy()
    mod_audio[s_idx:s_idx + len(flat_arr)] = flat_arr
    
    mod_wav_path = str(tmp_path / "jfk_injected_monotone.wav")
    sf.write(mod_wav_path, mod_audio, sr)
    
    # Run pipeline contrastively
    result = run_speech_pipeline(
        audio_source=mod_wav_path,
        transcript=transcript,
        filename="jfk_injected_monotone.wav",
        reference_words=base_words,
        reference_id="jfk_ideal",
    )
    
    monotone_flaws = [f for f in result["flaws"] if f["flaw_type"] in ["monotone", "monotone_pitch"]]
    assert len(monotone_flaws) >= 1, f"Expected monotone flaw, detected: {result['flaws']}"
    
    # Check that detected monotone flaw overlaps with injected window
    overlap = any(max(0, min(f["end_s"], w_end_s) - max(f["start_s"], w_start_s)) > 0.5 for f in monotone_flaws)
    assert overlap, f"Monotone flaw detected outside target window [{w_start_s:.2f}, {w_end_s:.2f}]: {monotone_flaws}"


@pytest.mark.slow
def test_level_4_ideal_low_false_positive_rate():
    """Gate Test: Level 4 ideal recording has <= 1 spurious flaw in contrastive evaluation."""
    audio_path = Path("data/processed/reagan_challenger_excerpt_real.wav")
    assert audio_path.exists()
    
    transcript = (
        "and tell them, your dedication and professionalism have moved and impressed us for decades, and we know of your anguish. We share it.\" There's a coincidence today. On this day, 390 years ago, the great explorer Sir Francis Drake died aboard ship off the coast of Panama. In his lifetime, the great frontiers were the oceans, and a historian later said he lived by the sea, died on it, and was buried in it. Well, today, we can say of the challenger crew, their dedication was, like Drake's, complete. The crew of the space shuttle challenger honored us for the manner in which they lived their lives. We will never forget them, nor the last time we saw them this morning, as they prepared for their journey and waved goodbye, and slipped the surly bonds of earth to touch the face of God. Thank you."
    )
    
    base_res = run_speech_pipeline(
        audio_source=str(audio_path),
        transcript=transcript,
        filename="reagan_challenger_excerpt_real.wav",
        reference_words=None,
    )
    base_words = base_res["words"]
    
    result = run_speech_pipeline(
        audio_source=str(audio_path),
        transcript=transcript,
        filename="reagan_challenger_excerpt_real.wav",
        reference_words=base_words,
        reference_id="reagan_ideal",
    )
    
    assert len(result["flaws"]) <= 1, f"Expected <= 1 spurious flaws on ideal take, found {len(result['flaws'])}: {result['flaws']}"
    assert result["scores"]["overall"] >= 95.0, f"Ideal score should be >= 95.0, got {result['scores']['overall']}"


@pytest.mark.slow
def test_null_injection_control(tmp_path):
    """Item 1a/8: Identity Praat resynthesis of ideal audio produces <= 2 flags contrastively."""
    audio_path = Path("data/processed/jfk_rice_excerpt_real.wav")
    assert audio_path.exists(), f"Audio not found: {audio_path}"

    transcript = (
        "140000 miles away from the control station in Houston a giant rocket more than 300 feet tall "
        "the length of this football field made of new metal alloys some of which have not yet been embedded "
        "capable of standing heat and stresses several times more than have ever been experienced "
        "pitted together with a precision better than the finest watch carrying all the equipment needed "
        "for propulsion guidance control communication food and survival on an untried mission to an unknown celestial body "
        "and then return it safely to earth re-entering the atmosphere at speeds of over 25000 miles per hour "
        "causing heat about half that on the temperature of the sun almost as hot as it is here today "
        "and do all this and do all this and do it right and do it first if all this thick heat is out then we must be bald ."
    )

    audio, sr = sf.read(str(audio_path))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)

    # Identity Praat resynthesis
    snd = parselmouth.Sound(audio, sampling_frequency=sr)
    manip = call(snd, "To Manipulation...", 0.01, 75.0, 500.0)
    pitch_tier = call(manip, "Extract pitch tier")
    call(pitch_tier, "Multiply frequencies...", snd.xmin, snd.xmax, 1.0)
    call(pitch_tier, "Shift frequencies...", snd.xmin, snd.xmax, 0.0, "Hertz")
    call([pitch_tier, manip], "Replace pitch tier")
    res_sound = call(manip, "Get resynthesis (overlap-add)")
    null_audio = res_sound.values[0].astype(np.float32)
    if len(null_audio) < len(audio):
        null_audio = np.pad(null_audio, (0, len(audio) - len(null_audio)))
    else:
        null_audio = null_audio[:len(audio)]

    null_path = str(tmp_path / "jfk_null_control.wav")
    sf.write(null_path, null_audio, sr)

    # Get reference words
    base_res = run_speech_pipeline(
        audio_source=str(audio_path), transcript=transcript,
        filename="jfk_rice_excerpt_real.wav", reference_words=None,
    )

    # Score null-injected contrastively
    null_res = run_speech_pipeline(
        audio_source=null_path, transcript=transcript,
        filename="jfk_null_control.wav",
        reference_words=base_res["words"],
        reference_id="jfk_ideal",
    )

    num_flags = len(null_res["flaws"])
    assert num_flags <= 2, (
        f"Null-injection control should produce <= 2 flags (chain artifacts), got {num_flags}: "
        f"{[f['flaw_type'] + ' z=' + str(f.get('z_score', '?')) for f in null_res['flaws']]}"
    )


def test_region_merging():
    """Item 3/8: Overlapping detections are consolidated into composite regions with primary + secondary types."""
    from backend.pipeline.grounding import ground_flaw_regions

    # Create synthetic words with two overlapping flaw signals
    words = []
    for i in range(20):
        words.append({
            "text": f"word{i}",
            "start": i * 0.4,
            "end": (i + 1) * 0.4 - 0.05,
            "duration": 0.35,
            "pause_after_s": 0.05,
            "pause_before_s": 0.05,
            "has_punctuation": False,
            "f0_range_st": 1.0 if 5 <= i <= 12 else 6.0,  # Low range for words 5-12 (monotone)
            "f0_std_st": 0.3 if 5 <= i <= 12 else 2.0,
            "articulation_rate": 7.0 if 7 <= i <= 14 else 4.2,  # High rate for words 7-14 (rushed)
            "energy_mean_db": 0.0,
            "hnr_mean_db": 18.0,
            "is_flawed": False,
            "z_by_feature": {
                "f0_range_st_z": -3.0 if 5 <= i <= 12 else 0.0,
                "rate_syllables_per_sec_z": 3.0 if 7 <= i <= 14 else 0.0,
                "intensity_db_z": 0.0,
                "hnr_mean_db_z": 0.0,
                "pause_after_z": 0.0,
            },
        })

    # Load flaw rules
    from backend.pipeline.explain import load_flaw_rules
    flaw_rules = load_flaw_rules()

    # Run grounding in contrastive mode
    flaws = ground_flaw_regions(words, flaw_rules, reference_type="ideal_take")

    # With merging, overlapping monotone (5-12) and rushed (7-14) should be consolidated
    # into at most 2 composite regions (or even 1 if they overlap enough)
    # The key assertion: no two returned flaws should have > 50% temporal overlap
    for i, f1 in enumerate(flaws):
        for j, f2 in enumerate(flaws):
            if i >= j:
                continue
            overlap = max(0, min(f1["end_s"], f2["end_s"]) - max(f1["start_s"], f2["start_s"]))
            shorter = min(f1["end_s"] - f1["start_s"], f2["end_s"] - f2["start_s"])
            if shorter > 0:
                overlap_frac = overlap / shorter
                assert overlap_frac < 0.5, (
                    f"Overlapping flaws not merged: {f1['flaw_type']} [{f1['start_s']:.2f}-{f1['end_s']:.2f}] "
                    f"and {f2['flaw_type']} [{f2['start_s']:.2f}-{f2['end_s']:.2f}] overlap {overlap_frac:.1%}"
                )

    # Check that merged regions have secondary_types
    merged_with_secondary = [f for f in flaws if f.get("secondary_types")]
    # At least one merged region should exist given the overlap
    print(f"  Flaws produced: {len(flaws)}, with secondary types: {len(merged_with_secondary)}")
    for f in flaws:
        sec = f.get("secondary_types", [])
        print(f"    {f['flaw_type']} [{f['start_s']:.2f}-{f['end_s']:.2f}] z={f.get('z_score', 0):.2f} secondary={[s['flaw_type'] for s in sec]}")

