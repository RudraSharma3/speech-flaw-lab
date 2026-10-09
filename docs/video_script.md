# Video Demonstration Script: Contrastive Speech Analytics & Temporal Flaw Grounding

**Hackathon**: Multimodal AI Hackathon 2026 — Track C Submission  
**Target Duration**: 4 – 6 Minutes (approx. 5:00)  
**Presenter Tone**: Authoritative, technically precise, evidence-grounded. Zero hype; exact metrics read directly from `results/benchmark.json`.

---

## 📋 Precomputed Samples & Live Upload Specification

### Precomputed Samples in Catalog (Immediate Zero-Latency Playback)
1. `jfk_moon_1962_level_4_seed42`: Pristine canonical baseline (Calibrated Score: **94.9**, Raw: 96.5, Flags/min: **0.00**).
2. `jfk_moon_1962_level_3_seed42`: Near-perfect perturbation (Calibrated Score: **84.5**, Raw: 94.9, Undetected L3 control).
3. `jfk_moon_1962_level_2_seed42`: Slightly flawed take (Calibrated Score: **75.0**, Raw: 88.5, 2 GT flaws).
4. `jfk_moon_1962_level_1_seed42`: Flawed take (Calibrated Score: **45.0**, Raw: 71.4, 3 GT flaws: drag, monotone, pause).
5. `jfk_moon_1962_level_0_seed42`: Egregious take (Calibrated Score: **38.3**, Raw: 70.4, 4 compound flaws).
6. `self_take_b_fp_control`: Independent replicate take (Calibrated Score: **100.0**, Flags/min: **0.00** — False Positive Control).
7. `self_take_monotone`: Out-of-distribution monotone take (Calibrated Score: **73.6**, Pitch Range: 3.2 semitones).
8. `self_take_rushed`: Out-of-distribution rushed take (Calibrated Score: **91.7**, Articulation Rate: 5.4 syl/sec).

### Live Upload Selection (Run Live During Video — Not Cached)
- **Target File**: `data/self_recordings/odd-pauses.wav`
- **Companion Artifacts**: `data/self_recordings/transcript.txt` and `data/self_recordings/notes.txt` (noted pause words: *"support [pause] of"* and *"leadership [pause] in"*).
- **Runtime Latency**: ~40.6 seconds end-to-end on CPU (warmed torchaudio MMS_FA aligner: 36.1s, VAD: 0.13s, DSP features: 4.21s, grounding: 0.05s).
- **UI Experience**: Real-time stage progress displayed (`Ingestion` ➔ `Alignment` ➔ `DSP Feature Extraction` ➔ `Contrastive Grounding`).

---

## 🎬 Act 1: The Dataset & Ground Truth Validation (0:00 – 1:15)

- **[Action / UI Click]**: 
  1. Open browser to `http://localhost:5173`.
  2. Point camera/cursor to the header: *"Track C: Contrastive Speech Analytics"*.
  3. Switch to terminal briefly showing `python -m dataset_tools.validate_dataset` output: `[OK] 75 recordings validated. Zero boundary overlaps. Schema compliant.`

- **[Voiceover]**:
  > *"Welcome to Track C: Contrastive Speech Analytics and Temporal Flaw Grounding.
  > Modern speech evaluation typically relies on black-box LLMs that produce vague feedback, hallucinate non-existent issues, and cannot provide sub-second timestamps.
  > We built a deterministic, zero-LLM architecture that aligns speech against an ideal reference take—or population priors—on a synchronized word-index axis.
  > 
  > To validate this system, we constructed the Contrastive Speech Analytics Dataset (CSAD-2026), consisting of 75 recordings across 5 historical public-domain addresses and 3 random seeds:
  > - 60 recordings across 4 speeches for our Tuning Set: JFK Moon, JFK We Choose, Reagan Challenger, and Reagan Mourning.
  > - 15 recordings strictly reserved as a Held-Out Test Set: FDR's 1933 'Fear Itself' Inaugural Address.
  > 
  > Our synthetic injector creates a 5-tier quality gradient from Level 4 down to Level 0 using Praat pitch resynthesis, rubberband time-stretching, and syntactically anchored pause insertion. Every single injected flaw has an exact microsecond ground truth timestamp, verified by our dataset validator."*

---

## 🎬 Act 2: Stress Test: Levels 4 to 0 Gradient & Monotonicity (1:15 – 2:30)

