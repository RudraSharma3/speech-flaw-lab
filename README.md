# 🎙️ Contrastive Speech Analytics & Temporal Flaw Grounding

> **Multimodal AI Hackathon 2026 — Track C Submission**  
> *Deterministic Acoustic Deviation Modeling, Word-Snapped Flaw Grounding & Zero-LLM Causal Explainability.*

---

## 🌟 Overview

**Track C: Contrastive Speech Analytics & Temporal Flaw Grounding** delivers an automated, mathematically rigorous system for evaluating spoken delivery. Rather than relying on non-deterministic black-box LLMs, this platform aligns speech against **ideal canonical baselines** (or **LibriSpeech population priors**) on a synchronized word-index axis to ground acoustic flaws down to exact millisecond boundaries.

```mermaid
graph TD
    UserAudio[Uploaded Audio + Transcript] --> Normalizer[LUFS Normalization & 16kHz WAV]
    Normalizer --> VAD[Silero / Energy VAD]
    Normalizer --> MFA[Montreal Forced Alignment 3.x]
    
    Normalizer --> Praat[Parselmouth Praat: Adaptive F0, Intensity, HNR]
    Normalizer --> Librosa[Librosa: MFCCs, Spectral Flux & Centroid]
    
    MFA --> WordBounds[Word & Phoneme Token Boundaries]
    Praat & Librosa & WordBounds --> Aggregation[Word-Level Feature Aggregation]
    
    Aggregation --> Normalization[Speaker Normalization: Semitones & dB re Median]
    Normalization --> ZScores[MAD Robust Z-Scores vs Baseline / Population]
    
    ZScores --> Grounding[Temporal Flaw Grounding: Hysteresis & Word-Snapping]
    Grounding --> Explanations[Structured Causal Rationale & Severity Scoring]
    Grounding --> Rubric[Deterministic 0-100 Rubric Dimensions]
    
    Explanations & Rubric --> Dashboard[Interactive React + Plotly + Wavesurfer UI]
```

---

## 🚀 Key Features

1. **Deterministic & Zero-LLM**: 100% reproducible byte-for-byte scoring. No hallucinated critiques, zero API costs, and sub-100ms inference.
2. **Sub-Millisecond Temporal Grounding**: Snapped strictly to forced-aligned word and phoneme boundaries using Montreal Forced Aligner (MFA 3.x, ARPA US English).
3. **5-Tier Contrastive Gradient**: Dataset spanning **Level 4 (Pristine Master)** down to **Level 0 (Egregious)** on the exact same canonical speech text with exact ground-truth flaw timestamps.
4. **Speaker-Normalized Invariants**: Pitch in semitones relative to speaker median ($12 \log_2(F_0 / \tilde{F}_0)$), dynamic energy contrast in dB, and syllable articulation rate.
5. **Structured Causal Explainability**: Template-driven diagnostic cards containing exact numbers, units, statistical deltas ($\Delta$), $z$-scores, calculated severity ($S = \Delta t \cdot |z| \cdot w$), and rhetorical impact analysis ("why it hurts").
6. **Pre-Cached Demo Safety**: Built-in 5-level demo catalog guaranteed to run without internet or external API requirements.

---

## 📦 System Architecture & Directory Structure

