"""Tests for the cue translation service and endpoint."""

from __future__ import annotations

import asyncio
import re

from fastapi.testclient import TestClient
import httpx

from app.api.routes import translate as translate_route
from app.main import app
from app.services.translator import SubtitleTranslator, TranslationResult


def _form_value(request: httpx.Request, key: str) -> str:
    return httpx.QueryParams(request.content.decode("utf-8"))[key]


def _batch_response(text: str) -> httpx.Response:
    """Build a Google-shaped response that preserves CUE markers."""
    segments = []
    for line in text.split("\n"):
        match = re.match(r"<<<CUE_(\d+)>>> (.*)", line)
        if not match:
            continue
        index, source = match.groups()
        segments.append(
            [
                f"<<<CUE_{index}>>> EN:{source}",
                line,
                None,
                None,
                3,
                None,
                None,
                [[]],
                [],
            ]
        )
    return httpx.Response(200, json=[segments, None, "ja", None, None, None, None, []])


def test_google_translates_a_batch_with_markers() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _batch_response(_form_value(request, "q"))

    translator = SubtitleTranslator(transport=httpx.MockTransport(handler))
    result = asyncio.run(translator.translate_many(["こんにちは", "さようなら"]))

    assert result.translations == ["EN:こんにちは", "EN:さようなら"]
    assert result.failed_count == 0
    assert len(requests) == 1


def test_google_deduplicates_repeated_cues() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _batch_response(_form_value(request, "q"))

    translator = SubtitleTranslator(transport=httpx.MockTransport(handler))
    result = asyncio.run(
        translator.translate_many(["こんにちは", "こんにちは", "さようなら"])
    )

    assert result.translations == ["EN:こんにちは", "EN:こんにちは", "EN:さようなら"]
    assert len(requests) == 1


def test_google_joins_segments_split_inside_a_cue() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                [
                    ["<<<CUE_0>>> Good", "<<<CUE_0>>> こん", None, None, 3],
                    ["bye", "にちは", None, None, 3],
                ],
                None,
                "ja",
                None,
                None,
                None,
                None,
                [],
            ],
        )

    translator = SubtitleTranslator(transport=httpx.MockTransport(handler))
    result = asyncio.run(translator.translate_many(["こんにちは"]))

    assert result.translations == ["Goodbye"]


def test_google_retries_individual_cues_when_markers_are_lost() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        text = _form_value(request, "q")
        if "<<<CUE_" in text:
            return httpx.Response(
                200,
                json=[
                    [["Batch translation", text, None, None, 3]],
                    None,
                    "ja",
                    None,
                    None,
                    None,
                    None,
                    [],
                ],
            )
        return httpx.Response(
            200,
            json=[
                [[f"EN:{text}", text, None, None, 3]],
                None,
                "ja",
                None,
                None,
                None,
                None,
                [],
            ],
        )

    translator = SubtitleTranslator(transport=httpx.MockTransport(handler))
    result = asyncio.run(translator.translate_many(["こんにちは", "さようなら"]))

    assert result.translations == ["EN:こんにちは", "EN:さようなら"]
    assert len(requests) == 3


def test_network_failure_returns_aligned_nulls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("provider unavailable", request=request)

    translator = SubtitleTranslator(transport=httpx.MockTransport(handler))
    result = asyncio.run(translator.translate_many(["こんにちは", "さようなら"]))

    assert result.translations == [None, None]
    assert result.failed_count == 2


def test_deepl_provider_uses_batch_payload() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "translations": [
                    {"detected_source_language": "JA", "text": "Hello"},
                    {"detected_source_language": "JA", "text": "Goodbye"},
                ]
            },
        )

    translator = SubtitleTranslator(
        provider="deepl",
        deepl_api_key="test-key:fx",
        transport=httpx.MockTransport(handler),
    )
    result = asyncio.run(translator.translate_many(["こんにちは", "さようなら"]))

    assert result.translations == ["Hello", "Goodbye"]
    assert requests[0].url.path == "/v2/translate"
    assert requests[0].headers["authorization"] == "DeepL-Auth-Key test-key:fx"


class _FakeTranslator:
    provider = "fake"

    async def translate_many(self, sentences: list[str]) -> TranslationResult:
        return TranslationResult(
            translations=[f"EN:{sentence}" for sentence in sentences],
            failed_count=0,
        )


def test_translate_endpoint_returns_aligned_translations(monkeypatch) -> None:
    translate_route.translation_rate_limiter.reset()
    monkeypatch.setattr(translate_route, "translator", _FakeTranslator())
    client = TestClient(app)

    response = client.post(
        "/api/translate", json={"sentences": ["こんにちは", "さようなら"]}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "translations": ["EN:こんにちは", "EN:さようなら"],
        "failed_count": 0,
        "provider": "fake",
    }


def test_translate_endpoint_rejects_empty_payload() -> None:
    client = TestClient(app)

    response = client.post("/api/translate", json={"sentences": []})

    assert response.status_code == 422


def test_translate_endpoint_allows_local_vite_origin() -> None:
    response = TestClient(app).options(
        "/api/translate",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_translate_endpoint_rate_limits_a_client(monkeypatch) -> None:
    translate_route.translation_rate_limiter.reset()
    monkeypatch.setattr(translate_route, "translator", _FakeTranslator())
    client = TestClient(app)

    responses = [
        client.post("/api/translate", json={"sentences": ["こんにちは"]})
        for _ in range(11)
    ]

    assert responses[-1].status_code == 429
    assert responses[-1].headers["retry-after"]
    translate_route.translation_rate_limiter.reset()
