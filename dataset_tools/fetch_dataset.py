"""
Dataset Fetch & Verification Tool for CSAD-2026 Benchmark Package.
Verifies the standalone dataset archive against the canonical SHA-256 checksum.
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path

EXPECTED_SHA256 = "4ba0eac057e013b14a97c2c2e99de5154834b9bdc5dbb7e527172e1871d64e6b"
EXPECTED_SIZE_BYTES = 119109722
DEFAULT_ZIP_PATH = Path(__file__).resolve().parent.parent / "dist" / "speech_prosody_benchmark_v1.zip"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_dataset(zip_path: Path) -> bool:
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
    print(f"Expected SHA: {EXPECTED_SHA256}")

    if actual_sha.lower() == EXPECTED_SHA256.lower():
        print("\n[PASS] CHECKSUM VERIFIED: Archive matches canonical benchmark dataset bit-for-bit.")
        print("Dataset is authentic, intact, and ready for benchmark reproduction.")
        print("=" * 80)
        return True
    else:
        print("\n[FAIL] CHECKSUM MISMATCH:")
        print(f"  Expected: {EXPECTED_SHA256}")
        print(f"  Actual  : {actual_sha}")
        print("The file may be corrupted or partially downloaded. Please re-download.")
        print("=" * 80)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify CSAD-2026 dataset archive integrity.")
    parser.add_argument("--verify", action="store_true", help="Verify SHA-256 checksum of downloaded dataset zip.")
    parser.add_argument("--path", type=str, default=str(DEFAULT_ZIP_PATH), help="Custom path to dataset archive zip.")
    args = parser.parse_args()

    zip_file = Path(args.path)
    if args.verify or True:
        passed = verify_dataset(zip_file)
        sys.exit(0 if passed else 1)
