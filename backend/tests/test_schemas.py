"""
Unit tests for Pydantic v2 schemas and mock result contract validation.
"""

import json
import os
from backend.schemas.api import AnalysisResult, JobStatus, SampleRecording


def test_mock_result_conforms_to_schema():
    mock_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "mock", "mock_result.json")
    assert os.path.exists(mock_path), "mock_result.json must exist"

    with open(mock_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate against AnalysisResult schema
    result = AnalysisResult.model_validate(data)
    assert result.meta.analysis_id == "demo_jfk_moon_level1_flawed"
    assert len(result.words) > 0
    assert len(result.series.t) > 0
    assert len(result.flaws) == 3
    assert result.scores.overall == 46.5
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