- **[Action / UI Click]**: 
  1. Click **"Compare Gradient (Levels 4 ➔ 0)"** in the top navigation bar.
  2. Select Speech: **`jfk_moon_1962`**.
  3. Click sequentially on **Level 4**, **Level 3**, **Level 2**, **Level 1**, and **Level 0**.
  4. Toggle the **"Show Ground Truth Overlay"** switch.

- **[Voiceover]**:
  > *"In the Compare Gradient view, we stress-test the model across all five tiers on John F. Kennedy's 1962 Moon speech.
  > 
  > Look at the overall calibrated scores:
  > - Level 4 (Pristine Master): **94.9** (Raw score: 96.5). The Clean False Positive rate across all Level 4 baselines is exactly **0.00 flags per minute**, both on tuning and held-out test sets.
  > - Level 3 (Near Perfect): **84.5**. Notice that Level 3 has 0 detected flaws at IoU $\ge 0.3$. This is by design: Level 3 acts as an acoustic boundary control.
  > - Level 2 (Slightly Flawed): **75.0**. Precision is **50.0%** with 7 matched flaws.
  > - Level 1 (Flawed): **45.0**. Precision reaches **81.4%**, Recall is **77.8%**, and F1 is **79.5%**.
  > - Level 0 (Egregious): **38.3**. Precision is **75.4%**, Recall is **71.7%**, and F1 is **73.5%**.
  > 
  > Across the entire 75-recording benchmark, pairwise ranking monotonicity achieves **97.78%** (only 2 ranking violations across 90 pairwise comparisons, cluster-bootstrap 95% confidence interval [95.83%, 100.00%]).
  > In the full-chain null-injection control—where audio undergoes the identical DSP resynthesis chain with zero flaw parameters—the false positive rate is just **0.21 flags per minute** (1 flag over 290 seconds)."*

---

## 🎬 Act 3: Live Upload of Out-of-Distribution Self-Recording (2:30 – 3:45)

- **[Action / UI Click]**: 
  1. Click **"Upload & Analyze"** in the navigation bar.
  2. Select Mode: **"Contrastive (vs Canonical Reference)"**.
  3. Drag and drop `data/self_recordings/odd-pauses.wav` into the audio dropzone.
  4. Paste the transcript from `data/self_recordings/transcript.txt`.
  5. Select Reference Audio: `data/self_recordings/ideal_take_a.wav`.
  6. Click the blue **"Run Contrastive Analysis"** button.
  7. Point to the live stage-wise progress indicators:
     - `Stage 1/4: Audio Ingestion & Loudness Normalization (-20 LUFS)`
     - `Stage 2/4: torchaudio MMS_FA Forced Alignment`
     - `Stage 3/4: Deterministic DSP Extraction (Praat F0, HNR, MFCCs)`
     - `Stage 4/4: Temporal Deviation Grounding & Causal Explainability`

- **[Voiceover]**:
  > *"Now let's test a completely unseen recording that was NOT in the dataset: my own live voice recording reading the same text, containing deliberate hesitations noted in notes.txt.
  > We submit the live audio against our ideal reference Take A.
  > 
  > Notice the live pipeline speed. 
  > Previously, a 60-second clip took 110 seconds because the alignment model reloaded per request. 
  > By pre-warming torchaudio MMS_FA at server startup, applying PyTorch inference mode, and utilizing full CPU threading, the total processing time drops to **40.6 seconds**—well under the audio duration.
  > 
  > The job completes, and the dashboard immediately loads the interactive WaveSurfer player and acoustic contours."*

---

## 🎬 Act 4: Flaw Click & Structured Causal Explainability (3:45 – 4:45)

- **[Action / UI Click]**: 
  1. Click on the orange **`inappropriate_pause`** region on the WaveSurfer timeline at timestamp `33.79s – 34.94s`.
  2. The waveform player immediately seeks and loops the segment between words **"support"** and **"of"**.
  3. Point to the **Causal Diagnostic Card** on the right side of the screen.
  4. Toggle the **"Spectrogram / MFCC"** toggle in the Acoustic Plots panel to inspect the silence energy gap.
  5. Scroll down to show the **Clarity Panel** (Word HNR: 22.4 dB, Jitter: 0.82%, Shimmer: 3.1%).

