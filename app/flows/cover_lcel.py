# app/flows/cover_lcel.py
from __future__ import annotations

import asyncio
import json
import uuid
import aiohttp
from typing import Dict, Any

from app.core.logger_config import setup_logger
from app.dependencies.supabase import get_supabase_client
from app.services.dalle_service import dalle_service

# LangChain LCEL
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

logger = setup_logger(__name__)

# --------------------------------------------------------------------------------------
# LCEL STEP 1: Fetch the story row (id, title, tone, story_outline) for the given user.
# --------------------------------------------------------------------------------------
async def _fetch_story(inputs: Dict[str, Any]) -> Dict[str, Any]:
    story_id = inputs["story_id"]
    user_id = inputs["user_id"]
    supabase = get_supabase_client()

    logger.info(f"[COVER][LCEL] fetch story story_id={story_id} user_id={user_id}")
    resp = supabase.table("Stories").select(
        "id, user_id, story_title, tone, story_outline, cover_generation_status"
    ).eq("id", story_id).eq("user_id", user_id).single().execute()

    if not resp.data:
        raise ValueError(f"Story {story_id} not found or not owned by user")

    story = resp.data or {}
    if not (story.get("story_outline") or "").strip():
        raise ValueError("Story outline is empty; cannot build prompt")

    logger.info(f"[COVER][LCEL] fetched story title='{story.get('story_title','Untitled')}' tone='{story.get('tone','')}'")
    return {"story": story, **inputs}

FetchStory = RunnableLambda(_fetch_story)

# --------------------------------------------------------------------------------------
# LCEL STEP 2: Build a prompt from story_outline (ONLY) using LLM.
# --------------------------------------------------------------------------------------
_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a senior book cover art director. Create ONE vivid, camera-agnostic image prompt."),
        (
            "user",
            """Title: {title}
Tone: {tone}
Story Outline:
{outline}

Task: Produce ONE rich, professional book cover image prompt (mood, palette, key visuals). 
Avoid camera jargon and technical photography terms."""
        ),
    ]
)

# Use a lightweight, fast model
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

def _prep_prompt_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    s = inputs["story"]
    outline = s.get("story_outline") or ""
    # Keep outline reasonably bounded for prompt
    outline = outline[:2000]
    title = s.get("story_title", "Untitled")
    tone = s.get("tone", "") or ""
    return {"title": title, "tone": tone, "outline": outline}

PrepPromptInputs = RunnableLambda(_prep_prompt_inputs)

def _extract_prompt(msg) -> str:
    content = msg.content if hasattr(msg, "content") else str(msg)
    logger.info(f"[COVER][LCEL] enhanced prompt ready chars={len(content or '')}")
    return (content or "").strip()

ExtractPrompt = RunnableLambda(_extract_prompt)

PromptEnhancer = (PrepPromptInputs | _prompt | llm | ExtractPrompt)

# --------------------------------------------------------------------------------------
# LCEL STEP 3: Generate image with DALL·E 3 using the enhanced prompt.
# --------------------------------------------------------------------------------------
async def _generate_image(inputs: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"[COVER][LCEL] _generate_image inputs keys: {list(inputs.keys())}")
    
    # Story data should now be available from previous steps
    if "story" not in inputs:
        raise ValueError("Story data missing from LCEL chain - check flow structure")
    
    story = inputs["story"]
    enhanced_prompt = inputs["enhanced_prompt"]
    author_email = inputs.get("user_email") or ""
    author_name = author_email.split("@")[0] if author_email else ""

    logger.info("[COVER][LCEL] calling DALL·E size=1024x1792 quality=hd style=vivid")
    res = await dalle_service.generate_image_with_text(
        prompt=enhanced_prompt,
        title=story.get("story_title", "Untitled"),
        author_name=author_name,
        size="1024x1792",   # cover aspect ratio
        quality="hd",
        style="vivid",
    )
    try:
        gid = res.get("generation_id")
        w = res.get("image_width")
        h = res.get("image_height")
        logger.info(f"[COVER][LCEL] dalle done gen_id={gid} dims={w}x{h}")
    except Exception:
        pass
    return {"dalle": res, **inputs}

GenerateImage = RunnableLambda(_generate_image)

