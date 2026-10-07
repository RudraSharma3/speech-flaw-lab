"""
Structured Causal Explainability Module.
Generates deterministic, template-interpolated explanations with mathematical rationale and severity weights.
Zero LLM dependencies in the scoring/explanation path.
"""

import os
import yaml
from typing import List, Dict, Any

RUBRIC_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "rubric.yaml")
FLAW_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "flaw_rules.yaml")


def load_flaw_rules() -> List[Dict[str, Any]]:
    if os.path.exists(FLAW_RULES_PATH):
        with open(FLAW_RULES_PATH, "r") as f:
            return yaml.safe_load(f).get("rules", [])
    return []


def load_severity_weights() -> Dict[str, float]:
    if os.path.exists(RUBRIC_PATH):
        with open(RUBRIC_PATH, "r") as f:
            return yaml.safe_load(f).get("severity_calculation", {}).get("type_weights", {})
    return {
        "monotone": 1.2,
        "rushed": 1.4,
        "drag_slow": 1.2,
        "inappropriate_pause": 1.6,
        "missing_pause": 1.3,
        "volume_drop": 1.1,
        "breathy_unclear": 1.0,
    }


def generate_causal_explanations(raw_grounded_flaws: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Interpolates statistical deltas into structured rationale and calculates severity.
    """
    type_weights = load_severity_weights()
    structured_flaws = []

    for raw in raw_grounded_flaws:
        rule = raw.get("rule", {})
        f_type = raw["flaw_type"]
        template = rule.get("rationale_template", "{flaw_type} detected: observed={observed} vs baseline={baseline}")
        why_it_hurts = rule.get("why_it_hurts", "Prosodic deviation degrades speech fluency and listener engagement.")

        dur = max(raw["end_s"] - raw["start_s"], 0.1)
        abs_z = abs(raw["z_score"])
        weight = type_weights.get(f_type, 1.0)
        severity = round(dur * abs_z * weight, 2)

        # Build template interpolation dict
        context = {
            "baseline": raw["baseline_value"],
            "observed": raw["observed_value"],
            "delta": raw["delta"],
            "z_score": raw["z_score"],
            "start_word_idx": raw["start_word_idx"],
            "end_word_idx": raw["end_word_idx"],
            "words": raw["words"],
            "word_before": raw.get("word_before", ""),
            "word_after": raw.get("word_after", ""),
            "punctuation": raw.get("punctuation", ""),
            "flaw_type": f_type,
        }

        try:
            rationale_text = template.format(**context)
        except Exception:
            rationale_text = (
                f"{f_type.replace('_', ' ').title()} deviation: observed {raw['observed_value']} {raw['unit']} "
                f"vs baseline {raw['baseline_value']} {raw['unit']} (z={raw['z_score']:+.1f})."
            )

        structured_flaws.append({
            "region_id": raw["flaw_id"],
            "start_s": raw["start_s"],
            "end_s": raw["end_s"],
            "start_word_idx": raw["start_word_idx"],
            "end_word_idx": raw["end_word_idx"],
            "words": raw["words"],
            "flaw_type": f_type,
            "feature": raw["feature"],
            "baseline_value": raw["baseline_value"],
            "observed_value": raw["observed_value"],
            "delta": raw["delta"],
            "unit": raw["unit"],
            "z_score": raw["z_score"],
            "severity": severity,
            "rationale_text": rationale_text,
            "why_it_hurts": why_it_hurts,
        })

    # Sort flaws by temporal start time
    structured_flaws.sort(key=lambda x: x["start_s"])
    return structured_flaws
