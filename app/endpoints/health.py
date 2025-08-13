from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings
from app.dependencies.supabase import get_supabase_client

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
        # lightweight readiness: ensure we can construct supabase client
        _ = get_supabase_client()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

@router.get("/version")
async def version():
    return {"version": "2.0.0", "env": {"debug": settings.DEBUG}}
