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

from config import settings
from logger_config import setup_logger
from chapter_summary import generate_chapter_summary

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
        Simplified optimized chapter save:
        1. Immediate chapter save (priority)
        2. Parallel summary + DNA generation
        3. Update chapter with summary + DNA
        4. Save choices with story_id + chapter_number + choice_id
        """
        start_time = time.time()
        story_id = chapter_data['story_id']
        chapter_number = chapter_data['chapter_number']
        content = chapter_data['content']
        
        logger.info(f"🚀 Starting optimized save for Chapter {chapter_number}")
        
        try:
            # STEP 1: IMMEDIATE CHAPTER SAVE (highest priority)
            chapter_id = await self._save_chapter_immediate(
                chapter_data, user_id, supabase_client
            )
            
            # STEP 2: Get previous chapters for DNA context
            previous_chapters = await self._get_previous_chapters_for_dna(
                story_id, chapter_number, supabase_client
            )
            
            # STEP 3: PARALLEL ASYNC OPERATIONS (NO VECTORS)
            summary_task = self._generate_summary_async(content, chapter_number, story_id)
            dna_task = self._generate_dna_async(content, chapter_number, previous_chapters, chapter_data.get('user_choice', ''))
            choices_task = self._extract_choices_async(chapter_data.get('choices', []))
            
            # Wait for all operations
            summary_result, dna_result, choices_result = await asyncio.gather(
                summary_task,
                dna_task,
                choices_task,
                return_exceptions=True
            )
            
            # STEP 4: UPDATE CHAPTER WITH SUMMARY + DNA + CHOICES
            await self._batch_update_chapter_with_dna(
                chapter_id=chapter_id,
                story_id=story_id,
                chapter_number=chapter_number,  # FIXED: Added chapter_number parameter
                user_id=user_id,                # FIXED: Added user_id parameter
                summary=summary_result if not isinstance(summary_result, Exception) else None,
                dna=dna_result if not isinstance(dna_result, Exception) else None,
                choices=choices_result if not isinstance(choices_result, Exception) else [],
                supabase_client=supabase_client
            )
            
            save_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(save_time, summary_result)
            
            logger.info(f"✅ Chapter {chapter_number} saved with summary, DNA, and choices in {save_time:.2f}s")
            
            return ChapterSaveResult(
                chapter_id=chapter_id,
                summary=summary_result.get('summary', '') if not isinstance(summary_result, Exception) else '',
                choices=choices_result if not isinstance(choices_result, Exception) else [],
                save_time=save_time,
                performance_metrics=self._get_performance_metrics()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to save chapter: {e}")
            raise

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
            from main import get_main_branch_id
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
        """Extract and validate choices"""
        if not choices:
            return []
        
        # Simple validation and formatting
        validated_choices = []
        for choice in choices:
            if isinstance(choice, dict) and choice.get('title'):
                validated_choices.append({
                    'title': choice.get('title', ''),
                    'description': choice.get('description', ''),
                    'story_impact': choice.get('story_impact', 'medium'),
                    'choice_type': choice.get('choice_type', 'narrative')
                })
        
        logger.info(f"✅ Validated {len(validated_choices)} choices")
        return validated_choices

    async def _get_previous_chapters_for_dna(
        self,
        story_id: int,
        current_chapter_number: int,
        supabase_client
    ) -> List[Dict[str, Any]]:
        """Get previous chapters for DNA context"""
        logger.info("📚 Getting previous chapters for DNA context...")
        
        try:
            response = supabase_client.table("Chapters").select(
                "content, summary, dna, chapter_number"
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
        """Generate story DNA in background thread"""
        logger.info("🧬 Generating DNA asynchronously...")
        
        loop = asyncio.get_event_loop()
        
        def generate_dna():
            try:
                from story_dna_extractor import EnhancedLLMStoryDNAExtractor
                dna_extractor = EnhancedLLMStoryDNAExtractor()
                
                # Extract previous DNA list
                previous_dna_list = []
                for chapter in previous_chapters:
                    if chapter.get('dna'):
                        dna = chapter['dna']
                        if isinstance(dna, str):
                            import json
                            try:
                                dna = json.loads(dna)
                            except:
                                continue
                        previous_dna_list.append(dna)
                
                # Generate DNA for current chapter
                dna_result = dna_extractor.extract_chapter_dna(
                    chapter_content=content,
                    chapter_number=chapter_number,
                    previous_dna_list=previous_dna_list,
                    user_choice_made=user_choice,
                    choice_options=[]
                )
                
                return dna_result
                
            except Exception as e:
                logger.error(f"DNA generation failed: {e}")
                return {"error": str(e), "fallback": True}
        
        dna_result = await loop.run_in_executor(
            self.summary_executor,  # Reuse executor
            generate_dna
        )
        
        logger.info("✅ DNA generated")
        return dna_result

    async def _batch_update_chapter_with_dna(
        self,
        chapter_id: int,
        story_id: int,
        chapter_number: int,  # FIXED: Added chapter_number parameter
        user_id: int,         # FIXED: Added user_id parameter
        summary: Optional[Dict[str, Any]],
        dna: Optional[Dict[str, Any]],
        choices: List[Dict[str, Any]],
        supabase_client
    ):
        """Update chapter with summary + DNA and save choices with correct schema"""
        logger.info("📝 Updating chapter with summary, DNA, and saving choices...")
        
        # PART 1: UPDATE CHAPTERS TABLE
        update_data = {}
        
        # Add summary if available
        if summary and summary.get('summary'):
            update_data['summary'] = summary['summary']
            logger.info(f"✅ Adding summary: {len(summary['summary'])} chars")
        
        # Add DNA if available (store as JSON string)
        if dna and not dna.get('error'):
            import json
            update_data['dna'] = json.dumps(dna)
            logger.info(f"✅ Adding DNA: {len(json.dumps(dna))} chars")
        
        # Update chapter
        if update_data:
            supabase_client.table("Chapters").update(update_data).eq('id', chapter_id).execute()
            logger.info(f"✅ Updated chapter with summary: {bool(summary)}, DNA: {bool(dna)}")
        
        # PART 2: SAVE CHOICES TO story_choices TABLE
        if choices:
            # Delete existing choices first
            supabase_client.table("story_choices").delete().eq('story_id', story_id).eq('chapter_number', chapter_number).execute()
            
            # Insert new choices with ALL required fields according to database schema
            choice_records = []
            for i, choice in enumerate(choices):
                choice_records.append({
                    'story_id': story_id,                           # Required - int4
                    'chapter_number': chapter_number,               # Required - int4  
                    'choice_id': str(i+1),                          # Required - text (unique ID)
                    'title': choice['title'],                       # Required - text
                    'description': choice['description'],           # Required - text
                    'story_impact': choice['story_impact'],         # Required - text
                    'choice_type': choice['choice_type'],           # Required - text
                    'user_id': user_id,                            # Required - uuid
                    'chapter_id': chapter_id,                       # Optional but good practice - int8
                    # Optional fields (can be NULL):
                    # 'is_selected': None,        # boolean (can be NULL)
                    # 'created_at': auto-generated timestamp
                    # 'selected_at': None,        # timestamp (can be NULL)
                    # 'branch_id': None           # uuid (can be NULL)
                })
            
            if choice_records:
                supabase_client.table("story_choices").insert(choice_records).execute()
                logger.info(f"✅ Saved {len(choice_records)} choices with story_id={story_id}, chapter_number={chapter_number}")
        
        logger.info("✅ Chapter update completed successfully!")

    def _update_metrics(self, save_time: float, summary_result: Any):
        """Update performance metrics"""
        self.metrics['total_saves'] += 1
        self.metrics['avg_save_time'] = (
            (self.metrics['avg_save_time'] * (self.metrics['total_saves'] - 1) + save_time) 
            / self.metrics['total_saves']
        )

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'total_saves': self.metrics['total_saves'],
            'avg_save_time': round(self.metrics['avg_save_time'], 2),
            'embedding_status': 'disabled_for_reliability'
        }

# Global instance for import compatibility
fixed_optimized_chapter_service = OptimizedChapterService()