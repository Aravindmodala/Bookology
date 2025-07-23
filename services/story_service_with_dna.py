"""
UPDATED VERSION: Unified story service with Enhanced LLM DNA extraction.
Fixed integration with the enhanced DNA extractor for perfect continuity.
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
    UPDATED VERSION: High-level story operations with Enhanced LLM DNA extraction for perfect continuity.
    Now properly integrated with the enhanced DNA extractor including choice context and plot tracking.
    """
    
    def __init__(self):
        self.db = db_service
        self.cache = cache_service
        logger.info("🧬 StoryServiceWithDNA initialized - Enhanced LLM DNA extraction enabled")
    
    @cache_service.cached(ttl=timedelta(minutes=30), key_prefix="story")
    async def get_story(self, story_id: int, user_id: Optional[uuid.UUID] = None) -> Optional[Story]:
        """Get story by ID with caching."""
        logger.info(f"Fetching story {story_id} for user {user_id}")
        
        try:
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
        """Get all Chapters for a story with caching."""
        logger.info(f"Fetching Chapters for story {story_id}")
        
        try:
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
        """Get story with all its Chapters in one optimized call."""
        logger.info(f"Fetching complete story {story_id} with Chapters")
        
        story = await self.get_story(story_id, user_id)
        if not story:
            return None
        
        Chapters = await self.get_Chapters(story_id)
        return StoryWithChapters(story=story, Chapters=Chapters)
    
    @cache_service.cached(ttl=timedelta(minutes=10), key_prefix="user_Stories")
    async def get_user_Stories(self, user_id: uuid.UUID) -> List[Story]:
        """Get all Stories for a user with caching."""
        logger.info(f"Fetching Stories for user {user_id}")
        
        try:
            Stories = await self.db.get_user_Stories_async(user_id)
            logger.info(f"Found {len(Stories)} Stories for user {user_id}")
            return Stories
        except Exception as e:
            logger.error(f"Error fetching Stories for user {user_id}: {e}")
            return []
    
    async def invalidate_story_cache(self, story_id: int):
        """Invalidate all cached data for a story."""
        logger.info(f"Invalidating cache for story {story_id}")
        
        await self.cache.clear_pattern(f"story:{story_id}")
        await self.cache.clear_pattern(f"Chapters:{story_id}")
        await self.cache.clear_pattern(f"embedding:{story_id}")
    
    async def invalidate_user_cache(self, user_id: uuid.UUID):
        """Invalidate all cached data for a user."""
        logger.info(f"Invalidating cache for user {user_id}")
        
        await self.cache.clear_pattern(f"user_Stories:{user_id}")
    
    def get_story_sync(self, story_id: int, user_id: Optional[uuid.UUID] = None) -> Optional[Story]:
        """Synchronous story fetch for compatibility."""
        return self.db.get_story_sync(story_id, user_id)
    
    def get_Chapters_sync(self, story_id: int) -> List[Chapter]:
        """Synchronous Chapters fetch for compatibility."""
        return self.db.get_Chapters_sync(story_id)
    
    async def get_service_stats(self) -> dict:
        """Get service performance statistics."""
        cache_stats = self.cache.get_cache_stats()
        
        return {
            "cache": cache_stats,
            "database_pool_initialized": self.db._async_pool is not None,
            "dna_extraction_enabled": True,
            "dna_extraction_method": "ENHANCED_LLM"  # Updated feature flag
        }

    async def generate_next_chapter_with_dna(
        self, 
        story, 
        previous_Chapters, 
        selected_choice, 
        next_chapter_number, 
        user_id=None,
        all_choice_options=None
    ):
        """
        🧬 UPDATED: Generate the next chapter using Enhanced LLM DNA extraction.
        
        Now includes choice context, previous DNA tracking, and plot thread preservation.
        
        Args:
            story: dict with story details (should include 'story_title' and 'story_outline')
            previous_Chapters: list of chapter dicts (should include 'content' and optionally 'summary')
            selected_choice: dict with the selected choice (should include 'title' and 'description')
            next_chapter_number: int, the chapter number to generate
            user_id: optional, for logging
            all_choice_options: list of all choice options that were available (for context)
            
        Returns:
            dict with generated chapter content, choices, and enhanced metrics
        """
        # Build DNA and summary context from DB fields, do not re-extract
        story_dna_contexts = []
        summaries = []
        for i, chapter in enumerate(previous_Chapters, 1):
            summary = chapter.get('summary', '')
            dna = chapter.get('dna', '')
            if dna:
                story_dna_contexts.append(f"CHAPTER {i} DNA:\n{dna}")
            if summary:
                summaries.append(summary)
        
        # Compose user choice string
        user_choice_made = selected_choice.get('title', '')
        choice_description = selected_choice.get('description', '')
        if choice_description:
            user_choice_made = f"{user_choice_made}: {choice_description}"
        
        # Prepare LLM input context
        story_title = story.get('story_title', 'Untitled Story')
        story_outline = story.get('story_outline', '')
        
        # Call the generator with saved DNA and summary context
        from lc_next_chapter_generator import NextChapterGeneratorWithDNA
        generator = NextChapterGeneratorWithDNA()
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            logger.info(f"🚀 Invoking NextChapterGeneratorWithDNA with saved DNA and summary context from DB")
            result = await loop.run_in_executor(None, generator.generate_next_chapter,
                story_title, story_outline, story_dna_contexts, next_chapter_number, user_choice_made, summaries)
            logger.info(f"✅ Chapter {next_chapter_number} generated successfully with saved DNA and summary context")
            return result
        except Exception as e:
            logger.error(f"❌ Error generating Chapter {next_chapter_number} with saved DNA and summary: {e}")
            raise
    
    # Keep the old method for compatibility during testing
    async def generate_next_chapter(self, story, previous_Chapters, selected_choice, next_chapter_number, user_id=None):
        """
        LEGACY METHOD: Generate the next chapter using the old broken approach.
        Keep this for comparison during testing.
        """
        logger.warning("⚠️ Using LEGACY chapter generation (broken 500-char truncation)")
        
        from lc_next_chapter_generator import NextChapterGenerator
        import asyncio

        story_title = story.get('story_title', 'Untitled Story')
        story_outline = story.get('story_outline', '')
        
        # OLD BROKEN APPROACH (for comparison)
        previous_summaries = []
        for ch in previous_Chapters:
            if ch.get('summary'):
                previous_summaries.append(ch['summary'])
            elif ch.get('content'):
                prev_content = ch.get('content', '')[:500] + '...'
                previous_summaries.append(f"Previous chapter: {prev_content}")
        
        # Compose user choice string
        user_choice = selected_choice.get('title', '')
        if selected_choice.get('description'):
            user_choice += ': ' + selected_choice['description']
        
        # Call the generator
        generator = NextChapterGenerator()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, generator.generate_next_chapter,
            story_title, story_outline, previous_summaries, next_chapter_number, user_choice)
        
        return result

# Create global service instance
story_service = StoryService()