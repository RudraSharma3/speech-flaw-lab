"""
Generate pre-cached AnalysisResult JSONs for the real injected recordings.
Stores in data/cached_results/{sample_id}.json with:
- Contrastive analysis against Level 4 reference
- Ground truth flaws loaded from data/injected/{recording_id}_flaws.json
- One-to-one Hungarian IoU matching and boundary errors for per-sample evaluation table
- Deletes any remaining mock_demo files.
"""

import json
import os
import glob
from scipy.optimize import linear_sum_assignment
from backend.pipeline.orchestrator import run_speech_pipeline

SPEECHES = [
    "jfk_moon_1962",
    "reagan_challenger_1986",
    "fdr_fear_itself_1933",
    "reagan_mourning_1986",
    "jfk_we_choose_1962",
]

LEVELS = [4, 3, 2, 1, 0]
SEEDS = ["", "_s1", "_s2"]  # Seed 0 (no suffix), Seed 1, Seed 2

import numpy as np

def json_serialize(obj):
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if isinstance(obj, (np.floating, float)):
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    return str(obj)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
INJECTED_DIR = os.path.join(DATA_DIR, "injected")
CACHED_DIR = os.path.join(DATA_DIR, "cached_results")
RAW_DIR = os.path.join(DATA_DIR, "raw")
MANIFESTS_DIR = os.path.join(DATA_DIR, "manifests")

os.makedirs(CACHED_DIR, exist_ok=True)

def compute_iou(s1, e1, s2, e2):
    inter = max(0.0, min(e1, e2) - max(s1, s2))
    union = max(e1, e2) - min(s1, s2)
    return inter / union if union > 0 else 0.0

def match_flaws_hungarian(detected_flaws, gt_flaws, iou_thresh=0.3):
    """Computes strict 1-to-1 Hungarian matching between detections and GT flaws."""
    eval_rows = []
    if not gt_flaws and not detected_flaws:
        return []
    
    cost_matrix = []
    for d in detected_flaws:
        row = []
        for g in gt_flaws:
            iou = compute_iou(d["start_s"], d["end_s"], g["start_s"], g["end_s"])
            row.append(1.0 - iou if iou >= iou_thresh else 1.0)
        cost_matrix.append(row)
        
    matched_det = set()
    matched_gt = set()
    
    if cost_matrix and len(cost_matrix[0]) > 0:
        d_ind, g_ind = linear_sum_assignment(cost_matrix)
        for d_i, g_i in zip(d_ind, g_ind):
            cost = cost_matrix[d_i][g_i]
            iou = 1.0 - cost
            if iou >= iou_thresh:
                det = detected_flaws[d_i]
                gt = gt_flaws[g_i]
                gt_t = gt.get("flaw_type", gt.get("type", "unknown"))
                matched_det.add(d_i)
                matched_gt.add(g_i)
                eval_rows.append({
                    "status": "MATCHED",
                    "detected_id": det["region_id"],
                    "detected_type": det["flaw_type"],
                    "detected_span": [det["start_s"], det["end_s"]],
                    "detected_words": det.get("words", ""),
                    "gt_id": gt.get("flaw_id", f"gt_{g_i}"),
                    "gt_type": gt_t,
                    "gt_span": [gt["start_s"], gt["end_s"]],
                    "gt_words": gt.get("words", ""),
                    "iou": round(iou, 3),
                    "start_error_ms": round(abs(det["start_s"] - gt["start_s"]) * 1000.0, 1),
                    "end_error_ms": round(abs(det["end_s"] - gt["end_s"]) * 1000.0, 1),
                    "type_match": det["flaw_type"] == gt_t
                })
                
    # Unmatched Detections (False Positives)
    for d_i, det in enumerate(detected_flaws):
        if d_i not in matched_det:
            eval_rows.append({
                "status": "FALSE_POSITIVE",
                "detected_id": det["region_id"],
                "detected_type": det["flaw_type"],
                "detected_span": [det["start_s"], det["end_s"]],
                "detected_words": det.get("words", ""),
                "gt_id": None,
                "gt_type": None,
                "gt_span": None,
                "gt_words": None,
                "iou": 0.0,
                "start_error_ms": None,
                "end_error_ms": None,
                "type_match": False
            })
            
    # Missed Ground Truth Flaws (False Negatives)
    for g_i, gt in enumerate(gt_flaws):
        if g_i not in matched_gt:
            gt_t = gt.get("flaw_type", gt.get("type", "unknown"))
            eval_rows.append({
                "status": "MISSED_GT",
                "detected_id": None,
                "detected_type": None,
                "detected_span": None,
                "detected_words": None,
                "gt_id": gt.get("flaw_id", f"gt_{g_i}"),
                "gt_type": gt_t,
                "gt_span": [gt["start_s"], gt["end_s"]],
                "gt_words": gt.get("words", ""),
                "iou": 0.0,
                "start_error_ms": 2000.0,  # Miss penalty
                "end_error_ms": 2000.0,
                "type_match": False
            })
            
    return eval_rows

