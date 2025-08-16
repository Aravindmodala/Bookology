import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from app.core.logger_config import setup_logger
from app.dependencies.supabase import get_authenticated_user, get_supabase_client
from app.flows.cover_lcel import run_cover_flow
from datetime import datetime
from app.services.cover_upload_service import CoverUploadService



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


@router.post("/story/{story_id}/upload_cover")
async def upload_cover_endpoint(
    story_id: int,
    file: UploadFile = File(...),
    user = Depends(get_authenticated_user)
):
    """Upload a user-provided cover image, validate/resize, store to Supabase, and persist URL."""
    try:
        supabase = get_supabase_client()

        # Verify ownership
        story_resp = supabase.table("Stories").select("id").eq("id", story_id).eq("user_id", user.id).execute()
        if not story_resp.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        # Read and validate file
        blob = await file.read()
        processed = CoverUploadService.validate_and_process(blob, file.content_type or "")

        # Upload to storage
        public_url = CoverUploadService.upload_to_supabase(supabase, str(user.id), story_id, processed)

        # Persist to DB
        supabase.table("Stories").update({
            "cover_image_url": public_url,
            "cover_generation_status": "uploaded",
            "cover_generated_at": datetime.utcnow().isoformat(),
            "cover_image_width": processed.width,
            "cover_image_height": processed.height,
            "cover_aspect_ratio": processed.aspect_ratio,
        }).eq("id", story_id).eq("user_id", user.id).execute()

        logger.info("[COVER][UPLOAD] Success story_id=%s url=%s", story_id, public_url)
        return {
            "success": True,
            "story_id": story_id,
            "cover_image_url": public_url,
            "image_width": processed.width,
            "image_height": processed.height,
            "aspect_ratio": processed.aspect_ratio,
            "status": "uploaded",
        }
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("[COVER][UPLOAD] Failed story_id=%s err=%s", story_id, e)
        raise HTTPException(status_code=500, detail="Failed to upload cover")


@router.delete("/story/{story_id}/cover")
async def remove_cover_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """Remove/reset the cover image metadata for a story (does not delete storage file)."""
    try:
        supabase = get_supabase_client()
        # Verify ownership
        story_resp = supabase.table("Stories").select("id").eq("id", story_id).eq("user_id", user.id).execute()
        if not story_resp.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        supabase.table("Stories").update({
            "cover_image_url": None,
            "cover_generation_status": "none",
            "cover_generated_at": None,
            "cover_image_width": None,
            "cover_image_height": None,
            "cover_aspect_ratio": None,
        }).eq("id", story_id).eq("user_id", user.id).execute()

        return {"success": True, "story_id": story_id, "status": "none"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[COVER][REMOVE] Failed story_id=%s err=%s", story_id, e)
        raise HTTPException(status_code=500, detail="Failed to remove cover")
