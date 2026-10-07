# Video Demonstration Script: Contrastive Speech Analytics (Track C)

**Target Duration**: 4 – 5 Minutes  
**Hackathon**: Multimodal AI Hackathon 2026 (Track C)  
**Tone**: Technical, authoritative, brisk, polished.

---

## 🎬 Act 1: The Problem & The Core Innovation (0:00 – 0:50)

- **[Visual]**: Screen recording of the dashboard hero section.
- **[Voiceover]**:
  > *"Welcome to our submission for Track C: Contrastive Speech Analytics and Temporal Flaw Grounding.
  > Modern speech evaluation typically relies on large language models that produce vague, ungrounded critiques with non-deterministic scores and zero millisecond timestamp accuracy.
  > We took a radically different engineering approach: a 100% deterministic, zero-LLM architecture that aligns speech against ideal master baselines or population priors, grounding acoustic flaws down to the exact word boundary with full mathematical explainability."*

---

## 🎬 Act 2: The Dataset & 5-Tier Contrastive Gradient (0:50 – 1:40)

- **[Visual]**: Switch to the **Compare Gradient (Levels 4 ➔ 0)** tab. Click through Level 4, Level 3, Level 2, Level 1, Level 0.
- **[Voiceover]**:
  > *"To validate our pipeline, we built the Contrastive Speech Analytics Dataset (CSAD-2026).
  > We took high-fidelity public domain addresses—such as John F. Kennedy's 1962 Moon Speech and Reagan's Challenger Address—and constructed a calibrated 5-tier quality gradient on the exact same canonical text.
  > Here in the Compare Gradient view, you can see the monotonic rubric score progression: from 97.4 on the Level 4 Pristine Master, down through Level 3, Level 2, Level 1, to 22.0 on Level 0.
  > Every injected flaw—monotone pitch compression, rushed articulation, or inappropriate pauses—has an exact ground-truth timestamp."*

---

## 🎬 Act 3: Interactive Dashboard & Temporal Grounding (1:40 – 2:50)

- **[Visual]**: Switch to **Dashboard & Grounding** tab. Click on the pink `monotone` flaw region on the waveform.
- **[Voiceover]**:
  > *"Let’s inspect a Level 1 flawed take.
  > In the interactive WaveSurfer player, our Montreal Forced Alignment engine has segmented every word and phoneme. Notice the highlighted flaw regions.
  > When I click this monotone flaw region, the player immediately seeks to 4.12 seconds, zooming into the affected phrase: 'in this decade and do the other things'.
  > The Causal Explanation Card immediately renders the quantitative breakdown:
  > - Baseline pitch range: 6.4 semitones.
  > - Observed pitch range: 1.6 semitones.
  > - Statistical Delta: -4.8 semitones, with a robust z-score of -3.6.
  > Notice the 'Why It Hurts' explanation: flattening pitch modulation destroys nuclear stress, creating a robotic cadence that hurts listener engagement."*

---

## 🎬 Act 4: Synchronized Acoustic Contours & Transcript Heat-Strip (2:50 – 3:45)

- **[Visual]**: Switch to **Acoustic Contours (Plotly)** tab and scroll through the synchronized subplots. Hover over words in the transcript heat-strip.
- **[Voiceover]**:
  > *"In the Acoustic Contours tab, we see stacked subplots generated via Plotly.js:
  > 1. Fundamental frequency ($F_0$) in semitones relative to the speaker median, complete with a ±1.5 MAD confidence band from the master baseline.
  > 2. Calibrated energy envelope in dB.
  > 3. Instantaneous articulation rate in syllables per second.
  > Below, our aligned transcript heat-strip color-codes every word by its maximum z-score deviation. Notice the pause badge showing a disruptive 0.75-second unpunctuated pause between 'energies' and 'and skills'."*

---

## 🎬 Act 5: Deterministic Rubric & Reproducibility (3:45 – 4:30)

- **[Visual]**: Focus on the **ScoreCard** with dimension breakdown and show `docker compose up` terminal.
- **[Voiceover]**:
  > *"Our scoring system is fully deterministic. All 5 rubric dimensions—Pacing, Pitch Expressiveness, Volume Dynamics, Pauses & Fluency, and Acoustic Clarity—are evaluated via documented monotonic mathematical functions defined in YAML config files.
  > Evaluating the same audio twice yields the exact same byte-for-byte score and rationale.
  > The entire stack runs in a single command via Docker Desktop on standard CPU hardware with zero cloud dependencies.
  > Thank you!"*
