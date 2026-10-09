import os

import numpy as np
import scipy.signal
import soundfile as sf

raw_mp3 = "data/raw/jfk_rice_1962.mp3"
out_wav = "data/processed/jfk_rice_excerpt_real.wav"
os.makedirs("data/processed", exist_ok=True)

# Read full audio
print("[INFO] Loading real JFK Rice Address MP3...")
data, sr = sf.read(raw_mp3)

# Convert to mono if stereo
if data.ndim > 1:
    data = np.mean(data, axis=1)

# In the 1060s speech, the Moon section occurs around 520s - 590s (approx 8m40s to 9m50s)
start_sec = 525.0
end_sec = 595.0
clip_data = data[int(start_sec * sr) : int(end_sec * sr)]

# Resample from 44100 to 16000
target_sr = 16000
num_target_samples = int(len(clip_data) * target_sr / sr)
resampled = scipy.signal.resample(clip_data, num_target_samples)

# Normalize amplitude
peak = np.max(np.abs(resampled))
if peak > 0:
    resampled = resampled / peak * 0.90

# Save 16-bit 16kHz mono WAV
int16_audio = (resampled * 32767.0).astype(np.int16)
sf.write(out_wav, int16_audio, target_sr, subtype="PCM_16")

print(f"[OK] Extracted real JFK excerpt ({end_sec - start_sec:.1f}s) to {out_wav}, sample_rate={target_sr}")
