# Active Task State

This document captures the current work in progress, goals, acceptance criteria, and task handoff notes.

---

## 1. Goal

Execute **Day 1 Milestone** for **Track C: Contrastive Speech Analytics & Temporal Flaw Grounding** (Multimodal AI Hackathon 2026):
1. Establish containerized architecture (`Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, `environment.yml`).
2. Implement frozen Pydantic v2 schemas (`backend/schemas/api.py`) and synchronized TypeScript interfaces (`frontend/src/types/api.ts`).
3. Build configuration contracts (`configs/rubric.yaml`, `configs/flaw_rules.yaml`, `configs/injector_levels.yaml`, `configs/thresholds.yaml`).
4. Curate public-domain baselines (`jfk_moon_1962`, `reagan_challenger_1986`, `fdr_fear_itself_1933`) and LibriSpeech population priors (`data/population_norms/librispeech_priors.json`).
5. Develop core pipeline modules v1: 16kHz LUFS audio ingestion, VAD, forced alignment (MFA + fallback), Parselmouth Praat + Librosa feature extraction, speaker normalization, temporal flaw grounding snapped to word boundaries, causal explainability, and rubric scoring.
6. Build full-featured React + Vite + TypeScript dashboard with Wavesurfer.js v7, Plotly stacked subplots, word-level heat-strip, causal explanation card, rubric score card, and 5-tier gradient comparison view.
7. Generate pre-cached demo catalog (`data/cached_results/`) across all 5 quality levels for a zero-fail live demo.

---

## 2. Acceptance Criteria (Day 1)

- [x] Docker setup with micromamba base, Montreal Forced Aligner 3.x, Python 3.11, and Node 20.
- [x] Pydantic v2 schemas and TypeScript types frozen and tested against mock result contract.
- [x] Public domain speech baselines curated with license provenance in [`data/manifests/sources_manifest.json`](file:///c:/Users/HP/OneDrive/Desktop/Speech/data/manifests/sources_manifest.json).
- [x] LibriSpeech population priors generated in [`data/population_norms/librispeech_priors.json`](file:///c:/Users/HP/OneDrive/Desktop/Speech/data/population_norms/librispeech_priors.json).
- [x] Dataset validator [`dataset_tools/validate_dataset.py`](file:///c:/Users/HP/OneDrive/Desktop/Speech/dataset_tools/validate_dataset.py) passes with zero errors.
- [x] Deterministic pipeline runner [`backend/pipeline/orchestrator.py`](file:///c:/Users/HP/OneDrive/Desktop/Speech/backend/pipeline/orchestrator.py) wired to FastAPI.
- [x] Interactive React dashboard with Wavesurfer flaw regions, Plotly synchronized curves, token heat-strip, and 5-tier gradient view.
- [x] All parameters in [`configs/`](file:///c:/Users/HP/OneDrive/Desktop/Speech/configs), zero LLM in the scoring path.
- [x] Running status tracking in [`docs/status.md`](file:///c:/Users/HP/OneDrive/Desktop/Speech/docs/status.md) and ADR in [`docs/decisions/001-pipeline-architecture.md`](file:///c:/Users/HP/OneDrive/Desktop/Speech/docs/decisions/001-pipeline-architecture.md).

---

## 3. Implementation Plan & Progress

- [x] Step 1: Initialize directory tree, Dockerfile.backend, Dockerfile.frontend, docker-compose.yml.
- [x] Step 2: Create YAML configs for rubric, flaw rules, injector levels, and thresholds.
- [x] Step 3: Implement Pydantic v2 schemas and TypeScript API interfaces.
- [x] Step 4: Build backend pipeline modules (audio, vad, align, features, normalize, grounding, explain, scoring).
- [x] Step 5: Implement FastAPI server with background job queue, SHA-256 caching, and sample endpoints.
- [x] Step 6: Create dataset curation tools and validate dataset integrity.
- [x] Step 7: Build React + Vite + Tailwind + Wavesurfer + Plotly frontend components.
- [x] Step 8: Verify build, schemas, and dataset integrity checks.

---

## 4. Current Status & Decisions

- **Status**: Day 1 milestone 100% completed and verified.
- **Decisions**:
  - Implemented ADR 001: 100% deterministic DSP + Forced Alignment + Robust Statistics architecture with zero LLMs in the evaluation path.
  - Sourced public domain speeches under 17 U.S.C. § 105.
  - Pre-cached 5-tier gradient samples in [`data/cached_results/`](file:///c:/Users/HP/OneDrive/Desktop/Speech/data/cached_results) ensuring demo resilience.

---

## 5. Handoff Notes

- **Verified Working**:
  - `python -m dataset_tools.download_sources` ➔ Generated sources manifest & LibriSpeech priors.
  - `python -m dataset_tools.validate_dataset` ➔ 5 cached gradient levels & manifests validated.
  - `python -c "import backend.tests.test_schemas as ts; ts.test_mock_result_conforms_to_schema()"` ➔ Pydantic v2 schemas validated.
  - Frontend bundle compiled cleanly with TypeScript & Vite.
- **Next Phase (Day 2)**:
  - Implement batch parameterized flaw injector (`dataset_tools/inject_flaws.py`) across all speech baselines.
  - Implement re-alignment and ground-truth mapping verification.
  - Wire live recording ingest and complete Day 2 milestone tag.

