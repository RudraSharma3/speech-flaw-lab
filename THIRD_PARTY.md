# Third-Party Licences & Intellectual Property Notice

This document catalogs all third-party software libraries, neural network weights, acoustic models, and reference corpora utilized in the **Contrastive Speech Analytics** platform, along with their respective intellectual property licences and upstream attribution.

---

## 1. Third-Party Software & Models

| Component / Asset | Author / Organization | Upstream Repository / Source | Licence | Notes & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **Torchaudio MMS_FA Weights** | Meta AI Research | [facebookresearch/mms](https://github.com/facebookresearch/fairseq/tree/main/examples/mms) | **CC-BY-NC 4.0** (Creative Commons Attribution-NonCommercial 4.0) | Neural forced aligner acoustic model weights. Pre-trained on 1,400+ languages. Restricted to non-commercial academic & research evaluation. |
| **Parselmouth** (`praat-parselmouth`) | Yannick Jadoul, Paul Boersma, David Weenink | [YannickJadoul/Parselmouth](https://github.com/YannickJadoul/Parselmouth) | **GPL-3.0** (GNU General Public License v3.0) | Python interface to Praat's native C++ acoustic signal processing engine. Strong copyleft. |
| **LibriSpeech (Priors)** | Vassil Panayotov, Guoguo Chen, Daniel Povey, Sanjeev Khudanpur | [LibriSpeech ASR Corpus](https://www.openslr.org/12) | **CC BY 4.0** (Creative Commons Attribution 4.0) | Used strictly for computing baseline population acoustic norms ($F_0$, intensity, articulation rate, HNR). |
| **faster-whisper** | Guillaume Klein, SYSTRAN | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | **MIT License** | CTranslate2-based Whisper transcription runtime. Permissive. |
| **Silero VAD** | Silero Team | [snakers4/silero-vad](https://github.com/snakers4/silero-vad) | **MIT License** | Voice Activity Detection (VAD) model. Permissive. |
| **torchaudio** | PyTorch / Linux Foundation | [pytorch/audio](https://github.com/pytorch/audio) | **BSD 2-Clause License** | Audio I/O, spectrogram DSP, and CTC forced alignment functional kernels. Permissive. |
| **librosa** | Brian McFee et al. | [librosa/librosa](https://github.com/librosa/librosa) | **ISC License** | Audio and music signal analysis in Python. Permissive (BSD-compatible). |
| **scikit-learn** | Scikit-learn developers | [scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn) | **BSD 3-Clause License** | Monotonic isotonic regression calibration engine. Permissive. |
| **SoundFile** | Bastibe | [bastibe/python-soundfile](https://github.com/bastibe/python-soundfile) | **BSD 3-Clause License** | Audio file I/O based on libsndfile. Permissive. |
| **Plotly.js** | Plotly, Inc. | [plotly/plotly.js](https://github.com/plotly/plotly.js) | **MIT License** | Interactive acoustic spectrogram and time-series plotting library. Permissive. |
| **WaveSurfer.js** | katspaugh | [katspaugh/wavesurfer.js](https://github.com/katspaugh/wavesurfer.js) | **BSD 3-Clause License** | Navigable audio waveform viewer and timeline interval plugin. Permissive. |

---

## 2. Repository Licence Suggestions (To be confirmed by the author)

The following licensing structure is proposed for consideration (not a formal legal conclusion):

1. **Software Code**:
   - Proposed Licence: **GNU General Public License v3.0 (GPL-3.0)** (or GPL-3.0-or-later).
   - *Author Note*: `praat-parselmouth` links Praat's core C/C++ engine, which is distributed under GPL-3.0. Releasing the application code under GPL-3.0 provides seamless compatibility with Parselmouth's reciprocal terms, alongside the permissive components (MIT, BSD, ISC).

2. **Dataset Annotations, Manifests & Injector Outputs**:
   - Proposed Licence: **Creative Commons Attribution 4.0 International (CC BY 4.0)** for project annotations, manifests, metadata, and synthetic prosodic injector outputs.
   - *Neural Model Weights*: If pre-trained MMS_FA forced alignment weights are distributed or bundled, Meta AI's upstream licensing indicates CC-BY-NC 4.0 for non-commercial research evaluation.
