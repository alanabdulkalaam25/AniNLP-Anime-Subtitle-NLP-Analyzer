"""Runtime configuration for the AniNLP API."""

from dataclasses import dataclass
import os


_LOCAL_FRONTEND_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")


def _cors_origins() -> tuple[str, ...]:
    """Read a comma-separated origin allowlist, with safe local defaults."""
    configured_origins = os.getenv("CORS_ORIGINS")
    if not configured_origins:
        return _LOCAL_FRONTEND_ORIGINS
    return tuple(
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    )


@dataclass(frozen=True)
class Settings:
    app_name: str = "AniNLP API"
    api_prefix: str = "/api"
    cors_origins: tuple[str, ...] = _cors_origins()
    max_upload_size_bytes: int = 10 * 1024 * 1024
    max_subtitle_text_chars: int = 500_000
    analysis_timeout_seconds: float = 30.0
    max_concurrent_analyses: int = 1
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60


settings = Settings()
