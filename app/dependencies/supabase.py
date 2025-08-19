# dependencies.py
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from supabase import create_client, Client
import asyncpg
from typing import AsyncGenerator
from app.core.logger_config import setup_logger
from app.core.config import settings
from collections import defaultdict
import base64
import json
import time as _time
import asyncio

logger = setup_logger(__name__)

# Lazy singleton Supabase client (sync) and async PostgreSQL connection pool
_supabase: Optional[Client] = None
_async_pool: Optional[asyncpg.Pool] = None
_async_lock = asyncio.Lock()

def get_supabase_client() -> Client:
    """Get synchronous Supabase client (for backward compatibility)"""
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        logger.info("Supabase sync client initialized")
    return _supabase

async def get_async_db_pool() -> asyncpg.Pool:
    """Get async PostgreSQL connection pool (RECOMMENDED for performance)"""
    global _async_pool
    if _async_pool is None:
        async with _async_lock:
            if _async_pool is None:
                _async_pool = await asyncpg.create_pool(
                    settings.SUPABASE_CONNECTION_STRING,
                    min_size=5,
                    max_size=settings.MAX_CONCURRENT_DB_CONNECTIONS,
                    command_timeout=10
                )
                logger.info("Async PostgreSQL pool initialized")
    return _async_pool

async def get_async_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get async database connection from pool"""
    pool = await get_async_db_pool()
    async with pool.acquire() as connection:
        yield connection

# Auth schemes
auth_scheme = HTTPBearer()
optional_auth_scheme = HTTPBearer(auto_error=False)

# Simple in-memory rate limiting for auth
_auth_attempts = defaultdict(list)
_MAX_AUTH_ATTEMPTS = 30
_AUTH_WINDOW = 60  # seconds

async def get_authenticated_user(request: Request, token = Depends(auth_scheme)):
    # Basic rate limit by client IP (from headers when behind proxy)
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip() or "unknown"
    now = _time.time()
    _auth_attempts[client_ip] = [t for t in _auth_attempts[client_ip] if now - t < _AUTH_WINDOW]
    if len(_auth_attempts[client_ip]) >= _MAX_AUTH_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many authentication attempts")
    _auth_attempts[client_ip].append(now)

    # Token checks (mirrors your main.py)
    if not token or not token.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")
    token_str = token.credentials.strip()
    if len(token_str) < 50 or token_str.count('.') != 2:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token structure")

    # Try decode header (lenient)
    try:
        hdr = token_str.split('.')[0]
        hdr += '=' * (4 - len(hdr) % 4)
        _ = json.loads(base64.b64decode(hdr) or b"{}")
    except Exception:
        pass

    supabase = get_supabase_client()
    user = supabase.auth.get_user(token_str).user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    # Reset rate-limit counter on successful auth
    _auth_attempts[client_ip].clear()
    return user

async def get_authenticated_user_optional(request: Request, token = Depends(optional_auth_scheme)):
    # Optional auth: if token is missing or invalid/expired, just return None
    if not token or not getattr(token, 'credentials', None):
        return None
    token_str = token.credentials.strip()
    try:
        # Ignore obviously malformed/short tokens to avoid unnecessary calls
        if len(token_str) < 50 or token_str.count('.') != 2:
            return None
        supabase = get_supabase_client()
        return supabase.auth.get_user(token_str).user
    except Exception as e:
        # Do not crash public endpoints due to expired/invalid tokens
        logger.warning(f"Optional auth token ignored: {e}")
        return None

async def get_current_user_from_token(token_string: str):
    supabase = get_supabase_client()
    user = supabase.auth.get_user(token_string).user
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user
