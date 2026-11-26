"""Tests for scripts/export_static_demo.py (static read-only dashboard export)."""

import importlib.util
import json
from pathlib import Path

import backend.app.main as main

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("export_static_demo", ROOT / "scripts" / "export_static_demo.py")
export_static_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_static_demo)


def test_export_writes_backend_responses_and_skips_self_recordings(tmp_path: Path, monkeypatch):
    real_samples = main.get_demo_samples()
    fake_self = {
        "sample_id": "participant_take", "speech_id": "self_recording", "title": "User Recording",
        "speech_name": "x", "quality_level": 2, "quality_label": "x", "speaker_name": "Participant",
        "duration_s": 1.0, "description": "x", "flaws_count": 0, "audio_url": "/api/audio/participant_take.wav",
        "transcript": "",
    }
    monkeypatch.setattr(main, "get_demo_samples", lambda: real_samples + [fake_self])

    summary = export_static_demo.export(tmp_path, include_audio=False)

    samples = json.loads((tmp_path / "api" / "samples.json").read_text())
    assert all(s["sample_id"] != "participant_take" for s in samples)
    assert not (tmp_path / "api" / "results" / "participant_take.json").exists()
    assert len(samples) == len(real_samples)

    benchmark = json.loads((tmp_path / "api" / "benchmark.json").read_text())
    committed = json.loads((ROOT / "results" / "benchmark.json").read_text())
    assert benchmark == committed

    assert summary["results_exported"] == 75
    assert not summary["results_missing"]
    result = json.loads((tmp_path / "api" / "results" / "jfk_moon_1962_level_1.json").read_text())
    assert result["flaws"] and "ground_truth_eval" in result
