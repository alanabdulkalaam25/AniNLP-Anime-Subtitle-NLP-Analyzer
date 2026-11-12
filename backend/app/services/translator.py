"""Best-effort English translation for analyzed subtitle cues.

The default provider uses Google's public web translation endpoint, which
requires no API key. Cues are deduplicated and batched so a typical episode
costs a handful of requests rather than one request per line. A key-backed
DeepL provider is available through configuration.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass
import logging
import re

import httpx

logger = logging.getLogger(__name__)

_MARKER = re.compile(r"<<<\s*CUE_(\d+)\s*>>>")
_GOOGLE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"
_DEEPL_FREE_ENDPOINT = "https://api-free.deepl.com/v2/translate"
_DEEPL_PAID_ENDPOINT = "https://api.deepl.com/v2/translate"
_MAX_CACHE_ENTRIES = 5_000
_USER_AGENT = "AniNLP/0.1 (subtitle study tool)"


class TranslationError(RuntimeError):
    """Raised when translation is disabled or the provider is misconfigured."""


@dataclass(frozen=True)
class TranslationResult:
    """Translations aligned to the input order, with ``None`` for failures."""

    translations: list[str | None]
    failed_count: int


def _normalize(text: str) -> str:
    """Collapse whitespace so repeated cues share one translation request."""
    return " ".join(text.split())


class SubtitleTranslator:
    """Translate Japanese cue text to English with batching and a small cache."""

    def __init__(
        self,
        *,
        provider: str = "google",
        deepl_api_key: str | None = None,
        timeout_seconds: float = 45.0,
        batch_size: int = 20,
        max_chars_per_batch: int = 3_000,
        max_concurrency: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.provider = provider.strip().lower()
        self._deepl_api_key = deepl_api_key
        self._timeout = timeout_seconds
        self._batch_size = max(1, batch_size)
        self._max_chars_per_batch = max(200, max_chars_per_batch)
        self._max_concurrency = max(1, max_concurrency)
        if self.provider == "deepl":
            # DeepL accepts at most 50 texts in one request.
            self._batch_size = min(self._batch_size, 50)
        self._transport = transport
        self._cache: OrderedDict[str, str] = OrderedDict()

    async def translate_many(self, sentences: list[str]) -> TranslationResult:
        """Return English translations in the same order as ``sentences``."""
        if self.provider not in {"google", "deepl"}:
            raise TranslationError(
                "Translation is not configured. Set TRANSLATION_PROVIDER to "
                "'google' or 'deepl'."
            )
        if self.provider == "deepl" and not self._deepl_api_key:
            raise TranslationError(
                "TRANSLATION_PROVIDER is 'deepl' but DEEPL_API_KEY is not set."
            )

        normalized = [_normalize(sentence) for sentence in sentences]
        unique: list[str] = []
        seen: set[str] = set()
        for text in normalized:
            if text and text not in seen:
                seen.add(text)
                unique.append(text)

        translated: dict[str, str] = {}
        pending: list[str] = []
        for text in unique:
            cached = self._cache.get(text)
            if cached is not None:
                translated[text] = cached
                self._cache.move_to_end(text)
            else:
                pending.append(text)

        if pending:
            batches = self._build_batches(pending)
            semaphore = asyncio.Semaphore(self._max_concurrency)
            async with httpx.AsyncClient(
                timeout=min(self._timeout, 15.0),
                transport=self._transport,
                follow_redirects=True,
                headers={"User-Agent": _USER_AGENT},
            ) as client:
                batch_results = await asyncio.gather(
                    *(
                        self._translate_batch(client, batch, semaphore)
                        for batch in batches
                    ),
                    return_exceptions=True,
                )

            for batch_result in batch_results:
                if isinstance(batch_result, BaseException):
                    logger.warning("Translation batch failed: %s", batch_result)
                    continue
                translated.update(batch_result)
                self._remember(batch_result)

        output = [
            translated.get(text) if text else ""
            for text in normalized
        ]
        failed_count = sum(
            1
            for sentence, translation in zip(sentences, output)
            if _normalize(sentence) and translation is None
        )
        return TranslationResult(translations=output, failed_count=failed_count)

    def _build_batches(self, texts: list[str]) -> list[list[str]]:
        batches: list[list[str]] = []
        current: list[str] = []
        current_chars = 0
        for text in texts:
            cost = len(text) + 24  # room for the CUE marker and newline
            if current and (
                len(current) >= self._batch_size
                or current_chars + cost > self._max_chars_per_batch
            ):
                batches.append(current)
                current = []
                current_chars = 0
            current.append(text)
            current_chars += cost
        if current:
            batches.append(current)
        return batches

    def _remember(self, values: dict[str, str]) -> None:
        for text, translation in values.items():
            if not text or not translation:
                continue
            self._cache[text] = translation
            self._cache.move_to_end(text)
        while len(self._cache) > _MAX_CACHE_ENTRIES:
            self._cache.popitem(last=False)

    async def _translate_batch(
        self,
        client: httpx.AsyncClient,
        batch: list[str],
        semaphore: asyncio.Semaphore,
    ) -> dict[str, str]:
        async with semaphore:
            if self.provider == "deepl":
                return await self._deepl_batch(client, batch)
            return await self._google_batch(client, batch)

    async def _google_batch(
        self, client: httpx.AsyncClient, batch: list[str]
    ) -> dict[str, str]:
        marked = "\n".join(
            f"<<<CUE_{index}>>> {text}" for index, text in enumerate(batch)
        )
        response = await client.post(
            _GOOGLE_ENDPOINT,
            data={
                "client": "gtx",
                "sl": "ja",
                "tl": "en",
                "dt": "t",
                "q": marked,
            },
        )
        response.raise_for_status()

        parts = _MARKER.split(self._google_text(response))
        translated: dict[str, str] = {}
        for position in range(1, len(parts) - 1, 2):
            index = int(parts[position])
            text = parts[position + 1].strip()
            if 0 <= index < len(batch) and text:
                translated[batch[index]] = text

        if len(translated) == len(batch):
            return translated

        # If the provider split or removed a marker, retry only the missing cues.
        for text in batch:
            if text in translated:
                continue
            try:
                single = await self._google_single(client, text)
            except Exception as error:  # noqa: BLE001 - one cue must not fail the batch
                logger.warning("Single translation failed: %s", error)
                continue
            if single:
                translated[text] = single
        return translated

    async def _google_single(
        self, client: httpx.AsyncClient, text: str
    ) -> str | None:
        response = await client.post(
            _GOOGLE_ENDPOINT,
            data={
                "client": "gtx",
                "sl": "ja",
                "tl": "en",
                "dt": "t",
                "q": text,
            },
        )
        response.raise_for_status()
        translation = self._google_text(response).strip()
        return translation or None

    @staticmethod
    def _google_text(response: httpx.Response) -> str:
        payload = response.json()
        if not isinstance(payload, list) or not payload:
            return ""
        segments = payload[0]
        if not isinstance(segments, list):
            return ""
        pieces: list[str] = []
        for segment in segments:
            if isinstance(segment, list) and segment and isinstance(segment[0], str):
                pieces.append(segment[0])
        return "".join(pieces)

    async def _deepl_batch(
        self, client: httpx.AsyncClient, batch: list[str]
    ) -> dict[str, str]:
        endpoint = (
            _DEEPL_FREE_ENDPOINT
            if self._deepl_api_key and self._deepl_api_key.endswith(":fx")
            else _DEEPL_PAID_ENDPOINT
        )
        response = await client.post(
            endpoint,
            headers={"Authorization": f"DeepL-Auth-Key {self._deepl_api_key}"},
            json={"text": batch, "source_lang": "JA", "target_lang": "EN"},
        )
        response.raise_for_status()
        payload = response.json()
        entries = payload.get("translations", []) if isinstance(payload, dict) else []

        translated: dict[str, str] = {}
        for text, entry in zip(batch, entries):
            value = entry.get("text") if isinstance(entry, dict) else None
            if isinstance(value, str) and value.strip():
                translated[text] = value.strip()
        return translated
