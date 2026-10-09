"""
Forced Alignment Interface.
Implements Real Torchaudio MMS_FA (Multilingual/English Forced Aligner).
Normalizes transcripts (expanding numbers via num2words, stripping punctuation to metadata),
and post-processes boundaries with energy/VAD silence detection (>=120ms pause gaps).
Strictly generates monotonic, non-overlapping word intervals with exact provenance.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any

import numpy as np
import num2words
import soundfile as sf
import torch
import torchaudio

ALIGNMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "alignments")


class AlignmentResult:
    def __init__(self, words: list[dict[str, Any]], engine_used: str, phonemes: list[dict[str, Any]] | None = None):
        self.words = words
        self.engine_used = engine_used
        self.phonemes = phonemes or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_used": self.engine_used,
            "words": self.words,
            "phonemes": self.phonemes,
        }

    def save_json(self, target_path: str):
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


def clean_transcript_tokens(transcript: str) -> tuple[list[dict[str, Any]], list[tuple[int, str]]]:
    """
    Cleans transcript into list of display words with punctuation metadata,
    and returns phonetic subword expansions (e.g. converting digits via num2words).
    Returns:
      words_meta: list of original display words
      expanded_tokens: list of (word_idx, phonetic_word_str)
    """
    token_pattern = re.compile(r"^[\"“'‘]*([a-zA-Z0-9\'-]+)([\.,\?!;:\"”'’\-_]*)$")
    words_meta = []
    expanded_tokens = []
    
    for raw_tok in transcript.strip().split():
        if re.match(r"^[\.,\?!;:\-_/\\\"“”'’]+$", raw_tok):
            if words_meta:
                words_meta[-1]["punctuation"] += raw_tok
                words_meta[-1]["has_punctuation"] = True
            continue

        m = token_pattern.match(raw_tok)
        if m:
            w_text = m.group(1)
            punct = m.group(2)
        else:
            w_text = re.sub(r"[^a-zA-Z0-9\'-]", "", raw_tok)
            punct = "".join([c for c in raw_tok if c in ".,?!;:-"])

        if not w_text:
            continue

        w_idx = len(words_meta)
        has_p = any(c in ".,?!;:--" for c in punct)
        words_meta.append({
            "index": w_idx,
            "text": w_text,
            "punctuation": punct,
            "has_punctuation": has_p,
        })

        # Number expansion (e.g. 140000 -> one hundred forty thousand)
        clean_digits = re.sub(r"[^0-9]", "", w_text)
        if clean_digits and clean_digits.isdigit() and len(clean_digits) == len(re.sub(r"[^a-zA-Z0-9]", "", w_text)):
            try:
                num_val = int(clean_digits)
                expanded = num2words.num2words(num_val)
                for sub_w in re.findall(r"[a-z]+", expanded.lower()):
                    expanded_tokens.append((w_idx, sub_w))
            except Exception:
                expanded_tokens.append((w_idx, w_text.lower()))
        else:
            clean_letters = re.sub(r"[^a-z']", "", w_text.lower())
            if clean_letters:
                expanded_tokens.append((w_idx, clean_letters))
            else:
                expanded_tokens.append((w_idx, "uh"))

    return words_meta, expanded_tokens


# Set torch intraop parallelism to utilize all available physical/logical cores
if os.cpu_count():
    try:
        torch.set_num_threads(os.cpu_count())
    except Exception:
        pass

# Cached global MMS_FA model bundle
_MMS_FA_BUNDLE = None


def get_mms_fa_model():
    global _MMS_FA_BUNDLE
    if _MMS_FA_BUNDLE is None:
        if os.cpu_count():
            try:
                torch.set_num_threads(os.cpu_count())
            except Exception:
                pass
        bundle = torchaudio.pipelines.MMS_FA
        model = bundle.get_model()
        model.eval()
        labels = bundle.get_labels()
        dictionary = bundle.get_dict()
        _MMS_FA_BUNDLE = (bundle, model, labels, dictionary)
    return _MMS_FA_BUNDLE


def warmup_mms_fa():
    """Warms up MMS_FA model on dummy audio so first live request has zero cold-start delay."""
    bundle, model, labels, dictionary = get_mms_fa_model()
    dummy = torch.randn(1, 16000)
    with torch.inference_mode():
        _ = model(dummy)
    return _MMS_FA_BUNDLE


def run_mms_fa_alignment(
    audio_arr: np.ndarray,
    transcript: str,
    sr: int = 16000,
) -> AlignmentResult:
    """
    Runs Real Torchaudio MMS_FA Forced Alignment.
    Extracts frame emissions, computes target sequence with '*' word separators,
    merges tokens into word spans, and refines boundaries against silence gaps >= 120ms.
    """
    if audio_arr.ndim > 1:
        audio_arr = audio_arr.mean(axis=1)
    
    waveform = torch.from_numpy(audio_arr).float().unsqueeze(0)
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(sr, 16000)
        waveform = resampler(waveform)

    words_meta, expanded_tokens = clean_transcript_tokens(transcript)
    if not words_meta:
        return AlignmentResult(words=[], engine_used="torchaudio_mms_fa")

    _, model, labels, dictionary = get_mms_fa_model()

    with torch.inference_mode():
        emissions, _ = model(waveform)
        emissions = torch.log_softmax(emissions, dim=-1)

    num_frames = emissions.size(1)
    total_audio_s = waveform.size(1) / 16000.0
    frame_dur_s = total_audio_s / max(num_frames, 1)

    full_text = "*".join([w for _, w in expanded_tokens]) + "*"
    targets = torch.tensor([[dictionary[c] for c in full_text if c in dictionary]], dtype=torch.int32)

    try:
        alignments, scores = torchaudio.functional.forced_align(emissions, targets, blank=0)
        token_spans = torchaudio.functional.merge_tokens(alignments[0], scores[0])
    except Exception as e:
        raise RuntimeError(f"Torchaudio MMS_FA forced_align failed: {e}") from e

    subword_intervals = []
    curr_w_start = None
    curr_w_end = None
    curr_token_idx = 0

    for span in token_spans:
        tok_char = labels[span.token]
        if tok_char == "*":
            if curr_w_start is not None and curr_token_idx < len(expanded_tokens):
                parent_idx, sub_text = expanded_tokens[curr_token_idx]
                start_s = curr_w_start * frame_dur_s
                end_s = curr_w_end * frame_dur_s
                subword_intervals.append({
                    "parent_idx": parent_idx,
                    "sub_text": sub_text,
                    "start": start_s,
                    "end": end_s,
                })
                curr_token_idx += 1
                curr_w_start = None
                curr_w_end = None
        else:
            if curr_w_start is None:
                curr_w_start = span.start
            curr_w_end = span.end

    if curr_w_start is not None and curr_token_idx < len(expanded_tokens):
        parent_idx, sub_text = expanded_tokens[curr_token_idx]
        start_s = curr_w_start * frame_dur_s
        end_s = curr_w_end * frame_dur_s
        subword_intervals.append({
            "parent_idx": parent_idx,
            "sub_text": sub_text,
            "start": start_s,
            "end": end_s,
        })

    # Group subwords by parent display word index
    word_raw_spans = {}
    for sub in subword_intervals:
        p_idx = sub["parent_idx"]
        if p_idx not in word_raw_spans:
            word_raw_spans[p_idx] = {"start": sub["start"], "end": sub["end"]}
        else:
            word_raw_spans[p_idx]["end"] = max(word_raw_spans[p_idx]["end"], sub["end"])

    # Compute short-time energy profile for VAD pause detection (>=120ms)
    hop_len = int(16000 * 0.010)
    win_len = int(16000 * 0.025)
    audio_sq = audio_arr ** 2
    frame_rms = [
        np.sqrt(np.mean(audio_sq[i * hop_len : i * hop_len + win_len]) + 1e-12)
        for i in range((len(audio_arr) - win_len) // hop_len + 1)
    ]
    frame_db = 20.0 * np.log10(np.maximum(frame_rms, 1e-6))
    noise_floor = np.percentile(frame_db, 15)
    speech_thresh_db = noise_floor + 8.0

    aligned_words = []
    num_words = len(words_meta)

    for i in range(num_words):
        w_meta = words_meta[i]
        prev_end = aligned_words[-1]["end"] if aligned_words else 0.0

        if i in word_raw_spans:
            raw_s = word_raw_spans[i]["start"]
            w_ctc_end = word_raw_spans[i]["end"]

            # Acoustic onset search: check backward up to 100ms for vocal tract energy onset
            speech_start_s = max(prev_end, raw_s - 0.080)
            f_limit = max(int(prev_end / 0.010), int((raw_s - 0.100) / 0.010))
            f_raw = int(raw_s / 0.010)
            for f_i in range(min(f_raw, len(frame_db) - 1), max(0, f_limit - 1), -1):
                if frame_db[f_i] >= speech_thresh_db:
                    speech_start_s = f_i * 0.010
                elif (raw_s - f_i * 0.010) >= 0.050:
                    break
            w_start = max(prev_end, speech_start_s)
        else:
            w_start = prev_end
            w_ctc_end = prev_end + 0.150

        # Post-process word boundaries:
        # Keep START from aligner.
        # Set END = next word's START, EXCEPT where silence >= 120ms exists, then end where speech ends.
        if i < num_words - 1 and (i + 1) in word_raw_spans:
            next_raw_s = word_raw_spans[i + 1]["start"]
            next_start = max(w_start + 0.050, next_raw_s - 0.080)
            gap = next_start - w_ctc_end
            if gap >= 0.120:
                f_start = int(w_ctc_end / 0.010)
                f_end = int(next_start / 0.010)
                speech_end_s = w_ctc_end
                for f_i in range(f_start, min(f_end, len(frame_db))):
                    if frame_db[f_i] >= speech_thresh_db:
                        speech_end_s = (f_i + 1) * 0.010
                    elif (f_i * 0.010 - speech_end_s) >= 0.100:
                        break
                w_end = max(speech_end_s, w_start + 0.050)
                w_end = min(w_end, next_start)
            else:
                w_end = max(next_start, w_start + 0.050)
        else:
            w_end = max(w_ctc_end + 0.060, w_start + 0.050)

        dur = max(w_end - w_start, 0.040)
        aligned_words.append({
            "index": i,
            "text": w_meta["text"],
            "start": round(float(w_start), 3),
            "end": round(float(w_end), 3),
            "duration": round(float(dur), 3),
            "punctuation": w_meta["punctuation"],
            "has_punctuation": w_meta["has_punctuation"],
        })

    # Enforce strict non-overlapping monotonicity
    for i in range(len(aligned_words) - 1):
        if aligned_words[i]["end"] > aligned_words[i + 1]["start"]:
            mid = (aligned_words[i]["start"] + aligned_words[i + 1]["start"]) / 2.0
            aligned_words[i]["end"] = round(max(mid, aligned_words[i]["start"] + 0.030), 3)
            aligned_words[i]["duration"] = round(aligned_words[i]["end"] - aligned_words[i]["start"], 3)

    return AlignmentResult(words=aligned_words, engine_used="torchaudio_mms_fa")


def run_mfa_alignment(
    audio_path: str, transcript: str, dictionary: str = "english_us_arpa", acoustic_model: str = "english_us_arpa"
) -> AlignmentResult | None:
    """Runs Montreal Forced Aligner via CLI if available."""
    mfa_bin = shutil.which("mfa")
    if not mfa_bin:
        return None

    with tempfile.TemporaryDirectory() as temp_dir:
        corpus_dir = os.path.join(temp_dir, "corpus")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(corpus_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        base_name = "utterance"
        target_wav = os.path.join(corpus_dir, f"{base_name}.wav")
        target_txt = os.path.join(corpus_dir, f"{base_name}.txt")

        shutil.copyfile(audio_path, target_wav)
        with open(target_txt, "w", encoding="utf-8") as f:
            f.write(transcript)

        cmd = [
            mfa_bin,
            "align",
            corpus_dir,
            dictionary,
            acoustic_model,
            output_dir,
            "--clean",
            "--single_speaker",
            "--num_jobs",
            "1",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
            if res.returncode == 0:
                textgrid_path = os.path.join(output_dir, f"{base_name}.TextGrid")
                if os.path.exists(textgrid_path):
                    words, phones = parse_textgrid(textgrid_path, transcript)
                    return AlignmentResult(words=words, engine_used="mfa_arpa", phonemes=phones)
        except Exception:
            pass

    return None


def parse_textgrid(textgrid_path: str, original_transcript: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parses Praat TextGrid into structured word intervals."""
    words_meta, _ = clean_transcript_tokens(original_transcript)
    words = []
    phones = []
    
    with open(textgrid_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()

    interval_pattern = re.compile(r'xmin\s*=\s*([0-9.]+)\s*xmax\s*=\s*([0-9.]+)\s*text\s*=\s*"([^"]*)"')
    matches = interval_pattern.findall(content)
    
    w_idx = 0
    for xmin, xmax, text in matches:
        text_clean = text.strip()
        if not text_clean or text_clean in ["<eps>", "sil", "sp", ""]:
            continue
        
        if w_idx < len(words_meta):
            w_meta = words_meta[w_idx]
            words.append({
                "index": w_idx,
                "text": w_meta["text"],
                "start": round(float(xmin), 3),
                "end": round(float(xmax), 3),
                "duration": round(float(xmax) - float(xmin), 3),
                "punctuation": w_meta["punctuation"],
                "has_punctuation": w_meta["has_punctuation"],
            })
            w_idx += 1

    return words, phones


def align_audio_with_transcript(
    audio_path_or_arr: Any,
    transcript: str,
    sr: int = 16000,
    audio_duration_s: float | None = None,
    speech_segments: list[dict[str, float]] | None = None,
    recording_id: str | None = None,
) -> AlignmentResult:
    """
    Unified alignment entry point.
    Tries MFA first, otherwise executes Real Torchaudio MMS_FA Forced Alignment.
    Saves single source of truth alignment JSON.
    """
    if isinstance(audio_path_or_arr, str) and os.path.exists(audio_path_or_arr):
        mfa_res = run_mfa_alignment(audio_path_or_arr, transcript)
        if mfa_res and len(mfa_res.words) > 0:
            if recording_id:
                align_path = os.path.join(ALIGNMENTS_DIR, f"{recording_id}_alignment.json")
                mfa_res.save_json(align_path)
            return mfa_res
        
        audio_arr, _ = sf.read(audio_path_or_arr)
        if audio_arr.ndim > 1:
            audio_arr = audio_arr.mean(axis=1)
    else:
        audio_arr = np.asarray(audio_path_or_arr, dtype=np.float32)

    # Real Torchaudio MMS_FA Forced Alignment
    align_res = run_mms_fa_alignment(audio_arr, transcript, sr=sr)
    
    if recording_id:
        align_path = os.path.join(ALIGNMENTS_DIR, f"{recording_id}_alignment.json")
        align_res.save_json(align_path)
        
    return align_res
