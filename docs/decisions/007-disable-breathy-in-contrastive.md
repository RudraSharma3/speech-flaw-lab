# ADR-007: Disabling breathy_unclear Flaw Type in Contrastive Mode

**Status**: Accepted  
**Date**: 2026-10-09  
**Authors**: Speech Pipeline Team  

---

## Context

In our diagnostic audit of the 33 far-from-ground-truth detections across the 75-recording benchmark dataset:
- **23 of the 33 detections** were `breathy_unclear` firing on untouched, un-injected audio regions (specifically 11 detections in `reagan_challenger_1986_level_2_s1`, 10 in `level_1_s2`, 1 in `level_0_s2`, and 1 in `reagan_mourning_level_0`).
- Across the entire 75-recording dataset, `breathy_unclear` matched **0 ground-truth flaws** (0 true positives).
- When identical un-injected audio was evaluated (in full-chain null identity control and in cross-seed $L_4$ comparison $L_{4,s1}$ vs $L_{4,s0}$), `breathy_unclear` produced **0 flags**.

## Diagnostic Root Cause

1. **Shared Stationary Noise Floor**: In contrastive mode, the test audio and reference audio share the exact same vintage recording session and microphone channel. Therefore, vintage background noise *cannot* explain a contrastive drop in Harmonics-to-Noise Ratio (HNR), because $(HNR_{test} - HNR_{ref})$ cancels stationary background noise.
2. **Alignment Boundary Jitter Artefacts**: When flaws are injected elsewhere in a file (e.g. rushed delivery at $t=40$s), the timeline length changes, causing subsequent forced alignment (`MMS_FA`) to shift word boundaries by 15–40 ms on untouched words.
3. **Consonant/Silence Window Intrusion**: Praat's frame-level HNR is highly sensitive to window boundaries. When a 25ms alignment shift causes a voiced word window to overlap an adjacent unvoiced stop consonant, fricative, or aspiration silence, word-average HNR plunges by 10–15 dB relative to the cleanly-aligned baseline word.
4. With a contrastive threshold of $z \le -1.6$, this alignment boundary jitter caused false `breathy_unclear` cascades on untouched speech.

## Decision

Completely disable the `breathy_unclear` flaw detector in contrastive evaluation mode.

## Consequences

**Positive**:
- Eliminates 23 false-positive detections on untouched audio regions.
- Greatly increases precision of contrastive flaw grounding.
- Eliminates alignment jitter sensitivity on stationary noise channels.

**Negative**:
- Synthetic breathy/aspiration noise flaws (if specifically injected with added noise) are not surfaced. Given that natural oratorical delivery flaws are primarily prosodic (pitch, tempo, rhythm, pause), this is an acceptable domain trade-off.

## References

- Diagnostic log: `scratch/diagnose_item2.py`
- Implementation: `backend/pipeline/grounding.py` (Line 80)
