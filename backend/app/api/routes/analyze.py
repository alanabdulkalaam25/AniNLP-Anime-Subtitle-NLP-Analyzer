"""Subtitle upload and analysis endpoint."""

import asyncio

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.rate_limit import RateLimiter
from app.models.schemas import AnalysisResponse
from app.services.analysis_pipeline import AnalysisPipeline, decode_subtitle_content
from app.services.srt_parser import SRTParseError

router = APIRouter(tags=["analysis"])
pipeline = AnalysisPipeline()
analysis_slots = asyncio.Semaphore(settings.max_concurrent_analyses)
rate_limiter = RateLimiter(
    settings.rate_limit_requests, settings.rate_limit_window_seconds
)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_subtitle(
    request: Request, file: UploadFile = File(...)
) -> AnalysisResponse:
    """Analyze a UTF-8/CP932 SubRip subtitle upload without persisting it."""
    client_id = request.client.host if request.client else "unknown"
    allowed, retry_after = rate_limiter.allow(client_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many analysis requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    filename = file.filename or "subtitle.srt"
    if not filename.lower().endswith(".srt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a valid .srt file.",
        )

    content = await file.read(settings.max_upload_size_bytes + 1)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Subtitle file is empty."
        )
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subtitle file exceeds the 10 MB limit.",
        )

    try:
        decoded_content = decode_subtitle_content(content)
        if len(decoded_content) > settings.max_subtitle_text_chars:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subtitle text is too large to analyze.",
            )
        async with analysis_slots:
            return await asyncio.wait_for(
                run_in_threadpool(pipeline.analyze, decoded_content, filename),
                timeout=settings.analysis_timeout_seconds,
            )
    except asyncio.TimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Subtitle analysis timed out.",
        ) from error
    except HTTPException:
        raise
    except (SRTParseError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="NLP processing failed.",
        ) from error
