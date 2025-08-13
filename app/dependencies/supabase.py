# dependencies.py
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from supabase import create_client, Client
from app.core.logger_config import setup_logger
from app.core.config import settings
from collections import defaultdict
import base64
import json
import time as _time

logger = setup_logger(__name__)

# Lazy singleton Supabase client
_supabase: Optional[Client] = None

def get_supabase_client() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized (dependencies)")
    return _supabase

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
