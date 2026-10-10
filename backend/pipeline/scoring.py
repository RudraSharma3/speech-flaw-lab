"""
Deterministic Rubric Scoring Module.
Evaluates dimensions (0-100) using monotonic mathematical curves from configs/rubric.yaml
and computes weighted overall composite scores and estimated quality levels.
Strictly excludes HNR from reference-free scoring (evaluated only contrastively).
"""

import math
import os
from typing import Any

import numpy as np
import yaml

RUBRIC_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "rubric.yaml")


def load_rubric_config() -> dict[str, Any]:
    if os.path.exists(RUBRIC_PATH):
        with open(RUBRIC_PATH) as f:
            return yaml.safe_load(f)
    return {}


def evaluate_piecewise_linear(val: float, points: list[list[float]]) -> float:
    """Monotonic piecewise linear interpolation."""
    pts = sorted(points, key=lambda p: p[0])
    if val <= pts[0][0]:
        return float(pts[0][1])
    if val >= pts[-1][0]:
        return float(pts[-1][1])

    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        if x0 <= val <= x1:
            frac = (val - x0) / (x1 - x0) if x1 != x0 else 0.0
            return float(y0 + frac * (y1 - y0))

    return float(pts[-1][1])


def evaluate_sigmoid_symmetric(z_val: float, center: float = 0.0, steepness: float = 1.5, min_score: float = 10.0, max_score: float = 100.0) -> float:
    """Symmetric sigmoid penalty centered at 0 deviation."""
    abs_dev = abs(z_val - center)
    sig = 1.0 / (1.0 + math.exp(steepness * (abs_dev - 1.5)))
    return float(min_score + (max_score - min_score) * sig)


def evaluate_exponential_decay(penalty_value: float, base: float = 100.0, decay_per_inappropriate_pause_sec: float = 18.0, min_score: float = 5.0, **kwargs) -> float:
    """Exponential decay for penalty accumulation (e.g. pause disruptions)."""
    decay_rate = decay_per_inappropriate_pause_sec / 100.0
    score = base * math.exp(-decay_rate * penalty_value)
    return float(max(min_score, min(100.0, score)))


def score_dimension(
    dim_key: str,
    dim_cfg: dict[str, Any],
    words: list[dict[str, Any]],
    grounded_flaws: list[dict[str, Any]],
    reference_type: str = "population_prior",
) -> dict[str, Any]:
    """Scores a single rubric dimension based on its configured mathematical curve."""
    params = dim_cfg.get("params", {})
    name = dim_cfg.get("name", dim_key.title())
    is_ideal = reference_type == "ideal_take"

    # Calculate metric raw and z
    if dim_key == "pacing":
        z_vals = [w.get("z_by_feature", {}).get("rate_syllables_per_sec_z", 0.0) for w in words]
        metric_z = float(np.mean(np.abs(z_vals))) if z_vals else 0.0
        raw_rates = [w["articulation_rate"] for w in words if w.get("articulation_rate") is not None]
        metric_raw = float(np.mean(raw_rates)) if raw_rates else 4.2
        if is_ideal:
            score = evaluate_sigmoid_symmetric(metric_z, **params)
        else:
            score = evaluate_sigmoid_symmetric(metric_z, center=0.0, steepness=0.8, min_score=65.0, max_score=100.0)
        summary = f"Mean articulation rate {metric_raw:.1f} syl/s with mean |z|={metric_z:.2f}."

    elif dim_key == "pitch_expressiveness":
        z_vals = [w.get("z_by_feature", {}).get("f0_range_st_z", 0.0) for w in words]
        metric_z = float(np.mean(z_vals)) if z_vals else 0.0
        raw_ranges = [w["f0_range_st"] for w in words if w.get("f0_range_st") is not None]
        metric_raw = float(np.mean(raw_ranges)) if raw_ranges else 5.4
        if is_ideal:
            score = evaluate_piecewise_linear(metric_z, params.get("points", []))
        else:
            priors_points = [[-4.0, 45.0], [-2.0, 75.0], [-1.0, 90.0], [0.0, 100.0], [1.5, 95.0], [3.0, 85.0], [5.0, 70.0]]
            score = evaluate_piecewise_linear(metric_z, priors_points)
        summary = f"Average pitch range {metric_raw:.1f} semitones (z={metric_z:+.2f})."

    elif dim_key == "volume_dynamics":
        z_vals = [w.get("z_by_feature", {}).get("intensity_db_z", 0.0) for w in words]
        metric_z = float(np.mean(z_vals)) if z_vals else 0.0
        raw_energies = [w["energy_mean_db"] for w in words if w.get("energy_mean_db") is not None]
        metric_raw = float(np.mean(raw_energies)) if raw_energies else 0.0
        score = evaluate_piecewise_linear(metric_z, params.get("points", []))
        summary = f"Mean energy dynamic offset {metric_raw:+.1f} dB re median (z={metric_z:+.2f})."

    elif dim_key == "pauses_fluency":
        inapp_pauses = [f for f in grounded_flaws if f["flaw_type"] == "inappropriate_pause"]
        total_inapp_s = sum(f["observed_value"] for f in inapp_pauses)
        metric_raw = total_inapp_s
        metric_z = len(inapp_pauses) * 1.5
        score = evaluate_exponential_decay(total_inapp_s, **params)
        summary = f"{len(inapp_pauses)} disruptive pauses ({total_inapp_s:.2f}s total)."

    elif dim_key == "clarity_articulation":
        z_vals = [w.get("z_by_feature", {}).get("hnr_mean_db_z", 0.0) for w in words]
        metric_z = float(np.mean(z_vals)) if z_vals else 0.0
        raw_hnrs = [w["hnr_mean_db"] for w in words if w.get("hnr_mean_db") is not None]
        metric_raw = float(np.mean(raw_hnrs)) if raw_hnrs else 18.0
        if is_ideal:
            mid = params.get("midpoint_z", -1.8)
            k = params.get("steepness", 1.2)
            score = 15.0 + 85.0 / (1.0 + math.exp(-k * (metric_z - mid)))
            summary = f"Contrastive HNR clarity change {metric_raw:.1f} dB (z={metric_z:+.2f})."
        else:
            # Strictly excluded from reference-free score computation
            score = None
            summary = "Excluded in reference-free mode (HNR is evaluated only contrastively vs reference take)."

    else:
        score = 80.0
        metric_raw = 0.0
        metric_z = 0.0
        summary = "Standard evaluation"

    # In contrastive mode, apply smooth exponential decay penalty per dimension based on grounded flaw severity
    if is_ideal and score is not None:
        flaw_type_map = {
            "pacing": ["rushed", "drag_slow"],
            "pitch_expressiveness": ["monotone"],
            "volume_dynamics": ["volume_drop"],
            "pauses_fluency": ["inappropriate_pause", "missing_pause"],
            "clarity_articulation": ["breathy_unclear"],
        }
        relevant_types = flaw_type_map.get(dim_key, [])
        dim_flaws = [f for f in grounded_flaws if f["flaw_type"] in relevant_types]
        if dim_flaws:
            total_sev = sum(
                max(1.0, abs(f.get("z_score", 1.5))) * max(0.5, f["end_s"] - f["start_s"])
                for f in dim_flaws
            )
            score = float(max(10.0, score * math.exp(-0.075 * total_sev)))

    return {
        "id": dim_key,
        "name": name,
        "score": round(float(np.clip(score, 0.0, 100.0)), 1) if score is not None else None,
        "metric_raw": round(metric_raw, 2),
        "metric_z": round(metric_z, 2),
        "summary": summary,
    }


