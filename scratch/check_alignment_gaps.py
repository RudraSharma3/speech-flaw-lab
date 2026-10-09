import glob
import json
import os

align_files = glob.glob("data/alignments/*_alignment.json")
print(f"Checking {len(align_files)} alignment files...")

min_gap_all = float("inf")
overlapping_count = 0

for fpath in align_files:
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    words = data.get("words", [])
    for i in range(len(words) - 1):
        gap = words[i+1]["start"] - words[i]["end"]
        if gap < min_gap_all:
            min_gap_all = gap
        if gap < -1e-4:
            overlapping_count += 1
            print(f"Overlap in {os.path.basename(fpath)}: {words[i]['text']} and {words[i+1]['text']} gap={gap:.4f}")

print(f"Min gap across all alignments: {min_gap_all:.4f} s")
print(f"Overlapping word pairs: {overlapping_count}")
