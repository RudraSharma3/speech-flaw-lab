# User Self-Recordings Directory (Out-of-Distribution Evaluation)

This directory holds real user self-recordings for out-of-distribution evaluation.

## Recommended Protocol

1. Record an **Ideal Reference Take** (Level 4):
   - Save as `user_speech_01_ideal.wav`
   - Provide the exact spoken transcript in `user_speech_01_transcript.txt`

2. Record one or more **Flawed Takes** speaking the same text with deliberate prosodic variations:
   - `user_speech_01_flawed_rushed.wav` (fast pacing)
   - `user_speech_01_flawed_monotone.wav` (flat pitch modulation)
   - `user_speech_01_flawed_pauses.wav` (unnatural hesitations)

3. Run automated analysis:
   ```bash
   python dataset_tools/ingest_self_recordings.py
   ```
   The pipeline will score each take contrastively against the ideal take and output an evaluation table.
