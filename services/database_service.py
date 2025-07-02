"""
Database service with connection pooling and async operations.
"""

import asyncio
import asyncpg
import psycopg
from typing import List, Optional, Dict, Any, Union
from contextlib import asynccontextmanager
import uuid
from config import settings
from logger_config import setup_logger
from models.story_models import Story, Chapter

logger = setup_logger(__name__)

class DatabaseService:
    """
    High-performance database service with connection pooling.
    Handles both sync and async operations with automatic fallback.
    """
    
    def __init__(self):
        self._async_pool: Optional[asyncpg.Pool] = None
        self._sync_connection_string = self._get_sync_connection_string()
        self._async_connection_string = self._get_async_connection_string()
    
    def _get_sync_connection_string(self) -> str:
        """Get connection string for synchronous operations."""
        connection_string = settings.get_postgres_connection_string()
        if "postgresql+psycopg://" in connection_string:
            return connection_string.replace("postgresql+psycopg://", "postgresql://")
        return connection_string
    
    def _get_async_connection_string(self) -> str:
        """Get connection string for async operations."""
        connection_string = settings.get_postgres_connection_string()
        # Remove any psycopg-specific prefixes for asyncpg
        return connection_string.replace("postgresql+psycopg://", "postgresql://")
    
    async def initialize_async_pool(self, min_size: int = 5, max_size: int = 20):
        """Initialize async connection pool."""
        try:
            self._async_pool = await asyncpg.create_pool(
                self._async_connection_string,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60
            )
            logger.info(f"Async database pool initialized (min={min_size}, max={max_size})")
        except Exception as e:
            logger.error(f"Failed to initialize async pool: {e}")
            self._async_pool = None
    
    async def close_async_pool(self):
        """Close async connection pool."""
        if self._async_pool:
            await self._async_pool.close()
            self._async_pool = None
            logger.info("Async database pool closed")
    
    @asynccontextmanager
    async def get_async_connection(self):
        """Get async database connection from pool."""
        if not self._async_pool:
            await self.initialize_async_pool()
        
        if self._async_pool:
            async with self._async_pool.acquire() as connection:
                yield connection
        else:
            # Fallback to direct connection
            connection = await asyncpg.connect(self._async_connection_string)
            try:
                yield connection
            finally:
                await connection.close()
    
    def get_sync_connection(self):
        """Get synchronous database connection."""
        return psycopg.connect(self._sync_connection_string)
    
    async def get_story_async(self, story_id: int, user_id: Optional[uuid.UUID] = None) -> Optional[Story]:
        """Get story by ID asynchronously."""
        async with self.get_async_connection() as conn:
            # Try Stories table first
            query = 'SELECT * FROM "Stories" WHERE id = $1'
            params = [story_id]
            
            if user_id:
                query += ' AND user_id = $2'
                params.append(user_id)
            
            try:
                row = await conn.fetchrow(query, *params)
                if row:
                    return Story.from_stories_table(dict(row))
            except Exception as e:
                logger.warning(f"Could not query Stories table: {e}")
            
            # Try stories table
            query = 'SELECT * FROM stories WHERE id = $1'
            params = [story_id]
            
            if user_id:
                query += ' AND user_id = $2'
                params.append(user_id)
            
            try:
                row = await conn.fetchrow(query, *params)
                if row:
                    return Story.from_stories_lowercase(dict(row))
            except Exception as e:
                logger.warning(f"Could not query stories table: {e}")
            
            return None
    
    def get_story_sync(self, story_id: int, user_id: Optional[uuid.UUID] = None) -> Optional[Story]:
        """Get story by ID synchronously."""
        with self.get_sync_connection() as conn:
            with conn.cursor() as cur:
                # Try Stories table first
                query = 'SELECT * FROM "Stories" WHERE id = %s'
                params = [story_id]
                
                if user_id:
                    query += ' AND user_id = %s'
                    params.append(user_id)
                
                try:
                    cur.execute(query, params)
                    row = cur.fetchone()
                    if row:
                        columns = [desc[0] for desc in cur.description]
                        data = dict(zip(columns, row))
                        return Story.from_stories_table(data)
                except Exception as e:
                    logger.warning(f"Could not query Stories table: {e}")
                
                # Try stories table
                query = 'SELECT * FROM stories WHERE id = %s'
                params = [story_id]
                
                if user_id:
                    query += ' AND user_id = %s'
                    params.append(user_id)
                
                try:
                    cur.execute(query, params)
                    row = cur.fetchone()
                    if row:
                        columns = [desc[0] for desc in cur.description]
                        data = dict(zip(columns, row))
                        return Story.from_stories_lowercase(data)
                except Exception as e:
                    logger.warning(f"Could not query stories table: {e}")
                
                return None
    
    async def get_chapters_async(self, story_id: int) -> List[Chapter]:
        """Get all chapters for a story asynchronously."""
        chapters = []
        
        async with self.get_async_connection() as conn:
            # Try Chapters table first
            try:
                rows = await conn.fetch(
                    'SELECT * FROM "Chapters" WHERE story_id = $1 ORDER BY chapter_number',
                    story_id
                )
                for row in rows:
                    chapters.append(Chapter.from_chapters_table(dict(row)))
                
                if chapters:
                    return chapters
            except Exception as e:
                logger.warning(f"Could not query Chapters table: {e}")
            
            # Try chapters table
            try:
                rows = await conn.fetch(
                    'SELECT * FROM chapters WHERE story_id = $1 ORDER BY chapter_number',
                    story_id
                )
                for row in rows:
                    chapters.append(Chapter.from_chapters_lowercase(dict(row)))
            except Exception as e:
                logger.warning(f"Could not query chapters table: {e}")
        
        return chapters
    
    def get_chapters_sync(self, story_id: int) -> List[Chapter]:
        """Get all chapters for a story synchronously."""
        chapters = []
        
        with self.get_sync_connection() as conn:
            with conn.cursor() as cur:
                # Try Chapters table first
                try:
                    cur.execute(
                        'SELECT * FROM "Chapters" WHERE story_id = %s ORDER BY chapter_number',
                        [story_id]
                    )
                    rows = cur.fetchall()
                    columns = [desc[0] for desc in cur.description]
                    
                    for row in rows:
                        data = dict(zip(columns, row))
                        chapters.append(Chapter.from_chapters_table(data))
                    
                    if chapters:
                        return chapters
                except Exception as e:
                    logger.warning(f"Could not query Chapters table: {e}")
                
                # Try chapters table
                try:
                    cur.execute(
                        'SELECT * FROM chapters WHERE story_id = %s ORDER BY chapter_number',
                        [story_id]
                    )
                    rows = cur.fetchall()
                    columns = [desc[0] for desc in cur.description]
                    
                    for row in rows:
                        data = dict(zip(columns, row))
                        chapters.append(Chapter.from_chapters_lowercase(data))
                except Exception as e:
                    logger.warning(f"Could not query chapters table: {e}")
        
        return chapters
    
    async def get_user_stories_async(self, user_id: uuid.UUID) -> List[Story]:
        """Get all stories for a user asynchronously."""
        stories = []
        
        async with self.get_async_connection() as conn:
            # Get from Stories table
            try:
                rows = await conn.fetch(
                    'SELECT * FROM "Stories" WHERE user_id = $1 ORDER BY created_at DESC',
                    user_id
                )
                for row in rows:
                    stories.append(Story.from_stories_table(dict(row)))
            except Exception as e:
                logger.warning(f"Could not query Stories table: {e}")
            
            # Get from stories table (avoid duplicates)
            try:
                rows = await conn.fetch(
                    'SELECT * FROM stories WHERE user_id = $1 ORDER BY created_at DESC',
                    user_id
                )
                existing_ids = {story.id for story in stories}
                for row in rows:
                    story = Story.from_stories_lowercase(dict(row))
                    if story.id not in existing_ids:
                        stories.append(story)
            except Exception as e:
                logger.warning(f"Could not query stories table: {e}")
        
        return stories

# Global database service instance
db_service = DatabaseService()