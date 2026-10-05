# Track C Master Plan: Contrastive Speech Analytics & Temporal Flaw Grounding

**Team:** 2 people. **Assumed duration:** \~48 hours (scale the timeline in section 12 if different). **Goal:** score high on every rubric line, not just build something that works.

---

## 1. What the judges score, and what we build for each

| Rubric (weight) | What wins it | Our deliverable |
| --- | --- | --- |
| Data Engineering & Stress Testing (30%) | Clever baselines, clean labels, a real severity gradient | Programmatic flaw injection with exact ground-truth timestamps, plus TTS-voice and human-recorded sets |
| Causal Explainability & Temporal Grounding (25%) | Accurate timestamps, math tied to context | Word-level flaw regions, each with a z-score explanation; measured IoU against ground truth |
| Feature Extraction (20%) | Rigor, stress points, energy contours | STFT/MFCC/F0/rate/pause/clarity features, speaker-normalized |
| Visualization & Dashboard (15%) | Clear time-series and rationale | Waveform + feature tracks + shaded flaw regions + explanation cards |
| Reproducibility & Code Quality (10%) | Clean run, clear instructions | Docker, pinned versions, Makefile, deterministic outputs |

**Core idea:** because we inject the flaws ourselves, we know exactly where they are. That lets us report real accuracy numbers (region IoU, boundary error in ms, severity correlation). Most teams will only show a demo.

---

## 2. System flow (end to end)

```
 Audio + transcript upload
          |
 [1] Ingest: convert to 16 kHz mono WAV, trim, loudness-check
          |
 [2] Forced alignment: word start/end times (+ confidence)
          |
 [3] Feature extraction: F0, energy, rate, pauses, MFCC, clarity, fluency
          |
 [4] Speaker normalization: semitones, dB-relative, self-relative rate
          |
 [5] Compare to baseline: word-level alignment + DTW -> deviation z-scores
          |
 [6] Flaw detection: threshold + merge -> regions (start, end, type)
          |
 [7] Explanation: template filled with real numbers
          |
 [8] Scoring: 6 rubric dimensions -> overall score
          |
 JSON result -> FastAPI -> React dashboard
```

---

## 3. Repository structure

```
speech-flaw-lab/
  data/            raw/ baseline/ mirrors/ labels/ README.md (dataset card)
  src/
    dataset/       build_dataset.py  inject.py  edl.py  tts_voices.py
    align/         aligner.py
    features/      extract.py  normalize.py
    analysis/      compare.py  detect.py  explain.py  score.py
    eval/          evaluate.py  report_figures.py
    api/           main.py  schemas.py
  web/             React + Vite + TypeScript
  docs/            contract.json  report.md  architecture.png
  Dockerfile  docker-compose.yml  Makefile  requirements.txt (pinned)
```

**Git workflow (do this from hour 0):** `main` is always runnable. Each person works on a feature branch (`feat/alignment`, `feat/dashboard`), opens a pull request, the other merges it. Commit small and often. Commit `docs/contract.json` (section 10) in the first hour so both sides build against it.

---

## 4. Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Alignment | WhisperX (wav2vec2 CTC alignment); fallback Montreal Forced Aligner | Word timestamps with confidence; CPU works but is slow, so cache results |
| ASR (fluency check) | Whisper `small`/`base` | Detect inserted fillers and repeats by diffing against the target transcript |
| Features | librosa (STFT, MFCC, RMS), parselmouth (Praat F0, HNR) | Standard, citable, deterministic |
| DSP flaw injection | Praat Manipulation (pitch), librosa/pyrubberband (time-stretch), numpy (gain, silence) | Controlled, parameterized flaws |
| TTS voices | Piper (offline, free) | Different "speakers" for the speaker-agnostic test |
| Backend | FastAPI + Pydantic | Fast to build, auto docs |
| Frontend | React + Vite + TS, wavesurfer.js (regions plugin), Plotly.js | Waveform with clickable regions plus linked time-series |
| Packaging | Docker + docker-compose, pinned `requirements.txt` | Reproducibility criterion |

**Verify on day one:** install WhisperX and parselmouth inside Docker and run each on one file. Install problems are the most common time sink. If WhisperX fails, switch to MFA immediately.

---

## 5. Dataset construction (30% of the score, so spend the most care here)

### 5.1 Baselines ("ideal")

- 8 clips of 45-90 seconds each, 1-2 per delivery style: oratory, declamation, extemporaneous-style, interpretive reading.
- Prefer **public-domain or openly licensed** sources: US government speeches (e.g. presidential addresses), LibriVox readings. Avoid TED (its license forbids derivatives) and check any estate-controlled speech before use. Record the source URL and license of each clip in the dataset card.
- Transcribe with Whisper, then **correct by hand** so the transcript is exact. Align and manually spot-check word boundaries.

