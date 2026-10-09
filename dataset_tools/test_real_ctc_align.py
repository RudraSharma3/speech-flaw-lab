"""
Test Real CTC Forced Alignment with torchaudio and merge tokens into exact word timestamps.
"""

import re

import numpy as np
import soundfile as sf
import torch
import torchaudio


def run_test():
    audio, sr = sf.read("data/processed/jfk_rice_excerpt_real.wav")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    waveform = torch.from_numpy(audio).float().unsqueeze(0)
    if sr != 16000:
        resampler = torchaudio.transforms.Resample(sr, 16000)
        waveform = resampler(waveform)

    bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
    model = bundle.get_model()
    labels = bundle.get_labels()
    dictionary = {c: i for i, c in enumerate(labels)}

    with torch.inference_mode():
        emissions, _ = model(waveform)
        emissions = torch.log_softmax(emissions, dim=-1)

    # Frame duration: 20ms per frame
    num_frames = emissions.size(1)
    total_audio_s = waveform.size(1) / 16000.0
    frame_dur_s = total_audio_s / num_frames

    transcript = (
        "140000 miles away from the control station in Houston a giant rocket more than 300 feet tall "
        "the length of this football field made of new metal alloys some of which have not yet been embedded "
        "capable of standing heat and stresses several times more than have ever been experienced "
        "pitted together with a precision better than the finest watch carrying all the equipment needed "
        "for propulsion guidance control communication food and survival on an untried mission to an unknown celestial body "
        "and then return it safely to earth re-entering the atmosphere at speeds of over 25000 miles per hour "
        "causing heat about half that on the temperature of the sun almost as hot as it is here today "
        "and do all this and do all this and do it right and do it first if all this thick heat is out then we must be bald ."
    )

    # Parse words and punctuation metadata
    token_pattern = re.compile(r"^([a-zA-Z0-9\'-]+)([\.,\?!;:]*)$")
    words_data = []
    for tok in transcript.strip().split():
        m = token_pattern.match(tok)
        if m:
            w_text = m.group(1).lower()
            punct = m.group(2)
            words_data.append({"text": w_text, "punct": punct, "has_punct": len(punct) > 0})

    clean_words = [re.sub(r"[^A-Z]", "", w["text"].upper()) for w in words_data if re.sub(r"[^A-Z]", "", w["text"].upper())]
    full_text = "|".join(clean_words) + "|"
    targets = torch.tensor([[dictionary[c] for c in full_text if c in dictionary]], dtype=torch.int32)

    alignments, scores = torchaudio.functional.forced_align(emissions, targets, blank=0)
    token_spans = torchaudio.functional.merge_tokens(alignments[0], scores[0])

    aligned_words = []
    curr_w_start = None
    curr_w_end = None
    curr_w_idx = 0

    for span in token_spans:
        tok_char = labels[span.token]
        if tok_char == "|":
            if curr_w_start is not None and curr_w_idx < len(words_data):
                w_meta = words_data[curr_w_idx]
                start_s = curr_w_start * frame_dur_s
                end_s = curr_w_end * frame_dur_s
                aligned_words.append({
                    "word_idx": curr_w_idx,
                    "text": w_meta["text"],
                    "punctuation": w_meta["punct"],
                    "has_punctuation": w_meta["has_punct"],
                    "start": round(start_s, 3),
                    "end": round(end_s, 3),
                    "duration": round(end_s - start_s, 3),
                })
                curr_w_idx += 1
                curr_w_start = None
                curr_w_end = None
        else:
            if curr_w_start is None:
                curr_w_start = span.start
            curr_w_end = span.end

    if curr_w_start is not None and curr_w_idx < len(words_data):
        w_meta = words_data[curr_w_idx]
        start_s = curr_w_start * frame_dur_s
        end_s = curr_w_end * frame_dur_s
        aligned_words.append({
            "word_idx": curr_w_idx,
            "text": w_meta["text"],
            "punctuation": w_meta["punct"],
            "has_punctuation": w_meta["has_punct"],
            "start": round(start_s, 3),
            "end": round(end_s, 3),
            "duration": round(end_s - start_s, 3),
        })

    print(f"Total Words Aligned: {len(aligned_words)}")
    print("\n--- FIRST 20 WORDS ---")
    for w in aligned_words[:20]:
        print(f"  #{w['word_idx']:02d} {w['text']:12s} [{w['start']:6.3f}s -> {w['end']:6.3f}s] (dur: {w['duration']:5.3f}s, punct: '{w['punctuation']}')")

    durations = [w["duration"] for w in aligned_words]
    print("\n--- DURATION DISTRIBUTION (Real, Irregular Spans) ---")
    print(f"Min duration: {min(durations):.3f}s, Max duration: {max(durations):.3f}s, Mean: {np.mean(durations):.3f}s, Median: {np.median(durations):.3f}s")
    hist, bin_edges = np.histogram(durations, bins=8)
    for i in range(len(hist)):
        print(f"  [{bin_edges[i]:.3f}s - {bin_edges[i+1]:.3f}s]: {'#' * hist[i]} ({hist[i]})")

if __name__ == "__main__":
    run_test()
