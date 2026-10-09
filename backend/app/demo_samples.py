"""
Real Demo Samples Provider.
Serves real recordings from data/injected/ and data/self_recordings/ across all 5 quality levels.
Completely removes all mock data.
"""

import json
import os
from typing import Any

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cached_results")
MANIFESTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "manifests")
SELF_REC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "self_recordings")

# Curated catalog of real speeches and injected gradient recordings
DEMO_CATALOG: list[dict[str, Any]] = [
    {
        "sample_id": "jfk_moon_1962_level_4",
        "title": "JFK Moon Speech — Level 4 (Pristine Reference)",
        "speech_name": "John F. Kennedy — Rice Stadium Space Address (1962)",
        "quality_level": 4,
        "quality_label": "Level 4: Pristine Master",
        "speaker_name": "John F. Kennedy",
        "duration_s": 70.0,
        "description": "Original historical master recording. Canonical prosodic dynamics, optimal cadence.",
        "flaws_count": 0,
        "audio_url": "/api/audio/jfk_moon_1962_level_4.wav",
        "transcript": "140,000 miles away from the control station in Houston, a giant rocket, more than 300 feet tall, the length of this football field, made of new metal alloys, some of which have not yet been embedded, capable of standing heat and stresses, several times more than have ever been experienced, pitted together with a precision better than the finest watch, carrying all the equipment needed for propulsion, guidance, control, communication, food and survival, on an untried mission to an unknown celestial body and then return it safely to earth, re-entering the atmosphere at speeds of over 25,000 miles per hour, causing heat about half that on the temperature of the sun, almost as hot as it is here today and do all this and do all this and do it right and do it first, if all this thick heat is out, then we must be bald.",
    },
    {
        "sample_id": "jfk_moon_1962_level_3",
        "title": "JFK Moon Speech — Level 3 (Near Perfect)",
        "speech_name": "John F. Kennedy — Rice Stadium Space Address (1962)",
        "quality_level": 3,
        "quality_label": "Level 3: Near Perfect",
        "speaker_name": "John F. Kennedy",
        "duration_s": 70.0,
        "description": "Subtle pitch compression (-35%). Perceptually near-flawless, falls beneath detection threshold.",
        "flaws_count": 1,
        "audio_url": "/api/audio/jfk_moon_1962_level_3.wav",
        "transcript": "140,000 miles away from the control station in Houston, a giant rocket, more than 300 feet tall, the length of this football field, made of new metal alloys, some of which have not yet been embedded, capable of standing heat and stresses, several times more than have ever been experienced, pitted together with a precision better than the finest watch, carrying all the equipment needed for propulsion, guidance, control, communication, food and survival, on an untried mission to an unknown celestial body and then return it safely to earth, re-entering the atmosphere at speeds of over 25,000 miles per hour, causing heat about half that on the temperature of the sun, almost as hot as it is here today and do all this and do all this and do it right and do it first, if all this thick heat is out, then we must be bald.",
    },
    {
        "sample_id": "jfk_moon_1962_level_2",
        "title": "JFK Moon Speech — Level 2 (Slightly Flawed)",
        "speech_name": "John F. Kennedy — Rice Stadium Space Address (1962)",
        "quality_level": 2,
        "quality_label": "Level 2: Slightly Flawed",
        "speaker_name": "John F. Kennedy",
        "duration_s": 69.6,
        "description": "Noticeable tempo surge (+25% rushed) and pitch compression (-60%).",
        "flaws_count": 2,
        "audio_url": "/api/audio/jfk_moon_1962_level_2.wav",
        "transcript": "140,000 miles away from the control station in Houston, a giant rocket, more than 300 feet tall, the length of this football field, made of new metal alloys, some of which have not yet been embedded, capable of standing heat and stresses, several times more than have ever been experienced, pitted together with a precision better than the finest watch, carrying all the equipment needed for propulsion, guidance, control, communication, food and survival, on an untried mission to an unknown celestial body and then return it safely to earth, re-entering the atmosphere at speeds of over 25,000 miles per hour, causing heat about half that on the temperature of the sun, almost as hot as it is here today and do all this and do all this and do it right and do it first, if all this thick heat is out, then we must be bald.",
    },
    {
        "sample_id": "jfk_moon_1962_level_1",
        "title": "JFK Moon Speech — Level 1 (Flawed)",
        "speech_name": "John F. Kennedy — Rice Stadium Space Address (1962)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "John F. Kennedy",
        "duration_s": 70.4,
        "description": "Distinct flaws: monotone pitch collapse (-80%), rushed climax, and unnatural pause insertion.",
        "flaws_count": 3,
        "audio_url": "/api/audio/jfk_moon_1962_level_1.wav",
        "transcript": "140,000 miles away from the control station in Houston, a giant rocket, more than 300 feet tall, the length of this football field, made of new metal alloys, some of which have not yet been embedded, capable of standing heat and stresses, several times more than have ever been experienced, pitted together with a precision better than the finest watch, carrying all the equipment needed for propulsion, guidance, control, communication, food and survival, on an untried mission to an unknown celestial body and then return it safely to earth, re-entering the atmosphere at speeds of over 25,000 miles per hour, causing heat about half that on the temperature of the sun, almost as hot as it is here today and do all this and do all this and do it right and do it first, if all this thick heat is out, then we must be bald.",
    },
    {
        "sample_id": "jfk_moon_1962_level_0",
        "title": "JFK Moon Speech — Level 0 (Egregiously Wrong)",
        "speech_name": "John F. Kennedy — Rice Stadium Space Address (1962)",
        "quality_level": 0,
        "quality_label": "Level 0: Egregious",
        "speaker_name": "John F. Kennedy",
        "duration_s": 74.7,
        "description": "Severe multi-tier failure: near-robotic flatline pitch, erratic tempo surges, drag pauses.",
        "flaws_count": 4,
        "audio_url": "/api/audio/jfk_moon_1962_level_0.wav",
        "transcript": "140,000 miles away from the control station in Houston, a giant rocket, more than 300 feet tall, the length of this football field, made of new metal alloys, some of which have not yet been embedded, capable of standing heat and stresses, several times more than have ever been experienced, pitted together with a precision better than the finest watch, carrying all the equipment needed for propulsion, guidance, control, communication, food and survival, on an untried mission to an unknown celestial body and then return it safely to earth, re-entering the atmosphere at speeds of over 25,000 miles per hour, causing heat about half that on the temperature of the sun, almost as hot as it is here today and do all this and do all this and do it right and do it first, if all this thick heat is out, then we must be bald.",
    },
    {
        "sample_id": "reagan_challenger_1986_level_1",
        "title": "Reagan Challenger Address — Level 1 (Flawed)",
        "speech_name": "Ronald Reagan — Shuttle Challenger Address (1986)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "Ronald Reagan",
        "duration_s": 63.0,
        "description": "Multi-tier injected prosodic flaws: rushed pacing and unnatural phrase hesitations.",
        "flaws_count": 3,
        "audio_url": "/api/audio/reagan_challenger_1986_level_1.wav",
        "transcript": "and tell them, your dedication and professionalism have moved and impressed us for decades, and we know of your anguish. We share it.\" There's a coincidence today. On this day, 390 years ago, the great explorer Sir Francis Drake died aboard ship off the coast of Panama. In his lifetime, the great frontiers were the oceans, and a historian later said he lived by the sea, died on it, and was buried in it. Well, today, we can say of the challenger crew, their dedication was, like Drake's, complete. The crew of the space shuttle challenger honored us for the manner in which they lived their lives. We will never forget them, nor the last time we saw them this morning, as they prepared for their journey and waved goodbye, and slipped the surly bonds of earth to touch the face of God. Thank you.",
    },
    {
        "sample_id": "fdr_fear_itself_1933_level_1",
        "title": "FDR Inaugural Address — Level 1 (Flawed) [Held-out]",
        "speech_name": "Franklin D. Roosevelt — First Inaugural Address (1933)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "Franklin D. Roosevelt",
        "duration_s": 48.5,
        "description": "Held-out speaker validation slice. Acoustic vintage audio with injected prosodic flaws.",
        "flaws_count": 3,
        "audio_url": "/api/audio/fdr_fear_itself_1933_level_1.wav",
        "transcript": "Let me assert my firm belief, that the only thing we have to fear is fear itself, nameless, unreasoning, unjustified terror, which paralyzes needed efforts to convert retreat into advance. In every dark hour of our national life, a leadership of frankness and a fitter has met with that understanding and support of the people themselves, which is essential to victory. And I am convinced to show a game, give that support, to leadership, in these critical days.",
    },
    {
        "sample_id": "reagan_mourning_1986_level_1",
        "title": "Reagan Memorial Opening — Level 1 (Flawed)",
        "speech_name": "Ronald Reagan — Day of Mourning Opening (1986)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "Ronald Reagan",
        "duration_s": 52.5,
        "description": "Injected prosodic degradation on solemn address: rushed tempo and flat pitch contour.",
        "flaws_count": 3,
        "audio_url": "/api/audio/reagan_mourning_1986_level_1.wav",
        "transcript": "Ladies and gentlemen, I'd plan to speak to you tonight to report on the State of the Union, but the events of earlier today have led me to change those plans. Today is a day for morning and remembering. Nancy and I are paying to the core of the tragedy of the Shuttle Challenger. We know we share this pain with all of the people of our country. This is truly a national loss. Nineteen years ago, almost to the day, we lost three astronauts in a terrible accident on the ground. But we've never lost an astronaut in flight. We've never had a tragedy like this.",
    },
    {
        "sample_id": "jfk_we_choose_1962_level_1",
        "title": "JFK We Choose — Level 1 (Flawed)",
        "speech_name": "John F. Kennedy — Rice Stadium We Choose Excerpt (1962)",
        "quality_level": 1,
        "quality_label": "Level 1: Flawed",
        "speaker_name": "John F. Kennedy",
        "duration_s": 60.0,
        "description": "Contrastive grounding on famous rhetorical climax with injected timing and pitch anomalies.",
        "flaws_count": 3,
        "audio_url": "/api/audio/jfk_we_choose_1962_level_1.wav",
        "transcript": "We choose to go to the moon. We choose to go to the moon in this decade and do the other things, not because they are easy, but because they are hard, because that goal will serve to organize and measure the best of our energies and skills, because that challenge is one that we are willing to accept, one we are unwilling to postpone, and one which we intend to win, and the others, too.",
    },
]

