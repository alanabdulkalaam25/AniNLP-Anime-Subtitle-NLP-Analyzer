"""Runtime configuration for the AniNLP API."""

from dataclasses import dataclass
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


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


def _cors_origin_regex() -> str | None:
    """Read an optional regex for origins such as Vercel preview deployments."""
    configured_regex = os.getenv("CORS_ORIGIN_REGEX")
    return configured_regex.strip() if configured_regex else None


@dataclass(frozen=True)
class Settings:
    app_name: str = "AniNLP API"
    api_prefix: str = "/api"
    cors_origins: tuple[str, ...] = _cors_origins()
    cors_origin_regex: str | None = _cors_origin_regex()
    max_upload_size_bytes: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))
    max_subtitle_text_chars: int = int(os.getenv("MAX_SUBTITLE_TEXT_CHARS", "500000"))
    analysis_timeout_seconds: float = float(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "30.0"))
    max_concurrent_analyses: int = int(os.getenv("MAX_CONCURRENT_ANALYSES", "1"))
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))


settings = Settings()
