"""
Audio ingestion, normalization, and quality validation module.
Enforces canonical 16 kHz mono WAV 16-bit format, LUFS normalization, and clipping checks.
"""

import glob
import hashlib
import io
import os
import shutil
import subprocess
from typing import Any

import librosa
import numpy as np
import pyloudnorm as pyln
import soundfile as sf
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "thresholds.yaml")


def find_ffmpeg_executable() -> str:
    """
    Locates FFmpeg on Windows, Linux, or macOS.
    Checks:
    1. System PATH via shutil.which('ffmpeg')
    2. Bundled imageio-ffmpeg binary (with alias fallback)
    3. Common Windows installation directories (winget / Gyan.FFmpeg / scoop / chocolatey)
    Configures PATH so that external sub-libraries can invoke ffmpeg directly.
    Raises RuntimeError with actionable installation instructions if not found.
    """
    # 1. System PATH
    cmd = shutil.which("ffmpeg")
    if cmd:
        return cmd

    # 2. imageio-ffmpeg bundled binary
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            exe_dir = os.path.dirname(exe)
            alias_path = os.path.join(exe_dir, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            if not os.path.exists(alias_path):
                try:
                    shutil.copy2(exe, alias_path)
                except Exception:
                    pass
            if exe_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = exe_dir + os.pathsep + os.environ.get("PATH", "")
            final_bin = alias_path if os.path.exists(alias_path) else exe
            return final_bin
    except Exception:
        pass

    # 3. Common Windows winget / chocolatey / scoop paths
    if os.name == "nt":
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-*\bin\ffmpeg.exe"),
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
        ]
        for pat in candidates:
            matches = glob.glob(pat)
            if matches and os.path.exists(matches[0]):
                bin_dir = os.path.dirname(matches[0])
                if bin_dir not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
                return matches[0]

    raise RuntimeError(
        "FFmpeg is required for processing compressed audio formats (M4A, MP3, AAC), but was not found.\n"
        "Please install FFmpeg:\n"
        "  - On Windows: run 'winget install Gyan.FFmpeg' or install 'pip install imageio-ffmpeg'\n"
        "  - On Linux: run 'sudo apt-get install ffmpeg'\n"
        "  - On macOS: run 'brew install ffmpeg'"
    )


import tempfile


