"""
Real Demo Samples Provider.
Serves real recordings from data/injected/ and data/self_recordings/ across all 5 quality levels.
All transcripts are dynamically resolved from data/manifests/real_speech_manifest.json (single source of truth).
"""

import json
import os
from typing import Any

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cached_results")
MANIFESTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "manifests")
SELF_REC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "self_recordings")


def get_canonical_speech_transcripts() -> dict[str, str]:
    """Loads canonical transcripts from real_speech_manifest.json as single source of truth."""
    manifest_path = os.path.join(MANIFESTS_DIR, "real_speech_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            speeches = json.load(f)
            return {s["speech_id"]: s.get("transcript", "") for s in speeches}
    return {}


# Curated catalog of real speeches and injected gradient recordings
DEMO_CATALOG_BASE: list[dict[str, Any]] = [
    {
        "sample_id": "jfk_moon_1962_level_4",
        "speech_id": "jfk_moon_1962",
        "title": "JFK Moon Speech — Level 4 (Pristine Reference)",
        "speech_name": "John F. Kennedy — Rice Stadium Space Address (1962)",
        "quality_level": 4,
        "quality_label": "Level 4: Pristine Master",
        "speaker_name": "John F. Kennedy",
        "duration_s": 70.0,
        "description": "Original historical master recording. Canonical prosodic dynamics, optimal cadence.",
        "flaws_count": 0,
        "audio_url": "/api/audio/jfk_moon_1962_level_4.wav",
    },
    {
        "sample_id": "jfk_moon_1962_level_3",
        "speech_id": "jfk_moon_1962",
        "title": "JFK Moon Speech — Level 3 (Near Perfect)",
        "speech_name": "John F. Kennedy — Rice Stadium Space Address (1962)",
        "quality_level": 3,
        "quality_label": "Level 3: Near Perfect",
        "speaker_name": "John F. Kennedy",
        "duration_s": 70.0,
        "description": "Subtle pitch compression (-35%). Perceptually near-flawless, falls beneath detection threshold.",
        "flaws_count": 1,
        "audio_url": "/api/audio/jfk_moon_1962_level_3.wav",
    },
    {
        "sample_id": "jfk_moon_1962_level_2",
        "speech_id": "jfk_moon_1962",
        "title": "JFK Moon Speech — Level 2 (Slightly Flawed)",
        "speech_name": "John F. Kennedy — Rice Stadium Space Address (1962)",
        "quality_level": 2,
        "quality_label": "Level 2: Slightly Flawed",
        "speaker_name": "John F. Kennedy",
        "duration_s": 69.6,
        "description": "Noticeable tempo surge (+25% rushed) and pitch compression (-60%).",
        "flaws_count": 2,
        "audio_url": "/api/audio/jfk_moon_1962_level_2.wav",
    },
    {
        "sample_id": "jfk_moon_1962_level_1",
        "speech_id": "jfk_moon_1962",
        "title": "JFK Moon Speech — Level 1 (Flawed)",
        "speech_name": "John F. Kennedy — Rice Stadium Space Address (1962)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "John F. Kennedy",
        "duration_s": 70.4,
        "description": "Distinct flaws: monotone pitch collapse (-80%), rushed climax, and unnatural pause insertion.",
        "flaws_count": 3,
        "audio_url": "/api/audio/jfk_moon_1962_level_1.wav",
    },
    {
        "sample_id": "jfk_moon_1962_level_0",
        "speech_id": "jfk_moon_1962",
        "title": "JFK Moon Speech — Level 0 (Egregiously Wrong)",
        "speech_name": "John F. Kennedy — Rice Stadium Space Address (1962)",
        "quality_level": 0,
        "quality_label": "Level 0: Egregious",
        "speaker_name": "John F. Kennedy",
        "duration_s": 74.7,
        "description": "Severe multi-tier failure: near-robotic flatline pitch, erratic tempo surges, drag pauses.",
        "flaws_count": 4,
        "audio_url": "/api/audio/jfk_moon_1962_level_0.wav",
    },
    {
        "sample_id": "reagan_challenger_1986_level_1",
        "speech_id": "reagan_challenger_1986",
        "title": "Reagan Challenger Address — Level 1 (Flawed)",
        "speech_name": "Ronald Reagan — Shuttle Challenger Address (1986)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "Ronald Reagan",
        "duration_s": 63.0,
        "description": "Multi-tier injected prosodic flaws: rushed pacing and unnatural phrase hesitations.",
        "flaws_count": 3,
        "audio_url": "/api/audio/reagan_challenger_1986_level_1.wav",
    },
    {
        "sample_id": "fdr_fear_itself_1933_level_1",
        "speech_id": "fdr_fear_itself_1933",
        "title": "FDR Inaugural Address — Level 1 (Flawed) [Held-out]",
        "speech_name": "Franklin D. Roosevelt — First Inaugural Address (1933)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "Franklin D. Roosevelt",
        "duration_s": 48.5,
        "description": "Held-out speaker validation slice. Acoustic vintage audio with injected prosodic flaws.",
        "flaws_count": 3,
        "audio_url": "/api/audio/fdr_fear_itself_1933_level_1.wav",
    },
    {
        "sample_id": "reagan_mourning_1986_level_1",
        "speech_id": "reagan_mourning_1986",
        "title": "Reagan Memorial Opening — Level 1 (Flawed)",
        "speech_name": "Ronald Reagan — Day of Mourning Opening (1986)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "Ronald Reagan",
        "duration_s": 52.5,
        "description": "Injected prosodic degradation on solemn address: rushed tempo and flat pitch contour.",
        "flaws_count": 3,
        "audio_url": "/api/audio/reagan_mourning_1986_level_1.wav",
    },
    {
        "sample_id": "jfk_we_choose_1962_level_1",
        "speech_id": "jfk_we_choose_1962",
        "title": "JFK We Choose — Level 1 (Flawed)",
        "speech_name": "John F. Kennedy — Rice Stadium We Choose Excerpt (1962)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "John F. Kennedy",
        "duration_s": 60.0,
        "description": "Contrastive grounding on famous rhetorical climax with injected timing and pitch anomalies.",
        "flaws_count": 3,
        "audio_url": "/api/audio/jfk_we_choose_1962_level_1.wav",
    },
]

REFERENCE_SPEECHES_BASE: list[dict[str, Any]] = [
    {
        "reference_id": "jfk_moon_1962_level_4",
        "speech_id": "jfk_moon_1962",
        "name": "JFK Moon Speech (1962) — Level 4 Master",
        "speaker": "John F. Kennedy",
    },
    {
        "reference_id": "reagan_challenger_1986_level_4",
        "speech_id": "reagan_challenger_1986",
        "name": "Reagan Challenger Address (1986) — Level 4 Master",
        "speaker": "Ronald Reagan",
    },
    {
        "reference_id": "fdr_fear_itself_1933_level_4",
        "speech_id": "fdr_fear_itself_1933",
        "name": "FDR First Inaugural Address (1933) — Level 4 Master [Held-out]",
        "speaker": "Franklin D. Roosevelt",
    },
    {
        "reference_id": "reagan_mourning_1986_level_4",
        "speech_id": "reagan_mourning_1986",
        "name": "Reagan Memorial Opening (1986) — Level 4 Master",
        "speaker": "Ronald Reagan",
    },
    {
        "reference_id": "jfk_we_choose_1962_level_4",
        "speech_id": "jfk_we_choose_1962",
        "name": "JFK We Choose Excerpt (1962) — Level 4 Master",
        "speaker": "John F. Kennedy",
    },
]


def get_demo_samples() -> list[dict[str, Any]]:
    transcripts = get_canonical_speech_transcripts()
    catalog = []
    for item in DEMO_CATALOG_BASE:
        entry = dict(item)
        speech_id = entry.get("speech_id", "")
        entry["transcript"] = transcripts.get(speech_id, "")
        catalog.append(entry)

    # Dynamically include any real files in data/self_recordings/
    if os.path.exists(SELF_REC_DIR):
        for f in os.listdir(SELF_REC_DIR):
            if f.endswith(".wav"):
                base_name = os.path.splitext(f)[0]
                catalog.append({
                    "sample_id": base_name,
                    "speech_id": "self_recording",
                    "title": f"User Recording: {base_name}",
                    "speech_name": "Self-Recording Out-Of-Distribution",
                    "quality_level": 2,
                    "quality_label": "User Recording",
                    "speaker_name": "Participant",
                    "duration_s": 30.0,
                    "description": "User self-recording evaluated contrastively against master reference take.",
                    "flaws_count": 0,
                    "audio_url": f"/api/audio/{f}",
                    "transcript": "",
                })
    return catalog


def get_cached_result_by_id(sample_id: str) -> dict[str, Any] | None:
    """Loads pre-cached result JSON from data/cached_results/."""
    for candidate in [f"{sample_id}.json", f"self_recording_{sample_id}.json"]:
        path = os.path.join(SAMPLES_DIR, candidate)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return None


def get_reference_speeches() -> list[dict[str, Any]]:
    transcripts = get_canonical_speech_transcripts()
    refs = []
    for item in REFERENCE_SPEECHES_BASE:
        entry = dict(item)
        speech_id = entry.get("speech_id", "")
        entry["transcript"] = transcripts.get(speech_id, "")
        refs.append(entry)
    return refs
