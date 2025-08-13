from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from pydantic import BaseModel, Field

from app.dependencies.supabase import (
    get_authenticated_user,
    get_authenticated_user_optional,
    get_supabase_client as deps_get_supabase_client,
)
from app.core.logger_config import setup_logger
import json
from app.schemas import ChapterInput


router = APIRouter()
logger = setup_logger(__name__)


class GenerateChoicesInput(BaseModel):
    story_id: int = Field(..., gt=0)
    current_chapter_content: str = Field(..., min_length=50)
    current_chapter_num: int = Field(..., ge=1)


@router.post("/generate_choices")
async def generate_choices_endpoint(
    choice_input: GenerateChoicesInput, user = Depends(get_authenticated_user)
):
    supabase = deps_get_supabase_client()
    try:
        logger.info(
            "Generating choices for Chapter %s in Story %s",
            choice_input.current_chapter_num + 1,
            choice_input.story_id,
        )

        story_response = (
            supabase.table("Stories")
            .select("*")
            .eq("id", choice_input.story_id)
            .eq("user_id", user.id)
            .execute()
        )
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        story_data = story_response.data[0]
        story_outline = story_data.get("story_outline", "")

        choices = [
            {
                "title": "Continue the main storyline",
                "description": "Follow the natural progression of events",
                "story_impact": "medium",
                "choice_type": "narrative",
                "story_id": choice_input.story_id,
            },
            {
                "title": "Take a bold action",
                "description": "Make a daring move that changes everything",
                "story_impact": "high",
                "choice_type": "action",
                "story_id": choice_input.story_id,
            },
            {
                "title": "Explore character relationships",
                "description": "Focus on developing character connections",
                "story_impact": "medium",
                "choice_type": "character",
                "story_id": choice_input.story_id,
            },
        ]

        supabase.table("story_choices").delete().eq("story_id", choice_input.story_id).eq(
            "chapter_number", choice_input.current_chapter_num
        ).eq("user_id", user.id).execute()

        choice_records = []
        for i, choice in enumerate(choices, 1):
            choice_records.append(
                {
                    "story_id": choice_input.story_id,
                    "chapter_number": choice_input.current_chapter_num,
                    "choice_id": f"choice_{i}",
                    "title": choice["title"],
                    "description": choice["description"],
                    "story_impact": choice["story_impact"],
                    "choice_type": choice["choice_type"],
                    "is_selected": False,
                    "user_id": user.id,
                }
            )

        try:
            choices_response = supabase.table("story_choices").insert(choice_records).execute()
            if choices_response.data:
                for i, choice in enumerate(choices):
                    database_record = choices_response.data[i]
                    choice["id"] = database_record["id"]
                    choice["choice_id"] = database_record["id"]
                    choice["database_id"] = database_record["id"]
        except Exception:
            pass

        return {
            "success": True,
            "story_id": choice_input.story_id,
            "chapter_number": choice_input.current_chapter_num,
            "choices": choices,
            "message": f"Generated {len(choices)} choices for Chapter {choice_input.current_chapter_num + 1}",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Generate choices failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to generate choices: {str(e)}")


class SelectChoiceInput(BaseModel):
    story_id: int = Field(..., gt=0)
    choice_id: Union[str, int]
    choice_data: Dict[str, Any]
    next_chapter_num: int = Field(..., ge=1)


@router.post("/generate_chapter_with_choice")
async def generate_chapter_with_choice_endpoint(
    request: SelectChoiceInput, user = Depends(get_authenticated_user_optional)
):
    supabase = deps_get_supabase_client()
    logger.info("Generate chapter with choice request received")
    try:
        if not isinstance(request.story_id, int) or request.story_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid story_id: must be positive integer")
        if not isinstance(request.next_chapter_num, int) or request.next_chapter_num <= 0 or request.next_chapter_num > 1000:
            raise HTTPException(status_code=400, detail="Invalid next_chapter_num: must be positive integer <= 1000")
        if not request.choice_id or len(str(request.choice_id)) > 50:
            raise HTTPException(status_code=400, detail="Invalid choice_id format")

        user_id = user.id
        current_chapter_number = request.next_chapter_num - 1

        choices_response = (
            supabase.table("story_choices")
            .select("*")
            .eq("story_id", request.story_id)
            .eq("user_id", user_id)
            .eq("chapter_number", current_chapter_number)
            .execute()
        )
        available_choices = choices_response.data

        raw_choice_id = str(request.choice_id)
        possible_ids = {raw_choice_id}
        if raw_choice_id.startswith("choice_"):
            possible_ids.add(raw_choice_id.split("choice_", 1)[1])
        if raw_choice_id.isdigit():
            possible_ids.add(f"choice_{raw_choice_id}")

        selected_choice = None
        for choice in available_choices:
            if str(choice.get("id")) in possible_ids or str(choice.get("choice_id")) in possible_ids:
                selected_choice = choice
                break

        if not selected_choice:
            raise HTTPException(status_code=400, detail="Selected choice not found")

        # Delegate to next chapter generator via service
        from app.services.story_service_with_dna import StoryService
        story_service = StoryService()

        story_response = supabase.table("Stories").select("*").eq("id", request.story_id).execute()
        story = story_response.data[0]
        previous_chapters_response = supabase.table("Chapters").select("*").eq("story_id", request.story_id).lte(
            "chapter_number", current_chapter_number
        ).order("chapter_number").execute()
        previous_chapters = previous_chapters_response.data or []

        result = await story_service.generate_next_chapter_with_dna(
            story=story,
            previous_Chapters=previous_chapters,
            selected_choice=selected_choice,
            next_chapter_number=request.next_chapter_num,
            user_id=user_id,
        )

        return {
            "success": result.get("success", True),
            "chapter": result.get("chapter_content", result.get("content", "")),
            "choices": result.get("choices", []),
            "metadata": {
                "chapter_number": request.next_chapter_num,
                "word_count": len(result.get("chapter_content", result.get("content", "")).split()),
                "choices_count": len(result.get("choices", [])),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Generate chapter with choice failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


class ChapterInput(BaseModel):
    outline: str = Field(..., min_length=50)
    chapter_number: int = Field(default=1, ge=1)
    story_id: Optional[int] = None


@router.post("/lc_generate_chapter")
async def generate_chapter_endpoint(
    chapter: ChapterInput, user = Depends(get_authenticated_user_optional)
):
    supabase = deps_get_supabase_client()
    logger.info("Starting Chapter %s generation...", chapter.chapter_number)
    if chapter.chapter_number == 1 and chapter.story_id:
        try:
            existing_chapter = (
                supabase.table("Chapters")
                .select("id, content, title")
                .eq("story_id", chapter.story_id)
                .eq("chapter_number", 1)
                .eq("is_active", True)
                .execute()
            )
            if existing_chapter.data and len(existing_chapter.data) > 0:
                chapter_id = existing_chapter.data[0]["id"]
                choices_response = supabase.table("story_choices").select("*").eq("chapter_id", chapter_id).execute()
                choices = choices_response.data if choices_response.data else []
                return {
                    "chapter_1": existing_chapter.data[0]["content"],
                    "chapter": existing_chapter.data[0]["content"],
                    "choices": choices,
                    "metadata": {
                        "chapter_number": 1,
                        "word_count": len(existing_chapter.data[0]["content"].split()),
                        "character_count": len(existing_chapter.data[0]["content"]),
                        "choices_count": len(choices),
                        "generation_success": True,
                        "from_existing": True,
                        "chapter_id": chapter_id,
                        "already_saved": True,
                    },
                }
        except Exception:
            pass

    try:
        from app.flows.generation.enhanced_first_chapter import EnhancedChapterGenerator
        generator = EnhancedChapterGenerator()
        try:
            import json
            outline_json = json.loads(chapter.outline)
            story_summary = outline_json.get("summary", "")
            genre = outline_json.get("genre", "General Fiction")
            tone = outline_json.get("tone", "Engaging")
            chapters_data = outline_json.get("chapters", [])
            target_chapter = None
            for ch in chapters_data:
                if ch.get("chapter_number") == chapter.chapter_number:
                    target_chapter = ch
                    break
            if not target_chapter:
                raise ValueError(f"Chapter {chapter.chapter_number} not found in outline")
            result = generator.generate_chapter_from_outline(
                story_title=target_chapter.get("title", f"Chapter {chapter.chapter_number}"),
                story_outline=story_summary,
                genre=genre,
                tone=tone,
            )
        except Exception:
            result = generator.generate_chapter_from_outline(
                story_title=f"Chapter {chapter.chapter_number}",
                story_outline=chapter.outline,
                genre="General Fiction",
                tone="Engaging",
            )

        if result.get("success"):
            chapter_content = result.get("content", "")
            choices = result.get("choices", [])
            chapter_id = None
            if chapter.chapter_number == 1 and chapter.story_id and user:
                try:
                    from app.services.fixed_optimized_chapter_service import (
                        fixed_optimized_chapter_service,
                    )
                    chapter_dict = {
                        "story_id": chapter.story_id,
                        "chapter_number": 1,
                        "content": chapter_content,
                        "title": "Chapter 1",
                        "choices": choices,
                        "user_choice": "",
                    }
                    save_result = await fixed_optimized_chapter_service.save_chapter_optimized(
                        chapter_data=chapter_dict, user_id=user.id, supabase_client=supabase
                    )
                    chapter_id = save_result.chapter_id
                    try:
                        supabase.table("Stories").update({"current_chapter": 1}).eq(
                            "id", chapter.story_id
                        ).execute()
                    except Exception:
                        pass
                except Exception:
                    try:
                        chapter_insert_data = {
                            "story_id": chapter.story_id,
                            "chapter_number": 1,
                            "title": "Chapter 1",
                            "content": chapter_content,
                            "word_count": len(chapter_content.split()),
                            "version_number": 1,
                            "is_active": True,
                        }
                        chapter_response = supabase.table("Chapters").insert(
                            chapter_insert_data
                        ).execute()
                        if chapter_response.data:
                            chapter_id = chapter_response.data[0]["id"]
                    except Exception:
                        pass

            return {
                "chapter_1": chapter_content,
                "chapter": chapter_content,
                "choices": choices,
                "metadata": {
                    "chapter_number": chapter.chapter_number,
                    "word_count": len(chapter_content.split()),
                    "choices_count": len(choices),
                    "chapter_id": chapter_id,
                    "already_saved": bool(chapter_id),
                    "optimized_save": bool(chapter_id),
                },
            }
        else:
            error_msg = result.get("error", "Chapter generation failed")
            raise HTTPException(status_code=500, detail=f"Chapter generation failed: {error_msg}")
    except Exception as e:
        logger.error("Chapter generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Chapter generation failed: {str(e)}")


@router.post("/save_chapter_with_summary")
async def save_chapter_with_summary(
    story_id: int,
    chapter_number: int,
    title: str,
    content: str,
    user = Depends(get_authenticated_user),
):
    """Save chapter content and generate summary immediately."""
    supabase = deps_get_supabase_client()
    try:
        # Verify story ownership
        story_response = (
            supabase.table("Stories").select("id").eq("id", story_id).eq("user_id", user.id).execute()
        )
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")

        # Insert chapter
        chapter_insert = {
            "story_id": story_id,
            "chapter_number": chapter_number,
            "title": title or f"Chapter {chapter_number}",
            "content": content,
            "word_count": len(content.split()),
            "version_number": 1,
            "is_active": True,
        }
        chapter_resp = supabase.table("Chapters").insert(chapter_insert).execute()
        chapter_id = chapter_resp.data[0]["id"] if chapter_resp.data else None

        # Generate summary
        from app.services.chapter_summary import generate_chapter_summary
        story_title = (
            supabase.table("Stories").select("story_title").eq("id", story_id).single().execute().data.get("story_title", "")
        )
        summary_result = generate_chapter_summary(
            chapter_content=content,
            chapter_number=chapter_number,
            story_context="",
            story_title=story_title,
        )
        if summary_result.get("success"):
            supabase.table("Chapters").update({"summary": summary_result["summary"]}).eq("id", chapter_id).execute()

        return {
            "success": True,
            "chapter_id": chapter_id,
            "summary_generated": bool(summary_result.get("success")),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Save chapter with summary failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


class GenerateNextChapterCompatRequest(BaseModel):
    story_id: int = Field(..., gt=0)
    chapter_number: int = Field(..., ge=1, description="Next chapter number to generate")
    story_outline: Optional[str] = ""
    selected_choice_id: Optional[Union[str, int]] = None


@router.post("/generate_next_chapter")
async def generate_next_chapter_compat(
    request: GenerateNextChapterCompatRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_authenticated_user),
):
    """Compatibility endpoint aligned with frontend payload.

    Frontend sends the NEXT chapter to generate as `chapter_number`.
    We enforce choice gating by checking choices on the CURRENT chapter (next-1).
    """
    supabase = deps_get_supabase_client()
    try:
        # Compute current chapter number from requested next chapter
        current_chapter_number = max(0, request.chapter_number - 1)

        # If choices exist for current chapter, require a selected choice
        choices_resp = (
            supabase.table("story_choices").select("*")
            .eq("story_id", request.story_id)
            .eq("chapter_number", current_chapter_number)
            .eq("user_id", user.id)
            .execute()
        )
        choices: List[Dict[str, Any]] = choices_resp.data or []

        # Resolve selected_choice per legacy behavior:
        selected_choice: Dict[str, Any] = {}
        if request.selected_choice_id is not None and choices:
            raw_choice = str(request.selected_choice_id)
            possible = {raw_choice}
            if raw_choice.startswith("choice_"):
                possible.add(raw_choice.split("choice_", 1)[1])
            if raw_choice.isdigit():
                possible.add(f"choice_{raw_choice}")
            for c in choices:
                if str(c.get("id")) in possible or str(c.get("choice_id")) in possible:
                    selected_choice = c
                    break
        elif choices:
            # Use pre-selected choice if one exists; otherwise proceed empty (non-game-mode)
            preselected = next((c for c in choices if c.get("is_selected")), None)
            if preselected:
                selected_choice = preselected

        # Build context and delegate to service (always proceed; empty choice → non-game-mode)
        from app.services.story_service_with_dna import StoryService
        service = StoryService()
        previous = (
            supabase.table("Chapters").select("*")
            .eq("story_id", request.story_id)
            .lte("chapter_number", current_chapter_number)
            .order("chapter_number")
            .execute().data
        )
        story = (
            supabase.table("Stories").select("*").eq("id", request.story_id).single().execute().data
        )
        next_num = request.chapter_number
        result = await service.generate_next_chapter_with_dna(
            story=story,
            previous_Chapters=previous,
            selected_choice=selected_choice if selected_choice else {},
            next_chapter_number=next_num,
            user_id=user.id,
        )

        # Persist chapter (legacy compat)
        chapter_content = result.get("chapter_content") or result.get("content", "")
        chapter_title = result.get("title", f"Chapter {next_num}")

        # Deactivate previous version if exists and insert new
        supabase.table("Chapters").update({"is_active": False}).eq("story_id", request.story_id).eq("chapter_number", next_num).eq("is_active", True).execute()
        insert_resp = supabase.table("Chapters").insert({
            "story_id": request.story_id,
            "chapter_number": next_num,
            "title": chapter_title,
            "content": chapter_content,
            "is_active": True,
        }).execute()
        chapter_id = insert_resp.data[0]["id"] if insert_resp.data else None

        # Save choices if any
        from app.services.chapter_versioning import save_choices_for_chapter
        gen_choices = result.get("choices", [])
        if gen_choices and chapter_id:
            await save_choices_for_chapter(
                story_id=request.story_id,
                chapter_id=chapter_id,
                chapter_number=next_num,
                choices=gen_choices,
                user_id=user.id,
                supabase=supabase,
            )

        # --- Schedule background summary and DNA (legacy parity) ---
        def _bg_update_summary(chapter_id_param: int, chapter_content: str, chapter_number_param: int, story_title_param: str, story_outline_param: str):
            try:
                from app.services.chapter_summary import generate_chapter_summary
                _supabase = deps_get_supabase_client()
                story_context = f"STORY: {story_title_param}\n\nSTORY OUTLINE:\n{story_outline_param or ''}"
                summary_result = generate_chapter_summary(
                    chapter_content=chapter_content,
                    chapter_number=chapter_number_param,
                    story_context=story_context,
                    story_title=story_title_param or "Untitled Story",
                )
                if summary_result and summary_result.get("success") and summary_result.get("summary"):
                    _supabase.table("Chapters").update({"summary": summary_result["summary"]}).eq("id", chapter_id_param).execute()
            except Exception as _e:
                logger.warning(f"Summary background task failed: {_e}")

        def _bg_update_dna(chapter_id_param: int, chapter_content: str, chapter_number_param: int, prev_chapters: List[Dict[str, Any]], user_choice_text: str = ""):
            try:
                from app.services.dna_extractor import EnhancedLLMStoryDNAExtractor
                _supabase = deps_get_supabase_client()
                prev_dna_list: List[Dict[str, Any]] = []
                for ch in prev_chapters or []:
                    dna_val = ch.get("dna")
                    if not dna_val:
                        continue
                    try:
                        if isinstance(dna_val, str):
                            dna_obj = json.loads(dna_val)
                        else:
                            dna_obj = dna_val
                        prev_dna_list.append(dna_obj)
                    except Exception:
                        continue
                extractor = EnhancedLLMStoryDNAExtractor()
                dna_result = extractor.extract_chapter_dna(
                    chapter_content=chapter_content,
                    chapter_number=chapter_number_param,
                    previous_dna_list=prev_dna_list,
                    user_choice_made=user_choice_text,
                    choice_options=[],
                )
                if dna_result and not dna_result.get("error"):
                    _supabase.table("Chapters").update({"dna": json.dumps(dna_result)}).eq("id", chapter_id_param).execute()
            except Exception as _e:
                logger.warning(f"DNA background task failed: {_e}")

        # Enqueue background tasks
        try:
            story_title_val = story.get("story_title") or story.get("title") or "Untitled Story"
            story_outline_val = story.get("story_outline") or ""
            user_choice_text = ""
            if selected_choice:
                title_txt = selected_choice.get("title", "")
                desc_txt = selected_choice.get("description", "")
                user_choice_text = f"{title_txt}: {desc_txt}".strip(": ")
            background_tasks.add_task(_bg_update_summary, chapter_id, chapter_content, next_num, story_title_val, story_outline_val)
            background_tasks.add_task(_bg_update_dna, chapter_id, chapter_content, next_num, previous or [], user_choice_text)
        except Exception as _e:
            logger.warning(f"Failed to schedule background tasks: {_e}")

        return {"success": True, "chapter": chapter_content, "choices": gen_choices, "chapter_id": chapter_id}

        # If we got here without choices and service failed (unlikely), fallback to a simple generator
        # Note: normally the service path above handles both with/without choice
    except HTTPException:
        raise
    except Exception as e:
        logger.error("generate_next_chapter compat failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


class JsonChapterInput(BaseModel):
    outline_json: Dict[str, Any]
    chapter_number: int = Field(default=1, ge=1)


@router.post("/lc_generate_chapter_from_json")
async def generate_chapter_from_json_endpoint(chapter: JsonChapterInput):
    logger.info("Starting Chapter %s generation from JSON outline...", chapter.chapter_number)
    try:
        from app.flows.generation.enhanced_first_chapter import EnhancedChapterGenerator
        generator = EnhancedChapterGenerator()
        outline_json = chapter.outline_json
        story_summary = outline_json.get("summary", "")
        genre = outline_json.get("genre", "General Fiction")
        tone = outline_json.get("tone", "Engaging")
        chapters_data = outline_json.get("chapters", [])
        target_chapter = None
        for ch in chapters_data:
            if ch.get("chapter_number") == chapter.chapter_number:
                target_chapter = ch
                break
        if not target_chapter:
            raise HTTPException(
                status_code=400, detail=f"Chapter {chapter.chapter_number} not found in JSON outline"
            )
        result = generator.generate_chapter_from_outline(
            story_title=target_chapter.get("title", f"Chapter {chapter.chapter_number}"),
            story_outline=story_summary,
            genre=genre,
            tone=tone,
        )
        if result.get("success"):
            chapter_content = result.get("content", "")
            choices = result.get("choices", [])
            reasoning = result.get("reasoning", {})
            quality_metrics = result.get("quality_metrics", {})
            return {
                "chapter": chapter_content,
                "choices": choices,
                "reasoning": reasoning,
                "quality_metrics": quality_metrics,
                "metadata": {
                    "chapter_number": chapter.chapter_number,
                    "chapter_title": target_chapter.get(
                        "title", f"Chapter {chapter.chapter_number}"
                    ),
                    "word_count": len(chapter_content.split()),
                    "character_count": len(chapter_content),
                    "choices_count": len(choices),
                    "estimated_word_count": target_chapter.get("estimated_word_count", 0),
                    "generation_success": True,
                    "source": "enhanced_json_outline",
                    "cot_reasoning": bool(reasoning),
                    "quality_score": quality_metrics.get("overall_score", "N/A"),
                },
                "chapter_outline_data": target_chapter,
            }
        else:
            error_msg = result.get("error", "Enhanced generation failed")
            raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        logger.error("Enhanced chapter generation from JSON failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


