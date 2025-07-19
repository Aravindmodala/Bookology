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
        from lc_next_chapter_generator import NextChapterGeneratorWithDNA
        
        # Import the enhanced LLM DNA extractor
        try:
            from enhanced_story_dna_extractor import extract_enhanced_chapter_dna, format_enhanced_dna_for_llm
            enhanced_dna_available = True
            logger.info("🧬 Using Enhanced LLM-powered DNA extraction system")
        except ImportError:
            logger.warning("⚠️ Enhanced LLM DNA extractor not available, falling back to basic")
            try:
                from story_dna_extractor import extract_chapter_dna, format_dna_for_llm
                enhanced_dna_available = False
                logger.info("🔄 Using basic LLM DNA extraction system")
            except ImportError:
                logger.error("❌ No LLM DNA extractor available, using fallback")
                enhanced_dna_available = None
        
        import asyncio

        logger.info(f"🧬 Generating Chapter {next_chapter_number} using Enhanced DNA extraction")
        logger.info(f"📚 Processing {len(previous_Chapters)} previous chapters")
        
        story_title = story.get('story_title', 'Untitled Story')
        story_outline = story.get('story_outline', '')
        
        # 🧬 ENHANCED DNA EXTRACTION APPROACH
        story_dna_contexts = []
        previous_dna_list = []  # Track DNA objects for context building
        total_dna_chars = 0
        
        # Extract choice context
        user_choice_made = selected_choice.get('title', '')
        choice_description = selected_choice.get('description', '')
        if choice_description:
            user_choice_made = f"{user_choice_made}: {choice_description}"
        
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
            
            # Extract DNA from chapter content using Enhanced LLM
            try:
                logger.info(f"🔬 Extracting Enhanced DNA from Chapter {i} ({len(chapter_content)} chars)")
                
                if enhanced_dna_available is True:
                    # Use Enhanced LLM DNA extraction with full context
                    chapter_dna = extract_enhanced_chapter_dna(
                        chapter_content=chapter_content,
                        chapter_number=i,
                        previous_dna_list=previous_dna_list.copy(),  # Pass previous DNA for context
                        user_choice_made=user_choice_made if i == len(previous_Chapters) else "",  # Only for last chapter
                        choice_options=all_choice_options if i == len(previous_Chapters) else None
                    )
                    formatted_dna = format_enhanced_dna_for_llm(chapter_dna)
                    
                    # Store DNA object for next iterations
                    previous_dna_list.append(chapter_dna)
                    
                    chapter_dna_context = f"CHAPTER {i} ENHANCED DNA:\n{formatted_dna}"
                    story_dna_contexts.append(chapter_dna_context)
                    
                    total_dna_chars += len(formatted_dna)
                    
                    logger.info(f"✅ Chapter {i} Enhanced DNA extracted: {len(formatted_dna)} chars")
                    
                    # Enhanced logging for plot threads
                    if isinstance(chapter_dna, dict) and chapter_dna.get('extraction_method') == 'ENHANCED_LLM':
                        # Log active plot threads
                        plot_genetics = chapter_dna.get('plot_genetics', {})
                        active_threads = plot_genetics.get('active_plot_threads', [])
                        if active_threads:
                            logger.info(f"🎯 Chapter {i} plot threads: {len(active_threads)} identified")
                            for thread in active_threads[:3]:  # Log first 3
                                if isinstance(thread, dict):
                                    thread_desc = thread.get('description', 'Unknown')
                                    thread_status = thread.get('status', 'unknown')
                                    logger.info(f"   • {thread_desc} [{thread_status}]")
                        
                        # Log choice fulfillment if this was after a choice
                        choice_genetics = chapter_dna.get('choice_genetics', {})
                        choice_fulfillment = choice_genetics.get('choice_fulfillment', '')
                        if choice_fulfillment and choice_fulfillment != 'unknown':
                            logger.info(f"🔄 Chapter {i} choice fulfillment: {choice_fulfillment}")
                        
                        # Log continuity anchors
                        anchors = chapter_dna.get('continuity_anchors', [])
                        if anchors:
                            logger.info(f"⚓ Chapter {i} continuity anchors: {len(anchors)} critical facts preserved")
                
                elif enhanced_dna_available is False:
                    # Use basic LLM DNA extraction
                    chapter_dna = extract_chapter_dna(chapter_content, i)
                    formatted_dna = format_dna_for_llm(chapter_dna)
                    
                    chapter_dna_context = f"CHAPTER {i} DNA:\n{formatted_dna}"
                    story_dna_contexts.append(chapter_dna_context)
                    
                    total_dna_chars += len(formatted_dna)
                    logger.info(f"✅ Chapter {i} Basic DNA extracted: {len(formatted_dna)} chars")
                
                else:
                    # Complete fallback
                    logger.warning(f"⚠️ No DNA extractor available for Chapter {i}, using simple extraction")
                    
                    if len(chapter_content) > 1000:
                        ending_context = "..." + chapter_content[-600:]
                        fallback_context = f"Chapter {i} (ending context): {ending_context}"
                    else:
                        fallback_context = f"Chapter {i} (full content): {chapter_content}"
                    
                    story_dna_contexts.append(fallback_context)
                    logger.info(f"🔄 Chapter {i}: Using simple fallback context")
                
            except Exception as e:
                logger.error(f"❌ Failed to extract DNA from Chapter {i}: {e}")
                
                # Enhanced fallback - take ending context
                if len(chapter_content) > 1000:
                    ending_context = "..." + chapter_content[-600:]
                    fallback_context = f"Chapter {i} (ending context): {ending_context}"
                else:
                    fallback_context = f"Chapter {i} (full content): {chapter_content}"
                
                story_dna_contexts.append(fallback_context)
                logger.info(f"🔄 Chapter {i}: Using enhanced fallback context")
        
        # Combine all DNA contexts
        combined_dna_context = "\n\n".join(story_dna_contexts)
        
        # Enhanced choice validation logging
        logger.info(f"🎯 User choice: '{user_choice_made}'")
        logger.info(f"📊 Total DNA context: {len(combined_dna_context)} chars from {len(story_dna_contexts)} chapters")
        
        # Enhanced DNA system identification
        if enhanced_dna_available is True:
            dna_system = "ENHANCED_LLM"
            logger.info(f"🧬 DNA system: {dna_system} (with plot tracking & choice context)")
        elif enhanced_dna_available is False:
            dna_system = "BASIC_LLM"
            logger.info(f"🧬 DNA system: {dna_system} (basic LLM extraction)")
        else:
            dna_system = "SIMPLE_FALLBACK"
            logger.info(f"🧬 DNA system: {dna_system} (text truncation)")
        
        # Enhanced metrics logging
        if total_dna_chars > 0:
            original_chars = sum(len(ch.get('content', '')) for ch in previous_Chapters)
            if original_chars > 0:
                compression_ratio = total_dna_chars / original_chars
                logger.info(f"📈 DNA efficiency: {total_dna_chars} chars (compression: {compression_ratio:.2%})")
        
        # Plot thread continuity check
        if enhanced_dna_available is True and previous_dna_list:
            total_plot_threads = sum(
                len(dna.get('plot_genetics', {}).get('active_plot_threads', []))
                for dna in previous_dna_list
            )
            if total_plot_threads > 0:
                logger.info(f"🎯 Plot continuity: {total_plot_threads} active threads tracked across chapters")
        
        # Validate that we have meaningful context
        if not combined_dna_context.strip():
            logger.error("❌ No DNA context generated - this will cause continuity issues")
            raise ValueError("Failed to generate story DNA context")
        
        # Call the generator with enhanced DNA context
        generator = NextChapterGeneratorWithDNA()
        loop = asyncio.get_event_loop()
        
        try:
            logger.info(f"🚀 Invoking NextChapterGeneratorWithDNA with Enhanced DNA context")
            
            result = await loop.run_in_executor(None, generator.generate_next_chapter,
                story_title, story_outline, story_dna_contexts, next_chapter_number, user_choice_made)
            
            logger.info(f"✅ Chapter {next_chapter_number} generated successfully with Enhanced DNA context")
            
            # Add enhanced DNA metrics to result
            if isinstance(result, dict):
                result['enhanced_dna_metrics'] = {
                    'total_dna_chars': total_dna_chars,
                    'chapters_processed': len(previous_Chapters),
                    'dna_contexts_generated': len(story_dna_contexts),
                    'extraction_method': dna_system,
                    'plot_threads_tracked': total_plot_threads if enhanced_dna_available is True and previous_dna_list else 0,
                    'choice_context_included': bool(user_choice_made),
                    'previous_dna_contexts': len(previous_dna_list) if enhanced_dna_available is True else 0,
                    'context_compression_ratio': total_dna_chars / sum(len(ch.get('content', '')) for ch in previous_Chapters) if previous_Chapters else 0
                }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating Chapter {next_chapter_number} with Enhanced DNA: {e}")
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