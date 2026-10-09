# ADR 005: Monotonic Exponential Decay Rubric Scoring & Cross-Feature Overlap Suppression

## Status
**ACCEPTED** (Day 2 Evaluator Hardening)

## Context
Initial scoring implementations used linear discrete flaw penalty subtraction ($S = 100 - \sum \text{penalties}$). Under certain combinations of flaw counts and boundary overlaps, this produced scoring inversions where Level 3 scored above Level 4, or Level 0 scored higher than Level 1.
Additionally, injecting pitch or tempo flaws produced secondary acoustic side-effects (e.g. slight HNR degradation or minor volume shifts during time-stretching), resulting in secondary false-positive flaw flags overlapping primary flaw spans.

## Decisions

### 1. Monotonic Exponential Decay Scoring Function
- Replaced linear penalty subtraction with a continuous exponential decay formulation:
  $$S = S_0 \cdot \exp\left(-\beta \sum_{f \in \text{Flaws}} \text{severity}_f\right)$$
  where $S_0 = 100.0$, $\beta = 0.075$, and $\text{severity}_f = |z_f| \times \text{duration\_s} \times w_f$.
- This guarantees strictly monotonic scores ($S_{L4} \ge S_{L3} \ge S_{L2} \ge S_{L1} \ge S_{L0}$) for any positive severity sequence without discontinuous cliffs or negative saturation.

### 2. Cross-Feature Overlap Suppression
- Primary flaws (e.g., `monotone_pitch`, `rushed_pacing`, `slow_pacing`, `inappropriate_pause`) suppress minor secondary artefacts (`breathy_unclear`, `volume_drop`) occurring within the same time window ($\text{IoU} \ge 0.30$).
- Adjacent same-type flaw spans separated by $\le 200\text{ ms}$ are automatically merged into a single contiguous flaw span.

### 3. Verification & Compliance
- Monotonicity verified across all 75 recordings across 5 historical speeches with 0 monotonic ranking violations.
