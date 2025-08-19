from fastapi import FastAPI, Request, HTTPException, status
import uuid as _uuid
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
import time
import asyncio

from app.core.config import settings
from app.api.router import router as api_router
from app.core.logger_config import setup_logger

logger = setup_logger(__name__)


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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Fixed: Use the computed cors_origins instead of hardcoded ["*"]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting middleware
    rate_limit_store = defaultdict(list)
    
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """Simple rate limiting middleware."""
        # Skip rate limiting for health checks
        if request.url.path in ["/healthz", "/readyz", "/health"]:
            return await call_next(request)
        
        # Get client identifier (IP or user ID)
        client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not client_ip and request.client:
            client_ip = request.client.host
        client_id = client_ip or "unknown"
        
        # Check rate limit
        now = time.time()
        minute_ago = now - 60
        rate_limit_store[client_id] = [t for t in rate_limit_store[client_id] if t > minute_ago]
        
        if len(rate_limit_store[client_id]) >= settings.RATE_LIMIT_PER_MINUTE:
            logger.warning(f"Rate limit exceeded for {client_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {settings.RATE_LIMIT_PER_MINUTE} requests per minute."
            )
        
        rate_limit_store[client_id].append(now)
        
        # Add timeout for requests
        try:
            path = request.url.path
            return await asyncio.wait_for(
                call_next(request),
                timeout=settings.REQUEST_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Request timeout after {settings.REQUEST_TIMEOUT_SECONDS} seconds"
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


