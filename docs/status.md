# Project Status & Schedule Tracking

**Project**: Track C: Contrastive Speech Analytics & Temporal Flaw Grounding  
**Hackathon**: Multimodal AI Hackathon 2026  
**Last Updated**: Day 1

---

## 📅 5-Day Roadmap & Milestones

| Day | Goal & Deliverables | Status | Notes / Blockers |
| :--- | :--- | :---: | :--- |
| **Day 1** | **Foundation, Schemas & Skeleton**<br>• Repo structure, Docker setup (`Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`)<br>• Pydantic v2 schemas & TypeScript type sync<br>• Curation of 3 public domain speech baselines & LibriSpeech priors<br>• Pipeline v1 (Audio, VAD, MFA/Torchaudio, Praat, Librosa, Grounding, Scoring)<br>• Interactive React dashboard skeleton with Wavesurfer + Plotly + Mock demo data | **DONE** | All Day 1 criteria satisfied & verified |
| **Day 2** | **Flaw Injector & Dataset Generation**<br>• Parameterized flaw injector (all 5 types across 5 levels)<br>• Re-alignment & ground-truth temporal mapping<br>• `validate_dataset.py` CI integration<br>• Grounding + causal explanations + rubric scoring v1 integration<br>• **Milestone**: Upload flawed file, grounded flaw regions with explanations in dashboard | **IN PROGRESS** | Injector configs & pipeline modules ready; batch injector script next |
| **Day 3** | **Tuning, Population Fallbacks & Polish**<br>• Grounding IoU & boundary error tuning<br>• Self-recording protocol & ingest script<br>• Full sample cache verification<br>• UI styling & responsive polish | **QUEUED** | On track |
| **Day 4** | **Validation Experiments, Docs & CI**<br>• Spearman rank correlation & IoU evaluation<br>• GradientBoostingRegressor cross-check<br>• Technical doc (6 pages max), dataset card, video script, clean-machine test | **QUEUED** | On track |
| **Day 5** | **Video Recording & Freeze**<br>• 3-10 min demo video recording<br>• Final bug fixes, tag release, submission | **QUEUED** | On track |

---

## 🎯 Current Task Progress (Day 1)

- [x] Docker configuration (`docker-compose.yml`, `Dockerfile.backend`, `Dockerfile.frontend`, `environment.yml`, `requirements.txt`)
- [x] Unified schemas (`backend/schemas/api.py`, `frontend/src/types/api.ts`)
- [x] Configuration files (`configs/rubric.yaml`, `configs/flaw_rules.yaml`, `configs/injector_levels.yaml`, `configs/thresholds.yaml`)
- [x] Core pipeline modules (`audio.py`, `vad.py`, `align.py`, `features.py`, `normalize.py`, `grounding.py`, `explain.py`, `scoring.py`, `orchestrator.py`)
- [x] Pre-cached demo catalog & 5-level gradient results (`data/cached_results/`, `data/demo_audio/`)
- [x] Dataset curation & validator tools (`dataset_tools/download_sources.py`, `dataset_tools/validate_dataset.py`)
- [x] React + Vite + TypeScript dashboard (`WaveformViewer`, `AcousticPlots`, `TranscriptHeatmap`, `CausalExplanationCard`, `ScoreCard`, `UploadPanel`, `CompareGradientView`)
- [x] Unit test suites & schema validation tests passed

---

## ⚠️ Known Risks & Mitigation

1. **Host Environment Differences (Windows vs Docker Linux)**:
   - *Mitigation*: All heavy C-extensions (Montreal Forced Aligner, Kaldi) are containerized inside `Dockerfile.backend`. Lightweight fallback paths (adaptive VAD, proportional alignment) are provided for local tests.
2. **Deterministic Grading vs Subjectivity**:
   - *Mitigation*: Monotonic mathematical curves (sigmoid, piecewise-linear) with strict speaker normalization (semitones/dB re median) guarantee byte-for-byte reproducibility.
