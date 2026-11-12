"""Tests for health endpoint availability."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok() -> None:
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"


def test_readiness_check_returns_ready() -> None:
    response = TestClient(app).get("/api/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_docs_csp_allows_cdn_resources() -> None:
    response = TestClient(app).get("/docs")

    assert response.status_code == 200
    csp = response.headers.get("content-security-policy", "")
    assert "https://cdn.jsdelivr.net" in csp
    assert "https://fastapi.tiangolo.com" in csp
