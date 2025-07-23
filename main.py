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
        logger.info(f"💾 Saving enhanced outline to database for user {user.id}...")
        
        # Handle new format (enhanced outline generator)
        if outline_data.summary:
            logger.info("📝 Using new enhanced outline format")
            
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
            logger.info("📄 Using legacy outline format")
            
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
        logger.info("Generating choices for Chapter {} in Story {}".format(choice_input.current_chapter_num + 1, choice_input.story_id))
        
        # CRITICAL: Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", choice_input.story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            logger.error("âŒ STORY ISOLATION: Story {} not found for user {}".format(choice_input.story_id, user.id))
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story_data = story_response.data[0]
        story_outline = story_data.get("story_outline", "")
        
        logger.info("âœ… Story verified: {}".format(story_data.get('story_title', 'Untitled')))
        
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
                logger.info("âœ… Saved {} choices to database for story {}".format(len(choice_records), choice_input.story_id))
                
                # CRITICAL FIX: Update choices with real database IDs
                for i, choice in enumerate(choices):
                    database_record = choices_response.data[i]
                    choice["id"] = database_record["id"]  # Use real database ID
                    choice["choice_id"] = database_record["id"]  # Use real database ID
                    choice["database_id"] = database_record["id"]  # Keep reference
                    
                logger.info("âœ… Updated choices with database IDs: {}".format([c['id'] for c in choices]))
            else:
                logger.warning("âš ï¸ Failed to save choices to database")
        except Exception as e:
            logger.error("âŒ Error saving choices: {}".format(e))
            # Continue anyway - don't break the user experience
 
        return {
            "success": True,
            "story_id": choice_input.story_id,  # CRITICAL: Include for frontend validation
            "chapter_number": choice_input.current_chapter_num,
            "choices": choices,
            "message": "Generated {} choices for Chapter {}".format(len(choices), choice_input.current_chapter_num + 1)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("âŒ Generate choices failed: {}".format(e))
        raise HTTPException(status_code=500, detail="Failed to generate choices: {}".format(str(e)))

class SelectChoiceInput(BaseModel):
    story_id: int = Field(..., gt=0, description="ID of the story")
    choice_id: Union[str, int] = Field(..., description="ID of the selected choice")
    choice_data: Dict[str, Any] = Field(..., description="The full choice object that was selected")
    next_chapter_num: int = Field(..., ge=1, description="Next chapter number to generate")

@app.post("/generate_chapter_with_choice")
async def generate_chapter_with_choice_endpoint(request: SelectChoiceInput, user = Depends(get_authenticated_user)):
    logger.info("Generate chapter with choice request received")
    logger.info("Request data: story_id={}, next_chapter_num={}, choice_id={}".format(request.story_id, request.next_chapter_num, request.choice_id))
    logger.info("Request choice_id type: {}".format(type(request.choice_id)))
    logger.info("Request choice_id value: '{}'".format(request.choice_id))
    
    try:
        # User is already authenticated via dependency injection
        user_id = user.id
        logger.info("User authenticated: {}".format(user_id))

        # First, fetch all available choices for this chapter to validate
        current_chapter_number = request.next_chapter_num - 1  # Choices are for the previous chapter
        logger.info("Fetching available choices for story {}, chapter {}".format(request.story_id, current_chapter_number))
        choices_response = supabase.table('story_choices').select('*').eq('story_id', request.story_id).eq('user_id', user_id).eq('chapter_number', current_chapter_number).execute()
        
        available_choices = choices_response.data
        logger.info("Available choices count: {}".format(len(available_choices)))
        
        for i, choice in enumerate(available_choices):
            logger.info("Choice {}: id={}, choice_id={}, title='{}'".format(i+1, choice.get('id'), choice.get('choice_id'), choice.get('choice_title', 'No title')))
            logger.info("Choice {} types: id type={}, choice_id type={}".format(i+1, type(choice.get('id')), type(choice.get('choice_id'))))

        # Try to find the selected choice by matching with both id and choice_id fields
        selected_choice = None
        
        # First try to match with 'id' field (database primary key)
        for choice in available_choices:
            if str(choice.get('id')) == str(request.choice_id):
                selected_choice = choice
                logger.info("Found choice by 'id' field: {}".format(choice))
                break
        
        # If not found, try to match with 'choice_id' field (user-facing identifier)
        if not selected_choice:
            for choice in available_choices:
                if str(choice.get('choice_id')) == str(request.choice_id):
                    selected_choice = choice
                    logger.info("Found choice by 'choice_id' field: {}".format(choice))
                    break
        
        if not selected_choice:
            logger.error("âŒ No choice found matching request.choice_id='{}'".format(request.choice_id))
            logger.error("âŒ Available choice IDs: {}".format([choice.get('id') for choice in available_choices]))
            logger.error("âŒ Available choice_ids: {}".format([choice.get('choice_id') for choice in available_choices]))
            raise HTTPException(status_code=400, detail="Invalid choice selected")

        logger.info("Selected choice found: {}".format(selected_choice))
        
        # Mark this choice as selected in the database
        logger.info("Marking choice as selected in database")
        from datetime import datetime
        update_response = supabase.table('story_choices').update({
            'is_selected': True,
            'selected_at': datetime.utcnow().isoformat()
        }).eq('id', selected_choice['id']).execute()

        # Get the story details
        logger.info("Fetching story details for story_id={}".format(request.story_id))
        story_response = supabase.table('Stories').select('*').eq('id', request.story_id).eq('user_id', user_id).single().execute()
        story = story_response.data
        logger.info("Story retrieved: title='{}'".format(story.get('story_title', 'No title')))

        # Get only ACTIVE chapters up to the previous chapter (exclude current chapter versions)
        max_context_chapter = request.next_chapter_num - 1
        logger.info("Fetching ACTIVE chapters up to chapter {} for story_id={}".format(max_context_chapter, request.story_id))
        Chapters_response = supabase.table('Chapters').select('*').eq('story_id', request.story_id).eq('is_active', True).lte('chapter_number', max_context_chapter).order('chapter_number').execute()
        previous_Chapters = Chapters_response.data
        logger.info("Active previous chapters count: {} (chapters 1-{})".format(len(previous_Chapters), max_context_chapter))

        # Generate the next chapter
        logger.info("Next chapter number will be: {}".format(request.next_chapter_num))

        # Use the story service to generate the next chapter
        try:
            logger.info("Generating Chapter {} with choice: '{}'".format(request.next_chapter_num, selected_choice.get('title', 'Unknown')))
            logger.info("LLM Input: Story='{}', Previous Chapters={}, Choice='{}'".format(story['story_title'], len(previous_Chapters), selected_choice.get('title', 'Unknown')))
            
            next_chapter_result = await story_service.generate_next_chapter_with_dna(
                story=story,
                previous_Chapters=previous_Chapters,
                selected_choice=selected_choice,
                next_chapter_number=request.next_chapter_num,
                user_id=user_id
            )
            logger.info("Chapter generation process completed successfully")
            
        except Exception as generation_error:
            logger.error("Chapter generation failed: {}".format(str(generation_error)))
            logger.error("Generation error type: {}".format(type(generation_error)))
            raise HTTPException(status_code=500, detail="Failed to generate next chapter: {}".format(str(generation_error)))

        logger.info("Chapter generation process completed successfully")

        # --- SAVE GENERATED CHAPTER TO DATABASE ---
        try:
            logger.info("Saving generated chapter {} to database...".format(request.next_chapter_num))
            
            # Get the next version number for this chapter
            next_version_number = await get_next_chapter_version_number(request.story_id, request.next_chapter_num, supabase)
            
            # Deactivate previous versions of this chapter
            await deactivate_previous_chapter_versions(request.story_id, request.next_chapter_num, supabase)
            
            # Use the correct key for chapter content
            chapter_text = next_chapter_result.get("chapter_content") or next_chapter_result.get("chapter") or next_chapter_result.get("content", "")
            chapter_insert_data = {
                "story_id": request.story_id,
                "chapter_number": request.next_chapter_num,
                "title": next_chapter_result.get("title") or f"Chapter {request.next_chapter_num}",
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
                logger.error("âŒ DATABASE ERROR: Insert returned no data")
                raise HTTPException(status_code=500, detail="Failed to save generated chapter")
            chapter_id = chapter_response.data[0]["id"]
            logger.info("âœ… Chapter saved with ID: {}".format(chapter_id))
            # --- GENERATE AND SAVE CHAPTER SUMMARY ---
            
            try:
                from chapter_summary import generate_chapter_summary
                story_outline = story.get("story_outline", "") if 'story' in locals() else ""

                summary_result = generate_chapter_summary(
                    chapter_content=chapter_text,
                    chapter_number=request.next_chapter_num,
                    story_context=story_outline,
                    story_title=story.get("story_title", "Untitled Story") if 'story' in locals() else "Untitled Story"
                )

                if summary_result["success"]:
                    summary_text = summary_result["summary"]
                    
                    update_response = supabase.table("Chapters").update({"summary": summary_text}).eq("id", chapter_id).execute()
                    
                    # Verify the update worked
                    verify_response = supabase.table("Chapters").select("summary").eq("id", chapter_id).execute()
                    if verify_response.data and verify_response.data[0].get("summary"):
                        logger.info("âœ… Chapter {} summary saved and verified in database".format(request.next_chapter_num))
                    else:
                        logger.error("âŒ Chapter {} summary update may have failed".format(request.next_chapter_num))
                else:
                    logger.error("âŒ Failed to generate summary for chapter {}".format(request.next_chapter_num))
            except Exception as summary_error:
                import traceback
        except Exception as db_error:
            logger.error("âŒ DATABASE INSERT FAILED: {}".format(str(db_error)))
            raise HTTPException(status_code=500, detail="Database insert failed: {}".format(str(db_error)))

        # --- SAVE GENERATED CHOICES FOR THE NEW CHAPTER ---
        try:
            choices = next_chapter_result.get("choices", [])
            if choices:
                await save_choices_for_chapter(
                    story_id=request.story_id,
                    chapter_id=chapter_id,
                    chapter_number=request.next_chapter_num,
                    choices=choices,
                    user_id=user_id,
                    supabase=supabase
                )
        except Exception as choice_error:
            logger.error("âŒ Failed to save choices: {}".format(str(choice_error)))
            # Continue anyway - don't break the user experience
        
        # Update story's current_chapter
        supabase.table("Stories").update({"current_chapter": request.next_chapter_num}).eq("id", request.story_id).execute()
        
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
        logger.info("Returning response to frontend: success={}, chapter_number={}, choices_count={}".format(response_payload.get('success'), response_payload.get('chapter_number'), len(response_payload.get('choices', []))))
        return response_payload

    except HTTPException:
        logger.error("âŒ HTTP Exception occurred, re-raising")
        raise
    except Exception as e:
        logger.error("âŒ Unexpected error in generate_chapter_with_choice: {}".format(str(e)))
        logger.error("Error type: {}".format(type(e)))
        import traceback
        logger.error("âŒ Full traceback: {}".format(traceback.format_exc()))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/story/{story_id}/choice_history")
async def get_choice_history_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """Get the complete choice history for a story showing all paths taken and not taken."""
    try:
        logger.info("Getting choice history for story {}".format(story_id))
        
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
        
        logger.info("Retrieved choice history for {} Chapters".format(len(history_list)))
        
        return {
            "success": True,
            "story_id": story_id,
            "choice_history": history_list,
            "total_chapters_with_choices": len(history_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Get choice history failed: {}".format(e))
        raise HTTPException(status_code=500, detail="Failed to get choice history: {}".format(str(e)))

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
        logger.error("Error fetching choices for chapter {}: {}".format(chapter_id, e))
        return {"success": False, "detail": str(e)}

@app.post("/lc_generate_chapter")
async def generate_chapter_endpoint(chapter: ChapterInput, user = Depends(get_authenticated_user_optional)):
    """Generate story chapter from either text or JSON outline."""
    logger.info("Starting Chapter {} generation...".format(chapter.chapter_number))
    logger.info("Outline length: {} characters".format(len(chapter.outline)))
    
    # STEP 1: Check if Chapter 1 already exists for this story
    if chapter.chapter_number == 1 and chapter.story_id:
        logger.info("Checking if Chapter 1 already exists for story {}...".format(chapter.story_id))
        try:
            existing_chapter = supabase.table("Chapters").select("id, content, title").eq("story_id", chapter.story_id).eq("chapter_number", 1).eq("is_active", True).execute()
            if existing_chapter.data and len(existing_chapter.data) > 0:
                chapter_id = existing_chapter.data[0]["id"]
                logger.info("Chapter 1 already exists with ID: {}".format(chapter_id))
                
                # Fetch choices for this chapter
                choices_response = supabase.table("story_choices").select("*").eq("chapter_id", chapter_id).execute()
                choices = choices_response.data if choices_response.data else []
                
                logger.info("Returning existing Chapter 1 with {} choices".format(len(choices)))
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
            logger.warning("Error checking for existing Chapter 1: {}".format(e))
            # Continue with generation if check fails
    
    try:
        from enhanced_chapter_generator import EnhancedChapterGenerator
        generator = EnhancedChapterGenerator()
        
        # Parse the outline to extract structured data
        try:
            # Try to parse as JSON first (from DSPy)
            import json
            outline_json = json.loads(chapter.outline)
            logger.info("Outline detected as JSON from DSPy")
            
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
                raise ValueError("Chapter {} not found in outline".format(chapter.chapter_number))
                
            logger.info("Found chapter data: {}".format(target_chapter.get('title', 'Untitled')))
            
            # Generate with enhanced CoT system
            result = generator.generate_chapter_from_outline(
                story_summary=story_summary,
                chapter_data=target_chapter,
                genre=genre,
                tone=tone
            )
            
        except json.JSONDecodeError:
            # Fallback: treat as text outline (legacy support)
            logger.info("Outline detected as text (legacy)")
            
            # For text outlines, create minimal chapter data
            chapter_data = {
                "chapter_number": chapter.chapter_number,
                "title": "Chapter {}".format(chapter.chapter_number),
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
        
        logger.info("Chapter {} generation completed!".format(chapter.chapter_number))
        
        # Handle new enhanced response structure
        if result.get("success"):
            chapter_content = result.get("chapter_content", "")
            choices = result.get("choices", [])
            # reasoning = result.get("reasoning", {})  # No longer returned
            # quality_metrics = result.get("quality_metrics", {})  # No longer returned
            
            logger.info("Generated: {} chars, {} choices".format(len(chapter_content), len(choices)))
            # logger.info(f"ðŸ§  CoT reasoning: {bool(reasoning)}")
            # logger.info(f"ðŸ" Quality metrics: {bool(quality_metrics)}")
            
            # Validate chapter content
            if not chapter_content or len(chapter_content.strip()) < 50:
                logger.error("Chapter content too short: {} characters".format(len(chapter_content)))
                raise HTTPException(status_code=500, detail="Generated chapter content is too short or empty")

            # --- SAVE CHAPTER 1 AND CHOICES TO DATABASE IMMEDIATELY ---
            chapter_id = None
            if chapter.chapter_number == 1 and chapter.story_id and user:
                try:
                    logger.info("🚀 OPTIMIZED SAVE: Chapter 1 with DNA, summaries, and vectors...")
                    
                    # Use our optimized service for Chapter 1 save
                    from services.fixed_optimized_chapter_service import fixed_optimized_chapter_service
                    
                    # Prepare chapter data for optimized save
                    chapter_dict = {
                        "story_id": chapter.story_id,
                        "chapter_number": 1,
                        "content": chapter_content,
                        "title": "Chapter 1",
                        "choices": choices,
                        "user_choice": ""
                    }
                    
                    # Save with full optimization (DNA + summaries + vectors)
                    save_result = await fixed_optimized_chapter_service.save_chapter_optimized(
                        chapter_data=chapter_dict,
                        user_id=user.id,
                        supabase_client=supabase
                    )
                    
                    chapter_id = save_result.chapter_id
                    logger.info("✅ OPTIMIZED SAVE COMPLETE: Chapter 1 saved with full features!")
                    logger.info("📊 Save time: {:.2f}s".format(save_result.save_time))
                    logger.info("📝 Summary: '{}'".format('generated' if save_result.summary else 'failed'))
                    logger.info("🧬 DNA: '{}'".format('extracted' if save_result.performance_metrics.get('dna_extracted') else 'failed'))
                    # Removed vector_chunks reference since it doesn't exist in ChapterSaveResult
                    
                    # Update story metadata
                    try:
                        supabase.table("Stories").update({"current_chapter": 1}).eq("id", chapter.story_id).execute()
                        logger.info("✅ Updated story current_chapter to 1")
                    except Exception as e:
                        logger.warning("⚠️ Could not update story metadata: {}".format(e))
                    
                except Exception as db_error:
                    logger.error("❌ Failed to save Chapter 1 with optimization: {}".format(str(db_error)))
                    # Fallback to basic save if optimized save fails
                    logger.info("🔄 Falling back to basic Chapter 1 save...")
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
                        
                        chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
                        if chapter_response.data:
                            chapter_id = chapter_response.data[0]["id"]
                            logger.info("✅ Basic Chapter 1 save successful with ID: {}".format(chapter_id))
                    except Exception as fallback_error:
                        logger.error("❌ Even fallback save failed: {}".format(str(fallback_error)))
                        # Do not raise, allow generation to succeed even if save fails

            return {
                "chapter_1": chapter_content,  # Frontend expects this field name
                "chapter": chapter_content,    # Keep for compatibility
                "choices": choices,            # Enhanced: automatic choices
                "metadata": {
                    "chapter_number": chapter.chapter_number,
                    "word_count": len(chapter_content.split()),
                    "choices_count": len(choices),
                    "chapter_id": chapter_id,
                    "already_saved": bool(chapter_id),
                    "optimized_save": bool(chapter_id)
                }
            }
        
        else:
            # For chapters other than 1, just return the generated content
            return {
                "chapter_1": chapter_content,
                "chapter": chapter_content,
                "choices": choices,
                "metadata": {
                    "chapter_number": chapter.chapter_number,
                    "word_count": len(chapter_content.split()),
                    "choices_count": len(choices)
                }
            }
            
    except Exception as e:
        logger.error("❌ Chapter generation failed: {}".format(str(e)))
        raise HTTPException(status_code=500, detail="Chapter generation failed: {}".format(str(e)))


class JsonChapterInput(BaseModel):
    """Input model for generating Chapters from JSON outline."""
    outline_json: Dict[str, Any] = Field(..., description="JSON outline data")
    chapter_number: int = Field(default=1, ge=1, description="Chapter number to generate")

@app.post("/lc_generate_chapter_from_json")
async def generate_chapter_from_json_endpoint(chapter: JsonChapterInput):
    """Generate story chapter specifically from JSON outline data."""
    logger.info("Starting Chapter {} generation from JSON outline...".format(chapter.chapter_number))
    
    try:
        # NEW CODE:
        from enhanced_chapter_generator import EnhancedChapterGenerator
        generator = EnhancedChapterGenerator()
        
        # Extract data from JSON outline
        outline_json = chapter.outline_json
        story_summary = outline_json.get("summary", "")
        genre = outline_json.get("genre", "General Fiction") 
        tone = outline_json.get("tone", "Engaging")
        chapters_data = outline_json.get("chapters", [])
        
        # Find target chapter
        target_chapter = None
        for ch in chapters_data:
            if ch.get("chapter_number") == chapter.chapter_number:
                target_chapter = ch
                break
                
        if not target_chapter:
            raise HTTPException(status_code=400, detail="Chapter {} not found in JSON outline".format(chapter.chapter_number))
        
        logger.info("Invoking Enhanced Chapter Generator with JSON data...")
        
        # Generate with enhanced system
        result = generator.generate_chapter_from_outline(
            story_summary=story_summary,
            chapter_data=target_chapter,
            genre=genre,
            tone=tone
        )
        
        logger.info("Chapter {} generation from JSON completed!".format(chapter.chapter_number))
        
        # Handle enhanced response
        if result.get("success"):
            chapter_content = result.get("chapter_content", "")
            choices = result.get("choices", [])
            reasoning = result.get("reasoning", {})
            quality_metrics = result.get("quality_metrics", {})
            
            logger.info("Generated: {} chars, {} choices".format(len(chapter_content), len(choices)))
            
            return {
                "chapter": chapter_content,
                "choices": choices,  # Enhanced: automatic choices with CoT
                "reasoning": reasoning,  # NEW: Transparent reasoning
                "quality_metrics": quality_metrics,  # NEW: Quality validation
                "metadata": {
                    "chapter_number": chapter.chapter_number,
                    "chapter_title": target_chapter.get("title", "Chapter {}".format(chapter.chapter_number)),
                    "word_count": len(chapter_content.split()),
                    "character_count": len(chapter_content),
                    "choices_count": len(choices),
                    "estimated_word_count": target_chapter.get("estimated_word_count", 0),
                    "generation_success": True,
                    "source": "enhanced_json_outline",
                    "cot_reasoning": bool(reasoning),
                    "quality_score": quality_metrics.get("overall_score", "N/A")
                },
                "chapter_outline_data": target_chapter
            }
        else:
            # Handle error case
            error_msg = result.get("error", "Enhanced generation failed")
            logger.error("Enhanced chapter generation failed: {}".format(error_msg))
            raise HTTPException(status_code=500, detail=error_msg)
            
    except Exception as e:
        logger.error("Enhanced chapter generation from JSON failed: {}".format(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stories/save")
async def save_story_endpoint(
    story_data: StorySaveInput,
    background_tasks: BackgroundTasks,
    user = Depends(get_authenticated_user)
):
    """Save story with complete JSON metadata parsing and database storage."""
    logger.info("Saving story with JSON parsing: {}".format(story_data.story_title))
    
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
            
            logger.info("Extracted metadata: {}".format(list(extracted_metadata.keys())))
            
            # DEBUG: Log specific theme and style values
            logger.info("   JSON theme: {}".format(json_data.get('theme', 'NOT_FOUND')))
            logger.info("   JSON style: {}".format(json_data.get('style', 'NOT_FOUND')))
            logger.info("   story_data.theme: {}".format(story_data.theme))
            logger.info("   story_data.style: {}".format(story_data.style))
            logger.info("   extracted_metadata theme: {}".format(extracted_metadata.get('theme', 'NOT_FOUND')))
            logger.info("   extracted_metadata style: {}".format(extracted_metadata.get('style', 'NOT_FOUND')))
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
        
        logger.info("Attempting to insert story with fields: {}".format(list(story_insert_data.keys())))
        
        # DEBUG: Show actual values being inserted
        logger.info("Final VALUES BEING INSERTED:")
        for key, value in story_insert_data.items():
            if key in ['theme', 'style', 'genre']:
                logger.info("   {}: '{}' (type: {})".format(key, value, type(value)))
        
        # Try to insert with all fields, fallback to minimal if schema issues
        try:
            story_response = supabase.table("Stories").insert(story_insert_data).execute()
            story_id = story_response.data[0]["id"]
            logger.info("Story inserted successfully with full metadata: {}".format(story_id))
        except Exception as db_error:
            logger.warning("Full metadata insert failed: {}".format(db_error))
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
                logger.info("Story inserted successfully with minimal data: {}".format(story_id))
            except Exception as minimal_error:
                logger.error("Even minimal story insert failed: {}".format(minimal_error))
                raise HTTPException(
                    status_code=500, 
                    detail="Database schema mismatch. Please check your Stories table columns. Error: {}".format(str(minimal_error))
                )
        
        # Calculate chapter metadata
        word_count = len(story_data.chapter_1_content.split())
        reading_time = max(1, word_count // 200)  # 200 words per minute
        
        # Generate summary for Chapter 1 using the new chapter_summary module
        logger.info("CHAPTER 1 SUMMARY: Starting summary generation for Chapter 1...")
        
        # Build basic story context for Chapter 1
        story_context = "STORY: {}\nGENRE: {}\nTHEME: {}\n\nSTORY OUTLINE:\n{}".format(extracted_metadata['book_title'], extracted_metadata.get('genre', ''), extracted_metadata.get('theme', ''), story_data.story_outline)
        
        logger.info("CHAPTER 1 SUMMARY: Story context built: {} chars".format(len(story_context)))
        
        # Generate summary
        logger.info("CHAPTER 1 SUMMARY: Calling LLM...")
        summary_result = generate_chapter_summary(
            chapter_content=story_data.chapter_1_content,
            chapter_number=1,
            story_context=story_context,
            story_title=extracted_metadata["book_title"]
        )
        
        logger.info("CHAPTER 1 SUMMARY: LLM Response Status: {}".format(summary_result['success']))
        
        chapter_1_summary = ""
        if summary_result["success"]:
            chapter_1_summary = summary_result["summary"]
            logger.info("âœ… CHAPTER 1 SUMMARY: Generated successfully!")
            logger.info("CHAPTER 1 SUMMARY: Length: {} chars".format(len(chapter_1_summary)))
            logger.info("CHAPTER 1 SUMMARY: Preview: {}...".format(chapter_1_summary[:100]))
        else:
            logger.warning("âš ï¸ CHAPTER 1 SUMMARY: Generation failed: {}".format(summary_result['error']))
            chapter_1_summary = chapter_1_metadata.get("summary", "First chapter")
        
        # Prepare chapter data WITH summary
        logger.info("CHAPTER 1 DATABASE: Preparing insert with summary...")
        
        # Get the next version number for this chapter
        next_version_number = await get_next_chapter_version_number(story_id, 1, supabase)
        
        # Deactivate previous versions of this chapter
        await deactivate_previous_chapter_versions(story_id, 1, supabase)
        
        chapter_insert_data = {
            "story_id": story_id,
            "chapter_number": 1,
            "title": chapter_1_metadata.get("title", "Chapter 1"),
            "content": story_data.chapter_1_content,
            "summary": chapter_1_summary,  # Summary is now included from generation above
            "version_number": next_version_number,  # Add proper versioning
            "is_active": True,  # Mark this version as active
        }
        
        logger.info("CHAPTER 1 DATABASE: Insert data keys: {}".format(list(chapter_insert_data.keys())))
        logger.info("CHAPTER 1 DATABASE: Summary field in insert: {}".format(bool(chapter_insert_data.get('summary'))))
        logger.info("CHAPTER 1 DATABASE: Summary length: {} chars".format(len(chapter_insert_data.get('summary', ''))))
        logger.info("CHAPTER 1 DATABASE: Summary preview: {}...".format(chapter_insert_data.get('summary', '')[:100]))
        
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
        
        logger.info("CHAPTER 1 DATABASE: Final insert data fields: {}".format(list(chapter_insert_data.keys())))
        
        # Try to insert chapter with fallback handling
        logger.info("CHAPTER 1 DATABASE: Executing INSERT...")
        try:
            chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
            
            logger.info("CHAPTER 1 DATABASE: Response: {}".format(chapter_response))
            logger.info("CHAPTER 1 DATABASE: Response data: {}".format(chapter_response.data))
            
            if not chapter_response.data:
                logger.error("âŒ CHAPTER 1 DATABASE: Insert returned no data")
                chapter_id = None
            else:
                chapter_id = chapter_response.data[0]["id"]
                saved_chapter = chapter_response.data[0]
                
                logger.info("âœ… CHAPTER 1 DATABASE: Chapter inserted with metadata: {}".format(chapter_id))
                logger.info("CHAPTER 1 DATABASE: Saved summary field: {}".format(saved_chapter.get('summary', 'NOT_FOUND')))
                
                # Verification query
                logger.info("CHAPTER 1 DATABASE: Verifying saved chapter...")
                verify_response = supabase.table("Chapters").select("id, summary").eq("id", chapter_id).execute()
                
                if verify_response.data:
                    verified_summary = verify_response.data[0].get("summary")
                    logger.info("âœ… CHAPTER 1 VERIFICATION: Summary in DB: {}".format(bool(verified_summary)))
                    if verified_summary:
                        logger.info("CHAPTER 1 VERIFICATION: Summary length: {} chars".format(len(verified_summary)))
                        logger.info("CHAPTER 1 VERIFICATION: Summary preview: {}...".format(verified_summary[:100]))
                    else:
                        logger.error("âŒ CHAPTER 1 VERIFICATION: Summary is NULL in database!")
                else:
                    logger.error("âŒ CHAPTER 1 VERIFICATION: Could not query saved chapter!")
                    
        except Exception as chapter_error:
            logger.error("âŒ CHAPTER 1 DATABASE: Full metadata insert failed: {}".format(chapter_error))
            logger.error("CHAPTER 1 DATABASE: Error type: {}".format(type(chapter_error)))
            logger.info("CHAPTER 1 DATABASE: Falling back to minimal chapter insert...")
            
            # Fallback: minimal chapter data WITH summary if possible
            minimal_chapter_data = {
                "story_id": story_id,
                "chapter_number": 1,
                "title": chapter_1_metadata.get("title", "Chapter 1"),
                "content": story_data.chapter_1_content,
                "summary": chapter_1_summary,  # Include summary in fallback too!
            }
            
            logger.info("CHAPTER 1 FALLBACK: Minimal data keys: {}".format(list(minimal_chapter_data.keys())))
            
            try:
                chapter_response = supabase.table("Chapters").insert(minimal_chapter_data).execute()
                chapter_id = chapter_response.data[0]["id"]
                logger.info("âœ… CHAPTER 1 FALLBACK: Chapter inserted with minimal data: {}".format(chapter_id))
            except Exception as minimal_chapter_error:
                logger.error("âŒ CHAPTER 1 FALLBACK: Even minimal chapter insert failed: {}".format(minimal_chapter_error))
                logger.error("CHAPTER 1 FALLBACK: Error type: {}".format(type(minimal_chapter_error)))
                # Don't fail the entire save if chapter insert fails
                chapter_id = None
                logger.warning("âš ï¸ CHAPTER 1 FALLBACK: Story saved but Chapter 1 could not be inserted due to schema issues")
        
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
                    user_id=user.id,
                    supabase=supabase
                )
                choices_saved_count = len(saved_choices)
                    
            except Exception as e:
                logger.error("âŒ CHOICES: Error saving choices to database: {}".format(e))
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
                success_message += " {} choices saved.".format(choices_saved_count)
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
        logger.error("Story saving with JSON parsing failed: {}".format(e))
        raise HTTPException(status_code=500, detail="Failed to save story with metadata: {}".format(str(e)))

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
        logger.error("Performance stats failed: {}".format(e))
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
            return {"message": "Cleared cache pattern: {}".format(pattern)}
        else:
            # Clear all memory cache
            cache_service._memory_cache.clear()
            return {"message": "Cleared memory cache"}
    except Exception as e:
        logger.error("Cache clear failed: {}".format(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )

# Test endpoint for JSON parsing flow
@app.post("/test/json_flow")
async def test_json_parsing_flow(test_idea: str = "A revenge story about a young warrior seeking justice"):
    """Test the new summary-based outline generation (no auth required)."""
    try:
        from lc_book_generator_prompt import generate_book_outline_json
        logger.info("Testing JSON flow with idea: {}".format(test_idea))
        result = generate_book_outline_json(test_idea)
        if not result or not result.get("summary"):
            return {
                "step": "json_generation",
                "success": False,
                "error": "No summary returned",
                "raw_response": result
            }
        return {
            "step": "json_generation",
            "success": True,
            "summary": result["summary"],
            "genre": result.get("genre", ""),
            "tone": result.get("tone", "")
        }
    except Exception as e:
        logger.error("Test JSON flow failed: {}".format(e))
        return {
            "step": "json_generation",
            "success": False,
            "error": str(e)
        }

# Simple test endpoint to see formatted text output
@app.post("/test/formatted_outline")
async def test_formatted_outline(idea: str = "A detective solving mysteries in Victorian London"):
    """Test new summary-based outline output for frontend display (no auth required)."""
    try:
        from lc_book_generator_prompt import generate_book_outline_json
        logger.info("Testing formatted outline for: {}".format(idea))
        result = generate_book_outline_json(idea)
        if not result or not result.get("summary"):
            return {
                "success": False,
                "error": "No summary returned",
                "formatted_text": "âŒ Failed to generate outline."
            }
        return {
            "success": True,
            "idea": idea,
            "formatted_text": result["summary"],
            "genre": result.get("genre", ""),
            "tone": result.get("tone", "")
        }
    except Exception as e:
        logger.error("Formatted outline test failed: {}".format(e))
        return {
            "success": False,
            "error": str(e),
            "formatted_text": "âŒ Error: {}".format(str(e))
        }

@app.post("/test/complete_json_to_chapter_flow")
async def test_complete_json_to_chapter_flow(idea: str = "A space explorer discovers a mysterious alien artifact"):
    """Test the complete flow: Idea â†' JSON Outline â†' Chapter 1 Generation (no auth required)."""
    logger.info("Testing COMPLETE JSON to Chapter 1 flow with idea: {}".format(idea))
    
    try:
        from lc_book_generator_prompt import generate_book_outline_json
        from lc_book_generator import BookStoryGenerator
        
        # Step 1: Generate JSON outline from idea
        logger.info("Step 1: Generating JSON outline...")
        outline_result = generate_book_outline_json(idea)
        
        if not outline_result["success"]:
            return {
                "step": "json_generation_failed",
                "success": False,
                "error": outline_result["error"],
                "idea": idea
            }
        
        outline_json = outline_result["outline_json"]
        logger.info("Step 1 completed: JSON outline generated successfully")
        
        # Step 2: Generate Chapter 1 from JSON outline
        logger.info("Step 2: Generating Chapter 1 from JSON outline...")
        generator = BookStoryGenerator()
        
        chapter_1_content = generator.generate_chapter_from_json(outline_json, 1)
        
        if chapter_1_content.startswith("âŒ"):
            return {
                "step": "chapter_generation_failed",
                "success": False,
                "error": chapter_1_content,
                "outline_json": outline_json,
                "idea": idea
            }
        
        logger.info("Step 2 completed: Chapter 1 generated successfully")
        
        # Step 3: Extract metadata for analysis
        Chapters = outline_json.get("Chapters", [])
        chapter_1_data = next(
            (ch for ch in Chapters if ch.get("chapter_number") == 1),
            {}
        )
        
        # Calculate statistics
        actual_word_count = len(chapter_1_content.split())
        estimated_word_count = chapter_1_data.get("estimated_word_count", 0)
        
        logger.info("Final Statistics:")
        logger.info("   Title: {}".format(outline_json.get('book_title', 'N/A')))
        logger.info("   Genre: {}".format(outline_json.get('genre', 'N/A')))
        logger.info("   Chapter 1 Title: {}".format(chapter_1_data.get('chapter_title', 'N/A')))
        logger.info("   Estimated Words: {}".format(estimated_word_count))
        logger.info("   Actual Words: {}".format(actual_word_count))
        logger.info("   Characters: {}".format(len(outline_json.get('main_characters', []))))
        logger.info("   Locations: {}".format(len(outline_json.get('key_locations', []))))
        
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
                "word_count_accuracy": "{:.1f}%".format((actual_word_count / max(estimated_word_count, 1)) * 100) if estimated_word_count > 0 else "N/A",
                "characters_created": len(outline_json.get("main_characters", [])),
                "locations_created": len(outline_json.get("key_locations", [])),
                "total_chapters_planned": len(Chapters),
                "total_estimated_book_words": sum(ch.get("estimated_word_count", 0) for ch in Chapters)
            },
            
            # Next Steps for Implementation
            "implementation_ready": {
                "has_complete_json": bool(outline_json),
                "has_chapter_content": bool(chapter_1_content and not chapter_1_content.startswith("âŒ")),
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
        logger.error("Complete flow test failed: {}".format(e))
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
        
        logger.info("Testing auto-save outline for idea: {}...".format(idea[:50]))
        
        # Generate JSON outline
        result = generate_book_outline_json(idea)
        
        if not result["success"]:
            return {"success": False, "error": "Outline generation failed: {}".format(result['error'])}
        
        # Extract data
        metadata = result["metadata"]
        outline_json = result["outline_json"]
        formatted_text = result["formatted_text"]
        usage_metrics = result.get("usage_metrics", {})  # LLM usage metrics
        
        # Test database save
        story_id = None
        database_save_success = False
        
        try:
            logger.info("Testing database auto-save...")
            
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
            
            logger.info("Saving test outline with fields: {}".format(list(story_data.keys())))
            
            # Insert to database
            story_response = supabase.table("Stories").insert(story_data).execute()
            story_id = story_response.data[0]["id"]
            database_save_success = True
            
            logger.info("Test outline auto-saved with story_id: {}".format(story_id))
            
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
                "locations_count": len(metadata["key_locations"])
            },
            "database_fields_saved": list(story_data.keys()) if database_save_success else [],
            "message": "âœ… Auto-save outline test completed! JSON outline was generated and saved to database automatically." if database_save_success else "âš ï¸ Outline generated but database save failed."
        }
        
    except Exception as e:
        logger.error("Auto-save outline test failed: {}".format(e))
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
    OPTIMIZED chapter save with async pipeline processing:
    
    Performance Improvements:
    - Immediate chapter save (priority #1)
    - Parallel summary + vector generation
    - Background vector embedding storage
    - Batch database operations
    - Smart caching and monitoring
    """
    try:
        logger.info("OPTIMIZED SAVE: Starting Chapter {}, Story {}".format(chapter_data.chapter_number, chapter_data.story_id))
        logger.info("User ID: {}".format(user.id))
        
        # STEP 0: Check if chapter already exists to prevent duplicate saves
        logger.info("STEP 0: Checking if Chapter {} already exists...".format(chapter_data.chapter_number))
        existing_chapter = supabase.table("Chapters").select("id, content").eq("story_id", chapter_data.story_id).eq("chapter_number", chapter_data.chapter_number).eq("is_active", True).execute()
        
        if existing_chapter.data and len(existing_chapter.data) > 0:
            existing_chapter_id = existing_chapter.data[0]["id"]
            logger.info("STEP 0: Chapter {} already exists with ID: {}".format(chapter_data.chapter_number, existing_chapter_id))
            
            # Fetch existing choices
            choices_response = supabase.table("story_choices").select("*").eq("chapter_id", existing_chapter_id).execute()
            existing_choices = choices_response.data if choices_response.data else []
            
            return {
                "success": True,
                "message": "Chapter {} already exists - no duplicate save needed".format(chapter_data.chapter_number),
                "chapter_id": existing_chapter_id,
                "story_id": chapter_data.story_id,
                "chapter_number": chapter_data.chapter_number,
                "choices": existing_choices,
                "from_existing": True,
                "summary": "Chapter already exists"
            }

        # STEP 1: Use optimized chapter service for high-performance save
        from services.fixed_optimized_chapter_service import fixed_optimized_chapter_service as optimized_chapter_service
        
        # Convert Pydantic model to dict
        chapter_dict = {
            "story_id": chapter_data.story_id,
            "chapter_number": chapter_data.chapter_number,
            "content": chapter_data.content,
            "title": chapter_data.title,
            "choices": getattr(chapter_data, 'choices', [])
        }
        
        # Execute optimized save pipeline
        save_result = await optimized_chapter_service.save_chapter_optimized(
            chapter_data=chapter_dict,
            user_id=user.id,
            supabase_client=supabase
        )
        
        logger.info("âœ… OPTIMIZED SAVE COMPLETE: Chapter {} saved in {:.2f}s".format(chapter_data.chapter_number, save_result.save_time))
        
        # Return optimized response
        return {
            "success": True,
            "message": "Chapter {} saved with optimized pipeline!".format(chapter_data.chapter_number),
            "chapter_id": save_result.chapter_id,
            "story_id": chapter_data.story_id,
            "chapter_number": chapter_data.chapter_number,
            "summary": save_result.summary,
            "choices": save_result.choices,
            "performance_metrics": {
                "save_time": save_result.save_time,
                "vector_chunks": save_result.vector_chunks,
                **save_result.performance_metrics
            },
            "enhanced_features": {
                "async_pipeline": True,
                "vector_embeddings": True,
                "background_processing": True,
                "batch_operations": True
            }
        }

        # STEP 1: Verify story ownership
        logger.info("STEP 1: Verifying story ownership...")
        story_response = supabase.table("Stories").select("*").eq("id", chapter_data.story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            logger.error("âŒ AUTHORIZATION: Story {} not found for user {}".format(chapter_data.story_id, user.id))
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        story_title = story.get("story_title", "Untitled Story")
        story_outline = story.get("story_outline", "")
        
        logger.info("STEP 1 COMPLETE: Story '{}' verified".format(story_title))
        
        # STEP 2: Get or create branch_id for proper branching support
        logger.info("STEP 2: Managing story branches...")
        try:
            main_branch_id = await get_main_branch_id(chapter_data.story_id)
            logger.info("âœ… Using main branch: {}".format(main_branch_id))
        except Exception as branch_error:
            logger.warning("Branch management failed: {}, continuing without branch_id".format(branch_error))
            main_branch_id = None
        
        # STEP 3: Optimized previous chapters fetching (summaries only, not full content)
        logger.info("STEP 3: Fetching previous chapter summaries...")
        
        # Only get summaries from previous chapters for efficiency
        query = supabase.table("Chapters").select("summary, chapter_number").eq("story_id", chapter_data.story_id).lt("chapter_number", chapter_data.chapter_number)
        
        if main_branch_id:
            query = query.eq("branch_id", main_branch_id)
        
        query = query.eq("is_active", True).order("chapter_number")
        previous_chapters_response = query.execute()
        
        previous_summaries = []
        if previous_chapters_response.data:
            for prev_chapter in previous_chapters_response.data:
                if prev_chapter.get("summary"):
                    previous_summaries.append(prev_chapter["summary"])
                    logger.info("Chapter {}: Using existing summary".format(prev_chapter['chapter_number']))
                else:
                    logger.warning("Chapter {}: No summary found".format(prev_chapter['chapter_number']))
        
        logger.info("STEP 3 COMPLETE: Found {} previous summaries".format(len(previous_summaries)))
        
        # STEP 4: Enhanced summary generation with CoT
        logger.info("STEP 4: Generating enhanced summary with CoT reasoning...")
        
        # Import the enhanced summary function
        from chapter_summary import generate_chapter_summary  # This should be your enhanced version
        
        # Build optimized story context
        story_context = "STORY: {}\nGENRE: {}\nOUTLINE: {}".format(story_title, story.get('genre', 'Fiction'), story_outline[:600])
        
        # Generate enhanced summary
        summary_result = generate_chapter_summary(
            chapter_content=chapter_data.content,
            chapter_number=chapter_data.chapter_number,
            story_context=story_context,
            story_title=story_title
        )
        
        summary_text = ""
        cot_analysis = ""
        quality_score = 0
        
        if summary_result["success"]:
            summary_text = summary_result["summary"]
            cot_analysis = summary_result.get("cot_analysis", "")
            quality_score = summary_result.get("metadata", {}).get("quality_score", 0)
            
            logger.info("âœ… STEP 4 COMPLETE: Enhanced summary generated!")
            logger.info("Quality Score: {}/10".format(quality_score))
            logger.info("Summary: {} chars".format(len(summary_text)))
            logger.info("CoT Analysis: {} chars".format(len(cot_analysis)))
        else:
            # Fallback to basic summary if enhanced fails
            logger.warning("Enhanced summary failed: {}".format(summary_result.get('error', 'Unknown error')))
            summary_text = "Chapter {} summary generation failed. Manual summary needed.".format(chapter_data.chapter_number)
            logger.info("Using fallback summary")
        
        # STEP 5: Calculate metadata
        word_count = len(chapter_data.content.split())
        summary_token_metrics = summary_result.get("usage_metrics", {})
        
        logger.info("Chapter metadata: {} words".format(word_count))
        
        # STEP 6: Database operations with proper versioning
        logger.info("STEP 6: Database save operations...")
        
        # Get next version and deactivate previous
        next_version_number = await get_next_chapter_version_number(
            chapter_data.story_id, 
            chapter_data.chapter_number,
            main_branch_id
        )
        
        await deactivate_previous_chapter_versions(
            chapter_data.story_id, 
            chapter_data.chapter_number,
            main_branch_id
        )
        
        # Prepare chapter data with enhanced fields
        chapter_insert_data = {
            "story_id": chapter_data.story_id,
            "chapter_number": chapter_data.chapter_number,
            "title": chapter_data.title or "Chapter {}".format(chapter_data.chapter_number),
            "content": chapter_data.content,
            "summary": summary_text,
            "word_count": word_count,
            "version_number": next_version_number,
            "is_active": True,
        }
        
        # Add branch_id if available
        if main_branch_id:
            chapter_insert_data["branch_id"] = main_branch_id
        
        # Add token tracking if fields exist in schema (graceful handling)
        token_fields = {
            "token_count_prompt": chapter_data.token_count_prompt or summary_token_metrics.get("estimated_input_tokens", 0),
            "token_count_completion": chapter_data.token_count_completion or summary_token_metrics.get("estimated_output_tokens", 0),
            "token_count_total": chapter_data.token_count_total or summary_token_metrics.get("estimated_total_tokens", 0),
            "temperature_used": chapter_data.temperature_used or summary_token_metrics.get("temperature_used", 0.3),
        }
        
        # Only add token fields if they have values (graceful schema handling)
        for field, value in token_fields.items():
            if value and value > 0:
                chapter_insert_data[field] = value
        
        # Add enhanced summary metadata if available
        if cot_analysis:
            # Only add if field exists in schema
            try:
                chapter_insert_data["cot_analysis"] = cot_analysis[:1000]  # Truncate if too long
            except:
                logger.info("CoT analysis field not available in schema")
        
        if quality_score > 0:
            try:
                chapter_insert_data["quality_score"] = quality_score
            except:
                logger.info("Quality score field not available in schema")
        
        logger.info("Insert fields: {}".format(list(chapter_insert_data.keys())))
        
        # Execute database insert
        try:
            chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
            
            if not chapter_response.data:
                raise HTTPException(status_code=500, detail="Failed to save chapter")
            
            chapter_id = chapter_response.data[0]["id"]
            logger.info("âœ… STEP 6 COMPLETE: Chapter saved with ID: {}".format(chapter_id))
            
            # Verify summary was saved
            verify_response = supabase.table("Chapters").select("summary").eq("id", chapter_id).execute()
            if verify_response.data and verify_response.data[0].get("summary"):
                logger.info("âœ… VERIFICATION: Summary confirmed in database")
            else:
                logger.warning("âš ï¸ VERIFICATION: Summary may not have saved properly")
                
        except Exception as db_error:
            logger.error("âŒ DATABASE INSERT FAILED: {}".format(str(db_error)))
            raise HTTPException(status_code=500, detail="Database insert failed: {}".format(str(db_error)))
        
        # STEP 7: Save choices for this chapter (from frontend or LLM result)
        logger.info("STEP 7: Saving choices for Chapter {}...".format(chapter_data.chapter_number))
        choices_to_save = getattr(chapter_data, 'choices', None) or getattr(chapter_data, 'chapter_1_choices', None) or []
        if not choices_to_save and hasattr(chapter_data, 'content'):
            # Try to extract choices from content if present (for future-proofing)
            try:
                import json
                content_json = json.loads(chapter_data.content)
                if isinstance(content_json, dict) and 'choices' in content_json:
                    choices_to_save = content_json['choices']
            except Exception:
                pass
        
        choices_saved_count = 0
        if choices_to_save and chapter_id:
            try:
                saved_choices = await save_choices_for_chapter(
                    story_id=chapter_data.story_id,
                    chapter_id=chapter_id,
                    chapter_number=chapter_data.chapter_number,
                    choices=choices_to_save,
                    user_id=user.id,
                    supabase=supabase
                )
                choices_saved_count = len(saved_choices)
                logger.info("âœ… STEP 7 COMPLETE: Saved {} choices".format(choices_saved_count))
            except Exception as e:
                logger.warning("STEP 7: Error saving choices: {}".format(e))
                choices_saved_count = 0
        else:
            logger.info("â„¹ï¸ No choices to save for this chapter.")
        
        # STEP 8: Update story metadata
        logger.info("STEP 8: Updating story metadata...")
        try:
            story_update = {"current_chapter": chapter_data.chapter_number}
            
            # Update word count if available
            if word_count > 0:
                try:
                    story_update["total_word_count"] = word_count  # If field exists
                except:
                    pass
            
            supabase.table("Stories").update(story_update).eq("id", chapter_data.story_id).execute()
            logger.info("âœ… STEP 8 COMPLETE: Story metadata updated")
        except Exception as e:
            logger.warning("STEP 8: Could not update story metadata: {}".format(e))
        
        # STEP 9: Background tasks
        logger.info("STEP 9: Scheduling background tasks...")
        try:
            # Generate embeddings
            from services.embedding_service import embedding_service
            background_tasks.add_task(
                embedding_service.create_embeddings_async,
                chapter_data.story_id,
                True  # Force recreate
            )
            
            # Invalidate caches
            background_tasks.add_task(
                story_service.invalidate_story_cache,
                chapter_data.story_id
            )
            
            logger.info("âœ… STEP 9 COMPLETE: Background tasks scheduled")
        except Exception as bg_error:
            logger.warning("STEP 9: Background task scheduling failed: {}".format(bg_error))
        
        logger.info("ENHANCED SAVE COMPLETE: All steps successful!")
        
        # Enhanced response with all new features
        return {
            "success": True,
            "message": "Chapter saved with enhanced summary and auto-generated choices!",
            "chapter_id": chapter_id,
            "story_id": chapter_data.story_id,
            "chapter_number": chapter_data.chapter_number,
            "summary": summary_text,
            "choices": choices_to_save,  # Always return the saved choices
            "enhanced_features": {
                "cot_reasoning": bool(cot_analysis),
                "quality_score": quality_score,
                "choices_generated": choices_saved_count,
                "branch_support": bool(main_branch_id),
                "summary_enhancement": summary_result["success"]
            },
            "summary_generation": {
                "success": summary_result["success"],
                "word_count": word_count,
                "summary_length": len(summary_text),
                "compression_ratio": summary_result.get("metadata", {}).get("compression_ratio", 0),
                "quality_score": quality_score,
                "uses_cot": bool(cot_analysis),
                "usage_metrics": summary_token_metrics
            },
            "metadata": {
                "version_number": next_version_number,
                "branch_id": main_branch_id,
                "previous_summaries_used": len(previous_summaries),
                "background_tasks_scheduled": 2
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("âŒ FATAL ERROR in optimized chapter save: {}".format(str(e)))
        import traceback
        logger.error("âŒ Traceback: {}".format(traceback.format_exc()))
        raise HTTPException(status_code=500, detail="Failed to save chapter: {}".format(str(e)))

@app.get("/performance/chapter_save")
async def get_chapter_save_performance():
    """Get performance metrics for chapter save operations"""
    try:
        from services.fixed_optimized_chapter_service import fixed_optimized_chapter_service as optimized_chapter_service
        
        metrics = optimized_chapter_service._get_performance_metrics()
        
        return {
            "success": True,
            "performance_metrics": metrics,
            "optimization_features": {
                "async_pipeline": True,
                "vector_embeddings": True,
                "background_processing": True,
                "batch_operations": True,
                "smart_chunking": True,
                "parallel_execution": True
            },
            "recommendations": {
                "avg_save_time_target": "< 3.0 seconds",
                "memory_usage_target": "< 500 MB",
                "vector_chunks_optimal": "5-15 chunks per chapter"
            }
        }
    except Exception as e:
        logger.error("Failed to get performance metrics: {}".format(e))
        return {"success": False, "error": str(e)}
@app.post("/generate_next_chapter")
async def generate_next_chapter_endpoint(
    chapter_input: GenerateNextChapterInput,
    user = Depends(get_authenticated_user)
):
    """
    ENHANCED Generate next chapter with DNA tracking, summaries, and vector context.
    
    Features:
    - Story DNA continuity tracking
    - Chapter summary context
    - Vector-based scene relevance
    - Plot thread preservation
    - Character consistency validation
    """
    try:
        logger.info("ENHANCED Chapter Generation: Chapter {} for story {}".format(chapter_input.chapter_number, chapter_input.story_id))
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", chapter_input.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        story_title = story.get("story_title", "Untitled Story")
        story_outline = story.get("story_outline", chapter_input.story_outline)
        
        # Get previous chapters with ALL context (content, summary, DNA)
        max_context_chapter = chapter_input.chapter_number - 1
        previous_chapters_response = supabase.table("Chapters").select(
            "content, summary, dna, chapter_number, title"
        ).eq("story_id", chapter_input.story_id).eq("is_active", True).lte(
            "chapter_number", max_context_chapter
        ).order("chapter_number").execute()
        
        previous_chapters = previous_chapters_response.data if previous_chapters_response.data else []
        
        logger.info("Retrieved {} previous chapters with DNA and summaries".format(len(previous_chapters)))
        
        # Get user's choice that led to this chapter
        user_choice = getattr(chapter_input, 'user_choice', "")
        choice_options = []
        
        if chapter_input.chapter_number > 1 and not user_choice:
            # Try to get the choice from the previous chapter
            prev_chapter_id = None
            if previous_chapters:
                # Find the previous chapter ID
                for chapter in previous_chapters:
                    if chapter.get('chapter_number') == chapter_input.chapter_number - 1:
                        prev_chapter_id = chapter.get('id')
                        break
            
            if prev_chapter_id:
                choice_response = supabase.table("story_choices").select("*").eq("chapter_id", prev_chapter_id).execute()
                if choice_response.data:
                    choice_options = choice_response.data
                    # Find the selected choice
                    for choice in choice_options:
                        if choice.get("is_selected"):
                            user_choice = "{}: {}".format(choice.get('title', ''), choice.get('description', ''))
                            break
        
        logger.info("User choice context: {}...".format(user_choice[:100]) if user_choice else "No specific user choice")
        
        # Use enhanced chapter generator with DNA and summaries
        from services.enhanced_chapter_generator import enhanced_chapter_generator
        
        generation_result = await enhanced_chapter_generator.generate_next_chapter_enhanced(
            story_id=chapter_input.story_id,
            story_title=story_title,
            story_outline=story_outline,
            current_chapter_number=chapter_input.chapter_number,
            user_choice=user_choice,
            previous_chapters=previous_chapters,
            choice_options=choice_options
        )
        
        logger.info("âœ… ENHANCED Chapter {} generated successfully!".format(chapter_input.chapter_number))
        logger.info("Generation time: {:.2f}s".format(generation_result['metrics']['generation_time']))
        logger.info("DNA components used: {}".format(generation_result['metrics']['context_components_used']['dna_components']))
        logger.info("Summary components used: {}".format(generation_result['metrics']['context_components_used']['summary_components']))
        logger.info("Continuity score: {:.2f}".format(generation_result['metrics']['continuity_score']))
        
        return {
            "chapter": generation_result["content"],
            "title": generation_result["title"],
            "choices": generation_result["choices"],
            "metadata": {
                "chapter_number": chapter_input.chapter_number,
                "story_id": chapter_input.story_id,
                "word_count": len(generation_result["content"].split()),
                "character_count": len(generation_result["content"]),
                "previous_chapters_used": len(previous_chapters),
                "generation_success": True,
                "user_choice_provided": bool(user_choice)
            },
            "continuity_features": {
                "dna": generation_result.get("dna"),
                "summary": generation_result.get("summary"),
                "continuity_score": generation_result["metrics"]["continuity_score"],
                "context_components_used": generation_result["metrics"]["context_components_used"],
                "enhanced_features": generation_result["enhanced_features"]
            },
            "performance_metrics": {
                "generation_time": generation_result["metrics"]["generation_time"],
                "context_length": generation_result["metrics"]["context_components_used"]["total_context_length"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in ENHANCED chapter generation: {}".format(str(e)))
        import traceback
        logger.error("Traceback: {}".format(traceback.format_exc()))
        raise HTTPException(status_code=500, detail="Failed to generate enhanced chapter: {}".format(str(e)))



@app.post("/generate_and_save_chapter")
async def generate_and_save_chapter_endpoint(
    chapter_input: GenerateNextChapterInput,
    background_tasks: BackgroundTasks,
    user = Depends(get_authenticated_user)
):
    '''
    ENHANCED: Generate and save chapter with DNA, summaries, and vector embeddings.
    Now uses the optimized service for complete feature support.
    '''
    try:
        logger.info(' ENHANCED GENERATE & SAVE: Starting Chapter {} for story {}...'.format(chapter_input.chapter_number, chapter_input.story_id))
        
        # Verify story belongs to user
        story_response = supabase.table('Stories').select('*').eq('id', chapter_input.story_id).eq('user_id', user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail='Story not found or access denied')
        
        story = story_response.data[0]
        story_title = story.get('story_title', 'Untitled Story')
        story_outline = story.get('story_outline', chapter_input.story_outline)
        
        # STEP 1: Generate chapter using enhanced generator
        from services.enhanced_chapter_generator import enhanced_chapter_generator
        
        # Get previous chapters for context (with DNA and summaries)
        previous_chapters_response = supabase.table('Chapters').select(
            'content, summary, dna, chapter_number, title'
        ).eq('story_id', chapter_input.story_id).eq('is_active', True).lt(
            'chapter_number', chapter_input.chapter_number
        ).order('chapter_number').execute()
        
        previous_chapters = previous_chapters_response.data if previous_chapters_response.data else []
        
        logger.info(' Using {} previous chapters for enhanced generation'.format(len(previous_chapters)))
        
        # Generate chapter with enhanced context (DNA + summaries + vectors)
        generation_result = await enhanced_chapter_generator.generate_next_chapter_enhanced(
            story_id=chapter_input.story_id,
            story_title=story_title,
            story_outline=story_outline,
            current_chapter_number=chapter_input.chapter_number,
            user_choice='',  # No specific user choice for initial generation
            previous_chapters=previous_chapters,
            choice_options=[]
        )
        
        logger.info(' STEP 1 COMPLETE: Enhanced chapter generated!')
        logger.info(' Content: {} chars'.format(len(generation_result["content"])))
        logger.info(' DNA: "{}"'.format("generated" if generation_result.get("dna") else "none"))
        logger.info(' Summary: "{}"'.format("generated" if generation_result.get("summary") else "none"))
        
        # STEP 2: Save using optimized service (DNA + summaries + vectors)
        from services.fixed_optimized_chapter_service import fixed_optimized_chapter_service
        
        # Prepare chapter data for optimized save
        chapter_dict = {
            'story_id': chapter_input.story_id,
            'chapter_number': chapter_input.chapter_number,
            'content': generation_result['content'],
            'title': generation_result.get('title', 'Chapter {}'.format(chapter_input.chapter_number)),
            'choices': generation_result.get('choices', []),
            'user_choice': ''
        }
        
        # Save with full optimization (DNA + summaries + vectors)
        save_result = await fixed_optimized_chapter_service.save_chapter_optimized(
            chapter_data=chapter_dict,
            user_id=user.id,
            supabase_client=supabase
        )
        
        logger.info(' STEP 2 COMPLETE: Chapter saved with optimization!')
        logger.info(' Total save time: {:.2f}s'.format(save_result.save_time))
        logger.info(' Vector chunks: {}'.format(save_result.vector_chunks))
        
        # STEP 3: Update story current chapter
        try:
            supabase.table('Stories').update({
                'current_chapter': chapter_input.chapter_number
            }).eq('id', chapter_input.story_id).execute()
            logger.info(' Updated story current_chapter to {}'.format(chapter_input.chapter_number))
        except Exception as update_error:
            logger.warning(' Could not update story current_chapter: {}'.format(update_error))
        
        return {
            'success': True,
            'message': 'Chapter {} generated and saved with full optimization!'.format(chapter_input.chapter_number),
            'chapter_id': save_result.chapter_id,
            'story_id': chapter_input.story_id,
            'chapter_number': chapter_input.chapter_number,
            'chapter_content': generation_result['content'],
            'title': generation_result.get('title'),
            'summary': save_result.summary,
            'choices': save_result.choices,
            'enhanced_features': {
                'dna_extracted': bool(generation_result.get('dna')),
                'summary_generated': bool(save_result.summary),
                'vector_chunks_created': save_result.vector_chunks,
                'async_pipeline': True,
                'background_processing': True
            },
            'performance_metrics': {
                'generation_time': generation_result['metrics']['generation_time'],
                'save_time': save_result.save_time,
                'total_time': generation_result['metrics']['generation_time'] + save_result.save_time,
                **save_result.performance_metrics
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(' Error in enhanced generate & save: {}'.format(str(e)))
        import traceback
        logger.error(' Traceback: {}'.format(traceback.format_exc()))
        raise HTTPException(status_code=500, detail='Failed to generate and save chapter: {}'.format(str(e)))



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
            logger.error("âŒ DEBUG - Story {} not found for user {}".format(story_id, user.id))
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story_data = story_response.data[0]
        logger.info("âœ… DEBUG - Found story: {}".format(story_data.get('story_title', 'Untitled')))
        
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
        
        logger.info("âœ… DEBUG - Found {} Chapters for story {}".format(len(Chapters_info), story_id))
        
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
        logger.error("âŒ DEBUG - Failed to get Chapters for story {}: {}".format(story_id, e))
        raise HTTPException(status_code=500, detail="Debug query failed: {}".format(str(e)))

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
        logger.info("BRANCH: User wants to branch from chapter {}, choice {}".format(request.chapter_number, request.choice_id))
        logger.info("BRANCH: story_id={}".format(request.story_id))
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", request.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        logger.info("âœ… BRANCH: Story verified: {}".format(story.get('story_title', 'Untitled')))
        
        # Get the main branch ID for this story
        main_branch_id = await get_main_branch_id(request.story_id)
        
        # Get all choices for the specified chapter to validate the choice exists
        choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
        
        available_choices = choices_response.data
        if not available_choices:
            raise HTTPException(status_code=404, detail="No choices found for chapter {}".format(request.chapter_number))
        
        # Find the selected choice
        selected_choice = None
        for choice in available_choices:
            if str(choice.get('id')) == str(request.choice_id) or str(choice.get('choice_id')) == str(request.choice_id):
                selected_choice = choice
                break
        
        if not selected_choice:
            raise HTTPException(status_code=400, detail="Invalid choice selected for branching")
        
        logger.info("BRANCH: Selected choice found: {}".format(selected_choice.get('title', 'No title')))
        
        # Clear the "is_selected" flag from all choices in this chapter (reset previous selection)
        logger.info("BRANCH: Resetting previous choice selections for chapter {}".format(request.chapter_number))
        supabase.table("story_choices").update({"is_selected": False, "selected_at": None}).eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("chapter_number", request.chapter_number).execute()
        
        # Mark the new choice as selected
        from datetime import datetime
        logger.info("BRANCH: Marking new choice as selected")
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
        logger.info("BRANCH: Using {} previous chapters for context".format(len(previous_chapters)))
        
        # Generate the next chapter based on the new choice
        next_chapter_number = request.chapter_number + 1
        logger.info("BRANCH: Generating chapter {} based on new choice".format(next_chapter_number))
        
        # Use the story service to generate the next chapter
        try:
            next_chapter_result = await story_service.generate_next_chapter_with_dna(
                story=story,
                previous_Chapters=previous_chapters,
                selected_choice=selected_choice,
                next_chapter_number=next_chapter_number,
                user_id=user.id
            )
            logger.info("BRANCH: Chapter {} generated successfully".format(next_chapter_number))
            chapter_content_length = len(next_chapter_result.get("chapter_content", "")) if next_chapter_result.get("chapter_content") else 0
            
        except Exception as generation_error:
            logger.error("BRANCH: Chapter generation failed: {}".format(str(generation_error)))
            raise HTTPException(status_code=500, detail="Failed to generate branched chapter: {}".format(str(generation_error)))
        
        # Get the next version number for this chapter (with branch support)
        next_version_number = await get_next_chapter_version_number(request.story_id, next_chapter_number, main_branch_id)
        
        # Deactivate previous versions of this chapter in this branch
        await deactivate_previous_chapter_versions(request.story_id, next_chapter_number, main_branch_id)
        
        # Always insert new chapter version (don't update existing ones)
        logger.info("BRANCH: Inserting new chapter version {} for chapter {}".format(next_version_number, next_chapter_number))
        chapter_content = next_chapter_result.get("chapter_content") or next_chapter_result.get("content", "")
        chapter_insert_data = {
                "story_id": request.story_id,
                "branch_id": main_branch_id,
                "chapter_number": next_chapter_number,
                "title": next_chapter_result.get("title", "Chapter {}".format(next_chapter_number)),
                "content": chapter_content,
                "word_count": len(chapter_content.split()),
            "version_number": next_version_number,  # Add proper versioning
            "is_active": True,  # Mark this version as active
            }
        chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
        chapter_id = chapter_response.data[0]["id"]
        
        # Generate and save chapter summary
        chapter_text = next_chapter_result.get("chapter_content") or next_chapter_result.get("content", "")
        logger.info("BRANCH SUMMARY: Starting summary generation for chapter {}".format(next_chapter_number))
        
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
                logger.info("BRANCH SUMMARY: Updating database with summary for chapter ID {}".format(chapter_id))
                supabase.table("Chapters").update({"summary": summary_text}).eq("id", chapter_id).execute()
                logger.info("âœ… BRANCH SUMMARY: Chapter {} summary saved".format(next_chapter_number))
            else:
                logger.error("BRANCH SUMMARY: Failed to generate summary for chapter {}".format(next_chapter_number))
        except Exception as summary_error:
            logger.error("BRANCH SUMMARY: Exception during summary generation: {}".format(str(summary_error)))
        
        # Remove any choices for chapters beyond this point (they're now invalid due to branching)
        logger.info("BRANCH: Cleaning up choices for chapters > {}".format(next_chapter_number))
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
                supabase=supabase
            )
        
        # Update story's current_chapter
        supabase.table("Stories").update({"current_chapter": next_chapter_number}).eq("id", request.story_id).execute()
        
        response_payload = {
            "success": True,
            "message": "Successfully branched from chapter {}".format(request.chapter_number),
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
        
        logger.info("BRANCH: Successfully completed branching operation")
        return response_payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("BRANCH: Unexpected error: {}".format(str(e)))
        import traceback
        logger.error("BRANCH: Full traceback: {}".format(traceback.format_exc()))
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
        logger.info("BRANCH-PREVIEW: User {} requesting preview for story {}, chapter {}, choice {}".format(user.id, request.story_id, request.chapter_number, request.choice_id))
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", request.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        logger.info("âœ… BRANCH-PREVIEW: Story verified: {}".format(story.get('story_title', 'Untitled')))
        
        # Get the main branch ID for this story
        main_branch_id = await get_main_branch_id(request.story_id)
        
        # Get all choices for the specified chapter to validate the choice exists
        logger.info("BRANCH-PREVIEW: Looking for choices with story_id={}, branch_id={}, user_id={}, chapter_number={}".format(request.story_id, main_branch_id, user.id, request.chapter_number))
        choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
        
        available_choices = choices_response.data
        logger.info("BRANCH-PREVIEW: Found {} choices for chapter {}".format(len(available_choices), request.chapter_number))
        
        if not available_choices:
            # Let's try without branch_id to see if choices exist but with wrong branch
            logger.info("BRANCH-PREVIEW: No choices found with branch_id, trying without branch_id...")
            fallback_choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
            fallback_choices = fallback_choices_response.data
            logger.info("BRANCH-PREVIEW: Found {} choices without branch_id filter".format(len(fallback_choices)))
            
            if fallback_choices:
                logger.info("BRANCH-PREVIEW: Updating {} choices to use main branch {}".format(len(fallback_choices), main_branch_id))
                # Update the choices to use the correct branch_id
                for choice in fallback_choices:
                    supabase.table("story_choices").update({"branch_id": main_branch_id}).eq("id", choice["id"]).execute()
                
                # Now try again with the updated choices
                choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
                available_choices = choices_response.data
                logger.info("BRANCH-PREVIEW: After update, found {} choices".format(len(available_choices)))
            
            if not available_choices:
                raise HTTPException(status_code=404, detail="No choices found for chapter {}".format(request.chapter_number))
        
        # Find the selected choice
        selected_choice = None
        for choice in available_choices:
            if str(choice.get('id')) == str(request.choice_id) or str(choice.get('choice_id')) == str(request.choice_id):
                selected_choice = choice
                break
        
        if not selected_choice:
            raise HTTPException(status_code=400, detail="Invalid choice selected for preview")
        
        logger.info("BRANCH-PREVIEW: Selected choice found: {}".format(selected_choice.get('title', 'No title')))
        
        # Get all chapters up to (but not including) the next chapter for context
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).lte("chapter_number", request.chapter_number).order("chapter_number").execute()
        
        previous_chapters = chapters_response.data
        logger.info("BRANCH-PREVIEW: Using {} previous chapters for context".format(len(previous_chapters)))
        
        # Generate the next chapter based on the choice (WITHOUT saving to database)
        next_chapter_number = request.chapter_number + 1
        logger.info("BRANCH-PREVIEW: Generating preview for chapter {} based on choice".format(next_chapter_number))
        
        # Use the story service to generate the next chapter
        try:
            logger.info("BRANCH-PREVIEW: Calling story_service.generate_next_chapter...")
            logger.info("BRANCH-PREVIEW: story_title='{}'".format(story.get('story_title', 'Unknown')))
            logger.info("BRANCH-PREVIEW: previous_chapters_count={}".format(len(previous_chapters)))
            logger.info("BRANCH-PREVIEW: selected_choice_title='{}'".format(selected_choice.get('title', 'Unknown')))
            logger.info("BRANCH-PREVIEW: next_chapter_number={}".format(next_chapter_number))
            
            next_chapter_result = await story_service.generate_next_chapter_with_dna(
                story=story,
                previous_Chapters=previous_chapters,
                selected_choice=selected_choice,
                next_chapter_number=next_chapter_number,
                user_id=user.id
            )
            logger.info("BRANCH-PREVIEW: Chapter {} preview generated successfully".format(next_chapter_number))
            logger.info("BRANCH-PREVIEW: Result keys: {}".format(list(next_chapter_result.keys()) if next_chapter_result else 'None'))
            
            chapter_content = next_chapter_result.get("chapter_content") or next_chapter_result.get("content", "")
            
        except Exception as generation_error:
            logger.error("BRANCH-PREVIEW: Chapter generation failed: {}".format(str(generation_error)))
            import traceback
            logger.error("BRANCH-PREVIEW: Full traceback: {}".format(traceback.format_exc()))
            raise HTTPException(status_code=500, detail="Failed to generate preview chapter: {}".format(str(generation_error)))
        
        # Generate summary for the preview chapter
        logger.info("BRANCH-PREVIEW: Generating summary for preview chapter {}...".format(next_chapter_number))
        
        try:
            from chapter_summary import generate_chapter_summary
            
            # Get previous chapter summaries for context
            previous_summaries = []
            if previous_chapters:
                for prev_chapter in previous_chapters:
                    if prev_chapter.get("summary"):
                        previous_summaries.append(prev_chapter["summary"])
                    else:
                        # If no summary exists, create a quick one from content
                        prev_content = prev_chapter.get("content", "")[:500] + "..."
                        previous_summaries.append("Previous chapter: {}".format(prev_content))
            
            # Build story context for summary
            story_context = "STORY: {}\nOUTLINE: {}".format(story.get('story_title', 'Untitled Story'), story.get('story_outline', ''))
            if previous_summaries:
                story_context += "\n\nPREVIOUS CHAPTERS:\n" + '\n'.join(previous_summaries)
            
            # Generate summary
            summary_result = generate_chapter_summary(
                chapter_content=chapter_content,
                chapter_number=next_chapter_number,
                story_context=story_context,
                story_title=story.get("story_title", "Untitled Story")
            )
            
            chapter_summary = ""
            if summary_result["success"]:
                chapter_summary = summary_result["summary"]
                logger.info("BRANCH-PREVIEW: Summary generated successfully ({}) chars".format(len(chapter_summary)))
            else:
                logger.warning("BRANCH-PREVIEW: Summary generation failed: {}".format(summary_result['error']))
                chapter_summary = "Summary generation failed: {}".format(summary_result['error'])
                
        except Exception as summary_error:
            logger.error("BRANCH-PREVIEW: Summary generation error: {}".format(str(summary_error)))
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
            "message": "Preview generated for chapter {} based on choice: {}".format(next_chapter_number, selected_choice.get('title', 'Unknown'))
        }
        
        logger.info("BRANCH-PREVIEW: Successfully generated preview for chapter {}".format(next_chapter_number))
        return response_payload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("BRANCH-PREVIEW: Unexpected error: {}".format(str(e)))
        import traceback
        logger.error("BRANCH-PREVIEW: Full traceback: {}".format(traceback.format_exc()))
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
        logger.info("CREATE-BRANCH: Creating new branch from chapter {}, choice {}".format(request.chapter_number, request.choice_id))
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", request.story_id).eq("user_id", user.id).execute()
        if not story_response.data:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story = story_response.data[0]
        logger.info("âœ… CREATE-BRANCH: Story verified: {}".format(story.get('story_title', 'Untitled')))
        
        # Get the main branch ID
        main_branch_id = await get_main_branch_id(request.story_id)
        
        # Validate the choice exists
        choices_response = supabase.table("story_choices").select("*").eq("story_id", request.story_id).eq("branch_id", main_branch_id).eq("user_id", user.id).eq("chapter_number", request.chapter_number).execute()
        
        available_choices = choices_response.data
        if not available_choices:
            raise HTTPException(status_code=404, detail="No choices found for chapter {}".format(request.chapter_number))
        
        # Find the selected choice
        selected_choice = None
        for choice in available_choices:
            if str(choice.get('id')) == str(request.choice_id) or str(choice.get('choice_id')) == str(request.choice_id):
                selected_choice = choice
                break
        
        if not selected_choice:
            raise HTTPException(status_code=400, detail="Invalid choice selected for branching")
        
        logger.info("CREATE-BRANCH: Selected choice found: {}".format(selected_choice.get('title', 'No title')))
        
        # Create new branch
        new_branch_id = await create_new_branch(
            story_id=request.story_id,
            parent_branch_id=main_branch_id,
            branched_from_chapter=request.chapter_number,
            branch_name="branch_from_ch{}_{}".format(request.chapter_number, selected_choice.get('title', 'choice')[:20])
        )
        
        logger.info("âœ… CREATE-BRANCH: New branch created: {}".format(new_branch_id))
        
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
        logger.info("CREATE-BRANCH: Generating chapter {} for new branch".format(next_chapter_number))
        
        # Get chapters from the new branch for context
        chapters_response = supabase.table("Chapters").select("*").eq("story_id", request.story_id).eq("branch_id", new_branch_id).lte("chapter_number", request.chapter_number).order("chapter_number").execute()
        
        previous_chapters = chapters_response.data
        
        # Generate the next chapter
        next_chapter_result = await story_service.generate_next_chapter_with_dna(
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
                supabase=supabase
            )
        
        return {
            "success": True,
            "message": "New branch created successfully from chapter {}".format(request.chapter_number),
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
        logger.error("CREATE-BRANCH: Unexpected error: {}".format(str(e)))
        import traceback
        logger.error("CREATE-BRANCH: Full traceback: {}".format(traceback.format_exc()))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/story/{story_id}/branches")
async def get_story_branches_endpoint(
    story_id: int,
    user = Depends(get_authenticated_user)
):
    """Get all branches for a story to display in the branch visualization."""
    try:
        logger.info("Getting branches for story {}".format(story_id))
        
        # Verify story belongs to user
        story_response = supabase.table("Stories").select("*").eq("id", story_id).eq("user_id", user.id).execute()
        
        if not story_response.data:
            logger.error("âŒ DEBUG - Story {} not found for user {}".format(story_id, user.id))
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
        story_data = story_response.data[0]
        logger.info("âœ… DEBUG - Found story: {}".format(story_data.get('story_title', 'Untitled')))
        
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
        
        logger.info("âœ… DEBUG - Found {} Chapters for story {}".format(len(Chapters_info), story_id))
        
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
        logger.error("âŒ DEBUG - Failed to get Chapters for story {}: {}".format(story_id, e))
        raise HTTPException(status_code=500, detail="Debug query failed: {}".format(str(e)))

async def get_next_chapter_version_number(story_id, chapter_number, supabase):
    """Get the next version number for a chapter (highest + 1)."""
    response = supabase.table("Chapters").select("version_number").eq("story_id", story_id).eq("chapter_number", chapter_number).execute()
    versions = [row["version_number"] for row in response.data] if response.data else []
    return max(versions) + 1 if versions else 1

async def deactivate_previous_chapter_versions(story_id, chapter_number, supabase):
    """Set is_active=False for all previous versions of a chapter."""
    supabase.table("Chapters") \
        .update({"is_active": False}) \
        .eq("story_id", story_id) \
        .eq("chapter_number", chapter_number) \
        .execute()

async def save_choices_for_chapter(story_id, chapter_id, chapter_number, choices, user_id, supabase):
    """Save choices to the story_choices table for any chapter."""
    for i, choice in enumerate(choices, 1):
        choice_record = {
            "story_id": story_id,
            "chapter_id": chapter_id,
            "chapter_number": chapter_number,
            "choice_id": choice.get("id", f"choice_{i}"),
            "title": choice.get("title", ""),
            "description": choice.get("description", ""),
            "story_impact": choice.get("story_impact", ""),
            "choice_type": choice.get("choice_type", ""),
            "user_id": user_id,
            "is_selected": False
        }
        supabase.table("story_choices").insert(choice_record).execute()
