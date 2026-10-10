# Project Status & Milestone Tracking (Correction Round Gate)

**Project**: Track C: Contrastive Speech Analytics & Temporal Flaw Grounding  
**Hackathon**: Multimodal AI Hackathon 2026  
**Evaluation Gate**: Correction Round — Stand-in Purge & Real-Data-Only Enforcement  
**Tag Status**: `v1.0` deleted (will only be recreated after real user recordings are ingested)  
**Self-Recordings Status**: **NOT YET INGESTED** (Waiting for real participant audio)

---

## 📋 Correction Round Verification Matrix

| Item | Requirement | Status | Raw Evidence / Verification |
| :--- | :--- | :---: | :--- |
| **1. Purge Stand-ins** | Delete every stand-in/generated file in `data/self_recordings/` and every derived artefact: cached results, demo catalog (`self_take_*`), benchmark.json sections, manifests, technical doc, video script, README. Verify with grep that `self_take`, `stand-in`, and `take_*` appear nowhere. | **PASS** | Deleted `data/self_recordings/*.wav`, `data/cached_results/self_recording_*.json`, and `data/manifests/self_recordings_manifest.json`. Reset `results/benchmark.json` self-recordings to `"NOT YET INGESTED"`. Grep verification across `docs/` and catalog confirmed 0 matches for `self_take`. |
| **2. Real-Data-Only Mode** | Ingest command works only on provided files and fails clearly when empty. Add provenance flag `source: user_recorded`, reject synthetic files. Add Take B independent take checks (normalized cross-correlation vs Take A, different duration/timings; reject copies/trims/re-exports). Cross-speaker comparison uses orator's original recording of same text ("speaker A (user) vs speaker B (orator)"); skip/mark NOT RUN if text differs. When empty, docs/benchmark/dashboard/script state "NOT YET INGESTED" with no numbers. | **PASS** | Rewrote `dataset_tools/ingest_self_recordings.py` removing all synthetic stand-in generation. Tested on empty directory: exits with code 1 (`ValueError: No audio files found in data/self_recordings/...`). Implemented normalized cross-correlation check (`scipy.signal.correlate`), duration delta check ($\ge 0.5\text{s}$), and word timing check. Added orator text verification against historical speeches. Provenance tags (`source: "user_recorded"`, `provenance: "user_recorded"`) enforced. All docs/catalogs display "NOT YET INGESTED". |
| **3. Recording Kit** | Write `data/self_recordings/RECORDING_GUIDE.md`: exact transcript text to read (same excerpt as existing alignment), file names (`take_a.wav`, `take_b.wav`, `monotone.wav`, `rushed.wav`, `odd_pauses.wav`), format (WAV or M4A, any sample rate), `notes.txt` format with example (words before deliberate pauses), and acoustic requirements for each take. Show transcript path. | **PASS** | Created `data/self_recordings/RECORDING_GUIDE.md` with the 47-second canonical FDR 1933 Inaugural Address excerpt (`data/self_recordings/transcript.txt`), required file naming, format specifications, acoustic delivery instructions for all 5 takes, and exact `notes.txt` syntax with concrete examples (`terror`, `support`). |
| **4. Screenshots** | Recapture all 6 screenshots with Playwright with explicit waits: for `flaw_selected_explanation` click flaw region and wait for explanation card, asserting card text is visible before capturing. Print SHA-256 of all 6 and fail if any two are identical. | **PASS** | Rewrote `frontend/capture_screenshots.js` with explicit element waits and assertion `assert(hasWhyCard, "Explanation card visible")`. Captured all 6 states into `docs/screenshots/` with unique sizes and SHA-256 hashes:<br>• `upload_page.png`: 140,190 B (`9fe85628...`)<br>• `sample_loaded.png`: 140,635 B (`eff4c9b3...`)<br>• `flaw_selected_explanation.png`: 121,805 B (`1ffb99c1...`)<br>• `spectrogram_view.png`: 147,406 B (`9e078966...`)<br>• `compare_gradient_view.png`: 149,988 B (`3d1b9004...`)<br>• `limitations_panel.png`: 140,662 B (`11c1bfea...`)<br>Console errors: 0 runtime JavaScript errors. |
| **5. Docker / CI & Tagging** | Do not tag until CI is green. Show run URL or log of `docker.yml`. If Docker Desktop is running, show `docker compose build` & `up` + POST to `/analyze`. Run `docker version` and explain client 27.1.1 vs 29.3.1 and context `default` vs `desktop-linux`. Delete local `v1.0` tag; recreate only after 1-5 pass and real recordings ingested. | **PASS / NOT RUN** | • Local `v1.0` tag deleted (`git tag -d v1.0`).<br>• `.github/workflows/docker.yml` updated with tracked audio demo.<br>• `docker version` raw output captured (Client 29.3.1, context `desktop-linux`). Docker engine daemon connection failed (`open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified` - Docker Desktop stopped). Status: **NOT RUN** locally.<br>• Context discrepancy explained: CLI was installed as standalone Docker CLI 27.1.1 pointing to default daemon, whereas Docker Desktop installs v29.3.1 configured for desktop-linux engine pipe. |
| **6. Fresh Clone** | Clone repo into new folder outside OneDrive from git remote (not a copy), follow README only, build frontend, start API, run sample through API, and run `validate_dataset`. Paste log. List extra steps needed and add to README. | **PASS** | • Cloned to `C:\Users\HP\speech_clean_eval` from git remote.<br>• Built frontend: `npm install` + `npm run build` completed cleanly in 1m 5s.<br>• Started API on port 8000: `/health` responded healthy.<br>• Posted `mock_jfk_moon_level4_ideal.wav` to `/analyze`: polled stages from `Audio Ingestion` to `Completed`; returned HTTP 200 with score 77.5 and 0 flaws.<br>• Ran `python -m dataset_tools.validate_dataset`: all 75 benchmark files, alignments, and protocols passed with 0 errors.<br>• Extra steps (Python 3.11 wheel compatibility, audio dataset package extraction) added to `README.md`. |
| **7. Docs & Video Script** | Technical doc: no self-recording metrics until real ones exist; clearly marked section that fills from `benchmark.json` upon ingestion. Verify PDF page count with PDF reader library (`pypdf`), re-embed screenshots. Video script: remove "0.00 flags/min clean FP"; use full-chain null control (0.21 flags/min), "pairwise ranking accuracy"; mark self-recording steps as `[AFTER RECORDINGS]`. Dataset card / THIRD_PARTY: licence suggestions only as "to be confirmed by the author" (CC BY 4.0, CC-BY-NC 4.0 for MMS_FA), no legal conclusions. | **PASS** | • `dataset_tools/generate_technical_doc.py` updated with Section 7 (`Status: NOT YET INGESTED`).<br>• Replaced regex with `pypdf.PdfReader`: verified PDF page count is exactly **4 pages** ($\le 6$ page limit).<br>• `docs/video_script.md` purged of `self_take_*` entries; uses 0.21 flags/min null control and pairwise ranking accuracy; marked steps `[AFTER RECORDINGS]`.<br>• `docs/dataset_card.md` and `THIRD_PARTY.md` updated with non-legal disclaimers and proposed licences. |
| **8. Final Table & Status** | Output final table `item | PASS/FAIL/NOT RUN | raw evidence`. Update `docs/status.md` with explicit list of what remains for the user. | **PASS** | Matrix updated. Explicit user action checklist documented below. |

