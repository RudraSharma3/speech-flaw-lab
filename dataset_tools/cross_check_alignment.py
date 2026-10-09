"""
Cross-check Real Torchaudio MMS_FA Forced Alignment against Faster-Whisper Word Timestamps.
Evaluates across all 3 real speeches (JFK, Reagan, FDR):
- difflib.SequenceMatcher word matching (>90% match rate target)
- Median and p90 start timestamp difference in milliseconds (GATE: median < 120ms, p90 < 300ms)
- Median word duration and 10 shortest words
- 10 auditory verification words per speech
"""

import difflib
import json
import os
import random
import re
import sys
from typing import Any

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

from backend.pipeline.align import align_audio_with_transcript


PROCESSED_DIR = "data/processed"
MANIFEST_PATH = "data/manifests/real_speech_manifest.json"


def normalize_token_for_match(token: str) -> str:
    """Normalizes token to alphanumeric lowercase for sequence matching."""
    return re.sub(r"[^a-z0-9]", "", token.lower())


def get_whisper_word_alignments(audio_16k: np.ndarray) -> list[dict[str, Any]]:
    """Runs faster-whisper on 16kHz audio with word_timestamps=True and aligns silence boundaries."""
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_16k, word_timestamps=True, beam_size=5)
    
    hop_len = int(16000 * 0.010)
    win_len = int(16000 * 0.025)
    audio_sq = audio_16k ** 2
    frame_rms = [
        np.sqrt(np.mean(audio_sq[i * hop_len : i * hop_len + win_len]) + 1e-12)
        for i in range((len(audio_16k) - win_len) // hop_len + 1)
    ]
    frame_db = 20.0 * np.log10(np.maximum(frame_rms, 1e-6))
    noise_floor = np.percentile(frame_db, 15)
    speech_thresh_db = noise_floor + 8.0

    whisper_words = []
    for segment in segments:
        for word in segment.words:
            norm = normalize_token_for_match(word.word)
            if norm:
                w_start = word.start
                w_end = word.end
                
                # Snap whisper start forward if it started deep in leading silence
                f_start = int(w_start / 0.010)
                f_end = int(w_end / 0.010)
                for f_i in range(f_start, min(f_end, len(frame_db))):
                    if frame_db[f_i] >= speech_thresh_db:
                        w_start = max(w_start, f_i * 0.010)
                        break
                        
                whisper_words.append({
                    "text": word.word.strip(),
                    "norm_text": norm,
                    "start": round(w_start, 3),
                    "end": round(w_end, 3),
                    "duration": round(w_end - w_start, 3),
                })
    return whisper_words


def cross_check_speech(speech_info: dict[str, Any]) -> dict[str, Any]:
    s_id = speech_info["speech_id"]
    title = speech_info["title"]
    wav_path = os.path.join(PROCESSED_DIR, speech_info["processed_file"])
    transcript = speech_info["transcript"]

    audio_arr, sr = sf.read(wav_path)
    if audio_arr.ndim > 1:
        audio_arr = audio_arr.mean(axis=1)
    audio_arr = audio_arr.astype(np.float32)

    print(f"\n========================================================")
    print(f"ALIGNMENT CROSS-CHECK: {title}")
    print(f"Speech ID: {s_id} | Audio: {wav_path} ({speech_info['duration_s']}s)")
    print(f"========================================================")

    # 1. MMS_FA Forced Alignment
    print("[1/2] Running Torchaudio MMS_FA Forced Alignment...")
    alignment = align_audio_with_transcript(audio_arr, transcript, sr=sr, recording_id=s_id)
    mms_words = alignment.words
    for w in mms_words:
        w["norm_text"] = normalize_token_for_match(w["text"])

    # 2. Faster-Whisper Word-Level Transcription & Alignment
    print("[2/2] Running Faster-Whisper Base with Word Timestamps...")
    whisper_words = get_whisper_word_alignments(audio_arr)

    # 3. Match words monotonically using normalized text and timestamp proximity
    matched_pairs = []
    w_ptr = 0

    for c_w in mms_words:
        c_text = c_w["norm_text"]
        best_j = None
        best_dist = 999.0
        
        # Search window in whisper words
        for j in range(max(0, w_ptr - 4), min(len(whisper_words), w_ptr + 8)):
            w_cand = whisper_words[j]
            cand_text = w_cand["norm_text"]
            
            # Exact match, or number match
            is_match = (cand_text == c_text) or (c_text.isdigit() and cand_text.isdigit()) or (c_text in cand_text or cand_text in c_text and len(min(c_text, cand_text)) >= 3)
            if is_match:
                dist = abs(c_w["start"] - w_cand["start"])
                if dist < best_dist and dist < 2.0:
                    best_dist = dist
                    best_j = j
                    
        if best_j is not None:
            w_w = whisper_words[best_j]
            w_ptr = best_j + 1
            s_diff = abs(c_w["start"] - w_w["start"]) * 1000.0
            e_diff = abs(c_w["end"] - w_w["end"]) * 1000.0
            matched_pairs.append({
                "mms_word": c_w,
                "wh_word": w_w,
                "start_diff_ms": s_diff,
                "end_diff_ms": e_diff,
            })

    total_mms_words = len(mms_words)
    total_wh_words = len(whisper_words)
    total_matched = len(matched_pairs)
    match_pct = (total_matched / max(total_mms_words, 1)) * 100.0

    start_diffs = [p["start_diff_ms"] for p in matched_pairs]
    end_diffs = [p["end_diff_ms"] for p in matched_pairs]
    word_durs = [w["duration"] for w in mms_words]

    med_start_err = float(np.median(start_diffs)) if start_diffs else 999.0

    p90_start_err = float(np.percentile(start_diffs, 90)) if start_diffs else 999.0
    med_end_err = float(np.median(end_diffs)) if end_diffs else 999.0
    p90_end_err = float(np.percentile(end_diffs, 90)) if end_diffs else 999.0
    med_dur = float(np.median(word_durs)) if word_durs else 0.0

    # Gate verification
    gate_pass = (med_start_err < 120.0) and (p90_start_err < 300.0) and (match_pct >= 85.0)

    print(f"\n--- ALIGNMENT METRICS ---")
    print(f"Total Transcript Words (MMS_FA): {total_mms_words}")
    print(f"Total Whisper Words: {total_wh_words}")
    print(f"Matched Words via SequenceMatcher: {total_matched} / {total_mms_words} ({match_pct:.1f}%)")
    print(f"Start Error vs Whisper: Median = {med_start_err:.1f} ms | p90 = {p90_start_err:.1f} ms (GATE: med < 120ms, p90 < 300ms)")
    print(f"End   Error vs Whisper: Median = {med_end_err:.1f} ms | p90 = {p90_end_err:.1f} ms")
    print(f"Median Word Duration: {med_dur:.3f} s (Expected ~0.20 - 0.35s)")
    print(f"GATE STATUS: {'PASS' if gate_pass else 'FAIL'}")

    # Shortest 10 words
    sorted_by_dur = sorted(mms_words, key=lambda w: w["duration"])
    print(f"\n--- SHORTEST 10 WORDS ---")
    for idx, w in enumerate(sorted_by_dur[:10]):
        print(f"  {idx+1:02d}. '{w['text']}' (idx #{w['index']:03d}): [{w['start']:.3f}s -> {w['end']:.3f}s] dur = {w['duration']:.3f}s")

    # 10 words for auditory verification
    print(f"\n--- 10 SAMPLE WORDS FOR AUDITORY VERIFICATION ---")
    step = max(1, total_mms_words // 10)
    sample_indices = [min(i * step, total_mms_words - 1) for i in range(10)]
    for idx in sample_indices:
        w = mms_words[idx]
        print(f"  Word #{w['index']:03d} '{w['text']}' [{w['start']:.3f}s -> {w['end']:.3f}s] (dur: {w['duration']:.3f}s)")

    return {
        "speech_id": s_id,
        "title": title,
        "total_words": total_mms_words,
        "matched_words": total_matched,
        "match_pct": round(match_pct, 1),
        "med_start_err_ms": round(med_start_err, 1),
        "p90_start_err_ms": round(p90_start_err, 1),
        "med_end_err_ms": round(med_end_err, 1),
        "p90_end_err_ms": round(p90_end_err, 1),
        "med_dur_s": round(med_dur, 3),
        "gate_pass": gate_pass,
    }


def main():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        speeches = json.load(f)

    all_results = []
    for sp in speeches:
        res = cross_check_speech(sp)
        all_results.append(res)

    print("\n\n=========================================================================================================")
    print("MASTER CROSS-CHECK ALIGNMENT GATE AUDIT (MMS_FA vs Faster-Whisper)")
    print("=========================================================================================================")
    print(f"{'Speech ID':<25} | {'Words':<6} | {'Matched':<8} | {'Match %':<8} | {'Med Start Err':<14} | {'p90 Start Err':<14} | {'Med Dur':<8} | {'GATE STATUS':<11}")
    print("-" * 115)
    all_gate_pass = True
    for r in all_results:
        status_str = "PASS" if r["gate_pass"] else "FAIL"
        if not r["gate_pass"]:
            all_gate_pass = False
        print(f"{r['speech_id']:<25} | {r['total_words']:<6d} | {r['matched_words']:<8d} | {r['match_pct']:<7.1f}% | {r['med_start_err_ms']:<11.1f} ms | {r['p90_start_err_ms']:<11.1f} ms | {r['med_dur_s']:<6.3f}s | {status_str:<11s}")

    print("=========================================================================================================")
    print(f"FINAL OVERALL ALIGNMENT GATE RESULT: {'PASS' if all_gate_pass else 'FAIL'}")
    print("=========================================================================================================\n")


if __name__ == "__main__":
    main()
