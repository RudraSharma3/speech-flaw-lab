"""
Integration tests for FastAPI endpoints.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

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
    response = client.get("/results/demo_jfk_moon_level1_flawed")
    assert response.status_code == 200
    result = response.json()
    assert result["meta"]["analysis_id"] == "demo_jfk_moon_level1_flawed"
    assert len(result["flaws"]) > 0
    assert result["scores"]["overall"] < 60.0
