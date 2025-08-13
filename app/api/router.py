from fastapi import APIRouter

from app.endpoints import covers, health
from app.api import chapters, create
from app.api import public, writing, stories
from app.api import choices, updates, branches, admin
import os
DEV_MODE = os.getenv("ENV", "development").lower() in {"dev", "development", "local"}


router = APIRouter()

# Built-in endpoints
router.include_router(health.router, tags=["health"])
router.include_router(covers.router, tags=["cover"])

# Public discovery/engagement endpoints
router.include_router(public.router, tags=["public"]) 

# Writing assistance endpoints
router.include_router(writing.router, tags=["writing"]) 

# Stories endpoints
router.include_router(stories.router, tags=["stories"]) 
router.include_router(create.router, tags=["create"]) 
router.include_router(chapters.router, tags=["chapters"]) 
router.include_router(choices.router, tags=["choices"]) 
router.include_router(updates.router, tags=["updates"]) 
router.include_router(branches.router, tags=["branches"]) 
router.include_router(admin.router, tags=["admin"]) 

# Dev/test endpoints (only in development)
if DEV_MODE:
    try:
        from app.api import dev_tests
        router.include_router(dev_tests.router, tags=["dev-tests"]) 
    except Exception:
        pass

# Chapters router will be included after main.py delegators are in place to avoid route duplication

# Create/save endpoints temporarily not included to avoid route duplication with main.py


