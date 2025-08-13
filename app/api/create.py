from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import json

from app.schemas import StorySaveInput, StoryInput
from app.dependencies.supabase import (
    get_authenticated_user,
    get_authenticated_user_optional,
    get_supabase_client as deps_get_supabase_client,
)
from app.core.logger_config import setup_logger
from app.services.embedding_service import embedding_service
from app.services.story_service_with_dna import StoryService
from app.services.chapter_versioning import (
    get_next_chapter_version_number,
    deactivate_previous_chapter_versions,
    save_choices_for_chapter,
)
from app.services.chapter_summary import generate_chapter_summary
from app.flows.generation.outline_generator import generate_book_outline_json


router = APIRouter()
logger = setup_logger(__name__)
story_service = StoryService()


@router.post("/lc_generate_outline")
async def generate_outline_endpoint(
    story: StoryInput,
    user = Depends(get_authenticated_user_optional),
):
    """Generate a cinematic story outline (summary, genre, tone, title, chapters)."""
    try:
        idea = (story.idea or "").strip()
        if len(idea) < 10:
            raise HTTPException(status_code=400, detail="Idea must be at least 10 characters long")

        logger.info(
            "[OUTLINE] Generating outline for %s, idea: %s",
            getattr(user, "id", "anonymous"),
            idea[:50],
        )

        result = generate_book_outline_json(idea)
        if not result or not result.get("summary"):
            raise HTTPException(status_code=500, detail="Outline generation failed: No summary returned.")

        outline_json = result.get("outline_json", {}) or {}

        return {
            "success": True,
            "summary": result["summary"],
            "genre": result["genre"],
            "tone": result["tone"],
            "title": result.get("book_title", ""),
            "chapters": result.get("chapters", []),
            "reflection": result.get("reflection", ""),
            "is_optimized": result.get("is_optimized", False),
            "main_characters": outline_json.get("main_characters", []),
            "key_locations": outline_json.get("key_locations", []),
            "outline_json": outline_json,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[OUTLINE] Failed to generate outline: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


class SaveOutlineRequest(BaseModel):
    story_id: int = Field(..., gt=0)
    outline_json: dict


class SaveOutlineInput(BaseModel):
    # New enhanced outline format
    summary: Optional[str] = Field(default=None, description="Story summary from outline generator")
    genre: Optional[str] = None
    tone: Optional[str] = None
    title: Optional[str] = None
    chapters: List[Dict[str, Any]] = Field(default_factory=list)
    reflection: Optional[str] = None
    is_optimized: Optional[bool] = False
    # Explicit characters and locations
    main_characters: List[str] = Field(default_factory=list)
    key_locations: List[str] = Field(default_factory=list)
    # Legacy format compatibility
    outline_json: Optional[Dict[str, Any]] = None
    formatted_text: Optional[str] = None


@router.post("/save_outline")
async def save_outline_endpoint(
    outline_data: SaveOutlineInput,
    user = Depends(get_authenticated_user_optional),
):
    """Create a new Story from an outline (enhanced or legacy format), matching legacy behavior."""
    supabase = deps_get_supabase_client()
    try:
        user_id = getattr(user, "id", "dev_user")

        # Enhanced format path
        if outline_data.summary:
            story_title = (
                outline_data.title
                if outline_data.title
                else (outline_data.summary.split(".")[0][:50] + "...")
            )

            # Characters/locations, priority: direct fields → outline_json
            main_characters: List[str] = list(outline_data.main_characters or [])
            key_locations: List[str] = list(outline_data.key_locations or [])
            if (not main_characters or not key_locations) and outline_data.outline_json:
                if not main_characters:
                    main_characters = list(outline_data.outline_json.get("main_characters", []) or [])
                if not key_locations:
                    key_locations = list(outline_data.outline_json.get("key_locations", []) or [])

            # Ensure lists
            if not isinstance(main_characters, list):
                main_characters = []
            if not isinstance(key_locations, list):
                key_locations = []

            story_data: Dict[str, Any] = {
                "user_id": user_id,
                "story_title": story_title,
                "story_outline": outline_data.summary,
                "total_chapters": len(outline_data.chapters) if outline_data.chapters else 1,
                "current_chapter": 0,
                "genre": outline_data.genre,
                "style": outline_data.genre,  # mirror legacy mapping
                "language": "English",
                "tags": json.dumps([outline_data.genre.lower()]) if outline_data.genre else json.dumps([]),
                "outline_json": json.dumps(
                    {
                        "summary": outline_data.summary,
                        "genre": outline_data.genre,
                        "tone": outline_data.tone,
                        "chapters": outline_data.chapters,
                        "reflection": outline_data.reflection,
                        "is_optimized": outline_data.is_optimized,
                        "title": story_title,
                        "main_characters": main_characters,
                        "key_locations": key_locations,
                    }
                ),
                # jsonb columns
                "main_characters": main_characters,
                "key_locations": key_locations,
            }

        # Legacy format path
        elif outline_data.outline_json and outline_data.formatted_text:
            outline_json = outline_data.outline_json
            # Build formatted text via helper
            from app.flows.generation.outline_generator import format_json_to_display_text

            formatted_text = format_json_to_display_text(outline_json)

            story_data = {
                "user_id": user_id,
                "story_title": outline_json.get("book_title", "Untitled Story"),
                "story_outline": formatted_text,
                "total_chapters": outline_json.get("estimated_total_chapters", 1),
                "current_chapter": 0,
                "outline_json": json.dumps(outline_json),
                "genre": outline_json.get("genre"),
                "style": outline_json.get("style"),
                "language": outline_json.get("language", "English"),
                "tags": json.dumps(outline_json.get("tags", [])),
                # jsonb arrays (direct Python lists)
                "main_characters": outline_json.get("main_characters", []),
                "key_locations": outline_json.get("key_locations", []),
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid outline data format")

        # Filter out None/empty non-jsonb while preserving empty arrays for jsonb
        filtered: Dict[str, Any] = {}
        jsonb_columns = {"main_characters", "key_locations"}
        for k, v in story_data.items():
            if v is None:
                continue
            if v == "" and k not in jsonb_columns:
                continue
            if v == [] and k not in jsonb_columns:
                continue
            filtered[k] = v

        # Ensure jsonb arrays present
        filtered.setdefault("main_characters", [])
        filtered.setdefault("key_locations", [])

        # Insert story
        story_response = supabase.table("Stories").insert(filtered).execute()
        story_id = story_response.data[0]["id"]

        # Optional verification (as legacy did)
        try:
            verify = supabase.table("Stories").select("main_characters, key_locations").eq("id", story_id).execute()
            _ = verify.data[0] if verify.data else None
        except Exception:
            pass

        return {
            "success": True,
            "message": "Outline saved successfully!",
            "story_id": story_id,
            "story_title": filtered.get("story_title", "Untitled Story"),
            "updated_formatted_text": outline_data.summary or outline_data.formatted_text,
            "characters_extracted": len(filtered.get("main_characters", [])),
            "locations_extracted": len(filtered.get("key_locations", [])),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Save outline failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stories/save")
async def save_story_endpoint(
    story_data: StorySaveInput,
    background_tasks: BackgroundTasks,
    user = Depends(get_authenticated_user),
):
    """Save story with complete JSON metadata parsing and database storage."""
    logger.info("Saving story with JSON parsing: {}".format(story_data.story_title))

    supabase = deps_get_supabase_client()
    try:
        extracted_metadata = {}
        chapter_1_metadata = {}

        if story_data.outline_json:
            logger.info("Parsing JSON outline for complete metadata extraction...")
            json_data = story_data.outline_json

            extracted_metadata = {
                "book_title": json_data.get("book_title", story_data.story_title),
                "genre": json_data.get("genre", story_data.genre),
                "theme": json_data.get("theme", story_data.theme),
                "style": json_data.get("style", story_data.style),
                "description": json_data.get("description", ""),
                "language": json_data.get("language", story_data.language or "English"),
                "tags": json_data.get("tags", story_data.tags or []),
                "estimated_total_chapters": json_data.get(
                    "estimated_total_chapters", story_data.estimated_total_chapters or 1
                ),
                "main_characters": json_data.get("main_characters", story_data.main_characters or []),
                "character_arcs_summary": json_data.get("character_arcs_summary", ""),
                "key_locations": json_data.get("key_locations", story_data.key_locations or []),
                "conflict": json_data.get("conflict", ""),
                "tone_keywords": json_data.get("tone_keywords", story_data.tone_keywords or []),
                "Chapters": json_data.get("Chapters", []),
            }

            total_words = sum(chapter.get("estimated_word_count", 0) for chapter in extracted_metadata["Chapters"])
            extracted_metadata["total_estimated_words"] = total_words or story_data.total_estimated_words

            if extracted_metadata["Chapters"]:
                chapter_1_data = next(
                    (ch for ch in extracted_metadata["Chapters"] if ch.get("chapter_number") == 1),
                    {},
                )
                if chapter_1_data:
                    chapter_1_metadata = {
                        "title": chapter_1_data.get("chapter_title", "Chapter 1"),
                        "summary": chapter_1_data.get("chapter_summary", "First chapter"),
                        "estimated_word_count": chapter_1_data.get("estimated_word_count", 0),
                        "cliffhanger_cta": chapter_1_data.get("cliffhanger_cta", ""),
                    }
        else:
            extracted_metadata = {
                "book_title": story_data.story_title,
                "genre": story_data.genre,
                "theme": story_data.theme,
                "style": story_data.style,
                "language": story_data.language,
                "tags": story_data.tags,
                "estimated_total_chapters": story_data.estimated_total_chapters or 1,
                "total_estimated_words": story_data.total_estimated_words,
                "main_characters": story_data.main_characters,
                "key_locations": story_data.key_locations,
                "tone_keywords": story_data.tone_keywords,
            }

        story_insert_data = {
            "user_id": user.id,
            "story_title": extracted_metadata["book_title"],
            "story_outline": story_data.story_outline,
            "total_chapters": extracted_metadata["estimated_total_chapters"],
            "current_chapter": 1,
        }

        optional_fields = {
            "outline_json": story_data.outline_json,
            "genre": extracted_metadata.get("genre"),
            "theme": extracted_metadata.get("theme"),
            "style": extracted_metadata.get("style"),
            "language": extracted_metadata.get("language"),
            "tags": extracted_metadata.get("tags"),
            "tone_keywords": extracted_metadata.get("tone_keywords"),
            "main_characters": extracted_metadata.get("main_characters"),
            "key_locations": extracted_metadata.get("key_locations"),
        }

        for field, value in optional_fields.items():
            if value is not None and value != [] and value != "":
                story_insert_data[field] = value

        story_insert_data = {k: v for k, v in story_insert_data.items() if v is not None}
        logger.info("Attempting to insert story with fields: {}".format(list(story_insert_data.keys())))

        try:
            story_response = supabase.table("Stories").insert(story_insert_data).execute()
            story_id = story_response.data[0]["id"]
            logger.info("Story inserted successfully with full metadata: {}".format(story_id))
        except Exception as db_error:
            logger.warning("Full metadata insert failed: {}".format(db_error))
            logger.info("Falling back to minimal story insert...")

            minimal_story_data = {
                "user_id": user.id,
                "story_title": extracted_metadata["book_title"],
                "story_outline": story_data.story_outline,
                "total_chapters": extracted_metadata["estimated_total_chapters"],
                "current_chapter": 1,
            }

            story_response = supabase.table("Stories").insert(minimal_story_data).execute()
            story_id = story_response.data[0]["id"]
            logger.info("Story inserted successfully with minimal data: {}".format(story_id))

        word_count = len(story_data.chapter_1_content.split())
        story_context = "STORY: {}\nGENRE: {}\nTHEME: {}\n\nSTORY OUTLINE:\n{}".format(
            extracted_metadata["book_title"],
            extracted_metadata.get("genre", ""),
            extracted_metadata.get("theme", ""),
            story_data.story_outline,
        )

        logger.info("CHAPTER 1 SUMMARY: Calling LLM...")
        summary_result = generate_chapter_summary(
            chapter_content=story_data.chapter_1_content,
            chapter_number=1,
            story_context=story_context,
            story_title=extracted_metadata["book_title"],
        )

        chapter_1_summary = ""
        if summary_result["success"]:
            chapter_1_summary = summary_result["summary"]
        else:
            chapter_1_summary = chapter_1_metadata.get("summary", "First chapter")

        next_version_number = await get_next_chapter_version_number(story_id, 1, supabase)
        await deactivate_previous_chapter_versions(story_id, 1, supabase)

        chapter_insert_data = {
            "story_id": story_id,
            "chapter_number": 1,
            "title": chapter_1_metadata.get("title", "Chapter 1"),
            "content": story_data.chapter_1_content,
            "summary": chapter_1_summary,
            "version_number": next_version_number,
            "is_active": True,
        }

        optional_chapter_fields = {
            "word_count": word_count,
            "cliffhanger_cta": chapter_1_metadata.get("cliffhanger_cta", ""),
        }
        for field, value in optional_chapter_fields.items():
            if value is not None and value != "" and value != []:
                chapter_insert_data[field] = value

        try:
            chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
            if not chapter_response.data:
                chapter_id = None
            else:
                chapter_id = chapter_response.data[0]["id"]
        except Exception:
            minimal_chapter_data = {
                "story_id": story_id,
                "chapter_number": 1,
                "title": chapter_1_metadata.get("title", "Chapter 1"),
                "content": story_data.chapter_1_content,
                "summary": chapter_1_summary,
            }
            chapter_response = supabase.table("Chapters").insert(minimal_chapter_data).execute()
            chapter_id = chapter_response.data[0]["id"]

        choices_saved_count = 0
        if story_data.chapter_1_choices and chapter_id:
            saved_choices = await save_choices_for_chapter(
                story_id=story_id,
                chapter_id=chapter_id,
                chapter_number=1,
                choices=story_data.chapter_1_choices,
                user_id=user.id,
                supabase=supabase,
            )
            choices_saved_count = len(story_data.chapter_1_choices)

        background_tasks.add_task(embedding_service.create_embeddings_async, story_id, False)
        background_tasks.add_task(story_service.invalidate_user_cache, user.id)

        success_message = "Story saved successfully!"
        if chapter_id:
            success_message += " Chapter 1 included."
            if choices_saved_count > 0:
                success_message += f" {choices_saved_count} choices saved."
        else:
            success_message += " (Note: Chapter 1 metadata couldn't be saved due to schema limitations)"

        return {
            "message": success_message,
            "story_id": story_id,
            "chapter_id": chapter_id,
            "choices_saved": choices_saved_count,
            "parsed_metadata": {
                "title": extracted_metadata["book_title"],
                "genre": extracted_metadata["genre"],
                "theme": extracted_metadata["theme"],
                "style": extracted_metadata["style"],
                "language": extracted_metadata["language"],
                "total_chapters": extracted_metadata["estimated_total_chapters"],
                "total_estimated_words": extracted_metadata.get("total_estimated_words", 0),
                "actual_word_count": word_count,
                "tags_count": len(extracted_metadata["tags"]),
                "characters_count": len(extracted_metadata["main_characters"]),
                "locations_count": len(extracted_metadata["key_locations"]),
                "tone_keywords_count": len(extracted_metadata.get("tone_keywords", [])),
                "Chapters_in_outline": len(extracted_metadata.get("Chapters", [])),
            },
            "json_parsing_success": bool(story_data.outline_json),
        }

    except Exception as e:
        logger.error("Story saving with JSON parsing failed: {}".format(e))
        raise HTTPException(status_code=500, detail="Failed to save story with metadata: {}".format(str(e)))


