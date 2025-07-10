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
    
    @cache_service.cached(ttl=timedelta(minutes=15), key_prefix="Chapters")
    async def get_Chapters(self, story_id: int) -> List[Chapter]:
        """
        Get all Chapters for a story with caching.
        
        Args:
            story_id: Story ID to fetch Chapters for
            
        Returns:
            List of Chapter objects
        """
        logger.info(f"Fetching Chapters for story {story_id}")
        
        try:
            # Try async first, fallback to sync
            Chapters = await self.db.get_Chapters_async(story_id)
            if not Chapters:
                Chapters = self.db.get_Chapters_sync(story_id)
            
            logger.info(f"Found {len(Chapters)} Chapters for story {story_id}")
            return Chapters
        except Exception as e:
            logger.error(f"Error fetching Chapters for story {story_id}: {e}")
            return []
    
    async def get_story_with_Chapters(
        self, 
        story_id: int, 
        user_id: Optional[uuid.UUID] = None
    ) -> Optional[StoryWithChapters]:
        """
        Get story with all its Chapters in one optimized call.
        
        Args:
            story_id: Story ID to fetch
            user_id: Optional user ID for access control
            
        Returns:
            StoryWithChapters object or None if story not found
        """
        logger.info(f"Fetching complete story {story_id} with Chapters")
        
        # Use caching for both story and Chapters
        story = await self.get_story(story_id, user_id)
        if not story:
            return None
        
        Chapters = await self.get_Chapters(story_id)
        
        return StoryWithChapters(story=story, Chapters=Chapters)
    
    @cache_service.cached(ttl=timedelta(minutes=10), key_prefix="user_Stories")
    async def get_user_Stories(self, user_id: uuid.UUID) -> List[Story]:
        """
        Get all Stories for a user with caching.
        
        Args:
            user_id: User ID to fetch Stories for
            
        Returns:
            List of Story objects
        """
        logger.info(f"Fetching Stories for user {user_id}")
        
        try:
            Stories = await self.db.get_user_Stories_async(user_id)
            logger.info(f"Found {len(Stories)} Stories for user {user_id}")
            return Stories
        except Exception as e:
            logger.error(f"Error fetching Stories for user {user_id}: {e}")
            return []
    
    async def invalidate_story_cache(self, story_id: int):
        """
        Invalidate all cached data for a story.
        
        Args:
            story_id: Story ID to invalidate cache for
        """
        logger.info(f"Invalidating cache for story {story_id}")
        
        await self.cache.clear_pattern(f"story:{story_id}")
        await self.cache.clear_pattern(f"Chapters:{story_id}")
        await self.cache.clear_pattern(f"embedding:{story_id}")
    
    async def invalidate_user_cache(self, user_id: uuid.UUID):
        """
        Invalidate all cached data for a user.
        
        Args:
            user_id: User ID to invalidate cache for
        """
        logger.info(f"Invalidating cache for user {user_id}")
        
        await self.cache.clear_pattern(f"user_Stories:{user_id}")
    
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
    
    def get_Chapters_sync(self, story_id: int) -> List[Chapter]:
        """
        Synchronous Chapters fetch for compatibility.
        
        Args:
            story_id: Story ID to fetch Chapters for
            
        Returns:
            List of Chapter objects
        """
        return self.db.get_Chapters_sync(story_id)
    
    async def get_service_stats(self) -> dict:
        """Get service performance statistics."""
        cache_stats = self.cache.get_cache_stats()
        
        return {
            "cache": cache_stats,
            "database_pool_initialized": self.db._async_pool is not None
        }

    async def generate_next_chapter(self, story, previous_Chapters, selected_choice, next_chapter_number, user_id=None):
        """
        Generate the next chapter using lc_next_chapter_generator.py's NextChapterGenerator.
        Args:
            story: dict with story details (should include 'story_title' and 'story_outline')
            previous_Chapters: list of chapter dicts (should include 'content' and optionally 'summary')
            selected_choice: dict with the selected choice (should include 'title' and 'description')
            next_chapter_number: int, the chapter number to generate
            user_id: optional, for logging
        Returns:
            dict with generated chapter content, choices, and token metrics
        """
        from lc_next_chapter_generator import NextChapterGenerator
        import asyncio

        story_title = story.get('story_title', 'Untitled Story')
        story_outline = story.get('story_outline', '')
        # Use summaries if available, else use content
        previous_summaries = []
        for ch in previous_Chapters:
            if ch.get('summary'):
                previous_summaries.append(ch['summary'])
            elif ch.get('content'):
                # fallback: use first 500 chars of content
                prev_content = ch.get('content', '')[:500] + '...'
                previous_summaries.append(f"Previous chapter: {prev_content}")
        # Compose user choice string
        user_choice = selected_choice.get('title', '')
        if selected_choice.get('description'):
            user_choice += ': ' + selected_choice['description']
        # Call the generator (run in thread if needed)
        generator = NextChapterGenerator()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, generator.generate_next_chapter,
            story_title, story_outline, previous_summaries, next_chapter_number, user_choice)
        return result

# Global story service instance
story_service = StoryService()