# Project Status & Milestone Tracking

**Project**: Track C: Contrastive Speech Analytics & Temporal Flaw Grounding  
**Hackathon**: Multimodal AI Hackathon 2026  
**Last Updated**: Final Evaluation & System Integration Gate  
**All Benchmark Metrics**: Strictly sourced from `results/benchmark.json` via `dataset_tools/run_benchmark.py`

---

## 📋 Comprehensive Status Table

| Item | Description | Status | Raw Evidence / Verification |
| :--- | :--- | :---: | :--- |
| **1. Metrics Bug Fix** | 1-to-1 Hungarian matching (IoU $\ge 0.3$ and $0.5$), eliminated $>100\%$ precision bug. Single script writes `results/benchmark.json`. | **PASS** | `dataset_tools/run_benchmark.py` uses `scipy.optimize.linear_sum_assignment`. Precision $\le 100.0\%$ for all flaw types (`monotone`: 100.0%, `rushed`: 96.4%, `drag_slow`: 83.3%, `inappropriate_pause`: 45.0%). Detections match total: 115 detected, 85 matched at IoU $\ge 0.3$, 76 at IoU $\ge 0.5$. |
| **2. Diagnostic on 33 Far-from-GT Detections** | Full-chain null control at identity; cross-seed checks; explain vintage noise and disable artefact flaw in contrastive mode. | **PASS** | Full-chain null control yielded 0.21 flags/min (1 flag in 290s). 23 of 33 far-from-GT flags were `breathy_unclear` triggered by window shifts over unvoiced consonants on historical noise floors. `breathy_unclear` disabled in contrastive mode in `backend/pipeline/grounding.py` and documented in `docs/decisions/007-disable-breathy-in-contrastive.md`. |
| **3. Boundary Accuracy & Edge Trimming** | Single vs merged regions start/end errors; trim merged regions to flagged words; penalize all-GT misses with 2000 ms. | **PASS** | Merged regions trimmed to extent of flagged words. Single-flaw regions: median start 200.0 ms (p90 928.2 ms), median end 200.0 ms (p90 1030.2 ms). Merged regions: median start 223.0 ms (p90 1506.2 ms), median end 260.0 ms (p90 1312.2 ms). All-GT flaws penalized (2000 ms penalty on misses): median start 1005.0 ms, p90 2000.0 ms. Mean IoU across all 150 GT flaws: 0.440. |
| **4. Monotone Score Calibration** | Isotonic regression fit on Tuning speeches only, evaluated on Held-Out FDR. | **PASS** | Monotone isotonic calibration maps scores to full 0–100 scale: JFK Moon L4 94.9 $\to$ L0 38.3; FDR L4 94.9 $\to$ L0 27.5. Monotonic pairwise ranking accuracy: 97.78% (95% bootstrap CI: [95.83%, 100.0%], 2 violations / 90 pairs). Tables in `results/benchmark.json`. |
| **5. Dashboard Revamp** | No mock data; contrastive default; hatched GT bars; gradient view; secondary merged deviations; limitations panel; dark theme; `plotly.js-basic-dist`. | **PASS** | Deleted `mock_result.json`. Bundle uninstalled and replaced with `plotly.js-basic-dist`. `tsc && vite build` built in 58.73s. Added `GroundTruthTable.tsx`, hatched bars in `WaveformViewer.tsx`, `LimitationsPanel.tsx`, and secondary merged deviations in `CausalExplanationCard.tsx`. |
| **6. Live Upload Path & Failure Handling** | End-to-end async API flow; 60s latency breakdown; failure handling (silence, 10-min file, stereo downmix, format checks). | **PASS / CONDITIONAL** | Async API flow verified (`/analyze` $\to$ `/jobs/{id}` $\to$ `/results/{id}`). Failure handling all passed (silent file 400 rejection, 10-min file rejection, stereo 2-channel downmix, severe transcript mismatch). 60s audio latency without cache is 110.51s (FAIL vs 60s CPU target due to MMS_FA); with SHA-256 precomputation cache: 0.01s (PASS). |
| **7. Dataset Packaging** | 75 recordings packaged with SHA-256 manifest, TextGrids, splits, ZIP archive, `validate_dataset.py` run on all 75 files. | **PASS** | Generated 95 Praat TextGrids. `dist/speech_prosody_benchmark_v1.zip` created (119,109,722 bytes, 113.59 MB, SHA-256: `4ba0eac057e013b14a97c2c2e99de5154834b9bdc5dbb7e527172e1871d64e6b`). `validate_dataset.py` successfully validated all 75 files, word monotonicity, non-overlap, and self-recordings protocol. |
| **8. Technical Documentation (Facts Only)** | Max 6 pages; zero manual metrics; Mermaid architecture diagram; failures included; exported to PDF. | **PASS** | `dataset_tools/generate_technical_doc.py` created `docs/technical_doc.md` reading strictly from `results/benchmark.json`. Generated `docs/technical_doc.html` and exported `docs/technical_doc.pdf` (259,195 bytes) via headless Microsoft Edge. Includes all gate failures honestly. |
| **9. Reproducibility & Docker Status** | Docker status honest; fresh clone instructions in README; pinned dependencies; fixed seeds. | **PASS / NOT RUN** | Dependencies pinned in `requirements.txt`. Seeds fixed (0, 1, 2). Fresh clone instructions added to `README.md`. Docker engine status: **NOT RUN** (Docker Desktop daemon not running on host machine: `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`). |

---

## 🎯 Benchmark Summary (IoU $\ge 0.3$ and $0.5$)

```json
{
  "total_recordings": 75,
  "l0_l1_recall_03": "74.3% (Target 80.0% -> FAIL)",
  "l0_l1_recall_05": "68.6%",
  "null_injection_fp_rate": "0.21 flags/min (Target <= 2.0 -> PASS)",
  "level4_clean_fp_rate": "0.00 flags/min (Target <= 2.0 -> PASS)",
  "pairwise_ranking_accuracy": "97.78% (95% CI: [95.83%, 100.0%])",
  "matched_ious_mean": 0.776,
  "matched_ious_median": 0.810,
  "all_gt_mean_iou": 0.440,
  "dataset_zip_sha256": "4ba0eac057e013b14a97c2c2e99de5154834b9bdc5dbb7e527172e1871d64e6b"
}
```
