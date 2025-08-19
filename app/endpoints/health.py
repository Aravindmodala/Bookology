from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings
from app.dependencies.supabase import get_supabase_client, get_async_db_pool
from app.core.concurrency import concurrency_monitor

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}

@router.get("/healthz")
async def healthz():
    return {"status": "ok"}

@router.get("/readyz")
async def readyz():
    try:
        # Check both sync client and async pool
        _ = get_supabase_client()
        pool = await get_async_db_pool()
        # Test a simple query
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return {"status": "ready", "async_pool": "connected"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

@router.get("/version")
async def version():
    return {"version": "2.0.0", "env": {"debug": settings.DEBUG}}

@router.get("/metrics")
async def metrics():
    """Get current system metrics and concurrency stats."""
    return {
        "concurrency": concurrency_monitor.get_stats(),
        "config": {
            "workers": 4,
            "max_llm_calls": settings.MAX_CONCURRENT_LLM_CALLS,
            "max_db_connections": settings.MAX_CONCURRENT_DB_CONNECTIONS,
            "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "request_timeout": settings.REQUEST_TIMEOUT_SECONDS
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
