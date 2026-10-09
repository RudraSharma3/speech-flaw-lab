import os
import sys
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, os.path.abspath("."))

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from backend.pipeline.align import align_audio_with_transcript

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
wh_words = [w for seg in segments for w in seg.words]

print(f"{'Index':<5} | {'MMS Word':<15} | {'MMS Start':<10} | {'MMS End':<10} | {'Wh Word':<15} | {'Wh Start':<10} | {'Wh End':<10} | {'Start Diff (ms)':<15}")
print("-" * 105)
for i in range(min(len(mms_words), 20)):
    mw = mms_words[i]
    # find corresponding whisper word
    ww = wh_words[i] if i < len(wh_words) else None
    if ww:
        diff_ms = (mw['start'] - ww.start) * 1000.0
        print(f"{i:<5d} | {mw['text']:<15} | {mw['start']:<10.3f} | {mw['end']:<10.3f} | {ww.word.strip():<15} | {ww.start:<10.3f} | {ww.end:<10.3f} | {diff_ms:<+15.1f}")
