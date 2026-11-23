# Project Status & Milestone Tracking (Final Gate & Pre-Submission Protocol)

**Project**: Track C: Contrastive Speech Analytics & Temporal Flaw Grounding  
**Hackathon**: Multimodal AI Hackathon 2026  
**Evaluation Gate**: Short Final Round — Mock Audio Purge, Pre-Flight Validator & Submission Protocol  
**Tag Status**: `v1.0` deleted (will be recreated by the user after real participant audio is ingested)  
**Self-Recordings Status**: **NOT YET INGESTED** (Waiting for real participant audio)

---

## 📋 Short Final Round Verification Matrix

| Item | Requirement | Status | Raw Evidence / Verification |
| :--- | :--- | :---: | :--- |
| **1. Mock Audio Purge & Live Path Calibration** | List every `mock_*` or synthetic file. Delete or replace with real clips (e.g. `data/injected/` Level 4). Re-run smoke test with real clip. Explain why ideal clip scored 77.5 / B in live path vs 94.9 in benchmark. Fix live path so no-reference upload is clearly labelled "coarse screening" and with-reference runs contrastive. | **PASS** | • Deleted all `data/demo_audio/mock_jfk_moon_level*.wav` and `dataset_tools/rename_mock_files.py`.<br>• Replaced with real recordings from `data/injected/`: `jfk_moon_1962_level_0.wav` through `level_4.wav` (2.24 MB each).<br>• Docker smoke test updated to use flawed clip `jfk_moon_1962_level_1.wav` against reference `jfk_moon_1962_level_4`.<br>• **Root Cause of 77.5 / B in Earlier Run**: Earlier live test submitted a 17.5s audio clip with only a 12-word partial transcript (~4s) and no reference ID. Unaligned trailing audio and reference-free mode compared audio against broad LibriSpeech population priors.<br>• **Fix Implemented**: Updated API schema, `ScoreCard.tsx`, and `scoring.py` to explicitly display `"Contrastive Reference Evaluation"` vs `"Coarse Screening (Reference-Free)"` badges. Disallowed self-comparison as evaluation evidence and added `SELF_COMPARISON_WARNING`. |
| **2. Transcript Check & Diff** | Diff `data/self_recordings/transcript.txt` word-by-word against aligned FDR excerpt (78 words, 45.9s). Make transcript.txt match exactly if different. Fix reading time in `RECORDING_GUIDE.md` (expected reading time 30–45s). Print diff. | **PASS** | • Word-by-word diff executed between `data/alignments/fdr_fear_itself_1933_level_4_alignment.json` and `data/self_recordings/transcript.txt`.<br>• Result: **ZERO DIFF** (exact 78 words matched in identical order and spelling).<br>• Updated `RECORDING_GUIDE.md` to state: *"canonical 78-word historical excerpt... expected reading time is 30 to 45 seconds... matching FDR's deliberate historical delivery of 45.9 seconds"*. |
| **3. Pre-Flight Validator** | `python -m dataset_tools.ingest_self_recordings --check` validates files before processing: prints table with file present, duration, sample rate, channels, clipping %, estimated SNR, voiced fraction, and warnings. Fails early with plain-English fixes. | **PASS** | Implemented `run_preflight_check()` in `dataset_tools/ingest_self_recordings.py`. Tested on empty directory: printed full diagnostics table with all columns, identified missing takes, verified `transcript.txt` (78 words) and `notes.txt`, and exited code 1 with explicit plain-English action items. |
| **4. Robustness Stress Testing** | Test ingestion on temporary stress files created outside `data/` (stereo, 44.1/48 kHz, added noise, DC offset, leading/trailing silence) and delete afterwards. Never write to benchmark.json, catalog, or docs. | **PASS** | Created `C:\Users\HP\temp_stress_test` outside `data/` with: (1) 48 kHz stereo +0.05 DC offset and 4s silence; (2) 44.1 kHz stereo with Gaussian noise (SNR 18 dB); (3) 44.1 kHz mono. All files preprocessed cleanly (resampled to 16 kHz mono, DC offset eliminated to $0.000000$). Temp directory completely deleted. Verified 0 writes to benchmark.json, catalog, or docs. |
| **5. GitHub & Dataset Verification** | Show `git remote -v`. Provide instructions for public repo and push. Verify `.gitignore`: no files > 100 MB, dataset zip not in git, README has Drive placeholder & SHA-256. Add `dataset_tools.fetch_dataset --verify`. | **PASS** | • `git remote -v` executed (stdout empty).<br>• Verified 0 files > 100 MB tracked in git (`Tracked files > 100 MB: []`).<br>• Verified dataset zip is not in git (`dist/` gitignored).<br>• README includes Google Drive link placeholder and SHA-256 checksum.<br>• Created `dataset_tools/fetch_dataset.py`. Ran `python -m dataset_tools.fetch_dataset --verify`: verified `dist/speech_prosody_benchmark_v1.zip` matches canonical SHA-256 (`4ba0eac0...`) with code 0. |
| **6. Submission Runbook & Checklist** | Provide exact commands in order after user recordings. Provide pre-submission checklist (public repo, quick start, Drive link in private window, PDF pages, video length/visibility, YouTube link). | **PASS** | Documented step-by-step runbook and pre-submission checklist below. |

