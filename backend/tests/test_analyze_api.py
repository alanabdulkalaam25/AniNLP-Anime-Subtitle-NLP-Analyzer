"""End-to-end tests for subtitle uploads."""

from fastapi.testclient import TestClient

from app.api.routes.analyze import rate_limiter
from app.main import app

client = TestClient(app)

_VALID_SRT = "1\n00:00:01,000 --> 00:00:03,000\n学校へ行きます。"


def test_analyze_endpoint_returns_dashboard_payload() -> None:
    response = client.post(
        "/api/analyze",
        files={
            "file": ("episode.srt", _VALID_SRT.encode("utf-8"), "application/x-subrip")
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["subtitle"] == {"filename": "episode.srt", "subtitle_count": 1}
    assert payload["statistics"]["total_tokens"] == 5
    assert payload["sentences"][0]["tokens"][2]["base"] == "行く"
    assert payload["jlpt_distribution"]["N5"] == 2


def test_analyze_endpoint_sanitizes_filename() -> None:
    response = client.post(
        "/api/analyze",
        files={
            "file": (
                "../../nested/path/sample.srt",
                _VALID_SRT.encode("utf-8"),
                "application/x-subrip",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["subtitle"]["filename"] == "sample.srt"


def test_analyze_endpoint_accepts_utf16() -> None:
    response = client.post(
        "/api/analyze",
        files={
            "file": (
                "utf16.srt",
                _VALID_SRT.encode("utf-16"),
                "application/x-subrip",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["statistics"]["total_tokens"] == 5


def test_analyze_endpoint_rejects_non_srt_and_malformed_content() -> None:
    wrong_type = client.post(
        "/api/analyze", files={"file": ("episode.txt", b"text/plain")}
    )
    malformed = client.post(
        "/api/analyze", files={"file": ("episode.srt", b"not an srt")}
    )

    assert wrong_type.status_code == 400
    assert wrong_type.json()["detail"] == "Please upload a valid .srt file."
    assert malformed.status_code == 422
    assert "incomplete" in malformed.json()["detail"]


def test_analyze_endpoint_rejects_non_positive_cue_index_cleanly() -> None:
    invalid_index = "0\n00:00:01,000 --> 00:00:03,000\nテスト"
    response = client.post(
        "/api/analyze",
        files={"file": ("invalid.srt", invalid_index.encode(), "application/x-subrip")},
    )

    assert response.status_code == 422
    assert "cue indexes must be >= 1" in response.json()["detail"]


def test_analyze_endpoint_allows_both_local_vite_origins() -> None:
    response = client.options(
        "/api/analyze",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_analyze_endpoint_rejects_oversized_subtitle_text() -> None:
    content = f"1\n00:00:01,000 --> 00:00:03,000\n{'a' * 500_001}".encode()

    response = client.post(
        "/api/analyze", files={"file": ("large.srt", content, "application/x-subrip")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Subtitle text is too large to analyze."


def test_analyze_endpoint_rejects_oversized_content_length() -> None:
    response = client.post(
        "/api/analyze",
        files={"file": ("big.srt", b"1\n00:00:01,000 --> 00:00:02,000\nhi", "application/x-subrip")},
        headers={"Content-Length": "20000000"},
    )

    assert response.status_code == 400
    assert "limit" in response.json()["detail"]


def test_analyze_endpoint_rate_limits_a_client() -> None:
    rate_limiter.reset()
    responses = [
        client.post("/api/analyze", files={"file": ("episode.txt", b"text/plain")})
        for _ in range(11)
    ]

    assert responses[-1].status_code == 429
    assert responses[-1].headers["retry-after"]
    rate_limiter.reset()
