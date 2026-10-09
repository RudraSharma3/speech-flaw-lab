"""
Dataset Packager & Manifest Generator with TextGrid export and SHA-256 verification.
"""

import hashlib
import json
import os
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
INJECTED_DIR = DATA_DIR / "injected"
ALIGNMENTS_DIR = DATA_DIR / "alignments"
MANIFESTS_DIR = DATA_DIR / "manifests"
TEXTGRIDS_DIR = DATA_DIR / "alignments" / "textgrids"
DIST_DIR = ROOT_DIR / "dist"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def json_to_textgrid(align_json_path: Path, tg_path: Path):
    with open(align_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    words = data.get("words", [])
    if not words:
        return

    total_dur = max(w["end"] for w in words)
    # Build non-overlapping intervals (including pauses)
    intervals = []
    current_time = 0.0

    for w in words:
        w_start = round(w["start"], 4)
        w_end = round(w["end"], 4)
        if w_start > current_time:
            # Silence / unlabelled interval
            intervals.append((current_time, w_start, ""))
        intervals.append((w_start, w_end, w["text"]))
        current_time = w_end

    if current_time < total_dur:
        intervals.append((current_time, total_dur, ""))

    lines = [
        'File type = "ooTextFile"',
        'Object class = "TextGrid"',
        "",
        "xmin = 0.0",
        f"xmax = {total_dur:.4f}",
        "tiers? <exists>",
        "size = 1",
        "item []:",
        '    item [1]:',
        '        class = "IntervalTier"',
        '        name = "words"',
        "        xmin = 0.0",
        f"        xmax = {total_dur:.4f}",
        f"        intervals: size = {len(intervals)}",
    ]

    for idx, (xmin, xmax, text) in enumerate(intervals, 1):
        lines.extend([
            f"        intervals [{idx}]:",
            f"            xmin = {xmin:.4f}",
            f"            xmax = {xmax:.4f}",
            f'            text = "{text}"',
        ])

    with open(tg_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def build_package():
    TEXTGRIDS_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Generate TextGrids for all alignments
    print("Generating TextGrids for JSON alignments...")
    tg_count = 0
    for align_file in ALIGNMENTS_DIR.glob("*_alignment.json"):
        rec_id = align_file.name.replace("_alignment.json", "")
        tg_out = TEXTGRIDS_DIR / f"{rec_id}.TextGrid"
        json_to_textgrid(align_file, tg_out)
        tg_count += 1
    print(f"Generated {tg_count} TextGrids in {TEXTGRIDS_DIR}")

    # 2. Build full dataset manifest with SHA-256 and injector profiles
    print("\nBuilding comprehensive dataset manifest...")
    raw_manifest_path = MANIFESTS_DIR / "injected_dataset_manifest.json"
    with open(raw_manifest_path, "r", encoding="utf-8") as f:
        base_manifest = json.load(f)

    packaged_entries = []
    for item in base_manifest:
        audio_path = INJECTED_DIR / item["audio_file"]
        flaws_path = INJECTED_DIR / item["annotation_file"]
        align_json = ALIGNMENTS_DIR / f"{item['recording_id']}_alignment.json"
        align_tg = TEXTGRIDS_DIR / f"{item['recording_id']}.TextGrid"

        # Load flaw annotations and injector parameters
        injector_params = []
        if flaws_path.exists():
            with open(flaws_path, "r", encoding="utf-8") as f:
                flaw_data = json.load(f)
            for fl in flaw_data.get("flaws", []):
                injector_params.append({
                    "flaw_type": fl.get("flaw_type"),
                    "start_s": fl.get("start_s"),
                    "end_s": fl.get("end_s"),
                    "words": fl.get("words"),
                    "profile": fl.get("profile", {}),
                })

        entry = {
            "recording_id": item["recording_id"],
            "speech_id": item["speech_id"],
            "speaker": item["speaker"],
            "quality_level": item["quality_level"],
            "level_name": item["level_name"],
            "seed": item["seed"],
            "duration_s": item["duration_s"],
            "flaw_count": item["flaw_count"],
            "audio": {
                "file": item["audio_file"],
                "sha256": compute_sha256(audio_path) if audio_path.exists() else None,
                "size_bytes": audio_path.stat().st_size if audio_path.exists() else 0,
            },
            "annotations": {
                "file": item["annotation_file"],
                "sha256": compute_sha256(flaws_path) if flaws_path.exists() else None,
                "size_bytes": flaws_path.stat().st_size if flaws_path.exists() else 0,
            },
            "alignment": {
                "json_file": align_json.name if align_json.exists() else None,
                "json_sha256": compute_sha256(align_json) if align_json.exists() else None,
                "textgrid_file": align_tg.name if align_tg.exists() else None,
                "textgrid_sha256": compute_sha256(align_tg) if align_tg.exists() else None,
            },
            "injector_flaw_parameters": injector_params,
        }
        packaged_entries.append(entry)

    out_manifest = MANIFESTS_DIR / "dataset_manifest_v1.json"
    with open(out_manifest, "w", encoding="utf-8") as f:
        json.dump(packaged_entries, f, indent=2)
    print(f"Saved complete package manifest to {out_manifest} ({len(packaged_entries)} entries)")

    # 3. Create ZIP archive
    zip_path = DIST_DIR / "speech_prosody_benchmark_v1.zip"
    print(f"\nCompressing package into {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Include manifest and splits
        zf.write(out_manifest, arcname="manifests/dataset_manifest_v1.json")
        zf.write(MANIFESTS_DIR / "splits.json", arcname="manifests/splits.json")
        zf.write(MANIFESTS_DIR / "sources_manifest.json", arcname="manifests/sources_manifest.json")

        # Include all 75 audio files and annotations
        for entry in packaged_entries:
            audio_f = INJECTED_DIR / entry["audio"]["file"]
            if audio_f.exists():
                zf.write(audio_f, arcname=f"audio/{entry['audio']['file']}")
            flaw_f = INJECTED_DIR / entry["annotations"]["file"]
            if flaw_f.exists():
                zf.write(flaw_f, arcname=f"annotations/{entry['annotations']['file']}")

            align_j = ALIGNMENTS_DIR / f"{entry['recording_id']}_alignment.json"
            if align_j.exists():
                zf.write(align_j, arcname=f"alignments/json/{align_j.name}")
            align_t = TEXTGRIDS_DIR / f"{entry['recording_id']}.TextGrid"
            if align_t.exists():
                zf.write(align_t, arcname=f"alignments/textgrids/{align_t.name}")

        # Include self_recordings README and instructions
        self_readme = DATA_DIR / "self_recordings" / "README.md"
        if self_readme.exists():
            zf.write(self_readme, arcname="self_recordings/README.md")

    zip_size = zip_path.stat().st_size
    zip_sha = compute_sha256(zip_path)
    print("\n" + "=" * 70)
    print("DATASET PACKAGE CREATION COMPLETE")
    print("=" * 70)
    print(f"Archive Path : {zip_path}")
    print(f"Archive Size : {zip_size:,} bytes ({zip_size / (1024*1024):.2f} MB)")
    print(f"Archive SHA256: {zip_sha}")
    print(f"Total Entries: {len(packaged_entries)} recordings")
    print("=" * 70)

    # Return metadata for docs
    return {
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_size,
        "zip_sha256": zip_sha,
        "entry_count": len(packaged_entries),
    }


if __name__ == "__main__":
    build_package()