def calculate_overall_scores(
    words: list[dict[str, Any]],
    grounded_flaws: list[dict[str, Any]],
    reference_type: str = "population_prior",
) -> dict[str, Any]:
    """Calculates all dimension scores and weighted composite overall score."""
    rubric = load_rubric_config()
    is_contrastive = (reference_type == "ideal_take")
    
    if is_contrastive:
        weights = rubric.get("weights", {
            "pacing": 0.25,
            "pitch_expressiveness": 0.25,
            "volume_dynamics": 0.20,
            "pauses_fluency": 0.15,
            "clarity_articulation": 0.15,
        })
    else:
        # Re-weight across the 4 valid dimensions in reference-free mode
        weights = {
            "pacing": 0.30,
            "pitch_expressiveness": 0.30,
            "volume_dynamics": 0.20,
            "pauses_fluency": 0.20,
            "clarity_articulation": 0.00,
        }

    dimensions_cfg = rubric.get("dimensions", {})

    dim_results = []
    overall_score = 0.0

    for dim_key, weight in weights.items():
        cfg = dimensions_cfg.get(dim_key, {})
        scored_dim = score_dimension(dim_key, cfg, words, grounded_flaws, reference_type=reference_type)
        if scored_dim["score"] is not None and weight > 0:
            weighted = round(scored_dim["score"] * weight, 2)
            scored_dim["weight"] = weight
            scored_dim["weighted_score"] = weighted
            overall_score += weighted
        else:
            scored_dim["weight"] = 0.0
            scored_dim["weighted_score"] = 0.0
        dim_results.append(scored_dim)

    overall_score = round(float(np.clip(overall_score, 0.0, 100.0)), 1)

    # Assign Letter Grade
    if overall_score >= 93.0:
        grade = "A+"
        quality_level = 4
    elif overall_score >= 85.0:
        grade = "A"
        quality_level = 4
    elif overall_score >= 75.0:
        grade = "B"
        quality_level = 3
    elif overall_score >= 60.0:
        grade = "C"
        quality_level = 2
    elif overall_score >= 40.0:
        grade = "D"
        quality_level = 1
    else:
        grade = "F"
        quality_level = 0

    return {
        "overall": overall_score,
        "grade": grade,
        "quality_level_est": quality_level,
        "mode": "contrastive" if is_contrastive else "coarse_screening",
        "mode_label": "Contrastive Reference Evaluation" if is_contrastive else "Coarse Screening (Reference-Free)",
        "calibration_label": "Calibrated against ideal reference baseline" if is_contrastive else "LibriSpeech population priors (coarse screening)",
        "dimensions": dim_results,
    }

