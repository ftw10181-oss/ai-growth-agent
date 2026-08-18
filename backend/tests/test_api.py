from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


VALID_BRIEF = {
    "product": "AI Translation Earbuds",
    "product_description": "Real-time AI translation earbuds for cross-language communication.",
    "target_market": "United States",
    "target_audience": "Frequent international business travelers",
    "business_goal": "User Acquisition",
    "additional_context": "Entering the US market; test Reddit and TikTok."
}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.2.1"


def test_mock_insight_matches_contract() -> None:
    response = client.post("/api/analyze", json=VALID_BRIEF)
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "mock"
    assert len(body["user_insight"]["jobs_to_be_done"]) >= 3
    assert body["context"]["primary_goal"] == "User Acquisition"
    assert body["user_insight"]["pain_points"][0]["evidence"]["validation_status"] == "needs_validation"
    assert body["quality_review"]["status"] == "passed"
    assert body["quality_review"]["auto_revision_count"] == 0
    assert len(body["quality_review"]["checks"]) == 4


def test_v02_insight_alias_is_available() -> None:
    response = client.post("/api/v2/insights", json=VALID_BRIEF)
    assert response.status_code == 200
    assert response.json()["mode"] == "mock"


def test_versioned_insight_alias_remains_available() -> None:
    response = client.post("/api/v1/insights", json=VALID_BRIEF)
    assert response.status_code == 200
    assert response.json()["mode"] == "mock"


def test_invalid_goal_is_rejected() -> None:
    response = client.post(
        "/api/analyze", json={**VALID_BRIEF, "business_goal": "Go Viral"}
    )
    assert response.status_code == 422
