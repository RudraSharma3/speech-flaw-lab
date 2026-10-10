# Video Demonstration Script: Contrastive Speech Analytics & Temporal Flaw Grounding

**Hackathon**: Multimodal AI Hackathon 2026 — Track C Submission  
**Target Duration**: 4 – 6 Minutes (approx. 5:00)  
**Presenter Tone**: Authoritative, technically precise, evidence-grounded. Zero hype; exact metrics read directly from `results/benchmark.json`.

---

## 📋 Precomputed Samples & Live Upload Specification

### Precomputed Samples in Catalog (Immediate Zero-Latency Playback)
1. `jfk_moon_1962_level_4`: Pristine canonical baseline (Calibrated Score: **94.9**, Raw: 96.5).
2. `jfk_moon_1962_level_3`: Near-perfect perturbation (Calibrated Score: **84.5**, Raw: 94.9, Undetected L3 control).
3. `jfk_moon_1962_level_2`: Slightly flawed take (Calibrated Score: **75.0**, Raw: 88.5, 2 GT flaws).
4. `jfk_moon_1962_level_1`: Flawed take (Calibrated Score: **45.0**, Raw: 71.4, 3 GT flaws: drag, monotone, pause).
5. `jfk_moon_1962_level_0`: Egregious take (Calibrated Score: **38.3**, Raw: 70.4, 4 compound flaws).
6. `reagan_challenger_1986_level_1`: Challenger address excerpt (Calibrated Score: **45.0**).
7. `fdr_fear_itself_1933_level_1`: FDR inaugural address held-out test excerpt (Calibrated Score: **45.0**).
8. `reagan_mourning_1986_level_1`: Memorial opening excerpt (Calibrated Score: **55.0**).
9. `jfk_we_choose_1962_level_1`: Rice stadium climax excerpt (Calibrated Score: **40.8**).

### Self-Recordings Status
> **Status: NOT YET INGESTED**  
> (Awaiting participant audio recording drop into `data/self_recordings/` as specified in `RECORDING_GUIDE.md`.)

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

## 🎬 Act 2: Stress Test: Levels 4 to 0 Gradient & Ranking Monotonicity (1:15 – 2:30)

- **[Action / UI Click]**: 
  1. Click **"Compare Gradient (Levels 4 ➔ 0)"** in the top navigation bar.
  2. Select Speech: **`jfk_moon_1962`**.
  3. Click sequentially on **Level 4**, **Level 3**, **Level 2**, **Level 1**, and **Level 0**.
  4. Toggle the **"Show Ground Truth Overlay"** switch.

- **[Voiceover]**:
  > *"In the Compare Gradient view, we stress-test the model across all five tiers on John F. Kennedy's 1962 Moon speech.
  > 
  > Look at the overall calibrated scores:
  > - Level 4 (Pristine Master): **94.9** (Raw score: 96.5).
  > - Level 3 (Near Perfect): **84.5**. Notice that Level 3 has 0 detected flaws at IoU $\ge 0.3$. This is by design: Level 3 acts as an acoustic boundary control.
  > - Level 2 (Slightly Flawed): **75.0**. Precision is **50.0%** with 7 matched flaws.
  > - Level 1 (Flawed): **45.0**. Precision reaches **81.4%**, Recall is **77.8%**, and F1 is **79.5%**.
  > - Level 0 (Egregious): **38.3**. Precision is **75.4%**, Recall is **71.7%**, and F1 is **73.5%**.
  > 
  > Across the entire 75-recording benchmark, pairwise ranking accuracy achieves **97.78%** (only 2 ranking violations across 90 pairwise comparisons, cluster-bootstrap 95% confidence interval [95.83%, 100.00%]).
  > In the full-chain null-injection control—where audio undergoes the identical DSP resynthesis chain with zero flaw parameters—the false positive rate is just **0.21 flags per minute** (1 flag over 290 seconds)."*

---

## 🎬 Act 3: Live Upload & Pipeline Latency (2:30 – 3:45)

- **[Action / UI Click]**: 
  1. Click **"Upload & Analyze"** in the navigation bar.
  2. Select Mode: **"Contrastive (vs Canonical Reference)"**.
  3. Demonstrate the live upload interface with a candidate speech file.
  4. Point to the live stage-wise progress indicators:
     - `Stage 1/4: Audio Ingestion & Loudness Normalization (-20 LUFS)`
     - `Stage 2/4: torchaudio MMS_FA Forced Alignment`
     - `Stage 3/4: Deterministic DSP Extraction (Praat F0, HNR, MFCCs)`
     - `Stage 4/4: Temporal Deviation Grounding & Causal Explainability`

- **[Voiceover]**:
  > *"Now let's examine the live upload architecture.
  > An uploaded audio file is evaluated against a selected reference take.
  > 
  > Previously, aligning a 60-second clip took 100 seconds because the acoustic aligner was re-instantiated on every request.
  > By pre-warming torchaudio MMS_FA at startup, running under PyTorch inference mode, and setting thread counts to the CPU core count, the total end-to-end processing latency drops to **40.6 seconds** on CPU (alignment: 36.1s, DSP features: 4.2s)—comfortably under the 60-second audio duration.
  > 
  > Real-time progress is streamed via the stage-wise progress callback."*

---

## 🎬 Act 4: Flaw Click & Structured Causal Explainability (3:45 – 4:45)

