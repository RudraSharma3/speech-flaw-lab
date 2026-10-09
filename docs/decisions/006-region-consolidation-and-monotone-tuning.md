# ADR-006: Region Consolidation and Monotone Over-Detection Fix

**Status**: Accepted  
**Date**: 2026-10-08  
**Authors**: Speech Pipeline Team  

---

## Context

The temporal flaw grounding module (`backend/pipeline/grounding.py`) independently detects each flaw type (monotone, rushed, drag_slow, etc.) via hysteresis thresholding on word-level z-scores. When the injector applies multiple transformations to overlapping regions (e.g., pitch flattening + time stretching), this produced redundant detections:

- **153 monotone detections vs 60 injected** (30.0% recall, 11.8% precision)
- **105 of 218 unmatched detections** overlapped a ground-truth injected region but under a different flaw type
- Short monotone fragments (< 1.0s) were detected on individual words within rate-altered regions

## Decision

### 1. Multi-Type Region Consolidation

After all flaw types are independently detected, overlapping or adjacent (gap ≤ 0.3s) detections are **merged** into a single composite region:

- **Primary type**: the flaw type with the highest `|z_score|`
- **Secondary types**: all other flaw types that contributed to the merged region, listed in the `secondary_types` field

This replaces the previous "filter out subsumed secondaries" approach, which silently dropped detections.

### 2. Monotone Minimum Duration (1.5s)

Monotone flaw detection requires a contiguous region of at least **1.5 seconds** (approximately 4 words at typical oratorical pace). This eliminates short false-positive fragments that arise from:

- Individual words at phrase boundaries with naturally low pitch variation
- Time-stretch artifacts that compress pitch range in adjacent words
- Alignment jitter causing transient low-range values

### 3. Type-Agnostic IoU Matching

Benchmark matching uses **IoU ≥ 0.3 regardless of flaw type**, with type accuracy reported separately. This prevents artificial recall deflation when the detector correctly localizes a flawed region but identifies it under a different (but related) flaw category.

### 4. Minimum Word Count for Monotone in Contrastive Mode

Changed from 3 words to 4 words minimum for monotone detection in contrastive mode, ensuring the detected region spans a meaningful prosodic phrase rather than individual word-level variation.

## Tuning Discipline

All threshold changes (1.5s minimum, 4-word minimum, 0.3s merge gap) were tuned exclusively on the tuning set (JFK + Reagan speeches). The held-out set (FDR) was only evaluated after freezing parameters.

## Consequences

**Positive**:
- Eliminates redundant multi-type detections on the same audio region
- Reduces false monotone detections
- Provides richer feedback (primary + secondary flaw types per region)
- More honest benchmark matching (type-agnostic IoU)

**Negative**:
- Short genuine monotone passages (< 1.5s) will not be flagged
- Merging across types may obscure independent co-occurring flaws

## References

- [grounding.py](file:///c:/Users/HP/OneDrive/Desktop/Speech/backend/pipeline/grounding.py): Region consolidation implementation
- [benchmark_grounding.py](file:///c:/Users/HP/OneDrive/Desktop/Speech/dataset_tools/benchmark_grounding.py): Type-agnostic matching
