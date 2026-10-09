# Dataset Card: Contrastive Speech Analytics Dataset (CSAD-2026)

## 1. Dataset Summary

The **Contrastive Speech Analytics Dataset (CSAD-2026)** is an open-access multimodal speech prosody evaluation dataset designed for benchmarking temporal speech flaw grounding and rubric-based speech quality assessment. Unlike conventional speech datasets that rate ungrounded audio clips holistically, CSAD-2026 provides paired **ideal vs. flawed** recordings of the **exact same canonical text**, spanning a calibrated 5-tier quality gradient (Level 4 = Ideal Reference down to Level 0 = Egregiously Wrong) with exact millisecond ground-truth timestamps snapped to forced-aligned word and phoneme boundaries.

- **Total Recordings**: 75 audio files across 5 speeches and 3 independent injection seeds (plus 5 null-control identity files).
- **Audio Specification**: 16 kHz mono 16-bit PCM WAV, normalized to -20.0 LUFS (ITU-R BS.1770-4).
- **Annotations**: JSON flaw annotations and Praat TextGrid interval alignments for every recording.
- **Archive Size**: 113.59 MB (119,109,722 bytes).
- **Archive SHA-256**: `4ba0eac057e013b14a97c2c2e99de5154834b9bdc5dbb7e527172e1871d64e6b`.

---

## 2. Dataset Structure & Hierarchy

```
/data
├── raw/                     # Original master archival recordings
├── processed/               # Normalized 16kHz mono 16-bit WAV excerpts
├── injected/                # 75 parameterized gradient WAV recordings (L0–L4, seeds 0-2)
├── alignments/              # Torchaudio MMS_FA JSON alignments & Praat TextGrids
│   └── textgrids/           # Praat .TextGrid interval files for acoustic software
├── annotations/             # Ground-truth temporal flaw JSON annotations
├── manifests/               # Dataset provenance, splits.json, and dataset_manifest_v1.json
├── population_norms/        # LibriSpeech acoustic parameter priors
└── self_recordings/         # Out-of-distribution user take directory & protocol
```

---

## 3. Baseline Speech Sources & Provenance

Baselines are historical speech recordings believed public domain based on their archival provenance and historical public broadcasts. Exact archival provenance and source URLs are documented below for full transparency (not a legal conclusion):

| Speech ID | Speaker | Event & Date | Audio Source URL | Archival Provenance | Believed Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `jfk_moon_1962` | John F. Kennedy | Rice University Space Address (1962-09-12) | [JFK Library Audio](https://www.jfklibrary.org/asset-viewer/archives/JFKWHA/1962/JFKWHA-127-002) / [Internet Archive MP3](https://archive.org/download/jfks19620912/jfks19620912.mp3) | U.S. Presidential public address recording, National Archives & Records Administration (NARA) | Believed public domain |
| `jfk_we_choose_1962` | John F. Kennedy | Rice University Space Address Excerpt 2 (1962-09-12) | [JFK Library Audio](https://www.jfklibrary.org/asset-viewer/archives/JFKWHA/1962/JFKWHA-127-002) / [Internet Archive MP3](https://archive.org/download/jfks19620912/jfks19620912.mp3) | U.S. Presidential public address recording, National Archives & Records Administration (NARA) | Believed public domain |
| `reagan_challenger_1986` | Ronald Reagan | Challenger Disaster Address (1986-01-28) | [Reagan Library Audio](https://www.reaganlibrary.gov/archives/speech/address-nation-explosion-space-shuttle-challenger) / [Internet Archive MP3](https://archive.org/download/ChallengerAddress/ReaganChallengerAddress.mp3) | Ronald Reagan Presidential Library & Museum audio collection | Believed public domain |
| `reagan_mourning_1986` | Ronald Reagan | Challenger Address Closing Remarks (1986-01-28) | [Reagan Library Audio](https://www.reaganlibrary.gov/archives/speech/address-nation-explosion-space-shuttle-challenger) / [Internet Archive MP3](https://archive.org/download/ChallengerAddress/ReaganChallengerAddress.mp3) | Ronald Reagan Presidential Library & Museum audio collection | Believed public domain |
| `fdr_fear_itself_1933` | Franklin D. Roosevelt | First Inaugural Address (1933-03-04) | [US National Archives Milestone Documents](https://www.archives.gov/milestone-documents/franklin-d-roosevelts-first-inaugural-address) / [Internet Archive MP3](https://archive.org/download/FDR_First_Inaugural_Address/FDR_Inaugural.mp3) | U.S. National Archives and Records Administration (Record Group 64) | Believed public domain |

All master baseline audio files are normalized to **-20.0 LUFS** (BS.1770) at **16 kHz mono 16-bit PCM WAV** to prevent amplitude bias.

---

## 4. Parameterized Flaw Injection Gradient

Each master baseline excerpt is transformed across 5 quality tiers:

| Quality Level | Label | Injected Flaw Types | Parameter Ranges | Target Rubric Score |
| :---: | :--- | :--- | :--- | :---: |
| **Level 4** | **Pristine Master** | None (Original baseline) | Nominal ($z \approx 0.0$) | **90 – 100** |
| **Level 3** | **Near Perfect** | 1 subtle localized flaw | $F_0$ compression 35%, rate $\pm 15-20\%$ | **80 – 92** |
| **Level 2** | **Slightly Flawed** | 2 distinct flaw regions | $F_0$ compression 60%, rate $+45\%$, pause 0.55s | **60 – 79** |
| **Level 1** | **Flawed** | 3 distinct flaw regions | $F_0$ compression 80%, rate $+70\%$, pause 0.90s | **40 – 59** |
| **Level 0** | **Egregious** | 4 multi-tier flaw regions | $F_0$ flatline 95%, rate $2.1\times$, pause 1.50s | **0 – 39** |

---

## 5. Dataset Splits (`splits.json`)

1. **Tuning Set (60 files)**:
   - `jfk_moon_1962` (Levels 0–4, seeds 0, 1, 2)
   - `jfk_we_choose_1962` (Levels 0–4, seeds 0, 1, 2)
   - `reagan_challenger_1986` (Levels 0–4, seeds 0, 1, 2)
   - `reagan_mourning_1986` (Levels 0–4, seeds 0, 1, 2)
   - *Purpose*: Used for threshold hysteresis tuning and isotonic regression calibration.
2. **Held-Out Test Set (15 files)**:
   - `fdr_fear_itself_1933` (Levels 0–4, seeds 0, 1, 2)
   - *Purpose*: Strictly held-out speech with 1933 acoustic characteristics used exclusively for unbiased benchmark evaluation.
3. **Out-of-Distribution Protocol**:
   - `data/self_recordings/` protocol for live modern microphone user takes.

---

## 6. Dataset Limitations

1. **Speaker Demographics**: Baseline speeches originate from 3 historical 20th-century male U.S. presidents. Although fundamental frequency extraction uses speaker-adaptive boundaries ($F_0$ in semitones relative to speaker median), evaluations across female speakers, pediatric voices, or non-native accents should utilize reference-free population mode or provide an in-distribution reference take.
2. **Vintage Acoustic Noise Floor**: 1930s–1960s audio contains shellac/optical recording surface noise. Flaws that rely on noise floor differentiation (e.g. `breathy_unclear`) were disabled in contrastive mode because window shifts on unvoiced consonants triggered false positives.
3. **Subtle Flaw Sensitivity (Level 3)**: Natural human speech exhibits localized rate variations of 10–20%. Level 3 perturbations blend into baseline expressive variance and are intentionally filtered by hysteresis thresholds to prevent false positives on Level 4.
