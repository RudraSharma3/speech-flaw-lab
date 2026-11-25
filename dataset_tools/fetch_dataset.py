"""
Dataset Fetch & Verification Tool for CSAD-2026 Benchmark Package.
Verifies the standalone dataset archive against the canonical SHA-256 checksum.

With --extract it also:
  1. extracts the 75 benchmark WAVs into data/injected/ (basename only, no path traversal),
  2. verifies every extracted WAV against data/manifests/dataset_manifest_v1.json,
  3. restores the 5 reference excerpts in data/processed/ that run_benchmark.py needs.

Why step 3 is valid: inject_flaws.py returns the processed excerpt unchanged for Level 4
and writes it with soundfile's default PCM_16 writer, exactly as extract_all_real_excerpts.py
wrote the excerpt. So <speech_id>_level_4.wav is byte-identical to data/processed/<processed_file>.
This is checked, not assumed: the three Level-4 seeds must hash identically, and the
tracked *_ideal alignments (computed on data/processed/) equal the *_level_4 alignments.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

EXPECTED_SHA256 = "4ba0eac057e013b14a97c2c2e99de5154834b9bdc5dbb7e527172e1871d64e6b"
EXPECTED_SIZE_BYTES = 119109722
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ZIP_PATH = ROOT_DIR / "dist" / "speech_prosody_benchmark_v1.zip"
DATA_DIR = ROOT_DIR / "data"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_dataset(zip_path: Path, expected_sha256: str = EXPECTED_SHA256) -> bool:
    print("=" * 80)
    print("DATASET ARCHIVE VERIFICATION (CSAD-2026)")
    print(f"Target Path : {zip_path}")
    print("=" * 80)

    if not zip_path.exists():
        print(f"[FAIL] Dataset archive not found at: {zip_path}")
        print("\nPlease download 'speech_prosody_benchmark_v1.zip' from the submission Drive link")
        print("and place it into the 'dist/' folder:")
        print("  1. Create 'dist/' directory: mkdir dist")
        print("  2. Place downloaded zip file: dist/speech_prosody_benchmark_v1.zip")
        print("  3. Re-run: python -m dataset_tools.fetch_dataset --verify")
        return False

    file_size = zip_path.stat().st_size
    print(f"File Size   : {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    print("Computing SHA-256 checksum...")
    actual_sha = compute_sha256(zip_path)
    print(f"Computed SHA: {actual_sha}")
    print(f"Expected SHA: {expected_sha256}")

    if actual_sha.lower() == expected_sha256.lower():
        print("\n[PASS] CHECKSUM VERIFIED: Archive matches canonical benchmark dataset bit-for-bit.")
        print("Dataset is authentic, intact, and ready for benchmark reproduction.")
        print("=" * 80)
        return True
    else:
        print("\n[FAIL] CHECKSUM MISMATCH:")
        print(f"  Expected: {expected_sha256}")
        print(f"  Actual  : {actual_sha}")
        print("The file may be corrupted or partially downloaded. Please re-download.")
        print("=" * 80)
        return False


def extract_and_restore(zip_path: Path, data_dir: Path = DATA_DIR) -> bool:
    """Extract benchmark WAVs, verify per-file SHA-256, restore reference excerpts.

    Returns True only if every file verifies. Never overwrites tracked JSON files.
    """
    injected_dir = data_dir / "injected"
    processed_dir = data_dir / "processed"
    manifests_dir = data_dir / "manifests"
    injected_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    with open(manifests_dir / "dataset_manifest_v1.json", encoding="utf-8") as f:
        expected = {e["audio"]["file"]: e["audio"]["sha256"] for e in json.load(f)}
    with open(manifests_dir / "real_speech_manifest.json", encoding="utf-8") as f:
        speeches = json.load(f)

    ok = True
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            name = os.path.basename(member)
            if not (member.startswith("audio/") and name.endswith(".wav")):
                continue
            if name not in expected:
                print(f"[FAIL] Unexpected audio file in archive: {member}")
                ok = False
                continue
            target = injected_dir / name
            with zf.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)

    for name, sha in sorted(expected.items()):
        target = injected_dir / name
        if not target.exists():
            print(f"[FAIL] Missing after extraction: {name}")
            ok = False
        elif compute_sha256(target) != sha:
            print(f"[FAIL] SHA-256 mismatch: {name}")
            ok = False
    print(f"[{'PASS' if ok else 'FAIL'}] Verified {len(expected)} benchmark WAVs against dataset_manifest_v1.json")

    for sp in speeches:
        sid = sp["speech_id"]
        seeds = [injected_dir / f"{sid}_level_4{suffix}.wav" for suffix in ("", "_s1", "_s2")]
        hashes = {compute_sha256(p) for p in seeds if p.exists()}
        if len(hashes) != 1 or not all(p.exists() for p in seeds):
            print(f"[FAIL] Level-4 seeds for {sid} are missing or not identical; cannot restore reference")
            ok = False
            continue
        dest = processed_dir / sp["processed_file"]
        shutil.copyfile(seeds[0], dest)
        print(f"[OK] Restored reference {dest.relative_to(data_dir.parent)} <- {seeds[0].name} (sha256 {hashes.pop()[:12]})")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify CSAD-2026 dataset archive integrity.")
    parser.add_argument("--verify", action="store_true", help="Verify SHA-256 checksum of downloaded dataset zip.")
    parser.add_argument("--extract", action="store_true",
                        help="After verifying, extract audio to data/injected/ and restore data/processed/ references.")
    parser.add_argument("--path", type=str, default=str(DEFAULT_ZIP_PATH), help="Custom path to dataset archive zip.")
    args = parser.parse_args()

    zip_file = Path(args.path)
    passed = verify_dataset(zip_file)
    if passed and args.extract:
        passed = extract_and_restore(zip_file)
    sys.exit(0 if passed else 1)
