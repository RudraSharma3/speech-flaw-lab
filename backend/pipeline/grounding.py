"""
Temporal flaw grounding module.
Identifies stress points, applies hysteresis thresholding, merges adjacent spans,
and snaps flaw start/end boundaries strictly to aligned word edges.
"""

import os
from typing import Any

import numpy as np
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "thresholds.yaml")


def load_grounding_config() -> dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f).get("grounding", {})
    return {
        "hysteresis_high_z": 2.2,
        "hysteresis_low_z": 1.5,
        "peak_prominence_z": 1.4,
        "min_region_duration_s": 0.25,
        "merge_gap_s": 0.30,
        "snap_to_words": True,
    }


def find_hysteresis_regions(
    signal: np.ndarray, high_thresh: float, low_thresh: float
) -> list[tuple[int, int]]:
    """
    Finds contiguous index regions using double-threshold hysteresis.
    A region activates when signal exceeds high_thresh and stays active until it drops below low_thresh.
    """
    regions = []
    in_region = False
    start_idx = 0

    for i, val in enumerate(signal):
        if not in_region:
            if val >= high_thresh:
                in_region = True
                start_idx = i
        else:
            if val < low_thresh:
                in_region = False
                regions.append((start_idx, i - 1))

    if in_region:
        regions.append((start_idx, len(signal) - 1))

    return regions


