"""
Unified story service with async operations and smart caching.
"""

import uuid
from typing import List, Optional
from datetime import timedelta

from models.story_models import Story, Chapter, StoryWithChapters
from .database_service import db_service
from .cache_service import cache_service
from logger_config import setup_logger

logger = setup_logger(__name__)

class StoryService:
    """
    High-level story operations with caching and performance optimization.
    Provides a unified interface for all story-related operations.
    """
    
    def __init__(self):
        self.db = db_service
        self.cache = cache_service
    
    @cache_service.cached(ttl=timedelta(minutes=30), key_prefix="story")
    async def get_story(self, story_id: int, user_id: Optional[uuid.UUID] = None) -> Optional[Story]:
        """
        Get story by ID with caching.
        
        Args:
            story_id: Story ID to fetch
            user_id: Optional user ID for access control
            
        Returns:
            Story object or None if not found
        """
        logger.info(f"Fetching story {story_id} for user {user_id}")
        
        try:
            # Try async first, fallback to sync
            story = await self.db.get_story_async(story_id, user_id)
            if not story:
                story = self.db.get_story_sync(story_id, user_id)
            
            if story:
                logger.info(f"Found story {story_id}: {story.title}")
            else:
                logger.warning(f"Story {story_id} not found")
            
            return story
        except Exception as e:
            logger.error(f"Error fetching story {story_id}: {e}")
            return None
    
    @cache_service.cached(ttl=timedelta(minutes=15), key_prefix="chapters")
    async def get_chapters(self, story_id: int) -> List[Chapter]:
        """
        Get all chapters for a story with caching.
        
        Args:
            story_id: Story ID to fetch chapters for
            
        Returns:
            List of Chapter objects
        """
        logger.info(f"Fetching chapters for story {story_id}")
        
        try:
            # Try async first, fallback to sync
            chapters = await self.db.get_chapters_async(story_id)
            if not chapters:
                chapters = self.db.get_chapters_sync(story_id)
            
            logger.info(f"Found {len(chapters)} chapters for story {story_id}")
            return chapters
        except Exception as e:
            logger.error(f"Error fetching chapters for story {story_id}: {e}")
            return []
    
    async def get_story_with_chapters(
        self, 
        story_id: int, 
        user_id: Optional[uuid.UUID] = None
    ) -> Optional[StoryWithChapters]:
        """
        Get story with all its chapters in one optimized call.
        
        Args:
            story_id: Story ID to fetch
            user_id: Optional user ID for access control
            
        Returns:
            StoryWithChapters object or None if story not found
        """
        logger.info(f"Fetching complete story {story_id} with chapters")
        
        # Use caching for both story and chapters
        story = await self.get_story(story_id, user_id)
        if not story:
            return None
        
        chapters = await self.get_chapters(story_id)
        
        return StoryWithChapters(story=story, chapters=chapters)
    
    @cache_service.cached(ttl=timedelta(minutes=10), key_prefix="user_stories")
    async def get_user_stories(self, user_id: uuid.UUID) -> List[Story]:
        """
        Get all stories for a user with caching.
        
        Args:
            user_id: User ID to fetch stories for
            
        Returns:
            List of Story objects
        """
        logger.info(f"Fetching stories for user {user_id}")
        
        try:
            stories = await self.db.get_user_stories_async(user_id)
            logger.info(f"Found {len(stories)} stories for user {user_id}")
            return stories
        except Exception as e:
            logger.error(f"Error fetching stories for user {user_id}: {e}")
            return []
    
    async def invalidate_story_cache(self, story_id: int):
        """
        Invalidate all cached data for a story.
        
        Args:
            story_id: Story ID to invalidate cache for
        """
        logger.info(f"Invalidating cache for story {story_id}")
        
        await self.cache.clear_pattern(f"story:{story_id}")
        await self.cache.clear_pattern(f"chapters:{story_id}")
        await self.cache.clear_pattern(f"embedding:{story_id}")
    
    async def invalidate_user_cache(self, user_id: uuid.UUID):
        """
        Invalidate all cached data for a user.
        
        Args:
            user_id: User ID to invalidate cache for
        """
        logger.info(f"Invalidating cache for user {user_id}")
        
        await self.cache.clear_pattern(f"user_stories:{user_id}")
    
    def get_story_sync(self, story_id: int, user_id: Optional[uuid.UUID] = None) -> Optional[Story]:
        """
        Synchronous story fetch for compatibility.
        
        Args:
            story_id: Story ID to fetch
            user_id: Optional user ID for access control
            
        Returns:
            Story object or None if not found
        """
        return self.db.get_story_sync(story_id, user_id)
    
    def get_chapters_sync(self, story_id: int) -> List[Chapter]:
        """
        Synchronous chapters fetch for compatibility.
        
        Args:
            story_id: Story ID to fetch chapters for
            
        Returns:
            List of Chapter objects
        """
        return self.db.get_chapters_sync(story_id)
    
    async def get_service_stats(self) -> dict:
        """Get service performance statistics."""
        cache_stats = self.cache.get_cache_stats()
        
        return {
            "cache": cache_stats,
            "database_pool_initialized": self.db._async_pool is not None
        }

# Global story service instance
story_service = StoryService()