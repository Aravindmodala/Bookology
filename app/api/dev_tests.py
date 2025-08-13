from fastapi import APIRouter
from app.core.logger_config import setup_logger
from app.flows.generation.outline_generator import generate_book_outline_json
from app.dependencies.supabase import get_supabase_client
import json


router = APIRouter()
logger = setup_logger(__name__)


@router.post("/test/json_flow")
async def test_json_parsing_flow(test_idea: str = "A revenge story about a young warrior seeking justice"):
    """Test the new summary-based outline generation (no auth required)."""
    try:
        logger.info("Testing JSON flow with idea: {}".format(test_idea))
        result = generate_book_outline_json(test_idea)
        if not result or not result.get("summary"):
            return {
                "step": "json_generation",
                "success": False,
                "error": "No summary returned",
                "raw_response": result,
            }
        return {
            "step": "json_generation",
            "success": True,
            "summary": result["summary"],
            "genre": result.get("genre", ""),
            "tone": result.get("tone", ""),
        }
    except Exception as e:
        logger.error("Test JSON flow failed: {}".format(e))
        return {"step": "json_generation", "success": False, "error": str(e)}


@router.post("/test/formatted_outline")
async def test_formatted_outline(idea: str = "A detective solving mysteries in Victorian London"):
    """Test new summary-based outline output for frontend display (no auth required)."""
    try:
        logger.info("Testing formatted outline for: {}".format(idea))
        result = generate_book_outline_json(idea)
        if not result or not result.get("summary"):
            return {"success": False, "error": "No summary returned", "formatted_text": "❌ Failed to generate outline."}
        return {
            "success": True,
            "idea": idea,
            "formatted_text": result["summary"],
            "genre": result.get("genre", ""),
            "tone": result.get("tone", ""),
        }
    except Exception as e:
        logger.error("Formatted outline test failed: {}".format(e))
        return {"success": False, "error": str(e), "formatted_text": "❌ Error: {}".format(str(e))}


@router.post("/test/complete_json_to_chapter_flow")
async def test_complete_json_to_chapter_flow(idea: str = "A space explorer discovers a mysterious alien artifact"):
    """Test the complete flow: Idea → JSON Outline → Chapter 1 Generation (no auth required)."""
    logger.info("Testing COMPLETE JSON to Chapter 1 flow with idea: {}".format(idea))
    try:
        # Step 1: Generate JSON outline from idea
        logger.info("Step 1: Generating JSON outline...")
        outline_result = generate_book_outline_json(idea)
        if not outline_result["success"]:
            return {"step": "json_generation_failed", "success": False, "error": outline_result["error"], "idea": idea}

        outline_json = outline_result["outline_json"]
        logger.info("Step 1 completed: JSON outline generated successfully")

        # Step 2: Generate Chapter 1 from JSON outline (kept legacy reference verbatim)
        try:
            from lc_book_generator import BookStoryGenerator
        except Exception:
            return {"step": "legacy_missing", "success": False, "outline_json": outline_json, "idea": idea}

        logger.info("Step 2: Generating Chapter 1 from JSON outline...")
        generator = BookStoryGenerator()
        chapter_1_content = generator.generate_chapter_from_json(outline_json, 1)
        if isinstance(chapter_1_content, str) and chapter_1_content.startswith("❌"):
            return {"step": "chapter_generation_failed", "success": False, "error": chapter_1_content, "outline_json": outline_json, "idea": idea}

        logger.info("Step 2 completed: Chapter 1 generated successfully")

        # Step 3: Extract metadata for analysis
        Chapters = outline_json.get("Chapters", [])
        chapter_1_data = next((ch for ch in Chapters if ch.get("chapter_number") == 1), {})

        actual_word_count = len(chapter_1_content.split())
        estimated_word_count = chapter_1_data.get("estimated_word_count", 0)

        return {
            "step": "complete_success",
            "success": True,
            "idea": idea,
            "json_outline": outline_json,
            "formatted_outline": outline_result["formatted_text"],
            "chapter_1_content": chapter_1_content,
            "chapter_1_metadata": chapter_1_data,
            "analysis": {
                "book_title": outline_json.get("book_title", ""),
                "genre": outline_json.get("genre", ""),
                "chapter_1_title": chapter_1_data.get("chapter_title", "Chapter 1"),
                "estimated_word_count": estimated_word_count,
                "actual_word_count": actual_word_count,
                "word_count_accuracy": "{:.1f}%".format((actual_word_count / max(estimated_word_count, 1)) * 100) if estimated_word_count > 0 else "N/A",
                "characters_created": len(outline_json.get("main_characters", [])),
                "locations_created": len(outline_json.get("key_locations", [])),
                "total_chapters_planned": len(Chapters),
                "total_estimated_book_words": sum(ch.get("estimated_word_count", 0) for ch in Chapters),
            },
            "implementation_ready": {
                "has_complete_json": bool(outline_json),
                "has_chapter_content": bool(chapter_1_content and not (isinstance(chapter_1_content, str) and chapter_1_content.startswith("❌"))),
                "ready_for_database": True,
                "can_continue_to_chapter_2": bool(len(Chapters) > 1),
            },
            "usage_instructions": {
                "save_to_database": "Use the /Stories/save endpoint with this data",
                "generate_more_Chapters": "Use /lc_generate_chapter_from_json with chapter_number=2,3,etc",
                "frontend_display": "Use the 'formatted_outline' for user display",
                "database_storage": "Use the 'json_outline' for metadata storage",
            },
        }
    except Exception as e:
        logger.error("Complete flow test failed: {}".format(e))
        return {"step": "error", "success": False, "error": str(e), "idea": idea, "traceback": str(e)}


