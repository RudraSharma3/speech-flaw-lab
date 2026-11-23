"""
Re-caches the 9 official demo catalog samples and 4 reference takes with canonical transcripts.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))
from backend.pipeline.orchestrator import run_speech_pipeline
from dataset_tools.cache_gradient_results import match_flaws_hungarian, json_serialize

DATA_DIR = Path("data")
INJECTED_DIR = DATA_DIR / "injected"
CACHED_DIR = DATA_DIR / "cached_results"
MANIFESTS_DIR = DATA_DIR / "manifests"

SPEECHES = [
    "jfk_moon_1962",
    "reagan_challenger_1986",
    "fdr_fear_itself_1933",
    "reagan_mourning_1986",
    "jfk_we_choose_1962",
]

CATALOG_LEVELS = {
    "jfk_moon_1962": [4, 3, 2, 1, 0],
    "reagan_challenger_1986": [4, 1],
    "fdr_fear_itself_1933": [4, 1],
    "reagan_mourning_1986": [4, 1],
    "jfk_we_choose_1962": [4, 1],
}

def recache_demo_catalog():
    with open(MANIFESTS_DIR / "real_speech_manifest.json", "r", encoding="utf-8") as f:
        manifest = {s["speech_id"]: s["transcript"] for s in json.load(f)}

    for sp in SPEECHES:
        transcript = manifest[sp]
        print(f"\nProcessing {sp}...")

        # 1. Level 4 (reference)
        ref_id = f"{sp}_level_4"
        ref_wav = INJECTED_DIR / f"{ref_id}.wav"
        with open(ref_wav, "rb") as f:
            ref_bytes = f.read()

        ref_result = run_speech_pipeline(
            audio_source=ref_bytes,
            transcript=transcript,
            filename=f"{ref_id}.wav",
            reference_words=None,
            reference_id=None
        )
        ref_result["ground_truth_flaws"] = []
        ref_result["ground_truth_eval"] = []
        ref_result.pop("_cached_context", None)
        if "series" in ref_result and ref_result["series"]:
            ref_result["series"]["spectrogram"] = None
            ref_result["series"]["mfcc"] = None

        with open(CACHED_DIR / f"{ref_id}.json", "w", encoding="utf-8") as f:
            json.dump(ref_result, f, default=json_serialize, indent=2)
        print(f"  [OK] Cached {ref_id}")

        ref_words = ref_result["words"]

        # 2. Other catalog levels
        other_levels = [lvl for lvl in CATALOG_LEVELS[sp] if lvl != 4]
        for lvl in other_levels:
            sample_id = f"{sp}_level_{lvl}"
            wav_path = INJECTED_DIR / f"{sample_id}.wav"
            gt_path = INJECTED_DIR / f"{sample_id}_flaws.json"

            with open(wav_path, "rb") as f:
                wav_bytes = f.read()

            gt_flaws = []
            if gt_path.exists():
                with open(gt_path, "r", encoding="utf-8") as f:
                    gt_flaws = json.load(f).get("flaws", [])

            res = run_speech_pipeline(
                audio_source=wav_bytes,
                transcript=transcript,
                filename=f"{sample_id}.wav",
                reference_words=ref_words,
                reference_id=ref_id
            )
            eval_rows = match_flaws_hungarian(res.get("flaws", []), gt_flaws, iou_thresh=0.3)
            res["ground_truth_flaws"] = gt_flaws
            res["ground_truth_eval"] = eval_rows
            res.pop("_cached_context", None)
            if "series" in res and res["series"]:
                res["series"]["spectrogram"] = None
                res["series"]["mfcc"] = None

            with open(CACHED_DIR / f"{sample_id}.json", "w", encoding="utf-8") as f:
                json.dump(res, f, default=json_serialize, indent=2)
            print(f"  [OK] Cached {sample_id} (Score: {res['scores']['overall']:.1f}, Flaws: {len(res['flaws'])})")

if __name__ == "__main__":
    recache_demo_catalog()
