"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analyze import router as analyze_router
from app.api.routes.health import router as health_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(analyze_router, prefix=settings.api_prefix)


_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "connect-src 'self'; "
    "frame-ancestors 'none'"
)
_API_CSP = "default-src 'none'; frame-ancestors 'none'"


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path in {"/docs", "/redoc", "/docs/oauth2-redirect"}:
        response.headers.setdefault("Content-Security-Policy", _DOCS_CSP)
    else:
        response.headers.setdefault("Content-Security-Policy", _API_CSP)

    if path.startswith(settings.api_prefix):
        response.headers.setdefault("Cache-Control", "no-store")

    response.headers.setdefault(
        "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
    )
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
    )
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    return response