@router.post("/test/auto_save_outline")
async def test_auto_save_outline_flow(idea: str = "A brave knight embarks on a quest to save the kingdom from an ancient curse"):
    """Test the auto-save outline functionality with authentication bypass."""
    try:
        from types import SimpleNamespace
        supabase = get_supabase_client()
        mock_user = SimpleNamespace(id=999, email="test@bookology.com")

        logger.info("Testing auto-save outline for idea: {}...".format(idea[:50]))
        result = generate_book_outline_json(idea)
        if not result["success"]:
            return {"success": False, "error": "Outline generation failed: {}".format(result["error"])}

        metadata = result["metadata"]
        outline_json = result["outline_json"]
        formatted_text = result["formatted_text"]
        usage_metrics = result.get("usage_metrics", {})

        story_id = None
        database_save_success = False
        try:
            story_data = {
                "user_id": mock_user.id,
                "story_title": outline_json.get("book_title", "Untitled Story"),
                "story_outline": formatted_text,
                "total_chapters": outline_json.get("estimated_total_chapters", 1),
                "current_chapter": 0,
                "outline_json": json.dumps(outline_json),
                "genre": outline_json.get("genre"),
                "theme": outline_json.get("theme"),
                "style": outline_json.get("style"),
                "language": outline_json.get("language", "English"),
                "tags": json.dumps(outline_json.get("tags", [])),
                "main_characters": outline_json.get("main_characters", []),
                "key_locations": outline_json.get("key_locations", []),
                "temperature_used": usage_metrics.get("temperature_used"),
                "token_count_total": usage_metrics.get("estimated_total_tokens"),
                "word_count_total": usage_metrics.get("total_word_count"),
                "model_used": usage_metrics.get("model_used"),
            }
            story_data = {k: v for k, v in story_data.items() if v is not None and v != [] and v != ""}
            story_response = supabase.table("Stories").insert(story_data).execute()
            story_id = story_response.data[0]["id"]
            database_save_success = True
        except Exception as db_error:
            logger.warning("Test database save failed: {}".format(db_error))
            database_save_success = False

        return {
            "success": True,
            "test_type": "auto_save_outline",
            "auto_saved": database_save_success,
            "story_id": story_id,
            "outline_preview": formatted_text[:200] + "...",
            "metadata_extracted": {
                "title": metadata["title"],
                "genre": metadata["genre"],
                "theme": metadata["theme"],
                "style": metadata["style"],
                "Chapters_count": len(outline_json.get("Chapters", [])),
                "characters_count": len(metadata["main_characters"]),
                "locations_count": len(metadata["key_locations"]),
            },
            "database_fields_saved": list(story_data.keys()) if database_save_success else [],
            "message": "✅ Auto-save outline test completed! JSON outline was generated and saved to database automatically." if database_save_success else "⚠️ Outline generated but database save failed.",
        }
    except Exception as e:
        logger.error("Auto-save outline test failed: {}".format(e))
        return {"success": False, "error": str(e)}





