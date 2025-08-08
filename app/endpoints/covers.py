import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from logger_config import setup_logger
from dependencies import get_authenticated_user, get_supabase_client
from app.flows.cover_lcel import run_cover_flow



router = APIRouter()
logger = setup_logger(__name__)

# Sync wrapper for background execution (new event loop)
def _run_cover_flow_sync(story_id: int, user_id: str, user_email: str) -> None:
    try:
        logger.info("[COVER][LCEL] background thread starting flow story_id=%s", story_id)
        asyncio.run(run_cover_flow(story_id, user_id, user_email))
    except Exception as e:
        logger.error("[COVER][LCEL] background thread failed story_id=%s err=%s", story_id, str(e))

@router.post("/story/{story_id}/generate_cover")
async def generate_cover_endpoint(
    story_id: int,
    force: bool = Query(False),
    user = Depends(get_authenticated_user)
):
    """
    Trigger LCEL cover flow (non-blocking). Returns immediately while the
    background flow fetches outline, builds prompt, generates image, uploads
    to storage, and updates the "Stories" row with a permanent URL.
    """
    logger.info(
        "[COVER][LCEL] enqueue request story_id=%s user_id=%s force=%s",
        story_id, getattr(user, "id", None), force
    )
    supabase = get_supabase_client()

    # Verify ownership and current status
    row = supabase.table("Stories").select(
        "cover_generation_status"
    ).eq("id", story_id).eq("user_id", user.id).single().execute().data

    if not row:
        raise HTTPException(status_code=404, detail="Story not found")

    if (row.get("cover_generation_status") or "none") == "generating" and not force:
        logger.warning("[COVER][LCEL] already generating — re-enqueueing flow story_id=%s", story_id)
        asyncio.create_task(run_cover_flow(story_id, str(user.id), user.email or ""))
        return {"success": False, "status": "generating", "message": "Re-enqueued"}

    # Mark as generating and enqueue LCEL flow
    supabase.table("Stories").update({
        "cover_generation_status": "generating"
    }).eq("id", story_id).eq("user_id", user.id).execute()
    logger.info("[COVER][LCEL] status set to generating; scheduling LCEL story_id=%s", story_id)

    asyncio.create_task(run_cover_flow(story_id, str(user.id), user.email or ""))
    logger.info("[COVER][LCEL] LCEL scheduled story_id=%s", story_id)
    
    # Return a shape that the frontend already handles to start polling
    return {"success": False, "status": "generating", "message": ("Re-enqueued (force)" if force else "Enqueued")}

@router.get("/story/{story_id}/cover_status")
async def get_cover_status_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """
    Get the current cover generation status for a story.
    
    Returns status and cover URL if available.
    """
    # Get a fresh Supabase client per request
    supabase = get_supabase_client()
    try:
        logger.info("[COVER][STATUS] fetch story_id=%s", story_id)
        story_response = supabase.table("Stories").select(
            "cover_image_url, cover_generation_status, cover_generated_at, cover_image_width, cover_image_height, cover_aspect_ratio"
        ).eq("id", story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            logger.warning("[COVER][STATUS] story_not_found story_id=%s user_id=%s", story_id, user.id)
            raise HTTPException(status_code=404, detail="Story not found")
        
        story = story_response.data[0]
        logger.info("[COVER][STATUS] status=%s has_url=%s",
                    story.get("cover_generation_status"), bool(story.get("cover_image_url")))
        
        return {
            "success": True,
            "story_id": story_id,
            "cover_image_url": story.get("cover_image_url"),
            "image_width": story.get("cover_image_width"),
            "image_height": story.get("cover_image_height"),
            "aspect_ratio": story.get("cover_aspect_ratio"),
            "status": story.get("cover_generation_status", "none"),
            "generated_at": story.get("cover_generated_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting cover status for story {story_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cover status")

@router.post("/story/{story_id}/generate_cover_sync_debug")
async def generate_cover_sync_debug(
    story_id: int,
    user = Depends(get_authenticated_user),
):
    logger.info("[COVER][LCEL][DEBUG] starting synchronous flow story_id=%s", story_id)
    result = await run_cover_flow(story_id, str(user.id), user.email or "")
    return {"ok": True, "result": result}
