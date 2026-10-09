import os
import sys
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, os.path.abspath("."))

import re
import difflib
import num2words
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from backend.pipeline.align import align_audio_with_transcript

def canon_word(w):
    clean = re.sub(r"[^a-zA-Z0-9]", "", w).lower()
    if clean.isdigit():
        try:
            return num2words.num2words(int(clean)).replace("-", " ")
        except Exception:
            return clean
    return clean

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

align_res = align_audio_with_transcript(audio_arr, transcript, sr=sr)
mms_words = align_res.words

model = WhisperModel("base.en", device="cpu", compute_type="int8")
segments, _ = model.transcribe(audio_arr, word_timestamps=True, beam_size=5)
whisper_words = []
for seg in segments:
    for w in seg.words:
        c = re.sub(r"[^a-zA-Z0-9]", "", w.word).lower()
        if c:
            whisper_words.append({
                "text": c,
                "start": w.start,
                "end": w.end,
            })

# Flatten / canon
mms_clean = []
for w in mms_words:
    mms_clean.append({
        "orig_idx": w["index"],
        "text": re.sub(r"[^a-zA-Z0-9]", "", w["text"]).lower(),
        "start": w["start"],
        "end": w["end"],
        "duration": w["duration"],
    })

# Monotonic matching
start_diffs = []
matched_count = 0
w_ptr = 0

for m_w in mms_clean:
    m_text = m_w["text"]
    # Look around current pointer in whisper_words for matching word
    best_j = None
    best_dist = 999.0
    for j in range(max(0, w_ptr - 3), min(len(whisper_words), w_ptr + 8)):
        cand = whisper_words[j]
        # Text match (exact or substring for numbers)
        if cand["text"] == m_text or (m_text.isdigit() and cand["text"].isdigit()):
            dist = abs(cand["start"] - m_w["start"])
            if dist < best_dist and dist < 2.0:
                best_dist = dist
                best_j = j
    if best_j is not None:
        matched_cand = whisper_words[best_j]
        w_ptr = best_j + 1
        s_diff = abs(m_w["start"] - matched_cand["start"]) * 1000.0
        start_diffs.append(s_diff)
        matched_count += 1

print(f"Total MMS: {len(mms_clean)}, Total Whisper: {len(whisper_words)}, Matched: {matched_count} ({matched_count/len(mms_clean)*100:.1f}%)")
print(f"Median Start Diff: {np.median(start_diffs):.1f} ms | p90 Start Diff: {np.percentile(start_diffs, 90):.1f} ms")
