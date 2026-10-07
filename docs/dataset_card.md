# Dataset Card: Contrastive Speech Analytics Dataset (CSAD-2026)

## 1. Dataset Summary

The **Contrastive Speech Analytics Dataset (CSAD-2026)** is an open-access multimodal dataset designed for benchmarking temporal speech flaw grounding and rubric-based speech quality evaluation. Unlike conventional speech datasets that rate ungrounded audio clips holistically, CSAD-2026 provides paired **ideal vs. flawed** recordings of the **exact same canonical text**, spanning a calibrated 5-tier quality gradient (Level 4 = Ideal to Level 0 = Egregiously Wrong) with exact millisecond ground-truth timestamps snapped to forced-aligned word and phoneme boundaries.

---

## 2. Dataset Structure & Hierarchy

```
/data
├── raw/                     # Original master recordings & audio clips
├── processed/               # Normalized 16kHz mono 16-bit WAV files
├── alignments/              # MFA Praat TextGrids & JSON word/phoneme tokens
├── annotations/             # Ground-truth temporal flaw JSON annotations
├── population_norms/        # LibriSpeech acoustic parameter priors
├── manifests/               # Dataset provenance and file metadata manifests
└── splits.json              # Speech-partitioned train/validation/test splits
```

---

## 3. Baseline Public Domain Speech Sources

Baselines are sourced from official US Federal Government / NASA historical archives under **Public Domain (17 U.S.C. § 105)**:

| Speech ID | Speaker | Event & Date | Canonical Duration | License Provenance |
| :--- | :--- | :--- | :---: | :--- |
| `jfk_moon_1962` | John F. Kennedy | Rice University Space Address (1962-09-12) | 17.5s (Excerpt) | Public Domain (US Gov) |
| `reagan_challenger_1986` | Ronald Reagan | Challenger Disaster Address (1986-01-28) | 24.0s (Excerpt) | Public Domain (US Gov) |
| `fdr_fear_itself_1933` | Franklin D. Roosevelt | First Inaugural Address (1933-03-04) | 20.0s (Excerpt) | Public Domain (US Gov) |

All master baseline audio files are normalized to **-20 LUFS** (BS.1770) at **16 kHz mono 16-bit PCM WAV** to prevent amplitude bias.

---

## 4. LibriSpeech Population Priors

To enable robust evaluation when no reference ideal take is provided, we compute population priors ($P_{10}, \text{Median}, \text{MAD}, P_{90}$) over 500 clean speech utterances from **LibriSpeech dev-clean / test-clean**:

- **Pitch Range ($F_0$ P10–P90)**: Median = 5.4 semitones ($\text{MAD} = 1.4\text{ st}$)
- **Articulation Rate**: Median = 4.3 syllables/sec ($\text{MAD} = 0.8\text{ syl/s}$)
- **Energy Contrast**: Median = 6.8 dB ($\text{MAD} = 1.9\text{ dB}$)
- **Harmonics-to-Noise Ratio (HNR)**: Median = 18.2 dB ($\text{MAD} = 2.6\text{ dB}$)
- **Syntactic Pause Duration**: Median = 0.52s at punctuation; 0.05s between non-punctuated words.

---

## 5. Parameterized Flaw Injection Gradient

Each master speech baseline is transformed across 5 discrete quality tiers:

| Quality Level | Label | Injected Flaw Types | Parameter Ranges | Target Rubric Score |
| :---: | :--- | :--- | :--- | :---: |
| **Level 4** | **Pristine Master** | None (Original baseline) | Nominal ($z \approx 0.0$) | **93 – 100 (A+)** |
| **Level 3** | **Near Perfect** | 1 minor localized flaw | $F_0$ compression 35%, rate $\pm 20\%$ | **80 – 92 (B/A)** |
| **Level 2** | **Slightly Flawed** | 2 distinct flaw regions | $F_0$ compression 60%, rate $+45\%$, pause 0.55s | **60 – 79 (C/C+)** |
| **Level 1** | **Flawed** | 3 distinct flaw regions | $F_0$ compression 80%, rate $+70\%$, pause 0.90s | **40 – 59 (D/D+)** |
| **Level 0** | **Egregious** | 4 multi-tier flaw regions | $F_0$ flatline 95%, rate $2\times$, pause 1.50s | **0 – 39 (F)** |

---

## 6. Dataset Splitting & Integrity Rules

1. **Text-Disjoint Splitting**: Splits are partitioned strictly by `speech_id` (the underlying text), ensuring that train, validation, and held-out test sets never share the same rhetorical transcript.
2. **Fixed Random Seed**: All random flaw permutations use seed `42`.
3. **Automated CI Validation**: Verified by `dataset_tools/validate_dataset.py` for duration bounds, word monotonicity, and SHA-256 checksums.

---

## 7. Ethical Considerations & Privacy

All recordings in the public domain tier are historical government addresses with no privacy or copyright restrictions. Self-recorded evaluation takes contain no private personally identifiable information (PII). Zero cloud APIs or remote tracking services are utilized.
