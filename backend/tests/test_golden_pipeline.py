"""
Golden integration test running the deterministic pipeline on real audio.
Verifies full end-to-end execution on data/processed/jfk_rice_excerpt_real.wav
and asserts that unmodified ideal speech is not heavily flagged.
"""

from pathlib import Path
import pytest

from backend.pipeline.orchestrator import run_speech_pipeline
from backend.schemas.api import AnalysisResult


@pytest.mark.slow
def test_golden_pipeline_real_jfk_audio():
    audio_path = Path("data/processed/jfk_rice_excerpt_real.wav")
    assert audio_path.exists(), f"Golden audio file not found at {audio_path}"
    
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
    
    # 1. Reference-Free Mode
    result_ref_free = run_speech_pipeline(
        audio_source=str(audio_path),
        transcript=transcript,
        filename="jfk_rice_excerpt_real.wav",
        reference_words=None,
        reference_id=None,
    )
    
    # Validate against Pydantic schema
    validated_ref_free = AnalysisResult.model_validate(result_ref_free)
    assert validated_ref_free.meta.filename == "jfk_rice_excerpt_real.wav"
    assert validated_ref_free.meta.duration_s > 60.0
    
    # Validate words and strict monotonicity
    words = validated_ref_free.words
    assert len(words) >= 100
    for i in range(len(words) - 1):
        assert words[i].text not in [".", ",", "!", "?", ";", ":"], "Punctuation must not be standalone word"
        assert words[i].start < words[i].end, f"Word #{i} start >= end"
        assert words[i].end <= words[i+1].start + 1e-3, f"Word #{i} overlaps word #{i+1}"
        
    # Reference-free score check
    assert validated_ref_free.scores.overall >= 70.0, "Reference-free score should be reasonable on real speech"
    assert len(validated_ref_free.flaws) <= 5, "Reference-free flaws should be sparse on unmodified speech"

    # 2. Contrastive Mode (Self-Ideal Take)
    result_contrastive = run_speech_pipeline(
        audio_source=str(audio_path),
        transcript=transcript,
        filename="jfk_rice_excerpt_real.wav",
        reference_words=[w.model_dump() for w in words],
        reference_id="jfk_rice_canonical",
    )
    
    validated_contrastive = AnalysisResult.model_validate(result_contrastive)
    assert validated_contrastive.scores.overall >= 90.0, "Contrastive self-ideal score must be >= 90.0"
    assert len(validated_contrastive.flaws) == 0, "Unmodified real speech must have 0 flaws in contrastive mode"
