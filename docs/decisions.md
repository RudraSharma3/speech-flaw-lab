# Architectural Decisions Log

This document records the architectural decisions made in the Speech project.

---

## Index of Decisions

1. [ADR 001: Deterministic Pipeline Architecture](file:///docs/decisions/001-pipeline-architecture.md)
   - 100% deterministic DSP + Forced Alignment + Robust Statistics architecture with zero LLMs in the evaluation path.
2. [ADR 003: Feature Calibration, Forced Alignment Fidelity & Real Speech Norming](file:///docs/decisions/003-feature-calibration-and-real-speech-norming.md)
   - Replacement of synthetic/proportional alignment with real Torchaudio CTC forced alignment (`WAV2VEC2_ASR_BASE_960H` + Viterbi `forced_align`).
   - Punctuation token exclusion into metadata-only fields (`punctuation`, `has_punctuation`).
   - Calibration of F0 range (minimum 4 voiced frames), speech rate (5-word sliding window), and HNR clarity (relative normalization).
   - Primary contrastive mode evaluation (96.5/100, 0 flaws on unmodified real speech) with calibrated fallback priors (88-90/100, <= 1 flaw).
3. [ADR 007: Disabling breathy_unclear Flaw Type in Contrastive Mode](file:///docs/decisions/007-disable-breathy-in-contrastive.md)
   - Diagnostic of the 33 far-from-GT detections proved 23 instances were `breathy_unclear` triggered by window shifts over unvoiced consonants on historical shellac/optical noise floors.
   - Disabled `breathy_unclear` strictly in contrastive mode because it fires solely on processing artefacts; retained in reference-free coarse screening mode.
