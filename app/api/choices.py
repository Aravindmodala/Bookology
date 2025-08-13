from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.core.logger_config import setup_logger
from app.dependencies.supabase import (
    get_authenticated_user,
    get_authenticated_user_optional,
    get_supabase_client as deps_get_supabase_client,
)


router = APIRouter()
logger = setup_logger(__name__)


@router.get("/story/{story_id}/choice_history")
async def get_choice_history_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user),
):
    """Get the complete choice history for a story showing all paths taken and not taken."""
    try:
        supabase = deps_get_supabase_client()
        logger.info("Getting choice history for story {}".format(story_id))

        # Get all choices for this story
        choices_response = (
            supabase.table("story_choices")
            .select("*")
            .eq("story_id", story_id)
            .eq("user_id", user.id)
            .order("chapter_number")
            .order("choice_id")
            .execute()
        )

        if not choices_response.data:
            return {
                "success": True,
                "story_id": story_id,
                "choice_history": [],
                "message": "No choices found for this story",
            }

        # Organize choices by chapter
        choice_history: Dict[int, Dict[str, Any]] = {}
        for choice in choices_response.data:
            chapter_num = choice["chapter_number"]
            if chapter_num not in choice_history:
                choice_history[chapter_num] = {
                    "chapter_number": chapter_num,
                    "choices": [],
                    "selected_choice": None,
                }

            choice_info = {
                "id": choice["id"],
                "choice_id": choice["choice_id"],
                "title": choice.get("title", "Untitled Choice"),
                "description": choice.get("description", ""),
                "story_impact": choice.get("story_impact", ""),
                "choice_type": choice.get("choice_type", "unknown"),
                "is_selected": choice.get("is_selected", False),
                "selected_at": choice.get("selected_at"),
            }

            choice_history[chapter_num]["choices"].append(choice_info)

            if choice.get("is_selected"):
                choice_history[chapter_num]["selected_choice"] = choice_info

        # Convert to list and sort by chapter number
        choice_history_list = list(choice_history.values())
        choice_history_list.sort(key=lambda x: x["chapter_number"])

        return {
            "success": True,
            "story_id": story_id,
            "choice_history": choice_history_list,
            "total_chapters_with_choices": len(choice_history_list),
        }
    except Exception as e:
        logger.error("Error fetching choice history for story {}: {}".format(story_id, str(e)))
        raise HTTPException(status_code=500, detail="Failed to fetch choice history: {}".format(str(e)))


@router.get("/chapter/{chapter_id}/choices")
async def get_choices_for_chapter_endpoint(
    chapter_id: int,
    user = Depends(get_authenticated_user_optional),
):
    """
    Get all choices for a specific chapter version (by chapter_id), always returning all options.
    """
    try:
        supabase = deps_get_supabase_client()
        # Fetch all choices for this chapter_id
        choices_response = (
            supabase.table("story_choices").select("*").eq("chapter_id", chapter_id).execute()
        )
        choices = choices_response.data or []
        return {"success": True, "chapter_id": chapter_id, "choices": choices, "total_choices": len(choices)}
    except Exception as e:
        logger.error("Error fetching choices for chapter {}: {}".format(chapter_id, e))
        return {"success": False, "detail": str(e)}