- **[Voiceover]**:
  > *"When I click the flagged inappropriate pause region, the waveform seeks directly to 33.79 seconds and zooms into the phrase: 'support [pause] of'.
  > 
  > This exactly matches word #1 in my pre-recorded notes.txt!
  > 
  > Look at the Causal Diagnostic Card. It provides complete physical quantification:
  > - Observed unpunctuated pause duration: **1.15 seconds**
  > - Expected baseline duration: **0.05 seconds**
  > - Statistical Delta: **+1.10 seconds**, corresponding to a robust z-score of **+3.87**
  > - Severity Score: **7.10**
  > 
  > Below the metrics, the card provides deterministic rhetorical explanation:
  > 'Inserting hesitations mid-phrase fractures syntactic chunking and introduces cognitive processing friction for the listener.'
  > 
  > Toggling the Mel Spectrogram and MFCC heatmaps confirms the complete dropout of formant energy during this unpunctuated gap.
  > Notice the Clarity Panel: even though breathy flaw detection is disabled in contrastive mode to avoid vintage recording noise floor artifacts, we compute HNR, jitter, and shimmer per word with an explicit vintage-recording caveat banner."*

---

## 🎬 Act 5: Honest Limitations & Systemic Audit (4:45 – 5:45)

- **[Action / UI Click]**: 
  1. Click the **"System Limitations"** tab or scroll to the limitations banner at the bottom of the page.
  2. Point cursor to the ScoreCard: hover over the badge reading *"calibrated on the injected gradient (tuning speeches)"* to show the uncalibrated score tooltip.
  3. Switch back to terminal to show the clean Docker compose status: `docker compose ps` running single-port FastAPI + static React build.

- **[Voiceover]**:
  > *"To conclude, we present an honest accounting of our system’s boundaries and empirical limitations, documented in our technical report:
  > 
  > 1. **Monotone Recall Ceiling (28.3%)**: While monotone precision is 100.0%, monotone recall reaches only 28.3%. Praat pitch tracking over unvoiced consonants exhibits octave jumps that artificially widen pitch variance, preventing activation on subtle monotone phrases.
  > 2. **Level 3 Undetectability**: Level 3 flaws are undetectable (0.0% recall at IoU $\ge 0.3$), which prevents false positives on pristine Level 4 audio.
  > 3. **L0–L1 Recall Target**: Achieved recall is **74.3%** at IoU 0.3 (and 68.6% at IoU 0.5), falling short of our aspirational 80.0% target due to compound multi-flaw overlap.
  > 4. **Boundary P90 Error**: Boundary error P90 is approximately **1.0 second** (1030 ms end error, 928 ms start error).
  > 5. **Unexplained Far-from-GT Detections**: Exactly **10 far-from-GT detections** remain unexplained across the 75-recording benchmark corpus, caused by localized unvoiced fricative energy spikes.
  > 6. **Calibration Scope**: Overall score calibration is fit on the injected gradient of the 4 tuning speeches; for arbitrary out-of-distribution audio without an identical text baseline, raw uncalibrated scores are displayed on hover.
  > 
  > All code, Docker containers with pre-baked torchaudio MMS_FA weights, and reproducible benchmarks are fully documented under GPL-3.0.
  > Thank you!"*

---

## ⏱️ Video Timing Summary Table

| Section | Target Time | Key Assets & Clicks | Exact Numbers Read from `benchmark.json` |
| :--- | :---: | :--- | :--- |
| **Act 1: Dataset & Validation** | 0:00 – 1:15 | Hero page, `validate_dataset` terminal log | 75 recordings, 5 baselines, 3 seeds, 60 tuning, 15 held-out FDR |
| **Act 2: Stress Test (L4➔L0)** | 1:15 – 2:30 | Compare Gradient tab, `jfk_moon_1962`, GT overlay | L4: 94.9, L3: 84.5, L2: 75.0, L1: 45.0, L0: 38.3; Monotonicity: 97.78%; Null FP: 0.21 flags/min; Clean FP: 0.00 |
| **Act 3: Live Upload** | 2:30 – 3:45 | Upload view, `odd-pauses.wav`, stage progress bar | Latency: 40.6s total (MMS_FA: 36.1s vs 100.5s before); CPU threads: full core count |
| **Act 4: Flaw Click & Rationale** | 3:45 – 4:45 | Waveform seek to 33.79s, Causal Card, Mel toggle | Pause: 1.15s vs 0.05s baseline, $\Delta = +1.10\text{s}$, $z = +3.87$, severity: 7.10 |
| **Act 5: Limitations & Audit** | 4:45 – 5:45 | Limitations panel, hover tooltip on ScoreCard, Docker | Monotone recall: 28.3%; L3 recall: 0.0%; Boundary P90: ~1.0s; 10 unexplained detections |
