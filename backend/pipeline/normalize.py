"""
Speaker normalization and robust statistical deviation module.
Computes Median Absolute Deviation (MAD) robust z-scores against baseline reference or population priors.
"""

import json
import os
import re
from typing import Any

import numpy as np

POP_NORMS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "population_norms", "librispeech_priors.json"
)

DEFAULT_POPULATION_PRIORS = {
    "f0_range_st": {"median": 5.4, "mad": 1.4},
    "articulation_rate": {"median": 4.2, "mad": 0.8},
    "energy_contrast_db": {"median": 6.8, "mad": 1.9},
    "hnr_mean_db": {"median": 18.2, "mad": 2.6},
    "unpunctuated_pause_s": {"median": 0.05, "mad": 0.04},
    "punctuated_pause_s": {"median": 0.52, "mad": 0.16},
}


def load_population_priors() -> dict[str, Any]:
    if os.path.exists(POP_NORMS_PATH):
        try:
            with open(POP_NORMS_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return DEFAULT_POPULATION_PRIORS
    return DEFAULT_POPULATION_PRIORS


def compute_robust_z(val: float, median: float, mad: float, eps: float = 1e-6) -> float:
    """Computes robust z-score: z = (x - median) / (1.4826 * MAD)."""
    scale = 1.4826 * max(mad, eps)
    return float((val - median) / scale)


def calculate_baseline_distribution(
    baseline_words: list[dict[str, Any]]
) -> dict[str, tuple[float, float]]:
    """
    Computes (median, MAD) for each feature across a baseline take's words.
    """
    feats = ["f0_range_st", "articulation_rate", "energy_mean_db", "hnr_mean_db"]
    dist = {}

    for f in feats:
        vals = [w[f] for w in baseline_words if f in w and w[f] is not None]
        if len(vals) > 0:
            arr = np.array(vals, dtype=np.float64)
            med = float(np.median(arr))
            mad = float(np.median(np.abs(arr - med)))
            dist[f] = (med, max(mad, 0.1))
        else:
            priors = DEFAULT_POPULATION_PRIORS.get(f, {"median": 0.0, "mad": 1.0})
            dist[f] = (priors["median"], priors["mad"])

    return dist


def normalize_words_against_baseline(
    observed_words: list[dict[str, Any]],
    baseline_words: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], str]:
    """
    Performs per-word deviation on a word-index axis.
    Uses exact word correspondence from forced alignment when baseline is available,
    falling back to population priors when no ideal reference take is supplied.
    """
    has_ideal = False
    aligned_baseline: list[dict[str, Any] | None] = []

    if baseline_words is not None and len(baseline_words) > 0:
        if len(baseline_words) == len(observed_words):
            aligned_baseline = list(baseline_words)
            has_ideal = True
        else:
            # Subsequence matching to align observed words to baseline words
            obs_texts = [re.sub(r'[^a-z0-9]', '', w.get("text", "").lower()) for w in observed_words]
            base_texts = [re.sub(r'[^a-z0-9]', '', w.get("text", "").lower()) for w in baseline_words]
            best_offset = 0
            best_matches = -1
            max_search = max(1, len(base_texts) - len(obs_texts) + 1)
            for offset in range(max_search):
                matches = sum(1 for j, ot in enumerate(obs_texts) if offset + j < len(base_texts) and base_texts[offset + j] == ot)
                if matches > best_matches:
                    best_matches = matches
                    best_offset = offset
            if best_matches >= max(1, int(len(obs_texts) * 0.4)):
                aligned_baseline = [
                    baseline_words[best_offset + j] if (best_offset + j < len(baseline_words)) else None
                    for j in range(len(obs_texts))
                ]
                has_ideal = True

    ref_type = "ideal_take" if has_ideal else "population_prior"
    base_dist = calculate_baseline_distribution([b for b in aligned_baseline if b is not None]) if has_ideal else {}
    priors = load_population_priors()

    normalized_words = []

    for i, w in enumerate(observed_words):
        w_norm = dict(w)
        z_dict = {}

        b_w = aligned_baseline[i] if (has_ideal and i < len(aligned_baseline)) else None
        if has_ideal and b_w is not None:
            
            # F0 range deviation and range ratio vs baseline window
            f0_r = w.get("f0_range_st")
            b_f0_r = b_w.get("f0_range_st")
            if f0_r is not None and b_f0_r is not None:
                f0_mad = base_dist.get("f0_range_st", (5.4, 1.4))[1]
                z_range = compute_robust_z(f0_r - b_f0_r, 0.0, f0_mad)
                z_dict["f0_range_st_z"] = z_range
                w_norm["f0_range_ratio"] = float(f0_r / max(b_f0_r, 0.5))
            else:
                z_dict["f0_range_st_z"] = 0.0
                w_norm["f0_range_ratio"] = 1.0

            # Articulation rate deviation vs baseline word
            rate = w.get("articulation_rate", 4.2)
            b_rate = b_w.get("articulation_rate", 4.2)
            rate_mad = base_dist.get("articulation_rate", (4.3, 1.0))[1]
            z_dict["rate_syllables_per_sec_z"] = compute_robust_z(rate - b_rate, 0.0, rate_mad)

            # Energy deviation
            e = w.get("energy_mean_db", 0.0)
            b_e = b_w.get("energy_mean_db", 0.0)
            e_mad = base_dist.get("energy_mean_db", (0.0, 2.5))[1]
            z_dict["intensity_db_z"] = compute_robust_z(e - b_e, 0.0, e_mad)

            # HNR deviation
            hnr = w.get("hnr_mean_db", 18.0)
            b_hnr = b_w.get("hnr_mean_db", 18.0)
            hnr_mad = base_dist.get("hnr_mean_db", (18.0, 3.0))[1]
            z_dict["hnr_mean_db_z"] = compute_robust_z(hnr - b_hnr, 0.0, hnr_mad)

            # Pause deviations
            p_after = w.get("pause_after_s", 0.0)
            b_p_after = b_w.get("pause_after_s", 0.0)
            p_mad = 0.20
            z_dict["pause_after_z"] = compute_robust_z(p_after - b_p_after, 0.0, p_mad)

        else:
            # Fallback to population priors with calibrated wide bands (accommodating diverse oratorical styles)
            f0_r = w.get("f0_range_st")
            if f0_r is not None:
                f0_p = priors["f0_range_st"]
                z_dict["f0_range_st_z"] = compute_robust_z(f0_r, f0_p["median"], 4.5)
            else:
                z_dict["f0_range_st_z"] = 0.0

            rate_p = priors["articulation_rate"]
            z_dict["rate_syllables_per_sec_z"] = compute_robust_z(
                w["articulation_rate"], rate_p["median"], 1.6
            )

            z_dict["intensity_db_z"] = compute_robust_z(w["energy_mean_db"], 0.0, 4.0)
            
            # In reference-free mode, normalize HNR relative to recording's own median HNR
            rec_hnrs = [item["hnr_mean_db"] for item in observed_words if item.get("hnr_mean_db") is not None]
            rec_med_hnr = float(np.median(rec_hnrs)) if rec_hnrs else 18.0
            z_dict["hnr_mean_db_z"] = compute_robust_z(w["hnr_mean_db"], rec_med_hnr, 6.0)

            p_after = w["pause_after_s"]
            has_p = w.get("has_punctuation", False)
            prior_key = "punctuated_pause_s" if has_p else "unpunctuated_pause_s"
            p_prior = priors[prior_key]
            # Use wider tolerance for natural oratorical pauses
            mad_pause = 0.50 if not has_p else 0.35
            z_dict["pause_after_z"] = compute_robust_z(p_after, p_prior["median"], mad_pause)

        # Round z-scores
        w_norm["z_by_feature"] = {k: round(v, 2) for k, v in z_dict.items()}
        normalized_words.append(w_norm)

    return normalized_words, ref_type
