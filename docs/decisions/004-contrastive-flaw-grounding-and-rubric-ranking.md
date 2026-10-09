# ADR 004: Contrastive Flaw Grounding & Monotonic Rubric Ranking Calibration

## Status
Accepted (2026-10-08)

## Context
When comparing a test speech take against an ideal reference take of the same transcript (contrastive mode), word-level feature differences $\Delta x_i = x_i - x_i^{\text{ideal}}$ reflect pure execution divergence rather than speaker population variation.
Under population priors, wide tolerances ($z \ge 2.6$) are required to avoid penalizing distinct rhetorical styles. However, in contrastive mode, any region where $|z| \ge 1.3$ ($p < 0.05$ against baseline take MAD) represents an intentional or accidental execution flaw.

Furthermore, calculating whole-recording dimension scores by simple arithmetic mean of all word z-scores washed out localized flaws (e.g. 5 rushed words diluted over 140 total words produced mean $z \approx 0$).

## Decisions

1. **Dual-Mode Grounding Thresholds**:
   - Reference-free mode (population priors): High threshold ($|z| \ge 2.6$) to accommodate broad rhetorical diversity.
   - Contrastive mode (ideal take reference): Precision threshold ($|z| \ge 1.3$) with min duration 2-3 words.
   - Pause flaws: Trigger at pause $\ge 0.35$s and $z \ge 1.3$ (inappropriate) or pause $\le 0.08$s and $z \le -1.3$ (missing).

2. **Flaw-Penalty Rubric Scoring**:
   - In contrastive mode, dimension scores start from the ideal baseline (100.0) and degrade monotonically according to localized flaw severity:
     $$\text{Penalty} = \sum_{f \in \text{Flaws}_{\text{dim}}} 12.0 \times \min(2.5, |z| \times \text{duration\_s} \times \text{weight})$$
   - Ensures strict monotonic ranking from Level 4 (98-100) down to Level 0 (20-40).

3. **Validation**:
   - Calibrated and tuned strictly on `jfk_moon_1962` and `reagan_challenger_1986`.
   - Evaluated out-of-sample on held-out speech `fdr_fear_itself_1933`.
