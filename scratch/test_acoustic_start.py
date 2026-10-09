import os
import sys
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, os.path.abspath("."))

import re
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
import torch
import torchaudio
import num2words

audio_arr, sr = sf.read("data/processed/jfk_rice_excerpt_real.wav")
if audio_arr.ndim > 1:
    audio_arr = audio_arr.mean(axis=1)

transcript = (
    "140000 miles away from the control station in Houston a giant rocket more than 300 feet tall "
    "the length of this football field made of new metal alloys some of which have not yet been embedded "
    "capable of standing heat and stresses several times more than have ever been experienced "
    "pitted together with a precision better than the finest watch carrying all the equipment needed "
    "for propulsion guidance control communication food and survival on an untried mission to an unknown celestial body "
    "and then return it safely to earth re-entering the atmosphere at speeds of over 25000 miles per hour "
    "causing heat about half that on the temperature of the sun almost as hot as it is here today "
    "and do all this and do all this and do it right and do it first if all this thick heat is out then we must be bald ."
)

# Load Whisper words
model = WhisperModel("base.en", device="cpu", compute_type="int8")
segments, _ = model.transcribe(audio_arr, word_timestamps=True, beam_size=5)
whisper_words = []
for seg in segments:
    for w in seg.words:
        c = re.sub(r"[^a-zA-Z0-9]", "", w.word).lower()
        if c:
            whisper_words.append({"text": c, "start": w.start, "end": w.end})

from backend.pipeline.align import clean_transcript_tokens, get_mms_fa_model

words_meta, expanded_tokens = clean_transcript_tokens(transcript)
bundle, mms_model, labels, dictionary = get_mms_fa_model()

waveform = torch.from_numpy(audio_arr).float().unsqueeze(0)
with torch.inference_mode():
    emissions, _ = mms_model(waveform)
    emissions = torch.log_softmax(emissions, dim=-1)

num_frames = emissions.size(1)
frame_dur_s = (len(audio_arr) / 16000.0) / num_frames

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
            subword_intervals.append({
                "parent_idx": parent_idx,
                "start": curr_w_start * frame_dur_s,
                "end": span.end * frame_dur_s,
            })
            curr_token_idx += 1
            curr_w_start = None
    else:
        if curr_w_start is None:
            curr_w_start = span.start

word_raw_spans = {}
for sub in subword_intervals:
    p_idx = sub["parent_idx"]
    if p_idx not in word_raw_spans:
        word_raw_spans[p_idx] = {"start": sub["start"], "end": sub["end"]}
    else:
        word_raw_spans[p_idx]["end"] = max(word_raw_spans[p_idx]["end"], sub["end"])

# Test various CTC lead-in offsets (e.g. 0ms, 40ms, 80ms, 100ms, 120ms)
for offset_ms in [0, 40, 60, 80, 100, 120]:
    start_diffs = []
    w_ptr = 0
    for i, w_meta in enumerate(words_meta):
        if i not in word_raw_spans:
            continue
        raw_s = word_raw_spans[i]["start"]
        adj_s = max(0.0, raw_s - offset_ms / 1000.0)
        
        w_text = re.sub(r"[^a-zA-Z0-9]", "", w_meta["text"]).lower()
        # Match against whisper
        best_j = None
        best_dist = 999.0
        for j in range(max(0, w_ptr - 3), min(len(whisper_words), w_ptr + 8)):
            cand = whisper_words[j]
            if cand["text"] == w_text or (w_text.isdigit() and cand["text"].isdigit()):
                dist = abs(cand["start"] - adj_s)
                if dist < best_dist and dist < 2.0:
                    best_dist = dist
                    best_j = j
        if best_j is not None:
            w_ptr = best_j + 1
            start_diffs.append(abs(adj_s - whisper_words[best_j]["start"]) * 1000.0)

    print(f"Offset {offset_ms:3d}ms: Matched {len(start_diffs):3d} | Median Start Diff = {np.median(start_diffs):.1f} ms | p90 = {np.percentile(start_diffs, 90):.1f} ms")
