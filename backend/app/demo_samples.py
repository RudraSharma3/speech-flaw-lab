"""
Pre-cached Demo Samples Provider.
Ensures hackathon demo recordings (levels 0-4) are pre-cached and cannot fail at demo time.
"""

import os
import json
from typing import List, Dict, Any, Optional

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cached_results")

DEMO_CATALOG: List[Dict[str, Any]] = [
    {
        "sample_id": "demo_jfk_moon_level4_ideal",
        "title": "JFK Moon Speech — Level 4 (Ideal Reference)",
        "speech_name": "John F. Kennedy — Rice Stadium Moon Address (1962)",
        "quality_level": 4,
        "quality_label": "Level 4: Pristine Master",
        "speaker_name": "John F. Kennedy",
        "duration_s": 17.5,
        "description": "Flawless canonical delivery, optimal rhythmic cadence, resonant pitch inflection, and dramatic rhetorical pauses.",
        "flaws_count": 0,
        "audio_url": "/api/audio/jfk_moon_level4_ideal.wav",
        "transcript": "We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .",
    },
    {
        "sample_id": "demo_jfk_moon_level3_near_perfect",
        "title": "JFK Moon Speech — Level 3 (Near Perfect)",
        "speech_name": "John F. Kennedy — Rice Stadium Moon Address (1962)",
        "quality_level": 3,
        "quality_label": "Level 3: Near Perfect",
        "speaker_name": "John F. Kennedy",
        "duration_s": 17.5,
        "description": "Mild prosodic imperfection with a subtle localized pitch compression on the second sentence.",
        "flaws_count": 1,
        "audio_url": "/api/audio/jfk_moon_level3_near_perfect.wav",
        "transcript": "We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .",
    },
    {
        "sample_id": "demo_jfk_moon_level2_slightly_flawed",
        "title": "JFK Moon Speech — Level 2 (Slightly Flawed)",
        "speech_name": "John F. Kennedy — Rice Stadium Moon Address (1962)",
        "quality_level": 2,
        "quality_label": "Level 2: Slightly Flawed",
        "speaker_name": "John F. Kennedy",
        "duration_s": 17.5,
        "description": "Noticeable pacing surge on the climax phrase combined with pitch flatness.",
        "flaws_count": 2,
        "audio_url": "/api/audio/jfk_moon_level2_slightly_flawed.wav",
        "transcript": "We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .",
    },
    {
        "sample_id": "demo_jfk_moon_level1_flawed",
        "title": "JFK Moon Speech — Level 1 (Flawed)",
        "speech_name": "John F. Kennedy — Rice Stadium Moon Address (1962)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "John F. Kennedy",
        "duration_s": 17.5,
        "description": "Multiple distinct flaws: severe monotone pitch collapse across 8 words, rushed tempo, and disruptive mid-phrase pause.",
        "flaws_count": 3,
        "audio_url": "/api/audio/jfk_moon_level1_flawed.wav",
        "transcript": "We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .",
    },
    {
        "sample_id": "demo_jfk_moon_level0_egregious",
        "title": "JFK Moon Speech — Level 0 (Egregiously Wrong)",
        "speech_name": "John F. Kennedy — Rice Stadium Moon Address (1962)",
        "quality_level": 0,
        "quality_label": "Level 0: Egregious",
        "speaker_name": "John F. Kennedy",
        "duration_s": 17.5,
        "description": "Multi-tier failure: near-flatline robotic pitch, erratic tempo shifts from dragging to rushing, and awkward pauses.",
        "flaws_count": 4,
        "audio_url": "/api/audio/jfk_moon_level0_egregious.wav",
        "transcript": "We choose to go to the moon . We choose to go to the moon in this decade and do the other things , not because they are easy , but because they are hard , because that goal will serve to organize and measure the best of our energies and skills .",
    },
]


def get_demo_samples() -> List[Dict[str, Any]]:
    return DEMO_CATALOG


def get_cached_result_by_id(sample_id: str) -> Optional[Dict[str, Any]]:
    """Loads pre-cached result JSON from data/cached_results/."""
    path = os.path.join(SAMPLES_DIR, f"{sample_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
