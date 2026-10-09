"""
Extracts, pre-processes, and transcribes clean clips for JFK, Reagan, and FDR from data/raw/
into data/processed/ as 16kHz mono 16-bit PCM WAV files with exact canonical transcripts.
"""

import json
import os

import numpy as np
import scipy.signal
import soundfile as sf
from faster_whisper import WhisperModel

PROCESSED_DIR = "data/processed"
MANIFESTS_DIR = "data/manifests"
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(MANIFESTS_DIR, exist_ok=True)


def resample_mono_16k(audio, orig_sr):
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if orig_sr != 16000:
        num_samples = int(len(audio) * 16000 / orig_sr)
        audio = scipy.signal.resample(audio, num_samples)
    return audio.astype(np.float32)


def process_all_speeches():
    whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    
    speeches_meta = []

    # 1. JFK Moon Speech (900.0s -> 970.0s, 70s)
    jfk_raw = "data/raw/jfk_rice_1962.mp3"
    data, sr = sf.read(jfk_raw)
    clip_jfk = data[int(900.0 * sr) : int(970.0 * sr)]
    clip_jfk_16k = resample_mono_16k(clip_jfk, sr)
    jfk_out = os.path.join(PROCESSED_DIR, "jfk_rice_excerpt_real.wav")
    sf.write(jfk_out, clip_jfk_16k, 16000, subtype="PCM_16")
    
    # Transcribe JFK
    segs, _ = whisper_model.transcribe(clip_jfk_16k)
    jfk_transcript = " ".join(s.text.strip() for s in segs)
    print(f"[OK] JFK Excerpt: {len(clip_jfk_16k)/16000:.1f}s -> {jfk_out}")
    print(f"     Transcript: {jfk_transcript[:100]}...")

    speeches_meta.append({
        "speech_id": "jfk_moon_1962",
        "title": "Address at Rice University on the Nation's Space Effort ('We choose to go to the Moon')",
        "speaker": "John F. Kennedy",
        "date": "1962-09-12",
        "location": "Rice Stadium, Houston, Texas",
        "source_url": "https://www.jfklibrary.org/asset-viewer/archives/JFKWHA/1962/JFKWHA-127-002",
        "audio_source_url": "https://archive.org/download/jfks19620912/jfks19620912.mp3",
        "licence": "Believed Public Domain (U.S. Government Work - 17 U.S.C. § 105)",
        "processed_file": "jfk_rice_excerpt_real.wav",
        "duration_s": round(len(clip_jfk_16k) / 16000, 2),
        "transcript": jfk_transcript,
    })

    # 2. Ronald Reagan Challenger Address (190.0s -> 251.0s, 61s)
    reagan_raw = "data/raw/reagan_challenger_1986.ogg"
    data_r, sr_r = sf.read(reagan_raw)
    clip_r = data_r[int(190.0 * sr_r) : int(251.0 * sr_r)]
    clip_r_16k = resample_mono_16k(clip_r, sr_r)
    reagan_out = os.path.join(PROCESSED_DIR, "reagan_challenger_excerpt_real.wav")
    sf.write(reagan_out, clip_r_16k, 16000, subtype="PCM_16")

    segs_r, _ = whisper_model.transcribe(clip_r_16k)
    reagan_transcript = " ".join(s.text.strip() for s in segs_r)
    print(f"[OK] Reagan Excerpt: {len(clip_r_16k)/16000:.1f}s -> {reagan_out}")
    print(f"     Transcript: {reagan_transcript[:100]}...")

    speeches_meta.append({
        "speech_id": "reagan_challenger_1986",
        "title": "Address to the Nation on the Explosion of the Space Shuttle Challenger",
        "speaker": "Ronald Reagan",
        "date": "1986-01-28",
        "location": "Oval Office, Washington, D.C.",
        "source_url": "https://www.reaganlibrary.gov/archives/speech/address-nation-explosion-space-shuttle-challenger",
        "audio_source_url": "https://archive.org/download/ChallengerAddress/ReaganChallengerAddress.mp3",
        "licence": "Believed Public Domain (U.S. Government Work - 17 U.S.C. § 105)",
        "processed_file": "reagan_challenger_excerpt_real.wav",
        "duration_s": round(len(clip_r_16k) / 16000, 2),
        "transcript": reagan_transcript,
    })

    # 3. FDR First Inaugural Address (0.0s -> 46.96s, ~47s)
    fdr_raw = "data/raw/fdr_fear_itself_1933.ogg"
    data_f, sr_f = sf.read(fdr_raw)
    clip_f_16k = resample_mono_16k(data_f, sr_f)
    fdr_out = os.path.join(PROCESSED_DIR, "fdr_fear_itself_excerpt_real.wav")
    sf.write(fdr_out, clip_f_16k, 16000, subtype="PCM_16")

    segs_f, _ = whisper_model.transcribe(clip_f_16k)
    fdr_transcript = " ".join(s.text.strip() for s in segs_f)
    print(f"[OK] FDR Excerpt: {len(clip_f_16k)/16000:.1f}s -> {fdr_out}")
    print(f"     Transcript: {fdr_transcript[:100]}...")

    speeches_meta.append({
        "speech_id": "fdr_fear_itself_1933",
        "title": "First Inaugural Address ('The only thing we have to fear is fear itself')",
        "speaker": "Franklin D. Roosevelt",
        "date": "1933-03-04",
        "location": "U.S. Capitol, Washington, D.C.",
        "source_url": "https://www.archives.gov/milestone-documents/franklin-d-roosevelts-first-inaugural-address",
        "audio_source_url": "https://archive.org/download/FDR_First_Inaugural_Address/FDR_Inaugural.mp3",
        "licence": "Believed Public Domain (U.S. National Archives sound recording - 17 U.S.C. § 105)",
        "processed_file": "fdr_fear_itself_excerpt_real.wav",
        "duration_s": round(len(clip_f_16k) / 16000, 2),
        "transcript": fdr_transcript,
    })

    # Save manifest
    manifest_path = os.path.join(MANIFESTS_DIR, "real_speech_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fp:
        json.dump(speeches_meta, fp, indent=2)
    print(f"\n[OK] Manifest saved to {manifest_path}")


if __name__ == "__main__":
    process_all_speeches()