def ground_flaw_regions(
    words: list[dict[str, Any]],
    flaw_rules: list[dict[str, Any]],
    reference_type: str = "population_prior",
) -> list[dict[str, Any]]:
    """
    Evaluates flaw rules against normalized word z-scores.
    Detects continuous spans, merges adjacent occurrences within merge_gap_s,
    and snaps boundaries to exact word start/end times.
    """
    cfg = load_grounding_config()
    min_dur = cfg.get("min_region_duration_s", 0.25)
    num_words = len(words)
    if num_words == 0:
        return []

    grounded_flaws = []
    flaw_id_counter = 1

    for rule in flaw_rules:
        f_type = rule["flaw_type"]
        
        # Breathy unclear is disabled: in reference-free mode due to uncalibrated absolute HNR,
        # and in contrastive mode because alignment boundary jitter causes false positive cascades.
        if f_type == "breathy_unclear":
            continue

        trigger = rule["trigger"]
        metric_name = trigger["metric"]
        threshold = trigger["threshold"]
        operator = trigger["operator"]
        min_words = trigger.get("min_duration_words", 1)

        # In reference-free mode, require at least 5 words for speech rate deviations
        if reference_type != "ideal_take" and f_type in ["rushed", "drag_slow"]:
            min_words = max(min_words, 5)

        # 1. Handle Pause Flaws (Inter-word event)
        if f_type in ["inappropriate_pause", "missing_pause"]:
            if reference_type == "ideal_take":
                pause_th = 0.35 if f_type == "inappropriate_pause" else 0.08
                z_thresh = 1.3
            else:
                pause_th = max(threshold, 1.20)
                z_thresh = 1.8

            for i, w in enumerate(words[:-1]):
                pause_val = w["pause_after_s"]
                has_punct = w.get("has_punctuation", False)
                word_after = words[i + 1]

                is_triggered = False
                p_z = w.get("z_by_feature", {}).get("pause_after_z", 0.0)
                if f_type == "inappropriate_pause" and not has_punct and pause_val >= pause_th and p_z >= z_thresh:
                    is_triggered = True
                elif f_type == "missing_pause" and has_punct and pause_val <= pause_th and p_z <= -z_thresh:
                    is_triggered = True

                if is_triggered:
                    start_t = w["end"]
                    end_t = word_after["start"]
                    # Mark involved words
                    w["is_flawed"] = True
                    word_after["is_flawed"] = True

                    grounded_flaws.append({
                        "flaw_id": f"flaw_{flaw_id_counter:02d}_{f_type}",
                        "rule_id": rule["id"],
                        "flaw_type": f_type,
                        "feature": rule["feature"],
                        "unit": rule["unit"],
                        "start_word_idx": i,
                        "end_word_idx": i + 1,
                        "start_s": round(start_t, 3),
                        "end_s": round(end_t, 3),
                        "words": f"{w['text']} [pause] {word_after['text']}",
                        "word_before": w["text"],
                        "word_after": word_after["text"],
                        "punctuation": w.get("punctuation", ""),
                        "observed_value": round(pause_val, 3),
                        "baseline_value": 0.05 if f_type == "inappropriate_pause" else 0.50,
                        "delta": round(pause_val - (0.05 if f_type == "inappropriate_pause" else 0.50), 3),
                        "z_score": round(w.get("z_by_feature", {}).get("pause_after_z", 2.5), 2),
                        "rule": rule,
                    })
                    flaw_id_counter += 1
            continue

        # 2. Handle Continuous Feature Flaws (F0, rate, intensity, HNR)
        z_scores = []
        for w in words:
            z = w.get("z_by_feature", {}).get(metric_name, 0.0)
            z_scores.append(z)

        z_arr = np.array(z_scores)

        # Calibrate effective threshold for contrastive vs population mode
        if reference_type == "ideal_take":
            if f_type == "monotone":
                eff_threshold = -1.8
                eff_min_words = 4  # ~1.5s at typical word rate
            elif f_type in ["rushed", "drag_slow"]:
                eff_threshold = 1.8 if operator == ">=" else -1.8
                eff_min_words = 3
            elif f_type == "volume_drop":
                eff_threshold = -1.5
                eff_min_words = 2
            else:
                eff_threshold = threshold * 0.50
                eff_min_words = max(2, min_words - 1)
        else:
            eff_threshold = threshold
            eff_min_words = min_words

        # Invert sign for '<=' operators so find_hysteresis_regions works uniformly
        if operator == "<=":
            signal = -z_arr
            high_th = -eff_threshold
            low_th = -eff_threshold * 0.70
        else:
            signal = z_arr
            high_th = eff_threshold
            low_th = eff_threshold * 0.70

        raw_regions = find_hysteresis_regions(signal, high_th, low_th)

        # Merge adjacent regions if word gap is small (gap <= 2 words)
        merged_regions = []
        for reg in raw_regions:
            s_idx, e_idx = reg
            if merged_regions and (s_idx - merged_regions[-1][1] <= 2):
                prev_s, _ = merged_regions.pop()
                merged_regions.append((prev_s, e_idx))
            else:
                merged_regions.append((s_idx, e_idx))

        # Filter by min duration words
        filtered_regions = [reg for reg in merged_regions if (reg[1] - reg[0] + 1) >= eff_min_words]

        # Snap to word boundaries and enforce duration
        for s_idx, e_idx in filtered_regions:
            start_s = words[s_idx]["start"]
            end_s = words[e_idx]["end"]
            dur = end_s - start_s

            if dur < min_dur:
                continue

            sub_words = words[s_idx : e_idx + 1]

            # For monotone: require at least 1.5s contiguous region and reference-relative pitch range ratio < 0.60
            if f_type == "monotone":
                if dur < 1.5:
                    continue
                if reference_type == "ideal_take":
                    ratios = [w.get("f0_range_ratio") for w in sub_words if w.get("f0_range_ratio") is not None]
                    mean_ratio = float(np.mean(ratios)) if ratios else 1.0
                    if mean_ratio >= 0.60:
                        continue

            # Mark words as flawed
            for w_i in range(s_idx, e_idx + 1):
                words[w_i]["is_flawed"] = True

            # Extract representative observed vs baseline values
            flaw_z = float(np.mean(z_arr[s_idx : e_idx + 1]))

            if f_type == "monotone":
                vals = [w["f0_range_st"] for w in sub_words if w.get("f0_range_st") is not None]
                obs_val = float(np.mean(vals)) if vals else 0.0
                base_val = 5.8
            elif f_type in ["rushed", "drag_slow"]:
                vals = [w["articulation_rate"] for w in sub_words if w.get("articulation_rate") is not None]
                obs_val = float(np.mean(vals)) if vals else 4.2
                base_val = 4.2
            elif f_type == "volume_drop":
                vals = [w["energy_mean_db"] for w in sub_words if w.get("energy_mean_db") is not None]
                obs_val = float(np.mean(vals)) if vals else 0.0
                base_val = 0.0
            elif f_type == "breathy_unclear":
                vals = [w["hnr_mean_db"] for w in sub_words if w.get("hnr_mean_db") is not None]
                obs_val = float(np.mean(vals)) if vals else 18.0
                base_val = 18.0
            else:
                obs_val = 0.0
                base_val = 0.0

            words_str = " ".join(w["text"] for w in sub_words)

            grounded_flaws.append({
                "flaw_id": f"flaw_{flaw_id_counter:02d}_{f_type}",
                "rule_id": rule["id"],
                "flaw_type": f_type,
                "feature": rule["feature"],
                "unit": rule["unit"],
                "start_word_idx": s_idx,
                "end_word_idx": e_idx,
                "start_s": round(start_s, 3),
                "end_s": round(end_s, 3),
                "words": words_str,
                "observed_value": round(obs_val, 2),
                "baseline_value": round(base_val, 2),
                "delta": round(obs_val - base_val, 2),
                "z_score": round(flaw_z, 2),
                "rule": rule,
            })
            flaw_id_counter += 1

    # ---- Region Consolidation ----
    # Merge overlapping or adjacent (gap < 0.3s) detections across flaw types
    # into composite regions with a primary type (highest |z|) and secondary deviations.
    if len(grounded_flaws) > 1:
        merge_gap_s = cfg.get("merge_gap_s", 0.30)
        # Sort by start time
        grounded_flaws.sort(key=lambda f: f["start_s"])
        
        merged = []
        current = dict(grounded_flaws[0])
        current["secondary_types"] = []
        current["_is_merged"] = False
        current_spans = [(current.get("start_word_idx", 0), current.get("end_word_idx", 0))]

        for nxt in grounded_flaws[1:]:
            gap = nxt["start_s"] - current["end_s"]
            overlap = min(current["end_s"], nxt["end_s"]) - max(current["start_s"], nxt["start_s"])
            
            # Only merge if there is true temporal overlap (overlap > 0)
            # or consecutive touching words without a gap (no unflagged words in between)
            touching_words = (nxt.get("start_word_idx", 0) <= current.get("end_word_idx", 0) + 1) and (gap <= 0.05)
            
            if overlap > 0 or touching_words:
                current["_is_merged"] = True
                nxt_spans = [(nxt.get("start_word_idx", 0), nxt.get("end_word_idx", 0))]
                current_spans.extend(nxt_spans)

                # Primary = highest |z_score|
                if abs(nxt.get("z_score", 0)) > abs(current.get("z_score", 0)):
                    old_primary_type = current["flaw_type"]
                    old_primary_z = current.get("z_score", 0)
                    current["secondary_types"].append({
                        "flaw_type": old_primary_type,
                        "z_score": old_primary_z,
                    })
                    current["flaw_type"] = nxt["flaw_type"]
                    current["flaw_id"] = nxt["flaw_id"]
                    current["rule_id"] = nxt["rule_id"]
                    current["feature"] = nxt["feature"]
                    current["unit"] = nxt["unit"]
                    current["observed_value"] = nxt["observed_value"]
                    current["baseline_value"] = nxt["baseline_value"]
                    current["delta"] = nxt["delta"]
                    current["z_score"] = nxt["z_score"]
                    current["rule"] = nxt["rule"]
                else:
                    current["secondary_types"].append({
                        "flaw_type": nxt["flaw_type"],
                        "z_score": nxt.get("z_score", 0),
                    })
                
                # Trim merged region strictly to extent of words actually flagged
                min_w = max(0, min(s for s, e in current_spans))
                max_w = min(len(words) - 1, max(e for s, e in current_spans))
                current["start_word_idx"] = min_w
                current["end_word_idx"] = max_w
                current["start_s"] = round(words[min_w]["start"], 3)
                current["end_s"] = round(words[max_w]["end"], 3)

                if current["start_word_idx"] < len(words) and current["end_word_idx"] < len(words):
                    current["words"] = " ".join(
                        words[k]["text"] for k in range(current["start_word_idx"], current["end_word_idx"] + 1)
                    )
            else:
                current.pop("_flagged_spans", None)
                merged.append(current)
                current = dict(nxt)
                current["secondary_types"] = []
                current["_is_merged"] = False
                current_spans = [(current.get("start_word_idx", 0), current.get("end_word_idx", 0))]
        
        current.pop("_flagged_spans", None)
        merged.append(current)
        grounded_flaws = merged

    return grounded_flaws