- **[Action / UI Click]**: 
  1. Select sample `jfk_moon_1962_level_1` from the catalog.
  2. Click on the highlighted flaw region on the WaveSurfer timeline.
  3. The player seeks to the segment and zooms into the affected phrase.
  4. Point to the **Causal Diagnostic Card** on the right side of the screen.
  5. Toggle the **"Spectrogram / MFCC"** toggle in the Acoustic Plots panel to inspect the frequency envelope.
  6. Scroll down to show the **Clarity Panel** (Word HNR, Jitter, Shimmer with vintage-recording caveat banner).

- **[Voiceover]**:
  > *"When I click a flagged flaw region on the WaveSurfer timeline, the player seeks directly to the start timestamp and zooms into the affected phrase.
  > 
  > The Causal Diagnostic Card provides physical quantification:
  > - Observed metric value vs canonical reference baseline
  > - Statistical Delta ($\Delta$) and robust z-score
  > - Calculated severity score ($S = \Delta t \cdot |z| \cdot w$)
  > - Rhetorical 'Why It Hurts' explanation
  > 
  > Toggling the Mel Spectrogram and MFCC heatmaps reveals the acoustic perturbation.
  > Notice the Clarity Panel: even though breathy flaw detection is disabled in contrastive mode to prevent triggering on vintage recording noise floors, we compute HNR, jitter, and shimmer per word with an explicit vintage-recording caveat banner."*

---

## 🎬 Act 5: Participant Self-Recordings & System Limitations (4:45 – 5:45)

- **[Action / UI Click]**: 
  1. Click **"System Limitations"** tab.
  2. Point cursor to the ScoreCard: hover over the badge reading *"calibrated on the injected gradient (tuning speeches)"* to show the raw score tooltip.
  3. Show the `data/self_recordings/RECORDING_GUIDE.md` file in the repository.

- **[Voiceover]**:
  > *"To ensure scientific integrity, we provide a structured protocol for out-of-distribution evaluation in `data/self_recordings/RECORDING_GUIDE.md`.
  > 
  > [AFTER RECORDINGS — to be populated once participant audio takes are dropped]:
  > - When real user takes are ingested, `dataset_tools.ingest_self_recordings` verifies Take B is a genuinely independent recording via normalized cross-correlation.
  > - It evaluates Take B vs Take A as a true independent false-positive control, evaluates deliberate flawed takes against Take A, and reports cross-speaker comparison against the orator's original recording of the same text.
  > - Until user audio is provided, self-recordings are marked strictly as NOT YET INGESTED.
  > 
  > Finally, we report our system boundaries honestly from benchmark evidence:
  > 1. **Monotone Recall Ceiling (28.3%)**: While precision is 100.0%, monotone recall reaches 28.3% because Praat pitch tracking over unvoiced consonants exhibits octave jumps that artificially widen pitch variance.
  > 2. **Level 3 Undetectability**: Level 3 flaws are undetectable (0.0% recall at IoU $\ge 0.3$), acting as an acoustic boundary control.
  > 3. **L0–L1 Recall Target**: Achieved recall is **74.3%** at IoU 0.3 (and 68.6% at IoU 0.5), falling short of our 80.0% target due to compound multi-flaw overlaps.
  > 4. **Boundary P90 Error**: Boundary error P90 is approximately **1.0 second** (1030 ms end error, 928 ms start error).
  > 5. **Unexplained Far-from-GT Detections**: Exactly **10 far-from-GT detections** remain unexplained across the 75-recording benchmark corpus.
  > 6. **Calibration Scope**: Score calibration is fit on the injected gradient of the 4 tuning speeches; for arbitrary out-of-distribution audio without an identical text baseline, raw uncalibrated scores are displayed on hover.
  > 
  > Thank you!"*

---

## ⏱️ Video Timing Summary Table

| Section | Target Time | Key Assets & Clicks | Exact Numbers Read from `benchmark.json` |
| :--- | :---: | :--- | :--- |
| **Act 1: Dataset & Validation** | 0:00 – 1:15 | Hero page, `validate_dataset` terminal log | 75 recordings, 5 baselines, 3 seeds, 60 tuning, 15 held-out FDR |
| **Act 2: Stress Test (L4➔L0)** | 1:15 – 2:30 | Compare Gradient tab, `jfk_moon_1962`, GT overlay | L4: 94.9, L3: 84.5, L2: 75.0, L1: 45.0, L0: 38.3; Pairwise Ranking Accuracy: 97.78%; Null FP: 0.21 flags/min |
| **Act 3: Live Upload** | 2:30 – 3:45 | Upload view, stage progress bar | Latency: 40.6s total on CPU (MMS_FA: 36.1s vs 100.5s before); CPU threads: full core count |
| **Act 4: Flaw Click & Rationale** | 3:45 – 4:45 | Waveform seek, Causal Card, Mel toggle, Clarity panel | $S = \Delta t \cdot \|z\| \cdot w$, Mel / MFCC heatmaps |
| **Act 5: Self-Recordings & Limitations** | 4:45 – 5:45 | `RECORDING_GUIDE.md`, Limitations panel, hover tooltip on ScoreCard | Self-recordings: NOT YET INGESTED; Monotone recall: 28.3%; L3 recall: 0.0%; Boundary P90: ~1.0s; 10 unexplained detections |
