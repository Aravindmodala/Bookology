from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.logger_config import setup_logger
from app.dependencies.supabase import get_supabase_client, get_authenticated_user


logger = setup_logger(__name__)
router = APIRouter()


class UpdateChapterContentInput(BaseModel):
    """Input model for updating only chapter content (no summary regeneration)."""
    story_id: int = Field(..., gt=0, description="ID of the story")
    chapter_id: int = Field(..., gt=0, description="ID of the chapter to update")
    content: str = Field(..., min_length=1, description="New chapter content")
    word_count: Optional[int] = None


@router.post("/update_chapter_content")
async def update_chapter_content_endpoint(
    update_data: UpdateChapterContentInput, user = Depends(get_authenticated_user)
):
    supabase = get_supabase_client()
    """
    Simple endpoint to update only chapter content without regenerating summaries or choices.
    Used for text rewrites and real-time auto-save functionality.
    
    Performance Benefits:
    - No summary regeneration
    - No choice regeneration  
    - No version creation
    - Simple database update only
    - Sub-second response time
    """
    try:
        logger.info(
            "🚀 REAL-TIME SAVE: Updating Chapter {} content, Story {}".format(
                update_data.chapter_id, update_data.story_id
            )
        )

        # STEP 1: Verify story ownership
        story_response = (
            supabase.table("Stories")
            .select("id")
            .eq("id", update_data.story_id)
            .eq("user_id", user.id)
            .execute()
        )

        if not story_response.data:
            logger.error(
                "❌ AUTHORIZATION: Story {} not found for user {}".format(
                    update_data.story_id, user.id
                )
            )
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        # STEP 2: Verify chapter exists and belongs to the story
        chapter_response = (
            supabase.table("Chapters")
            .select("id, story_id, chapter_number")
            .eq("id", update_data.chapter_id)
            .eq("story_id", update_data.story_id)
            .eq("is_active", True)
            .execute()
        )

        if not chapter_response.data:
            logger.error(
                "❌ Chapter {} not found for story {}".format(
                    update_data.chapter_id, update_data.story_id
                )
            )
            raise HTTPException(status_code=404, detail="Chapter not found")

        chapter = chapter_response.data[0]
        logger.info(
            "✅ Chapter {} verified for story {}".format(
                chapter["chapter_number"], update_data.story_id
            )
        )

        # STEP 3: Calculate word count if not provided
        word_count = (
            update_data.word_count
            if update_data.word_count is not None
            else len(update_data.content.split())
        )

        # STEP 4: Update only the content and word count (overwrite previous content)
        update_result = (
            supabase.table("Chapters")
            .update(
                {
                    "content": update_data.content,
                    "word_count": word_count,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
            .eq("id", update_data.chapter_id)
            .execute()
        )

        if not update_result.data:
            logger.error("❌ Failed to update chapter content")
            raise HTTPException(status_code=500, detail="Failed to update chapter content")

        logger.info(
            "✅ REAL-TIME SAVE COMPLETE: Chapter {} updated successfully".format(
                update_data.chapter_id
            )
        )

        return {
            "success": True,
            "message": "Chapter content updated successfully",
            "chapter_id": update_data.chapter_id,
            "story_id": update_data.story_id,
            "chapter_number": chapter["chapter_number"],
            "word_count": word_count,
            "content_length": len(update_data.content),
            "updated_at": update_result.data[0]["updated_at"],
            "performance": {
                "save_type": "real_time",
                "summary_regenerated": False,
                "choices_regenerated": False,
                "version_created": False,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ FATAL ERROR in real-time content update: {}".format(str(e)))
        import traceback
        logger.error("❌ Traceback: {}".format(traceback.format_exc()))
        raise HTTPException(
            status_code=500,
            detail="Failed to update chapter content: {}".format(str(e)),
        )





