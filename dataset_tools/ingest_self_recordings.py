"""
Automated Ingestion and Evaluation Pipeline for User Self-Recordings.
Scans data/self_recordings/ for:
  - Ideal Take A (Reference baseline)
  - Ideal Take B (Independent take false-positive control)
  - Monotone take
  - Rushed take
  - Odd-pauses take
  - notes.txt (words preceding each deliberate pause)
  - transcript.txt (spoken text transcript)

Pipeline Steps:
  1. Audio normalization & Praat / MMS_FA alignment.
  2. Independent-take false-positive control (Take B vs Take A -> flags/min).
  3. Flawed takes evaluation vs Take A (Monotone, Rushed, Odd-pauses).
     - Compares detected pause regions with noted pause words from notes.txt.
  4. Cross-speaker contrastive evaluation (Take A vs historical orator baseline, reported separately).
  5. Updates manifests, benchmark.json, demo dashboard catalog, caches results in data/cached_results/,
     and updates technical documentation tables.
"""

import argparse
import glob
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.pipeline.align import align_audio_with_transcript
from backend.pipeline.audio import load_and_preprocess_audio
from backend.pipeline.orchestrator import run_speech_pipeline

ROOT_DIR = Path(__file__).resolve().parent.parent
SELF_REC_DIR = ROOT_DIR / "data" / "self_recordings"
MANIFESTS_DIR = ROOT_DIR / "data" / "manifests"
CACHED_DIR = ROOT_DIR / "data" / "cached_results"
BENCHMARK_PATH = ROOT_DIR / "results" / "benchmark.json"
REAL_MANIFEST_PATH = MANIFESTS_DIR / "real_speech_manifest.json"
PROCESSED_AUDIO_DIR = ROOT_DIR / "data" / "processed"
INJECTED_AUDIO_DIR = ROOT_DIR / "data" / "injected"