### 5.2 Three tiers of "flawed" mirrors

| Tier | How made | Purpose |
| --- | --- | --- |
| 1. DSP-injected | Programmatically alter the baseline audio | Exact ground-truth labels, full severity gradient |
| 2. TTS voices | Synthesize the same transcript in 2-3 Piper voices, then inject flaws | Test speaker-agnostic behavior on different voices |
| 3. Human recordings | Both of you read 6-8 clips with deliberate real flaws; label regions by hand in Audacity/Praat | Show it works on real, messy audio |

### 5.3 Flaw taxonomy and injection

| Flaw | Injection method | Severity 1 (near-perfect) to 5 (botched) |
| --- | --- | --- |
| Pace too fast | Time-stretch a region (keep pitch) | rate x1.1, 1.25, 1.5, 1.8, 2.2 |
| Pace too slow | Time-stretch a region | x0.9, 0.8, 0.65, 0.5, 0.4 |
| Monotone | Praat: scale F0 variation around the median | variance scale 0.8, 0.6, 0.4, 0.2, 0.05 |
| Volume drop / swell | Gain envelope on a region | -2, -4, -7, -10, -14 dB |
| Bad pauses | Delete pauses at punctuation, or insert long pauses mid-phrase | 1 to 5 inserted/removed, longer for higher severity |
| Fillers and repeats | Insert recorded "um/uh" clips; duplicate a word | 1, 2, 3, 5, 8 per clip |

- Each flaw affects one **region** (e.g. 4-12 words) so the detector has something to localize. Severity 1 uses short regions and small parameters, giving the "almost perfect" end of the gradient.
- Also make **composite** mirrors (several flaws mixed) at each severity level.
- **Edit decision list (EDL):** every edit (stretch, insert, delete) is logged. After editing, a function maps original word times to new times, so ground-truth region timestamps stay exact even after the audio's length changes. This is the trickiest part of the dataset code, so write it first and unit-test it.

### 5.4 Size and label schema

- Per speech: 1 baseline, 30 single-flaw mirrors (6 flaws x 5 severities), 5 composites. For 8 speeches that is \~300 clips, plus the TTS and human sets. If time is short, cut to 5 severities x 4 flaws.
- Store audio as 16 kHz mono FLAC. Put the audio on Google Drive with a public link in the README if the repo gets too large (the rules allow it).

```json
{
  "clip_id": "sp03_pace_fast_s4",
  "speech_id": "sp03",
  "tier": 1,
  "baseline_clip": "sp03_baseline",
  "severity": 4,
  "regions": [
    {"type": "pace_fast", "start_s": 12.40, "end_s": 16.10,
     "word_start": 41, "word_end": 58, "params": {"rate_factor": 1.8}}
  ]
}
```

### 5.5 Quality control

- Listen to at least 2 clips per flaw type and severity level. If severity 1 sounds identical to the baseline, widen the parameter gap.
- Script `make dataset` rebuilds everything from raw baselines with a fixed random seed.
- Write the dataset card: sources, licenses, flaw definitions, parameters, label schema, splits.

### 5.6 Splits (decide now, never change later)

- **Tune** thresholds on speeches 1-4. **Test** on speeches 5-8 (never seen during tuning).
- TTS and human sets are test-only.

---

## 6. Feature extraction (20%)

All features come from the aligned audio, at the word level and at a 10 ms frame level for plotting.

| Feature | How | Unit after normalization |
| --- | --- | --- |
| Spectrogram (FFT) | STFT, 25 ms window, 10 ms hop; show under the waveform | dB |
| F0 contour | Praat autocorrelation, 75-500 Hz, voiced frames only | **semitones** re speaker median: `12*log2(f0/median)` |
| Energy | Frame RMS in dB | dB minus speaker median voiced energy |
| Speech rate | Syllables per second per word (CMUdict, vowel-group fallback) | ratio to the speaker's own global rate |
| Pauses | Gap between aligned words (ms) | ms, compared by position (e.g. at commas) |
| Clarity | HNR (Praat), alignment confidence, per-word MFCC distance to baseline | z-score |
| Fluency | Whisper transcript diffed against target: inserted fillers, repeats, dropped words | counts per region |

**Speaker-agnostic normalization (required by the rules):**

