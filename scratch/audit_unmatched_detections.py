import os, sys
sys.path.insert(0, os.path.abspath('.'))
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import json, soundfile as sf, numpy as np
from backend.pipeline.orchestrator import run_speech_pipeline
from dataset_tools.benchmark_grounding import compute_iou

with open('data/manifests/real_speech_manifest.json') as f:
    real_manifest = json.load(f)
with open('data/manifests/injected_dataset_manifest.json') as f:
    injected_manifest = json.load(f)

# Cache reference pipeline results
ref_cache = {}
for sp in real_manifest:
    s_id = sp['speech_id']
    audio_path = os.path.join('data', 'processed', sp['processed_file'])
    res = run_speech_pipeline(audio_path, sp['transcript'], filename=sp['processed_file'])
    ref_cache[s_id] = res

unmatched_detections = []
all_detections_count = 0
all_matches_count = 0

for rec in injected_manifest:
    rec_id = rec['recording_id']
    sp_id = rec['speech_id']
    level = rec['quality_level']
    if level == 4:
        continue

    audio_path = os.path.join('data', 'injected', rec['audio_file'])
    json_path = os.path.join('data', 'injected', rec['annotation_file'])
    with open(json_path) as f:
        gt_data = json.load(f)
    gt_flaws = gt_data['flaws']
    sp_entry = next(s for s in real_manifest if s['speech_id'] == sp_id)
    transcript = sp_entry['transcript']
    ref_res = ref_cache[sp_id]

    res = run_speech_pipeline(
        audio_path,
        transcript,
        filename=rec['audio_file'],
        reference_words=ref_res['words'],
        reference_id=f"{sp_id}_level_4",
    )
    detected_flaws = res['flaws']
    all_detections_count += len(detected_flaws)

    matched_gt = set()
    matched_det = set()

    for g_i, g in enumerate(gt_flaws):
        for d_i, d in enumerate(detected_flaws):
            if d_i in matched_det:
                continue
            if d['flaw_type'] == g['flaw_type']:
                iou = compute_iou(g['start_s'], g['end_s'], d['start_s'], d['end_s'])
                if iou >= 0.50:
                    matched_gt.add(g_i)
                    matched_det.add(d_i)
                    all_matches_count += 1
                    break

    # Inspect unmatched detections
    for d_i, d in enumerate(detected_flaws):
        if d_i not in matched_det:
            # Check overlap with any GT flaw
            overlaps = []
            for g in gt_flaws:
                iou = compute_iou(g['start_s'], g['end_s'], d['start_s'], d['end_s'])
                inter_s = max(0, min(g['end_s'], d['end_s']) - max(g['start_s'], d['start_s']))
                if inter_s > 0.05:
                    overlaps.append((g, iou, inter_s))

            # Classify
            classification = "unknown"
            notes = ""
            if overlaps:
                ov_g, ov_iou, ov_inter = overlaps[0]
                if ov_g['flaw_type'] == d['flaw_type']:
                    classification = "(a) fragment of same GT flaw"
                    notes = f"overlaps GT {ov_g['flaw_type']} [{ov_g['start_s']}-{ov_g['end_s']}] with partial IoU={ov_iou:.2f}"
                else:
                    classification = "(b) overlaps GT but wrong type"
                    notes = f"overlaps GT {ov_g['flaw_type']} [{ov_g['start_s']}-{ov_g['end_s']}] (detected as {d['flaw_type']})"
            else:
                if d['flaw_type'] == 'breathy_unclear':
                    classification = "(c) injection artefact (HNR dip near splice/stretch)"
                    notes = "unvoiced/transition frame near time stretch splice"
                elif abs(d['z_score']) >= 2.0:
                    classification = "(d) genuine feature of speech/prosody"
                    notes = "natural phrase boundary tempo/pitch modulation"
                else:
                    classification = "(e) other"

            unmatched_detections.append({
                "recording_id": rec_id,
                "level": level,
                "flaw_type": d['flaw_type'],
                "start_s": d['start_s'],
                "end_s": d['end_s'],
                "words": d['words'],
                "z_score": d['z_score'],
                "severity": d.get('severity', 0.0),
                "classification": classification,
                "notes": notes,
            })

print(f"Total Detections: {all_detections_count} | Total Matched: {all_matches_count} | Unmatched: {len(unmatched_detections)}")
print("\n" + "="*120)
print(f"{'Recording':<32} | {'Type':<18} | {'Span (s)':<16} | {'z':<6} | {'Class':<35} | {'Notes'}")
print("="*120)
for u in unmatched_detections:
    span_str = f"[{u['start_s']:.2f}-{u['end_s']:.2f}]"
    print(f"{u['recording_id']:<32} | {u['flaw_type']:<18} | {span_str:<16} | {u['z_score']:+5.1f} | {u['classification']:<35} | {u['notes']}")
