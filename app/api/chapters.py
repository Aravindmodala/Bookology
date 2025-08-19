from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from pydantic import BaseModel, Field
 

from app.dependencies.supabase import (
    get_authenticated_user,
    get_authenticated_user_optional,
    get_supabase_client as deps_get_supabase_client,
    get_async_db_pool,
)
from app.core.concurrency import DB_SEMAPHORE
from app.core.logger_config import setup_logger
import json
import asyncio
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
    async with DB_SEMAPHORE:
        try:
            logger.info(
                "Generating choices for Chapter %s in Story %s",
                choice_input.current_chapter_num + 1,
                choice_input.story_id,
            )

            # Use async PostgreSQL pool for better performance
            pool = await get_async_db_pool()
            
            # Get story data
            async with pool.acquire() as conn:
                story_rows = await conn.fetch(
                    "SELECT * FROM \"Stories\" WHERE id = $1 AND user_id = $2",
                    choice_input.story_id, user.id
                )
                
                if not story_rows:
                    raise HTTPException(status_code=404, detail="Story not found or access denied")

                story_data = dict(story_rows[0])
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

            # Delete existing choices and insert new ones
            async with pool.acquire() as conn:
                # Delete existing choices
                await conn.execute(
                    "DELETE FROM story_choices WHERE story_id = $1 AND chapter_number = $2 AND user_id = $3",
                    choice_input.story_id, choice_input.current_chapter_num, user.id
                )

                # Insert new choices
                choice_records = []
                for i, choice in enumerate(choices, 1):
                    choice_records.append((
                        choice_input.story_id,
                        choice_input.current_chapter_num,
                        f"choice_{i}",
                        choice["title"],
                        choice["description"],
                        choice["story_impact"],
                        choice["choice_type"],
                        False,  # is_selected
                        user.id,
                    ))

                # Batch insert for better performance
                await conn.executemany(
                    """
                    INSERT INTO story_choices 
                    (story_id, chapter_number, choice_id, title, description, story_impact, choice_type, is_selected, user_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                    """,
                    choice_records
                )

                # Get inserted IDs
                inserted_rows = await conn.fetch(
                    "SELECT id FROM story_choices WHERE story_id = $1 AND chapter_number = $2 AND user_id = $3 ORDER BY choice_id",
                    choice_input.story_id, choice_input.current_chapter_num, user.id
                )

                # Update choices with database IDs
                for i, row in enumerate(inserted_rows):
                    choices[i]["id"] = row["id"]
                    choices[i]["choice_id"] = row["id"]
                    choices[i]["database_id"] = row["id"]

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
    async with DB_SEMAPHORE:
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

            # Use async PostgreSQL pool for better performance
            pool = await get_async_db_pool()
            
            # Get available choices
            async with pool.acquire() as conn:
                choices_rows = await conn.fetch(
                    "SELECT * FROM story_choices WHERE story_id = $1 AND user_id = $2 AND chapter_number = $3",
                    request.story_id, user_id, current_chapter_number
                )
                available_choices = [dict(row) for row in choices_rows]

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

            # Get story and previous chapters
            async with pool.acquire() as conn:
                story_rows = await conn.fetch(
                    "SELECT * FROM \"Stories\" WHERE id = $1",
                    request.story_id
                )
                story = dict(story_rows[0]) if story_rows else {}
                
                previous_chapters_rows = await conn.fetch(
                    "SELECT * FROM \"Chapters\" WHERE story_id = $1 AND chapter_number <= $2 ORDER BY chapter_number",
                    request.story_id, current_chapter_number
                )
                previous_chapters = [dict(row) for row in previous_chapters_rows]

            result = await story_service.generate_next_chapter_with_dna(
                story=story,
                previous_Chapters=previous_chapters,
                selected_choice=selected_choice,
                next_chapter_number=request.next_chapter_num,
                user_id=user_id,
            )

            # Persist chapter
            chapter_content = result.get("chapter_content") or result.get("content", "")
            chapter_title = result.get("title", f"Chapter {request.next_chapter_num}")

            # Deactivate previous version and insert new
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE \"Chapters\" SET is_active = false WHERE story_id = $1 AND chapter_number = $2 AND is_active = true",
                    request.story_id, request.next_chapter_num
                )
                
                chapter_row = await conn.fetchrow(
                    """
                    INSERT INTO "Chapters" (story_id, chapter_number, title, content, is_active)
                    VALUES ($1, $2, $3, $4, true)
                    RETURNING id
                    """,
                    request.story_id, request.next_chapter_num, chapter_title, chapter_content
                )
                chapter_id = chapter_row["id"] if chapter_row else None

            # Save choices if any
            from app.services.chapter_versioning import save_choices_for_chapter
            gen_choices = result.get("choices", [])
            if gen_choices and chapter_id:
                await save_choices_for_chapter(
                    story_id=request.story_id,
                    chapter_id=chapter_id,
                    chapter_number=request.next_chapter_num,
                    choices=gen_choices,
                    user_id=user_id,
                    supabase=deps_get_supabase_client(),  # Keep sync for now
                )

            # Increase-only update of current_chapter
            try:
                async with pool.acquire() as conn:
                    current_val_row = await conn.fetchrow(
                        "SELECT current_chapter FROM \"Stories\" WHERE id = $1",
                        request.story_id
                    )
                    current_val = current_val_row["current_chapter"] if current_val_row else 0
                    
                    if int(current_val) < int(request.next_chapter_num):
                        await conn.execute(
                            "UPDATE \"Stories\" SET current_chapter = $1 WHERE id = $2",
                            request.next_chapter_num, request.story_id
                        )
                        logger.info(f"✅ Updated story current_chapter to {request.next_chapter_num}")
            except Exception as update_error:
                logger.warning(f"⚠️ Could not update story current_chapter: {update_error}")

            return {
                "success": result.get("success", True),
                "chapter": chapter_content,
                "choices": gen_choices,
                "metadata": {
                    "chapter_number": request.next_chapter_num,
                    "word_count": len(chapter_content.split()),
                    "choices_count": len(gen_choices),
                    "chapter_id": chapter_id,
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
            # Prefer genre from DB when story_id is provided
            genre = outline_json.get("genre", "General Fiction")
            if chapter.story_id:
                try:
                    db_story_row = (
                        supabase.table("Stories").select("genre").eq("id", chapter.story_id).single().execute().data
                    )
                    if db_story_row and db_story_row.get("genre"):
                        genre = db_story_row.get("genre")
                except Exception:
                    # Fallback to outline_json genre if DB lookup fails
                    pass
            tone = outline_json.get("tone", "Engaging")
            chapters_data = outline_json.get("chapters", [])
            target_chapter = None
            for ch in chapters_data:
                if ch.get("chapter_number") == chapter.chapter_number:
                    target_chapter = ch
                    break
            if not target_chapter:
                raise ValueError(f"Chapter {chapter.chapter_number} not found in outline")
            result = await generator.generate_chapter_from_outline(
                story_title=target_chapter.get("title", f"Chapter {chapter.chapter_number}"),
                story_outline=story_summary,
                genre=genre,
                tone=tone,
            )
        except Exception:
            result = await generator.generate_chapter_from_outline(
                story_title=f"Chapter {chapter.chapter_number}",
                story_outline=chapter.outline,
                # Prefer genre from DB when story_id is provided
                genre=(
                    (
                        supabase.table("Stories").select("genre").eq("id", chapter.story_id).single().execute().data.get("genre")
                        if chapter.story_id else None
                    )
                    or "General Fiction"
                ),
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
                            # Fallback path: also save choices if present
                            if choices:
                                # Normalize choices to expected shape
                                normalized_choices = []
                                for i, ch in enumerate(choices, 1):
                                    if isinstance(ch, dict) and ("text" in ch or "consequence" in ch):
                                        normalized_choices.append({
                                            "title": (ch.get("text") or "").strip(),
                                            "description": (ch.get("consequence") or "").strip(),
                                            "story_impact": (ch.get("consequence") or "").strip(),
                                            "choice_type": ch.get("choice_type", "story_choice"),
                                            "choice_id": ch.get("id", str(i)),
                                        })
                                    else:
                                        normalized_choices.append(ch)
                                try:
                                    for rec in normalized_choices:
                                        supabase.table("story_choices").insert({
                                            "story_id": chapter.story_id,
                                            "chapter_id": chapter_id,
                                            "chapter_number": 1,
                                            "choice_id": rec.get("choice_id", str(i)),
                                            "title": rec.get("title", ""),
                                            "description": rec.get("description", ""),
                                            "story_impact": rec.get("story_impact", ""),
                                            "choice_type": rec.get("choice_type", "story_choice"),
                                            "is_selected": False,
                                            "user_id": getattr(user, 'id', None),
                                        }).execute()
                                except Exception:
                                    pass
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
            .eq("is_active", True)
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
        # Normalize choice shape from first-chapter generator (text/consequence) to title/description
        if gen_choices:
            normalized_choices = []
            for i, ch in enumerate(gen_choices, 1):
                if isinstance(ch, dict) and ("text" in ch or "consequence" in ch):
                    normalized_choices.append({
                        "title": (ch.get("text") or "").strip(),
                        "description": (ch.get("consequence") or "").strip(),
                        "story_impact": (ch.get("consequence") or "").strip(),
                        "choice_type": ch.get("choice_type", "story_choice"),
                        "choice_id": ch.get("id", str(i)),
                    })
                else:
                    normalized_choices.append(ch)
            gen_choices = normalized_choices

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

        # Increase-only update of current_chapter (rewrites shouldn't bump)
        try:
            current_val_resp = supabase.table("Stories").select("current_chapter").eq("id", request.story_id).single().execute()
            current_val = (current_val_resp.data or {}).get("current_chapter") or 0
            if int(current_val) < int(next_num):
                supabase.table("Stories").update({"current_chapter": next_num}).eq("id", request.story_id).execute()
                logger.info(f"✅ Updated story current_chapter to {next_num}")
        except Exception as update_error:
            logger.warning(f"⚠️ Could not update story current_chapter: {update_error}")

        return {"success": True, "chapter": chapter_content, "choices": gen_choices, "chapter_id": chapter_id}

        # If we got here without choices and service failed (unlikely), fallback to a simple generator
        # Note: normally the service path above handles both with/without choice
    except HTTPException:
        raise
    except Exception as e:
        logger.error("generate_next_chapter compat failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# === Streaming endpoints for next/rewrite chapters ===
class StreamNextChapterRequest(BaseModel):
    story_id: int = Field(..., gt=0)
    chapter_number: int = Field(..., ge=1, description="Chapter number to generate (use current number for rewrite)")
    selected_choice_id: Optional[Union[str, int]] = None


async def _generate_and_persist_next_chapter(request: StreamNextChapterRequest, user) -> Dict[str, Any]:
    """Shared logic to generate a chapter using StoryService and persist it.

    Returns dict with: chapter_content, chapter_title, choices, chapter_id
    """
    supabase = deps_get_supabase_client()
    current_chapter_number = max(0, request.chapter_number - 1)

    # Resolve selected choice
    choices_resp = (
        supabase.table("story_choices").select("*")
        .eq("story_id", request.story_id)
        .eq("chapter_number", current_chapter_number)
        .eq("user_id", user.id)
        .execute()
    )
    available_choices: List[Dict[str, Any]] = choices_resp.data or []

    selected_choice: Dict[str, Any] = {}
    if request.selected_choice_id is not None and available_choices:
        raw_choice = str(request.selected_choice_id)
        possible = {raw_choice}
        if raw_choice.startswith("choice_"):
            possible.add(raw_choice.split("choice_", 1)[1])
        if raw_choice.isdigit():
            possible.add(f"choice_{raw_choice}")
        for c in available_choices:
            if str(c.get("id")) in possible or str(c.get("choice_id")) in possible:
                selected_choice = c
                break
    elif available_choices:
        preselected = next((c for c in available_choices if c.get("is_selected")), None)
        if preselected:
            selected_choice = preselected

    from app.services.story_service_with_dna import StoryService
    service = StoryService()
    previous = (
        supabase.table("Chapters").select("*")
        .eq("story_id", request.story_id)
        .eq("is_active", True)
        .lte("chapter_number", current_chapter_number)
        .order("chapter_number")
        .execute().data
    )
    story = (
        supabase.table("Stories").select("*").eq("id", request.story_id).single().execute().data
    )

    result = await service.generate_next_chapter_with_dna(
        story=story,
        previous_Chapters=previous,
        selected_choice=selected_choice if selected_choice else {},
        next_chapter_number=request.chapter_number,
        user_id=user.id,
    )

    chapter_content: str = result.get("chapter_content") or result.get("content", "")
    chapter_title: str = result.get("title", f"Chapter {request.chapter_number}")

    # Deactivate previous version then insert new
    supabase.table("Chapters").update({"is_active": False}).eq("story_id", request.story_id).eq("chapter_number", request.chapter_number).eq("is_active", True).execute()
    insert_resp = supabase.table("Chapters").insert({
        "story_id": request.story_id,
        "chapter_number": request.chapter_number,
        "title": chapter_title,
        "content": chapter_content,
        "is_active": True,
    }).execute()
    chapter_id = insert_resp.data[0]["id"] if insert_resp.data else None

    # Save choices if present
    from app.services.chapter_versioning import save_choices_for_chapter
    gen_choices = result.get("choices", []) or []
    if gen_choices:
        normalized_choices = []
        for i, ch in enumerate(gen_choices, 1):
            if isinstance(ch, dict) and ("text" in ch or "consequence" in ch):
                normalized_choices.append({
                    "title": (ch.get("text") or "").strip(),
                    "description": (ch.get("consequence") or "").strip(),
                    "story_impact": (ch.get("consequence") or "").strip(),
                    "choice_type": ch.get("choice_type", "story_choice"),
                    "choice_id": ch.get("id", str(i)),
                })
            else:
                normalized_choices.append(ch)
        gen_choices = normalized_choices

    if gen_choices and chapter_id:
        await save_choices_for_chapter(
            story_id=request.story_id,
            chapter_id=chapter_id,
            chapter_number=request.chapter_number,
            choices=gen_choices,
            user_id=user.id,
            supabase=supabase,
        )

    # Update current_chapter if needed
    try:
        current_val_resp = supabase.table("Stories").select("current_chapter").eq("id", request.story_id).single().execute()
        current_val = (current_val_resp.data or {}).get("current_chapter") or 0
        if int(current_val) < int(request.chapter_number):
            supabase.table("Stories").update({"current_chapter": request.chapter_number}).eq("id", request.story_id).execute()
    except Exception as _e:
        logger.warning(f"Could not update story current_chapter: {_e}")

    # Schedule background summary and DNA updates (non-blocking)
    try:
        story_title_val = story.get("story_title") or story.get("title") or "Untitled Story"
        story_outline_val = story.get("story_outline") or ""
        user_choice_text = ""
        if selected_choice:
            title_txt = selected_choice.get("title", "")
            desc_txt = selected_choice.get("description", "")
            user_choice_text = f"{title_txt}: {desc_txt}".strip(": ")

        def _bg_update_summary(ch_id, content, ch_num, title, outline):
            try:
                from app.services.chapter_summary import generate_chapter_summary
                _sb = deps_get_supabase_client()
                ctx = f"STORY: {title}\n\nSTORY OUTLINE:\n{outline or ''}"
                res = generate_chapter_summary(chapter_content=content, chapter_number=ch_num, story_context=ctx, story_title=title)
                if res and res.get("success") and res.get("summary"):
                    _sb.table("Chapters").update({"summary": res["summary"]}).eq("id", ch_id).execute()
            except Exception as _e2:
                logger.warning(f"[STREAM-NEXT] Summary task failed: {_e2}")

        def _bg_update_dna(ch_id, content, ch_num, prev, choice_txt):
            try:
                from app.services.dna_extractor import EnhancedLLMStoryDNAExtractor
                import json as _json
                _sb = deps_get_supabase_client()
                prev_dnas = []
                for ch in prev or []:
                    dna_val = ch.get("dna")
                    if not dna_val:
                        continue
                    try:
                        prev_dnas.append(_json.loads(dna_val) if isinstance(dna_val, str) else dna_val)
                    except Exception:
                        continue
                extractor = EnhancedLLMStoryDNAExtractor()
                dna_res = extractor.extract_chapter_dna(content, ch_num, prev_dnas, choice_txt, [])
                if dna_res and not dna_res.get("error"):
                    _sb.table("Chapters").update({"dna": _json.dumps(dna_res)}).eq("id", ch_id).execute()
            except Exception as _e2:
                logger.warning(f"[STREAM-NEXT] DNA task failed: {_e2}")

        if chapter_id:
            import asyncio as _asyncio
            _asyncio.create_task(_asyncio.to_thread(_bg_update_summary, chapter_id, chapter_content, request.chapter_number, story_title_val, story_outline_val))
            _asyncio.create_task(_asyncio.to_thread(_bg_update_dna, chapter_id, chapter_content, request.chapter_number, previous or [], user_choice_text))
    except Exception as _e:
        logger.warning(f"[STREAM-NEXT] Failed to schedule background tasks: {_e}")

    return {
        "chapter_content": chapter_content,
        "chapter_title": chapter_title,
        "choices": gen_choices,
        "chapter_id": chapter_id,
    }


# Streaming helper removed


# Streaming next/rewrite endpoints removed; use non-streaming endpoints instead


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
        result = await generator.generate_chapter_from_outline(
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


@router.post("/stream_first_chapter")
async def stream_first_chapter(
	chapter: ChapterInput,
	user = Depends(get_authenticated_user_optional),
):
	"""
	Streaming removed. Use /lc_generate_chapter to get full chapter at once.
	"""
	return {"error": "Streaming removed. Use /lc_generate_chapter instead."}


