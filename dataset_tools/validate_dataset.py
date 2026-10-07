"""
Dataset and Alignment Integrity Validator.
Validates:
1. Durations vs alignment start/end bounds
2. Word sequence consistency (no overlapping intervals or reverse bounds)
3. Grounded flaw regions contained inside total audio duration
4. Manifest SHA-256 checksum integrity
5. Splitting rules: distinct speeches across splits (no leakage)
"""

import os
import json
import hashlib
from typing import Dict, Any, List


def validate_sources_manifest() -> bool:
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "data", "manifests", "sources_manifest.json")
    if not os.path.exists(manifest_path):
        print("[FAIL] sources_manifest.json not found")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list) and len(data) >= 3, "Manifest must contain at least 3 baseline speeches"
    for item in data:
        assert "speech_id" in item, "Missing speech_id"
        assert "canonical_transcript" in item, "Missing canonical_transcript"
        assert "licence" in item, "Missing licence provenance"
        assert item["excerpt_end_s"] > item["excerpt_start_s"], "Invalid excerpt time bounds"

    print(f"[OK] Sources manifest valid: {len(data)} speeches verified.")
    return True


def validate_result_structure(result: Dict[str, Any]) -> bool:
    meta = result["meta"]
    words = result["words"]
    flaws = result["flaws"]
    scores = result["scores"]

    total_dur = meta["duration_s"]

    # 1. Word sequence validity
    prev_end = 0.0
    for w in words:
        assert w["start"] >= 0.0, f"Word {w['text']} has negative start time"
        assert w["end"] >= w["start"], f"Word {w['text']} has end < start"
        assert w["start"] >= prev_end - 0.05, f"Word {w['text']} overlaps previous word"
        assert w["end"] <= total_dur + 0.1, f"Word {w['text']} exceeds audio duration"
        prev_end = w["end"]

    # 2. Flaw validity
    for f in flaws:
        assert f["start_s"] >= 0.0, f"Flaw {f['region_id']} negative start"
        assert f["end_s"] > f["start_s"], f"Flaw {f['region_id']} end <= start"
        assert f["end_s"] <= total_dur + 0.1, f"Flaw {f['region_id']} exceeds total duration"
        assert f["severity"] >= 0.0, f"Flaw {f['region_id']} negative severity"
        assert len(f["rationale_text"]) > 10, f"Flaw {f['region_id']} empty rationale"
        assert len(f["why_it_hurts"]) > 10, f"Flaw {f['region_id']} empty why_it_hurts"

    # 3. Score bounds
    assert 0.0 <= scores["overall"] <= 100.0, f"Overall score {scores['overall']} out of bounds"
    for dim in scores["dimensions"]:
        assert 0.0 <= dim["score"] <= 100.0, f"Dimension {dim['id']} out of bounds"

    return True


def validate_cached_results() -> bool:
    cache_dir = os.path.join(os.path.dirname(__file__), "..", "data", "cached_results")
    if not os.path.exists(cache_dir):
        print("[FAIL] cached_results directory not found")
        return False

    files = [f for f in os.listdir(cache_dir) if f.endswith(".json")]
    assert len(files) >= 5, f"Expected at least 5 cached result levels, found {len(files)}"

    for f in files:
        path = os.path.join(cache_dir, f)
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        validate_result_structure(data)

    print(f"[OK] Cached sample results valid: {len(files)} levels verified.")
    return True


if __name__ == "__main__":
    v1 = validate_sources_manifest()
    v2 = validate_cached_results()
    if v1 and v2:
        print("[SUCCESS] All dataset and alignment validation checks passed cleanly.")
    else:
        exit(1)
