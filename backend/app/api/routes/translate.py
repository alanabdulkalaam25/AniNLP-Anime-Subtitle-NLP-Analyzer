"""English translation endpoint for analyzed subtitle cues."""

import asyncio

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.models.schemas import TranslationRequest, TranslationResponse
from app.services.translator import SubtitleTranslator, TranslationError

router = APIRouter(tags=["translation"])

translator = SubtitleTranslator(
    provider=settings.translation_provider,
    deepl_api_key=settings.deepl_api_key,
    timeout_seconds=settings.translation_timeout_seconds,
    batch_size=settings.translation_batch_size,
    max_chars_per_batch=settings.translation_max_chars_per_batch,
    max_concurrency=settings.translation_max_concurrency,
)
translation_rate_limiter = RateLimiter(
    settings.rate_limit_requests, settings.rate_limit_window_seconds
)


@router.post("/translate", response_model=TranslationResponse)
async def translate_subtitles(
    request: Request, payload: TranslationRequest
) -> TranslationResponse:
    """Translate cue text to English without persisting or logging the input."""
    client_id = request.client.host if request.client else "unknown"
    allowed, retry_after = translation_rate_limiter.allow(client_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many translation requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    if not settings.translation_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="English translation is not enabled on this server.",
        )

    if (
        sum(len(sentence) for sentence in payload.sentences)
        > settings.max_subtitle_text_chars
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subtitle text is too large to translate.",
        )

    try:
        result = await asyncio.wait_for(
            translator.translate_many(payload.sentences),
            timeout=settings.translation_timeout_seconds + 2.0,
        )
    except TranslationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except asyncio.TimeoutError:
        return TranslationResponse(
            translations=[None] * len(payload.sentences),
            failed_count=len(payload.sentences),
            provider=translator.provider,
        )

    return TranslationResponse(
        translations=result.translations,
        failed_count=result.failed_count,
        provider=translator.provider,
    )