def decode_compressed_audio(audio_source: bytes | str, target_sr: int = 16000) -> tuple[np.ndarray, int]:
    """
    Decodes compressed audio (M4A, MP3, AAC, OGG) via FFmpeg to 16kHz float32 PCM.
    Uses seekable temp file for container formats requiring seekability (e.g. M4A/MP4).
    """
    ffmpeg_exe = find_ffmpeg_executable()
    temp_file = None
    if isinstance(audio_source, str) and os.path.exists(audio_source):
        in_path = audio_source
    else:
        temp_file = tempfile.NamedTemporaryFile(suffix=".audio", delete=False)
        temp_file.write(audio_source)
        temp_file.close()
        in_path = temp_file.name

    try:
        proc = subprocess.Popen(
            [
                ffmpeg_exe,
                "-y",
                "-i", in_path,
                "-f", "f32le",
                "-ac", "1",
                "-ar", str(target_sr),
                "pipe:1",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = proc.communicate()
        if proc.returncode != 0 or len(out) == 0:
            err_msg = err.decode("utf-8", errors="ignore")[:300]
            raise ValueError(f"FFmpeg failed to decode audio: {err_msg}")
        audio = np.frombuffer(out, dtype=np.float32)
        return audio, target_sr
    finally:
        if temp_file is not None and os.path.exists(temp_file.name):
            try:
                os.remove(temp_file.name)
            except Exception:
                pass


def load_audio_config() -> dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f).get("audio", {})
    return {
        "canonical_sample_rate": 16000,
        "channels": 1,
        "target_lufs": -20.0,
        "clipping_threshold_dbfs": -0.5,
        "min_audio_duration_s": 3.0,
        "max_audio_duration_s": 300.0,
    }


def compute_sha256(audio_bytes: bytes) -> str:
    return hashlib.sha256(audio_bytes).hexdigest()


def load_and_preprocess_audio(
    audio_source: Any, target_sr: int = 16000, target_lufs: float = -20.0
) -> tuple[np.ndarray, int, str, dict[str, Any]]:
    """
    Loads any input audio (bytes, file-like, or path), converts to mono,
    resamples to 16kHz, performs BS.1770 LUFS loudness normalization,
    and returns (audio_array, sample_rate, sha256_hash, metadata_dict).
    Supports WAV, MP3, M4A, FLAC, OGG.
    """
    cfg = load_audio_config()
    target_sr = cfg.get("canonical_sample_rate", target_sr)
    target_lufs = cfg.get("target_lufs", target_lufs)

    if isinstance(audio_source, bytes):
        raw_bytes = audio_source
    elif isinstance(audio_source, str) and os.path.exists(audio_source):
        with open(audio_source, "rb") as f:
            raw_bytes = f.read()
    else:
        # File-like object
        raw_bytes = audio_source.read()

    sha256_hash = compute_sha256(raw_bytes)

    # Attempt fast standard soundfile decoding
    bio = io.BytesIO(raw_bytes)
    try:
        y, sr = sf.read(bio)
    except Exception:
        # Fallback to direct FFmpeg pipe decoding (handles M4A, MP3, AAC, etc.)
        try:
            y, sr = decode_compressed_audio(raw_bytes, target_sr=target_sr)
        except Exception as ffmpeg_err:
            # Fallback to librosa/audioread
            try:
                bio.seek(0)
                y, sr = librosa.load(bio, sr=target_sr)
            except Exception as librosa_err:
                raise ValueError(
                    f"Failed to decode audio file. Neither SoundFile, FFmpeg, nor Librosa could parse it: {ffmpeg_err}"
                ) from librosa_err

    # Convert to mono if multi-channel (handles stereo/surround)
    if y.ndim > 1:
        if y.shape[0] <= 8 and y.shape[1] > y.shape[0]:
            y = np.mean(y, axis=0)
        else:
            y = np.mean(y, axis=1)

    # Remove DC bias/offset
    y = y - np.mean(y)

    # Silence check: reject silent files
    rms = float(np.sqrt(np.mean(y**2)))
    if rms < 1e-4:
        raise ValueError("Audio is completely silent (RMS < 1e-4). Cannot extract speech contours or perform alignment.")

    # Resample to 16kHz if necessary
    if sr != target_sr:
        y = librosa.resample(y.astype(np.float32), orig_sr=sr, target_sr=target_sr)
        sr = target_sr

    duration_s = float(len(y)) / sr

    # Max duration check: reject files > max_audio_duration_s (e.g. 10-minute files)
    max_dur = cfg.get("max_audio_duration_s", 300.0)
    if duration_s > max_dur:
        raise ValueError(
            f"Audio duration {duration_s:.1f}s exceeds maximum allowed duration ({max_dur:.0f}s / 5 minutes). "
            f"Please trim audio before analysis."
        )

    # Quality metrics: clipping detection
    clipping_thresh = 10.0 ** (cfg.get("clipping_threshold_dbfs", -0.5) / 20.0)
    clipping_count = np.sum(np.abs(y) >= clipping_thresh)
    clipping_fraction = float(clipping_count) / max(len(y), 1)

    # LUFS Loudness normalization
    meter = pyln.Meter(sr)
    try:
        current_lufs = meter.integrated_loudness(y)
        if not np.isinf(current_lufs) and not np.isnan(current_lufs):
            y_norm = pyln.normalize.loudness(y, current_lufs, target_lufs)
            # Peak preventer to avoid hard digital clipping
            peak = np.max(np.abs(y_norm))
            if peak > 0.99:
                y_norm = y_norm / peak * 0.99
            y = y_norm
        else:
            current_lufs = -30.0
    except Exception:
        # Fallback to peak/RMS scaling if loudness meter fails on very short audio
        current_lufs = -20.0
        peak = np.max(np.abs(y))
        if peak > 0:
            y = y / peak * 0.85

    meta = {
        "duration_s": round(duration_s, 3),
        "sample_rate": sr,
        "initial_lufs": round(float(current_lufs), 2),
        "clipping_fraction": round(clipping_fraction, 4),
        "num_samples": len(y),
    }

    return y.astype(np.float32), sr, sha256_hash, meta


def save_canonical_wav(audio_arr: np.ndarray, sr: int, output_path: str) -> str:
    """Saves normalized 16-bit 16kHz mono WAV to output_path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Scale float32 in [-1, 1] to int16
    int16_arr = np.clip(audio_arr * 32767.0, -32768, 32767).astype(np.int16)
    sf.write(output_path, int16_arr, sr, subtype="PCM_16")
    return output_path
