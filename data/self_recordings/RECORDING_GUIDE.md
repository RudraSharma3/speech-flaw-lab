# User Self-Recording Guide (Evaluation Protocol)

This directory (`data/self_recordings/`) is reserved for participant-recorded audio to evaluate out-of-distribution prosodic generalization against the canonical benchmark.

---

## 📄 Canonical Transcript to Read

Read the exact text below (canonical 47-second historical excerpt from Franklin D. Roosevelt's 1933 Inaugural Address):

> *"Let me assert my firm belief, that the only thing we have to fear is fear itself, nameless, unreasoning, unjustified terror, which paralyzes needed efforts to convert retreat into advance. In every dark hour of our national life, a leadership of frankness and a fitter has met with that understanding and support of the people themselves, which is essential to victory. And I am convinced to show a game, give that support, to leadership, in these critical days."*

- **Transcript File Location**: `data/self_recordings/transcript.txt`

---

## 🎙️ Required Audio Files & Delivery Descriptions

Record and save 5 separate audio takes into `data/self_recordings/`:

| Filename | Format | Intended Delivery & Acoustic Characteristics | Pipeline Role |
| :--- | :--- | :--- | :--- |
| **`take_a.wav`** (or `.m4a`) | WAV or M4A (any sample rate, mono/stereo) | **Ideal Take A (Canonical Reference)**: Your best natural, expressive, confident reading. Natural pitch variety, clean cadence, thoughtful pauses. | Ground-truth reference baseline for your voice. |
| **`take_b.wav`** (or `.m4a`) | WAV or M4A (any sample rate, mono/stereo) | **Ideal Take B (Independent Control)**: A second, distinct reading of the exact same text with good delivery. **Must be a genuinely independent recording** (different overall timing and natural acoustic differences). | False-Positive Control (verifies within-speaker consistency, flags/min). |
| **`monotone.wav`** (or `.m4a`) | WAV or M4A (any sample rate, mono/stereo) | **Monotone Take**: Intentionally flatten your pitch. Read with robotic, flatline intonation, avoiding expressive inflection or pitch jumps on stressed words. | Tests contrastive pitch modulation collapse detection. |
| **`rushed.wav`** (or `.m4a`) | WAV or M4A (any sample rate, mono/stereo) | **Rushed Take**: Speak noticeably fast (high articulation rate, $\ge 5.5$ syllables/sec), shortening vowel sounds and racing through clauses without pausing. | Tests tempo surge and syllabic compression detection. |
| **`odd_pauses.wav`** (or `.m4a`) | WAV or M4A (any sample rate, mono/stereo) | **Odd-Pauses Take**: Insert 2 or 3 deliberate, awkward, unpunctuated pauses ($\ge 1.0$ s silence) in the middle of sentences where there is no punctuation. | Tests temporal pause grounding against `notes.txt`. |

---

## 📝 Companion Annotation File: `notes.txt`

When recording `odd_pauses.wav`, note the exact word that immediately precedes each of your deliberate pauses.

### Format of `notes.txt`
List one word per line (or separated by commas) identifying the word spoken immediately before you paused:

```text
# Words immediately before deliberate awkward pauses in odd_pauses.wav:
terror
support
```

### Example
If you read:
- *"unjustified terror... [deliberate 1.5s silence] ...which paralyzes"* ➔ note `terror`
- *"and support... [deliberate 1.2s silence] ...of the people"* ➔ note `support`

The automated ingestion pipeline compares the exact detected pause timestamps against the word boundaries of `terror` and `support` to compute the **Noted Pause Recall Rate**.

---

## ⚙️ How to Ingest Once Files Are Dropped

Once you place your files into `data/self_recordings/`:

```bash
python -m dataset_tools.ingest_self_recordings
```

The tool will:
1. Validate that real files exist and verify independence between `take_a.wav` and `take_b.wav` (rejecting copies/trims).
2. Resample and normalize audio to -20 LUFS 16kHz mono.
3. Compute word-level alignments via torchaudio MMS_FA.
4. Score `take_b.wav` vs `take_a.wav` (independent false positive control).
5. Score `monotone.wav`, `rushed.wav`, and `odd_pauses.wav` against `take_a.wav`.
6. Contrast `take_a.wav` against Franklin D. Roosevelt's original 1933 master take ("speaker A (user) vs speaker B (orator)").
7. Update `results/benchmark.json` and generate report tables.
