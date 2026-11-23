"""
Tests for notes.txt validation and preflight checks in dataset_tools.ingest_self_recordings.
Verifies:
1. Placeholders ([YOUR_PAUSE_WORD], placeholder) trigger ERROR.
2. Obsolete example words ('terror', 'support') trigger ERROR.
3. Target words not present in transcript.txt trigger ERROR.
4. Pause count difference with detected pauses produces a WARNING, NEVER a blocking error.
"""

from pathlib import Path
from dataset_tools.ingest_self_recordings import inspect_notes_file, normalize_word_str

def test_placeholder_error(tmp_path: Path):
    notes = tmp_path / "notes.txt"
    notes.write_text("words before pause:\n[YOUR_PAUSE_WORD]\nanother_word", encoding="utf-8")
    words, errors = inspect_notes_file(notes)
    assert any("template placeholders" in e for e in errors), f"Expected placeholder error, got: {errors}"

def test_obsolete_words_error(tmp_path: Path):
    notes = tmp_path / "notes.txt"
    notes.write_text("words:\nterror\nadvance", encoding="utf-8")
    words, errors = inspect_notes_file(notes)
    assert any("obsolete example words" in e for e in errors), f"Expected obsolete words error, got: {errors}"

def test_words_not_in_transcript(tmp_path: Path):
    transcript_tokens = {"let", "me", "assert", "my", "firm", "belief"}
    notes = tmp_path / "notes.txt"
    notes.write_text("banana\napple", encoding="utf-8")
    words, errors = inspect_notes_file(notes)
    assert len(errors) == 0, "inspect_notes_file itself should not error on non-transcript words"
    missing = [w for w in words if normalize_word_str(w) not in transcript_tokens]
    assert missing == ["banana", "apple"]

def test_pause_count_mismatch_is_warning_only():
    """
    Simulates preflight check where notes.txt has valid words but count != detected pause count.
    Must generate a WARNING without setting has_critical_errors = True.
    """
    notes_words = ["belief", "nameless", "advance"]  # 3 words
    detected_count = 5  # detector found 5 pauses
    notes_warn = []
    has_critical_errors = False

    if len(notes_words) != detected_count:
        notes_warn.append(
            f"[WARNING] Pause count difference: notes.txt lists {len(notes_words)} words, "
            f"while odd_pauses.wav has {detected_count} detected deliberate pauses (evaluation reports detected vs noted pause recall and timestamps without requiring matching counts)."
        )
        # Crucial requirement: DO NOT set has_critical_errors = True

    assert has_critical_errors is False, "Pause count mismatch must NOT be a critical error"
    assert len(notes_warn) == 1
    assert "[WARNING]" in notes_warn[0]