1. F0 in semitones and energy relative to the speaker's own median remove most differences between voices.
2. Local contours are compared as *shape* after removing each speaker's own global mean. Speaking slowly overall is a personal trait. A sudden local slowdown is the flaw.
3. Global properties (overall pitch range, overall monotone) are compared against a **pooled reference range** from the good baselines.

---

## 7. Comparison, detection and explanation (25%)

### 7.1 Deviation

1. Align participant words to baseline words using the shared transcript (word index = anchor). Where words were dropped or inserted, use DTW on the MFCC sequence as a fallback.
2. For each word and feature compute `z = (x_participant - x_baseline) / sigma_ref`, where `sigma_ref` is the feature's natural variation across the good baselines (so ordinary variation is not penalized).

### 7.2 Region detection

- Mark a word as deviant when `|z|` exceeds the feature's threshold (start at 2.0, tune on the tuning split).
- Use hysteresis: a region starts at a word above the high threshold and extends while words stay above a lower one (e.g. 1.2). Merge regions closer than 2 words. Drop regions shorter than 3 words.
- Region boundaries snap to word boundaries from the alignment, which gives good temporal precision.
- **Flaw type** = the feature with the largest mean `|z|` in the region (rate -> pace, F0 variance -> monotone, and so on).

### 7.3 Explanation (rule-based, deterministic)

Each region produces a card filled from a template, with real numbers:

> **Words 41-58 (00:12.4-00:16.1): rushed delivery.** Speaking rate 5.8 syl/s vs baseline 3.9 (+49%, z = 3.1). Fast pace shortens pauses and reduces clarity. Slow down at clause boundaries.

- Every card shows: time range, flaw type, measured value, baseline value, % difference, z-score, and one short advice line from a fixed lookup table.
- An LLM may optionally rephrase the advice, but **numbers always come from the code**, never the LLM. Treat this as a stretch goal, because the rule-based version is more reproducible.

---

## 8. Scoring (reproducible rubric)

Six dimensions, each 0-100: **Pace, Pauses, Pitch variation, Volume dynamics, Clarity, Fluency**.

- Dimension score = `100 * exp(-D / tau)`, where `D` is the duration-weighted mean `|z|` over that dimension's features across the whole clip.
- Fit `tau` per dimension on the tuning split so that severity 5 lands below \~30 and severity 1 above \~85.
- Overall score is a weighted average (start with equal weights and state them in the docs).
- Publish the rubric as a table in the report: what each dimension measures, formula, and what a high or low score means.
- Determinism: no randomness in inference, fixed seeds in dataset building, pinned dependency versions. Check that two runs on the same input produce byte-identical JSON.

**Stretch:** a small gradient-boosted regressor that predicts severity from the six dimension scores, evaluated with leave-one-speech-out cross-validation. Compare it to the pure formula in an ablation.

---

## 9. Evaluation (what goes in the report)

| Metric | Definition |
| --- | --- |
| Region precision/recall/F1 | A predicted region matches a ground-truth region at temporal IoU >= 0.5 |
| Boundary error | Mean absolute start/end error in ms for matched regions |
| Flaw-type accuracy | Confusion matrix across the 6 types |
| Severity monotonicity | Spearman rho between true severity and overall score, per speech |
| Speaker-agnostic check | Same metrics on the TTS and human sets, with and without normalization |
| Reproducibility | Two clean-container runs give identical output |

Report results broken down **by severity**. Expect severity 1 (near-perfect) to be hardest, and say so honestly. Honest limits score better than inflated claims. Include a limitations section: synthetic flaws are cleaner than real ones, alignment can fail on badly botched audio, and thresholds depend on the tuning speeches.

---

## 10. API and JSON contract (commit in hour 1)

`POST /analyze` (audio file, transcript text, optional baseline clip id) returns:

```json
{
  "overall_score": 71.4,
  "dimensions": {"pace": 54, "pauses": 80, "pitch": 77, "volume": 88, "clarity": 69, "fluency": 85},
  "words": [{"i": 41, "text": "freedom", "start_s": 12.40, "end_s": 12.78, "conf": 0.93}],
  "tracks": {"t": [0.00, 0.01], "f0_st": [0.0, 0.2], "f0_st_baseline": [0.0, 0.1],
             "energy_db": [0.0, -0.4], "energy_db_baseline": [0.0, 0.1], "rate": [], "rate_baseline": []},
  "flaws": [{"type": "pace_fast", "start_s": 12.4, "end_s": 16.1, "word_start": 41, "word_end": 58,
             "severity_est": 4, "z": 3.1, "explanation": "..."}]
}
```

Also `GET /clips` (dataset browser) and `GET /health`. Make a `mock_result.json` on day one so the frontend never waits for the backend.

---

## 11. Dashboard design

