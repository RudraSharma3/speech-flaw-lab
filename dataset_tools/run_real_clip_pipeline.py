"""
Executes real pipeline and forced alignment on the extracted 70s JFK Moon Speech excerpt.
Outputs full Result JSON and prints:
1. Alignment details & word intervals
2. First 5 and last 5 words with timestamps
3. 3 sampled frames of F0 (semitones) and Energy (dB)
4. Grounded flaws list
"""

import json

from backend.pipeline.align import align_audio_with_transcript
from backend.pipeline.orchestrator import run_speech_pipeline

audio_path = "data/processed/jfk_rice_excerpt_real.wav"
transcript = (
    "We choose to go to the moon . We choose to go to the moon in this decade and do the other things , "
    "not because they are easy , but because they are hard , because that goal will serve to organize and "
    "measure the best of our energies and skills , because that challenge is one that we are willing to accept , "
    "one we are unwilling to postpone , and one which we intend to win , and the others , too ."
)

print(f"[INFO] Running forced alignment on {audio_path}...")
alignment = align_audio_with_transcript(audio_path, transcript, sr=16000, audio_duration_s=70.0)

print(f"[OK] Alignment Engine Used: {alignment.engine_used}")
print(f"[OK] Total Words Aligned: {len(alignment.words)}")
print("\n--- FIRST 20 WORD INTERVALS (from Alignment) ---")
for i, w in enumerate(alignment.words[:20]):
    print(f"  Word #{i:02d}: {w['text']:15s} [{w['start']:6.3f}s -> {w['end']:6.3f}s] (dur: {w['duration']:.3f}s)")

print("\n[INFO] Running Master Pipeline Orchestrator on real JFK audio...")
result = run_speech_pipeline(
    audio_source=audio_path,
    transcript=transcript,
    filename="jfk_rice_excerpt_real.wav",
    reference_id=None,
)

# Save result JSON
out_json_path = "data/cached_results/jfk_moon_canonical_real_result.json"
with open(out_json_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)
print(f"\n[OK] Pipeline output saved to {out_json_path}")

words = result["words"]
print("\n--- FIRST 5 WORDS ---")
for w in words[:5]:
    print(f"  #{w['index']:02d} {w['text']:12s} [{w['start']:.3f}s -> {w['end']:.3f}s] F0_range={w['f0_range_st']}st, Energy={w['energy_mean_db']}dB, Rate={w['articulation_rate']}syl/s")

print("\n--- LAST 5 WORDS ---")
for w in words[-5:]:
    print(f"  #{w['index']:02d} {w['text']:12s} [{w['start']:.3f}s -> {w['end']:.3f}s] F0_range={w['f0_range_st']}st, Energy={w['energy_mean_db']}dB, Rate={w['articulation_rate']}syl/s")

series = result["series"]
t_arr = series["t"]
mid_idx = len(t_arr) // 2
sample_indices = [int(len(t_arr) * 0.15), mid_idx, int(len(t_arr) * 0.85)]

print("\n--- 3 SAMPLED TIME-SERIES FRAMES ---")
for idx in sample_indices:
    t_val = t_arr[idx]
    f0_val = series["f0_st"][idx]
    e_val = series["energy_db"][idx]
    r_val = series["rate"][idx]
    p_mask = series["pause_mask"][idx]
    f0_str = f"{f0_val:+.2f} st" if f0_val is not None else "Unvoiced"
    print(f"  Frame at t={t_val:.2f}s: F0={f0_str:12s}, Energy={e_val:+.2f} dB, Rate={r_val:.2f} syl/s, Pause={p_mask}")

print("\n--- GROUNDED FLAWS DETECTED ON REAL AUDIO ---")
flaws = result["flaws"]
print(f"Total Flaws Found: {len(flaws)}")
for f in flaws:
    print(f"  • [{f['start_s']:.2f}s - {f['end_s']:.2f}s] {f['flaw_type']:20s} (Severity {f['severity']}): \"{f['words']}\"")
    print(f"    Rationale: {f['rationale_text']}")

print("\n--- DETERMINISTIC RUBRIC SCORES ---")
print(f"Overall Score: {result['scores']['overall']}/100 (Grade: {result['scores']['grade']}, Quality Level: {result['scores']['quality_level_est']})")
for dim in result["scores"]["dimensions"]:
    print(f"  • {dim['name']:35s}: {dim['score']:5.1f}/100 (Metric raw: {dim['metric_raw']}, z: {dim['metric_z']:+.2f})")
