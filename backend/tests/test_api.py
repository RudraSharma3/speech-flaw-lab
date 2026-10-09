"""
Integration tests for FastAPI endpoints.
"""

from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Contrastive Speech Analytics"


def test_samples_endpoint():
    response = client.get("/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) >= 5
    # Verify all 5 quality levels exist
    levels = {s["quality_level"] for s in samples}
    assert {0, 1, 2, 3, 4}.issubset(levels)


def test_results_endpoint_for_cached_sample():
    response = client.get("/results/jfk_moon_1962_level_1")
    assert response.status_code == 200
    result = response.json()
    assert len(result["meta"]["analysis_id"]) > 0
    assert len(result["flaws"]) > 0
    assert result["scores"]["overall"] < 80.0
