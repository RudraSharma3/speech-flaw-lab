# ADR 001: Deterministic Contrastive Speech Analytics & Temporal Flaw Grounding Architecture

- **Status**: Accepted
- **Date**: 2026-10-07
- **Author**: AI-OS Senior Lead Engineer
- **Deciders**: Multimodal AI Hackathon Team

---

## 1. Context and Problem Statement

Speech evaluation tools often rely on non-deterministic end-to-end LLM evaluations that suffer from hallucinations, high latency, ungrounded timestamps, and lack of reproducible mathematical justification.
For Track C of the Multimodal AI Hackathon 2026, we require:
1. Exact temporal flaw grounding snapped to word and phoneme boundaries.
2. Mathematically rigorous acoustic deviation modeling against reference takes or population priors.
3. 100% deterministic, byte-for-byte reproducible rubric scoring and causal explanations with zero LLM dependencies in the scoring/grounding/explanation path.
4. Containerized execution on Windows Docker Desktop without GPU dependencies.

---

## 2. Considered Options

- **Option 1: End-to-End Multimodal LLM (Gemini 1.5 Pro / GPT-4o Audio)**:
  - *Pros*: Fast initial prototype.
  - *Cons*: Non-deterministic, high latency, poor timestamp resolution (>500ms jitter), black-box scoring, fails hackathon evaluation rigor.
- **Option 2: Pure Deep Speech Embedding (Wav2Vec2 / HuBERT + Classification Head)**:
  - *Pros*: Representation power.
  - *Cons*: Black-box neural representations lack human-understandable causal explanations (e.g. why pitch was flat in semitones).
- **Option 3: Deterministic DSP + Forced Alignment + Robust Statistics (Selected)**:
  - *Pros*:
    - Exact word boundary snapping via Montreal Forced Aligner (MFA 3.x) and Torchaudio fallback.
    - Praat (Parselmouth) for physical acoustic invariants (F0 in semitones re speaker median, HNR in dB, intensity in dB).
    - Median Absolute Deviation (MAD) robust z-scores against baseline or LibriSpeech population priors.
    - Rule-based structured templates for causal explanations ("Pitch range collapsed from 6.4 to 1.6 semitones across words 11-18 (z=-3.6)").
    - 100% deterministic, sub-100ms inference, zero API cost, zero LLM hallucination.

---

## 3. Decision Outcome

We selected **Option 3**: Deterministic DSP + Forced Alignment + Robust Statistical Deviation.

### Positive Consequences
- Sub-millisecond temporal grounding snapped to MFA word boundaries.
- Full mathematical transparency: all thresholds and curves are configured in `/configs` (`rubric.yaml`, `flaw_rules.yaml`, `thresholds.yaml`).
- Zero LLM in the path; CPU-friendly, fast execution on Docker Desktop.

### Negative Consequences / Trade-offs
- Requires MFA dictionary/acoustic models or fallback alignment when running outside container.
- *Mitigation*: Implemented unified alignment interface with automatic Torchaudio/proportional fallback.

---

## 4. Implementation Details
- Pipeline modules in [`backend/pipeline/`](file:///c:/Users/HP/OneDrive/Desktop/Speech/backend/pipeline).
- Pydantic v2 schemas in [`backend/schemas/api.py`](file:///c:/Users/HP/OneDrive/Desktop/Speech/backend/schemas/api.py).
- Docker environment in [`Dockerfile.backend`](file:///c:/Users/HP/OneDrive/Desktop/Speech/Dockerfile.backend) and [`docker-compose.yml`](file:///c:/Users/HP/OneDrive/Desktop/Speech/docker-compose.yml).