# --------------------------------------------------------------------------------------
# LCEL STEP 4: Persist — upload to Supabase Storage and update the DB with permanent URL.
# --------------------------------------------------------------------------------------
async def _persist_and_update(inputs: Dict[str, Any]) -> Dict[str, Any]:
    story_id = inputs["story_id"]
    user_id = inputs["user_id"]
    supabase = get_supabase_client()

    dalle = inputs["dalle"] or {}
    primary_image_url = dalle.get("primary_image_url")
    width = dalle.get("image_width", 1792)
    height = dalle.get("image_height", 1024)
    aspect = dalle.get("aspect_ratio", 1.75)
    prompt_used = inputs.get("enhanced_prompt", "")

    if not primary_image_url:
        # Mark failed if no URL returned
        supabase.table("Stories").update(
            {"cover_generation_status": "failed"}
        ).eq("id", story_id).eq("user_id", user_id).execute()
        return {"success": False, "status": "failed", "error": "No image URL returned"}

    # Attempt to store permanently
    try:
        logger.info("[COVER][LCEL] downloading temp image for storage upload…")
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            async with session.get(primary_image_url) as response:
                if response.status != 200:
                    raise RuntimeError(f"download failed status={response.status}")
                img_bytes = await response.read()
        ext = "png" if primary_image_url.lower().endswith(".png") else "jpg"
        filename = f"{story_id}_{uuid.uuid4().hex}.{ext}"
        supabase.storage.from_("covers").upload(filename, img_bytes, {"content-type": f"image/{ext}"})
        permanent_url = supabase.storage.from_("covers").get_public_url(filename)
        if permanent_url:
            primary_image_url = permanent_url
            logger.info("[COVER][LCEL] image stored and public URL obtained")
    except Exception as e:
        # Keep the temp URL if upload fails
        logger.warning(f"[COVER][LCEL] storage upload failed (keeping temp URL): {e}")

    # Update DB as completed
    logger.info("[COVER][LCEL] updating DB as completed…")
    supabase.table("Stories").update(
        {
            "cover_image_url": primary_image_url,
            "cover_generation_status": "completed",
            "cover_generated_at": "now()",  # mirrors existing pattern
            "cover_prompt": prompt_used,
            "cover_image_width": width,
            "cover_image_height": height,
            "cover_aspect_ratio": aspect,
        }
    ).eq("id", story_id).eq("user_id", user_id).execute()

    return {
        "success": True,
        "status": "completed",
        "story_id": story_id,
        "cover_image_url": primary_image_url,
        "image_width": width,
        "image_height": height,
        "aspect_ratio": aspect,
    }

PersistAndUpdate = RunnableLambda(_persist_and_update)

# --------------------------------------------------------------------------------------
# LCEL STEP 5: Add enhanced_prompt to the inputs for _generate_image.
# --------------------------------------------------------------------------------------
async def _add_enhanced_prompt(inputs: Dict[str, Any]) -> Dict[str, Any]:
    # run the enhancer with the full inputs so it can pick up "story"
    value = await PromptEnhancer.ainvoke(inputs)
    return {**inputs, "enhanced_prompt": value}

AddEnhancedPrompt = RunnableLambda(_add_enhanced_prompt)

# --------------------------------------------------------------------------------------
# LCEL: Full flow (fetch -> prompt -> generate -> persist)
# --------------------------------------------------------------------------------------
Flow = (
    RunnablePassthrough()
    | FetchStory
    | AddEnhancedPrompt
    | GenerateImage
    | PersistAndUpdate
)

# --------------------------------------------------------------------------------------
# Public entrypoint: call this from your endpoint via BackgroundTasks.
# --------------------------------------------------------------------------------------
async def run_cover_flow(story_id: int, user_id: str, user_email: str) -> Dict[str, Any]:
    supabase = get_supabase_client()

    # Mark as generating (idempotent)
    supabase.table("Stories").update(
        {"cover_generation_status": "generating"}
    ).eq("id", story_id).eq("user_id", user_id).execute()

    try:
        logger.info(f"[COVER][LCEL] flow start story_id={story_id} user_id={user_id}")
        result = await Flow.ainvoke({"story_id": story_id, "user_id": user_id, "user_email": user_email})
        logger.info(f"[COVER][LCEL] flow success story_id={story_id}")
        return result
    except Exception as e:
        logger.error(f"[COVER][LCEL] flow failed for story_id={story_id}: {e}")
        supabase.table("Stories").update(
            {"cover_generation_status": "failed"}
        ).eq("id", story_id).eq("user_id", user_id).execute()
        return {"success": False, "status": "failed", "error": str(e)}