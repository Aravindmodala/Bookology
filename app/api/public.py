from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies.supabase import (
    get_authenticated_user,
    get_authenticated_user_optional,
    get_supabase_client as deps_get_supabase_client,
)
from app.core.logger_config import setup_logger
from pydantic import BaseModel, Field


router = APIRouter()
logger = setup_logger(__name__)


@router.patch("/story/{story_id}/visibility")
async def update_story_visibility(
    story_id: int,
    visibility_data: dict,
    user = Depends(get_authenticated_user),
):
    """Update story visibility (public/private)"""
    supabase = deps_get_supabase_client()
    try:
        logger.info(f"Updating visibility for story {story_id} by user {user.id}")

        is_public = visibility_data.get("is_public", False)
        update_data = {
            "is_public": is_public,
            "published_at": datetime.utcnow().isoformat() if is_public else None,
        }

        story_response = (
            supabase.table("Stories")
            .select("id")
            .eq("id", story_id)
            .eq("user_id", user.id)
            .execute()
        )
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        result = (
            supabase.table("Stories")
            .update(update_data)
            .eq("id", story_id)
            .eq("user_id", user.id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update story")

        logger.info(
            f"Successfully updated story {story_id} visibility to {'public' if is_public else 'private'}"
        )
        return {
            "success": True,
            "story": result.data[0],
            "message": f"Story is now {'public' if is_public else 'private'}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update story visibility: {e}")
        raise HTTPException(status_code=500, detail="Failed to update story visibility")


class CommentStoryRequest(BaseModel):
    comment: str = Field(..., min_length=1, max_length=500, description="Comment text")


@router.post("/story/{story_id}/like")
async def toggle_story_like(story_id: int, request: Request):
    """Toggle like on a story - simplified auth for Supabase tokens"""
    supabase = deps_get_supabase_client()
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.replace("Bearer ", "").strip()
        if len(token) < 50:
            raise HTTPException(status_code=401, detail="Invalid token format")

        try:
            user_response = supabase.auth.get_user(token)
            user = user_response.user
            if not user:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        logger.info(f"User {user.id} toggling like on story {story_id}")

        story_response = supabase.table("Stories").select("id, is_public").eq("id", story_id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found")
        story = story_response.data[0]
        if not story.get("is_public"):
            raise HTTPException(status_code=403, detail="Cannot like private stories")

        like_response = (
            supabase.table("StoryLikes").select("id").eq("story_id", story_id).eq("user_id", user.id).execute()
        )
        if like_response.data:
            supabase.table("StoryLikes").delete().eq("id", like_response.data[0]["id"]).execute()
            liked = False
        else:
            insert_data = {
                "story_id": story_id,
                "user_id": user.id,
                "created_at": datetime.utcnow().isoformat(),
            }
            supabase.table("StoryLikes").insert(insert_data).execute()
            liked = True

        count_response = supabase.table("StoryLikes").select("id", count="exact").eq("story_id", story_id).execute()
        like_count = count_response.count or 0

        return {"success": True, "liked": liked, "like_count": like_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle story like: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle story like")


@router.post("/story/{story_id}/comment")
async def add_story_comment(story_id: int, comment_data: CommentStoryRequest, request: Request):
    """Add a comment to a story - simplified auth for Supabase tokens"""
    supabase = deps_get_supabase_client()
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.replace("Bearer ", "").strip()
        if len(token) < 50:
            raise HTTPException(status_code=401, detail="Invalid token format")

        try:
            user_response = supabase.auth.get_user(token)
            user = user_response.user
            if not user:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")

        logger.info(f"User {user.id} adding comment to story {story_id}")

        story_response = supabase.table("Stories").select("id, is_public").eq("id", story_id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found")
        story = story_response.data[0]
        if not story.get("is_public"):
            raise HTTPException(status_code=403, detail="Cannot comment on private stories")

        comment_response = supabase.table("StoryComments").insert(
            {
                "story_id": story_id,
                "user_id": user.id,
                "comment": comment_data.comment,
                "created_at": datetime.utcnow().isoformat(),
            }
        ).execute()

        if not comment_response.data:
            raise HTTPException(status_code=500, detail="Failed to add comment")
        comment = comment_response.data[0]

        count_response = (
            supabase.table("StoryComments").select("id", count="exact").eq("story_id", story_id).execute()
        )
        comment_count = count_response.count or 0

        return {"success": True, "comment": comment, "comment_count": comment_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add story comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to add story comment")


@router.get("/story/{story_id}/likes")
async def get_story_likes(story_id: int, user = Depends(get_authenticated_user_optional)):
    """Get like count and user's like status for a story"""
    supabase = deps_get_supabase_client()
    try:
        count_response = supabase.table("StoryLikes").select("id", count="exact").eq("story_id", story_id).execute()
        like_count = count_response.count or 0

        user_liked = False
        if user:
            like_response = (
                supabase.table("StoryLikes").select("id").eq("story_id", story_id).eq("user_id", user.id).execute()
            )
            user_liked = len(like_response.data) > 0

        return {"like_count": like_count, "user_liked": user_liked}
    except Exception as e:
        logger.error(f"Failed to get story likes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get story likes")


@router.get("/story/{story_id}/comments")
async def get_story_comments(story_id: int, page: int = 1, limit: int = 20):
    """Get comments for a story"""
    supabase = deps_get_supabase_client()
    try:
        story_response = supabase.table("Stories").select("id, is_public").eq("id", story_id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found")
        story = story_response.data[0]
        if not story.get("is_public"):
            raise HTTPException(status_code=403, detail="Cannot view comments for private stories")

        comments_response = (
            supabase.table("StoryComments")
            .select("*")
            .eq("story_id", story_id)
            .order("created_at", desc=True)
            .range((page - 1) * limit, page * limit - 1)
            .execute()
        )

        count_response = supabase.table("StoryComments").select("id", count="exact").eq("story_id", story_id).execute()
        total_count = count_response.count or 0

        return {
            "comments": comments_response.data,
            "page": page,
            "limit": limit,
            "total": total_count,
            "total_pages": (total_count + limit - 1) // limit,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get story comments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get story comments")


@router.get("/stories/public")
async def get_public_stories(
    page: int = 1,
    limit: int = 20,
    genre: Optional[str] = None,
    sort_by: str = "published_at",
    user = Depends(get_authenticated_user_optional),
):
    """Get public stories for discovery"""
    supabase = deps_get_supabase_client()
    try:
        logger.info(f"Fetching public stories - page: {page}, limit: {limit}, genre: {genre}")

        query = supabase.table("Stories").select("*").eq("is_public", True)
        if genre:
            query = query.eq("genre", genre)

        valid_sort_fields = ["published_at", "created_at", "story_title", "total_chapters"]
        if sort_by not in valid_sort_fields:
            sort_by = "published_at"

        result = query.order(sort_by, desc=True).range((page - 1) * limit, page * limit - 1).execute()

        count_query = supabase.table("Stories").select("id", count="exact").eq("is_public", True)
        if genre:
            count_query = count_query.eq("genre", genre)
        count_result = count_query.execute()
        total_count = count_result.count or 0

        enhanced_stories = []
        for story in result.data:
            story_id_val = story["id"]
            like_count_response = (
                supabase.table("StoryLikes").select("id", count="exact").eq("story_id", story_id_val).execute()
            )
            like_count = like_count_response.count or 0

            comment_count_response = (
                supabase.table("StoryComments").select("id", count="exact").eq("story_id", story_id_val).execute()
            )
            comment_count = comment_count_response.count or 0

            user_liked = False
            if user:
                user_like_response = (
                    supabase.table("StoryLikes").select("id").eq("story_id", story_id_val).eq("user_id", user.id).execute()
                )
                user_liked = len(user_like_response.data) > 0

            enhanced_story = {
                **story,
                "like_count": like_count,
                "comment_count": comment_count,
                "user_liked": user_liked,
            }
            enhanced_stories.append(enhanced_story)

        return {
            "stories": enhanced_stories,
            "page": page,
            "limit": limit,
            "total": total_count,
            "total_pages": (total_count + limit - 1) // limit,
        }
    except Exception as e:
        logger.error(f"Failed to fetch public stories: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch public stories")


