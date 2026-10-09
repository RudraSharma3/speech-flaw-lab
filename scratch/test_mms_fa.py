import os
import re
import difflib
import numpy as np
import soundfile as sf
import torch
import torchaudio
import num2words
from faster_whisper import WhisperModel

def normalize_text_for_alignment(transcript: str):
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


def run_mms_fa_alignment(audio_arr: np.ndarray, transcript: str, sr: int = 16000):
    if audio_arr.ndim > 1:
        audio_arr = audio_arr.mean(axis=1)

    waveform = torch.from_numpy(audio_arr).float().unsqueeze(0)
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(sr, 16000)
        waveform = resampler(waveform)

    words_meta, expanded_tokens = normalize_text_for_alignment(transcript)
    if not words_meta:
        return []

    bundle = torchaudio.pipelines.MMS_FA
    model = bundle.get_model()
    model.eval()
    labels = bundle.get_labels()
    dictionary = bundle.get_dict()

    with torch.inference_mode():
        emissions, _ = model(waveform)
        emissions = torch.log_softmax(emissions, dim=-1)

    num_frames = emissions.size(1)
    total_audio_s = waveform.size(1) / 16000.0
    frame_dur_s = total_audio_s / max(num_frames, 1)

    full_text = "*".join([w for _, w in expanded_tokens]) + "*"
    targets = torch.tensor([[dictionary[c] for c in full_text if c in dictionary]], dtype=torch.int32)

    alignments, scores = torchaudio.functional.forced_align(emissions, targets, blank=0)
    token_spans = torchaudio.functional.merge_tokens(alignments[0], scores[0])

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

    # Group subwords by parent original word index
    word_raw_spans = {}
    for sub in subword_intervals:
        p_idx = sub["parent_idx"]
        if p_idx not in word_raw_spans:
            word_raw_spans[p_idx] = {"start": sub["start"], "end": sub["end"]}
        else:
            word_raw_spans[p_idx]["end"] = max(word_raw_spans[p_idx]["end"], sub["end"])

    # Compute short-time energy to detect silences >= 120ms
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
        if i in word_raw_spans:
            w_start = word_raw_spans[i]["start"]
            w_ctc_end = word_raw_spans[i]["end"]
        else:
            # Fallback interpolation if missing
            prev_end = aligned_words[-1]["end"] if aligned_words else 0.0
            w_start = prev_end
            w_ctc_end = prev_end + 0.150

        # Post-process word boundaries:
        # Keep START from aligner.
        # Set END = next word's START, EXCEPT where silence >= 120ms exists, then end where speech ends.
        if i < num_words - 1 and (i + 1) in word_raw_spans:
            next_start = word_raw_spans[i + 1]["start"]
            gap = next_start - w_ctc_end
            if gap >= 0.120:
                # Find where speech actually ends between w_ctc_end and next_start
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
                # No significant silence: boundary meets next word
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

    # Ensure strictly monotonic non-overlapping
    for i in range(len(aligned_words) - 1):
        if aligned_words[i]["end"] > aligned_words[i + 1]["start"]:
            mid = (aligned_words[i]["start"] + aligned_words[i + 1]["start"]) / 2.0
            aligned_words[i]["end"] = round(max(mid, aligned_words[i]["start"] + 0.030), 3)
            aligned_words[i]["duration"] = round(aligned_words[i]["end"] - aligned_words[i]["start"], 3)

    return aligned_words


def test_jfk_alignment():
    audio, sr = sf.read("data/processed/jfk_rice_excerpt_real.wav")
    transcript = (
        "140,000 miles away from the control station in Houston, a giant rocket, more than 300 feet tall, "
        "the length of this football field, made of new metal alloys, some of which have not yet been embedded, "
        "capable of standing heat and stresses, several times more than have ever been experienced, "
        "pitted together with a precision better than the finest watch, carrying all the equipment needed "
        "for propulsion, guidance, control, communication, food and survival, on an untried mission to an unknown celestial body "
        "and then return it safely to earth, re-entering the atmosphere at speeds of over 25,000 miles per hour, "
        "causing heat about half that on the temperature of the sun, almost as hot as it is here today "
        "and do all this and do all this and do it right and do it first, if all this thick heat is out, then we must be bald."
    )

    print("[INFO] Running MMS_FA Forced Alignment on JFK speech...")
    mms_words = run_mms_fa_alignment(audio, transcript, sr=sr)
    print(f"[OK] Total Words Aligned: {len(mms_words)}")

    print("\n--- FIRST 20 WORDS ---")
    for w in mms_words[:20]:
        print(f"  #{w['index']:02d} {w['text']:12s} [{w['start']:6.3f}s -> {w['end']:6.3f}s] (dur: {w['duration']:5.3f}s, punct: '{w['punctuation']}')")

    durations = [w["duration"] for w in mms_words]
    print(f"\nMedian word duration: {np.median(durations):.3f}s, Mean: {np.mean(durations):.3f}s, Min: {min(durations):.3f}s, Max: {max(durations):.3f}s")

    # Faster Whisper cross check
    print("\n[INFO] Running Faster-Whisper with word_timestamps=True...")
    whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    segs, _ = whisper_model.transcribe(audio.astype(np.float32), word_timestamps=True)
    whisper_words = []
    for s in segs:
        for w in s.words:
            clean = re.sub(r"[^a-zA-Z0-9\'-]", "", w.word).lower()
            if clean:
                whisper_words.append({"text": clean, "start": w.start, "end": w.end, "dur": w.end - w.start})

    # Difflib matching on normalized word sequences
    mms_clean = [re.sub(r"[^a-zA-Z0-9\'-]", "", w["text"]).lower() for w in mms_words]
    wh_clean = [w["text"] for w in whisper_words]

    matcher = difflib.SequenceMatcher(None, mms_clean, wh_clean)
    matching_blocks = matcher.get_matching_blocks()

    start_diffs_ms = []
    end_diffs_ms = []
    matched_pairs = []

    for block in matching_blocks:
        for offset in range(block.size):
            m_i = block.a + offset
            w_i = block.b + offset
            m_w = mms_words[m_i]
            w_w = whisper_words[w_i]
            s_diff = abs(m_w["start"] - w_w["start"]) * 1000.0
            e_diff = abs(m_w["end"] - w_w["end"]) * 1000.0
            start_diffs_ms.append(s_diff)
            end_diffs_ms.append(e_diff)
            matched_pairs.append((m_w, w_w, s_diff, e_diff))

    match_pct = (len(matched_pairs) / len(mms_words)) * 100.0
    med_s = float(np.median(start_diffs_ms))
    p90_s = float(np.percentile(start_diffs_ms, 90))
    med_e = float(np.median(end_diffs_ms))
    p90_e = float(np.percentile(end_diffs_ms, 90))

    print(f"\n[OK] Matched: {len(matched_pairs)} / {len(mms_words)} words ({match_pct:.1f}%)")
    print(f"Start Timestamp Difference: Median = {med_s:.1f} ms | 90th-percentile = {p90_s:.1f} ms")
    print(f"End   Timestamp Difference: Median = {med_e:.1f} ms | 90th-percentile = {p90_e:.1f} ms")

    # Shortest 10 words
    sorted_by_dur = sorted(mms_words, key=lambda x: x["duration"])
    print("\n--- SHORTEST 10 WORDS ---")
    for w in sorted_by_dur[:10]:
        print(f"  Word '{w['text']}' (#{w['index']:02d}): [{w['start']:.3f}s -> {w['end']:.3f}s] dur={w['duration']:.3f}s")


if __name__ == "__main__":
    test_jfk_alignment()