1. **Upload page:** drop audio and paste or upload transcript, optionally pick a baseline from the dataset. Show a progress indicator per pipeline stage.
2. **Results page:**
   - Top: overall score and a radar chart of the six dimensions.
   - Main: waveform (wavesurfer.js) with shaded, color-coded flaw regions. Below it, synchronized tracks (Plotly, shared time axis): F0, energy, rate, pauses, each with the baseline overlaid.
   - Right: list of flaw cards. Clicking one scrolls both views to that region and **plays just that region**.
   - Transcript panel: words colored by deviation, clickable to seek.
3. **Dataset browser:** pick a speech and a severity, play baseline against mirror, and see the labeled regions. This directly supports the 30% dataset score.
4. Keep the design clean and readable. A single accent color, large time axis, and clear legends beat fancy styling.

---

## 12. Timeline and roles

Split by skill. **Person 1:** alignment, features, detection, scoring, evaluation. **Person 2:** dataset building, API, dashboard. Both write docs. Swap if your skills point the other way.

| Hours | Person 1 | Person 2 | Exit criterion |
| --- | --- | --- | --- |
| 0-4 | Repo, Docker, test WhisperX + parselmouth on one file | Pick and download 8 baselines, check licenses, commit contract + mock JSON | Container runs; contract committed |
| 4-12 | Alignment + features on baselines | Transcribe/correct transcripts, write EDL + 2 injectors (pace, volume) | **Vertical slice:** upload a pair, see one flaw on screen |
| 12-24 | Normalization, comparison, detection, explanation | Remaining injectors, TTS voices, label schema, frontend with mock then real data | Full dataset v1 built; dashboard shows real regions |
| 24-34 | Scoring, tune thresholds on speeches 1-4, evaluation on 5-8 | Record human clips + label, dataset browser, polish dashboard | Evaluation table complete |
| 34-42 | Fix failure cases, reproducibility check, ablations | Dataset card, README, deploy/Docker run from clean clone | Fresh machine runs `make demo` |
| 42-48 | Report (6 pages) | Demo video (3-10 min, English, YouTube unlisted), Devpost page | **Submitted with buffer** |

**Rule:** by hour 12 you must have an end-to-end ugly version. After hour 34 add no new features.

---

## 13. Documentation, video and submission

**6-page report outline:** (1) problem and approach, (2) dataset construction and licenses, (3) feature extraction and normalization, (4) detection and explanation method, (5) scoring rubric, (6) evaluation results and limitations.

**Demo video (aim for \~6-7 min):**

- 0:00 problem and idea
- 0:45 dataset: show baseline vs mirror, severities, labels
- 2:00 architecture and pipeline
- 3:15 live demo on a severity-5 clip, click each flaw card
- 4:15 live demo on a near-perfect clip: it still finds the small flaw
- 5:00 human-recorded clip and a different TTS voice
- 5:45 evaluation numbers and honest limitations
- 6:30 reproducibility: `docker compose up` from a clean clone

**Submission checklist (miss one and you may not be judged):**

- [ ] Devpost description complete
- [ ] Public GitHub repo with README: setup, prerequisites, run instructions
- [ ] Dataset (in repo or public Drive link in README)
- [ ] YouTube video is **unlisted or public** (not private), 3-10 min, English audio or subtitles
- [ ] Every teammate has a Devpost account, is added to the project, and uses their real full name

---

## 14. Risks and fallbacks

| Risk | Fallback |
| --- | --- |
| Alignment fails on heavily botched audio | Align with Whisper's own transcript, then fuzzy-match to the target text |
| WhisperX install/CPU speed problems | Switch to Montreal Forced Aligner; cache all alignments |
| Synthetic flaws seem artificial | Human-recorded set (Tier 3) plus honest discussion in limitations |
| Severity 1 undetectable | Report it honestly and show the detection curve by severity |
| Behind schedule | Cut in this order: LLM rephrasing, severity regressor, PDF export, dataset browser, extra flaw types |
| "Works on my machine" | Docker from hour 0; test from a clean clone before submitting |

---

## 15. Definition of done

- [ ] `make dataset` builds the full dataset from raw baselines
- [ ] `docker compose up` serves a working dashboard
- [ ] Upload any audio + transcript, get flagged regions with timestamps and explanations
- [ ] Evaluation table (IoU, boundary error, severity correlation) in the report
- [ ] Two runs give identical results
- [ ] All submission items complete, with a buffer of at least 2 hours

*Caveat: this is a plan, not tested code. Thresholds, library behavior on CPU, and flaw parameters need tuning against real output, so budget time for it (hours 24-34).*
