import os, sys
sys.path.insert(0, os.path.abspath('.'))
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import json
import soundfile as sf
import numpy as np
from backend.pipeline.align import align_audio_with_transcript
from backend.pipeline.vad import detect_speech_and_pauses
from faster_whisper import WhisperModel

audio_path = 'data/processed/fdr_fear_itself_excerpt_real.wav'
audio_arr, sr = sf.read(audio_path)
with open('data/manifests/real_speech_manifest.json') as f:
    manifest = json.load(f)
transcript = manifest[2]['transcript']

# 1. Silero VAD
vad_speech, vad_pauses, _ = detect_speech_and_pauses(audio_arr, sr=sr)

# 2. Snapped MMS_FA
snapped_res = align_audio_with_transcript(audio_arr, transcript, sr=sr, recording_id='fdr')

# 3. Faster-Whisper
whisper_model = WhisperModel('base.en', device='cpu', compute_type='int8')
segs, _ = whisper_model.transcribe(audio_path, word_timestamps=True)
wh_words = []
for s in segs:
    for w in s.words:
        wh_words.append({'text': w.word.strip().lower(), 'start': w.start, 'end': w.end})

print(f"=== FDR ALIGNMENT COMPARISON (Duration: {len(audio_arr)/sr:.2f}s, Words: {len(snapped_res.words)}) ===")
print(f"Silero VAD Speech Segments Detected: {len(vad_speech)}")
for i, v in enumerate(vad_speech[:8]):
    print(f"  VAD Seg {i}: [{v['start_s']:.3f}s -> {v['end_s']:.3f}s] (dur = {v['end_s']-v['start_s']:.3f}s)")

print("\nWord-Level Timing Comparison (First 25 words):")
print(f"{'Idx':<4} | {'Word':<12} | {'MMS_Snapped':<16} | {'Whisper':<16} | {'Wh-MMS diff':<12} | {'Nearest VAD Interval':<24}")
print("-" * 90)

diffs = []
for i in range(min(len(snapped_res.words), len(wh_words))):
    sw = snapped_res.words[i]
    ww = wh_words[i]
    diff_s = (ww['start'] - sw['start']) * 1000.0
    diffs.append(abs(diff_s))
    n_vad = min(vad_speech, key=lambda v: abs(v['start_s'] - sw['start']))
    vad_str = f"[{n_vad['start_s']:.2f}s -> {n_vad['end_s']:.2f}s]"
    if i < 25:
        print(f"{i:4d} | {sw['text']:<12} | [{sw['start']:.3f}, {sw['end']:.3f}] | [{ww['start']:.3f}, {ww['end']:.3f}] | {diff_s:+8.1f} ms | {vad_str:<24}")

print(f"\nOverall Whisper vs MMS_Snapped Start Diff on FDR:")
print(f"  Median: {np.median(diffs):.1f} ms | p90: {np.percentile(diffs, 90):.1f} ms")