def main():
    # Remove old mock_demo files
    for mock_file in glob.glob(os.path.join(CACHED_DIR, "mock_*.json")):
        try:
            os.remove(mock_file)
            print(f"Removed old mock file: {mock_file}")
        except Exception:
            pass

    manifest_path = os.path.join(MANIFESTS_DIR, "real_speech_manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest_items = json.load(f)
    speech_transcripts = {item["speech_id"]: item["transcript"] for item in manifest_items}

    for speech in SPEECHES:
        transcript = speech_transcripts.get(speech)
        if not transcript:
            continue
            
        # 1. First process Level 4 (reference) to get reference words
        ref_wav_path = os.path.join(INJECTED_DIR, f"{speech}_level_4.wav")
        if not os.path.exists(ref_wav_path):
            continue
            
        print(f"\n--- Processing Reference: {speech} Level 4 ---")
        with open(ref_wav_path, "rb") as f:
            ref_bytes = f.read()
            
        ref_result = run_speech_pipeline(
            audio_source=ref_bytes,
            transcript=transcript,
            filename=f"{speech}_level_4.wav",
            reference_words=None,
            reference_id=None
        )
        
        # Save reference Level 4
        ref_id = f"{speech}_level_4"
        ref_result["ground_truth_flaws"] = []
        ref_result["ground_truth_eval"] = []
        ref_result.pop("_cached_context", None)
        if "series" in ref_result and ref_result["series"]:
            ref_result["series"]["spectrogram"] = None
            ref_result["series"]["mfcc"] = None
        with open(os.path.join(CACHED_DIR, f"{ref_id}.json"), "w", encoding="utf-8") as f:
            json.dump(ref_result, f, default=json_serialize)
        print(f"Saved cached reference: {ref_id}.json")
        
        ref_words = ref_result["words"]
        
        # 2. Process all levels 4..0 and seeds
        for seed_suf in SEEDS:
            for lvl in LEVELS:
                rec_id = f"{speech}_level_{lvl}{seed_suf}"
                wav_path = os.path.join(INJECTED_DIR, f"{rec_id}.wav")
                flaws_path = os.path.join(INJECTED_DIR, f"{rec_id}_flaws.json")
                
                if not os.path.exists(wav_path):
                    continue
                    
                # Load GT flaws
                gt_flaws = []
                if os.path.exists(flaws_path):
                    with open(flaws_path, encoding="utf-8") as f:
                        gt_data = json.load(f)
                        gt_flaws = gt_data.get("flaws", [])
                        
                with open(wav_path, "rb") as f:
                    audio_bytes = f.read()
                    
                print(f"Caching: {rec_id} (contrastive vs {speech}_level_4)...")
                # Run contrastive against Level 4
                res = run_speech_pipeline(
                    audio_source=audio_bytes,
                    transcript=transcript,
                    filename=f"{rec_id}.wav",
                    reference_words=ref_words,
                    reference_id=f"{speech}_level_4"
                )
                
                # Strip heavy spectrogram matrices and internal cached context for compact fast caching
                res.pop("_cached_context", None)
                if "series" in res and res["series"]:
                    res["series"]["spectrogram"] = None
                    res["series"]["mfcc"] = None
                    
                # Attach GT flaws
                res["ground_truth_flaws"] = gt_flaws
                # Compute Hungarian evaluation
                res["ground_truth_eval"] = match_flaws_hungarian(res.get("flaws", []), gt_flaws, iou_thresh=0.3)
                
                out_path = os.path.join(CACHED_DIR, f"{rec_id}.json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(res, f, default=json_serialize)
                print(f"  -> Saved {out_path} (GT: {len(gt_flaws)}, Det: {len(res.get('flaws', []))})")

if __name__ == "__main__":
    main()
