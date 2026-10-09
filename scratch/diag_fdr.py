import os
import sys
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, os.path.abspath("."))

import re
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from backend.pipeline.align import align_audio_with_transcript

audio_arr, sr = sf.read("data/processed/fdr_fear_itself_excerpt_real.wav")
if audio_arr.ndim > 1:
    audio_arr = audio_arr.mean(axis=1)

transcript = (
    "Let me assert my firm belief that the only thing we have to fear is fear itself "
    "nameless unreasoning unjustified terror which paralyzes needed efforts to convert retreat into advance . "
    "In every dark hour of our national life a leadership of frankness and vigor has met with that understanding "
    "and support of the people themselves which is essential to victory . "
    "And I am convinced that you will again give that support to leadership in these critical days ."
)

align_res = align_audio_with_transcript(audio_arr, transcript, sr=sr)
mms_words = align_res.words

model = WhisperModel("base.en", device="cpu", compute_type="int8")
segments, _ = model.transcribe(audio_arr, word_timestamps=True, beam_size=5)
whisper_words = []
for seg in segments:
    for w in seg.words:
        c = re.sub(r"[^a-zA-Z0-9]", "", w.word).lower()
        if c:
            whisper_words.append({"text": c, "start": w.start, "end": w.end, "raw": w.word})

print(f"{'Idx':<4} | {'MMS Word':<15} | {'MMS Start':<10} | {'MMS End':<10} | {'Wh Word':<15} | {'Wh Start':<10} | {'Wh End':<10} | {'Start Diff (ms)':<15}")
print("-" * 105)

w_ptr = 0
for i, mw in enumerate(mms_words):
    c_text = re.sub(r"[^a-zA-Z0-9]", "", mw["text"]).lower()
    best_j = None
    best_dist = 999.0
    for j in range(max(0, w_ptr - 4), min(len(whisper_words), w_ptr + 8)):
        cand = whisper_words[j]
        if cand["text"] == c_text:
            dist = abs(cand["start"] - mw["start"])
            if dist < best_dist and dist < 3.0:
                best_dist = dist
                best_j = j
    if best_j is not None:
        ww = whisper_words[best_j]
        w_ptr = best_j + 1
        s_diff = (mw["start"] - ww["start"]) * 1000.0
        print(f"{i:<4d} | {mw['text']:<15} | {mw['start']:<10.3f} | {mw['end']:<10.3f} | {ww['raw'].strip():<15} | {ww['start']:<10.3f} | {ww['end']:<10.3f} | {s_diff:<+15.1f}")
    else:
        print(f"{i:<4d} | {mw['text']:<15} | {mw['start']:<10.3f} | {mw['end']:<10.3f} | {'[NO MATCH]':<15} | {'-':<10} | {'-':<10} | {'-'}")
