import asyncio
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logger_config import setup_logger
from app.dependencies.supabase import get_authenticated_user
from app.services.embedding_service import embedding_service
from app.services.story_service_with_dna import StoryService
from app.services.cache_service import cache_service


router = APIRouter()
logger = setup_logger(__name__)


@router.get("/admin/performance")
async def get_performance_stats(user = Depends(get_authenticated_user)):
    """Get detailed performance statistics."""
    try:
        story_stats = await StoryService().get_service_stats()
        embedding_stats = await embedding_service.get_service_stats()
        return {
            "story_service": story_stats,
            "embedding_service": embedding_stats,
            "timestamp": asyncio.get_event_loop().time(),
        }
    except Exception as e:
        logger.error("Performance stats failed: {}".format(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance stats",
        )


@router.post("/admin/cache/clear")
async def clear_cache(pattern: str = "", user = Depends(get_authenticated_user)):
    """Clear cache by pattern."""
    try:
        if pattern:
            await cache_service.clear_pattern(pattern)
            return {"message": "Cleared cache pattern: {}".format(pattern)}
        else:
            cache_service._memory_cache.clear()
            return {"message": "Cleared memory cache"}
    except Exception as e:
        logger.error("Cache clear failed: {}".format(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache",
        )


@router.get("/performance/chapter_save")
async def get_chapter_save_performance():
    """Get performance metrics for chapter save operations"""
    try:
        from app.services.fixed_optimized_chapter_service import (
            fixed_optimized_chapter_service as optimized_chapter_service,
        )

        metrics = optimized_chapter_service._get_performance_metrics()
        return {
            "success": True,
            "performance_metrics": metrics,
            "optimization_features": {
                "async_pipeline": True,
                "vector_embeddings": True,
                "background_processing": True,
                "batch_operations": True,
                "smart_chunking": True,
                "parallel_execution": True,
            },
            "recommendations": {
                "avg_save_time_target": "< 3.0 seconds",
                "memory_usage_target": "< 500 MB",
                "vector_chunks_optimal": "5-15 chunks per chapter",
            },
        }
    except Exception as e:
        logger.error("Failed to get performance metrics: {}".format(e))
        return {"success": False, "error": str(e)}


