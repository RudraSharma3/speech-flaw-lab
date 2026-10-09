"""
Calibrates and validates the deterministic speech pipeline across all 3 real speeches:
- JFK Rice Address (1962)
- Ronald Reagan Challenger Address (1986)
- FDR First Inaugural Address (1933) - Held-out test set
Evaluates strictly in Reference-Free Mode against population priors.
Reports speech rate (excluding pauses >= 250ms), voiced fraction, and exact pacing z-score math.
"""

import json
import os
import sys

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.pipeline.features import compute_speech_rate_excluding_pauses, extract_frame_features_praat
from backend.pipeline.normalize import load_population_priors
from backend.pipeline.orchestrator import run_speech_pipeline


PROCESSED_DIR = "data/processed"
MANIFEST_PATH = "data/manifests/real_speech_manifest.json"


def test_speech_pipeline():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        speeches = json.load(f)

    priors = load_population_priors()
    rate_prior_med = priors["articulation_rate"]["median"]
    rate_prior_mad = priors["articulation_rate"]["mad"]
    rate_prior_sigma = 1.4826 * rate_prior_mad

    results_summary = []

    for speech in speeches:
        s_id = speech["speech_id"]
        title = speech["title"]
        speaker = speech["speaker"]
        wav_file = os.path.join(PROCESSED_DIR, speech["processed_file"])
        transcript = speech["transcript"]

        print("\n========================================================")
        print(f"EVALUATING REAL SPEECH: {title}")
        print(f"Speaker: {speaker} | Audio: {wav_file} ({speech['duration_s']}s)")
        print("========================================================")

        # 1. Reference-Free Mode (Priors norming)
        res_priors = run_speech_pipeline(
            audio_source=wav_file,
            transcript=transcript,
            filename=speech["processed_file"],
            reference_words=None,
            reference_id=None,
        )

        score_priors = res_priors["scores"]["overall"]
        grade_priors = res_priors["scores"]["grade"]
        flaws_priors = res_priors["flaws"]
        words_priors = res_priors["words"]

        # 2. Independent Speech Rate (excluding pauses >= 250ms)
        rate_info = compute_speech_rate_excluding_pauses(words_priors, pause_threshold_s=0.250)
        speech_rate = rate_info["speech_rate_syl_per_s"]
        total_syl = rate_info["total_syllables"]
        active_speech_time = rate_info["active_speech_time_s"]

        # Exact pacing z-score arithmetic
        pacing_z = (speech_rate - rate_prior_med) / rate_prior_sigma

        # 3. Voiced frames analysis & HNR
        import soundfile as sf
        audio_arr, sr = sf.read(wav_file)
        if audio_arr.ndim > 1:
            audio_arr = audio_arr.mean(axis=1)
        praat_feats = extract_frame_features_praat(audio_arr, sr=sr)
        voiced_frac = praat_feats["voiced_frame_fraction"]
        mean_hnr = praat_feats["speaker_mean_hnr_db"]

        print("\n--- [REFERENCE-FREE / POPULATION PRIORS EVALUATION] ---")
        print(f"Overall Score: {score_priors:.1f}/100 (Grade: {grade_priors})")
        print(f"Total Words Aligned: {len(words_priors)} | Total Syllables: {total_syl}")
        print(f"Total Duration: {speech['duration_s']:.2f}s | Active Speech Time: {active_speech_time:.2f}s")
        print(f"Speech Rate (excluding pauses >= 250ms): {speech_rate:.2f} syl/s")
        print(f"Pacing z-score Arithmetic: ({speech_rate:.2f} - {rate_prior_med:.2f}) / (1.4826 * {rate_prior_mad:.2f}) = ({speech_rate - rate_prior_med:+.2f}) / {rate_prior_sigma:.4f} = {pacing_z:+.2f}")
        print(f"Voiced Frames Fraction: {voiced_frac*100:.1f}% | Voiced Mean HNR: {mean_hnr:.1f} dB")
        print(f"Total Prosodic Flaws Flagged: {len(flaws_priors)}")
        for flaw in flaws_priors:
            print(f"  * [{flaw['start_s']:.2f}s - {flaw['end_s']:.2f}s] {flaw['flaw_type']:20s} (Sev: {flaw['severity']:.2f}): \"{flaw['words']}\"")
            print(f"    Rationale: {flaw['rationale_text']}")

        print("\nDimension Breakdown:")
        for dim in res_priors["scores"]["dimensions"]:
            score_str = f"{dim['score']:5.1f}/100" if dim['score'] is not None else "  EXCLUDED"
            print(f"    - {dim['name']:30s} (wt: {dim['weight']:.2f}): {score_str} | {dim['summary']}")

        results_summary.append({
            "speech_id": s_id,
            "speaker": speaker,
            "duration_s": speech["duration_s"],
            "words_count": len(words_priors),
            "total_syllables": total_syl,
            "active_speech_time_s": active_speech_time,
            "speech_rate": speech_rate,
            "pacing_z": round(pacing_z, 2),
            "voiced_frac": round(voiced_frac, 3),
            "mean_hnr": round(mean_hnr, 1),
            "score": score_priors,
            "grade": grade_priors,
            "flaws_count": len(flaws_priors),
        })

    print("\n\n=========================================================================================================")
    print("MASTER SUMMARY TABLE: 3 REAL SPEECHES (REFERENCE-FREE EVALUATION)")
    print("=========================================================================================================")
    print(f"{'Speech ID':<25} | {'Dur (s)':<8} | {'Words':<6} | {'Syllables':<9} | {'Speech Time':<11} | {'Rate (syl/s)':<12} | {'Pacing z':<9} | {'Voiced %':<8} | {'Score':<7} | {'Grade':<5} | {'Flaws':<5}")
    print("-" * 125)
    for r in results_summary:
        print(f"{r['speech_id']:<25} | {r['duration_s']:<8.1f} | {r['words_count']:<6d} | {r['total_syllables']:<9d} | {r['active_speech_time_s']:<11.1f} | {r['speech_rate']:<12.2f} | {r['pacing_z']:<+9.2f} | {r['voiced_frac']*100:<7.1f}% | {r['score']:<7.1f} | {r['grade']:<5s} | {r['flaws_count']:<5d}")


if __name__ == "__main__":
    test_speech_pipeline()