---

## 🔬 Final Fixes Verification Matrix (Pre-Recording Gate)

| Item | Requirement | Status | Raw Evidence / Verification |
| :--- | :--- | :---: | :--- |
| **1. Self-vs-Self Rejection & Flawed Smoke Test** | Remove self-comparison evidence (`level_4` vs `level_4`). Reject or warn when reference and participant audio are same file/envelope. CI smoke test evaluates flawed clip (`level_1`) vs `level_4`, asserting $\ge 1$ flaw and score below level 4. | **PASS** | • Implemented identity detection in `backend/pipeline/orchestrator.py` via SHA-256 and envelope timestamp matching; emits `SELF_COMPARISON_WARNING` and sets `scores['self_comparison_warning']`. Tested: flag emitted on self-run.<br>• Removed self-vs-self score evidence from CI and docs.<br>• Updated `.github/workflows/docker.yml` to POST `jfk_moon_1962_level_1.wav` with `reference_id=jfk_moon_1962_level_4`; asserts `region_id >= 1` and `overall_score < 90.0`. |
| **2. Transcript Coverage & Plausibility** | Compute fraction of audio covered and words/s. If coverage $< 80\%$ or rate is implausible, return visible warning in result and UI (`"transcript covers only X of the audio"`). Reproduce 17.5s audio with 12-word transcript. | **PASS** | • Implemented coverage span calculation in `orchestrator.py`; emits `LOW_TRANSCRIPT_COVERAGE` flag and `scores['transcript_coverage_warning']`.<br>• Added prominent warning banner in `frontend/src/components/ScoreCard.tsx` and re-built frontend (`built in 17.81s`).<br>• Reproduced in test: 17.5s audio with 12 words produced `LOW_TRANSCRIPT_COVERAGE: Transcript covers only 37.5% of the audio (12 words in 17.5s, 0.69 words/s)`. |
| **3. M4A / MP3 Ingest Preprocessing & API** | Test real M4A and MP3 inputs through ingest preprocessing and API (created via ffmpeg in temp folder outside `data/`, deleted after). Show `ffmpeg -version` and Windows locator; add clear error message and README note if missing. | **PASS** | • Implemented `find_ffmpeg_executable()` and seekable temp file decoding in `backend/pipeline/audio.py`.<br>• Verified: locates Gyan.FFmpeg v7.1 at `.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg.exe`.<br>• Tested real M4A (86.8 KB) and MP3 (30.4 KB) in `AppData/Local/Temp`: Ingest preprocessing PASS (160k samples, 16kHz); API upload PASS (`analysis_e7c9a681e3a2643d` score 95.9, `analysis_fb7af2c8a70515bb` score 96.0). Temp folder cleaned up (`Exists? False`). |
| **4. notes.txt Template & Strict Validation** | Reset `notes.txt` to placeholder template without `terror` / `support`. `--check` must fail if template or example words remain, if word not in `transcript.txt`, or if word count doesn't match pause count in `odd_pauses.wav`. | **PASS** | • Reset `data/self_recordings/notes.txt` to clean `[YOUR_PAUSE_WORD_1]`, `[YOUR_PAUSE_WORD_2]`.<br>• Updated `dataset_tools/ingest_self_recordings.py` with `inspect_notes_file()`. Tested `--check`: fails with code 1 (`notes.txt contains unedited template placeholders; Notes words not in transcript`). Tested obsolete words (`terror`, `support`): fails with explicit message. VAD pause counter added for `odd_pauses.wav`. |
| **5. CI Docker Container Proof** | Review `docker.yml` and `Dockerfile` for failures (image size, torch CPU wheel, model download in build, ffmpeg install, port, health check wait loop). Fix them before push. Show workflow file. | **PASS** | • `Dockerfile`: Added CPU-only PyTorch wheel install (`pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu`) reducing image size by ~3 GB; configured explicit bake paths `TORCH_HOME` and `HF_HOME`.<br>• `.github/workflows/docker.yml`: Extended health check wait loop from 30s to 60s with `docker compose logs` failure dump; updated smoke test to assert flawed clip detection vs reference. |
| **6. README Quick Start Update** | Update README with: Python 3.11, ffmpeg install on Windows (`winget install Gyan.FFmpeg`), frontend build, running API, running benchmark, dataset download. | **PASS** | Updated `README.md` `## ⚡ Quick Start` covering: (1) Prerequisites (Python 3.11, winget Gyan.FFmpeg, Node 20); (2) Environment setup with CPU wheels; (3) Frontend build (`npm run build`); (4) Running unified API (`uvicorn backend.app.main:app --port 8000`); (5) Running benchmark (`python -m dataset_tools.run_benchmark`); (6) Dataset download verification (`dist/speech_prosody_benchmark_v1.zip` SHA-256). |

