"""
UPDATED VERSION: Unified story service with Enhanced LLM DNA extraction.
Fixed integration with the enhanced DNA extractor for perfect continuity.
"""

import uuid
from typing import List, Optional
import json
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

    # === Rolling context helpers ===
    def _compact_dna_json(self, dna_json_str: str, max_threads: int = 3, max_anchors: int = 4) -> str:
        """Create a compact, priority-preserving representation of a chapter DNA JSON.

        Keeps critical continuity details and trims verbose/low-priority fields.
        """
        try:
            data = json.loads(dna_json_str) if isinstance(dna_json_str, str) else dna_json_str
        except Exception:
            # Fallback: return a safe slice of raw text
            return str(dna_json_str)[:2000]

        compact = {}

        # Always keep continuity anchors and ending genetics (no trim)
        continuity_anchors = data.get("continuity_anchors")
        if continuity_anchors:
            compact["continuity_anchors"] = continuity_anchors[:max_anchors]

        ending = data.get("ending_genetics")
        if ending:
            compact["ending_genetics"] = {
                k: ending.get(k, "") for k in [
                    "final_scene_context",
                    "last_dialogue",
                    "last_action",
                    "immediate_situation"
                ]
            }

        # Plot genetics: keep top active_plot_threads with next_action_needed + pending_decisions
        plot = data.get("plot_genetics", {}) or {}
        if plot:
            threads = plot.get("active_plot_threads", []) or []
            trimmed_threads = []
            for t in threads[:max_threads]:
                if isinstance(t, dict):
                    trimmed_threads.append({
                        "description": t.get("description", str(t)),
                        "next_action_needed": t.get("next_action_needed", "")
                    })
                else:
                    trimmed_threads.append({"description": str(t), "next_action_needed": ""})
            compact["plot_genetics"] = {
                "active_plot_threads": trimmed_threads,
                "pending_decisions": (plot.get("pending_decisions", []) or [])[:max_threads],
            }

            # Include promises/deadlines if present (bounded)
            if plot.get("promises_made") or plot.get("deadlines_mentioned"):
                compact["plot_genetics"]["promises_made"] = (plot.get("promises_made", []) or [])[:max_threads]
                compact["plot_genetics"]["deadlines_mentioned"] = (plot.get("deadlines_mentioned", []) or [])[:max_threads]

        # Character genetics: active characters and their current states
        char = data.get("character_genetics", {}) or {}
        if char:
            active = (char.get("active_characters", []) or [])[:8]
            states_all = char.get("character_states", {}) or {}
            states = {name: states_all.get(name, "") for name in active}
            compact["character_genetics"] = {
                "active_characters": active,
                "character_states": states,
            }

        # Minimal scene snapshot (who/where/when vibes)
        scene = data.get("scene_genetics", {}) or {}
        if scene:
            compact["scene_snapshot"] = {
                "location_type": scene.get("location_type", ""),
                "time_context": scene.get("time_context", ""),
                "atmosphere": scene.get("atmosphere", ""),
            }

        # Final compaction pass
        text = json.dumps(compact, ensure_ascii=False)
        return text[:2000]  # soft cap per DNA chunk

    def _build_generation_context(self, previous_Chapters: List[dict], next_chapter_number: int):
        """Build rolling context: last-2 compact DNAs + hierarchical super-summary when deep.

        Returns a tuple (recent_dna_list, summaries_payload, summaries_mode)
        - recent_dna_list: List[str]
        - summaries_payload: List[str]
        - summaries_mode: "list" or "super"
        """
        if not previous_Chapters:
            return [], [], "list"

        # Ensure sorted by chapter_number
        prev_sorted = sorted(previous_Chapters, key=lambda c: c.get("chapter_number", 0))

        # Last-2 DNA (most recent)
        lower_bound = max(1, next_chapter_number - 2)
        recent = [c for c in prev_sorted if c.get("chapter_number", 0) >= lower_bound]
        recent_dna: List[str] = []
        for ch in recent[-2:]:
            dna_raw = ch.get("dna")
            if dna_raw:
                compacted = self._compact_dna_json(dna_raw)
                recent_dna.append(f"CHAPTER {ch.get('chapter_number')} DNA:\n{compacted}")

        # If next_chapter_number <= 5, return list of individual summaries
        if next_chapter_number <= 5:
            summaries = [c.get("summary", "") for c in prev_sorted if c.get("summary")]
            return recent_dna, summaries, "list"

        # Otherwise produce one hierarchical super-summary for 1..N-3
        older = [c for c in prev_sorted if c.get("chapter_number", 0) <= next_chapter_number - 3]
        older_summaries = [c.get("summary", "") for c in older if c.get("summary")]
        super_summary = ""
        try:
            # Use existing summarizer module (note filename spelling in repo)
            from hierarchial_summarizer import HierarchicalSummarizer
            hs = HierarchicalSummarizer()
            start = 1
            end = max(1, next_chapter_number - 3)
            super_summary = hs.generate_super_summary(older_summaries, start, end)
        except Exception as e:
            logger.warning(f"[SERVICE] Super-summary generation failed, fallback to concatenation: {e}")
            super_summary = " ".join(older_summaries)[:1200]

        return recent_dna, [super_summary], "super"

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
        # Build DNA and summary context using rolling policy
        story_dna_contexts, summaries, summaries_mode = self._build_generation_context(previous_Chapters, next_chapter_number)
        
        # Compose user choice string
        user_choice_made = selected_choice.get('title', '')
        choice_description = selected_choice.get('description', '')
        if choice_description:
            user_choice_made = f"{user_choice_made}: {choice_description}"
        
        # Prepare LLM input context
        story_outline = story.get('story_outline', '')

        # Resolve planned chapter title from outline_json; fallback to "Chapter N"
        planned_chapter_title = f"Chapter {next_chapter_number}"
        next_planned_chapter_title = ""
        try:
            outline_json_raw = story.get('outline_json')
            if outline_json_raw:
                outline_obj = json.loads(outline_json_raw) if isinstance(outline_json_raw, str) else outline_json_raw
                chapters_list = outline_obj.get('chapters') or outline_obj.get('Chapters') or []
                if isinstance(chapters_list, list) and len(chapters_list) >= next_chapter_number:
                    planned = chapters_list[next_chapter_number - 1] or {}
                    planned_chapter_title = planned.get('title', planned_chapter_title)
                # Next chapter to be set up by this chapter's ending
                next_idx = next_chapter_number  # 0-based index for the next chapter after this one
                if isinstance(chapters_list, list) and len(chapters_list) > next_idx:
                    next_planned = chapters_list[next_idx] or {}
                    next_planned_chapter_title = next_planned.get('title', "")
        except Exception as e:
            logger.warning(f"[SERVICE] Failed to parse outline_json for planned title: {e}")
        
        # Call the generator with saved DNA and summary context
        from lc_next_chapter_generator import NextChapterGeneratorWithDNA
        generator = NextChapterGeneratorWithDNA()
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            # Log exact inputs that will be forwarded into the generator
            try:
                logger.info(
                    "[SERVICE] Forwarding to generator → chapter_title='%s', next_chapter_title='%s', chapter=%s, dna_ctx_count=%s, summaries_mode=%s, summaries_count=%s, user_choice_chars=%s",
                    planned_chapter_title[:80],
                    (next_planned_chapter_title or "")[:80],
                    next_chapter_number,
                    len(story_dna_contexts or []),
                    summaries_mode,
                    len(summaries or []),
                    len(user_choice_made or "")
                )
            except Exception as log_err:
                logger.warning(f"[SERVICE] Logging inputs failed: {log_err}")

            logger.info(f"🚀 Invoking NextChapterGeneratorWithDNA with saved DNA and summary context from DB")
            # Ensure keyword args are forwarded (including is_game_mode)
            result = await loop.run_in_executor(
                None,
                lambda: generator.generate_next_chapter(
                    story_title=planned_chapter_title,
                    story_outline=story_outline,
                    story_dna_contexts=story_dna_contexts,
                    chapter_number=next_chapter_number,
                    user_choice=user_choice_made,
                    previous_chapter_summaries=summaries,
                    is_game_mode=bool(selected_choice),
                    next_chapter_title=next_planned_chapter_title
                )
            )
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