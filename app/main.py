from fastapi import FastAPI, Request
import uuid as _uuid
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Bookology API", version="2.0.0")

    # Fail fast on missing critical env in production
    try:
        settings.validate_required_settings()
    except ValueError:
        if not settings.DEBUG:
            raise
        # In DEBUG, continue to ease local development

    # CORS: Restrict in production; wildcard only in development
    allow_all = settings.DEBUG
    cors_origins = ["*"] if allow_all else settings.ALLOWED_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        # Request/trace id
        req_id = request.headers.get("X-Request-ID") or str(_uuid.uuid4())
        response = await call_next(request)
        # Core security headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=(), payment=()")
        response.headers.setdefault("X-Request-ID", req_id)
        # HSTS (only if not DEBUG)
        if not settings.DEBUG:
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains; preload")
        # CSP (configurable)
        if settings.DEBUG:
            csp = (
                "default-src 'self'; "
                "img-src 'self' data: blob: *; "
                "media-src 'self' data: blob: *; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "connect-src 'self' *; "
                "font-src 'self' data:; "
                "frame-ancestors 'none'"
            )
        else:
            allowed_connect = ["'self'"] + [o for o in settings.ALLOWED_ORIGINS]
            csp = (
                "default-src 'self'; "
                "img-src 'self' data: blob:; "
                "media-src 'self' data: blob:; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                f"connect-src {' '.join(allowed_connect)}; "
                "font-src 'self' data:; "
                "frame-ancestors 'none'"
            )
        response.headers.setdefault("Content-Security-Policy", csp)
        return response

    app.include_router(api_router)
    return app
                       
app = create_app()


