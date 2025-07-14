"""
Optimized main.py with service layer architecture and async operations.
"""

import asyncio
from typing import Dict, Any, List, Union
from contextlib import asynccontextmanager
import json
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, field_validator

from config import settings
from logger_config import setup_logger
from exceptions import *

# Import optimized services
from services import DatabaseService, StoryService, EmbeddingService, CacheService
from services.database_service import db_service
from services.story_service import story_service  
from services.embedding_service import embedding_service
from services.cache_service import cache_service

# Import models
from models.story_models import Story, Chapter
from models.chat_models import ChatMessage, ChatResponse

# Keep original imports for compatibility
from story_chatbot import StoryChatbot
from supabase import create_client, Client
from typing import Optional

from chapter_summary import generate_chapter_summary, build_story_context_for_next_chapter

logger = setup_logger(__name__)

# Authentication
auth_scheme = HTTPBearer()

# Initialize services at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with simplified initialization."""
    logger.info("Starting Bookology backend with simplified services...")
    
    try:
        # Initialize Supabase client only (minimal initialization)
        global supabase
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized")
        
        logger.info("Basic services initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        yield
    finally:
        # Minimal cleanup
        logger.info("Application shutdown complete")

# FastAPI app with lifespan
app = FastAPI(
    title="Bookology API - Optimized",
    description="High-performance story generation and chat API with service layer architecture",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep original models for compatibility
class StoryInput(BaseModel):
    idea: str = Field(..., min_length=10, max_length=500)
    format: Optional[str] = Field(default="book", pattern="^(book|movie)$")
    story_id: Optional[int] = Field(default=None, description="Optional story ID for continuation")
    
    @field_validator('idea')
    @classmethod
    def validate_idea(cls, v):
        if not v.strip():
            raise ValueError("Story idea cannot be empty")
        return v.strip()

class ChapterInput(BaseModel):
    outline: str = Field(..., min_length=50)
    chapter_number: int = Field(default=1, ge=1)
    story_id: Optional[int] = Field(default=None, description="Story ID for saving generated chapter")

class StorySaveInput(BaseModel):
    story_outline: str = Field(..., min_length=50)
    chapter_1_content: str = Field(..., min_length=100)
    story_title: str = Field(..., min_length=1, max_length=200)
    # New metadata fields
    outline_json: Optional[Dict[str, Any]] = None
    genre: Optional[str] = None
    theme: Optional[str] = None
    style: Optional[str] = None
    language: str = "English"
    tags: List[str] = Field(default_factory=list)
    tone_keywords: List[str] = Field(default_factory=list)
    estimated_total_chapters: Optional[int] = None
    total_estimated_words: Optional[int] = None
    main_characters: List[Dict[str, Any]] = Field(default_factory=list)
    key_locations: List[Dict[str, Any]] = Field(default_factory=list)
    # New field for automatic choices
    chapter_1_choices: List[Dict[str, Any]] = Field(default_factory=list, description="Auto-generated choices for Chapter 1")

class StoryChatRequest(BaseModel):
    """Input model for story chat interactions."""
    story_id: int = Field(..., gt=0, description="ID of the story to chat about")
    message: str = Field(..., min_length=1, max_length=1000, description="User message")

# Initialize chatbot (keep for compatibility) - DISABLED due to connection issues
# story_chatbot = StoryChatbot()
story_chatbot = None

# Initialize Supabase client globally
supabase: Optional[Client] = None

# Authentication dependency (keep original for compatibility)
async def get_authenticated_user(token = Depends(auth_scheme)):
    """Get authenticated user - optimized version."""
    try:
        global supabase
        if not supabase:
            # Fallback: create client if global one not available
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        
        user_response = supabase.auth.get_user(token.credentials)
        user = user_response.user
        
        if not user:
            raise AuthorizationError("Invalid or expired token")
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# Optional auth scheme  
optional_auth_scheme = HTTPBearer(auto_error=False)

async def get_authenticated_user_optional(token = Depends(optional_auth_scheme)):
    """Get authenticated user but return None if not authenticated (no error)."""
    if not token:
        return None
        
    try:
        global supabase
        if not supabase:
            # Fallback: create client if global one not available
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        
        user_response = supabase.auth.get_user(token.credentials)
        user = user_response.user
        
        return user  # Return user or None
        
    except Exception as e:
        logger.info(f"Optional authentication failed (this is OK): {e}")
        return None  # Return None instead of raising error

async def get_current_user_from_token(token_string: str):
    """Extract user from raw token string (for manual token parsing)."""
    try:
        global supabase
        if not supabase:
            # Fallback: create client if global one not available
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        
        # Use the raw token string directly
        user_response = supabase.auth.get_user(token_string)
        user = user_response.user
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        logger.info(f"User authenticated successfully: {user.id}")
        return user
        
    except Exception as e:
        logger.error(f"Token authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check with service status."""
    try:
        # Check service health
        story_stats = await story_service.get_service_stats()
        embedding_stats = await embedding_service.get_service_stats()
        cache_stats = cache_service.get_cache_stats()
        
        return {
            "status": "healthy",
            "version": "2.0.0",
            "services": {
                "database": {
                    "async_pool": story_stats["database_pool_initialized"],
                    "connection": "ok"
                },
                "cache": cache_stats,
                "embeddings": {
                    "initialized": embedding_stats["initialized"],
                    "collection": embedding_stats["vectorstore_collection"]
                },
                "story_service": "ok"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded", 
            "error": str(e)
        }

# Optimized Stories endpoint
@app.get("/stories")
async def get_user_stories_optimized(user = Depends(get_authenticated_user)):
    """Get user Stories with caching and async operations."""
    logger.info(f"Fetching Stories for user {user.id}")
    
    try:
        Stories = await story_service.get_user_Stories(user.id)
        
        # Convert to API format
        story_list = []
        for story in Stories:
            story_list.append({
                "id": story.id,
                "title": story.story_title,
                "outline": story.outline or "",
                "created_at": story.created_at.isoformat(),
                "source_table": story.source_table,
                "chapter_count": story.current_chapter or 0
            })
        
        return {"Stories": story_list}
        
    except Exception as e:
        logger.error(f"Failed to fetch Stories for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Stories"
        )

# Optimized embedding endpoint
@app.post("/stories/{story_id}/ensure_embeddings")
async def ensure_story_embeddings_optimized(
    story_id: int, 
    user = Depends(get_authenticated_user)
):
    """Ensure embeddings exist with async operations and caching."""
    logger.info(f"Ensuring embeddings for story {story_id}")
    
    try:
        # Verify user has access to this story
        story = await story_service.get_story(story_id, user.id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        # Ensure embeddings
        result = await embedding_service.ensure_embeddings(story_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ensure embeddings for story {story_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ensure embeddings"
        )

# Optimized chat endpoint - TEMPORARILY DISABLED
# @app.post("/story_chat")
# async def story_chat_optimized(body: StoryChatRequest, user = Depends(get_authenticated_user)):
#     """Process story chat with optimized embedding lookup."""
#     logger.info(f"Story chat request from user {user.id} for story {body.story_id}")
#     
#     try:
#         # Verify story access
#         story = await story_service.get_story(body.story_id, user.id)
#         if not story:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Story not found"
#             )
#         
#         # Ensure embeddings exist
#         await embedding_service.ensure_embeddings(body.story_id)
#         
#         # Process chat with proper type conversion
#         response = story_chatbot.chat(
#             str(user.id),
#             str(body.story_id),  # Convert int to str for chatbot
#             body.message
#         )
#         
#         logger.info("Story chat response generated successfully")
#         return response
#         
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Story chat failed: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Chat processing failed"
#         )

# Original story generation endpoints for compatibility
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Root endpoint."""
    return HTMLResponse(content="<h1>Bookology API - Optimized v2.0</h1><p>Visit /docs for API documentation</p>")

@app.post("/lc_generate_outline")
async def generate_outline_endpoint(story: StoryInput, user = Depends(get_authenticated_user_optional)):
    """Generate structured JSON story outline with formatted text display AND auto-save to database."""
    try:
        from lc_book_generator_prompt import generate_book_outline_json
        
        user_info = f"user {user.id}" if user else "anonymous user"
        logger.info(f"Generating outline for {user_info}, idea: {story.idea[:50]}...")
        
        # Generate JSON outline with formatted text
        result = generate_book_outline_json(story.idea)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Outline generation failed: {result['error']}"
            )
        
        # Extract data from result
        metadata = result["metadata"]
        outline_json = result["outline_json"]
        formatted_text = result["formatted_text"]  # Nicely formatted for frontend display
        usage_metrics = result.get("usage_metrics", {})  # LLM usage metrics
        
        logger.info(f"Successfully generated outline with {len(outline_json.get('Chapters', []))} Chapters")
        logger.info(f"📊 LLM Usage: {usage_metrics.get('estimated_total_tokens', 0)} tokens, {usage_metrics.get('total_word_count', 0)} words")
        
        # Note: Auto-save removed - outline will only be saved when user clicks "Save & Continue"
        logger.info(f"✨ Outline generated successfully - ready for user editing and manual save")
        
        # Return response with outline data for user editing
        return {
            "success": True,
            # Frontend display (what the user sees)
            "expanded_prompt": formatted_text,  # Formatted text with static fields + JSON data
            "outline_text": formatted_text,    # Same as above for compatibility
            
            # Database info (no auto-save)
            "auto_saved": False,  # Changed: no auto-save
            "story_id": None,     # Changed: no story ID until manual save
            
            # Structured data for potential frontend use
            "outline_json": outline_json,
            "metadata": {
                "title": metadata["title"],
                "genre": metadata["genre"],
                "theme": metadata["theme"],
                "style": metadata["style"],
                "language": metadata["language"],
                "estimated_total_chapters": metadata["estimated_total_chapters"],
                "total_estimated_words": metadata["total_estimated_words"],
                "estimated_reading_time_hours": metadata["estimated_reading_time_hours"],
                "tags": metadata["tags"],
                "tone_keywords": metadata["tone_keywords"],
                "character_count": metadata["character_count"],
                "location_count": metadata["location_count"],
                "chapter_count": metadata["chapter_count"]
            },
            
            # Detailed structured data
            "characters": metadata["main_characters"],
            "locations": metadata["key_locations"],
            "Chapters": metadata["Chapters"],
            
            # Additional info
            "generation_info": {
                "json_parsing_success": True,
                "Chapters_generated": len(outline_json.get("Chapters", [])),
                "characters_created": len(metadata["main_characters"]),
                "locations_created": len(metadata["key_locations"]),
                "total_estimated_words": metadata["total_estimated_words"],
                "ready_for_database": True,
                "auto_saved_to_db": False  # Changed: no auto-save
            }
        }
        
    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint for saving edited outline
class SaveOutlineInput(BaseModel):
    outline_json: Dict[str, Any] = Field(..., description="Edited outline JSON data")
    formatted_text: str = Field(..., min_length=50, description="Formatted outline text")

@app.post("/save_outline")
async def save_outline_endpoint(
    outline_data: SaveOutlineInput,
    user = Depends(get_authenticated_user)
):
    """Save the user-edited outline to database."""
    try:
        logger.info(f"💾 Saving edited outline to database for user {user.id}...")
        
        outline_json = outline_data.outline_json
        
        # Regenerate formatted text with the updated character names
        from lc_book_generator_prompt import format_json_to_display_text
        formatted_text = format_json_to_display_text(outline_json)
        
        logger.info(f"✅ Regenerated formatted text with updated character names")
        
        # Prepare story data for database save
        story_data = {
            "user_id": user.id,
            "story_title": outline_json.get("book_title", "Untitled Story"),
            "story_outline": formatted_text,  # Save the regenerated formatted text
            "total_chapters": outline_json.get("estimated_total_chapters", 1),
            "current_chapter": 0,  # 0 = outline only, no Chapters written yet
            
            # Map exact JSON fields to database columns
            "outline_json": json.dumps(outline_json),  # Store full JSON as text
            "genre": outline_json.get("genre"),
            "theme": outline_json.get("theme"), 
            "style": outline_json.get("style"),
            "language": outline_json.get("language", "English"),
            "tags": json.dumps(outline_json.get("tags", [])),  # Convert array to JSON string
            "main_characters": outline_json.get("main_characters", []),  # JSONB column - keep as array
            "key_locations": outline_json.get("key_locations", []),  # JSONB column - keep as array
        }
        
        # Remove None values to avoid database errors
        story_data = {k: v for k, v in story_data.items() if v is not None and v != [] and v != ""}
        
        logger.info(f"Saving outline to database with fields: {list(story_data.keys())}")
        
        try:
            # Try saving to database
            story_response = supabase.table("Stories").insert(story_data).execute()
            story_id = story_response.data[0]["id"]
            logger.info(f"✅ Outline saved successfully with story_id: {story_id}")

            # --- OUTLINE SAVED SUCCESSFULLY, BUT DON'T AUTO-GENERATE CHAPTER 1 ---
            # The user should explicitly click "Generate Chapter 1" to create chapters
            logger.info(f"✅ Outline saved successfully. User can now generate Chapter 1 manually.")
            
            return {
                "success": True,
                "message": "Outline saved successfully!",
                "story_id": story_id,
                "story_title": outline_json.get("book_title", "Untitled Story"),
                "updated_formatted_text": formatted_text  # Return the updated text for frontend
            }
            
        except Exception as save_error:
            logger.error(f"❌ Database save failed: {save_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save outline: {str(save_error)}"
            )
            
    except Exception as e:
        logger.error(f"Save outline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# New endpoints for branching choices feature
# OLD GENERATE_CHOICES ENDPOINT REMOVED
# Choices are now automatically generated with Chapters
# See /lc_generate_chapter and /generate_next_chapter endpoints

class GenerateChoicesInput(BaseModel):
    story_id: int = Field(..., gt=0, description="ID of the story")
    current_chapter_content: str = Field(..., min_length=50, description="Content of the current chapter")
    current_chapter_num: int = Field(..., ge=1, description="Current chapter number")

@app.post("/generate_choices")
async def generate_choices_endpoint(
    choice_input: GenerateChoicesInput,
    user = Depends(get_authenticated_user)
):
    """Generate 3-4 choices for the next chapter based on current chapter content."""
    try:
        logger.info(f"🎯 Generating choices for Chapter {choice_input.current_chapter_num + 1}, Story {choice_input.story_id}")
        
        # CRITICAL: Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", choice_input.story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            logger.error(f"❌ STORY ISOLATION: Story {choice_input.story_id} not found for user {user.id}")
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story_data = story_response.data[0]
        story_outline = story_data.get("story_outline", "")
        
        logger.info(f"✅ Story verified: {story_data.get('story_title', 'Untitled')}")
        
        # Generate choices using existing logic (simplified for now)
        from lc_book_generator import BookStoryGenerator
        generator = BookStoryGenerator()
        
        # Create context for choice generation
        choice_context = f"""
STORY OUTLINE:
{story_outline}

CURRENT CHAPTER {choice_input.current_chapter_num} CONTENT:
{choice_input.current_chapter_content}

Generate 3-4 meaningful choices for what happens next in Chapter {choice_input.current_chapter_num + 1}.
Each choice should lead to different story directions and consequences.
"""
        
        # Generate choices (simplified version - will get real IDs from database)
        choices = [
            {
                "title": "Continue the main storyline",
                "description": "Follow the natural progression of events",
                "story_impact": "medium",
                "choice_type": "narrative",
                "story_id": choice_input.story_id
            },
            {
                "title": "Take a bold action",
                "description": "Make a daring move that changes everything",
                "story_impact": "high",
                "choice_type": "action",
                "story_id": choice_input.story_id
            },
            {
                "title": "Explore character relationships",
                "description": "Focus on developing character connections",
                "story_impact": "medium",
                "choice_type": "character",
                "story_id": choice_input.story_id
            }
        ]
        
        # Save choices to database FIRST to get real database IDs
        choice_records = []
        for i, choice in enumerate(choices, 1):
            choice_records.append({
                "story_id": choice_input.story_id,
                "chapter_number": choice_input.current_chapter_num,
                "choice_id": f"choice_{i}",  # Temporary ID for database
                "title": choice["title"],
                "description": choice["description"],
                "story_impact": choice["story_impact"],
                "choice_type": choice["choice_type"],
                "is_selected": False,
                "user_id": user.id
            })
        
        # Insert choices into database to get real IDs
        try:
            choices_response = supabase.table("story_choices").insert(choice_records).execute()
            if choices_response.data:
                logger.info(f"✅ Saved {len(choice_records)} choices to database for story {choice_input.story_id}")
                
                # CRITICAL FIX: Update choices with real database IDs
                for i, choice in enumerate(choices):
                    database_record = choices_response.data[i]
                    choice["id"] = database_record["id"]  # Use real database ID
                    choice["choice_id"] = database_record["id"]  # Use real database ID
                    choice["database_id"] = database_record["id"]  # Keep reference
                    
                logger.info(f"🔧 Updated choices with database IDs: {[c['id'] for c in choices]}")
            else:
                logger.warning("⚠️ Failed to save choices to database")
        except Exception as e:
            logger.error(f"❌ Error saving choices: {e}")
            # Continue anyway - don't break the user experience
 
        return {
            "success": True,
            "story_id": choice_input.story_id,  # CRITICAL: Include for frontend validation
            "chapter_number": choice_input.current_chapter_num,
            "choices": choices,
            "message": f"Generated {len(choices)} choices for Chapter {choice_input.current_chapter_num + 1}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Generate choices failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate choices: {str(e)}")

class SelectChoiceInput(BaseModel):
    story_id: int = Field(..., gt=0, description="ID of the story")
    choice_id: Union[str, int] = Field(..., description="ID of the selected choice")
    choice_data: Dict[str, Any] = Field(..., description="The full choice object that was selected")
    next_chapter_num: int = Field(..., ge=1, description="Next chapter number to generate")
    token: str = Field(..., description="Authentication token")

@app.post("/generate_chapter_with_choice")
async def generate_chapter_with_choice_endpoint(request: SelectChoiceInput):
    logger.info(f"🔄 Generate chapter with choice request received")
    logger.info(f"📊 Request data: story_id={request.story_id}, next_chapter_num={request.next_chapter_num}, choice_id={request.choice_id}")
    logger.info(f"📊 Request choice_id type: {type(request.choice_id)}")
    logger.info(f"📊 Request choice_id value: '{request.choice_id}'")
    
    try:
        # Get user from token
        user = await get_current_user_from_token(request.token)
        user_id = user.id
        logger.info(f"👤 User authenticated: {user_id}")

        # First, fetch all available choices for this chapter to validate
        current_chapter_number = request.next_chapter_num - 1  # Choices are for the previous chapter
        logger.info(f"🔍 Fetching available choices for story {request.story_id}, chapter {current_chapter_number}")
        choices_response = supabase.table('story_choices').select('*').eq('story_id', request.story_id).eq('user_id', user_id).eq('chapter_number', current_chapter_number).execute()
        
        available_choices = choices_response.data
        logger.info(f"📋 Available choices count: {len(available_choices)}")
        
        for i, choice in enumerate(available_choices):
            logger.info(f"📋 Choice {i+1}: id={choice.get('id')}, choice_id={choice.get('choice_id')}, title='{choice.get('choice_title', 'No title')}'")
            logger.info(f"📋 Choice {i+1} types: id type={type(choice.get('id'))}, choice_id type={type(choice.get('choice_id'))}")

        # Try to find the selected choice by matching with both id and choice_id fields
        selected_choice = None
        
        # First try to match with 'id' field (database primary key)
        for choice in available_choices:
            if str(choice.get('id')) == str(request.choice_id):
                selected_choice = choice
                logger.info(f"✅ Found choice by 'id' field: {choice}")
                break
        
        # If not found, try to match with 'choice_id' field (user-facing identifier)
        if not selected_choice:
            for choice in available_choices:
                if str(choice.get('choice_id')) == str(request.choice_id):
                    selected_choice = choice
                    logger.info(f"✅ Found choice by 'choice_id' field: {choice}")
                    break
        
        if not selected_choice:
            logger.error(f"❌ No choice found matching request.choice_id='{request.choice_id}'")
            logger.error(f"❌ Available choice IDs: {[choice.get('id') for choice in available_choices]}")
            logger.error(f"❌ Available choice_ids: {[choice.get('choice_id') for choice in available_choices]}")
            raise HTTPException(status_code=400, detail="Invalid choice selected")

        logger.info(f"🎯 Selected choice found: {selected_choice}")
        
        # Mark this choice as selected in the database
        logger.info(f"💾 Marking choice as selected in database")
        from datetime import datetime
        update_response = supabase.table('story_choices').update({
            'is_selected': True,
            'selected_at': datetime.utcnow().isoformat()
        }).eq('id', selected_choice['id']).execute()

        # Get the story details
        logger.info(f"📖 Fetching story details for story_id={request.story_id}")
        story_response = supabase.table('Stories').select('*').eq('id', request.story_id).eq('user_id', user_id).single().execute()
        story = story_response.data
        logger.info(f"📖 Story retrieved: title='{story.get('story_title', 'No title')}'")

        # Get all previous Chapters
        logger.info(f"📚 Fetching previous Chapters for story_id={request.story_id}")
        Chapters_response = supabase.table('Chapters').select('*').eq('story_id', request.story_id).order('chapter_number').execute()
        previous_Chapters = Chapters_response.data
        logger.info(f"📚 Previous Chapters count: {len(previous_Chapters)}")

        # Generate the next chapter
        logger.info(f"⚡ Starting chapter generation process")
        next_chapter_number = request.next_chapter_num
        logger.info(f"📝 Next chapter number will be: {next_chapter_number}")

        # Use the story service to generate the next chapter
        try:
            logger.info(f"🎯 Generating Chapter {next_chapter_number} with choice: '{selected_choice.get('title', 'Unknown')}'")
            logger.info(f"📝 LLM Input: Story='{story['story_title']}', Previous Chapters={len(previous_Chapters)}, Choice='{selected_choice.get('title', 'Unknown')}'")
            
            next_chapter_result = await story_service.generate_next_chapter(
                story=story,
                previous_Chapters=previous_Chapters,
                selected_choice=selected_choice,
                next_chapter_number=next_chapter_number,
                user_id=user_id
            )
            logger.info(f"✅ Chapter {next_chapter_number} generated successfully")
            
        except Exception as generation_error:
            logger.error(f"❌ Chapter generation failed: {str(generation_error)}")
            logger.error(f"❌ Generation error type: {type(generation_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate next chapter: {str(generation_error)}")

        logger.info(f"🎉 Chapter generation process completed successfully")

        # --- SAVE GENERATED CHAPTER TO DATABASE ---
        try:
            logger.info(f"💾 Saving generated chapter {next_chapter_number} to database...")
            
            # Get the next version number for this chapter
            next_version_number = await get_next_chapter_version_number(request.story_id, next_chapter_number)
            
            # Deactivate previous versions of this chapter
            await deactivate_previous_chapter_versions(request.story_id, next_chapter_number)
            
            # Use the correct key for chapter content
            chapter_text = next_chapter_result.get("chapter_content") or next_chapter_result.get("chapter") or next_chapter_result.get("content", "")
            chapter_insert_data = {
                "story_id": request.story_id,
                "chapter_number": next_chapter_number,
                "title": next_chapter_result.get("title") or f"Chapter {next_chapter_number}",
                "content": chapter_text,
                "word_count": len(chapter_text.split()),
                "version_number": next_version_number,  # Add proper versioning
                "is_active": True,  # Mark this version as active
                # No summary at this stage; can be added later
                # Token tracking fields (optional, if available)
                "token_count_prompt": next_chapter_result.get("token_count_prompt"),
                "token_count_completion": next_chapter_result.get("token_count_completion"),
                "token_count_total": next_chapter_result.get("token_count_total"),
                "temperature_used": next_chapter_result.get("temperature_used"),
            }
            chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
            if not chapter_response.data:
                logger.error(f"❌ DATABASE ERROR: Insert returned no data")
                raise HTTPException(status_code=500, detail="Failed to save generated chapter")
            chapter_id = chapter_response.data[0]["id"]
            logger.info(f"✅ Chapter saved with ID: {chapter_id}")
            # --- GENERATE AND SAVE CHAPTER SUMMARY ---
            
            try:
                from chapter_summary import generate_chapter_summary
                story_outline = story.get("story_outline", "") if 'story' in locals() else ""

                summary_result = generate_chapter_summary(
                    chapter_content=chapter_text,
                    chapter_number=next_chapter_number,
                    story_context=story_outline,
                    story_title=story.get("story_title", "Untitled Story") if 'story' in locals() else "Untitled Story"
                )

                if summary_result["success"]:
                    summary_text = summary_result["summary"]
                    
                    update_response = supabase.table("Chapters").update({"summary": summary_text}).eq("id", chapter_id).execute()
                    
                    # Verify the update worked
                    verify_response = supabase.table("Chapters").select("summary").eq("id", chapter_id).execute()
                    if verify_response.data and verify_response.data[0].get("summary"):
                        logger.info(f"✅ Chapter {next_chapter_number} summary saved and verified in database")
                    else:
                        logger.error(f"❌ Chapter {next_chapter_number} summary update may have failed")
                else:
                    logger.error(f"❌ Failed to generate summary for chapter {next_chapter_number}")
            except Exception as summary_error:
                import traceback
        except Exception as db_error:
            logger.error(f"❌ DATABASE INSERT FAILED: {str(db_error)}")
            raise HTTPException(status_code=500, detail=f"Database insert failed: {str(db_error)}")

        # --- SAVE GENERATED CHOICES FOR THE NEW CHAPTER ---
        try:
            choices = next_chapter_result.get("choices", [])
            if choices:
                await save_choices_for_chapter(
                    story_id=request.story_id,
                    chapter_id=chapter_id,
                    chapter_number=next_chapter_number,
                    choices=choices,
                    user_id=user_id
                )
        except Exception as choice_error:
            logger.error(f"❌ Failed to save choices: {str(choice_error)}")
            # Continue anyway - don't break the user experience
        
        # Update story's current_chapter
        supabase.table("Stories").update({"current_chapter": next_chapter_number}).eq("id", request.story_id).execute()
        
        response_payload = {
            "success": True,
            "message": "Next chapter generated and saved successfully",
            "chapter_content": chapter_text,  # Frontend expects this field
            "chapter_number": next_chapter_result.get("chapter_number", request.next_chapter_num),
            "story_id": request.story_id,  # Include story_id for verification
            "chapter": next_chapter_result,  # Keep full chapter data
            "selected_choice": selected_choice,
            "choices": next_chapter_result.get("choices", [])  # Include any new choices generated
        }
        logger.info(f"🚀 Returning response to frontend: success={response_payload.get('success')}, chapter_number={response_payload.get('chapter_number')}, choices_count={len(response_payload.get('choices', []))}")
        return response_payload

    except HTTPException:
        logger.error(f"❌ HTTP Exception occurred, re-raising")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in generate_chapter_with_choice: {str(e)}")
        logger.error(f"❌ Error type: {type(e)}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/story/{story_id}/choice_history")
async def get_choice_history_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """Get the complete choice history for a story showing all paths taken and not taken."""
    try:
        logger.info(f"📚 Getting choice history for story {story_id}")
        
        # Get all choices for this story
        choices_response = supabase.table("story_choices").select("*").eq("story_id", story_id).eq("user_id", user.id).order("chapter_number").order("choice_id").execute()
        
        if not choices_response.data:
            return {
                "success": True,
                "story_id": story_id,
                "choice_history": [],
                "message": "No choices found for this story"
            }
        
        # Organize choices by chapter
        choice_history = {}
        for choice in choices_response.data:
            chapter_num = choice["chapter_number"]
            if chapter_num not in choice_history:
                choice_history[chapter_num] = {
                    "chapter_number": chapter_num,
                    "choices": [],
                    "selected_choice": None
                }
            
            choice_data = {
                "id": choice["id"],  # CRITICAL: Include database ID
                "choice_id": choice["choice_id"],
                "title": choice["title"],
                "description": choice["description"],
                "story_impact": choice["story_impact"],
                "choice_type": choice["choice_type"],
                "is_selected": choice["is_selected"],
                "selected_at": choice.get("selected_at"),  # Include selected_at timestamp
                "created_at": choice["created_at"]
            }
            
            choice_history[chapter_num]["choices"].append(choice_data)
            
            if choice["is_selected"]:
                choice_history[chapter_num]["selected_choice"] = choice_data
        
        # Convert to list and sort by chapter number
        history_list = list(choice_history.values())
        history_list.sort(key=lambda x: x["chapter_number"])
        
        logger.info(f"✅ Retrieved choice history for {len(history_list)} Chapters")
        
        return {
            "success": True,
            "story_id": story_id,
            "choice_history": history_list,
            "total_chapters_with_choices": len(history_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get choice history failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get choice history: {str(e)}")

@app.get("/chapter/{chapter_id}/choices")
async def get_choices_for_chapter_endpoint(
    chapter_id: int,
    user = Depends(get_authenticated_user)
):
    """Get all choices for a specific chapter version by chapter_id."""
    try:
        logger.info(f"🎯 Getting choices for chapter ID {chapter_id}")
        
        # First verify the chapter belongs to a story owned by this user
        chapter_response = supabase.table("Chapters").select("story_id").eq("id", chapter_id).execute()
        if not chapter_response.data:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        story_id = chapter_response.data[0]["story_id"]
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("id").eq("id", story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Chapter not found or access denied")
        
        # Get choices for this specific chapter version
        choices_response = supabase.table("story_choices").select("*").eq("chapter_id", chapter_id).execute()
        
        choices = choices_response.data or []
        
        # Format choices for frontend
        formatted_choices = []
        for choice in choices:
            formatted_choice = {
                "id": choice["id"],
                "choice_id": choice.get("choice_id", choice["id"]),
                "title": choice["title"],
                "description": choice["description"],
                "story_impact": choice["story_impact"],
                "choice_type": choice["choice_type"],
                "is_selected": choice.get("is_selected", False),
                "selected_at": choice.get("selected_at"),
                "created_at": choice["created_at"],
                "chapter_id": choice["chapter_id"],
                "story_id": choice["story_id"]
            }
            formatted_choices.append(formatted_choice)
        
        logger.info(f"✅ Retrieved {len(formatted_choices)} choices for chapter ID {chapter_id}")
        
        return {
            "success": True,
            "chapter_id": chapter_id,
            "story_id": story_id,
            "choices": formatted_choices,
            "total_choices": len(formatted_choices)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get choices for chapter failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get choices for chapter: {str(e)}")

@app.post("/lc_generate_chapter")
async def generate_chapter_endpoint(chapter: ChapterInput, user = Depends(get_authenticated_user_optional)):
    """Generate story chapter from either text or JSON outline."""
    logger.info(f"📖 Starting Chapter {chapter.chapter_number} generation...")
    logger.info(f"Outline length: {len(chapter.outline)} characters")
    
    try:
        from lc_book_generator import BookStoryGenerator
        generator = BookStoryGenerator()
        
        # Enhanced logging to see what's happening
        logger.info("🚀 Invoking BookStoryGenerator...")
        
        result = generator.generate_chapter(chapter.outline, chapter.chapter_number)
        
        logger.info(f"✅ Chapter {chapter.chapter_number} generation completed!")
        
        # Log the raw result for debugging
        
        # Handle new JSON response structure
        if isinstance(result, dict) and result.get("success"):
            chapter_content = result.get("chapter_content", "")
            choices = result.get("choices", [])
            
            logger.info(f"📊 Generated: {len(chapter_content)} chars, {len(choices)} choices")
            
            # Validate chapter content
            if not chapter_content or len(chapter_content.strip()) < 50:
                logger.error(f"❌ Chapter content too short: {len(chapter_content)} characters")
                logger.error(f"❌ Chapter content too short: {len(chapter_content)} characters")
                raise HTTPException(status_code=500, detail="Generated chapter content is too short or empty")

            # --- SAVE CHAPTER 1 AND CHOICES TO DATABASE ---
            try:
                # Only save if this is Chapter 1 and we have a story_id
                if chapter.chapter_number == 1 and chapter.story_id:
                    logger.info(f"💾 Saving Chapter 1 content to Chapters table...")
                    # Get main branch ID for this story
                    main_branch_id = await get_main_branch_id(chapter.story_id)
                    
                    # Get the next version number for this chapter (with branch support)
                    next_version_number = await get_next_chapter_version_number(chapter.story_id, 1, main_branch_id)
                    
                    # Deactivate previous versions of this chapter in this branch
                    await deactivate_previous_chapter_versions(chapter.story_id, 1, main_branch_id)
                    
                    chapter_insert_data = {
                        "story_id": chapter.story_id,  # Use the story_id from the request
                        "branch_id": main_branch_id,
                        "chapter_number": 1,
                        "title": f"Chapter 1",
                        "content": chapter_content,
                        "word_count": len(chapter_content.split()),
                        "version_number": next_version_number,  # Add proper versioning
                        "is_active": True,  # Mark this version as active
                    }
                    # Remove None fields (story_id may not be present)
                    chapter_insert_data = {k: v for k, v in chapter_insert_data.items() if v is not None}
                    chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
                    chapter_id = chapter_response.data[0]["id"]
                    # --- GENERATE AND SAVE CHAPTER 1 SUMMARY ---
                    
                    try:
                        from chapter_summary import generate_chapter_summary
                        story_outline = result.get("story_outline", "") if isinstance(result, dict) else ""

                        summary_result = generate_chapter_summary(
                            chapter_content=chapter_content,
                            chapter_number=1,
                            story_context=story_outline,
                            story_title=story.get("story_title", "Untitled Story") if 'story' in locals() else "Untitled Story"
                        )

                        if summary_result["success"]:
                            summary_text = summary_result["summary"]
                            
                            update_response = supabase.table("Chapters").update({"summary": summary_text}).eq("id", chapter_id).execute()
                            
                            # Verify the update worked
                            verify_response = supabase.table("Chapters").select("summary").eq("id", chapter_id).execute()
                            if verify_response.data and verify_response.data[0].get("summary"):
                                logger.info(f"✅ Chapter 1 summary saved and verified in database")
                            else:
                                logger.error(f"❌ Chapter 1 summary update may have failed")
                        else:
                            logger.error(f"❌ Failed to generate summary for Chapter 1")
                    except Exception as summary_error:
                        import traceback
                    # Save choices
                    logger.info(f"💾 Saving Chapter 1 choices to story_choices table...")
                    # Get main branch ID for this story
                    main_branch_id = await get_main_branch_id(chapter.story_id)
                    
                    # Save choices using helper function
                    if choices and user:
                        await save_choices_for_chapter(
                            story_id=chapter.story_id,
                            chapter_id=chapter_id,
                            chapter_number=1,
                            choices=choices,
                            user_id=user.id,
                            branch_id=main_branch_id
                        )
            except Exception as db_error:
                logger.error(f"❌ Failed to save Chapter 1 or choices: {str(db_error)}")
                # Do not raise, allow generation to succeed even if save fails

            return {
                "chapter_1": chapter_content,  # Frontend expects this field name
                "chapter": chapter_content,    # Keep for compatibility
                "choices": choices,            # New: automatic choices
                "metadata": {
                    "chapter_number": chapter.chapter_number,
                    "word_count": len(chapter_content.split()),
                    "character_count": len(chapter_content),
                    "choices_count": len(choices),
                    "generation_success": True
                }
            }
        elif isinstance(result, dict):
            # Handle error case with dictionary response
            error_msg = result.get("chapter_content", result.get("error", "Generation failed"))
            logger.error(f"❌ Chapter generation failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        else:
            # Handle unexpected response type
            logger.error(f"❌ Unexpected result type: {type(result)}")
            logger.error(f"❌ Result content: {str(result)[:500]}")
            raise HTTPException(status_code=500, detail=f"Unexpected response format: {type(result)}")
            
    except Exception as e:
        logger.error(f"❌ Chapter generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class JsonChapterInput(BaseModel):
    """Input model for generating Chapters from JSON outline."""
    outline_json: Dict[str, Any] = Field(..., description="JSON outline data")
    chapter_number: int = Field(default=1, ge=1, description="Chapter number to generate")

@app.post("/lc_generate_chapter_from_json")
async def generate_chapter_from_json_endpoint(chapter: JsonChapterInput):
    """Generate story chapter specifically from JSON outline data."""
    logger.info(f"📖 Starting Chapter {chapter.chapter_number} generation from JSON outline...")
    
    # Log the JSON outline we received
    logger.info("📥 RECEIVED JSON OUTLINE FOR CHAPTER GENERATION:")
    logger.info(f"   📊 Keys: {list(chapter.outline_json.keys())}")
    logger.info(f"   📚 Chapters: {len(chapter.outline_json.get('Chapters', []))}")
    
    try:
        from lc_book_generator import BookStoryGenerator
        generator = BookStoryGenerator()
        
        logger.info("🚀 Invoking BookStoryGenerator with JSON data...")
        
        # Use the JSON-specific method
        result = generator.generate_chapter_from_json(chapter.outline_json, chapter.chapter_number)
        
        logger.info(f"✅ Chapter {chapter.chapter_number} generation from JSON completed!")
        
        # Handle new JSON response structure
        if result.get("success"):
            chapter_content = result.get("chapter_content", "")
            choices = result.get("choices", [])
            
            logger.info(f"📊 Generated: {len(chapter_content)} chars, {len(choices)} choices")
            
            # Extract chapter metadata from JSON for response
            Chapters = chapter.outline_json.get("Chapters", [])
            target_chapter = next(
                (ch for ch in Chapters if ch.get("chapter_number") == chapter.chapter_number),
                {}
            )
            
            return {
                "chapter": chapter_content,
                "choices": choices,  # New: automatic choices
                "metadata": {
                    "chapter_number": chapter.chapter_number,
                    "chapter_title": target_chapter.get("chapter_title", f"Chapter {chapter.chapter_number}"),
                    "word_count": len(chapter_content.split()),
                    "character_count": len(chapter_content),
                    "choices_count": len(choices),
                    "estimated_word_count": target_chapter.get("estimated_word_count", 0),
                    "generation_success": True,
                    "source": "json_outline"
                },
                "chapter_outline_data": target_chapter
            }
        else:
            # Handle error case
            error_msg = result.get("chapter_content", "Generation failed")
            logger.error(f"❌ Chapter generation failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except Exception as e:
        logger.error(f"❌ Chapter generation from JSON failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stories/save")
async def save_story_endpoint(
    story_data: StorySaveInput,
    background_tasks: BackgroundTasks,
    user = Depends(get_authenticated_user)
):
    """Save story with complete JSON metadata parsing and database storage."""
    logger.info(f"Saving story with JSON parsing: {story_data.story_title}")
    
    try:
        # Extract ALL metadata from outline_json if provided
        extracted_metadata = {}
        chapter_1_metadata = {}
        
        if story_data.outline_json:
            logger.info("Parsing JSON outline for complete metadata extraction...")
            json_data = story_data.outline_json
            
            # Extract story-level metadata from JSON
            extracted_metadata = {
                "book_title": json_data.get("book_title", story_data.story_title),
                "genre": json_data.get("genre", story_data.genre),
                "theme": json_data.get("theme", story_data.theme),
                "style": json_data.get("style", story_data.style),
                "description": json_data.get("description", ""),
                "language": json_data.get("language", story_data.language or "English"),
                "tags": json_data.get("tags", story_data.tags or []),
                "estimated_total_chapters": json_data.get("estimated_total_chapters", story_data.estimated_total_chapters or 1),
                "main_characters": json_data.get("main_characters", story_data.main_characters or []),
                "character_arcs_summary": json_data.get("character_arcs_summary", ""),
                "key_locations": json_data.get("key_locations", story_data.key_locations or []),
                "conflict": json_data.get("conflict", ""),
                "tone_keywords": json_data.get("tone_keywords", story_data.tone_keywords or []),
                "writing_guidelines": json_data.get("writing_guidelines", ""),
                "Chapters": json_data.get("Chapters", [])
            }
            
            # Calculate total estimated words from Chapters
            total_words = sum(
                chapter.get("estimated_word_count", 0) 
                for chapter in extracted_metadata["Chapters"]
            )
            extracted_metadata["total_estimated_words"] = total_words or story_data.total_estimated_words
            
            # Extract Chapter 1 specific metadata
            if extracted_metadata["Chapters"]:
                chapter_1_data = next(
                    (ch for ch in extracted_metadata["Chapters"] if ch.get("chapter_number") == 1),
                    {}
                )
                if chapter_1_data:
                    chapter_1_metadata = {
                        "title": chapter_1_data.get("chapter_title", "Chapter 1"),
                        "summary": chapter_1_data.get("chapter_summary", "First chapter"),
                        "estimated_word_count": chapter_1_data.get("estimated_word_count", 0),
                        "cliffhanger_cta": chapter_1_data.get("cliffhanger_cta", "")
                    }
            
            logger.info(f"Extracted metadata: {list(extracted_metadata.keys())}")
            
            # DEBUG: Log specific theme and style values
            logger.info(f"   JSON theme: {json_data.get('theme', 'NOT_FOUND')}")
            logger.info(f"   JSON style: {json_data.get('style', 'NOT_FOUND')}")
            logger.info(f"   story_data.theme: {story_data.theme}")
            logger.info(f"   story_data.style: {story_data.style}")
            logger.info(f"   extracted_metadata theme: {extracted_metadata.get('theme', 'NOT_FOUND')}")
            logger.info(f"   extracted_metadata style: {extracted_metadata.get('style', 'NOT_FOUND')}")
        else:
            # Fallback to provided data if no JSON
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
                "tone_keywords": story_data.tone_keywords
            }
        
        # Prepare basic story data that should exist in all databases
        story_insert_data = {
            "user_id": user.id,
            "story_title": extracted_metadata["book_title"],
            "story_outline": story_data.story_outline,
            "total_chapters": extracted_metadata["estimated_total_chapters"],
            "current_chapter": 1,
        }
        
        # Add optional metadata fields only if they have values
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
        
        # Only add fields that have non-empty values
        for field, value in optional_fields.items():
            if value is not None and value != [] and value != "":
                story_insert_data[field] = value
        
        # Remove None values to avoid database errors
        story_insert_data = {k: v for k, v in story_insert_data.items() if v is not None}
        
        logger.info(f"Attempting to insert story with fields: {list(story_insert_data.keys())}")
        
        # DEBUG: Show actual values being inserted
        logger.info(f"🔍 FINAL VALUES BEING INSERTED:")
        for key, value in story_insert_data.items():
            if key in ['theme', 'style', 'genre']:
                logger.info(f"   {key}: '{value}' (type: {type(value)})")
        
        # Try to insert with all fields, fallback to minimal if schema issues
        try:
            story_response = supabase.table("Stories").insert(story_insert_data).execute()
            story_id = story_response.data[0]["id"]
            logger.info(f"Story inserted successfully with full metadata: {story_id}")
        except Exception as db_error:
            logger.warning(f"Full metadata insert failed: {db_error}")
            logger.info("Falling back to minimal story insert...")
            
            # Fallback: Try with minimal required fields only
            minimal_story_data = {
                "user_id": user.id,
                "story_title": extracted_metadata["book_title"],
                "story_outline": story_data.story_outline,
                "total_chapters": extracted_metadata["estimated_total_chapters"],
                "current_chapter": 1,
            }
            
            try:
                story_response = supabase.table("Stories").insert(minimal_story_data).execute()
                story_id = story_response.data[0]["id"]
                logger.info(f"Story inserted successfully with minimal data: {story_id}")
            except Exception as minimal_error:
                logger.error(f"Even minimal story insert failed: {minimal_error}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Database schema mismatch. Please check your Stories table columns. Error: {str(minimal_error)}"
                )
        
        # Calculate chapter metadata
        word_count = len(story_data.chapter_1_content.split())
        reading_time = max(1, word_count // 200)  # 200 words per minute
        
        # Generate summary for Chapter 1 using the new chapter_summary module
        logger.info(f"🤖 CHAPTER 1 SUMMARY: Starting summary generation for Chapter 1...")
        
        # Build basic story context for Chapter 1
        story_context = f"STORY: {extracted_metadata['book_title']}\nGENRE: {extracted_metadata.get('genre', '')}\nTHEME: {extracted_metadata.get('theme', '')}\n\nSTORY OUTLINE:\n{story_data.story_outline}"
        
        logger.info(f"📄 CHAPTER 1 SUMMARY: Story context built: {len(story_context)} chars")
        
        # Generate summary
        logger.info(f"🎯 CHAPTER 1 SUMMARY: Calling LLM...")
        summary_result = generate_chapter_summary(
            chapter_content=story_data.chapter_1_content,
            chapter_number=1,
            story_context=story_context,
            story_title=extracted_metadata["book_title"]
        )
        
        logger.info(f"🤖 CHAPTER 1 SUMMARY: LLM Response Status: {summary_result['success']}")
        
        chapter_1_summary = ""
        if summary_result["success"]:
            chapter_1_summary = summary_result["summary"]
            logger.info(f"✅ CHAPTER 1 SUMMARY: Generated successfully!")
            logger.info(f"📝 CHAPTER 1 SUMMARY: Length: {len(chapter_1_summary)} chars")
            logger.info(f"📝 CHAPTER 1 SUMMARY: Preview: {chapter_1_summary[:100]}...")
        else:
            logger.warning(f"⚠️ CHAPTER 1 SUMMARY: Generation failed: {summary_result['error']}")
            chapter_1_summary = chapter_1_metadata.get("summary", "First chapter")
        
        # Prepare chapter data WITH summary
        logger.info(f"💾 CHAPTER 1 DATABASE: Preparing insert with summary...")
        
        # Get the next version number for this chapter
        next_version_number = await get_next_chapter_version_number(story_id, 1)
        
        # Deactivate previous versions of this chapter
        await deactivate_previous_chapter_versions(story_id, 1)
        
        chapter_insert_data = {
            "story_id": story_id,
            "chapter_number": 1,
            "title": chapter_1_metadata.get("title", "Chapter 1"),
            "content": story_data.chapter_1_content,
            "summary": chapter_1_summary,  # Summary is now included from generation above
            "version_number": next_version_number,  # Add proper versioning
            "is_active": True,  # Mark this version as active
        }
        
        logger.info(f"📋 CHAPTER 1 DATABASE: Insert data keys: {list(chapter_insert_data.keys())}")
        logger.info(f"🔍 CHAPTER 1 DATABASE: Summary field in insert: {bool(chapter_insert_data.get('summary'))}")
        logger.info(f"📝 CHAPTER 1 DATABASE: Summary length: {len(chapter_insert_data.get('summary', ''))} chars")
        logger.info(f"📝 CHAPTER 1 DATABASE: Summary preview: {chapter_insert_data.get('summary', '')[:100]}...")
        
        # Add optional chapter fields - only include fields that exist in database schema
        optional_chapter_fields = {
            # Use the generated summary instead of metadata fallback
            # "summary" is already included in chapter_insert_data above
            "word_count": word_count,  # This exists in your DB schema
            "cliffhanger_cta": chapter_1_metadata.get("cliffhanger_cta", ""),  # This exists in your DB schema
            # Note: reading_time_minutes removed - doesn't exist in database schema
        }
        
        # Add any additional metadata from JSON if available
        if story_data.outline_json and "Chapters" in story_data.outline_json:
            chapter_1_full = next(
                (ch for ch in story_data.outline_json["Chapters"] if ch.get("chapter_number") == 1),
                {}
            )
            if chapter_1_full:
                # Only add fields that exist in database schema
                # Removed: key_events, character_appearances, location, mood (don't exist in schema)
                pass  # For now, don't add any additional JSON fields until we verify they exist
        
        # Only add optional fields that have values
        for field, value in optional_chapter_fields.items():
            if value is not None and value != "" and value != []:
                chapter_insert_data[field] = value
        
        logger.info(f"🔧 CHAPTER 1 DATABASE: Final insert data fields: {list(chapter_insert_data.keys())}")
        
        # Try to insert chapter with fallback handling
        logger.info(f"🎯 CHAPTER 1 DATABASE: Executing INSERT...")
        try:
            chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
            
            logger.info(f"📊 CHAPTER 1 DATABASE: Response: {chapter_response}")
            logger.info(f"📊 CHAPTER 1 DATABASE: Response data: {chapter_response.data}")
            
            if not chapter_response.data:
                logger.error(f"❌ CHAPTER 1 DATABASE: Insert returned no data")
                chapter_id = None
            else:
                chapter_id = chapter_response.data[0]["id"]
                saved_chapter = chapter_response.data[0]
                
                logger.info(f"✅ CHAPTER 1 DATABASE: Chapter inserted with metadata: {chapter_id}")
                logger.info(f"🔍 CHAPTER 1 DATABASE: Saved summary field: {saved_chapter.get('summary', 'NOT_FOUND')}")
                
                # Verification query
                logger.info(f"🔍 CHAPTER 1 DATABASE: Verifying saved chapter...")
                verify_response = supabase.table("Chapters").select("id, summary").eq("id", chapter_id).execute()
                
                if verify_response.data:
                    verified_summary = verify_response.data[0].get("summary")
                    logger.info(f"✅ CHAPTER 1 VERIFICATION: Summary in DB: {bool(verified_summary)}")
                    if verified_summary:
                        logger.info(f"📝 CHAPTER 1 VERIFICATION: Summary length: {len(verified_summary)} chars")
                        logger.info(f"📝 CHAPTER 1 VERIFICATION: Summary preview: {verified_summary[:100]}...")
                    else:
                        logger.error(f"❌ CHAPTER 1 VERIFICATION: Summary is NULL in database!")
                else:
                    logger.error(f"❌ CHAPTER 1 VERIFICATION: Could not query saved chapter!")
                    
        except Exception as chapter_error:
            logger.error(f"❌ CHAPTER 1 DATABASE: Full metadata insert failed: {chapter_error}")
            logger.error(f"🔍 CHAPTER 1 DATABASE: Error type: {type(chapter_error)}")
            logger.info("🔄 CHAPTER 1 DATABASE: Falling back to minimal chapter insert...")
            
            # Fallback: minimal chapter data WITH summary if possible
            minimal_chapter_data = {
                "story_id": story_id,
                "chapter_number": 1,
                "title": chapter_1_metadata.get("title", "Chapter 1"),
                "content": story_data.chapter_1_content,
                "summary": chapter_1_summary,  # Include summary in fallback too!
            }
            
            logger.info(f"🔧 CHAPTER 1 FALLBACK: Minimal data keys: {list(minimal_chapter_data.keys())}")
            
            try:
                chapter_response = supabase.table("Chapters").insert(minimal_chapter_data).execute()
                chapter_id = chapter_response.data[0]["id"]
                logger.info(f"✅ CHAPTER 1 FALLBACK: Chapter inserted with minimal data: {chapter_id}")
            except Exception as minimal_chapter_error:
                logger.error(f"❌ CHAPTER 1 FALLBACK: Even minimal chapter insert failed: {minimal_chapter_error}")
                logger.error(f"🔍 CHAPTER 1 FALLBACK: Error type: {type(minimal_chapter_error)}")
                # Don't fail the entire save if chapter insert fails
                chapter_id = None
                logger.warning("⚠️ CHAPTER 1 FALLBACK: Story saved but Chapter 1 could not be inserted due to schema issues")
        
        # Save Chapter 1 choices if provided
        choices_saved_count = 0
        if story_data.chapter_1_choices and chapter_id:
            try:
                # Use helper function to save choices consistently
                saved_choices = await save_choices_for_chapter(
                    story_id=story_id,
                    chapter_id=chapter_id,
                    chapter_number=1,
                    choices=story_data.chapter_1_choices,
                    user_id=user.id
                )
                choices_saved_count = len(saved_choices)
                    
            except Exception as e:
                logger.error(f"❌ CHOICES: Error saving choices to database: {e}")
                choices_saved_count = 0
                # Continue anyway - don't break the user experience
        
        # Generate embeddings in background for optimization
        background_tasks.add_task(
            embedding_service.create_embeddings_async,
            story_id,
            False
        )
        
        # Invalidate user cache
        background_tasks.add_task(
            story_service.invalidate_user_cache,
            user.id
        )
        
        # Prepare detailed response
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
                "Chapters_in_outline": len(extracted_metadata.get("Chapters", []))
            },
            "json_parsing_success": bool(story_data.outline_json)
        }
        
    except Exception as e:
        logger.error(f"Story saving with JSON parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save story with metadata: {str(e)}")

# Performance monitoring endpoint
@app.get("/admin/performance")
async def get_performance_stats(user = Depends(get_authenticated_user)):
    """Get detailed performance statistics."""
    try:
        story_stats = await story_service.get_service_stats()
        embedding_stats = await embedding_service.get_service_stats()
        
        return {
            "story_service": story_stats,
            "embedding_service": embedding_stats,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Performance stats failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance stats"
        )

# Cache management endpoint
@app.post("/admin/cache/clear")
async def clear_cache(pattern: str = "", user = Depends(get_authenticated_user)):
    """Clear cache by pattern."""
    try:
        if pattern:
            await cache_service.clear_pattern(pattern)
            return {"message": f"Cleared cache pattern: {pattern}"}
        else:
            # Clear all memory cache
            cache_service._memory_cache.clear()
            return {"message": "Cleared memory cache"}
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )

# Test endpoint for JSON parsing flow
@app.post("/test/json_flow")
async def test_json_parsing_flow(test_idea: str = "A revenge story about a young warrior seeking justice"):
    """Test the complete JSON generation and parsing flow (no auth required)."""
    try:
        from lc_book_generator_prompt import generate_book_outline_json
        
        logger.info(f"Testing JSON flow with idea: {test_idea}")
        
        # Step 1: Generate JSON outline
        result = generate_book_outline_json(test_idea)
        
        if not result["success"]:
            return {
                "step": "json_generation",
                "success": False,
                "error": result["error"],
                "raw_response": result.get("raw_response", "")
            }
        
        outline_json = result["outline_json"]
        metadata = result["metadata"]
        
        # Step 2: Test metadata extraction
        extracted_fields = {
            "title": outline_json.get("book_title"),
            "genre": outline_json.get("genre"),
            "theme": outline_json.get("theme"),
            "style": outline_json.get("style"),
            "description": outline_json.get("description"),
            "language": outline_json.get("language"),
            "tags": outline_json.get("tags", []),
            "estimated_total_chapters": outline_json.get("estimated_total_chapters"),
            "main_characters": outline_json.get("main_characters", []),
            "key_locations": outline_json.get("key_locations", []),
            "tone_keywords": outline_json.get("tone_keywords", []),
            "Chapters": outline_json.get("Chapters", []),
            "writing_guidelines": outline_json.get("writing_guidelines"),
            "conflict": outline_json.get("conflict")
        }
        
        # Step 3: Analyze what we extracted
        analysis = {
            "total_fields_extracted": len([v for v in extracted_fields.values() if v]),
            "has_characters": len(extracted_fields["main_characters"]) > 0,
            "has_locations": len(extracted_fields["key_locations"]) > 0,
            "has_Chapters": len(extracted_fields["Chapters"]) > 0,
            "has_tags": len(extracted_fields["tags"]) > 0,
            "estimated_words": sum(
                ch.get("estimated_word_count", 0) 
                for ch in extracted_fields["Chapters"]
            ),
            "chapter_count": len(extracted_fields["Chapters"])
        }
        
        return {
            "step": "complete",
            "success": True,
            "test_idea": test_idea,
            "json_generation_success": True,
            "outline_json": outline_json,
            "extracted_metadata": extracted_fields,
            "analysis": analysis,
            "ready_for_database": {
                "title": bool(extracted_fields["title"]),
                "genre": bool(extracted_fields["genre"]),
                "has_structured_data": analysis["has_characters"] and analysis["has_Chapters"],
                "can_save_to_db": bool(extracted_fields["title"] and extracted_fields["genre"])
            },
            "next_steps": [
                "Use this JSON in /Stories/save endpoint",
                "All metadata will be automatically extracted and saved",
                "Check your database for the saved structured data"
            ]
        }
        
    except Exception as e:
        logger.error(f"JSON flow test failed: {e}")
        return {
            "step": "error",
            "success": False,
            "error": str(e),
                         "test_idea": test_idea
         }

# Simple test endpoint to see formatted text output
@app.post("/test/formatted_outline")
async def test_formatted_outline(idea: str = "A detective solving mysteries in Victorian London"):
    """Test formatted text output for frontend display (no auth required)."""
    try:
        from lc_book_generator_prompt import generate_book_outline_json
        
        logger.info(f"Testing formatted outline for: {idea}")
        
        # Generate outline
        result = generate_book_outline_json(idea)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
                "formatted_text": f"❌ Failed to generate outline: {result['error']}"
            }
        
        return {
            "success": True,
            "idea": idea,
            "formatted_text": result["formatted_text"],  # This is what the frontend will display
            "json_available": bool(result["outline_json"]),
            "characters_count": len(result["outline_json"].get("main_characters", [])),
            "Chapters_count": len(result["outline_json"].get("Chapters", [])),
            "note": "This formatted_text is what users will see in the frontend"
        }
        
    except Exception as e:
        logger.error(f"Formatted outline test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "formatted_text": f"❌ Error: {str(e)}"
        }

@app.post("/test/complete_json_to_chapter_flow")
async def test_complete_json_to_chapter_flow(idea: str = "A space explorer discovers a mysterious alien artifact"):
    """Test the complete flow: Idea → JSON Outline → Chapter 1 Generation (no auth required)."""
    logger.info(f"🚀 Testing COMPLETE JSON to Chapter 1 flow with idea: {idea}")
    
    try:
        from lc_book_generator_prompt import generate_book_outline_json
        from lc_book_generator import BookStoryGenerator
        
        # Step 1: Generate JSON outline from idea
        logger.info("📝 Step 1: Generating JSON outline...")
        outline_result = generate_book_outline_json(idea)
        
        if not outline_result["success"]:
            return {
                "step": "json_generation_failed",
                "success": False,
                "error": outline_result["error"],
                "idea": idea
            }
        
        outline_json = outline_result["outline_json"]
        logger.info("✅ Step 1 completed: JSON outline generated successfully")
        
        # Step 2: Generate Chapter 1 from JSON outline
        logger.info("📖 Step 2: Generating Chapter 1 from JSON outline...")
        generator = BookStoryGenerator()
        
        chapter_1_content = generator.generate_chapter_from_json(outline_json, 1)
        
        if chapter_1_content.startswith("❌"):
            return {
                "step": "chapter_generation_failed",
                "success": False,
                "error": chapter_1_content,
                "outline_json": outline_json,
                "idea": idea
            }
        
        logger.info("✅ Step 2 completed: Chapter 1 generated successfully")
        
        # Step 3: Extract metadata for analysis
        Chapters = outline_json.get("Chapters", [])
        chapter_1_data = next(
            (ch for ch in Chapters if ch.get("chapter_number") == 1),
            {}
        )
        
        # Calculate statistics
        actual_word_count = len(chapter_1_content.split())
        estimated_word_count = chapter_1_data.get("estimated_word_count", 0)
        
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   Title: {outline_json.get('book_title', 'N/A')}")
        logger.info(f"   Genre: {outline_json.get('genre', 'N/A')}")
        logger.info(f"   Chapter 1 Title: {chapter_1_data.get('chapter_title', 'N/A')}")
        logger.info(f"   Estimated Words: {estimated_word_count}")
        logger.info(f"   Actual Words: {actual_word_count}")
        logger.info(f"   Characters: {len(outline_json.get('main_characters', []))}")
        logger.info(f"   Locations: {len(outline_json.get('key_locations', []))}")
        
        return {
            "step": "complete_success",
            "success": True,
            "idea": idea,
            
            # JSON Outline Results
            "json_outline": outline_json,
            "formatted_outline": outline_result["formatted_text"],
            
            # Chapter 1 Results
            "chapter_1_content": chapter_1_content,
            "chapter_1_metadata": chapter_1_data,
            
            # Statistics and Analysis
            "analysis": {
                "book_title": outline_json.get("book_title", ""),
                "genre": outline_json.get("genre", ""),
                "chapter_1_title": chapter_1_data.get("chapter_title", "Chapter 1"),
                "estimated_word_count": estimated_word_count,
                "actual_word_count": actual_word_count,
                "word_count_accuracy": f"{((actual_word_count / max(estimated_word_count, 1)) * 100):.1f}%" if estimated_word_count > 0 else "N/A",
                "characters_created": len(outline_json.get("main_characters", [])),
                "locations_created": len(outline_json.get("key_locations", [])),
                "total_chapters_planned": len(Chapters),
                "total_estimated_book_words": sum(ch.get("estimated_word_count", 0) for ch in Chapters)
            },
            
            # Next Steps for Implementation
            "implementation_ready": {
                "has_complete_json": bool(outline_json),
                "has_chapter_content": bool(chapter_1_content and not chapter_1_content.startswith("❌")),
                "ready_for_database": True,
                "can_continue_to_chapter_2": bool(len(Chapters) > 1)
            },
            
            "usage_instructions": {
                "save_to_database": "Use the /Stories/save endpoint with this data",
                "generate_more_Chapters": "Use /lc_generate_chapter_from_json with chapter_number=2,3,etc",
                "frontend_display": "Use the 'formatted_outline' for user display",
                "database_storage": "Use the 'json_outline' for metadata storage"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Complete flow test failed: {e}")
        return {
            "step": "error",
            "success": False,
            "error": str(e),
            "idea": idea,
            "traceback": str(e)
        }

@app.post("/test/auto_save_outline")
async def test_auto_save_outline_flow(idea: str = "A brave knight embarks on a quest to save the kingdom from an ancient curse"):
    """Test the auto-save outline functionality with authentication bypass."""
    try:
        # Mock user for testing
        from types import SimpleNamespace
        mock_user = SimpleNamespace(id=999, email="test@bookology.com")
        
        # Test the outline generation with auto-save
        from lc_book_generator_prompt import generate_book_outline_json
        
        logger.info(f"🧪 Testing auto-save outline for idea: {idea[:50]}...")
        
        # Generate JSON outline
        result = generate_book_outline_json(idea)
        
        if not result["success"]:
            return {"success": False, "error": f"Outline generation failed: {result['error']}"}
        
        # Extract data
        metadata = result["metadata"]
        outline_json = result["outline_json"]
        formatted_text = result["formatted_text"]
        usage_metrics = result.get("usage_metrics", {})  # LLM usage metrics
        
        # Test database save
        story_id = None
        database_save_success = False
        
        try:
            logger.info("🧪 Testing database auto-save...")
            
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
                # Note: tone_keywords excluded as it doesn't exist in database schema
                
                # LLM Usage Metrics
                "temperature_used": usage_metrics.get("temperature_used"),
                "token_count_total": usage_metrics.get("estimated_total_tokens"),
                "word_count_total": usage_metrics.get("total_word_count"),
                "model_used": usage_metrics.get("model_used"),
            }
            
            # Remove None values
            story_data = {k: v for k, v in story_data.items() if v is not None and v != [] and v != ""}
            
            logger.info(f"🧪 Saving test outline with fields: {list(story_data.keys())}")
            
            # Insert to database
            story_response = supabase.table("Stories").insert(story_data).execute()
            story_id = story_response.data[0]["id"]
            database_save_success = True
            
            logger.info(f"✅ Test outline auto-saved with story_id: {story_id}")
            
        except Exception as db_error:
            logger.warning(f"❌ Test database save failed: {db_error}")
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
                "locations_count": len(metadata["key_locations"])
            },
            "database_fields_saved": list(story_data.keys()) if database_save_success else [],
            "message": "✅ Auto-save outline test completed! JSON outline was generated and saved to database automatically." if database_save_success else "⚠️ Outline generated but database save failed."
        }
        
    except Exception as e:
        logger.error(f"❌ Auto-save outline test failed: {e}")
        return {"success": False, "error": str(e)}

class ChaptersaveInput(BaseModel):
    story_id: int
    chapter_number: int
    content: str
    title: Optional[str] = None
    # Optional token metrics (will be calculated if not provided)
    token_count_prompt: Optional[int] = None
    token_count_completion: Optional[int] = None
    token_count_total: Optional[int] = None
    temperature_used: Optional[float] = None

class GenerateNextChapterInput(BaseModel):
    story_id: int
    chapter_number: int
    story_outline: str

@app.post("/save_chapter_with_summary")
async def save_chapter_with_summary_endpoint(
    chapter_data: ChaptersaveInput,
    background_tasks: BackgroundTasks,
    user = Depends(get_authenticated_user)
):
    """
    Save a chapter and automatically generate its summary for story continuity.
    This endpoint does 3 things:
    1. Saves the chapter to the database
    2. Generates a summary using LLM
    3. Updates the chapter with the summary
    """
    try:
        logger.info(f"🚀 STARTING Chapter Save Process for Chapter {chapter_data.chapter_number}, Story {chapter_data.story_id}")
        logger.info(f"📖 User ID: {user.id}")
        
        # Verify story belongs to user
        logger.info(f"🔍 STEP 1: Verifying story ownership...")
        story_response = supabase.table("Stories").select("*").eq("id", chapter_data.story_id).eq("user_id", user.id).execute()
        
        logger.info(f"📊 Database Query Response: found {len(story_response.data) if story_response.data else 0} Stories")
        
        if not story_response.data:
            logger.error(f"❌ AUTHORIZATION FAILED: Story {chapter_data.story_id} not found for user {user.id}")
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        story_title = story.get("story_title", "Untitled Story")
        story_outline = story.get("story_outline", "")
        
        logger.info(f"✅ STEP 1 COMPLETE: Story found: '{story_title}'")
        logger.info(f"📚 Story outline length: {len(story_outline)} chars")
        
        # FIRST: Generate summary BEFORE saving to database
        logger.info(f"🤖 STEP 2: Starting summary generation for Chapter {chapter_data.chapter_number}...")
        
        # Get previous Chapters for context (if any)
        logger.info(f"🔍 STEP 2a: Fetching previous Chapters for context...")
        previous_Chapters_response = supabase.table("Chapters").select("content, summary").eq("story_id", chapter_data.story_id).lte("chapter_number", chapter_data.chapter_number).order("chapter_number").execute()
        
        logger.info(f"📊 Previous Chapters found: {len(previous_Chapters_response.data) if previous_Chapters_response.data else 0}")
        
        previous_summaries = []
        if previous_Chapters_response.data:
            for i, prev_chapter in enumerate(previous_Chapters_response.data):
                if prev_chapter.get("summary"):
                    previous_summaries.append(prev_chapter["summary"])
                    logger.info(f"📝 Previous Chapter {i+1}: Has summary ({len(prev_chapter['summary'])} chars)")
                else:
                    # If no summary exists, create a quick one from content
                    prev_content = prev_chapter.get("content", "")[:500] + "..."  # First 500 chars
                    previous_summaries.append(f"Previous chapter content: {prev_content}")
                    logger.warning(f"⚠️ Previous Chapter {i+1}: NO SUMMARY FOUND, using content truncation")
        
        logger.info(f"📋 Built context with {len(previous_summaries)} previous summaries")
        
        # Build story context
        logger.info(f"🔧 STEP 2b: Building story context...")
        story_context = build_story_context_for_next_chapter(
            story_outline=story_outline,
            previous_chapter_summaries=previous_summaries,
            current_chapter_number=chapter_data.chapter_number
        )
        
        logger.info(f"📄 Story context built: {len(story_context)} chars")
        
        # Generate summary
        logger.info(f"🎯 STEP 2c: Calling LLM to generate summary...")
        summary_result = generate_chapter_summary(
            chapter_content=chapter_data.content,
            chapter_number=chapter_data.chapter_number,
            story_context=story_context,
            story_title=story_title
        )
        
        logger.info(f"🤖 LLM Response Status: {summary_result['success']}")
        
        summary_text = ""
        if summary_result["success"]:
            summary_text = summary_result["summary"]
            logger.info(f"✅ STEP 2 COMPLETE: Summary generated successfully!")
            logger.info(f"📝 Summary length: {len(summary_text)} chars")
            logger.info(f"📝 Summary preview: {summary_text[:100]}...")
            logger.info(f"📊 Usage metrics: {summary_result.get('usage_metrics', {})}")
        else:
            logger.error(f"❌ STEP 2 FAILED: Summary generation failed: {summary_result['error']}")
            summary_text = f"Summary generation failed: {summary_result['error']}"
        
        # Calculate chapter metadata
        word_count = len(chapter_data.content.split())
        reading_time = max(1, word_count // 200)  # 200 words per minute
        
        logger.info(f"📊 Chapter metadata: {word_count} words, {reading_time} min reading time")
        
        # Calculate token metrics for the summary generation (if not provided)
        summary_token_metrics = summary_result.get("usage_metrics", {})
        
        # Get the next version number for this chapter
        next_version_number = await get_next_chapter_version_number(chapter_data.story_id, chapter_data.chapter_number)
        
        # Deactivate previous versions of this chapter
        await deactivate_previous_chapter_versions(chapter_data.story_id, chapter_data.chapter_number)
        
        # NOW: Save chapter WITH the generated summary AND token metrics in one operation
        chapter_insert_data = {
            "story_id": chapter_data.story_id,
            "chapter_number": chapter_data.chapter_number,
            "title": chapter_data.title or f"Chapter {chapter_data.chapter_number}",
            "content": chapter_data.content,
            "summary": summary_text,  # Include the summary in the initial insert
            "word_count": word_count,
            "version_number": next_version_number,  # Add proper versioning
            "is_active": True,  # Mark this version as active
            # Token tracking fields
            "token_count_prompt": chapter_data.token_count_prompt or summary_token_metrics.get("estimated_input_tokens", 0),
            "token_count_completion": chapter_data.token_count_completion or summary_token_metrics.get("estimated_output_tokens", 0),
            "token_count_total": chapter_data.token_count_total or summary_token_metrics.get("estimated_total_tokens", 0),
            "temperature_used": chapter_data.temperature_used or summary_token_metrics.get("temperature_used", 0.3),
        }
        
        logger.info(f"💾 STEP 3: Preparing database insert with summary AND token metrics...")
        logger.info(f"📋 Insert data keys: {list(chapter_insert_data.keys())}")
        logger.info(f"🔍 Summary field in insert data: {bool(chapter_insert_data.get('summary'))}")
        logger.info(f"📝 Summary field length: {len(chapter_insert_data.get('summary', ''))} chars")
        logger.info(f"📝 Summary field preview: {chapter_insert_data.get('summary', '')[:100]}...")
        logger.info(f"📊 Token metrics: prompt={chapter_insert_data.get('token_count_prompt', 0)}, completion={chapter_insert_data.get('token_count_completion', 0)}, total={chapter_insert_data.get('token_count_total', 0)}")
        logger.info(f"🌡️ Temperature used: {chapter_insert_data.get('temperature_used', 'N/A')}")
        
        # Insert chapter with summary in one operation
        logger.info(f"🎯 STEP 3a: Executing database INSERT...")
        
        try:
            chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
            
            logger.info(f"📊 Database response: {chapter_response}")
            logger.info(f"📊 Response data: {chapter_response.data}")
            
            if not chapter_response.data:
                logger.error(f"❌ DATABASE ERROR: Insert returned no data")
                raise HTTPException(status_code=500, detail="Failed to save chapter with summary")
            
            chapter_id = chapter_response.data[0]["id"]
            saved_chapter = chapter_response.data[0]
            
            logger.info(f"✅ STEP 3a COMPLETE: Chapter saved! ID: {chapter_id}")
            logger.info(f"🔍 VERIFICATION: Checking saved summary...")
            logger.info(f"📝 Saved summary field: {saved_chapter.get('summary', 'NOT_FOUND')}")
            
            # Additional verification - query the database to confirm
            logger.info(f"🔍 STEP 3b: Verifying saved chapter in database...")
            verify_response = supabase.table("Chapters").select("id, summary").eq("id", chapter_id).execute()
            
            if verify_response.data:
                verified_summary = verify_response.data[0].get("summary")
                logger.info(f"✅ VERIFICATION: Chapter {chapter_id} summary in DB: {bool(verified_summary)}")
                if verified_summary:
                    logger.info(f"📝 Verified summary length: {len(verified_summary)} chars")
                    logger.info(f"📝 Verified summary preview: {verified_summary[:100]}...")
                else:
                    logger.error(f"❌ VERIFICATION FAILED: Summary is NULL in database!")
            else:
                logger.error(f"❌ VERIFICATION FAILED: Could not query saved chapter!")
                
        except Exception as db_error:
            logger.error(f"❌ DATABASE INSERT FAILED: {str(db_error)}")
            logger.error(f"🔍 Error type: {type(db_error)}")
            logger.error(f"🔍 Error details: {db_error}")
            raise HTTPException(status_code=500, detail=f"Database insert failed: {str(db_error)}")
        
        # Update story's current_chapter count
        logger.info(f"📈 STEP 4: Updating story current_chapter count...")
        try:
            story_update_response = supabase.table("Stories").update({
                "current_chapter": chapter_data.chapter_number
            }).eq("id", chapter_data.story_id).execute()
            
            logger.info(f"✅ STEP 4 COMPLETE: Story current_chapter updated")
        except Exception as e:
            logger.warning(f"⚠️ STEP 4 WARNING: Could not update story current_chapter: {e}")
        
        # STEP 5: Generate embeddings for the updated story (including new chapter)
        logger.info(f"🔍 STEP 5: Triggering embedding generation for story {chapter_data.story_id}...")
        from services.embedding_service import embedding_service
        
        try:
            background_tasks.add_task(
                embedding_service.create_embeddings_async,
                chapter_data.story_id,
                True  # Force recreate to include the new chapter
            )
            logger.info(f"✅ STEP 5 COMPLETE: Embedding generation scheduled in background")
        except Exception as embedding_error:
            logger.warning(f"⚠️ STEP 5 WARNING: Could not schedule embedding generation: {embedding_error}")
        
        logger.info(f"🎉 SUCCESS: Chapter save process completed successfully!")
        
        return {
            "message": "Chapter saved with auto-generated summary!",
            "chapter_id": chapter_id,
            "story_id": chapter_data.story_id,
            "chapter_number": chapter_data.chapter_number,
            "summary": summary_text if summary_result["success"] else None,
            "summary_generation": {
                "success": summary_result["success"],
                "word_count": word_count,
                "summary_length": len(summary_text) if summary_result["success"] else 0,
                "compression_ratio": summary_result.get("metadata", {}).get("compression_ratio", 0),
                "usage_metrics": summary_result.get("usage_metrics", {})
            },
            "debug_info": {
                "summary_included_in_insert": bool(chapter_insert_data.get("summary")),
                "summary_length": len(summary_text),
                "database_response_received": bool(chapter_response.data),
                "verification_summary_exists": bool(verified_summary) if 'verified_summary' in locals() else "not_checked"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ FATAL ERROR in chapter save process: {str(e)}")
        logger.error(f"🔍 Error type: {type(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save chapter: {str(e)}")

@app.post("/generate_next_chapter")
async def generate_next_chapter_endpoint(
    chapter_input: GenerateNextChapterInput,
    user = Depends(get_authenticated_user)
):
    """
    Generate the next chapter for a story using previous Chapters as context.
    This uses the summary-based approach for story continuity.
    """
    try:
        logger.info(f"📖 Generating Chapter {chapter_input.chapter_number} for story {chapter_input.story_id}...")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", chapter_input.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        story_title = story.get("story_title", "Untitled Story")
        
        # Get previous Chapters and their summaries for context
        previous_Chapters_response = supabase.table("Chapters").select("content, summary").eq("story_id", chapter_input.story_id).lte("chapter_number", chapter_input.chapter_number).order("chapter_number").execute()
        
        previous_summaries = []
        if previous_Chapters_response.data:
            for prev_chapter in previous_Chapters_response.data:
                if prev_chapter.get("summary"):
                    previous_summaries.append(prev_chapter["summary"])
                else:
                    # If no summary exists, create a quick one from content
                    prev_content = prev_chapter.get("content", "")[:500] + "..."
                    previous_summaries.append(f"Previous chapter: {prev_content}")
        
        logger.info(f"📚 Using {len(previous_summaries)} previous chapter summaries for context")
        
        # Generate the chapter using the specialized next chapter generator
        from lc_next_chapter_generator import NextChapterGenerator
        next_generator = NextChapterGenerator()
        
        # Generate the chapter with proper story continuity and token tracking
        generation_result = next_generator.generate_next_chapter(
            story_title=story_title,
            story_outline=chapter_input.story_outline,
            previous_chapter_summaries=previous_summaries,
            chapter_number=chapter_input.chapter_number
        )
        
        if not generation_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Chapter generation failed: {generation_result['token_metrics'].get('error', 'Unknown error')}"
            )
        
        chapter_content = generation_result["chapter_content"]
        token_metrics = generation_result["token_metrics"]
        
        logger.info(f"✅ Chapter {chapter_input.chapter_number} generated successfully!")
        logger.info(f"📊 Generated content length: {len(chapter_content)} characters")
        logger.info(f"📊 Token usage: {token_metrics['token_count_total']} total tokens (input: {token_metrics['token_count_prompt']}, output: {token_metrics['token_count_completion']})")
        
        return {
            "chapter": chapter_content,
            "metadata": {
                "chapter_number": chapter_input.chapter_number,
                "story_id": chapter_input.story_id,
                "word_count": len(chapter_content.split()),
                "character_count": len(chapter_content),
                "previous_Chapters_used": len(previous_summaries),
                "generation_success": True
            },
            "token_metrics": {
                "token_count_prompt": token_metrics["token_count_prompt"],
                "token_count_completion": token_metrics["token_count_completion"],
                "token_count_total": token_metrics["token_count_total"],
                "temperature_used": token_metrics["temperature_used"],
                "model_used": token_metrics["model_used"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating Chapter {chapter_input.chapter_number}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate chapter: {str(e)}")

@app.post("/generate_and_save_chapter")
async def generate_and_save_chapter_endpoint(
    chapter_input: GenerateNextChapterInput,
    background_tasks: BackgroundTasks,
    user = Depends(get_authenticated_user)
):
    """
    Generate the next chapter AND save it to database with complete token tracking.
    This endpoint combines chapter generation and saving in one step.
    """
    try:
        logger.info(f"🚀 GENERATE & SAVE: Starting Chapter {chapter_input.chapter_number} for story {chapter_input.story_id}...")
        
        # Verify story belongs to user - use capitalized table name
        story_response = supabase.table("Stories").select("*").eq("id", chapter_input.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        story_title = story.get("story_title", "Untitled Story")
        
        # Get previous Chapters and their summaries for context - use capitalized table name
        previous_Chapters_response = supabase.table("Chapters").select("content, summary").eq("story_id", chapter_input.story_id).lte("chapter_number", chapter_input.chapter_number).order("chapter_number").execute()
        
        previous_summaries = []
        if previous_Chapters_response.data:
            for prev_chapter in previous_Chapters_response.data:
                if prev_chapter.get("summary"):
                    previous_summaries.append(prev_chapter["summary"])
                else:
                    # If no summary exists, create a quick one from content
                    prev_content = prev_chapter.get("content", "")[:500] + "..."
                    previous_summaries.append(f"Previous chapter: {prev_content}")
        
        logger.info(f"📚 Using {len(previous_summaries)} previous chapter summaries for context")
        
        # STEP 1: Generate the chapter with token tracking
        from lc_next_chapter_generator import NextChapterGenerator
        next_generator = NextChapterGenerator()
        
        generation_result = next_generator.generate_next_chapter(
            story_title=story_title,
            story_outline=chapter_input.story_outline,
            previous_chapter_summaries=previous_summaries,
            chapter_number=chapter_input.chapter_number
        )
        
        if not generation_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Chapter generation failed: {generation_result['token_metrics'].get('error', 'Unknown error')}"
            )
        
        chapter_content = generation_result["chapter_content"]
        token_metrics = generation_result["token_metrics"]
        
        logger.info(f"✅ STEP 1 COMPLETE: Chapter {chapter_input.chapter_number} generated successfully!")
        logger.info(f"📊 Generated content: {len(chapter_content)} characters, {len(chapter_content.split())} words")
        logger.info(f"📊 Token usage: {token_metrics['token_count_total']} total tokens")
        
        # STEP 2: Generate summary for the chapter
        from chapter_summary import generate_chapter_summary
        
        # Build story context for summary
        story_context = f"STORY: {story_title}\nOUTLINE:\n{chapter_input.story_outline}"
        if previous_summaries:
            story_context += f"\n\nPREVIOUS Chapters:\n" + "\n".join(previous_summaries)
        
        logger.info(f"🤖 STEP 2: Generating summary for Chapter {chapter_input.chapter_number}...")
        
        summary_result = generate_chapter_summary(
            chapter_content=chapter_content,
            chapter_number=chapter_input.chapter_number,
            story_context=story_context,
            story_title=story_title
        )
        
        summary_text = ""
        summary_tokens = {}
        if summary_result["success"]:
            summary_text = summary_result["summary"]
            summary_tokens = summary_result.get("usage_metrics", {})
            logger.info(f"✅ STEP 2 COMPLETE: Summary generated ({len(summary_text)} chars)")
        else:
            logger.warning(f"⚠️ STEP 2 WARNING: Summary generation failed: {summary_result['error']}")
            summary_text = f"Summary generation failed: {summary_result['error']}"
        
        # STEP 3: Save chapter with complete token tracking
        word_count = len(chapter_content.split())
        
        # Combine token metrics from both generation and summarization
        total_prompt_tokens = token_metrics["token_count_prompt"] + summary_tokens.get("estimated_input_tokens", 0)
        total_completion_tokens = token_metrics["token_count_completion"] + summary_tokens.get("estimated_output_tokens", 0)
        total_all_tokens = total_prompt_tokens + total_completion_tokens
        
        # Get the next version number for this chapter
        next_version_number = await get_next_chapter_version_number(chapter_input.story_id, chapter_input.chapter_number)
        
        # Deactivate previous versions of this chapter
        await deactivate_previous_chapter_versions(chapter_input.story_id, chapter_input.chapter_number)
        
        # Use only fields that exist in basic schema 
        chapter_insert_data = {
            "story_id": chapter_input.story_id,
            "chapter_number": chapter_input.chapter_number,
            "title": f"Chapter {chapter_input.chapter_number}",  # Auto-generated title
            "content": chapter_content,
            "summary": summary_text,
            "version_number": next_version_number,  # Add proper versioning
            "is_active": True,  # Mark this version as active
            # Note: Removed token tracking fields since they don't exist in basic schema
        }
        
        logger.info(f"💾 STEP 3: Saving chapter with complete metrics...")
        logger.info(f"📊 Total tokens: prompt={total_prompt_tokens}, completion={total_completion_tokens}, total={total_all_tokens}")
        
        try:
            chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
            
            if not chapter_response.data:
                raise HTTPException(status_code=500, detail="Failed to save chapter")
            
            chapter_id = chapter_response.data[0]["id"]
            
            logger.info(f"✅ STEP 3 COMPLETE: Chapter saved with ID: {chapter_id}")
            
            # Update story's current_chapter count if field exists
            try:
                supabase.table("Stories").update({
                    "current_chapter": chapter_input.chapter_number
                }).eq("id", chapter_input.story_id).execute()
                logger.info(f"✅ Updated story current_chapter to {chapter_input.chapter_number}")
            except Exception as update_error:
                logger.warning(f"⚠️ Could not update story current_chapter: {update_error}")
            
            # Generate embeddings for the updated story (including new chapter)
            logger.info(f"🔍 Triggering embedding generation for story {chapter_input.story_id}...")
            from services.embedding_service import embedding_service
            
            try:
                background_tasks.add_task(
                    embedding_service.create_embeddings_async,
                    chapter_input.story_id,
                    True  # Force recreate to include the new chapter
                )
                logger.info(f"✅ Embedding generation scheduled in background")
            except Exception as embedding_error:
                logger.warning(f"⚠️ Could not schedule embedding generation: {embedding_error}")
            
            logger.info(f"🎉 SUCCESS: Generate & Save completed for Chapter {chapter_input.chapter_number}!")
            
            return {
                "success": True,
                "message": "Chapter generated and saved successfully!",
                "chapter_id": chapter_id,
                "chapter_number": chapter_input.chapter_number,
                "story_id": chapter_input.story_id,
                "chapter_content": chapter_content,
                "summary": summary_text,
                "metadata": {
                    "word_count": word_count,
                    "character_count": len(chapter_content),
                    "generation_success": True,
                    "summary_success": summary_result["success"]
                },
                "token_metrics": {
                    "generation": {
                        "prompt_tokens": token_metrics["token_count_prompt"],
                        "completion_tokens": token_metrics["token_count_completion"],
                        "total_tokens": token_metrics["token_count_total"],
                        "temperature": token_metrics["temperature_used"],
                        "model": token_metrics["model_used"]
                    },
                    "summarization": {
                        "prompt_tokens": summary_tokens.get("estimated_input_tokens", 0),
                        "completion_tokens": summary_tokens.get("estimated_output_tokens", 0),
                        "total_tokens": summary_tokens.get("estimated_total_tokens", 0),
                        "temperature": summary_tokens.get("temperature_used", 0.3),
                        "model": summary_tokens.get("model_used", "gpt-4o-mini")
                    },
                    "combined": {
                        "total_prompt_tokens": total_prompt_tokens,
                        "total_completion_tokens": total_completion_tokens,
                        "total_all_tokens": total_all_tokens
                    }
                }
            }
            
        except Exception as db_error:
            logger.error(f"❌ DATABASE ERROR: {str(db_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to save chapter: {str(db_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ FATAL ERROR in generate & save: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate and save chapter: {str(e)}")

@app.get("/debug/story/{story_id}/Chapters")
async def debug_story_Chapters(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """Debug endpoint to check chapter storage and retrieval for a specific story."""
    try:
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            logger.error(f"❌ DEBUG - Story {story_id} not found for user {user.id}")
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story_data = story_response.data[0]
        logger.info(f"✅ DEBUG - Found story: {story_data.get('story_title', 'Untitled')}")
        
        # Get Chapters from database
        Chapters_response = supabase.table("Chapters").select("*").eq("story_id", story_id).order("chapter_number").execute()
        
        Chapters_info = []
        if Chapters_response.data:
            for chapter in Chapters_response.data:
                Chapters_info.append({
                    "id": chapter["id"],
                    "chapter_number": chapter["chapter_number"],
                    "title": chapter.get("title", "Untitled"),
                    "content_length": len(chapter.get("content", "")),
                    "content_preview": chapter.get("content", "")[:100] + "..." if len(chapter.get("content", "")) > 100 else chapter.get("content", ""),
                    "created_at": chapter.get("created_at"),
                    "has_summary": bool(chapter.get("summary"))
                })
        
        logger.info(f"📊 DEBUG - Found {len(Chapters_info)} Chapters for story {story_id}")
        
        return {
            "success": True,
            "story_id": story_id,
            "story_title": story_data.get("story_title", "Untitled"),
            "Chapters_count": len(Chapters_info),
            "Chapters": Chapters_info,
            "database_query_success": True,
            "user_id": str(user.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ DEBUG - Failed to get Chapters for story {story_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Debug query failed: {str(e)}")

# Add this after the existing endpoint definitions, before the test endpoints section

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

@app.post("/branch_from_choice")
async def branch_from_choice_endpoint(
    request: BranchFromChoiceInput,
    user = Depends(get_authenticated_user)
):
    """
    Generate a new branch in the story by selecting a different choice from a previous chapter.
    This will generate new chapters from that point onward while preserving the original path.
    """
    try:
        logger.info(f"🌿 BRANCH: User wants to branch from chapter {request.chapter_number}, choice {request.choice_id}")
        logger.info(f"📊 BRANCH: story_id={request.story_id}")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", request.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        logger.info(f"✅ BRANCH: Story verified: {story.get('story_title', 'Untitled')}")
        
        # Get the main branch ID for this story
        main_branch_id = await get_main_branch_id(request.story_id)
        
        # Get all choices for the specified chapter to validate the choice exists
        choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
        
        available_choices = choices_response.data
        if not available_choices:
            raise HTTPException(status_code=404, detail=f"No choices found for chapter {request.chapter_number}")
        
        # Find the selected choice
        selected_choice = None
        for choice in available_choices:
            if str(choice.get('id')) == str(request.choice_id) or str(choice.get('choice_id')) == str(request.choice_id):
                selected_choice = choice
                break
        
        if not selected_choice:
            raise HTTPException(status_code=400, detail="Invalid choice selected for branching")
        
        logger.info(f"🎯 BRANCH: Selected choice found: {selected_choice.get('title', 'No title')}")
        
        # Clear the "is_selected" flag from all choices in this chapter (reset previous selection)
        logger.info(f"🔄 BRANCH: Resetting previous choice selections for chapter {request.chapter_number}")
        supabase.table("story_choices").update({"is_selected": False, "selected_at": None}).eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("chapter_number", request.chapter_number).execute()
        
        # Mark the new choice as selected
        from datetime import datetime
        logger.info(f"✅ BRANCH: Marking new choice as selected")
        supabase.table("story_choices").update({
            "is_selected": True,
            "selected_at": datetime.utcnow().isoformat()
        }).eq("id", selected_choice["id"]).execute()
        
        # Get the main branch ID for this story
        main_branch_id = await get_main_branch_id(request.story_id)
        
        # Get all chapters up to (but not including) the next chapter from the main branch
        # This gives us the context for generating from this point
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).lte("chapter_number", request.chapter_number).order("chapter_number").execute()
        
        previous_chapters = chapters_response.data
        logger.info(f"📚 BRANCH: Using {len(previous_chapters)} previous chapters for context")
        
        # Generate the next chapter based on the new choice
        next_chapter_number = request.chapter_number + 1
        logger.info(f"📝 BRANCH: Generating chapter {next_chapter_number} based on new choice")
        
        # Use the story service to generate the next chapter
        try:
            next_chapter_result = await story_service.generate_next_chapter(
                story=story,
                previous_Chapters=previous_chapters,
                selected_choice=selected_choice,
                next_chapter_number=next_chapter_number,
                user_id=user.id
            )
            logger.info(f"✅ BRANCH: Chapter {next_chapter_number} generated successfully")
            chapter_content_length = len(next_chapter_result.get("chapter_content", "")) if next_chapter_result.get("chapter_content") else 0
            
        except Exception as generation_error:
            logger.error(f"❌ BRANCH: Chapter generation failed: {str(generation_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate branched chapter: {str(generation_error)}")
        
        # Get the next version number for this chapter (with branch support)
        next_version_number = await get_next_chapter_version_number(request.story_id, next_chapter_number, main_branch_id)
        
        # Deactivate previous versions of this chapter in this branch
        await deactivate_previous_chapter_versions(request.story_id, next_chapter_number, main_branch_id)
        
        # Always insert new chapter version (don't update existing ones)
        logger.info(f"💾 BRANCH: Inserting new chapter version {next_version_number} for chapter {next_chapter_number}")
        chapter_content = next_chapter_result.get("chapter_content") or next_chapter_result.get("content", "")
        chapter_insert_data = {
            "story_id": request.story_id,
            "branch_id": main_branch_id,
            "chapter_number": next_chapter_number,
            "title": next_chapter_result.get("title", f"Chapter {next_chapter_number}"),
            "content": chapter_content,
            "word_count": len(chapter_content.split()),
            "version_number": next_version_number,  # Add proper versioning
            "is_active": True,  # Mark this version as active
        }
        chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
        chapter_id = chapter_response.data[0]["id"]
        
        # Generate and save chapter summary
        chapter_text = next_chapter_result.get("chapter_content") or next_chapter_result.get("content", "")
        logger.info(f"🔍 BRANCH SUMMARY: Starting summary generation for chapter {next_chapter_number}")
        
        try:
            from chapter_summary import generate_chapter_summary
            story_outline = story.get("story_outline", "")
            
            summary_result = generate_chapter_summary(
                chapter_content=chapter_text,
                chapter_number=next_chapter_number,
                story_context=story_outline,
                story_title=story.get("story_title", "Untitled Story")
            )
            
            if summary_result["success"]:
                summary_text = summary_result["summary"]
                logger.info(f"🔍 BRANCH SUMMARY: Updating database with summary for chapter ID {chapter_id}")
                supabase.table("Chapters").update({"summary": summary_text}).eq("id", chapter_id).execute()
                logger.info(f"✅ BRANCH SUMMARY: Chapter {next_chapter_number} summary saved")
            else:
                logger.error(f"❌ BRANCH SUMMARY: Failed to generate summary for chapter {next_chapter_number}")
        except Exception as summary_error:
            logger.error(f"❌ BRANCH SUMMARY: Exception during summary generation: {str(summary_error)}")
        
        # Remove any choices for chapters beyond this point (they're now invalid due to branching)
        logger.info(f"🧹 BRANCH: Cleaning up choices for chapters > {next_chapter_number}")
        supabase.table("story_choices").delete().eq("story_id", request.story_id).eq("branch_id", main_branch_id).gt("chapter_number", next_chapter_number).execute()
        
        # Save new choices for the generated chapter
        choices = next_chapter_result.get("choices", [])
        if choices:
            # Save choices using helper function
            await save_choices_for_chapter(
                story_id=request.story_id,
                chapter_id=chapter_id,
                chapter_number=next_chapter_number,
                choices=choices,
                user_id=user.id,
                branch_id=main_branch_id
            )
        
        # Update story's current_chapter
        supabase.table("Stories").update({"current_chapter": next_chapter_number}).eq("id", request.story_id).execute()
        
        response_payload = {
            "success": True,
            "message": f"Successfully branched from chapter {request.chapter_number}",
            "chapter_content": chapter_text,
            "chapter_number": next_chapter_number,
            "story_id": request.story_id,
            "selected_choice": selected_choice,
            "choices": choices,
            "branch_info": {
                "branched_from_chapter": request.chapter_number,
                "branched_choice": selected_choice.get("title", ""),
                "new_chapter_number": next_chapter_number
            }
        }
        
        logger.info(f"🌿 BRANCH: Successfully completed branching operation")
        return response_payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ BRANCH: Unexpected error: {str(e)}")
        import traceback
        logger.error(f"❌ BRANCH: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/branch_preview")
async def branch_preview_endpoint(
    request: BranchPreviewInput,
    user = Depends(get_authenticated_user)
):
    """
    Generate a preview of the next chapter based on a different choice from a previous chapter.
    This endpoint does NOT save anything to the database - it only returns what the chapter would look like.
    """
    try:
        logger.info(f"👀 BRANCH-PREVIEW: User {user.id} requesting preview for story {request.story_id}, chapter {request.chapter_number}, choice {request.choice_id}")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", request.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        logger.info(f"✅ BRANCH-PREVIEW: Story verified: {story.get('story_title', 'Untitled')}")
        
        # Get the main branch ID for this story
        main_branch_id = await get_main_branch_id(request.story_id)
        
        # Get all choices for the specified chapter to validate the choice exists
        logger.info(f"🔍 BRANCH-PREVIEW: Looking for choices with story_id={request.story_id}, branch_id={main_branch_id}, user_id={user.id}, chapter_number={request.chapter_number}")
        choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
        
        available_choices = choices_response.data
        logger.info(f"📊 BRANCH-PREVIEW: Found {len(available_choices)} choices for chapter {request.chapter_number}")
        
        if not available_choices:
            # Let's try without branch_id to see if choices exist but with wrong branch
            logger.info(f"🔍 BRANCH-PREVIEW: No choices found with branch_id, trying without branch_id...")
            fallback_choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
            fallback_choices = fallback_choices_response.data
            logger.info(f"📊 BRANCH-PREVIEW: Found {len(fallback_choices)} choices without branch_id filter")
            
            if fallback_choices:
                logger.info(f"🔄 BRANCH-PREVIEW: Updating {len(fallback_choices)} choices to use main branch {main_branch_id}")
                # Update the choices to use the correct branch_id
                for choice in fallback_choices:
                    supabase.table("story_choices").update({"branch_id": main_branch_id}).eq("id", choice["id"]).execute()
                
                # Now try again with the updated choices
                choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
                available_choices = choices_response.data
                logger.info(f"✅ BRANCH-PREVIEW: After update, found {len(available_choices)} choices")
            
            if not available_choices:
                raise HTTPException(status_code=404, detail=f"No choices found for chapter {request.chapter_number}")
        
        # Find the selected choice
        selected_choice = None
        for choice in available_choices:
            if str(choice.get('id')) == str(request.choice_id) or str(choice.get('choice_id')) == str(request.choice_id):
                selected_choice = choice
                break
        
        if not selected_choice:
            raise HTTPException(status_code=400, detail="Invalid choice selected for preview")
        
        logger.info(f"🎯 BRANCH-PREVIEW: Selected choice found: {selected_choice.get('title', 'No title')}")
        
        # Get all chapters up to (but not including) the next chapter for context
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).lte("chapter_number", request.chapter_number).order("chapter_number").execute()
        
        previous_chapters = chapters_response.data
        logger.info(f"📚 BRANCH-PREVIEW: Using {len(previous_chapters)} previous chapters for context")
        
        # Generate the next chapter based on the choice (WITHOUT saving to database)
        next_chapter_number = request.chapter_number + 1
        logger.info(f"📝 BRANCH-PREVIEW: Generating preview for chapter {next_chapter_number} based on choice")
        
        # Use the story service to generate the next chapter
        try:
            logger.info(f"📝 BRANCH-PREVIEW: Calling story_service.generate_next_chapter...")
            logger.info(f"📝 BRANCH-PREVIEW: story_title='{story.get('story_title', 'Unknown')}'")
            logger.info(f"📝 BRANCH-PREVIEW: previous_chapters_count={len(previous_chapters)}")
            logger.info(f"📝 BRANCH-PREVIEW: selected_choice_title='{selected_choice.get('title', 'Unknown')}'")
            logger.info(f"📝 BRANCH-PREVIEW: next_chapter_number={next_chapter_number}")
            
            next_chapter_result = await story_service.generate_next_chapter(
                story=story,
                previous_Chapters=previous_chapters,
                selected_choice=selected_choice,
                next_chapter_number=next_chapter_number,
                user_id=user.id
            )
            logger.info(f"✅ BRANCH-PREVIEW: Chapter {next_chapter_number} preview generated successfully")
            logger.info(f"📊 BRANCH-PREVIEW: Result keys: {list(next_chapter_result.keys()) if next_chapter_result else 'None'}")
            
            chapter_content = next_chapter_result.get("chapter_content") or next_chapter_result.get("content", "")
            
        except Exception as generation_error:
            logger.error(f"❌ BRANCH-PREVIEW: Chapter generation failed: {str(generation_error)}")
            import traceback
            logger.error(f"❌ BRANCH-PREVIEW: Full traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to generate preview chapter: {str(generation_error)}")
        
        # Return the preview without saving anything to database
        response_payload = {
            "success": True,
            "preview": True,
            "chapter_number": next_chapter_number,
            "chapter_content": chapter_content,
            "choices": next_chapter_result.get("choices", []),
            "selected_choice": selected_choice,
            "message": f"Preview generated for chapter {next_chapter_number} based on choice: {selected_choice.get('title', 'Unknown')}"
        }
        
        logger.info(f"👀 BRANCH-PREVIEW: Successfully generated preview for chapter {next_chapter_number}")
        return response_payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ BRANCH-PREVIEW: Unexpected error: {str(e)}")
        import traceback
        logger.error(f"❌ BRANCH-PREVIEW: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# New branching endpoints
@app.post("/create_branch")
async def create_branch_endpoint(
    request: BranchFromChoiceInput,
    user = Depends(get_authenticated_user)
):
    """
    Create a new branch from a choice without overwriting the main branch.
    This preserves all existing branches and creates a new parallel storyline.
    """
    try:
        logger.info(f"🌿 CREATE-BRANCH: Creating new branch from chapter {request.chapter_number}, choice {request.choice_id}")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", request.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        logger.info(f"✅ CREATE-BRANCH: Story verified: {story.get('story_title', 'Untitled')}")
        
        # Get the main branch ID
        main_branch_id = await get_main_branch_id(request.story_id)
        
        # Validate the choice exists
        choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
        
        available_choices = choices_response.data
        if not available_choices:
            raise HTTPException(status_code=404, detail=f"No choices found for chapter {request.chapter_number}")
        
        # Find the selected choice
        selected_choice = None
        for choice in available_choices:
            if str(choice.get('id')) == str(request.choice_id) or str(choice.get('choice_id')) == str(request.choice_id):
                selected_choice = choice
                break
        
        if not selected_choice:
            raise HTTPException(status_code=400, detail="Invalid choice selected for branching")
        
        logger.info(f"🎯 CREATE-BRANCH: Selected choice found: {selected_choice.get('title', 'No title')}")
        
        # Create new branch
        new_branch_id = await create_new_branch(
            story_id=request.story_id,
            parent_branch_id=main_branch_id,
            branched_from_chapter=request.chapter_number,
            branch_name=f"branch_from_ch{request.chapter_number}_{selected_choice.get('title', 'choice')[:20]}"
        )
        
        logger.info(f"✅ CREATE-BRANCH: New branch created: {new_branch_id}")
        
        # Copy chapters and choices up to the branch point
        await copy_chapters_to_branch(
            story_id=request.story_id,
            from_branch_id=main_branch_id,
            to_branch_id=new_branch_id,
            up_to_chapter=request.chapter_number
        )
        
        # Mark the selected choice as selected in the new branch
        from datetime import datetime
        supabase.table("story_choices").update({
            "is_selected": True,
            "selected_at": datetime.utcnow().isoformat()
        }).eq("story_id", request.story_id).eq("branch_id", new_branch_id).eq("chapter_number", request.chapter_number).eq("id", selected_choice["id"]).execute()
        
        # Generate the next chapter for the new branch
        next_chapter_number = request.chapter_number + 1
        logger.info(f"📝 CREATE-BRANCH: Generating chapter {next_chapter_number} for new branch")
        
        # Get chapters from the new branch for context
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", request.story_id).eq("branch_id", new_branch_id).lte("chapter_number", request.chapter_number).order("chapter_number").execute()
        
        previous_chapters = chapters_response.data
        
        # Generate the next chapter
        next_chapter_result = await story_service.generate_next_chapter(
            story=story,
            previous_Chapters=previous_chapters,
            selected_choice=selected_choice,
            next_chapter_number=next_chapter_number,
            user_id=user.id
        )
        
        # Save the new chapter to the new branch
        chapter_content = next_chapter_result.get("chapter_content") or next_chapter_result.get("content", "")
        
        # Get the next version number for this chapter in the new branch
        next_version_number = await get_next_chapter_version_number(request.story_id, next_chapter_number, new_branch_id)
        
        chapter_insert_data = {
            "story_id": request.story_id,
            "branch_id": new_branch_id,
            "chapter_number": next_chapter_number,
            "title": next_chapter_result.get("title", f"Chapter {next_chapter_number}"),
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
                branch_id=new_branch_id
            )
        
        return {
            "success": True,
            "message": f"New branch created successfully from chapter {request.chapter_number}",
            "branch_id": new_branch_id,
            "chapter_content": chapter_content,
            "chapter_number": next_chapter_number,
            "story_id": request.story_id,
            "selected_choice": selected_choice,
            "choices": choices,
            "branch_info": {
                "parent_branch_id": main_branch_id,
                "branched_from_chapter": request.chapter_number,
                "new_chapter_number": next_chapter_number
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ CREATE-BRANCH: Unexpected error: {str(e)}")
        import traceback
        logger.error(f"❌ CREATE-BRANCH: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/story/{story_id}/branches")
async def get_story_branches_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """Get all branches for a story to display in the branch visualization."""
    try:
        logger.info(f"📊 Getting branches for story {story_id}")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        # Get all branches for this story
        branches_response = supabase.table("branches").select("*").eq("story_id", story_id).order("created_at").execute()
        
        branches_data = []
        for branch in branches_response.data:
            # Get chapter count for this branch
            chapters_response = supabase.table("Chapters").select("id").eq("story_id", story_id).eq("branch_id", branch["id"]).execute()
            chapter_count = len(chapters_response.data) if chapters_response.data else 0
            
            branches_data.append({
                "id": branch["id"],
                "branch_name": branch["branch_name"],
                "parent_branch_id": branch["parent_branch_id"],
                "branched_from_chapter": branch["branched_from_chapter"],
                "created_at": branch["created_at"],
                "chapter_count": chapter_count
            })
        
        return {
            "success": True,
            "story_id": story_id,
            "branches": branches_data,
            "total_branches": len(branches_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get branches failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get branches: {str(e)}")

@app.get("/story/{story_id}/branch/{branch_id}/chapters")
async def get_branch_chapters_endpoint(
    story_id: int,
    branch_id: str,
    user = Depends(get_authenticated_user)
):
    """Get all chapters for a specific branch."""
    try:
        logger.info(f"📚 Getting chapters for story {story_id}, branch {branch_id}")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        # Get chapters for this branch
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", story_id).eq("branch_id", branch_id).order("chapter_number").execute()
        
        chapters_data = []
        for chapter in chapters_response.data:
            chapters_data.append({
                "id": chapter["id"],
                "chapter_number": chapter["chapter_number"],
                "title": chapter["title"],
                "content": chapter["content"],
                "summary": chapter.get("summary"),
                "word_count": chapter.get("word_count", 0),
                "created_at": chapter.get("created_at")
            })
        
        return {
            "success": True,
            "story_id": story_id,
            "branch_id": branch_id,
            "chapters": chapters_data,
            "total_chapters": len(chapters_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get branch chapters failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get branch chapters: {str(e)}")

# Chapter versioning helper functions
async def get_next_chapter_version_number(story_id: int, chapter_number: int, branch_id: str = None) -> int:
    """
    Get the next version number for a chapter by finding the highest existing version number
    and incrementing it by 1. If no versions exist, returns 1.
    """
    try:
        logger.info(f"🔍 Getting next version number for story {story_id}, chapter {chapter_number}")
        
        # Build query to find highest version number
        query = supabase.table("Chapters").select("version_number").eq("story_id", story_id).eq("chapter_number", chapter_number)
        
        # Add branch filter if provided
        if branch_id:
            query = query.eq("branch_id", branch_id)
        
        # Execute query to get highest version
        existing_versions = query.order("version_number", desc=True).limit(1).execute()
        
        if existing_versions.data and len(existing_versions.data) > 0:
            max_version = existing_versions.data[0]["version_number"] or 0
            next_version = max_version + 1
            logger.info(f"✅ Found existing version {max_version}, next version will be {next_version}")
        else:
            next_version = 1
            logger.info(f"✅ No existing versions found, starting with version 1")
        
        return next_version
        
    except Exception as e:
        logger.error(f"❌ Error getting next version number: {str(e)}")
        # Default to 1 if there's an error
        return 1

async def deactivate_previous_chapter_versions(story_id: int, chapter_number: int, branch_id: str = None):
    """
    Mark all previous versions of a chapter as inactive.
    """
    try:
        logger.info(f"🔄 Deactivating previous versions for story {story_id}, chapter {chapter_number}")
        
        # Build query to find all active versions
        query = supabase.table("Chapters").update({"is_active": False}).eq("story_id", story_id).eq("chapter_number", chapter_number).eq("is_active", True)
        
        # Add branch filter if provided
        if branch_id:
            query = query.eq("branch_id", branch_id)
        
        # Execute the update
        result = query.execute()
        
        if result.data:
            logger.info(f"✅ Deactivated {len(result.data)} previous version(s)")
        else:
            logger.info(f"ℹ️ No previous active versions found")
            
    except Exception as e:
        logger.error(f"❌ Error deactivating previous versions: {str(e)}")
        # Don't raise exception - this is not critical

async def save_choices_for_chapter(story_id: int, chapter_id: int, chapter_number: int, choices: list, user_id: int, branch_id: str = None):
    """
    Save choices for a specific chapter version, ensuring they're properly linked to the chapter_id.
    This helper function ensures consistency across all endpoints.
    """
    try:
        logger.info(f"💾 Saving {len(choices)} choices for chapter {chapter_number} (ID: {chapter_id}) in story {story_id}")
        
        # Remove any existing choices for this specific chapter version
        delete_query = supabase.table("story_choices").delete().eq("chapter_id", chapter_id)
        delete_query.execute()
        
        # Insert new choices linked to the specific chapter version
        choice_records = []
        for idx, choice in enumerate(choices):
            choice_data = {
                "story_id": story_id,
                "chapter_id": chapter_id,  # CRITICAL: Link to specific chapter version
                "chapter_number": chapter_number,
                "choice_id": choice.get("choice_id") or f"choice_{idx+1}",
                "title": choice.get("title"),
                "description": choice.get("description"),
                "story_impact": choice.get("impact") or choice.get("story_impact") or "medium",
                "choice_type": choice.get("type") or choice.get("choice_type") or "action",
                "user_id": user_id,
                "is_selected": False,
            }
            
            # Add branch_id if provided
            if branch_id:
                choice_data["branch_id"] = branch_id
            
            choice_records.append(choice_data)
        
        # Batch insert all choices
        if choice_records:
            choices_response = supabase.table("story_choices").insert(choice_records).execute()
            if choices_response.data:
                logger.info(f"✅ Successfully saved {len(choice_records)} choices for chapter version {chapter_id}")
                return choices_response.data
            else:
                logger.error(f"❌ Failed to save choices - no data returned")
        
        return []
        
    except Exception as e:
        logger.error(f"❌ Error saving choices for chapter {chapter_id}: {str(e)}")
        # Don't raise exception - continue with the main operation
        return []

# Branch helper functions
async def get_main_branch_id(story_id: int) -> str:
    """Get the main branch ID for a story."""
    try:
        logger.info(f"🔍 Getting main branch ID for story {story_id}")
        branch_response = supabase.table("branches").select("id").eq("story_id", story_id).eq("branch_name", "main").execute()
        
        if branch_response.data:
            branch_id = branch_response.data[0]["id"]
            logger.info(f"✅ Found existing main branch: {branch_id}")
            return branch_id
        else:
            # Create main branch if it doesn't exist
            logger.info(f"🆕 Creating main branch for story {story_id}")
            main_branch = {
                "id": str(uuid.uuid4()),
                "story_id": story_id,
                "parent_branch_id": None,
                "branched_from_chapter": None,
                "branch_name": "main",
                "created_at": datetime.utcnow().isoformat()
            }
            create_response = supabase.table("branches").insert(main_branch).execute()
            new_branch_id = create_response.data[0]["id"]
            logger.info(f"✅ Created main branch: {new_branch_id}")
            
            # Update existing chapters to use this branch
            logger.info(f"🔄 Updating existing chapters to use main branch")
            supabase.table("Chapters").update({"branch_id": new_branch_id}).eq("story_id", story_id).is_("branch_id", "null").execute()
            
            # Update existing choices to use this branch  
            logger.info(f"🔄 Updating existing choices to use main branch")
            supabase.table("story_choices").update({"branch_id": new_branch_id}).eq("story_id", story_id).is_("branch_id", "null").execute()
            
            return new_branch_id
    except Exception as e:
        logger.error(f"❌ Error getting/creating main branch ID for story {story_id}: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get main branch for story {story_id}: {str(e)}")

async def create_new_branch(story_id: int, parent_branch_id: str, branched_from_chapter: int, branch_name: str = None) -> str:
    """Create a new branch for a story."""
    try:
        new_branch = {
            "id": str(uuid.uuid4()),
            "story_id": story_id,
            "parent_branch_id": parent_branch_id,
            "branched_from_chapter": branched_from_chapter,
            "branch_name": branch_name or f"branch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.utcnow().isoformat()
        }
        create_response = supabase.table("branches").insert(new_branch).execute()
        return create_response.data[0]["id"]
    except Exception as e:
        logger.error(f"Error creating new branch: {e}")
        raise HTTPException(status_code=500, detail="Failed to create new branch")

async def copy_chapters_to_branch(story_id: int, from_branch_id: str, to_branch_id: str, up_to_chapter: int):
    """Copy chapters from one branch to another up to a specific chapter number."""
    try:
        # Get chapters from source branch
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", story_id).eq("branch_id", from_branch_id).lte("chapter_number", up_to_chapter).execute()
        
        if chapters_response.data:
            # Copy chapters to new branch
            for chapter in chapters_response.data:
                chapter_copy = dict(chapter)
                del chapter_copy["id"]  # Remove ID so new one is generated
                chapter_copy["branch_id"] = to_branch_id
                supabase.table("Chapters").insert(chapter_copy).execute()
                
        # Get choices from source branch
        choices_response = supabase.table("story_choices").select("*").eq("story_id", story_id).eq("branch_id", from_branch_id).lte("chapter_number", up_to_chapter).execute()
        
        if choices_response.data:
            # Copy choices to new branch
            for choice in choices_response.data:
                choice_copy = dict(choice)
                del choice_copy["id"]  # Remove ID so new one is generated
                choice_copy["branch_id"] = to_branch_id
                supabase.table("story_choices").insert(choice_copy).execute()
                
    except Exception as e:
        logger.error(f"Error copying chapters to branch: {e}")
        raise HTTPException(status_code=500, detail="Failed to copy chapters to new branch")

@app.delete("/story/{story_id}")
async def delete_story_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """
    Delete a story and all its associated data (branches, chapters, choices).
    This handles cascade deletion properly.
    """
    try:
        logger.info(f"🗑️ Deleting story {story_id} for user {user.id}")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        story_title = story.get("story_title", "Untitled")
        logger.info(f"✅ Story verified for deletion: {story_title}")
        
        # Delete in the correct order to avoid foreign key constraint violations
        
        # 1. Delete embeddings first (if any)
        try:
            logger.info(f"🧹 Deleting embeddings for story {story_id}")
            await embedding_service._delete_embeddings(story_id)
        except Exception as e:
            logger.warning(f"⚠️ Could not delete embeddings: {e}")
        
        # 2. Delete story_choices (they reference branches)
        logger.info(f"🧹 Deleting story choices for story {story_id}")
        supabase.table("story_choices").delete().eq("story_id", story_id).execute()
        
        # 3. Delete chapters (they reference branches)
        logger.info(f"🧹 Deleting chapters for story {story_id}")
        supabase.table("Chapters").delete().eq("story_id", story_id).execute()
        
        # 4. Delete branches (they reference the story)
        logger.info(f"🧹 Deleting branches for story {story_id}")
        supabase.table("branches").delete().eq("story_id", story_id).execute()
        
        # 5. Finally delete the story itself
        logger.info(f"🧹 Deleting story {story_id}")
        supabase.table("Stories").delete().eq("id", story_id).eq("user_id", user.id).execute()
        
        # Invalidate caches
        await story_service.invalidate_story_cache(story_id)
        await story_service.invalidate_user_cache(user.id)
        
        logger.info(f"✅ Story {story_id} '{story_title}' deleted successfully")
        
        return {
            "success": True,
            "message": f"Story '{story_title}' deleted successfully",
            "story_id": story_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete story failed: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to delete story: {str(e)}")

@app.get("/story/{story_id}/tree")
async def get_story_tree_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """
    Get the complete story structure as a tree for visualization.
    Returns nodes (chapters) and edges (choices) with their relationships.
    """
    try:
        logger.info(f"🌳 Getting story tree for story {story_id}")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        
        # Get all branches for this story
        branches_response = supabase.table("branches").select("*").eq("story_id", story_id).order("created_at").execute()
        branches = branches_response.data
        
        # Get all chapters for all branches
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", story_id).order("branch_id").order("chapter_number").execute()
        chapters = chapters_response.data
        
        # Get all choices for all branches
        choices_response = supabase.table("story_choices").select("*").eq("story_id", story_id).order("branch_id").order("chapter_number").execute()
        choices = choices_response.data
        
        # Build the tree structure
        tree_data = {
            "story": {
                "id": story_id,
                "title": story.get("story_title", "Untitled"),
                "outline": story.get("story_outline", ""),
                "created_at": story.get("created_at")
            },
            "branches": [],
            "nodes": [],
            "edges": []
        }
        
        # Process branches
        branch_lookup = {}
        for branch in branches:
            branch_data = {
                "id": branch["id"],
                "name": branch["branch_name"],
                "parent_branch_id": branch["parent_branch_id"],
                "branched_from_chapter": branch["branched_from_chapter"],
                "created_at": branch["created_at"],
                "is_main": branch["branch_name"] == "main"
            }
            tree_data["branches"].append(branch_data)
            branch_lookup[branch["id"]] = branch_data
        
        # Process chapters as nodes
        chapter_lookup = {}
        for chapter in chapters:
            node_id = f"chapter_{chapter['id']}"
            branch_info = branch_lookup.get(chapter["branch_id"], {})
            
            node_data = {
                "id": node_id,
                "type": "chapter",
                "chapter_id": chapter["id"],
                "chapter_number": chapter["chapter_number"],
                "title": chapter.get("title", f"Chapter {chapter['chapter_number']}"),
                "content": chapter["content"],
                "summary": chapter.get("summary", ""),
                "word_count": chapter.get("word_count", 0),
                "branch_id": chapter["branch_id"],
                "branch_name": branch_info.get("name", "unknown"),
                "is_main_branch": branch_info.get("is_main", False),
                "created_at": chapter.get("created_at"),
                "position": {
                    "x": chapter["chapter_number"] * 200,  # Horizontal spacing
                    "y": 0  # Will be calculated based on branch
                }
            }
            tree_data["nodes"].append(node_data)
            chapter_lookup[f"{chapter['branch_id']}_{chapter['chapter_number']}"] = node_data
        
        # Process choices as edges
        choice_lookup = {}
        for choice in choices:
            choice_key = f"{choice['branch_id']}_{choice['chapter_number']}"
            if choice_key not in choice_lookup:
                choice_lookup[choice_key] = []
            choice_lookup[choice_key].append(choice)
        
        # Create edges for choices
        for chapter in chapters:
            source_node_id = f"chapter_{chapter['id']}"
            chapter_key = f"{chapter['branch_id']}_{chapter['chapter_number']}"
            chapter_choices = choice_lookup.get(chapter_key, [])
            
            for choice in chapter_choices:
                # Find the target chapter (next chapter in sequence or branched chapter)
                target_chapter_number = chapter["chapter_number"] + 1
                target_chapter_key = f"{chapter['branch_id']}_{target_chapter_number}"
                target_node = chapter_lookup.get(target_chapter_key)
                
                if target_node:
                    edge_data = {
                        "id": f"choice_{choice['id']}",
                        "type": "choice",
                        "source": source_node_id,
                        "target": target_node["id"],
                        "choice_id": choice["id"],
                        "choice_title": choice.get("title", "Untitled Choice"),
                        "choice_description": choice.get("description", ""),
                        "story_impact": choice.get("story_impact", "medium"),
                        "choice_type": choice.get("choice_type", "action"),
                        "is_selected": choice.get("is_selected", False),
                        "selected_at": choice.get("selected_at"),
                        "branch_id": choice["branch_id"],
                        "chapter_number": choice["chapter_number"]
                    }
                    tree_data["edges"].append(edge_data)
        
        # Calculate Y positions for branches (spread them vertically)
        main_branch_y = 0
        branch_y_offset = 300
        current_y = main_branch_y
        
        for branch in tree_data["branches"]:
            if branch["is_main"]:
                branch_y = main_branch_y
            else:
                current_y += branch_y_offset
                branch_y = current_y
            
            # Update node positions for this branch
            for node in tree_data["nodes"]:
                if node["branch_id"] == branch["id"]:
                    node["position"]["y"] = branch_y
        
        # Add metadata
        tree_data["metadata"] = {
            "total_branches": len(tree_data["branches"]),
            "total_chapters": len(tree_data["nodes"]),
            "total_choices": len(tree_data["edges"]),
            "main_branch_id": next((b["id"] for b in tree_data["branches"] if b["is_main"]), None)
        }
        
        logger.info(f"✅ Story tree generated: {tree_data['metadata']['total_branches']} branches, {tree_data['metadata']['total_chapters']} chapters, {tree_data['metadata']['total_choices']} choices")
        
        return {
            "success": True,
            "story_id": story_id,
            "tree": tree_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get story tree failed: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get story tree: {str(e)}")

class SetMainBranchInput(BaseModel):
    """Input model for setting a branch as the main branch."""
    story_id: int = Field(..., gt=0, description="ID of the story")
    branch_id: str = Field(..., description="ID of the branch to set as main")

@app.post("/set_main_branch")
async def set_main_branch_endpoint(
    request: SetMainBranchInput,
    user = Depends(get_authenticated_user)
):
    """
    Set a specific branch as the main branch for a story.
    This effectively promotes a branch to be the main storyline for all users.
    """
    try:
        logger.info(f"🎯 SET-MAIN-BRANCH: User {user.id} setting branch {request.branch_id} as main for story {request.story_id}")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", request.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        logger.info(f"✅ SET-MAIN-BRANCH: Story verified: {story.get('story_title', 'Untitled')}")
        
        # Verify the branch exists and belongs to this story
        branch_response = supabase.table("branches").select("*").eq("id", request.branch_id).eq("story_id", request.story_id).execute()
        if not branch_response.data:
            raise HTTPException(status_code=404, detail="Branch not found or does not belong to this story")
        
        branch = branch_response.data[0]
        logger.info(f"✅ SET-MAIN-BRANCH: Branch verified: {branch.get('branch_name', 'Unknown')}")
        
        # Get current main branch
        current_main_response = supabase.table("branches").select("*").eq("story_id", request.story_id).eq("branch_name", "main").execute()
        if not current_main_response.data:
            raise HTTPException(status_code=404, detail="No main branch found for this story")
        
        current_main_branch = current_main_response.data[0]
        logger.info(f"🔍 SET-MAIN-BRANCH: Current main branch: {current_main_branch['id']}")
        
        # If the branch is already the main branch, nothing to do
        if request.branch_id == current_main_branch["id"]:
            logger.info(f"⚠️ SET-MAIN-BRANCH: Branch {request.branch_id} is already the main branch")
            return {
                "success": True,
                "message": "Branch is already the main branch",
                "story_id": request.story_id,
                "branch_id": request.branch_id
            }
        
        # Step 1: Rename current main branch to a backup name
        backup_branch_name = f"main_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🔄 SET-MAIN-BRANCH: Renaming current main branch to: {backup_branch_name}")
        supabase.table("branches").update({"branch_name": backup_branch_name}).eq("id", current_main_branch["id"]).execute()
        
        # Step 2: Set the new branch as main
        logger.info(f"🎯 SET-MAIN-BRANCH: Setting branch {request.branch_id} as main")
        supabase.table("branches").update({"branch_name": "main"}).eq("id", request.branch_id).execute()
        
        # Step 3: Update story's current_chapter to match the new main branch's latest chapter
        chapters_response = supabase.table("Chapters").select("chapter_number").eq("story_id", request.story_id).eq("branch_id", request.branch_id).order("chapter_number", desc=True).limit(1).execute()
        
        if chapters_response.data:
            latest_chapter_num = chapters_response.data[0]["chapter_number"]
            logger.info(f"🔄 SET-MAIN-BRANCH: Updating story current_chapter to {latest_chapter_num}")
            supabase.table("Stories").update({"current_chapter": latest_chapter_num}).eq("id", request.story_id).execute()
        
        logger.info(f"✅ SET-MAIN-BRANCH: Successfully set branch {request.branch_id} as main for story {request.story_id}")
        
        return {
            "success": True,
            "message": f"Branch '{branch.get('branch_name', 'Unknown')}' is now the main branch",
            "story_id": request.story_id,
            "new_main_branch_id": request.branch_id,
            "previous_main_branch_id": current_main_branch["id"],
            "backup_branch_name": backup_branch_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ SET-MAIN-BRANCH: Unexpected error: {str(e)}")
        import traceback
        logger.error(f"❌ SET-MAIN-BRANCH: Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Add this new endpoint after the existing branch endpoints

@app.post("/accept_preview_with_versioning")
async def accept_preview_with_versioning_endpoint(
    request: BranchFromChoiceInput,
    user = Depends(get_authenticated_user)
):
    """
    Accept a preview and create a new version of the chapter, keeping the old version.
    This implements proper versioning where old versions are preserved but hidden.
    """
    try:
        logger.info(f"✅ ACCEPT-PREVIEW-VERSIONING: User accepting preview for chapter {request.chapter_number}")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", request.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        
        # Get the main branch ID
        main_branch_id = await get_main_branch_id(request.story_id)
        
        # Find the selected choice
        choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
        
        available_choices = choices_response.data
        selected_choice = None
        for choice in available_choices:
            if str(choice.get('id')) == str(request.choice_id) or str(choice.get('choice_id')) == str(request.choice_id):
                selected_choice = choice
                break
        
        if not selected_choice:
            raise HTTPException(status_code=400, detail="Invalid choice selected")
        
        # Get the next chapter number
        next_chapter_number = request.chapter_number + 1
        
        # Check if there's an existing active chapter at this number
        existing_chapter_response = supabase.table("Chapters").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("chapter_number", next_chapter_number).eq("is_active", True).execute()
        
        parent_version_id = None
        new_version_number = 1
        
        if existing_chapter_response.data:
            # There's an existing active chapter - we need to version it
            existing_chapter = existing_chapter_response.data[0]
            parent_version_id = existing_chapter["id"]
            new_version_number = existing_chapter["version_number"] + 1
            
            # Deactivate the old version
            logger.info(f"🔄 VERSIONING: Deactivating old version {existing_chapter['version_number']}")
            supabase.table("Chapters").update({"is_active": False}).eq("id", existing_chapter["id"]).execute()
        
        # Generate the new chapter content
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).lte("chapter_number", request.chapter_number).eq("is_active", True).order("chapter_number").execute()
        
        previous_chapters = chapters_response.data
        
        next_chapter_result = await story_service.generate_next_chapter(
            story=story,
            previous_Chapters=previous_chapters,
            selected_choice=selected_choice,
            next_chapter_number=next_chapter_number,
            user_id=user.id
        )
        
        # Save the new version
        chapter_content = next_chapter_result.get("chapter_content") or next_chapter_result.get("content", "")
        chapter_insert_data = {
            "story_id": request.story_id,
            "branch_id": main_branch_id,
            "chapter_number": next_chapter_number,
            "title": next_chapter_result.get("title", f"Chapter {next_chapter_number}"),
            "content": chapter_content,
            "word_count": len(chapter_content.split()),
            "version_number": new_version_number,
            "is_active": True,
            "parent_version_id": parent_version_id,
            "user_choice_id": str(selected_choice.get("id")),
            "user_choice_title": selected_choice.get("title"),
            "user_choice_type": selected_choice.get("choice_type", "action")
        }
        
        chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
        new_chapter_id = chapter_response.data[0]["id"]
        
        # Update choice selections
        supabase.table("story_choices").update({"is_selected": False}).eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("chapter_number", request.chapter_number).execute()
        supabase.table("story_choices").update({
            "is_selected": True,
            "selected_at": datetime.utcnow().isoformat()
        }).eq("id", selected_choice["id"]).execute()
        
        # Save new choices for the generated chapter
        choices = next_chapter_result.get("choices", [])
        if choices:
            # Save choices using helper function
            await save_choices_for_chapter(
                story_id=request.story_id,
                chapter_id=new_chapter_id,
                chapter_number=next_chapter_number,
                choices=choices,
                user_id=user.id,
                branch_id=main_branch_id
            )
        
        # Update story's current_chapter
        supabase.table("Stories").update({"current_chapter": next_chapter_number}).eq("id", request.story_id).execute()
        
        return {
            "success": True,
            "chapter_id": new_chapter_id,
            "chapter_number": next_chapter_number,
            "version_number": new_version_number,
            "message": f"✅ Chapter {next_chapter_number} (v{new_version_number}) created based on choice: '{selected_choice.get('title')}'"
        }
        
    except Exception as e:
        logger.error(f"❌ ACCEPT-PREVIEW-VERSIONING: Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/story/{story_id}/chapter/{chapter_number}/versions")
async def get_chapter_versions_endpoint(
    story_id: int,
    chapter_number: int,
    user = Depends(get_authenticated_user)
):
    """
    Get all versions of a specific chapter, including inactive ones.
    This allows users to see the version history and switch between versions.
    """
    try:
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        # Get the main branch ID
        main_branch_id = await get_main_branch_id(story_id)
        
        # Get all versions of this chapter
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", story_id).eq("branch_id", main_branch_id).eq("chapter_number", chapter_number).order("version_number", desc=True).execute()
        
        versions = []
        for chapter in chapters_response.data:
            version_info = {
                "id": chapter["id"],
                "version_number": chapter["version_number"],
                "title": chapter["title"],
                "content": chapter["content"],
                "is_active": chapter["is_active"],
                "created_at": chapter["created_at"],
                "user_choice_title": chapter.get("user_choice_title"),
                "user_choice_type": chapter.get("user_choice_type"),
                "word_count": chapter.get("word_count", 0)
            }
            versions.append(version_info)
        
        return {
            "success": True,
            "story_id": story_id,
            "chapter_number": chapter_number,
            "versions": versions,
            "active_version": next((v for v in versions if v["is_active"]), None)
        }
        
    except Exception as e:
        logger.error(f"❌ GET-VERSIONS: Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/story/{story_id}/chapter/{chapter_number}/switch_version")
async def switch_chapter_version_endpoint(
    story_id: int,
    chapter_number: int,
    request: Dict[str, int],
    user = Depends(get_authenticated_user)
):
    """
    Switch to a different version of a chapter, making it active and others inactive.
    """
    try:
        version_id = request.get("version_id")
        if not version_id:
            raise HTTPException(status_code=400, detail="version_id is required")
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        # Get the main branch ID
        main_branch_id = await get_main_branch_id(story_id)
        
        # Verify the version exists and belongs to this story/chapter
        chapter_response = supabase.table("Chapters").select("*").eq("id", version_id).eq("story_id", story_id).eq("branch_id", main_branch_id).eq("chapter_number", chapter_number).execute()
        if not chapter_response.data:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Deactivate all versions of this chapter
        supabase.table("Chapters").update({"is_active": False}).eq("story_id", story_id).eq("branch_id", main_branch_id).eq("chapter_number", chapter_number).execute()
        
        # Activate the selected version
        supabase.table("Chapters").update({"is_active": True}).eq("id", version_id).execute()
        
        return {
            "success": True,
            "message": f"✅ Switched to version {chapter_response.data[0]['version_number']} of Chapter {chapter_number}"
        }
        
    except Exception as e:
        logger.error(f"❌ SWITCH-VERSION: Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save_previewed_chapter")
async def save_previewed_chapter_endpoint(
    request: dict = Body(...),
    user = Depends(get_authenticated_user)
):
    """
    Save the provided previewed chapter content as a new version, mark previous as inactive, and save choices.
    """
    try:
        story_id = request.get("story_id")
        chapter_number = request.get("chapter_number")
        choice_id = request.get("choice_id")
        choice_data = request.get("choice_data")
        content = request.get("content")
        choices = request.get("choices", [])

        # Get the next version number for this chapter
        next_version_number = await get_next_chapter_version_number(story_id, chapter_number)
        
        # Mark previous active version as inactive
        await deactivate_previous_chapter_versions(story_id, chapter_number)

        # Insert new chapter version with correct version number
        chapter_insert_data = {
            "story_id": story_id,
            "chapter_number": chapter_number,
            "content": content,
            "is_active": True,
            "version_number": next_version_number,  # Now properly incremented
            "title": f"Chapter {chapter_number}",
        }
        chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
        chapter_id = chapter_response.data[0]["id"]

        # Save choices for this chapter version
        for idx, choice in enumerate(choices):
            choice_data_to_save = {
                "story_id": story_id,
                "chapter_id": chapter_id,
                "chapter_number": chapter_number,
                "choice_id": choice.get("id") or f"choice_{idx+1}",
                "title": choice.get("title"),
                "description": choice.get("description"),
                "story_impact": choice.get("impact") or choice.get("story_impact") or "medium",
                "choice_type": choice.get("type") or choice.get("choice_type") or "action",
                "user_id": user.id if user else None,
                "is_selected": False,
            }
            supabase.table("story_choices").insert(choice_data_to_save).execute()

        return {"success": True, "message": "Previewed chapter saved!", "chapter_id": chapter_id}
    except Exception as e:
        logger.error(f"❌ Error saving previewed chapter: {e}")
        return {"success": False, "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting optimized server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level="debug" if settings.DEBUG else "info"
    )