```
├── backend/
│   ├── app/                 # FastAPI application, background jobs & demo provider
│   ├── pipeline/            # Deterministic pipeline (audio, vad, align, features, normalize, grounding, explain, scoring)
│   ├── schemas/             # Pydantic v2 data models
│   └── tests/               # Unit, integration, and falsification test suites
├── configs/
│   ├── rubric.yaml          # 5 dimension definitions, weights & mathematical score curves
│   ├── flaw_rules.yaml      # Causal explainability rules, triggers & templates
│   ├── injector_levels.yaml # 5-tier flaw injection parameters (Levels 4 to 0)
│   └── thresholds.yaml      # DSP parameters, Praat thresholds & hysteresis bands
├── data/
│   ├── raw/                 # Public domain source recordings (JFK, Reagan, FDR)
│   ├── processed/           # 16kHz mono WAV files
│   ├── cached_results/      # Pre-cached JSON results by SHA-256
│   ├── demo_audio/          # Audio WAV assets for dashboard playback
│   └── population_norms/    # LibriSpeech acoustic parameter priors
├── dataset_tools/
│   ├── download_sources.py  # Public domain dataset curation & manifest builder
│   └── validate_dataset.py  # Dataset integrity, boundary & schema validator
├── docs/
│   ├── technical_doc.md     # 6-page comprehensive technical report
│   ├── dataset_card.md      # Dataset provenance, splits & ethical card
│   ├── status.md            # Roadmap milestones & progress tracker
│   ├── video_script.md      # 4-minute demonstration script
│   └── decisions/           # Architectural Decision Records (ADRs)
├── frontend/                # React + Vite + TypeScript + Tailwind + Wavesurfer + Plotly
├── docker-compose.yml       # One-command orchestration
├── Dockerfile.backend       # Micromamba base image with MFA 3.x, Praat & PyTorch
├── Dockerfile.frontend      # Node.js 20 Vite dev/prod container
└── environment.yml          # Pinned Conda/Micromamba environment specification
```

---

## ⚡ Quick Start

### 1. Prerequisites
- **Python**: **Python 3.11** (recommended for deterministic PyTorch and Parselmouth Praat binary compatibility).
- **FFmpeg**: Required for processing compressed audio (M4A, MP3, AAC).
  - **Windows**: Install using Windows Package Manager:
    ```powershell
    winget install Gyan.FFmpeg
    ```
    *(Alternatively, the bundled `imageio-ffmpeg` package automatically locates an embedded Gyan.FFmpeg binary).*
  - **Linux (Ubuntu/Debian)**: `sudo apt-get update && sudo apt-get install -y ffmpeg`
  - **macOS**: `brew install ffmpeg`
- **Node.js**: Node.js 20+ and `npm` (for the React frontend).

---

### 2. Python Environment Setup
```bash
# Clone repository
git clone https://github.com/your-org/speech.git
cd speech

# Create virtual environment with Python 3.11
python -m venv .venv

# Activate environment
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Install dependencies (CPU-only PyTorch first for fast lightweight install)
pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

---

### 3. Frontend Build
Compile the React/TypeScript/Plotly web dashboard:
```bash
cd frontend
npm install
npm run build
cd ..
```
The compiled bundle is output to `frontend/dist/` and served automatically by FastAPI on the unified port.

---

### 4. Running the API & Dashboard
Launch the unified server (FastAPI backend + static frontend):
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
- **Unified Interactive Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

### 5. Running the Evaluation Benchmark
Run the full 75-recording deterministic evaluation benchmark across all 5 quality levels and 3 seeds:
```bash
python -m dataset_tools.run_benchmark
```
Metrics and confusion matrices are written directly to `results/benchmark.json`.

---

### 6. Dataset Download (CSAD-2026)
The complete 75-recording evaluation corpus (16kHz WAV audio, JSON flaw ground truth, alignment TextGrids, and manifests) is pre-packaged:
- **Archive Path**: `dist/speech_prosody_benchmark_v1.zip`
- **Package Size**: `119,109,722 bytes` (113.59 MB)
- **SHA-256 Checksum**: `4ba0eac057e013b14a97c2c2e99de5154834b9bdc5dbb7e527172e1871d64e6b`

Verify integrity:
```powershell
# On Windows PowerShell:
Get-FileHash dist/speech_prosody_benchmark_v1.zip -Algorithm SHA256

# On Linux / macOS:
sha256sum dist/speech_prosody_benchmark_v1.zip
```

---

## 🛠️ CLI & Reproduction Commands

Run all pipeline tools directly using standard Python commands:

```bash
# 1. Run full 75-recording benchmark & generate results/benchmark.json
python -m dataset_tools.run_benchmark

