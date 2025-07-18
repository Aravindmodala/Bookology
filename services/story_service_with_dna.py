"""
UPDATED VERSION: Unified story service with LLM DNA extraction instead of broken regex.
This replaces the built-in regex DNA extraction with intelligent LLM-based extraction.
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
    UPDATED VERSION: High-level story operations with LLM DNA extraction for perfect continuity.
    Replaces broken regex patterns with intelligent LLM-based story genetic preservation.
    """
    
    def __init__(self):
        self.db = db_service
        self.cache = cache_service
        logger.info("🧬 StoryServiceWithDNA initialized - LLM DNA extraction enabled")
    
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
            "database_pool_initialized": self.db._async_pool is not None,
            "dna_extraction_enabled": True,
            "dna_extraction_method": "LLM"  # Updated feature flag
        }

    async def generate_next_chapter_with_dna(self, story, previous_Chapters, selected_choice, next_chapter_number, user_id=None):
        """
        🧬 UPDATED: Generate the next chapter using LLM DNA extraction instead of broken regex.
        
        This method now uses the new LLM-powered DNA extractor for intelligent context preservation.
        
        Args:
            story: dict with story details (should include 'story_title' and 'story_outline')
            previous_Chapters: list of chapter dicts (should include 'content' and optionally 'summary')
            selected_choice: dict with the selected choice (should include 'title' and 'description')
            next_chapter_number: int, the chapter number to generate
            user_id: optional, for logging
            
        Returns:
            dict with generated chapter content, choices, and token metrics
        """
        from lc_next_chapter_generator import NextChapterGeneratorWithDNA
        
        # Import the new LLM DNA extractor
        try:
            from story_dna_extractor import extract_chapter_dna, format_dna_for_llm
            llm_dna_available = True
            logger.info("🧬 Using LLM-powered DNA extraction system")
        except ImportError:
            logger.warning("⚠️ LLM DNA extractor not available, using fallback")
            llm_dna_available = False
        
        import asyncio

        logger.info(f"🧬 Generating Chapter {next_chapter_number} using DNA extraction")
        logger.info(f"📚 Processing {len(previous_Chapters)} previous chapters")
        
        story_title = story.get('story_title', 'Untitled Story')
        story_outline = story.get('story_outline', '')
        
        # 🧬 LLM DNA EXTRACTION APPROACH
        story_dna_contexts = []
        total_dna_chars = 0
        
        for i, chapter in enumerate(previous_Chapters, 1):
            chapter_content = chapter.get('content', '')
            
            if not chapter_content:
                # If no content, try summary as fallback
                summary = chapter.get('summary', '')
                if summary:
                    fallback_context = f"Chapter {i} (summary only): {summary}"
                    story_dna_contexts.append(fallback_context)
                    logger.warning(f"⚠️ Chapter {i}: No content, using summary fallback")
                continue
            
            # Extract DNA from chapter content using LLM
            try:
                logger.info(f"🔬 Extracting DNA from Chapter {i} ({len(chapter_content)} chars)")
                
                if llm_dna_available:
                    # Use intelligent LLM DNA extraction
                    chapter_dna = extract_chapter_dna(chapter_content, i)
                    formatted_dna = format_dna_for_llm(chapter_dna)
                    
                    chapter_dna_context = f"CHAPTER {i} DNA:\n{formatted_dna}"
                    story_dna_contexts.append(chapter_dna_context)
                    
                    total_dna_chars += len(formatted_dna)
                    
                    logger.info(f"✅ Chapter {i} DNA extracted: {len(formatted_dna)} chars")
                    
                    # Log LLM DNA elements for debugging
                    if isinstance(chapter_dna, dict) and not chapter_dna.get('fallback'):
                        # Log scene DNA
                        if chapter_dna.get('scene_genetics'):
                            scene = chapter_dna['scene_genetics']
                            logger.info(f"🏞️ Scene: {scene.get('location_description', 'unknown')} - {scene.get('atmosphere', 'neutral')} atmosphere")
                        
                        # Log character DNA
                        if chapter_dna.get('character_genetics'):
                            chars = chapter_dna['character_genetics']
                            active_chars = chars.get('active_characters', [])
                            if active_chars:
                                logger.info(f"👥 Characters: {', '.join(active_chars)}")
                        
                        # Log emotional DNA
                        if chapter_dna.get('emotional_genetics'):
                            emotions = chapter_dna['emotional_genetics']
                            dominant = emotions.get('dominant_emotions', [])
                            tension = emotions.get('tension_level', 'unknown')
                            if dominant:
                                logger.info(f"💭 Emotions: {', '.join(dominant)} (tension: {tension})")
                        
                        # Log ending DNA
                        if chapter_dna.get('ending_genetics'):
                            ending = chapter_dna['ending_genetics']
                            logger.info(f"🎯 Chapter {i} ending: {ending.get('scene_status', 'unknown')} scene")
                            if ending.get('last_dialogue'):
                                logger.info(f"💬 Last dialogue: {ending['last_dialogue'][:50]}...")
                            if ending.get('cliffhanger_type') != 'none':
                                logger.info(f"🎪 Cliffhanger: {ending.get('cliffhanger_type', 'none')}")
                        
                        # Log continuity anchors
                        anchors = chapter_dna.get('continuity_anchors', [])
                        if anchors:
                            logger.info(f"⚓ Continuity anchors: {len(anchors)} critical facts preserved")
                    else:
                        logger.info(f"🔄 Using LLM DNA extraction (fallback mode)")
                else:
                    # Fallback to simple context extraction
                    logger.warning(f"⚠️ LLM DNA not available, using simple extraction for Chapter {i}")
                    
                    if len(chapter_content) > 1000:
                        # Take the last 600 chars for better context preservation
                        ending_context = "..." + chapter_content[-600:]
                        fallback_context = f"Chapter {i} (ending context): {ending_context}"
                    else:
                        fallback_context = f"Chapter {i} (full content): {chapter_content}"
                    
                    story_dna_contexts.append(fallback_context)
                    logger.info(f"🔄 Chapter {i}: Using simple fallback context")
                
            except Exception as e:
                logger.error(f"❌ Failed to extract DNA from Chapter {i}: {e}")
                
                # Enhanced fallback - take ending context instead of beginning
                if len(chapter_content) > 1000:
                    # Take the last 600 chars for better context preservation
                    ending_context = "..." + chapter_content[-600:]
                    fallback_context = f"Chapter {i} (ending context): {ending_context}"
                else:
                    fallback_context = f"Chapter {i} (full content): {chapter_content}"
                
                story_dna_contexts.append(fallback_context)
                logger.info(f"🔄 Chapter {i}: Using enhanced fallback context")
        
        # Combine all DNA contexts
        combined_dna_context = "\n\n".join(story_dna_contexts)
        
        # Compose user choice string with better formatting
        user_choice = selected_choice.get('title', '')
        choice_description = selected_choice.get('description', '')
        
        if choice_description:
            user_choice = f"{user_choice}: {choice_description}"
        
        # Add choice validation logging
        logger.info(f"🎯 User choice: '{user_choice}'")
        logger.info(f"📊 Total DNA context: {len(combined_dna_context)} chars from {len(story_dna_contexts)} chapters")
        logger.info(f"🧬 DNA system: {'LLM-POWERED' if llm_dna_available else 'SIMPLE FALLBACK'}")
        
        if total_dna_chars > 0:
            original_chars = sum(len(ch.get('content', '')) for ch in previous_Chapters)
            if original_chars > 0:
                compression_ratio = total_dna_chars / original_chars
                logger.info(f"📈 DNA efficiency: {total_dna_chars} chars (compression: {compression_ratio:.2%})")
        
        # Validate that we have meaningful context
        if not combined_dna_context.strip():
            logger.error("❌ No DNA context generated - this will cause continuity issues")
            raise ValueError("Failed to generate story DNA context")
        
        # Call the generator with DNA context
        generator = NextChapterGeneratorWithDNA()
        loop = asyncio.get_event_loop()
        
        try:
            logger.info(f"🚀 Invoking NextChapterGeneratorWithDNA with DNA context")
            
            result = await loop.run_in_executor(None, generator.generate_next_chapter,
                story_title, story_outline, story_dna_contexts, next_chapter_number, user_choice)
            
            logger.info(f"✅ Chapter {next_chapter_number} generated successfully with DNA context")
            
            # Add DNA metrics to result
            if isinstance(result, dict):
                result['dna_metrics'] = {
                    'total_dna_chars': total_dna_chars,
                    'chapters_processed': len(previous_Chapters),
                    'dna_contexts_generated': len(story_dna_contexts),
                    'extraction_method': 'LLM' if llm_dna_available else 'fallback',
                    'context_compression_ratio': total_dna_chars / sum(len(ch.get('content', '')) for ch in previous_Chapters) if previous_Chapters else 0
                }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating Chapter {next_chapter_number} with DNA: {e}")
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
        
        # 🚨 OLD BROKEN APPROACH (for comparison)
        previous_summaries = []
        for ch in previous_Chapters:
            if ch.get('summary'):
                previous_summaries.append(ch['summary'])
            elif ch.get('content'):
                # fallback: use first 500 chars of content - THIS IS BROKEN!
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

# Create global service instance
story_service = StoryService()