"""Health check endpoint."""

from functools import lru_cache

from fastapi import APIRouter

from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@lru_cache(maxsize=1)
def _warm_nlp_resources() -> None:
    """Load the tokenizer and JLPT data once, then reuse for every probe."""
    from app.services.jlpt_classifier import JLPTClassifier
    from app.services.morphological_analyzer import analyze_morphology

    analyze_morphology("テスト")
    JLPTClassifier()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return API availability without depending on NLP resources."""
    return HealthResponse()


@router.get("/ready", response_model=HealthResponse)
def readiness_check() -> HealthResponse:
    """Return API readiness, verifying NLP analyzer and vocabulary resources."""
    _warm_nlp_resources()
    return HealthResponse(status="ready")