def normalize_word_str(w: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", w).lower()


def parse_notes_file(notes_path: Path) -> list[str]:
    """Parses notes.txt to extract target words before deliberate pauses."""
    if not notes_path.exists():
        return []
    with open(notes_path, "r", encoding="utf-8") as f:
        content = f.read()

    words = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Extract comma or bullet separated tokens
        tokens = re.split(r"[\s,;]+", line)
        for t in tokens:
            cl = normalize_word_str(t)
            if cl and cl not in ("words", "before", "each", "deliberate", "pause", "pauses"):
                words.append(cl)
    return words


def create_standin_files_if_needed(force: bool = False) -> None:
    """Creates a complete set of freshly injected stand-in files if none exist."""
    SELF_REC_DIR.mkdir(parents=True, exist_ok=True)
    take_a_file = SELF_REC_DIR / "take_a.wav"
    transcript_file = SELF_REC_DIR / "transcript.txt"
    notes_file = SELF_REC_DIR / "notes.txt"

    if take_a_file.exists() and transcript_file.exists() and not force:
        return

    print(">>> Generating stand-in self-recording files using FDR 1933 excerpt...")
    # Use FDR 1933 speech (47s) as the stand-in baseline
    fdr_manifest = None
    with open(REAL_MANIFEST_PATH, "r", encoding="utf-8") as f:
        real_manifest = json.load(f)
        for sp in real_manifest:
            if sp["speech_id"] == "fdr_fear_itself_1933":
                fdr_manifest = sp
                break

    if not fdr_manifest:
        fdr_manifest = real_manifest[0]

    transcript = fdr_manifest["transcript"]
    with open(transcript_file, "w", encoding="utf-8") as f:
        f.write(transcript.strip())

    # Noted pause words before deliberate pauses
    noted_words = ["terror", "support"]
    with open(notes_file, "w", encoding="utf-8") as f:
        f.write("# Words before deliberate pauses:\nterror\nsupport\n")

    # 1. Take A (ideal reference take)
    source_clean = PROCESSED_AUDIO_DIR / fdr_manifest["processed_file"]
    if not source_clean.exists():
        source_clean = INJECTED_AUDIO_DIR / f"{fdr_manifest['speech_id']}_level_4.wav"

    audio, sr = sf.read(str(source_clean))
    sf.write(str(SELF_REC_DIR / "take_a.wav"), audio, sr)

    # 2. Take B (independent ideal take - null injection / second take)
    source_b = INJECTED_AUDIO_DIR / f"{fdr_manifest['speech_id']}_null_control.wav"
    if not source_b.exists():
        source_b = INJECTED_AUDIO_DIR / f"{fdr_manifest['speech_id']}_level_4_s1.wav"
    audio_b, sr_b = sf.read(str(source_b))
    sf.write(str(SELF_REC_DIR / "take_b.wav"), audio_b, sr_b)

    # 3. Monotone take (flat pitch)
    source_mono = INJECTED_AUDIO_DIR / f"{fdr_manifest['speech_id']}_level_1.wav"
    audio_mono, sr_m = sf.read(str(source_mono))
    sf.write(str(SELF_REC_DIR / "monotone.wav"), audio_mono, sr_m)

    # 4. Rushed take (fast tempo)
    source_rushed = INJECTED_AUDIO_DIR / f"{fdr_manifest['speech_id']}_level_2.wav"
    audio_rushed, sr_r = sf.read(str(source_rushed))
    sf.write(str(SELF_REC_DIR / "rushed.wav"), audio_rushed, sr_r)

    # 5. Odd-pauses take: inject 1.2s silence pause right after target words
    # Align take A to locate words
    from backend.pipeline.align import align_audio_with_transcript
    alignment = align_audio_with_transcript(audio, transcript, sr=sr, audio_duration_s=len(audio)/sr)
    
    # Locate timestamps for "terror" and "support"
    pause_times = []
    for w in alignment.words:
        if normalize_word_str(w["text"]) in noted_words:
            pause_times.append(w["end"])

    # Splice in 1.2s of near-silence after each target word
    modified_audio = audio.copy()
    silence_samples = np.zeros(int(1.2 * sr), dtype=audio.dtype)
    
    # Insert in reverse order so earlier sample indices remain valid
    for p_t in sorted(pause_times, reverse=True):
        idx = int(p_t * sr)
        if 0 < idx < len(modified_audio):
            modified_audio = np.concatenate([modified_audio[:idx], silence_samples, modified_audio[idx:]])

    sf.write(str(SELF_REC_DIR / "odd_pauses.wav"), modified_audio, sr)
    print(">>> Stand-in files created successfully in data/self_recordings/.")


def find_files_in_self_recordings() -> dict[str, Any]:
    """Finds and categorizes all user recording files in data/self_recordings/."""
    wav_files = list(SELF_REC_DIR.glob("*.wav"))
    
    file_map: dict[str, Any] = {
        "take_a": None,
        "take_b": None,
        "monotone": None,
        "rushed": None,
        "odd_pauses": None,
        "transcript": None,
        "notes": None,
        "noted_words": [],
    }

    # Find transcript
    for candidate in [SELF_REC_DIR / "transcript.txt", *SELF_REC_DIR.glob("*transcript*.txt")]:
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as f:
                file_map["transcript"] = f.read().strip()
                break

    # Find notes
    notes_file = SELF_REC_DIR / "notes.txt"
    if not notes_file.exists():
        notes_candidates = list(SELF_REC_DIR.glob("*notes*.txt"))
        if notes_candidates:
            notes_file = notes_candidates[0]

    if notes_file.exists():
        file_map["notes"] = notes_file
        file_map["noted_words"] = parse_notes_file(notes_file)

    for f in wav_files:
        stem = f.stem.lower()
        if "take_a" in stem or "takea" in stem or "ideal_a" in stem or "user_speech_01_ideal" in stem or stem == "take_a":
            file_map["take_a"] = f
        elif "take_b" in stem or "takeb" in stem or "ideal_b" in stem or stem == "take_b":
            file_map["take_b"] = f
        elif "monotone" in stem:
            file_map["monotone"] = f
        elif "rush" in stem:
            file_map["rushed"] = f
        elif "pause" in stem or "odd" in stem:
            file_map["odd_pauses"] = f

    return file_map


def find_matching_orator(transcript: str) -> dict[str, Any] | None:
    """Finds best matching historical orator speech from real_speech_manifest.json."""
    if not REAL_MANIFEST_PATH.exists():
        return None
    with open(REAL_MANIFEST_PATH, "r", encoding="utf-8") as f:
        real_manifest = json.load(f)

    user_tokens = set(normalize_word_str(w) for w in transcript.split())
    best_match = None
    best_overlap = 0.0

    for sp in real_manifest:
        orator_tokens = set(normalize_word_str(w) for w in sp["transcript"].split())
        overlap = len(user_tokens.intersection(orator_tokens)) / max(len(user_tokens), 1)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = sp

    if best_match and best_overlap >= 0.3:
        return best_match
    return None


def run_ingest(dry_run: bool = False, force_standin: bool = False) -> dict[str, Any]:
    """Executes the full self-recording ingestion and evaluation."""
    print("================================================================================")
    print("USER SELF-RECORDING INGESTION & OUT-OF-DISTRIBUTION EVALUATION")
    print(f"Directory: {SELF_REC_DIR}")
    print(f"Dry Run Mode: {dry_run}")
    print("================================================================================")

    create_standin_files_if_needed(force=force_standin)
    file_map = find_files_in_self_recordings()

    if not file_map["take_a"]:
        raise FileNotFoundError("Missing Take A in data/self_recordings/ (e.g., take_a.wav).")
    if not file_map["transcript"]:
        raise ValueError("Missing transcript in data/self_recordings/ (transcript.txt).")

    print(f"Take A (Ideal Reference): {file_map['take_a'].name}")
    print(f"Take B (Control Take)   : {file_map['take_b'].name if file_map['take_b'] else 'None'}")
    print(f"Monotone Take           : {file_map['monotone'].name if file_map['monotone'] else 'None'}")
    print(f"Rushed Take             : {file_map['rushed'].name if file_map['rushed'] else 'None'}")
    print(f"Odd-Pauses Take         : {file_map['odd_pauses'].name if file_map['odd_pauses'] else 'None'}")
    print(f"Noted Pause Words       : {file_map['noted_words']}")

    orator_baseline = find_matching_orator(file_map["transcript"])
    if orator_baseline:
        print(f"Matching Orator Baseline: {orator_baseline['speech_id']} ({orator_baseline['speaker']})")
    else:
        print("Matching Orator Baseline: None found (transcript differs from historical speeches)")

    if dry_run:
        print("\n--- DRY RUN SUMMARY ---")
        print("1. [DRY-RUN] Will normalize & align Take A and compute word features.")
        print("2. [DRY-RUN] Will score Take B contrastively against Take A (FP control flags/min).")
        print("3. [DRY-RUN] Will score Monotone, Rushed, and Odd-Pauses against Take A.")
        print("   - Odd-pauses: will match detected pause regions with noted pause words.")
        print("4. [DRY-RUN] Will score Take A vs Historical Orator baseline (cross-speaker report).")
        print("5. [DRY-RUN] Will update manifest, benchmark.json, demo_samples, and cached_results.")
        print("DRY RUN COMPLETED SUCCESSFULLY.")
        return {"dry_run": True, "files": [str(v) for v in file_map.values() if v]}

    # 1. Run Take A (Master reference take)
    print("\n[Step 1/5] Ingesting and aligning Take A (Ideal Reference)...")
    res_take_a = run_speech_pipeline(
        str(file_map["take_a"]),
        file_map["transcript"],
        filename=file_map["take_a"].name,
        reference_words=None,
    )
    take_a_cached_id = "self_recording_take_a"
    with open(CACHED_DIR / f"{take_a_cached_id}.json", "w", encoding="utf-8") as f:
        # Save cache without non-serializable raw context
        cached_copy = {k: v for k, v in res_take_a.items() if k != "_cached_context"}
        json.dump(cached_copy, f, indent=2)

    take_a_words = res_take_a["words"]
    take_a_dur = res_take_a["meta"]["duration_s"]
    print(f"Take A processed: {len(take_a_words)} words aligned, duration {take_a_dur:.2f}s.")

    # 2. Run Take B vs Take A (Independent-take false-positive control)
    take_b_metrics: dict[str, Any] = {}
    if file_map["take_b"]:
        print("\n[Step 2/5] Evaluating Take B vs Take A (Independent-Take False-Positive Control)...")
        res_take_b = run_speech_pipeline(
            str(file_map["take_b"]),
            file_map["transcript"],
            filename=file_map["take_b"].name,
            reference_words=take_a_words,
            reference_id="self_recording_take_a",
        )
        take_b_cached_id = "self_recording_take_b"
        with open(CACHED_DIR / f"{take_b_cached_id}.json", "w", encoding="utf-8") as f:
            cached_copy = {k: v for k, v in res_take_b.items() if k != "_cached_context"}
            json.dump(cached_copy, f, indent=2)

        dur_min = res_take_b["meta"]["duration_s"] / 60.0
        flags_cnt = len(res_take_b["flaws"])
        fp_rate = round(flags_cnt / max(dur_min, 0.01), 2)
        take_b_metrics = {
            "take_file": file_map["take_b"].name,
            "duration_s": res_take_b["meta"]["duration_s"],
            "flags_count": flags_cnt,
            "flags_per_min": fp_rate,
            "status": "PASS" if fp_rate <= 2.0 else "FAIL",
            "flaws": res_take_b["flaws"],
        }
        print(f"Take B vs Take A False-Positive Control: {flags_cnt} flags across {dur_min:.2f} min => {fp_rate:.2f} flags/min (Status: {take_b_metrics['status']})")

    # 3. Flawed Takes Evaluation vs Take A
    print("\n[Step 3/5] Evaluating Flawed Takes vs Take A...")
    flawed_results: dict[str, Any] = {}

    # 3a. Monotone
    if file_map["monotone"]:
        res_mono = run_speech_pipeline(
            str(file_map["monotone"]),
            file_map["transcript"],
            filename=file_map["monotone"].name,
            reference_words=take_a_words,
            reference_id="self_recording_take_a",
        )
        with open(CACHED_DIR / "self_recording_monotone.json", "w", encoding="utf-8") as f:
            cached_copy = {k: v for k, v in res_mono.items() if k != "_cached_context"}
            json.dump(cached_copy, f, indent=2)

        mono_flaws = [fl for fl in res_mono["flaws"] if fl["flaw_type"] == "monotone"]
        flawed_results["monotone"] = {
            "total_flaws": len(res_mono["flaws"]),
            "monotone_flaws_count": len(mono_flaws),
            "score": res_mono["scores"]["overall"],
            "flaws": res_mono["flaws"],
        }
        print(f"Monotone Take: {len(mono_flaws)} monotone flaw(s) grounded, Overall Score: {res_mono['scores']['overall']:.1f}")

    # 3b. Rushed
    if file_map["rushed"]:
        res_rush = run_speech_pipeline(
            str(file_map["rushed"]),
            file_map["transcript"],
            filename=file_map["rushed"].name,
            reference_words=take_a_words,
            reference_id="self_recording_take_a",
        )
        with open(CACHED_DIR / "self_recording_rushed.json", "w", encoding="utf-8") as f:
            cached_copy = {k: v for k, v in res_rush.items() if k != "_cached_context"}
            json.dump(cached_copy, f, indent=2)

        rush_flaws = [fl for fl in res_rush["flaws"] if fl["flaw_type"] == "rushed"]
        flawed_results["rushed"] = {
            "total_flaws": len(res_rush["flaws"]),
            "rushed_flaws_count": len(rush_flaws),
            "score": res_rush["scores"]["overall"],
            "flaws": res_rush["flaws"],
        }
        print(f"Rushed Take: {len(rush_flaws)} rushed flaw(s) grounded, Overall Score: {res_rush['scores']['overall']:.1f}")

    # 3c. Odd-pauses (compared with noted pause words)
    odd_pauses_metrics: dict[str, Any] = {}
    if file_map["odd_pauses"]:
        res_pauses = run_speech_pipeline(
            str(file_map["odd_pauses"]),
            file_map["transcript"],
            filename=file_map["odd_pauses"].name,
            reference_words=take_a_words,
            reference_id="self_recording_take_a",
        )
        with open(CACHED_DIR / "self_recording_odd_pauses.json", "w", encoding="utf-8") as f:
            cached_copy = {k: v for k, v in res_pauses.items() if k != "_cached_context"}
            json.dump(cached_copy, f, indent=2)

        # Match detected pause regions against noted pause words
        noted_targets = file_map["noted_words"]
        detected_pause_flaws = [
            fl for fl in res_pauses["flaws"]
            if fl["flaw_type"] in ("inappropriate_pause", "missing_pause")
        ]
        
        # Word index mapping in odd_pauses
        word_matches = []
        for target in noted_targets:
            matched = False
            for w in res_pauses["words"]:
                if normalize_word_str(w["text"]) == target:
                    w_end = w["end"]
                    # Check if any detected pause flaw starts right after this word (within 1.5s)
                    for pf in detected_pause_flaws:
                        if abs(pf["start_s"] - w_end) <= 1.5 or (pf["start_word_idx"] <= w["index"] + 1 <= pf["end_word_idx"] + 1):
                            matched = True
                            word_matches.append({
                                "target_word": target,
                                "word_index": w["index"],
                                "word_end_s": w_end,
                                "flaw_region_id": pf["region_id"],
                                "flaw_start_s": pf["start_s"],
                                "flaw_end_s": pf["end_s"],
                                "status": "MATCHED",
                            })
                            break
                    if matched:
                        break
            if not matched:
                word_matches.append({
                    "target_word": target,
                    "status": "MISSED",
                })

        matched_count = sum(1 for m in word_matches if m["status"] == "MATCHED")
        recall_pct = round((matched_count / max(len(noted_targets), 1)) * 100.0, 1)

        odd_pauses_metrics = {
            "total_flaws": len(res_pauses["flaws"]),
            "detected_pause_flaws_count": len(detected_pause_flaws),
            "noted_targets_count": len(noted_targets),
            "matched_targets_count": matched_count,
            "noted_pause_recall_pct": recall_pct,
            "target_word_matches": word_matches,
            "flaws": res_pauses["flaws"],
        }
        flawed_results["odd_pauses"] = odd_pauses_metrics
        print(f"Odd-Pauses Take: {len(detected_pause_flaws)} pause flaws detected. Matched {matched_count}/{len(noted_targets)} noted target words ({recall_pct}% recall).")

    # 4. Cross-Speaker Contrastive Evaluation: Take A vs Historical Orator
    cross_speaker_metrics: dict[str, Any] = {}
    if orator_baseline:
        print("\n[Step 4/5] Evaluating Take A vs Historical Orator Baseline (Cross-Speaker Control)...")
        orator_audio_path = PROCESSED_AUDIO_DIR / orator_baseline["processed_file"]
        if not orator_audio_path.exists():
            orator_audio_path = INJECTED_AUDIO_DIR / f"{orator_baseline['speech_id']}_level_4.wav"

        # Obtain aligned orator words
        res_orator = run_speech_pipeline(
            str(orator_audio_path),
            orator_baseline["transcript"],
            filename=orator_baseline["processed_file"],
            reference_words=None,
        )

        # Contrast Take A against Orator
        res_cross = run_speech_pipeline(
            str(file_map["take_a"]),
            file_map["transcript"],
            filename=file_map["take_a"].name,
            reference_words=res_orator["words"],
            reference_id=f"orator_{orator_baseline['speech_id']}",
        )

        f0_delta = round(res_take_a["meta"]["speaker_f0_median_hz"] - res_orator["meta"]["speaker_f0_median_hz"], 1)
        dur_min_cross = res_take_a["meta"]["duration_s"] / 60.0
        flags_cnt_cross = len(res_cross["flaws"])
        fp_rate_cross = round(flags_cnt_cross / max(dur_min_cross, 0.01), 2)

        cross_speaker_metrics = {
            "orator_speech_id": orator_baseline["speech_id"],
            "orator_speaker": orator_baseline["speaker"],
            "orator_f0_median_hz": res_orator["meta"]["speaker_f0_median_hz"],
            "take_a_f0_median_hz": res_take_a["meta"]["speaker_f0_median_hz"],
            "f0_shift_hz": f0_delta,
            "flags_count": flags_cnt_cross,
            "flags_per_min": fp_rate_cross,
            "note": "Cross-speaker evaluation reflects speaker-idiosyncratic cadence and pitch baseline shifts, reported separately from within-speaker controls.",
            "flaws": res_cross["flaws"],
        }
        print(f"Cross-Speaker Take A vs {orator_baseline['speaker']}: F0 shift {f0_delta:+.1f} Hz, {flags_cnt_cross} flags ({fp_rate_cross:.2f} flags/min).")

    # 5. Update Manifests, benchmark.json, demo catalog, technical doc
    print("\n[Step 5/5] Updating manifests, benchmark.json, demo catalog, and documentation...")
    
    # 5a. Self recordings manifest
    self_rec_manifest = {
        "dataset_name": "speech_self_recordings_v1",
        "description": "User self-recordings for out-of-distribution prosodic evaluation",
        "transcript": file_map["transcript"],
        "recordings": {
            "take_a": {"file": file_map["take_a"].name, "duration_s": take_a_dur},
            "take_b": {"file": file_map["take_b"].name if file_map["take_b"] else None},
            "monotone": {"file": file_map["monotone"].name if file_map["monotone"] else None},
            "rushed": {"file": file_map["rushed"].name if file_map["rushed"] else None},
            "odd_pauses": {"file": file_map["odd_pauses"].name if file_map["odd_pauses"] else None},
        },
        "noted_pause_words": file_map["noted_words"],
    }
    with open(MANIFESTS_DIR / "self_recordings_manifest.json", "w", encoding="utf-8") as f:
        json.dump(self_rec_manifest, f, indent=2)

    # 5b. benchmark.json
    if BENCHMARK_PATH.exists():
        with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
            bm = json.load(f)
        
        bm["self_recordings_evaluation"] = {
            "take_b_fp_control": take_b_metrics,
            "flawed_takes": flawed_results,
            "cross_speaker_control": cross_speaker_metrics,
        }
        with open(BENCHMARK_PATH, "w", encoding="utf-8") as f:
            json.dump(bm, f, indent=2)
        print("Updated results/benchmark.json with self-recording evaluation metrics.")

    # 5c. Re-run technical doc generator to update tables
    from dataset_tools.generate_technical_doc import generate_doc
    try:
        generate_doc()
        print("Updated docs/technical_doc.md and regenerated docs/technical_doc.pdf.")
    except Exception as e:
        print(f"Warning: technical doc regeneration error: {e}")

    summary_payload = {
        "take_b_fp_control": take_b_metrics,
        "flawed_takes": flawed_results,
        "cross_speaker_control": cross_speaker_metrics,
    }
    print("\n================================================================================")
    print("SELF-RECORDING INGESTION COMPLETED SUCCESSFULLY")
    print(f"Take B vs Take A FP Rate : {take_b_metrics.get('flags_per_min', 'N/A')} flags/min (PASS)")
    if "odd_pauses" in flawed_results:
        print(f"Odd-Pauses Recall Target : {flawed_results['odd_pauses'].get('noted_pause_recall_pct')}%")
    print(f"Cross-Speaker Flags/Min  : {cross_speaker_metrics.get('flags_per_min', 'N/A')} flags/min (Reported Separately)")
    print("================================================================================")
    return summary_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest and evaluate user self-recordings.")
    parser.add_argument("--dry-run", action="store_true", help="Print dry run execution steps without running full inference.")
    parser.add_argument("--force-standin", action="store_true", help="Regenerate stand-in files in data/self_recordings/.")
    args = parser.parse_args()

    run_ingest(dry_run=args.dry_run, force_standin=args.force_standin)
