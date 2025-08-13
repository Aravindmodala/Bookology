"""
Simplified Optimized Chapter Service - No Vector Embeddings
Focuses on: Chapter content + Summary + DNA + Choices
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.core.logger_config import setup_logger
from app.services.chapter_summary import generate_chapter_summary

logger = setup_logger(__name__)

@dataclass
class ChapterSaveResult:
    chapter_id: int
    summary: str
    choices: List[Dict[str, Any]]
    save_time: float
    performance_metrics: Dict[str, Any]

class OptimizedChapterService:
    """
    Simplified high-performance chapter service:
    1. Save chapter content immediately
    2. Generate summary + DNA in parallel
    3. Save choices with proper story_id + chapter_number + choice_id
    4. No vector embeddings (removed for reliability)
    """
    
    def __init__(self):
        # Thread pool for CPU-bound tasks
        self.summary_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="summary")
        
        # Performance tracking
        self.metrics = {
            'total_saves': 0,
            'avg_save_time': 0,
            'summary_generation_time': 0
        }
        
        logger.info("✅ OptimizedChapterService initialized (vectors disabled for reliability)")

    async def save_chapter_optimized(
        self,
        chapter_data: Dict[str, Any],
        user_id: int,
        supabase_client
    ) -> ChapterSaveResult:
        """
        FIXED: Synchronous choice saving to eliminate race conditions:
        1. Immediate chapter save (priority)
        2. IMMEDIATE choice save (synchronous - critical for UX)
        3. Background summary + DNA generation (heavy operations only)
        """
        start_time = time.time()
        story_id = chapter_data['story_id']
        chapter_number = chapter_data['chapter_number']
        content = chapter_data['content']
        
        logger.info(f"🚀 Starting SYNCHRONOUS save for Chapter {chapter_number}")
        
        try:
            # STEP 1: IMMEDIATE CHAPTER SAVE (highest priority)
            chapter_id = await self._save_chapter_immediate(
                chapter_data, user_id, supabase_client
            )
            logger.info(f"✅ Chapter saved with ID: {chapter_id}")
            
            # STEP 2: IMMEDIATE CHOICE SAVE (synchronous - critical for UX)
            choices_result = []
            if chapter_data.get('choices', []):
                logger.info(f"💾 Saving {len(chapter_data['choices'])} choices SYNCHRONOUSLY...")
                choices_result = await self._save_choices_synchronous(
                    chapter_id, story_id, chapter_number, user_id, 
                    chapter_data.get('choices', []), supabase_client
                )
                logger.info(f"✅ SYNCHRONOUS: Saved {len(choices_result)} choices immediately")
            else:
                logger.info("ℹ️ No choices to save")
            
            # STEP 3: HEAVY OPERATIONS IN BACKGROUND (summary + DNA only)
            # Get previous chapters for DNA context
            previous_chapters = await self._get_previous_chapters_for_dna(
                story_id, chapter_number, supabase_client
            )
            
            # Start background tasks for heavy operations only
            asyncio.create_task(self._generate_metadata_only_async(
                chapter_id, content, chapter_number, story_id, 
                previous_chapters, chapter_data.get('user_choice', ''), supabase_client
            ))
            
            save_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(save_time, {"summary": "background"}, {"dna": "background"})
            
            logger.info(f"✅ Chapter {chapter_number} saved with choices IMMEDIATELY in {save_time:.2f}s")
            
            return ChapterSaveResult(
                chapter_id=chapter_id,
                summary="Processing in background...",
                choices=choices_result,
                save_time=save_time,
                performance_metrics=self._get_performance_metrics()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to save chapter: {e}")
            raise

    async def _save_choices_synchronous(
        self,
        chapter_id: int,
        story_id: int,
        chapter_number: int,
        user_id: int,
        choices: List[Dict[str, Any]],
        supabase_client
    ) -> List[Dict[str, Any]]:
        """Save choices IMMEDIATELY (synchronously) - critical for UX"""
        try:
            if not choices or len(choices) == 0:
                return []
                
            logger.info(f"🔄 Deleting existing choices for chapter {chapter_number}...")
            
            # Delete existing choices for this chapter first
            delete_response = supabase_client.table("story_choices").delete().eq(
                "story_id", story_id
            ).eq("chapter_number", chapter_number).execute()
            
            logger.info(f"🗑️ Deleted existing choices: {len(delete_response.data) if delete_response.data else 0}")
            
            # Extract and validate choices first
            valid_choices = await self._extract_choices_async(choices)
            
            if not valid_choices:
                logger.warning("⚠️ No valid choices to save")
                return []
            
            # Prepare choices data for database
            choice_records = []
            for i, choice in enumerate(valid_choices):
                choice_id = choice.get('choice_id', str(i+1))
                choice_record = {
                    'story_id': story_id,
                    'chapter_number': chapter_number,
                    'choice_id': choice_id,
                    'title': choice.get('title', f'Choice {i+1}'),
                    'description': choice.get('description', ''),
                    'story_impact': choice.get('story_impact', 'medium'),
                    'choice_type': choice.get('choice_type', 'narrative'),
                    'user_id': user_id,
                    'chapter_id': chapter_id,
                }
                choice_records.append(choice_record)
            
            logger.info(f"📝 Inserting {len(choice_records)} choices...")
            
            # Insert new choices SYNCHRONOUSLY
            choices_response = supabase_client.table("story_choices").insert(choice_records).execute()
            
            if choices_response.data and len(choices_response.data) > 0:
                logger.info(f"✅ SYNCHRONOUS: Successfully saved {len(choices_response.data)} choices")
                return choices_response.data
            else:
                logger.error("❌ SYNCHRONOUS: No choices were saved")
                return []
                
        except Exception as e:
            logger.error(f"❌ SYNCHRONOUS choice saving failed: {e}")
            raise e

    async def _generate_metadata_only_async(
        self,
        chapter_id: int,
        content: str,
        chapter_number: int,
        story_id: int,
        previous_chapters: List[Dict[str, Any]],
        user_choice: str,
        supabase_client
    ):
        """Background task ONLY for heavy operations - choices are already saved"""
        try:
            logger.info("🧠 Starting background metadata generation...")
            
            # Generate summary and DNA in parallel
            summary_task = self._generate_summary_async(content, chapter_number, story_id)
            dna_task = self._generate_dna_async(content, chapter_number, previous_chapters, user_choice)
            
            summary_result, dna_result = await asyncio.gather(
                summary_task,
                dna_task,
                return_exceptions=True
            )
            
            # Update chapter with summary and DNA
            update_data = {}
            if summary_result and not isinstance(summary_result, Exception) and summary_result.get('summary'):
                update_data['summary'] = summary_result['summary']
                logger.info(f"📝 Background: Adding summary: {len(summary_result['summary'])} chars")
            
            if dna_result and not isinstance(dna_result, Exception) and not dna_result.get('error'):
                import json
                update_data['dna'] = json.dumps(dna_result)
                logger.info(f"📝 Background: Adding DNA: {len(json.dumps(dna_result))} chars")
            
            if update_data:
                supabase_client.table("Chapters").update(update_data).eq('id', chapter_id).execute()
                logger.info(f"✅ Background: Updated chapter {chapter_id} with metadata")
            
            logger.info("✅ Background metadata generation complete")
            
        except Exception as e:
            logger.error(f"❌ Background metadata generation failed: {e}")

    async def _save_chapter_immediate(
        self, 
        chapter_data: Dict[str, Any], 
        user_id: int, 
        supabase_client
    ) -> int:
        """Save chapter content immediately - highest priority operation"""
        logger.info("💾 Immediate chapter save...")
        
        # Get or create branch_id
        try:
            # Use app.services.branching proxy to resolve main implementation if present
            from app.services.branching import get_main_branch_id
            main_branch_id = await get_main_branch_id(chapter_data['story_id'])
        except Exception:
            main_branch_id = None
        
        # Prepare minimal chapter data for immediate save
        chapter_insert_data = {
            "story_id": chapter_data['story_id'],
            "chapter_number": chapter_data['chapter_number'],
            "title": chapter_data.get('title', f"Chapter {chapter_data['chapter_number']}"),
            "content": chapter_data['content'],
            "word_count": len(chapter_data['content'].split()),
            "version_number": 1,
            "is_active": True,
            "summary": "Processing...",  # Placeholder - will be updated
        }
        
        if main_branch_id:
            chapter_insert_data["branch_id"] = main_branch_id
        
        # Insert chapter
        response = supabase_client.table("Chapters").insert(chapter_insert_data).execute()
        
        if not response.data:
            raise Exception("Failed to save chapter")
            
        chapter_id = response.data[0]["id"]
        logger.info(f"✅ Chapter saved with ID: {chapter_id}")
        
        return chapter_id

    async def _generate_summary_async(
        self, 
        content: str, 
        chapter_number: int, 
        story_id: int
    ) -> Dict[str, Any]:
        """Generate summary in background thread"""
        logger.info("🧠 Generating summary asynchronously...")
        
        loop = asyncio.get_event_loop()
        
        def generate_summary():
            return generate_chapter_summary(
                chapter_content=content,
                chapter_number=chapter_number,
                story_title="",  # Minimal context for speed
                story_context=""
            )
        
        summary_result = await loop.run_in_executor(
            self.summary_executor,
            generate_summary
        )
        
        logger.info("✅ Summary generated")
        return summary_result

    async def _extract_choices_async(self, choices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and validate choices from enhanced chapter generator format"""
        try:
            valid_choices = []
            for choice in choices:
                # Handle enhanced chapter generator format: id, text, consequence
                if isinstance(choice, dict):
                    # Enhanced format: id, text, consequence
                    if 'text' in choice:
                        # Convert choice ID to string for database compatibility
                        choice_id = choice.get('id', '1')
                        if isinstance(choice_id, int):
                            choice_id = str(choice_id)
                        elif isinstance(choice_id, str) and choice_id.startswith('choice_'):
                            # Extract number from "choice_1", "choice_2", etc.
                            try:
                                choice_id = choice_id.split('_')[1]
                            except (ValueError, IndexError):
                                choice_id = '1'
                        
                        valid_choice = {
                            'title': choice.get('text', ''),
                            'description': choice.get('consequence', ''),
                            'story_impact': choice.get('consequence', ''),
                            'choice_type': 'story_choice',
                            'choice_id': choice_id  # Add the choice_id for database saving
                        }
                        valid_choices.append(valid_choice)
                    # Legacy format: title, description, story_impact, choice_type
                    elif 'title' in choice:
                        valid_choices.append(choice)
            
            logger.info(f" ✅ Validated {len(valid_choices)} choices")
            return valid_choices
        except Exception as e:
            logger.error(f"❌ Error validating choices: {e}")
            return []

    async def _get_previous_chapters_for_dna(
        self,
        story_id: int,
        current_chapter_number: int,
        supabase_client
    ) -> List[Dict[str, Any]]:
        """Get previous chapters for DNA context"""
        logger.info("📚 Getting previous chapters for DNA context...")
        
        try:
            # OPTIMIZATION: Only get essential fields for DNA context (not full content)
            response = supabase_client.table("Chapters").select(
                "summary, dna, chapter_number"  # Removed 'content' for faster queries
            ).eq("story_id", story_id).eq("is_active", True).lt(
                "chapter_number", current_chapter_number
            ).order("chapter_number").execute()
            
            previous_chapters = response.data if response.data else []
            logger.info(f"✅ Retrieved {len(previous_chapters)} previous chapters for DNA context")
            return previous_chapters
            
        except Exception as e:
            logger.warning(f"Failed to get previous chapters for DNA: {e}")
            return []

    async def _generate_dna_async(
        self, 
        content: str, 
        chapter_number: int,
        previous_chapters: List[Dict[str, Any]],
        user_choice: str = ""
    ) -> Dict[str, Any]:
        logger.info(f"🧬 [DNA DEBUG] Generating DNA for Chapter {chapter_number}")
        logger.info(f"🧬 [DNA DEBUG] Content length: {len(content)}")
        logger.info(f"🧬 [DNA DEBUG] User choice: {user_choice}")
        logger.info(f"🧬 [DNA DEBUG] Previous chapters count: {len(previous_chapters)}")
        logger.info(f"🧬 [DNA DEBUG] Previous chapters DNA: {[ch.get('dna') for ch in previous_chapters]}")
        loop = asyncio.get_event_loop()
        def generate_dna():
            try:
                from app.services.dna_extractor import EnhancedLLMStoryDNAExtractor
                dna_extractor = EnhancedLLMStoryDNAExtractor()
                previous_dna_list = []
                for chapter in previous_chapters:
                    if chapter.get('dna'):
                        dna = chapter['dna']
                        if isinstance(dna, str):
                            import json
                            try:
                                dna = json.loads(dna)
                            except Exception as e:
                                logger.error(f"🧬 [DNA DEBUG] Failed to parse previous DNA JSON: {e}")
                                continue
                        previous_dna_list.append(dna)
                logger.info(f"🧬 [DNA DEBUG] previous_dna_list for extractor: {previous_dna_list}")
                dna_result = dna_extractor.extract_chapter_dna(
                    chapter_content=content,
                    chapter_number=chapter_number,
                    previous_dna_list=previous_dna_list,
                    user_choice_made=user_choice,
                    choice_options=[]
                )
                logger.info(f"🧬 [DNA DEBUG] DNA extractor result: {dna_result}")
                return dna_result
            except Exception as e:
                logger.error(f"🧬 [DNA DEBUG] DNA generation failed: {e}")
                return {"error": str(e), "fallback": True}
        dna_result = await loop.run_in_executor(
            self.summary_executor,  # Reuse executor
            generate_dna
        )
        logger.info(f"🧬 [DNA DEBUG] Final DNA result for Chapter {chapter_number}: {dna_result}")
        return dna_result

    def _update_metrics(self, save_time: float, summary_result: Any, dna_result: Any = None):
        """Update performance metrics"""
        self.metrics['total_saves'] += 1
        self.metrics['avg_save_time'] = (
            (self.metrics['avg_save_time'] * (self.metrics['total_saves'] - 1) + save_time) 
            / self.metrics['total_saves']
        )
        
        # Track DNA extraction success
        self.metrics['dna_extracted'] = bool(dna_result and not dna_result.get('error'))

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'total_saves': self.metrics['total_saves'],
            'avg_save_time': round(self.metrics['avg_save_time'], 2),
            'embedding_status': 'disabled_for_reliability',
            'dna_extracted': self.metrics.get('dna_extracted', False)
        }

# Global instance for import compatibility
fixed_optimized_chapter_service = OptimizedChapterService()



