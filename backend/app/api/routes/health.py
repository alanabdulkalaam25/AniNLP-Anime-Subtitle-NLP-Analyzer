"""Health check endpoint."""

from fastapi import APIRouter

from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return API availability without depending on NLP resources."""
    return HealthResponse()
