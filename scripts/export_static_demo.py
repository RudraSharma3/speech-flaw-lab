"""
Export the dashboard's backend responses as static files for a read-only demo build.

Every file is produced by calling the real FastAPI routes in backend/app/main.py through
TestClient, so the static demo shows exactly what the live server returns. Nothing is computed
or edited here. Startup hooks are not run, so the MMS_FA aligner is never loaded.

Layout written under --out (matches frontend/src/lib/staticApi.ts):
  api/samples.json, api/references.json, api/benchmark.json
  api/results/<recording_id>.json
  audio/<recording_id>.wav          (only where the backend can serve the file)

Self-recordings are skipped unless --include-self-recordings is passed: real participant
voices must not be published without written consent.

Usage:
  python scripts/export_static_demo.py --out <dir>
  cd frontend && VITE_STATIC_DEMO=true npx vite build --outDir <dir>
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def export(out_dir: Path, include_self_recordings: bool = False, include_audio: bool = True) -> dict:
    from fastapi.testclient import TestClient

    import backend.app.main as backend_main

    client = TestClient(backend_main.app)  # not used as a context manager: startup hooks do not run
    api_dir = out_dir / "api"
    (api_dir / "results").mkdir(parents=True, exist_ok=True)
    (out_dir / "audio").mkdir(parents=True, exist_ok=True)

    def get_json(route: str):
        r = client.get(route)
        r.raise_for_status()
        return r.json()

    # The /samples response model drops speech_id, so identify participant recordings
    # from the backend's own catalog, which still carries it.
    self_recording_ids = {
        s["sample_id"] for s in backend_main.get_demo_samples() if s.get("speech_id") == "self_recording"
    }
    samples = [
        s for s in get_json("/samples")
        if include_self_recordings or s["sample_id"] not in self_recording_ids
    ]
    (api_dir / "samples.json").write_text(json.dumps(samples), encoding="utf-8")
    (api_dir / "references.json").write_text(json.dumps(get_json("/api/references")), encoding="utf-8")
    (api_dir / "benchmark.json").write_text(json.dumps(get_json("/api/benchmark")), encoding="utf-8")

    with open(ROOT / "data" / "manifests" / "injected_dataset_manifest.json", encoding="utf-8") as f:
        recording_ids = [r["recording_id"] for r in json.load(f)]
    for s in samples:
        if s["sample_id"] not in recording_ids:
            recording_ids.append(s["sample_id"])

    exported, audio_files, missing = [], [], []
    for rid in recording_ids:
        r = client.get(f"/results/{rid}")
        if r.status_code != 200:
            missing.append(rid)
            continue
        (api_dir / "results" / f"{rid}.json").write_text(r.text, encoding="utf-8")
        exported.append(rid)
        if include_audio:
            a = client.get(f"/api/audio/{rid}.wav")
            if a.status_code == 200:
                (out_dir / "audio" / f"{rid}.wav").write_bytes(a.content)
                audio_files.append(rid)

    summary = {
        "results_exported": len(exported),
        "audio_exported": len(audio_files),
        "results_missing": missing,
        "audio_missing": [rid for rid in exported if rid not in audio_files],
    }
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, type=Path, help="Output directory for the static demo files.")
    parser.add_argument("--include-self-recordings", action="store_true",
                        help="Also export participant self-recordings (only with written consent).")
    parser.add_argument("--no-audio", action="store_true", help="Export JSON only.")
    args = parser.parse_args()
    os.chdir(ROOT)
    result = export(args.out, args.include_self_recordings, include_audio=not args.no_audio)
    print(json.dumps({k: (v if isinstance(v, int) else f"{len(v)} ids") for k, v in result.items()}, indent=2))
    if result["audio_missing"]:
        print("No audio for:", ", ".join(result["audio_missing"][:10]), "..." if len(result["audio_missing"]) > 10 else "")