# Canonical ideal references available for contrastive mode
REFERENCE_SPEECHES = [
    {
        "reference_id": "jfk_moon_1962_level_4",
        "name": "JFK Moon Speech (1962) — Level 4 Master",
        "speaker": "John F. Kennedy",
        "transcript": "140,000 miles away from the control station in Houston, a giant rocket, more than 300 feet tall, the length of this football field, made of new metal alloys, some of which have not yet been embedded, capable of standing heat and stresses, several times more than have ever been experienced, pitted together with a precision better than the finest watch, carrying all the equipment needed for propulsion, guidance, control, communication, food and survival, on an untried mission to an unknown celestial body and then return it safely to earth, re-entering the atmosphere at speeds of over 25,000 miles per hour, causing heat about half that on the temperature of the sun, almost as hot as it is here today and do all this and do all this and do it right and do it first, if all this thick heat is out, then we must be bald.",
    },
    {
        "reference_id": "reagan_challenger_1986_level_4",
        "name": "Reagan Challenger Address (1986) — Level 4 Master",
        "speaker": "Ronald Reagan",
        "transcript": "and tell them, your dedication and professionalism have moved and impressed us for decades, and we know of your anguish. We share it.\" There's a coincidence today. On this day, 390 years ago, the great explorer Sir Francis Drake died aboard ship off the coast of Panama. In his lifetime, the great frontiers were the oceans, and a historian later said he lived by the sea, died on it, and was buried in it. Well, today, we can say of the challenger crew, their dedication was, like Drake's, complete. The crew of the space shuttle challenger honored us for the manner in which they lived their lives. We will never forget them, nor the last time we saw them this morning, as they prepared for their journey and waved goodbye, and slipped the surly bonds of earth to touch the face of God. Thank you.",
    },
    {
        "reference_id": "fdr_fear_itself_1933_level_4",
        "name": "FDR First Inaugural Address (1933) — Level 4 Master [Held-out]",
        "speaker": "Franklin D. Roosevelt",
        "transcript": "Let me assert my firm belief, that the only thing we have to fear is fear itself, nameless, unreasoning, unjustified terror, which paralyzes needed efforts to convert retreat into advance. In every dark hour of our national life, a leadership of frankness and a fitter has met with that understanding and support of the people themselves, which is essential to victory. And I am convinced to show a game, give that support, to leadership, in these critical days.",
    },
    {
        "reference_id": "reagan_mourning_1986_level_4",
        "name": "Reagan Memorial Opening (1986) — Level 4 Master",
        "speaker": "Ronald Reagan",
        "transcript": "Ladies and gentlemen, I'd plan to speak to you tonight to report on the State of the Union, but the events of earlier today have led me to change those plans. Today is a day for morning and remembering. Nancy and I are paying to the core of the tragedy of the Shuttle Challenger. We know we share this pain with all of the people of our country. This is truly a national loss. Nineteen years ago, almost to the day, we lost three astronauts in a terrible accident on the ground. But we've never lost an astronaut in flight. We've never had a tragedy like this.",
    },
    {
        "reference_id": "jfk_we_choose_1962_level_4",
        "name": "JFK We Choose Excerpt (1962) — Level 4 Master",
        "speaker": "John F. Kennedy",
        "transcript": "We choose to go to the moon. We choose to go to the moon in this decade and do the other things, not because they are easy, but because they are hard, because that goal will serve to organize and measure the best of our energies and skills, because that challenge is one that we are willing to accept, one we are unwilling to postpone, and one which we intend to win, and the others, too.",
    },
]


def get_demo_samples() -> list[dict[str, Any]]:
    # Dynamically include any real files in data/self_recordings/
    catalog = list(DEMO_CATALOG)
    if os.path.exists(SELF_REC_DIR):
        for f in os.listdir(SELF_REC_DIR):
            if f.endswith(".wav"):
                base_name = os.path.splitext(f)[0]
                catalog.append({
                    "sample_id": base_name,
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
    return REFERENCE_SPEECHES