# 2. Run dataset integrity and alignment validation across all 75 files
python -m dataset_tools.validate_dataset

# 3. Generate technical documentation from benchmark facts
python -m dataset_tools.generate_technical_doc

# 4. Ingest and score out-of-distribution self-recordings
python -m dataset_tools.ingest_self_recordings

# 5. Execute backend test suite
pytest backend/tests/ -v

# 6. Build and preview frontend
cd frontend
npm install
npm run build
```

---

## 💻 Fresh Clone Setup (Non-OneDrive Environment)

To test a clean setup on a new machine without pre-existing environment state:

1. **Prerequisites**: Python 3.11 (strictly recommended for PyTorch & Praat wheel compatibility), Node.js 20+, Git.
2. **Clone & Virtual Environment**:
   ```bash
   git clone https://github.com/your-org/speech.git
   cd speech
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Dataset Audio Setup (for full 75-recording validation)**:
   > *Note*: Git tracks demo audio in `data/demo_audio/` out of the box. To run the full benchmark validator across all 75 recordings, extract the audio package into `data/injected/`:
   ```bash
   # From project root, if speech_prosody_benchmark_v1.zip is downloaded to dist/:
   python -c "import zipfile, os; os.makedirs('data/injected', exist_ok=True); [open(os.path.join('data/injected', os.path.basename(m)), 'wb').write(zf.open(m).read()) for zf in [zipfile.ZipFile('dist/speech_prosody_benchmark_v1.zip')] for m in zf.namelist() if m.startswith('audio/') and os.path.basename(m)]"
   ```
5. **Run Dataset Validator**:
   ```bash
   python -m dataset_tools.validate_dataset
   ```
6. **Build Frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```
7. **Launch API & Interactive Dashboard**:
   ```bash
   # Start backend API (serves API and built static frontend)
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   
   # Or run Vite dev server in parallel:
   # cd frontend && npm run dev
   ```
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000) or [http://localhost:5173](http://localhost:5173).

---

## 📊 Rubric Dimensions & Scoring Formulation

Overall speech score ($0 - 100$) is computed as a weighted sum across 5 core dimensions defined in `configs/rubric.yaml`:

$$\text{Score}_{\text{overall}} = 0.25 \cdot S_{\text{Pacing}} + 0.25 \cdot S_{\text{Pitch}} + 0.20 \cdot S_{\text{Volume}} + 0.15 \cdot S_{\text{Pauses}} + 0.15 \cdot S_{\text{Clarity}}$$

- **Pacing & Speech Rate** ($25\%$): Evaluates syllable articulation rate consistency via symmetric sigmoid penalty curve.
- **Pitch Expressiveness** ($25\%$): Evaluates $F_0$ modulation ($P_{90}-P_{10}$ range in semitones) via monotonic piecewise-linear mapping.
- **Volume Dynamics** ($20\%$): Evaluates energy contrast in dB between stressed vowels and background baseline.
- **Pauses & Fluency** ($15\%$): Penalizes unpunctuated hesitations ($\ge 0.35\text{s}$) via exponential decay.
- **Acoustic Clarity** ($15\%$): Evaluates Harmonics-to-Noise Ratio (HNR in dB) to detect turbulence and breathiness.

---

## 📄 Documentation Links

- [Technical Documentation (Report & Audit)](docs/technical_doc.md)
- [Technical Documentation PDF Export](docs/technical_doc.pdf)
- [Dataset Card (CSAD-2026)](docs/dataset_card.md)
- [Video Demonstration Script](docs/video_script.md)
- [ADR 001: Architecture Decision](docs/decisions/001-pipeline-architecture.md)
- [ADR 007: Disable Breathy in Contrastive Mode](docs/decisions/007-disable-breathy-in-contrastive.md)
- [Project Status & Roadmap Tracking](docs/status.md)
