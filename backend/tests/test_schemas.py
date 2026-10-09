"""
Unit tests for Pydantic v2 schemas and mock result contract validation.
"""

import json
import os

from backend.schemas.api import AnalysisResult, JobStatus


def test_cached_result_conforms_to_schema():
    cached_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "cached_results", "jfk_moon_1962_level_1.json")
    assert os.path.exists(cached_path), "Cached result must exist"

    with open(cached_path, encoding="utf-8") as f:
        data = json.load(f)

    # Validate against AnalysisResult schema
    result = AnalysisResult.model_validate(data)
    assert len(result.meta.analysis_id) > 0
    assert len(result.words) > 0
    assert len(result.series.t) > 0
    assert len(result.flaws) > 0
    assert 0.0 <= result.scores.overall <= 100.0
    assert len(result.scores.dimensions) == 5


def test_job_status_schema():
    status = JobStatus(
        job_id="job_123",
        status="processing",
        progress=0.45,
        message="Running alignment",
    )
    assert status.status == "processing"
    assert status.progress == 0.45
