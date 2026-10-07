"""
Temporal flaw grounding module.
Identifies stress points, applies hysteresis thresholding, merges adjacent spans,
and snaps flaw start/end boundaries strictly to aligned word edges.
"""

import os
import yaml
import numpy as np
from scipy.signal import find_peaks
from typing import List, Dict, Any, Tuple

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "thresholds.yaml")


def load_grounding_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
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
) -> List[Tuple[int, int]]:
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
    words: List[Dict[str, Any]],
    flaw_rules: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Evaluates flaw rules against normalized word z-scores.
    Detects continuous spans, merges adjacent occurrences within merge_gap_s,
    and snaps boundaries to exact word start/end times.
    """
    cfg = load_grounding_config()
    high_z = cfg.get("hysteresis_high_z", 2.2)
    low_z = cfg.get("hysteresis_low_z", 1.5)
    min_dur = cfg.get("min_region_duration_s", 0.25)
    merge_gap = cfg.get("merge_gap_s", 0.30)

    num_words = len(words)
    if num_words == 0:
        return []

    grounded_flaws = []
    flaw_id_counter = 1

    for rule in flaw_rules:
        f_type = rule["flaw_type"]
        trigger = rule["trigger"]
        metric_name = trigger["metric"]
        threshold = trigger["threshold"]
        operator = trigger["operator"]
        min_words = trigger.get("min_duration_words", 1)

        # 1. Handle Pause Flaws (Inter-word event)
        if f_type in ["inappropriate_pause", "missing_pause"]:
            for i, w in enumerate(words[:-1]):
                pause_val = w["pause_after_s"]
                has_punct = w.get("has_punctuation", False)
                word_after = words[i + 1]

                is_triggered = False
                if f_type == "inappropriate_pause":
                    # Non-punctuated pause that exceeds threshold
                    if not has_punct and pause_val >= threshold:
                        is_triggered = True
                elif f_type == "missing_pause":
                    # Punctuated pause that is too short
                    if has_punct and pause_val <= threshold:
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

        # Invert sign for '<=' operators so find_hysteresis_regions works uniformly
        if operator == "<=":
            signal = -z_arr
            high_th = -threshold
            low_th = -threshold * 0.7
        else:
            signal = z_arr
            high_th = threshold
            low_th = threshold * 0.7

        raw_regions = find_hysteresis_regions(signal, high_th, low_th)

        # Merge adjacent regions if word gap is small
        merged_regions = []
        for reg in raw_regions:
            s_idx, e_idx = reg
            if (e_idx - s_idx + 1) < min_words:
                continue

            if merged_regions and (s_idx - merged_regions[-1][1] <= 1):
                # Merge
                prev_s, _ = merged_regions.pop()
                merged_regions.append((prev_s, e_idx))
            else:
                merged_regions.append((s_idx, e_idx))

        # Snap to word boundaries and enforce duration
        for s_idx, e_idx in merged_regions:
            start_s = words[s_idx]["start"]
            end_s = words[e_idx]["end"]
            dur = end_s - start_s

            if dur < min_dur:
                continue

            # Mark words as flawed
            for w_i in range(s_idx, e_idx + 1):
                words[w_i]["is_flawed"] = True

            # Extract representative observed vs baseline values
            sub_words = words[s_idx : e_idx + 1]
            flaw_z = float(np.mean(z_arr[s_idx : e_idx + 1]))

            if f_type == "monotone":
                obs_val = float(np.mean([w["f0_range_st"] for w in sub_words]))
                base_val = 5.8
            elif f_type in ["rushed", "drag_slow"]:
                obs_val = float(np.mean([w["articulation_rate"] for w in sub_words]))
                base_val = 4.2
            elif f_type == "volume_drop":
                obs_val = float(np.mean([w["energy_mean_db"] for w in sub_words]))
                base_val = 0.0
            elif f_type == "breathy_unclear":
                obs_val = float(np.mean([w["hnr_mean_db"] for w in sub_words]))
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

    return grounded_flaws
