"""
Speaker normalization and robust statistical deviation module.
Computes Median Absolute Deviation (MAD) robust z-scores against baseline reference or population priors.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

POP_NORMS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "population_norms", "librispeech_priors.json"
)

DEFAULT_POPULATION_PRIORS = {
    "f0_range_st": {"median": 5.4, "mad": 1.4},
    "articulation_rate": {"median": 4.3, "mad": 0.8},
    "energy_contrast_db": {"median": 6.8, "mad": 1.9},
    "hnr_mean_db": {"median": 18.2, "mad": 2.6},
    "unpunctuated_pause_s": {"median": 0.05, "mad": 0.04},
    "punctuated_pause_s": {"median": 0.52, "mad": 0.16},
}


def load_population_priors() -> Dict[str, Any]:
    if os.path.exists(POP_NORMS_PATH):
        try:
            with open(POP_NORMS_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_POPULATION_PRIORS


def compute_robust_z(val: float, median: float, mad: float, eps: float = 1e-6) -> float:
    """Computes robust z-score: z = (x - median) / (1.4826 * MAD)."""
    scale = 1.4826 * max(mad, eps)
    return float((val - median) / scale)


def calculate_baseline_distribution(
    baseline_words: List[Dict[str, Any]]
) -> Dict[str, Tuple[float, float]]:
    """
    Computes (median, MAD) for each feature across a baseline take's words.
    """
    feats = ["f0_range_st", "articulation_rate", "energy_mean_db", "hnr_mean_db"]
    dist = {}

    for f in feats:
        vals = [w[f] for w in baseline_words if f in w and w[f] is not None]
        if len(vals) > 0:
            med = float(np.median(vals))
            mad = float(np.median(np.abs(vals - med)))
            dist[f] = (med, max(mad, 0.1))
        else:
            priors = DEFAULT_POPULATION_PRIORS.get(f, {"median": 0.0, "mad": 1.0})
            dist[f] = (priors["median"], priors["mad"])

    return dist


def normalize_words_against_baseline(
    observed_words: List[Dict[str, Any]],
    baseline_words: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Performs per-word deviation on a word-index axis.
    Uses exact word correspondence from forced alignment when baseline is available,
    falling back to population priors when no ideal reference take is supplied.
    """
    priors = load_population_priors()
    has_ideal = baseline_words is not None and len(baseline_words) == len(observed_words)
    ref_type = "ideal_take" if has_ideal else "population_prior"

    base_dist = calculate_baseline_distribution(baseline_words) if has_ideal else {}

    normalized_words = []

    for i, w in enumerate(observed_words):
        w_norm = dict(w)
        z_dict = {}

        if has_ideal:
            b_w = baseline_words[i]
            
            # F0 range deviation vs baseline word
            f0_r = w["f0_range_st"]
            b_f0_r = b_w["f0_range_st"]
            f0_mad = base_dist.get("f0_range_st", (5.4, 1.4))[1]
            z_dict["f0_range_st_z"] = compute_robust_z(f0_r - b_f0_r, 0.0, f0_mad)

            # Articulation rate deviation vs baseline word
            rate = w["articulation_rate"]
            b_rate = b_w["articulation_rate"]
            rate_mad = base_dist.get("articulation_rate", (4.3, 0.8))[1]
            z_dict["rate_syllables_per_sec_z"] = compute_robust_z(rate - b_rate, 0.0, rate_mad)

            # Energy deviation
            e = w["energy_mean_db"]
            b_e = b_w["energy_mean_db"]
            e_mad = base_dist.get("energy_mean_db", (0.0, 2.0))[1]
            z_dict["intensity_db_z"] = compute_robust_z(e - b_e, 0.0, e_mad)

            # HNR deviation
            hnr = w["hnr_mean_db"]
            b_hnr = b_w["hnr_mean_db"]
            hnr_mad = base_dist.get("hnr_mean_db", (18.0, 2.5))[1]
            z_dict["hnr_mean_db_z"] = compute_robust_z(hnr - b_hnr, 0.0, hnr_mad)

            # Pause deviations
            p_after = w["pause_after_s"]
            b_p_after = b_w["pause_after_s"]
            p_mad = 0.12
            z_dict["pause_after_z"] = compute_robust_z(p_after - b_p_after, 0.0, p_mad)

        else:
            # Fallback to population priors
            f0_p = priors["f0_range_st"]
            z_dict["f0_range_st_z"] = compute_robust_z(w["f0_range_st"], f0_p["median"], f0_p["mad"])

            rate_p = priors["articulation_rate"]
            z_dict["rate_syllables_per_sec_z"] = compute_robust_z(
                w["articulation_rate"], rate_p["median"], rate_p["mad"]
            )

            z_dict["intensity_db_z"] = compute_robust_z(w["energy_mean_db"], 0.0, 2.0)
            
            hnr_p = priors["hnr_mean_db"]
            z_dict["hnr_mean_db_z"] = compute_robust_z(w["hnr_mean_db"], hnr_p["median"], hnr_p["mad"])

            p_after = w["pause_after_s"]
            has_p = w.get("has_punctuation", False)
            prior_key = "punctuated_pause_s" if has_p else "unpunctuated_pause_s"
            p_prior = priors[prior_key]
            z_dict["pause_after_z"] = compute_robust_z(p_after, p_prior["median"], p_prior["mad"])

        # Round z-scores
        w_norm["z_by_feature"] = {k: round(v, 2) for k, v in z_dict.items()}
        normalized_words.append(w_norm)

    return normalized_words, ref_type
