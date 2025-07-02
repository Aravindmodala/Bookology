"""
Optimized main.py with service layer architecture and async operations.
"""

import asyncio
from typing import Dict, Any, List
from contextlib import asynccontextmanager

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
    format: str = Field(..., pattern="^(book|movie)$")
    
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
async def generate_outline_endpoint(story: StoryInput):
    """Generate story outline."""
    try:
        from lc_book_generator import BookStoryGenerator
        generator = BookStoryGenerator()
        
        if story.format == "book":
            result = generator.generate_book_outline(story.idea)
        else:
            result = generator.generate_movie_outline(story.idea)
            
        return {"expanded_prompt": result}
    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/lc_generate_chapter")
async def generate_chapter_endpoint(chapter: ChapterInput):
    """Generate story chapter."""
    try:
        from lc_book_generator import BookStoryGenerator
        generator = BookStoryGenerator()
        
        result = generator.generate_chapter(chapter.outline, chapter.chapter_number)
        return {"chapter": result}
    except Exception as e:
        logger.error(f"Chapter generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stories/save")
async def save_story_endpoint(
    story_data: StorySaveInput,
    background_tasks: BackgroundTasks,
    user = Depends(get_authenticated_user)
):
    """Save story with background embedding generation."""
    logger.info(f"Saving story: {story_data.story_title}")
    
    try:
        # Use Supabase client for saving
        story_insert_data = {
            "user_id": user.id,
            "story_title": story_data.story_title,
            "story_outline": story_data.story_outline,
            "total_chapters": 1,
            "current_chapter": 1,
        }
        
        story_response = supabase.table("Stories").insert(story_insert_data).execute()
        story_id = story_response.data[0]["id"]
        
        # Insert chapter 1
        chapter_insert_data = {
            "story_id": story_id,
            "chapter_number": 1,
            "content": story_data.chapter_1_content,
        }
        
        chapter_response = supabase.table("Chapters").insert(chapter_insert_data).execute()
        chapter_id = chapter_response.data[0]["id"]
        
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
        
        return {
            "message": "Story saved successfully!",
            "story_id": story_id,
            "chapter_id": chapter_id
        }
        
    except Exception as e:
        logger.error(f"Story saving failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save story")

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