from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.dependencies.supabase import (
    get_authenticated_user_optional,
    get_authenticated_user,
)
from app.core.logger_config import setup_logger


router = APIRouter()
logger = setup_logger(__name__)


class RewriteTextRequest(BaseModel):
    selected_text: str = Field(..., min_length=1, max_length=2000, description="Text to be rewritten")
    story_context: Optional[dict] = None


@router.post("/rewrite_text")
async def rewrite_text_endpoint(
    request: RewriteTextRequest,
    user = Depends(get_authenticated_user_optional),
):
    """Rewrite selected text using AI for improved clarity, flow, and engagement."""
    import traceback
    try:
        logger.info(f"[REWRITE] Received request from {'authenticated' if user else 'anonymous'} user")
        logger.info(f"[REWRITE] Selected text length: {len(request.selected_text)} characters")

        story_context = request.story_context or {}
        context_info = f"Story: {story_context.get('title', 'Unknown')}, Genre: {story_context.get('genre', 'Unknown')}"
        logger.info(f"[REWRITE] Context: {context_info}")

        from app.flows.generation.outline_generator import rewrite_text_with_context

        rewrite_context = {
            "story_title": story_context.get("title", ""),
            "story_genre": story_context.get("genre", ""),
            "story_outline": story_context.get("outline", ""),
            "current_chapter": story_context.get("currentChapter", ""),
            "chapter_content": story_context.get("chapterContent", ""),
        }

        logger.info("[REWRITE] Calling AI rewrite function...")
        rewritten_text = rewrite_text_with_context(request.selected_text, rewrite_context)

        if not rewritten_text:
            logger.error("[REWRITE] No rewritten text returned from AI")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Rewrite failed: No text returned from AI",
            )

        logger.info(
            f"[REWRITE] Successfully rewritten text, new length: {len(rewritten_text)} characters"
        )

        return {
            "success": True,
            "rewritten_text": rewritten_text,
            "original_length": len(request.selected_text),
            "rewritten_length": len(rewritten_text),
            "improvement_ratio": len(rewritten_text) / len(request.selected_text)
            if len(request.selected_text) > 0
            else 1.0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in rewrite endpoint: {str(e)}")
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rewrite failed: {str(e)}",
        )

"""Streaming rewrite removed; use /rewrite_text instead."""

class SuggestContinueRequest(BaseModel):
    """Input model for AI writing suggestions."""
    current_content: str = Field(
        ..., min_length=10, max_length=10000, description="Current story content"
    )
    story_title: Optional[str] = Field(
        default="Untitled Story", description="Title of the story"
    )
    story_genre: Optional[str] = Field(default="Fiction", description="Genre of the story")
    chapter_title: Optional[str] = Field(default="", description="Current chapter title")

    @field_validator("current_content")
    @classmethod
    def validate_current_content(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Content must be at least 10 characters long")
        return v


@router.post("/suggest_continue")
async def suggest_continue_endpoint(
    request: SuggestContinueRequest,
    user = Depends(get_authenticated_user_optional),
):
    """
    Generate AI-powered writing suggestions to continue the story.
    Similar to GitHub Copilot but for creative writing.
    """
    try:
        logger.info(f"Generating AI suggestion for user {getattr(user, 'id', 'anonymous')}")

        prompt = f"""
        You are an AI writing assistant helping to continue a story. 
        
        Story Title: {request.story_title}
        Genre: {request.story_genre}
        Chapter: {request.chapter_title or 'Current Chapter'}
        
        Current Content:
        {request.current_content}
        
        Please provide a natural continuation of the story. The suggestion should:
        1. Flow naturally from the current content
        2. Maintain the established tone and style
        3. Be 2-4 sentences long
        4. Be engaging and move the story forward
        5. Not repeat what's already written
        
        Write only the continuation, no explanations or meta-commentary.
        """

        from app.services.story_service_with_dna import StoryService

        story_service = StoryService()

        suggestion = await story_service.generate_text(
            prompt=prompt,
            max_tokens=150,
            temperature=0.7,
            system_prompt=
            "You are a creative writing assistant. Provide natural, engaging story continuations.",
        )

        suggestion = suggestion.strip()
        if suggestion.startswith('"') and suggestion.endswith('"'):
            suggestion = suggestion[1:-1]

        logger.info(f"Generated suggestion: {suggestion[:100]}...")

        return {
            "suggestion": suggestion,
            "success": True,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generating AI suggestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI suggestion: {str(e)}",
        )


@router.post("/story_chat")
async def story_chat_endpoint(
    payload: dict,
    user = Depends(get_authenticated_user),
):
    """Chat about a story with retrieval-backed context.

    Expects: { user_id, story_id, message, session_id }
    """
    try:
        from app.services.chatbot import story_chatbot, ChatbotError
        if not story_chatbot:
            raise HTTPException(status_code=500, detail="Chatbot not initialized")
        user_id = str(user.id)
        story_id = str(payload.get("story_id"))
        message = str(payload.get("message") or "").strip()
        session_id = payload.get("session_id")
        if not story_id or not message:
            raise HTTPException(status_code=400, detail="story_id and message are required")
        result = story_chatbot.chat(user_id=user_id, story_id=story_id, message=message, session_id=session_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")
