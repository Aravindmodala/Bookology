"""
Optimized main.py with service layer architecture and async operations.
"""

import asyncio
from typing import Dict, Any, List
from contextlib import asynccontextmanager
import json

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
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

logger = setup_logger(__name__)

# Authentication
auth_scheme = HTTPBearer()

# Initialize services at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with service initialization."""
    logger.info("Starting Bookology backend with optimized services...")
    
    try:
        # Initialize async database pool
        await db_service.initialize_async_pool(min_size=5, max_size=20)
        
        # Initialize cache service (Redis optional)
        redis_url = settings.__dict__.get('REDIS_URL')
        await cache_service.initialize_redis(redis_url)
        
        # Initialize embedding service
        await embedding_service._ensure_initialized()
        
        # Initialize Supabase client
        global supabase
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized")
        
        logger.info("All services initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        yield
    finally:
        # Cleanup
        await db_service.close_async_pool()
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

class StoryChatRequest(BaseModel):
    """Input model for story chat interactions."""
    story_id: int = Field(..., gt=0, description="ID of the story to chat about")
    message: str = Field(..., min_length=1, max_length=1000, description="User message")

# Initialize chatbot (keep for compatibility)
story_chatbot = StoryChatbot()

# Initialize Supabase client globally
supabase: Optional[Client] = None

# Authentication dependency (keep original for compatibility)
async def get_authenticated_user(token = Depends(auth_scheme)):
    """Get authenticated user - optimized version."""
    try:
        # This would integrate with your existing auth system
        # For now, keeping the original logic
        from supabase import create_client
        
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_SERVICE_KEY
        supabase = create_client(supabase_url, supabase_key)
        
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
        # Try authentication
        from supabase import create_client
        
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_SERVICE_KEY
        supabase = create_client(supabase_url, supabase_key)
        
        user_response = supabase.auth.get_user(token.credentials)
        user = user_response.user
        
        return user  # Return user or None
        
    except Exception as e:
        logger.info(f"Optional authentication failed (this is OK): {e}")
        return None  # Return None instead of raising error

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

# Optimized stories endpoint
@app.get("/stories")
async def get_user_stories_optimized(user = Depends(get_authenticated_user)):
    """Get user stories with caching and async operations."""
    logger.info(f"Fetching stories for user {user.id}")
    
    try:
        stories = await story_service.get_user_stories(user.id)
        
        # Convert to API format
        story_list = []
        for story in stories:
            story_list.append({
                "id": story.id,
                "title": story.title,
                "outline": story.outline or "",
                "created_at": story.created_at.isoformat(),
                "source_table": story.source_table,
                "chapter_count": story.current_chapter or 0
            })
        
        return {"stories": story_list}
        
    except Exception as e:
        logger.error(f"Failed to fetch stories for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch stories"
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

# Optimized chat endpoint
@app.post("/story_chat")
async def story_chat_optimized(body: StoryChatRequest, user = Depends(get_authenticated_user)):
    """Process story chat with optimized embedding lookup."""
    logger.info(f"Story chat request from user {user.id} for story {body.story_id}")
    
    try:
        # Verify story access
        story = await story_service.get_story(body.story_id, user.id)
        if not story:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story not found"
            )
        
        # Ensure embeddings exist
        await embedding_service.ensure_embeddings(body.story_id)
        
        # Process chat with proper type conversion
        response = story_chatbot.chat(
            str(user.id),
            str(body.story_id),  # Convert int to str for chatbot
            body.message
        )
        
        logger.info("Story chat response generated successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Story chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat processing failed"
        )

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
        
        logger.info(f"Successfully generated outline with {len(outline_json.get('chapters', []))} chapters")
        logger.info(f"📊 LLM Usage: {usage_metrics.get('estimated_total_tokens', 0)} tokens, {usage_metrics.get('total_word_count', 0)} words")
        
        # 🚀 IMMEDIATELY SAVE TO DATABASE (only if user is authenticated)
        story_id = None
        database_save_success = False
        
        if user:
            try:
                logger.info(f"💾 Auto-saving outline to database for user {user.id}...")
                
                # Prepare story data for immediate database save - use EXACT JSON fields + usage metrics
                story_data = {
                    "user_id": user.id,
                    "story_title": outline_json.get("book_title", "Untitled Story"),
                    "story_outline": formatted_text,  # Save the formatted text as outline
                    "total_chapters": outline_json.get("estimated_total_chapters", 1),
                    "current_chapter": 0,  # 0 = outline only, no chapters written yet
                    
                    # Map exact JSON fields to database columns (only columns that exist)
                    "outline_json": json.dumps(outline_json),  # Store full JSON as text
                    "genre": outline_json.get("genre"),
                    "theme": outline_json.get("theme"), 
                    "style": outline_json.get("style"),
                    "language": outline_json.get("language", "English"),
                    "tags": json.dumps(outline_json.get("tags", [])),  # Convert array to JSON string
                    "main_characters": outline_json.get("main_characters", []),  # JSONB column - keep as array
                    "key_locations": outline_json.get("key_locations", []),  # JSONB column - keep as array
                    
                    # LLM Usage Metrics
                    "temperature_used": usage_metrics.get("temperature_used"),
                    "token_count_total": usage_metrics.get("estimated_total_tokens"),
                    "word_count_total": usage_metrics.get("total_word_count"),
                    "model_used": usage_metrics.get("model_used"),
                    
                    # Note: tone_keywords is in JSON but not in database schema, so excluded
                }
                
                # Remove None values to avoid database errors
                story_data = {k: v for k, v in story_data.items() if v is not None and v != [] and v != ""}
                
                logger.info(f"Saving outline to database with fields: {list(story_data.keys())}")
                
                try:
                    # Try full metadata insert first
                    story_response = supabase.table("Stories").insert(story_data).execute()
                    story_id = story_response.data[0]["id"]
                    database_save_success = True
                    logger.info(f"✅ Full metadata auto-save successful with story_id: {story_id}")
                    
                except Exception as full_save_error:
                    logger.warning(f"⚠️ Full metadata save failed: {full_save_error}")
                    logger.info("🔄 Attempting fallback save with minimal fields...")
                    
                    # Fallback: Save with minimal required fields only
                    minimal_story_data = {
                        "user_id": user.id,
                        "story_title": outline_json.get("book_title", "Untitled Story"),
                        "story_outline": formatted_text,
                        "total_chapters": outline_json.get("estimated_total_chapters", 1),
                        "current_chapter": 0
                    }
                    
                    try:
                        story_response = supabase.table("Stories").insert(minimal_story_data).execute()
                        story_id = story_response.data[0]["id"]
                        database_save_success = True
                        logger.info(f"✅ Fallback auto-save successful with story_id: {story_id}")
                        logger.info("📝 Note: Only basic fields saved. Rich metadata can be added when database schema is updated.")
                        
                    except Exception as minimal_save_error:
                        logger.error(f"❌ Even minimal save failed: {minimal_save_error}")
                        database_save_success = False
                
            except Exception as db_error:
                logger.warning(f"❌ Database auto-save failed: {db_error}")
                # Don't fail the entire request - still return the outline to user
                database_save_success = False
        else:
            logger.info("👤 Anonymous user - outline not saved to database")
        
        # Return response with both outline AND database info
        return {
            "success": True,
            # Frontend display (what the user sees)
            "expanded_prompt": formatted_text,  # Formatted text with static fields + JSON data
            "outline_text": formatted_text,    # Same as above for compatibility
            
            # Database info
            "auto_saved": database_save_success,
            "story_id": story_id,  # Frontend can use this for future operations
            
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
            "chapters": metadata["chapters"],
            
            # Additional info
            "generation_info": {
                "json_parsing_success": True,
                "chapters_generated": len(outline_json.get("chapters", [])),
                "characters_created": len(metadata["main_characters"]),
                "locations_created": len(metadata["key_locations"]),
                "total_estimated_words": metadata["total_estimated_words"],
                "ready_for_database": True,
                "auto_saved_to_db": database_save_success
            }
        }
        
    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/lc_generate_chapter")
async def generate_chapter_endpoint(chapter: ChapterInput):
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
        logger.info(f"📊 Generated chapter length: {len(result)} characters")
        
        return {
            "chapter_1": result,  # Frontend expects this field name
            "chapter": result,    # Keep for compatibility
            "metadata": {
                "chapter_number": chapter.chapter_number,
                "word_count": len(result.split()),
                "character_count": len(result),
                "generation_success": True
            }
        }
    except Exception as e:
        logger.error(f"❌ Chapter generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class JsonChapterInput(BaseModel):
    """Input model for generating chapters from JSON outline."""
    outline_json: Dict[str, Any] = Field(..., description="JSON outline data")
    chapter_number: int = Field(default=1, ge=1, description="Chapter number to generate")

@app.post("/lc_generate_chapter_from_json")
async def generate_chapter_from_json_endpoint(chapter: JsonChapterInput):
    """Generate story chapter specifically from JSON outline data."""
    logger.info(f"📖 Starting Chapter {chapter.chapter_number} generation from JSON outline...")
    
    # Log the JSON outline we received
    logger.info("📥 RECEIVED JSON OUTLINE FOR CHAPTER GENERATION:")
    logger.info("=" * 80)
    logger.info(json.dumps(chapter.outline_json, indent=2, ensure_ascii=False))
    logger.info("=" * 80)
    
    try:
        from lc_book_generator import BookStoryGenerator
        generator = BookStoryGenerator()
        
        logger.info("🚀 Invoking BookStoryGenerator with JSON data...")
        
        # Use the JSON-specific method
        result = generator.generate_chapter_from_json(chapter.outline_json, chapter.chapter_number)
        
        logger.info(f"✅ Chapter {chapter.chapter_number} generation from JSON completed!")
        logger.info(f"📊 Generated chapter length: {len(result)} characters")
        logger.info(f"📊 Generated word count: {len(result.split())} words")
        
        # Extract chapter metadata from JSON for response
        chapters = chapter.outline_json.get("chapters", [])
        target_chapter = next(
            (ch for ch in chapters if ch.get("chapter_number") == chapter.chapter_number),
            {}
        )
        
        return {
            "chapter": result,
            "metadata": {
                "chapter_number": chapter.chapter_number,
                "chapter_title": target_chapter.get("chapter_title", f"Chapter {chapter.chapter_number}"),
                "word_count": len(result.split()),
                "character_count": len(result),
                "estimated_word_count": target_chapter.get("estimated_word_count", 0),
                "generation_success": True,
                "source": "json_outline"
            },
            "chapter_outline_data": target_chapter
        }
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
                "chapters": json_data.get("chapters", [])
            }
            
            # Calculate total estimated words from chapters
            total_words = sum(
                chapter.get("estimated_word_count", 0) 
                for chapter in extracted_metadata["chapters"]
            )
            extracted_metadata["total_estimated_words"] = total_words or story_data.total_estimated_words
            
            # Extract Chapter 1 specific metadata
            if extracted_metadata["chapters"]:
                chapter_1_data = next(
                    (ch for ch in extracted_metadata["chapters"] if ch.get("chapter_number") == 1),
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
            logger.info(f"🔍 DEBUGGING THEME/STYLE:")
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
        
        # Prepare basic chapter data
        chapter_insert_data = {
            "story_id": story_id,
            "chapter_number": 1,
            "title": chapter_1_metadata.get("title", "Chapter 1"),
            "content": story_data.chapter_1_content,
        }
        
        # Add optional chapter fields
        optional_chapter_fields = {
            "summary": chapter_1_metadata.get("summary", "First chapter"),
            "word_count": word_count,
            "reading_time_minutes": reading_time,
            "cliffhanger_cta": chapter_1_metadata.get("cliffhanger_cta", ""),
        }
        
        # Add any additional metadata from JSON if available
        if story_data.outline_json and "chapters" in story_data.outline_json:
            chapter_1_full = next(
                (ch for ch in story_data.outline_json["chapters"] if ch.get("chapter_number") == 1),
                {}
            )
            if chapter_1_full:
                optional_chapter_fields.update({
                    "key_events": chapter_1_full.get("key_events"),
                    "character_appearances": chapter_1_full.get("character_appearances"),
                    "location": chapter_1_full.get("location"),
                    "mood": chapter_1_full.get("mood")
                })
        
        # Only add optional fields that have values
        for field, value in optional_chapter_fields.items():
            if value is not None and value != "" and value != []:
                chapter_insert_data[field] = value
        
        logger.info(f"Attempting to insert chapter with fields: {list(chapter_insert_data.keys())}")
        
        # Try to insert chapter with fallback handling
        try:
            chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
            chapter_id = chapter_response.data[0]["id"]
            logger.info(f"Chapter inserted successfully with metadata: {chapter_id}")
        except Exception as chapter_error:
            logger.warning(f"Full chapter metadata insert failed: {chapter_error}")
            logger.info("Falling back to minimal chapter insert...")
            
            # Fallback: minimal chapter data
            minimal_chapter_data = {
                "story_id": story_id,
                "chapter_number": 1,
                "title": chapter_1_metadata.get("title", "Chapter 1"),
                "content": story_data.chapter_1_content,
            }
            
            try:
                chapter_response = supabase.table("Chapters").insert(minimal_chapter_data).execute()
                chapter_id = chapter_response.data[0]["id"]
                logger.info(f"Chapter inserted successfully with minimal data: {chapter_id}")
            except Exception as minimal_chapter_error:
                logger.error(f"Even minimal chapter insert failed: {minimal_chapter_error}")
                # Don't fail the entire save if chapter insert fails
                chapter_id = None
                logger.warning("Story saved but Chapter 1 could not be inserted due to schema issues")
        
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
        else:
            success_message += " (Note: Chapter 1 metadata couldn't be saved due to schema limitations)"
            
        return {
            "message": success_message,
            "story_id": story_id,
            "chapter_id": chapter_id,
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
                "chapters_in_outline": len(extracted_metadata.get("chapters", []))
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
            "chapters": outline_json.get("chapters", []),
            "writing_guidelines": outline_json.get("writing_guidelines"),
            "conflict": outline_json.get("conflict")
        }
        
        # Step 3: Analyze what we extracted
        analysis = {
            "total_fields_extracted": len([v for v in extracted_fields.values() if v]),
            "has_characters": len(extracted_fields["main_characters"]) > 0,
            "has_locations": len(extracted_fields["key_locations"]) > 0,
            "has_chapters": len(extracted_fields["chapters"]) > 0,
            "has_tags": len(extracted_fields["tags"]) > 0,
            "estimated_words": sum(
                ch.get("estimated_word_count", 0) 
                for ch in extracted_fields["chapters"]
            ),
            "chapter_count": len(extracted_fields["chapters"])
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
                "has_structured_data": analysis["has_characters"] and analysis["has_chapters"],
                "can_save_to_db": bool(extracted_fields["title"] and extracted_fields["genre"])
            },
            "next_steps": [
                "Use this JSON in /stories/save endpoint",
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
            "chapters_count": len(result["outline_json"].get("chapters", [])),
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
        chapters = outline_json.get("chapters", [])
        chapter_1_data = next(
            (ch for ch in chapters if ch.get("chapter_number") == 1),
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
                "total_chapters_planned": len(chapters),
                "total_estimated_book_words": sum(ch.get("estimated_word_count", 0) for ch in chapters)
            },
            
            # Next Steps for Implementation
            "implementation_ready": {
                "has_complete_json": bool(outline_json),
                "has_chapter_content": bool(chapter_1_content and not chapter_1_content.startswith("❌")),
                "ready_for_database": True,
                "can_continue_to_chapter_2": bool(len(chapters) > 1)
            },
            
            "usage_instructions": {
                "save_to_database": "Use the /stories/save endpoint with this data",
                "generate_more_chapters": "Use /lc_generate_chapter_from_json with chapter_number=2,3,etc",
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
                "chapters_count": len(outline_json.get("chapters", [])),
                "characters_count": len(metadata["main_characters"]),
                "locations_count": len(metadata["key_locations"])
            },
            "database_fields_saved": list(story_data.keys()) if database_save_success else [],
            "message": "✅ Auto-save outline test completed! JSON outline was generated and saved to database automatically." if database_save_success else "⚠️ Outline generated but database save failed."
        }
        
    except Exception as e:
        logger.error(f"❌ Auto-save outline test failed: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting optimized server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "main_optimized:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level="debug" if settings.DEBUG else "info"
    )