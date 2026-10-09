import json
import os
import sys
import numpy as np

sys.path.insert(0, ".")
from backend.pipeline.orchestrator import run_speech_pipeline

rec_path = "data/injected/reagan_challenger_1986_level_2_s1.wav"
ref_path = "data/processed/reagan_challenger_excerpt_real.wav"

with open("data/manifests/real_speech_manifest.json") as f:
    manifest = json.load(f)
reagan_meta = next(s for s in manifest if s["speech_id"] == "reagan_challenger_1986")
transcript = reagan_meta["transcript"]

# 1. Run reference
ref_res = run_speech_pipeline(ref_path, transcript, filename="reagan_ideal.wav")
ref_words = ref_res["words"]

# 2. Run level_2_s1 contrastively vs ref
mod_res = run_speech_pipeline(
    rec_path, transcript, filename="reagan_l2_s1.wav",
    reference_words=ref_words, reference_id="reagan_ideal"
)

print(f"Detected flaws in reagan_l2_s1: {len(mod_res['flaws'])}")
for f in mod_res["flaws"]:
    print(f"  {f['flaw_type']} [{f['start_s']:.2f}-{f['end_s']:.2f}] z={f.get('z_score', 0):.2f}")

# Check words at 2.7s - 7.0s
print("\nWord-level HNR comparison for first 15 words:")
for i in range(min(15, len(mod_res["words"]), len(ref_words))):
    mw = mod_res["words"][i]
    rw = ref_words[i]
    print(f"  [{mw['text']:<12}] mod HNR={mw.get('hnr_mean_db',0):.1f}dB, ref HNR={rw.get('hnr_mean_db',0):.1f}dB, z_hnr={mw['z_by_feature'].get('hnr_mean_db_z', 0)}")
