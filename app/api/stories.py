from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies.supabase import (
    get_authenticated_user,
    get_authenticated_user_optional,
    get_supabase_client as deps_get_supabase_client,
)
from app.core.logger_config import setup_logger
from app.services.story_service_with_dna import StoryService
from app.services.embedding_service import embedding_service


router = APIRouter()
logger = setup_logger(__name__)
story_service = StoryService()


@router.get("/stories")
async def get_user_stories_optimized(user = Depends(get_authenticated_user)):
    """Get user Stories with caching and async operations."""
    logger.info(f"Fetching Stories for user {user.id}")

    try:
        Stories = await story_service.get_user_Stories(user.id)

        story_list = []
        for story in Stories:
            try:
                story_data = {
                    "id": story.id,
                    "title": story.title,
                    "outline": story.outline or "",
                    "created_at": story.created_at.isoformat(),
                    "updated_at": story.updated_at.isoformat() if story.updated_at else None,
                    "chapter_count": story.current_chapter or 0,
                    "status": story.status or "draft",
                    "genre": story.genre or "Fiction",
                    # For backwards compatibility
                    "story_title": story.title,
                    "story_outline": story.outline or "",
                    # Cover image support
                    "cover_image_url": getattr(story, "cover_image_url", None),
                    "cover_generation_status": getattr(story, "cover_generation_status", None),
                }
                story_list.append(story_data)
            except Exception as e:
                logger.error(f"Error formatting story {story.id}: {e}")
                continue

        return {"stories": story_list}

    except Exception as e:
        logger.error(f"Failed to fetch Stories for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch Stories"
        )


# Backwards-compatible alias (capital S) used by some clients
@router.get("/Stories")
async def get_user_Stories_alias(user = Depends(get_authenticated_user)):
    return await get_user_stories_optimized(user)


@router.get("/story/{story_id}")
async def get_story_details(story_id: int, user = Depends(get_authenticated_user_optional)):
    """Get details for a specific story."""
    supabase = deps_get_supabase_client()
    try:
        query = supabase.table("Stories").select("*").eq("id", story_id)

        if user:
            story_response = query.or_(f"user_id.eq.{user.id},is_public.eq.true").execute()
        else:
            story_response = query.eq("is_public", True).execute()

        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        story = story_response.data[0]

        return {
            "id": story["id"],
            "story_title": story["story_title"],
            "story_outline": story.get("story_outline", ""),
            "summary": story.get("summary", ""),
            "created_at": story["created_at"],
            "published_at": story.get("published_at"),
            "genre": story.get("genre", ""),
            "total_chapters": story.get("total_chapters", 0),
            "current_chapter": story.get("current_chapter", 0),
            "is_public": story.get("is_public", False),
            "author_name": story.get("author_name", "Anonymous Author"),
            "cover_image_url": story.get("cover_image_url"),
            "estimated_total_words": story.get("estimated_total_words", 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch story {story_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch story details")


@router.get("/story/{story_id}/chapters")
async def get_story_chapters(
    story_id: int, response: Response, user = Depends(get_authenticated_user_optional)
):
    """Get all chapters for a specific story."""
    supabase = deps_get_supabase_client()
    try:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        query = supabase.table("Stories").select("*").eq("id", story_id)

        if user:
            story_response = query.or_(f"user_id.eq.{user.id},is_public.eq.true").execute()
        else:
            story_response = query.eq("is_public", True).execute()

        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        chapters_response = (
            supabase.table("Chapters")
            .select("*")
            .eq("story_id", story_id)
            .eq("is_active", True)
            .order("chapter_number")
            .execute()
        )

        chapters = []
        for chapter in chapters_response.data or []:
            chapters.append(
                {
                    "id": chapter["id"],
                    "chapter_number": chapter["chapter_number"],
                    "title": chapter.get("title", f"Chapter {chapter['chapter_number']}"),
                    "content": chapter["content"],
                    "summary": chapter.get("summary", ""),
                    "created_at": chapter["created_at"],
                    "word_count": len(chapter["content"].split()) if chapter["content"] else 0,
                }
            )

        return {"chapters": chapters}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch chapters for story {story_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch story chapters")


@router.post("/Stories/{story_id}/ensure_embeddings")
async def ensure_embeddings_endpoint(story_id: int, user = Depends(get_authenticated_user)):
    """Ensure embeddings exist for a story (creates if missing)."""
    try:
        # Verify story ownership
        supabase = deps_get_supabase_client()
        story_response = (
            supabase.table("Stories").select("id").eq("id", story_id).eq("user_id", user.id).execute()
        )
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        result = await embedding_service.ensure_embeddings(story_id)
        return {"success": result.get("status") in {"exists", "created"}, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ensure embeddings for story {story_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to ensure embeddings")