---

## 🚀 Post-Recording Runbook (Exact Commands in Order)

Once participant audio files (`take_a.wav`, `take_b.wav`, `monotone.wav`, `rushed.wav`, `odd_pauses.wav`, `notes.txt`) are recorded into `data/self_recordings/`:

### Step 1: Pre-Flight Audio Diagnostics
```bash
python -m dataset_tools.ingest_self_recordings --check
```
- **What it outputs**: Formatted table with duration, sample rate, channels, clipping %, SNR, voiced fraction, and warnings. Exits `0` if all checks pass.

### Step 2: Automated Ingestion & Evaluation
```bash
python -m dataset_tools.ingest_self_recordings
```
- **What it outputs**: Normalizes audio, aligns speech, verifies Take B independence (cross-correlation), computes false-positive rate (flags/min), evaluates flaw detection vs `notes.txt`, runs Take A vs historical FDR cross-speaker comparison, updates `results/benchmark.json`, and caches results in `data/cached_results/`.

### Step 3: Regenerate Documentation & Technical Report PDF
```bash
python -m dataset_tools.generate_technical_doc
```
- **What it outputs**: Updates `docs/technical_doc.md` and generates `docs/technical_doc.pdf` with Section 7 populated from `benchmark.json`. Verifies PDF page count ($\le 6$ pages).

### Step 4: Verify Benchmark Integrity Gates
```bash
python -m dataset_tools.validate_dataset
```
- **What it outputs**: Validates all 75 dataset files, self-recordings, alignments, TextGrids, and boundary constraints.

### Step 5: Commit Real Ingestion Results & Tag Release
```bash
git add data/self_recordings/ data/cached_results/ results/benchmark.json docs/ README.md
git commit -m "feat: ingest participant recordings and finalize benchmark results"
git tag v1.0
```

---

## 🌐 GitHub Remote Setup Instructions

Because no remote is currently attached to this repository (`git remote -v` returned empty):

1. **Create a Public GitHub Repository**:
   - Go to [https://github.com/new](https://github.com/new).
   - Set Repository Name: `speech` (or your preferred name).
   - Set Visibility: **Public**.
   - Do **NOT** initialize with README, `.gitignore`, or license (the repository already has them).
2. **Add Remote and Push**:
   ```bash
   git remote add origin https://github.com/<YOUR-USERNAME>/speech.git
   git branch -M master
   git push -u origin master
   git push origin --tags
   ```

---

## 📋 Final Pre-Submission Checklist

- [ ] **Repository Public**: Verify the GitHub repository URL is accessible without logging in.
- [ ] **README Quick Start**: Ensure the `README.md` Docker and fresh-clone instructions match the published repo.
- [ ] **Google Drive Dataset Link**:
  - Upload `dist/speech_prosody_benchmark_v1.zip` to Google Drive.
  - Set sharing to: **Anyone with the link can view**.
  - Test opening the link in an **Incognito / Private browser window** to ensure no login is requested.
  - Replace the placeholder link in `README.md` and `docs/dataset_card.md`.
- [ ] **Technical Doc PDF**: Verify `docs/technical_doc.pdf` page count is $\le 6$ pages (currently 4 pages).
- [ ] **Demonstration Video**:
  - Video length: 4 to 6 minutes.
  - Visibility: **Public** or **Unlisted** on YouTube (not Private).
  - Add the YouTube video link to `README.md` and submission portal.
- [ ] **Git Tag**: Ensure `git tag v1.0` has been pushed: `git push origin v1.0`.
