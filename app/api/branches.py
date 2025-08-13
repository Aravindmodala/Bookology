from typing import Any, Dict, List, Optional, Union
import time
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.logger_config import setup_logger
from app.dependencies.supabase import (
    get_authenticated_user,
    get_authenticated_user_optional,
    get_supabase_client as deps_get_supabase_client,
)


router = APIRouter()
logger = setup_logger(__name__)


@router.get("/story/{story_id}/tree")
async def get_story_tree_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user),
):
    """Get story structure as tree with choice paths for visualization - OPTIMIZED"""
    try:
        supabase = deps_get_supabase_client()
        start_time = time.time()
        logger.info("🌳 Getting optimized story tree for story {}".format(story_id))

        # OPTIMIZATION 1: Single query for all active chapters
        chapters_response = (
            supabase.table("Chapters")
            .select("*")
            .eq("story_id", story_id)
            .eq("is_active", True)
            .order("chapter_number")
            .execute()
        )
        chapters = chapters_response.data

        if not chapters:
            return {
                "success": True,
                "story_id": story_id,
                "tree": [],
                "message": "No chapters found for this story",
                "performance": {"query_time": round(time.time() - start_time, 3)},
            }

        # OPTIMIZATION 2: Single query for ALL choices for this story
        all_choices_response = (
            supabase.table("story_choices")
            .select("*")
            .eq("story_id", story_id)
            .eq("user_id", user.id)
            .execute()
        )
        all_choices = all_choices_response.data or []

        # OPTIMIZATION 3: Group choices by chapter_number for O(1) lookup
        choices_by_chapter: Dict[int, List[Dict[str, Any]]] = {}
        for choice in all_choices:
            chapter_num = choice.get("chapter_number")
            if chapter_num not in choices_by_chapter:
                choices_by_chapter[chapter_num] = []
            choices_by_chapter[chapter_num].append(choice)

        # OPTIMIZATION 4: Build tree structure with efficient lookups
        tree_data = []
        chapter_numbers = [ch["chapter_number"] for ch in chapters]
        max_chapter = max(chapter_numbers) if chapter_numbers else 0

        for chapter in chapters:
            chapter_num = chapter["chapter_number"]
            choices = choices_by_chapter.get(chapter_num, [])

            # Determine selected choice and next chapter existence
            selected_choice_id = None
            selected_choices = [c for c in choices if c.get("is_selected", False)]

            if selected_choices:
                selected_choice_id = selected_choices[0]["id"]
                for choice in choices:
                    choice["selected"] = choice["id"] == selected_choice_id
            elif choices and chapter_num < max_chapter:
                # Fallback: mark first choice as selected if next chapter exists
                choices[0]["selected"] = True
                selected_choice_id = choices[0]["id"]
                for i, choice in enumerate(choices):
                    choice["selected"] = i == 0
            else:
                # No choices or last chapter
                for choice in choices:
                    choice["selected"] = False

            # Calculate word count efficiently
            content = chapter.get("content", "")
            word_count = len(content.split()) if content else 0

            tree_data.append(
                {
                    "chapter": {
                        "id": chapter["id"],
                        "chapter_number": chapter_num,
                        "title": chapter.get("title", f"Chapter {chapter_num}"),
                        "content": content,
                        "created_at": chapter.get("created_at"),
                        "word_count": word_count,
                    },
                    "choices": choices,
                    "selected_choice_id": selected_choice_id,
                    "has_next_chapter": chapter_num < max_chapter,
                    "is_current_chapter": chapter_num == max_chapter,
                    "choice_stats": {
                        "total": len(choices),
                        "selected": len([c for c in choices if c.get("selected", False)]),
                        "unselected": len([c for c in choices if not c.get("selected", False)]),
                    },
                }
            )

        total_choices = sum(len(node["choices"]) for node in tree_data)
        query_time = round(time.time() - start_time, 3)

        logger.info(
            "✅ Optimized story tree built: {} chapters, {} choices in {}s".format(
                len(tree_data), total_choices, query_time
            )
        )

        return {
            "success": True,
            "story_id": story_id,
            "tree": tree_data,
            "total_chapters": len(tree_data),
            "total_choices": total_choices,
            "performance": {
                "query_time": query_time,
                "chapters_fetched": len(chapters),
                "choices_fetched": len(all_choices),
                "optimization": "single_query_approach",
            },
        }
    except Exception as e:
        logger.error(
            "❌ Error fetching optimized story tree for story {}: {}".format(
                story_id, str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to fetch story tree: {}".format(str(e))
        )


class BranchFromChoiceInput(BaseModel):
    story_id: int = Field(..., gt=0, description="ID of the story")
    chapter_number: int = Field(..., ge=1, description="Chapter number where the choice was made")
    choice_id: Union[str, int] = Field(..., description="ID of the choice to branch from")
    choice_data: Dict[str, Any] = Field(..., description="The full choice object that was selected")


class BranchPreviewInput(BaseModel):
    """Input model for generating a preview of branching without saving to database."""
    story_id: int = Field(..., gt=0, description="ID of the story")
    chapter_number: int = Field(..., ge=1, description="Chapter number where the choice was made")
    choice_id: Union[str, int] = Field(..., description="ID of the choice to branch from")
    choice_data: Dict[str, Any] = Field(..., description="The full choice object that was selected")


@router.post("/branch_from_choice")
async def branch_from_choice_endpoint(
    request: BranchFromChoiceInput, user = Depends(get_authenticated_user)
):
    """
    Generate a new branch in the story by selecting a different choice from a previous chapter.
    This will generate new chapters from that point onward while preserving the original path.
    """
    try:
        supabase = deps_get_supabase_client()
        logger.info(
            "BRANCH: User wants to branch from chapter {}, choice {}".format(
                request.chapter_number, request.choice_id
            )
        )
        logger.info("BRANCH: story_id={}".format(request.story_id))

        # Verify story belongs to user
        story_response = (
            supabase.table("Stories")
            .select("*")
            .eq("id", request.story_id)
            .eq("user_id", user.id)
            .execute()
        )
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        story = story_response.data[0]
        logger.info("✅ BRANCH: Story verified: {}".format(story.get("story_title", "Untitled")))

        # Get the main branch ID for this story
        try:
            from app.services.branching import get_main_branch_id as _get_main_branch_id
            main_branch_id = await _get_main_branch_id(request.story_id)
        except Exception:
            main_branch_id = None

        # Get all choices for the specified chapter to validate the choice exists
        choices_response = (
            supabase.table("story_choices")
            .select("*")
            .eq("story_id", request.story_id)
            .eq("branch_id", main_branch_id)
            .eq("user_id", user.id)
            .eq("chapter_number", request.chapter_number)
            .execute()
        )

        available_choices = choices_response.data
        if not available_choices:
            raise HTTPException(
                status_code=404, detail="No choices found for chapter {}".format(request.chapter_number)
            )

        # NORMALISE the incoming choice-id for consistent matching
        raw_choice_id = str(request.choice_id)
        possible_ids = {raw_choice_id}
        if raw_choice_id.startswith("choice_"):
            possible_ids.add(raw_choice_id.split("choice_", 1)[1])
        if raw_choice_id.isdigit():
            possible_ids.add(f"choice_{raw_choice_id}")

        # Find the selected choice
        selected_choice = None
        for choice in available_choices:
            if str(choice.get("id")) in possible_ids or str(choice.get("choice_id")) in possible_ids:
                selected_choice = choice
                break

        if not selected_choice:
            raise HTTPException(status_code=400, detail="Invalid choice selected for branching")

        logger.info("BRANCH: Selected choice found: {}".format(selected_choice.get("title", "No title")))

        # Create new branch
        from app.services.branching import create_new_branch as _create_new_branch
        new_branch_id = await _create_new_branch(
            story_id=request.story_id,
            parent_branch_id=main_branch_id,
            branched_from_chapter=request.chapter_number,
            branch_name="branch_from_ch{}_{}".format(
                request.chapter_number, selected_choice.get("title", "choice")[:20]
            ),
        )

        logger.info("✅ CREATE-BRANCH: New branch created: {}".format(new_branch_id))

        # Copy chapters and choices up to the branch point
        from app.services.branching import copy_chapters_to_branch as _copy_chapters_to_branch
        await _copy_chapters_to_branch(
            story_id=request.story_id,
            from_branch_id=main_branch_id,
            to_branch_id=new_branch_id,
            up_to_chapter=request.chapter_number,
        )

        # Mark the selected choice as selected in the new branch
        from datetime import datetime
        supabase.table("story_choices").update({
            "is_selected": True,
            "selected_at": datetime.utcnow().isoformat(),
        }).eq("story_id", request.story_id).eq("branch_id", new_branch_id).eq("chapter_number", request.chapter_number).eq("id", selected_choice["id"]).execute()

        # Generate the next chapter for the new branch
        next_chapter_number = request.chapter_number + 1
        logger.info(
            "CREATE-BRANCH: Generating chapter {} for new branch".format(
                next_chapter_number
            )
        )

        # Get chapters from the new branch for context
        chapters_response = (
            supabase.table("Chapters")
            .select("*")
            .eq("story_id", request.story_id)
            .eq("branch_id", new_branch_id)
            .lte("chapter_number", request.chapter_number)
            .order("chapter_number")
            .execute()
        )

        previous_chapters = chapters_response.data

        # Generate the next chapter
        from app.services.story_service_with_dna import StoryService
        story_service = StoryService()
        next_chapter_result = await story_service.generate_next_chapter_with_dna(
            story=story,
            previous_Chapters=previous_chapters,
            selected_choice=selected_choice,
            next_chapter_number=next_chapter_number,
            user_id=user.id,
        )

        # Save the new chapter to the new branch
        chapter_content = next_chapter_result.get("chapter_content") or next_chapter_result.get(
            "content", ""
        )

        # Get the next version number for this chapter in the new branch
        from app.services.chapter_versioning import get_next_chapter_version_number, save_choices_for_chapter
        next_version_number = await get_next_chapter_version_number(
            request.story_id, next_chapter_number, new_branch_id
        )

        chapter_insert_data = {
            "story_id": request.story_id,
            "branch_id": new_branch_id,
            "chapter_number": next_chapter_number,
            "title": next_chapter_result.get("title", "Chapter {}".format(next_chapter_number)),
            "content": chapter_content,
            "word_count": len(chapter_content.split()),
            "version_number": next_version_number,  # Add proper versioning
            "is_active": True,  # Mark this version as active
        }

        chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
        chapter_id = chapter_response.data[0]["id"]

        # Save choices for the new chapter in the new branch
        choices = next_chapter_result.get("choices", [])
        if choices:
            await save_choices_for_chapter(
                story_id=request.story_id,
                chapter_id=chapter_id,
                chapter_number=next_chapter_number,
                choices=choices,
                user_id=user.id,
                supabase=supabase,
            )

        return {
            "success": True,
            "message": "New branch created successfully from chapter {}".format(
                request.chapter_number
            ),
            "branch_id": new_branch_id,
            "chapter_content": chapter_content,
            "chapter_number": next_chapter_number,
            "story_id": request.story_id,
            "selected_choice": selected_choice,
            "choices": choices,
            "branch_info": {
                "parent_branch_id": main_branch_id,
                "branched_from_chapter": request.chapter_number,
                "new_chapter_number": next_chapter_number,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("CREATE-BRANCH: Unexpected error: {}".format(str(e)))
        import traceback
        logger.error("CREATE-BRANCH: Full traceback: {}".format(traceback.format_exc()))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/branch_preview")
async def branch_preview_endpoint(
    request: BranchPreviewInput, user = Depends(get_authenticated_user)
):
    """
    Generate a preview of the next chapter based on a different choice from a previous chapter.
    This endpoint does NOT save anything to the database - it only returns what the chapter would look like.
    """
    try:
        supabase = deps_get_supabase_client()
        logger.info(
            "BRANCH-PREVIEW: User {} requesting preview for story {}, chapter {}, choice {}".format(
                user.id, request.story_id, request.chapter_number, request.choice_id
            )
        )

        # Verify story belongs to user
        story_response = (
            supabase.table("Stories").select("*").eq("id", request.story_id).eq("user_id", user.id).execute()
        )
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        story = story_response.data[0]
        logger.info("✅ BRANCH-PREVIEW: Story verified: {}".format(story.get("story_title", "Untitled")))

        # Get the main branch ID for this story
        try:
            from app.services.branching import get_main_branch_id as _get_main_branch_id
            main_branch_id = await _get_main_branch_id(request.story_id)
        except Exception:
            main_branch_id = None

        # Get all choices for the specified chapter to validate the choice exists
        logger.info(
            "BRANCH-PREVIEW: Looking for choices with story_id={}, branch_id={}, user_id={}, chapter_number={}".format(
                request.story_id, main_branch_id, user.id, request.chapter_number
            )
        )
        choices_response = (
            supabase.table("story_choices")
            .select("*")
            .eq("story_id", request.story_id)
            .eq("branch_id", main_branch_id)
            .eq("user_id", user.id)
            .eq("chapter_number", request.chapter_number)
            .execute()
        )

        available_choices = choices_response.data
        logger.info(
            "BRANCH-PREVIEW: Found {} choices for chapter {}".format(
                len(available_choices), request.chapter_number
            )
        )

        if not available_choices:
            # Let's try without branch_id to see if choices exist but with wrong branch
            logger.info(
                "BRANCH-PREVIEW: No choices found with branch_id, trying without branch_id..."
            )
            fallback_choices_response = (
                supabase.table("story_choices")
                .select("*")
                .eq("story_id", request.story_id)
                .eq("user_id", user.id)
                .eq("chapter_number", request.chapter_number)
                .execute()
            )
            fallback_choices = fallback_choices_response.data
            logger.info(
                "BRANCH-PREVIEW: Found {} choices without branch_id filter".format(
                    len(fallback_choices)
                )
            )

            if fallback_choices:
                logger.info(
                    "BRANCH-PREVIEW: Updating {} choices to use main branch {}".format(
                        len(fallback_choices), main_branch_id
                    )
                )
                # Update the choices to use the correct branch_id
                for choice in fallback_choices:
                    supabase.table("story_choices").update({"branch_id": main_branch_id}).eq("id", choice["id"]).execute()

                # Now try again with the updated choices
                choices_response = (
                    supabase.table("story_choices")
                    .select("*")
                    .eq("story_id", request.story_id)
                    .eq("branch_id", main_branch_id)
                    .eq("user_id", user.id)
                    .eq("chapter_number", request.chapter_number)
                    .execute()
                )
                available_choices = choices_response.data
                logger.info(
                    "BRANCH-PREVIEW: After update, found {} choices".format(
                        len(available_choices)
                    )
                )

            if not available_choices:
                raise HTTPException(
                    status_code=404, detail="No choices found for chapter {}".format(request.chapter_number)
                )

        # NORMALISE the incoming choice-id for consistent matching
        raw_choice_id = str(request.choice_id)
        possible_ids = {raw_choice_id}
        if raw_choice_id.startswith("choice_"):
            possible_ids.add(raw_choice_id.split("choice_", 1)[1])
        if raw_choice_id.isdigit():
            possible_ids.add(f"choice_{raw_choice_id}")

        # Find the selected choice
        selected_choice = None
        for choice in available_choices:
            if str(choice.get("id")) in possible_ids or str(choice.get("choice_id")) in possible_ids:
                selected_choice = choice
                break

        if not selected_choice:
            raise HTTPException(status_code=400, detail="Invalid choice selected for preview")

        logger.info(
            "BRANCH-PREVIEW: Selected choice found: {}".format(
                selected_choice.get("title", "No title")
            )
        )

        # Get all chapters up to (but not including) the next chapter for context
        chapters_response = (
            supabase.table("Chapters")
            .select("*")
            .eq("story_id", request.story_id)
            .eq("branch_id", main_branch_id)
            .lte("chapter_number", request.chapter_number)
            .order("chapter_number")
            .execute()
        )

        previous_chapters = chapters_response.data
        logger.info(
            "BRANCH-PREVIEW: Using {} previous chapters for context".format(
                len(previous_chapters)
            )
        )

        # Generate the next chapter based on the choice (WITHOUT saving to database)
        next_chapter_number = request.chapter_number + 1
        logger.info(
            "BRANCH-PREVIEW: Generating preview for chapter {} based on choice".format(
                next_chapter_number
            )
        )

        # Use the story service to generate the next chapter
        try:
            logger.info("BRANCH-PREVIEW: Calling story_service.generate_next_chapter...")
            logger.info("BRANCH-PREVIEW: story_title='{}'".format(story.get("story_title", "Unknown")))
            logger.info(
                "BRANCH-PREVIEW: previous_chapters_count={}".format(
                    len(previous_chapters)
                )
            )
            logger.info(
                "BRANCH-PREVIEW: selected_choice_title='{}'".format(
                    selected_choice.get("title", "Unknown")
                )
            )
            logger.info(
                "BRANCH-PREVIEW: next_chapter_number={}".format(next_chapter_number)
            )

            from app.services.story_service_with_dna import StoryService
            story_service = StoryService()
            next_chapter_result = await story_service.generate_next_chapter_with_dna(
                story=story,
                previous_Chapters=previous_chapters,
                selected_choice=selected_choice,
                next_chapter_number=next_chapter_number,
                user_id=user.id,
            )
            logger.info(
                "BRANCH-PREVIEW: Chapter {} preview generated successfully".format(
                    next_chapter_number
                )
            )
            logger.info(
                "BRANCH-PREVIEW: Result keys: {}".format(
                    list(next_chapter_result.keys()) if next_chapter_result else "None"
                )
            )

            chapter_content = next_chapter_result.get("chapter_content") or next_chapter_result.get(
                "content", ""
            )

        except Exception as generation_error:
            logger.error(
                "BRANCH-PREVIEW: Chapter generation failed: {}".format(
                    str(generation_error)
                )
            )
            import traceback
            logger.error(
                "BRANCH-PREVIEW: Full traceback: {}".format(traceback.format_exc())
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to generate preview chapter: {}".format(
                    str(generation_error)
                ),
            )

        # Generate summary for the preview chapter
        logger.info(
            "BRANCH-PREVIEW: Generating summary for preview chapter {}...".format(
                next_chapter_number
            )
        )

        try:
            from app.services.chapter_summary import generate_chapter_summary

            # Get previous chapter summaries for context
            previous_summaries: List[str] = []
            if previous_chapters:
                for prev_chapter in previous_chapters:
                    if prev_chapter.get("summary"):
                        previous_summaries.append(prev_chapter["summary"])
                    else:
                        # If no summary exists, create a quick one from content
                        prev_content = prev_chapter.get("content", "")[:500] + "..."
                        previous_summaries.append("Previous chapter: {}".format(prev_content))

            # Build story context for summary
            story_context = "STORY: {}\nOUTLINE: {}".format(
                story.get("story_title", "Untitled Story"), story.get("story_outline", "")
            )
            if previous_summaries:
                story_context += "\n\nPREVIOUS CHAPTERS:\n" + "\n".join(previous_summaries)

            # Generate summary
            summary_result = generate_chapter_summary(
                chapter_content=chapter_content,
                chapter_number=next_chapter_number,
                story_context=story_context,
                story_title=story.get("story_title", "Untitled Story"),
            )

            chapter_summary = ""
            if summary_result["success"]:
                chapter_summary = summary_result["summary"]
                logger.info(
                    "BRANCH-PREVIEW: Summary generated successfully ({}) chars".format(
                        len(chapter_summary)
                    )
                )
            else:
                logger.warning(
                    "BRANCH-PREVIEW: Summary generation failed: {}".format(
                        summary_result["error"]
                    )
                )
                chapter_summary = "Summary generation failed: {}".format(
                    summary_result["error"]
                )

        except Exception as summary_error:
            logger.error(
                "BRANCH-PREVIEW: Summary generation error: {}".format(
                    str(summary_error)
                )
            )
            chapter_summary = "Summary generation error: {}".format(str(summary_error))

        # Return the preview with summary (without saving anything to database)
        response_payload = {
            "success": True,
            "preview": True,
            "chapter_number": next_chapter_number,
            "chapter_content": chapter_content,
            "chapter_summary": chapter_summary,  # Include the generated summary
            "choices": next_chapter_result.get("choices", []),
            "selected_choice": selected_choice,
            "message": "Preview generated for chapter {} based on choice: {}".format(
                next_chapter_number, selected_choice.get("title", "Unknown")
            ),
        }

        logger.info(
            "BRANCH-PREVIEW: Successfully generated preview for chapter {}".format(
                next_chapter_number
            )
        )
        return response_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error("BRANCH-PREVIEW: Unexpected error: {}".format(str(e)))
        import traceback
        logger.error("BRANCH-PREVIEW: Full traceback: {}".format(traceback.format_exc()))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_branch")
async def create_branch_endpoint(
    request: BranchFromChoiceInput, user = Depends(get_authenticated_user)
):
    """
    Create a new branch from a choice without overwriting the main branch.
    This preserves all existing branches and creates a new parallel storyline.
    """
    try:
        supabase = deps_get_supabase_client()
        logger.info(
            "CREATE-BRANCH: Creating new branch from chapter {}, choice {}".format(
                request.chapter_number, request.choice_id
            )
        )

        # Verify story belongs to user
        story_response = (
            supabase.table("Stories")
            .select("*")
            .eq("id", request.story_id)
            .eq("user_id", user.id)
            .execute()
        )
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        story = story_response.data[0]
        logger.info("✅ CREATE-BRANCH: Story verified: {}".format(story.get("story_title", "Untitled")))

        # Get the main branch ID
        try:
            from app.services.branching import get_main_branch_id as _get_main_branch_id
            main_branch_id = await _get_main_branch_id(request.story_id)
        except Exception:
            main_branch_id = None

        # Validate the choice exists
        choices_response = (
            supabase.table("story_choices")
            .select("*")
            .eq("story_id", request.story_id)
            .eq("branch_id", main_branch_id)
            .eq("user_id", user.id)
            .eq("chapter_number", request.chapter_number)
            .execute()
        )

        available_choices = choices_response.data
        if not available_choices:
            raise HTTPException(
                status_code=404, detail="No choices found for chapter {}".format(request.chapter_number)
            )

        # NORMALISE the incoming choice-id for consistent matching
        raw_choice_id = str(request.choice_id)
        possible_ids = {raw_choice_id}
        if raw_choice_id.startswith("choice_"):
            possible_ids.add(raw_choice_id.split("choice_", 1)[1])
        if raw_choice_id.isdigit():
            possible_ids.add(f"choice_{raw_choice_id}")

        # Find the selected choice
        selected_choice = None
        for choice in available_choices:
            if str(choice.get("id")) in possible_ids or str(choice.get("choice_id")) in possible_ids:
                selected_choice = choice
                break

        if not selected_choice:
            raise HTTPException(status_code=400, detail="Invalid choice selected for branching")

        logger.info(
            "CREATE-BRANCH: Selected choice found: {}".format(
                selected_choice.get("title", "No title")
            )
        )

        # Create new branch
        from app.services.branching import create_new_branch as _create_new_branch
        new_branch_id = await _create_new_branch(
            story_id=request.story_id,
            parent_branch_id=main_branch_id,
            branched_from_chapter=request.chapter_number,
            branch_name="branch_from_ch{}_{}".format(
                request.chapter_number, selected_choice.get("title", "choice")[:20]
            ),
        )

        logger.info("✅ CREATE-BRANCH: New branch created: {}".format(new_branch_id))

        # Copy chapters and choices up to the branch point
        from app.services.branching import copy_chapters_to_branch as _copy_chapters_to_branch
        await _copy_chapters_to_branch(
            story_id=request.story_id,
            from_branch_id=main_branch_id,
            to_branch_id=new_branch_id,
            up_to_chapter=request.chapter_number,
        )

        # Mark the selected choice as selected in the new branch
        from datetime import datetime
        supabase.table("story_choices").update({
            "is_selected": True,
            "selected_at": datetime.utcnow().isoformat(),
        }).eq("story_id", request.story_id).eq("branch_id", new_branch_id).eq("chapter_number", request.chapter_number).eq("id", selected_choice["id"]).execute()

        # Generate the next chapter for the new branch
        next_chapter_number = request.chapter_number + 1
        logger.info(
            "CREATE-BRANCH: Generating chapter {} for new branch".format(
                next_chapter_number
            )
        )

        # Get chapters from the new branch for context
        chapters_response = (
            supabase.table("Chapters")
            .select("*")
            .eq("story_id", request.story_id)
            .eq("branch_id", new_branch_id)
            .lte("chapter_number", request.chapter_number)
            .order("chapter_number")
            .execute()
        )

        previous_chapters = chapters_response.data

        # Generate the next chapter
        from app.services.story_service_with_dna import StoryService
        story_service = StoryService()
        next_chapter_result = await story_service.generate_next_chapter_with_dna(
            story=story,
            previous_Chapters=previous_chapters,
            selected_choice=selected_choice,
            next_chapter_number=next_chapter_number,
            user_id=user.id,
        )

        # Save the new chapter to the new branch
        chapter_content = next_chapter_result.get("chapter_content") or next_chapter_result.get(
            "content", ""
        )

        # Get the next version number for this chapter in the new branch
        from app.services.chapter_versioning import get_next_chapter_version_number, save_choices_for_chapter
        next_version_number = await get_next_chapter_version_number(
            request.story_id, next_chapter_number, new_branch_id
        )

        chapter_insert_data = {
            "story_id": request.story_id,
            "branch_id": new_branch_id,
            "chapter_number": next_chapter_number,
            "title": next_chapter_result.get("title", "Chapter {}".format(next_chapter_number)),
            "content": chapter_content,
            "word_count": len(chapter_content.split()),
            "version_number": next_version_number,  # Add proper versioning
            "is_active": True,  # Mark this version as active
        }

        chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
        chapter_id = chapter_response.data[0]["id"]

        # Save choices for the new chapter in the new branch
        choices = next_chapter_result.get("choices", [])
        if choices:
            await save_choices_for_chapter(
                story_id=request.story_id,
                chapter_id=chapter_id,
                chapter_number=next_chapter_number,
                choices=choices,
                user_id=user.id,
                supabase=supabase,
            )

        return {
            "success": True,
            "message": "New branch created successfully from chapter {}".format(
                request.chapter_number
            ),
            "branch_id": new_branch_id,
            "chapter_content": chapter_content,
            "chapter_number": next_chapter_number,
            "story_id": request.story_id,
            "selected_choice": selected_choice,
            "choices": choices,
            "branch_info": {
                "parent_branch_id": main_branch_id,
                "branched_from_chapter": request.chapter_number,
                "new_chapter_number": next_chapter_number,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("CREATE-BRANCH: Unexpected error: {}".format(str(e)))
        import traceback
        logger.error("CREATE-BRANCH: Full traceback: {}".format(traceback.format_exc()))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/story/{story_id}/branches")
async def get_story_branches_endpoint(
    story_id: int, user = Depends(get_authenticated_user)
):
    """Get all branches for a story to display in the branch visualization."""
    try:
        supabase = deps_get_supabase_client()
        logger.info("Getting branches for story {}".format(story_id))

        # Verify story belongs to user
        story_response = (
            supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        )

        if not story_response.data:
            logger.error("❌ DEBUG - Story {} not found for user {}".format(story_id, user.id))
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        story_data = story_response.data[0]
        logger.info("✅ DEBUG - Found story: {}".format(story_data.get("story_title", "Untitled")))

        # Get Chapters from database
        Chapters_response = (
            supabase.table("Chapters").select("*").eq("story_id", story_id).order("chapter_number").execute()
        )

        Chapters_info: List[Dict[str, Any]] = []
        if Chapters_response.data:
            for chapter in Chapters_response.data:
                Chapters_info.append(
                    {
                        "id": chapter["id"],
                        "chapter_number": chapter["chapter_number"],
                        "title": chapter.get("title", "Untitled"),
                        "content_length": len(chapter.get("content", "")),
                        "content_preview": chapter.get("content", "")[:100]
                        + "..."
                        if len(chapter.get("content", "")) > 100
                        else chapter.get("content", ""),
                        "created_at": chapter.get("created_at"),
                        "has_summary": bool(chapter.get("summary")),
                    }
                )

        logger.info(
            "✅ DEBUG - Found {} Chapters for story {}".format(
                len(Chapters_info), story_id
            )
        )

        return {
            "success": True,
            "story_id": story_id,
            "chapters": Chapters_info,
            "total_chapters": len(Chapters_info),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "CREATE-BRANCH: Unexpected error: {}".format(str(e))
        )
        import traceback
        logger.error(
            "CREATE-BRANCH: Full traceback: {}".format(traceback.format_exc())
        )
        raise HTTPException(status_code=500, detail=str(e))