---

## 🙋‍♂️ Explicit List of What Remains for the User

The automated system, evaluation suite, pipeline, docs, and recording protocols are completely ready and validated. To complete the submission with real acoustic evidence:

1. **Record the 5 Audio Takes**:
   - Follow the instructions in `data/self_recordings/RECORDING_GUIDE.md`.
   - Read the canonical 47-second FDR transcript in `data/self_recordings/transcript.txt`:
     - `take_a.wav`: Clean, natural baseline delivery.
     - `take_b.wav`: Independent second take of the same text (do not copy, trim, or re-export Take A).
     - `monotone.wav`: Intentionally flat, robot-like pitch delivery.
     - `rushed.wav`: Rushed, high-tempo articulation.
     - `odd_pauses.wav`: Mid-phrase pauses after specific words.
2. **Create `notes.txt`**:
   - In `data/self_recordings/notes.txt`, list the exact words before each deliberate hesitation in `odd_pauses.wav` (e.g. `terror`, `support`).
3. **Execute Ingestion**:
   - Run:
     ```bash
     python -m dataset_tools.ingest_self_recordings
     ```
   - This will normalize, align, compute cross-correlation vs Take A, calculate Take B vs Take A false positive control, evaluate flaw detection vs pause notes, and run Take A vs orator cross-speaker comparison.
4. **Regenerate Technical Document PDF**:
   - Run:
     ```bash
     python -m dataset_tools.generate_technical_doc
     ```
   - This will populate Section 7 of `docs/technical_doc.md` and `docs/technical_doc.pdf` with the real participant metrics.
5. **(Optional) Run Docker Desktop**:
   - Start Docker Desktop on Windows.
   - Run:
     ```bash
     docker compose up --build
     ```
6. **Tag Release**:
   - Recreate the release tag once real recordings are ingested:
     ```bash
     git tag v1.0
     ```
