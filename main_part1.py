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
# Use the correct class name
from services.story_service_with_dna import StoryService  
story_service = StoryService()

from services.embedding_service import embedding_service
from services.cache_service import cache_service

# Import models
from models.story_models import Story, Chapter
from models.chat_models import ChatMessage, ChatResponse

# Keep original imports for compatibility
from story_chatbot import StoryChatbot
from supabase import create_client, Client
from typing import Optional

from chapter_summary import generate_chapter_summary

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
                "title": story.title,  # Fixed: use 'title' instead of 'story_title'
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

@app.get("/story/{story_id}")
async def get_story_details(story_id: int, user = Depends(get_authenticated_user)):
    """Get details for a specific story."""
    try:
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        
        return {
            "id": story["id"],
            "title": story["story_title"],
            "outline": story.get("story_outline", ""),
            "created_at": story["created_at"],
            "genre": story.get("genre", ""),
            "total_chapters": story.get("total_chapters", 0),
            "current_chapter": story.get("current_chapter", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch story {story_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch story details")

@app.get("/story/{story_id}/chapters")
async def get_story_chapters(story_id: int, user = Depends(get_authenticated_user)):
    """Get all chapters for a specific story."""
    try:
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        # Get chapters
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", story_id).eq("is_active", True).order("chapter_number").execute()
        
        chapters = []
        for chapter in chapters_response.data or []:
            chapters.append({
                "id": chapter["id"],
                "chapter_number": chapter["chapter_number"],
                "title": chapter.get("title", f"Chapter {chapter['chapter_number']}"),
                "content": chapter["content"],
                "summary": chapter.get("summary", ""),
                "created_at": chapter["created_at"],
                "word_count": len(chapter["content"].split()) if chapter["content"] else 0
            })
        
        return {"chapters": chapters}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch chapters for story {story_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch story chapters")

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

# Updated for DSPy summary-based outline, July 2024
@app.post("/lc_generate_outline")
async def generate_outline_endpoint(story: StoryInput, user = Depends(get_authenticated_user_optional)):
    """Generate a cinematic story summary with genre and tone using DSPy (no chapter breakdown)."""
    import traceback
    try:
        logger.info(f"[OUTLINE] Received request: idea='{story.idea[:50]}', user={'None' if not user else user.id}")
        from lc_book_generator_prompt import generate_book_outline_json
        user_info = f"user {user.id}" if user else "anonymous user"
        logger.info(f"[OUTLINE] Generating outline for {user_info}, idea: {story.idea[:50]}...")
        result = generate_book_outline_json(story.idea)
        logger.info(f"[OUTLINE] Result from generate_book_outline_json: {result}")
        if not result or not result.get("summary"):
            logger.error(f"[OUTLINE] No summary returned from outline generator.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Outline generation failed: No summary returned."
            )
        # Return only the new summary-based output
        logger.info(f"[OUTLINE] Returning summary, genre, tone for idea: {story.idea[:50]}")
        return {
            "success": True,
            "summary": result["summary"],
            "genre": result["genre"],
            "tone": result["tone"],
            "title": result.get("book_title", ""),  # Include the generated title
            "chapters": result["chapters"],  # â† This might be missing!
            "reflection": result.get("reflection", ""),
            "is_optimized": result.get("is_optimized", False),
        }
    except Exception as e:
        logger.error(f"[OUTLINE] Outline generation failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions to extract characters and locations from chapters
def extract_characters_from_chapters(chapters):
    """Extract unique characters from chapter data."""
    characters = []
    seen_names = set()
    
    if not chapters:
        return characters
    
    for chapter in chapters:
        # Extract from character_development field
        char_dev = chapter.get("character_development", "")
        if char_dev:
            # Simple extraction - look for character names
            # This is a basic implementation - could be enhanced with NLP
            words = char_dev.split()
            for word in words:
                if word.endswith("'s") and len(word) > 3:  # Possessive form like "Alex's"
                    name = word[:-2]  # Remove 's
                    if name not in seen_names and name[0].isupper():
                        characters.append({"name": name, "role": "Character"})
                        seen_names.add(name)
    
    return characters

def extract_locations_from_chapters(chapters):
    """Extract unique locations from chapter data."""
    locations = []
    seen_names = set()
    
    if not chapters:
        return locations
    
    for chapter in chapters:
        # Extract from setting field
        setting = chapter.get("setting", "")
        if setting:
            # Simple extraction - look for location names
            # This is a basic implementation - could be enhanced with NLP
            words = setting.split()
            for word in words:
                if word[0].isupper() and len(word) > 2 and word not in seen_names:
                    # Basic location detection (could be improved)
                    if any(location_word in word.lower() for location_word in ["room", "house", "street", "city", "gallery", "cafe", "apartment", "building"]):
                        locations.append({"name": word, "description": f"Location from {chapter.get('title', 'chapter')}"})
                        seen_names.add(word)
    
    return locations

# New endpoint for saving edited outline
class SaveOutlineInput(BaseModel):
    # New format from enhanced outline generator
    summary: str = Field(..., min_length=50, description="Story summary from outline generator")
    genre: Optional[str] = None
    tone: Optional[str] = None
    title: Optional[str] = None  # User-edited story title
    chapters: List[Dict[str, Any]] = Field(default_factory=list, description="Chapter breakdown from outline generator")
    reflection: Optional[str] = None
    is_optimized: Optional[bool] = False
    
    # Optional: Allow old format for backward compatibility
    outline_json: Optional[Dict[str, Any]] = None
    formatted_text: Optional[str] = None

@app.post("/save_outline")
async def save_outline_endpoint(
    outline_data: SaveOutlineInput,
    user = Depends(get_authenticated_user)
):
    """Save the user-edited outline to database."""
    try:
        logger.info(f"ðŸ’¾ Saving enhanced outline to database for user {user.id}...")
        
        # Handle new format (enhanced outline generator)
        if outline_data.summary:
            logger.info("ðŸ“ Using new enhanced outline format")
            
            # Use user-provided title or create one from the summary
            story_title = outline_data.title if outline_data.title else outline_data.summary.split('.')[0][:50] + "..."
            
            # Prepare story data for database save - mapped to existing schema
            story_data = {
                "user_id": user.id,
                "story_title": story_title,
                "story_outline": outline_data.summary,  # Use summary as outline
                "total_chapters": len(outline_data.chapters) if outline_data.chapters else 1,
                "current_chapter": 0,  # 0 = outline only, no Chapters written yet
                
                # Map to existing fields
                "genre": outline_data.genre,
                "style": outline_data.genre,  # Map genre to style
                "language": "English",
                "tags": json.dumps([outline_data.genre.lower()]) if outline_data.genre else json.dumps([]),
                
                # Store full response in outline_json
                "outline_json": json.dumps({
                    "summary": outline_data.summary,
                    "genre": outline_data.genre,
                    "tone": outline_data.tone,
                    "chapters": outline_data.chapters,
                    "reflection": outline_data.reflection,
                    "is_optimized": outline_data.is_optimized,
                    "title": story_title
                }),
                
                # Extract characters and locations from chapters
                "main_characters": json.dumps(extract_characters_from_chapters(outline_data.chapters)),
                "key_locations": json.dumps(extract_locations_from_chapters(outline_data.chapters)),
            }
            
        # Handle old format (backward compatibility)
        elif outline_data.outline_json and outline_data.formatted_text:
            logger.info("ðŸ“ Using legacy outline format")
            
            outline_json = outline_data.outline_json
            
            # Regenerate formatted text with the updated character names
            from lc_book_generator_prompt import format_json_to_display_text
            formatted_text = format_json_to_display_text(outline_json)
            
            logger.info(f"âœ… Regenerated formatted text with updated character names")
            
            # Prepare story data for database save - legacy format
            story_data = {
                "user_id": user.id,
                "story_title": outline_json.get("book_title", "Untitled Story"),
                "story_outline": formatted_text,  # Save the regenerated formatted text
                "total_chapters": outline_json.get("estimated_total_chapters", 1),
                "current_chapter": 0,  # 0 = outline only, no Chapters written yet
                
                # Map exact JSON fields to database columns
                "outline_json": json.dumps(outline_json),  # Store full JSON as text
                "genre": outline_json.get("genre"),
                "style": outline_json.get("style"),
                "language": outline_json.get("language", "English"),
                "tags": json.dumps(outline_json.get("tags", [])),  # Convert array to JSON string
                "main_characters": json.dumps(outline_json.get("main_characters", [])),  # JSONB column - convert to JSON string
                "key_locations": json.dumps(outline_json.get("key_locations", [])),  # JSONB column - convert to JSON string
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid outline data format")
        
        # Remove None values to avoid database errors
        story_data = {k: v for k, v in story_data.items() if v is not None and v != [] and v != ""}
        
        logger.info(f"Saving outline to database with fields: {list(story_data.keys())}")
        
        try:
            # Try saving to database
            story_response = supabase.table("Stories").insert(story_data).execute()
            story_id = story_response.data[0]["id"]
            logger.info(f"âœ… Outline saved successfully with story_id: {story_id}")

            # --- OUTLINE SAVED SUCCESSFULLY, BUT DON'T AUTO-GENERATE CHAPTER 1 ---
            # The user should explicitly click "Generate Chapter 1" to create chapters
            logger.info(f"âœ… Outline saved successfully. User can now generate Chapter 1 manually.")
            
            return {
                "success": True,
                "message": "Outline saved successfully!",
                "story_id": story_id,
                "story_title": story_data.get("story_title", "Untitled Story"),
                "updated_formatted_text": outline_data.summary if outline_data.summary else outline_data.formatted_text  # Return the summary/text for frontend
            }
            
        except Exception as save_error:
            logger.error(f"âŒ Database save failed: {save_error}")
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
        logger.info(f"ðŸŽ¯ Generating choices for Chapter {choice_input.current_chapter_num + 1}, Story {choice_input.story_id}")
        
        # CRITICAL: Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", choice_input.story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            logger.error(f"âŒ STORY ISOLATION: Story {choice_input.story_id} not found for user {user.id}")
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story_data = story_response.data[0]
        story_outline = story_data.get("story_outline", "")
        
        logger.info(f"âœ… Story verified: {story_data.get('story_title', 'Untitled')}")
        
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
                logger.info(f"âœ… Saved {len(choice_records)} choices to database for story {choice_input.story_id}")
                
                # CRITICAL FIX: Update choices with real database IDs
                for i, choice in enumerate(choices):
                    database_record = choices_response.data[i]
                    choice["id"] = database_record["id"]  # Use real database ID
                    choice["choice_id"] = database_record["id"]  # Use real database ID
                    choice["database_id"] = database_record["id"]  # Keep reference
                    
                logger.info(f"ðŸ”§ Updated choices with database IDs: {[c['id'] for c in choices]}")
            else:
                logger.warning("âš ï¸ Failed to save choices to database")
        except Exception as e:
            logger.error(f"âŒ Error saving choices: {e}")
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
        logger.error(f"âŒ Generate choices failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate choices: {str(e)}")

class SelectChoiceInput(BaseModel):
    story_id: int = Field(..., gt=0, description="ID of the story")
    choice_id: Union[str, int] = Field(..., description="ID of the selected choice")
    choice_data: Dict[str, Any] = Field(..., description="The full choice object that was selected")
    next_chapter_num: int = Field(..., ge=1, description="Next chapter number to generate")

@app.post("/generate_chapter_with_choice")
async def generate_chapter_with_choice_endpoint(request: SelectChoiceInput, user = Depends(get_authenticated_user)):
    logger.info(f"ðŸ”„ Generate chapter with choice request received")
    logger.info(f"ðŸ“Š Request data: story_id={request.story_id}, next_chapter_num={request.next_chapter_num}, choice_id={request.choice_id}")
    logger.info(f"ðŸ“Š Request choice_id type: {type(request.choice_id)}")
    logger.info(f"ðŸ“Š Request choice_id value: '{request.choice_id}'")
    
    try:
        # User is already authenticated via dependency injection
        user_id = user.id
        logger.info(f"ðŸ‘¤ User authenticated: {user_id}")

        # First, fetch all available choices for this chapter to validate
        current_chapter_number = request.next_chapter_num - 1  # Choices are for the previous chapter
        logger.info(f"ðŸ” Fetching available choices for story {request.story_id}, chapter {current_chapter_number}")
        choices_response = supabase.table('story_choices').select('*').eq('story_id', request.story_id).eq('user_id', user_id).eq('chapter_number', current_chapter_number).execute()
        
        available_choices = choices_response.data
        logger.info(f"ðŸ“‹ Available choices count: {len(available_choices)}")
        
        for i, choice in enumerate(available_choices):
            logger.info(f"ðŸ“‹ Choice {i+1}: id={choice.get('id')}, choice_id={choice.get('choice_id')}, title='{choice.get('choice_title', 'No title')}'")
            logger.info(f"ðŸ“‹ Choice {i+1} types: id type={type(choice.get('id'))}, choice_id type={type(choice.get('choice_id'))}")

        # Try to find the selected choice by matching with both id and choice_id fields
        selected_choice = None
        
        # First try to match with 'id' field (database primary key)
        for choice in available_choices:
            if str(choice.get('id')) == str(request.choice_id):
                selected_choice = choice
                logger.info(f"âœ… Found choice by 'id' field: {choice}")
                break
        
        # If not found, try to match with 'choice_id' field (user-facing identifier)
        if not selected_choice:
            for choice in available_choices:
                if str(choice.get('choice_id')) == str(request.choice_id):
                    selected_choice = choice
                    logger.info(f"âœ… Found choice by 'choice_id' field: {choice}")
                    break
        
        if not selected_choice:
            logger.error(f"âŒ No choice found matching request.choice_id='{request.choice_id}'")
            logger.error(f"âŒ Available choice IDs: {[choice.get('id') for choice in available_choices]}")
            logger.error(f"âŒ Available choice_ids: {[choice.get('choice_id') for choice in available_choices]}")
            raise HTTPException(status_code=400, detail="Invalid choice selected")

        logger.info(f"ðŸŽ¯ Selected choice found: {selected_choice}")
        
        # Mark this choice as selected in the database
        logger.info(f"ðŸ’¾ Marking choice as selected in database")
        from datetime import datetime
        update_response = supabase.table('story_choices').update({
            'is_selected': True,
            'selected_at': datetime.utcnow().isoformat()
        }).eq('id', selected_choice['id']).execute()

        # Get the story details
        logger.info(f"ðŸ“– Fetching story details for story_id={request.story_id}")
        story_response = supabase.table('Stories').select('*').eq('id', request.story_id).eq('user_id', user_id).single().execute()
        story = story_response.data
        logger.info(f"ðŸ“– Story retrieved: title='{story.get('story_title', 'No title')}'")

        # Get only ACTIVE chapters up to the previous chapter (exclude current chapter versions)
        max_context_chapter = request.next_chapter_num - 1
        logger.info(f"ðŸ“š Fetching ACTIVE chapters up to chapter {max_context_chapter} for story_id={request.story_id}")
        Chapters_response = supabase.table('Chapters').select('*').eq('story_id', request.story_id).eq('is_active', True).lte('chapter_number', max_context_chapter).order('chapter_number').execute()
        previous_Chapters = Chapters_response.data
        logger.info(f"ðŸ“š Active previous chapters count: {len(previous_Chapters)} (chapters 1-{max_context_chapter})")

        # Generate the next chapter
        logger.info(f"âš¡ Starting chapter generation process")
        next_chapter_number = request.next_chapter_num
        logger.info(f"ðŸ“ Next chapter number will be: {next_chapter_number}")

        # Use the story service to generate the next chapter
        try:
            logger.info(f"ðŸŽ¯ Generating Chapter {next_chapter_number} with choice: '{selected_choice.get('title', 'Unknown')}'")
            logger.info(f"ðŸ“ LLM Input: Story='{story['story_title']}', Previous Chapters={len(previous_Chapters)}, Choice='{selected_choice.get('title', 'Unknown')}'")
            
            next_chapter_result = await story_service.generate_next_chapter_with_dna(
                story=story,
                previous_Chapters=previous_Chapters,
                selected_choice=selected_choice,
                next_chapter_number=next_chapter_number,
                user_id=user_id
            )
            logger.info(f"âœ… Chapter {next_chapter_number} generated successfully")
            
        except Exception as generation_error:
            logger.error(f"âŒ Chapter generation failed: {str(generation_error)}")
            logger.error(f"âŒ Generation error type: {type(generation_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate next chapter: {str(generation_error)}")

        logger.info(f"ðŸŽ‰ Chapter generation process completed successfully")

        # --- SAVE GENERATED CHAPTER TO DATABASE ---
        try:
            logger.info(f"ðŸ’¾ Saving generated chapter {next_chapter_number} to database...")
            
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
                logger.error(f"âŒ DATABASE ERROR: Insert returned no data")
                raise HTTPException(status_code=500, detail="Failed to save generated chapter")
            chapter_id = chapter_response.data[0]["id"]
            logger.info(f"âœ… Chapter saved with ID: {chapter_id}")
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
                        logger.info(f"âœ… Chapter {next_chapter_number} summary saved and verified in database")
                    else:
                        logger.error(f"âŒ Chapter {next_chapter_number} summary update may have failed")
                else:
                    logger.error(f"âŒ Failed to generate summary for chapter {next_chapter_number}")
            except Exception as summary_error:
                import traceback
        except Exception as db_error:
            logger.error(f"âŒ DATABASE INSERT FAILED: {str(db_error)}")
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
            logger.error(f"âŒ Failed to save choices: {str(choice_error)}")
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
        logger.info(f"ðŸš€ Returning response to frontend: success={response_payload.get('success')}, chapter_number={response_payload.get('chapter_number')}, choices_count={len(response_payload.get('choices', []))}")
        return response_payload

    except HTTPException:
        logger.error(f"âŒ HTTP Exception occurred, re-raising")
        raise
    except Exception as e:
        logger.error(f"âŒ Unexpected error in generate_chapter_with_choice: {str(e)}")
        logger.error(f"âŒ Error type: {type(e)}")
        import traceback
        logger.error(f"âŒ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/story/{story_id}/choice_history")
async def get_choice_history_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """Get the complete choice history for a story showing all paths taken and not taken."""
    try:
        logger.info(f"ðŸ“š Getting choice history for story {story_id}")
        
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
        
        logger.info(f"âœ… Retrieved choice history for {len(history_list)} Chapters")
        
        return {
            "success": True,
            "story_id": story_id,
            "choice_history": history_list,
            "total_chapters_with_choices": len(history_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"âŒ Get choice history failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get choice history: {str(e)}")

@app.get("/chapter/{chapter_id}/choices")
async def get_choices_for_chapter_endpoint(
    chapter_id: int,
    user = Depends(get_authenticated_user)
):
    """
    Get all choices for a specific chapter version (by chapter_id), always returning all options.
    """
    try:
        # Fetch all choices for this chapter_id
        choices_response = supabase.table("story_choices").select("*").eq("chapter_id", chapter_id).execute()
        choices = choices_response.data or []
        return {"success": True, "chapter_id": chapter_id, "choices": choices, "total_choices": len(choices)}
    except Exception as e:
        logger.error(f"âŒ Error fetching choices for chapter {chapter_id}: {e}")
        return {"success": False, "detail": str(e)}

@app.post("/lc_generate_chapter")
async def generate_chapter_endpoint(chapter: ChapterInput, user = Depends(get_authenticated_user_optional)):
    """Generate story chapter from either text or JSON outline."""
    logger.info(f"ðŸ“– Starting Chapter {chapter.chapter_number} generation...")
    logger.info(f"Outline length: {len(chapter.outline)} characters")
    
    # STEP 1: Check if Chapter 1 already exists for this story
    if chapter.chapter_number == 1 and chapter.story_id:
        logger.info(f"ðŸ” Checking if Chapter 1 already exists for story {chapter.story_id}...")
        try:
            existing_chapter = supabase.table("Chapters").select("id, content, title").eq("story_id", chapter.story_id).eq("chapter_number", 1).eq("is_active", True).execute()
            if existing_chapter.data and len(existing_chapter.data) > 0:
                chapter_id = existing_chapter.data[0]["id"]
                logger.info(f"âœ… Chapter 1 already exists with ID: {chapter_id}")
                
                # Fetch choices for this chapter
                choices_response = supabase.table("story_choices").select("*").eq("chapter_id", chapter_id).execute()
                choices = choices_response.data if choices_response.data else []
                
                logger.info(f"ðŸ“– Returning existing Chapter 1 with {len(choices)} choices")
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
                        "already_saved": True  # Flag to prevent frontend from saving again
                    }
                }
        except Exception as e:
            logger.warning(f"âš ï¸ Error checking for existing Chapter 1: {e}")
            # Continue with generation if check fails
    
    try:
        from enhanced_chapter_generator import EnhancedChapterGenerator
        generator = EnhancedChapterGenerator()
        
        # Parse the outline to extract structured data
        try:
            # Try to parse as JSON first (from DSPy)
            import json
            outline_json = json.loads(chapter.outline)
            logger.info("âœ… Outline detected as JSON from DSPy")
            
            # Extract data for enhanced generator
            story_summary = outline_json.get("summary", "")
            genre = outline_json.get("genre", "General Fiction")
            tone = outline_json.get("tone", "Engaging")
            chapters_data = outline_json.get("chapters", [])
            
            # Get specific chapter data
            target_chapter = None
            for ch in chapters_data:
                if ch.get("chapter_number") == chapter.chapter_number:
                    target_chapter = ch
                    break
            
            if not target_chapter:
                raise ValueError(f"Chapter {chapter.chapter_number} not found in outline")
                
            logger.info(f"ðŸŽ¯ Found chapter data: {target_chapter.get('title', 'Untitled')}")
            
            # Generate with enhanced CoT system
            result = generator.generate_chapter_from_outline(
                story_summary=story_summary,
                chapter_data=target_chapter,
                genre=genre,
                tone=tone
            )
            
        except json.JSONDecodeError:
            # Fallback: treat as text outline (legacy support)
            logger.info("ðŸ“„ Outline detected as text (legacy)")
            
            # For text outlines, create minimal chapter data
            chapter_data = {
                "chapter_number": chapter.chapter_number,
                "title": f"Chapter {chapter.chapter_number}",
                "key_events": ["Chapter events from outline"],
                "character_development": "Character development",
                "setting": "Story setting",
                "cliffhanger": "Chapter ending"
            }
            
            # Use first 200 chars as summary
            story_summary = chapter.outline[:200] + "..." if len(chapter.outline) > 200 else chapter.outline
            
            result = generator.generate_chapter_from_outline(
                story_summary=story_summary,
                chapter_data=chapter_data,
                genre="General Fiction",
                tone="Engaging"
            )
        
        logger.info(f"âœ… Chapter {chapter.chapter_number} generation completed!")
        
        # Handle new enhanced response structure
        if result.get("success"):
            chapter_content = result.get("chapter_content", "")
            choices = result.get("choices", [])
            # reasoning = result.get("reasoning", {})  # No longer returned
            # quality_metrics = result.get("quality_metrics", {})  # No longer returned
            
            logger.info(f"ðŸ“Š Generated: {len(chapter_content)} chars, {len(choices)} choices")
            # logger.info(f"ðŸ§  CoT reasoning: {bool(reasoning)}")
            # logger.info(f"ðŸ“ˆ Quality metrics: {bool(quality_metrics)}")
            
            # Validate chapter content
            if not chapter_content or len(chapter_content.strip()) < 50:
                logger.error(f"âŒ Chapter content too short: {len(chapter_content)} characters")
                raise HTTPException(status_code=500, detail="Generated chapter content is too short or empty")

            # --- SAVE CHAPTER 1 AND CHOICES TO DATABASE IMMEDIATELY ---
