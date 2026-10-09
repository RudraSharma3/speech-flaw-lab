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

# Calculate frame RMS / dB
hop_len = int(16000 * 0.010)
win_len = int(16000 * 0.025)
audio_sq = audio_arr ** 2
frame_rms = [
    np.sqrt(np.mean(audio_sq[i * hop_len : i * hop_len + win_len]) + 1e-12)
    for i in range((len(audio_arr) - win_len) // hop_len + 1)
]
frame_db = 20.0 * np.log10(np.maximum(frame_rms, 1e-6))
noise_floor = np.percentile(frame_db, 20)
speech_thresh_db = noise_floor + 10.0

whisper_words = []
for seg in segments:
    for w in seg.words:
        c = re.sub(r"[^a-zA-Z0-9]", "", w.word).lower()
        if not c:
            continue
        # Check backward from w.end to find where speech actually began
        f_end = int(w.end / 0.010)
        f_start = int(w.start / 0.010)
        
        # Look forward from w.start to find the actual energy rise
        actual_start = w.start
        for f_i in range(f_start, min(f_end, len(frame_db))):
            if frame_db[f_i] >= speech_thresh_db:
                actual_start = f_i * 0.010
                break
                
        whisper_words.append({
            "text": c,
            "start": round(actual_start, 3),
            "end": round(w.end, 3),
        })

# Match
start_diffs = []
w_ptr = 0
for m_w in mms_words:
    c_text = re.sub(r"[^a-zA-Z0-9]", "", m_w["text"]).lower()
    best_j = None
    best_dist = 999.0
    for j in range(max(0, w_ptr - 4), min(len(whisper_words), w_ptr + 8)):
        cand = whisper_words[j]
        if cand["text"] == c_text:
            dist = abs(cand["start"] - m_w["start"])
            if dist < best_dist and dist < 2.5:
                best_dist = dist
                best_j = j
    if best_j is not None:
        w_ptr = best_j + 1
        s_diff = abs(m_w["start"] - whisper_words[best_j]["start"]) * 1000.0
        start_diffs.append(s_diff)

print(f"FDR Matched: {len(start_diffs)} / {len(mms_words)} ({len(start_diffs)/len(mms_words)*100:.1f}%)")
print(f"Median Start Diff: {np.median(start_diffs):.1f} ms | p90 Start Diff: {np.percentile(start_diffs, 90):.1f} ms")
