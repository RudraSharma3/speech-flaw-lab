"""Unit tests for dataset_tools.fetch_dataset.extract_and_restore (archive handling only).

The archive here is a tiny placeholder zip built in tmp_path to exercise the file-handling
logic (hash checks, path-traversal guard, reference restore). It is never used as evaluation data.
"""

import hashlib
import json
import zipfile
from pathlib import Path

from dataset_tools.fetch_dataset import extract_and_restore


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _make_data_dir(tmp_path: Path, files: dict[str, bytes]) -> Path:
    data = tmp_path / "data"
    (data / "manifests").mkdir(parents=True)
    manifest = [{"audio": {"file": n, "sha256": _sha(b)}} for n, b in files.items()]
    (data / "manifests" / "dataset_manifest_v1.json").write_text(json.dumps(manifest))
    speeches = [{"speech_id": "spk_a", "processed_file": "spk_a_excerpt.wav"}]
    (data / "manifests" / "real_speech_manifest.json").write_text(json.dumps(speeches))
    return data


def _make_zip(tmp_path: Path, files: dict[str, bytes], prefix: str = "audio/") -> Path:
    zp = tmp_path / "bench.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        for n, b in files.items():
            zf.writestr(prefix + n, b)
    return zp


def test_extract_restores_reference_from_identical_level4(tmp_path: Path):
    ref = b"RIFF-level4-bytes"
    files = {
        "spk_a_level_4.wav": ref,
        "spk_a_level_4_s1.wav": ref,
        "spk_a_level_4_s2.wav": ref,
        "spk_a_level_0.wav": b"RIFF-level0",
    }
    data = _make_data_dir(tmp_path, files)
    assert extract_and_restore(_make_zip(tmp_path, files), data_dir=data)
    assert (data / "processed" / "spk_a_excerpt.wav").read_bytes() == ref
    assert (data / "injected" / "spk_a_level_0.wav").read_bytes() == b"RIFF-level0"


def test_extract_fails_on_hash_mismatch(tmp_path: Path):
    good = {"spk_a_level_4.wav": b"a", "spk_a_level_4_s1.wav": b"a", "spk_a_level_4_s2.wav": b"a"}
    data = _make_data_dir(tmp_path, good)
    tampered = dict(good, **{"spk_a_level_4_s1.wav": b"tampered"})
    assert not extract_and_restore(_make_zip(tmp_path, tampered), data_dir=data)


def test_extract_ignores_directories_in_member_names(tmp_path: Path):
    files = {"spk_a_level_4.wav": b"a", "spk_a_level_4_s1.wav": b"a", "spk_a_level_4_s2.wav": b"a"}
    data = _make_data_dir(tmp_path, files)
    zp = tmp_path / "bench.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        for n, b in files.items():
            zf.writestr("audio/../../" + n, b)
    assert extract_and_restore(zp, data_dir=data)
    assert not (tmp_path / "spk_a_level_4.wav").exists()
    assert (data / "injected" / "spk_a_level_4.wav").exists()
