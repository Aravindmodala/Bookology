"""
Optimized Chapter Service - High Performance Save Pipeline
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import psutil

from sqlalchemy import text
from sentence_transformers import SentenceTransformer
import torch

from config import settings
from logger_config import setup_logger
from chapter_summary import generate_chapter_summary

logger = setup_logger(__name__)

@dataclass
class ChapterSaveResult:
    chapter_id: int
    summary: str
    choices: List[Dict[str, Any]]
    vector_chunks: int
    save_time: float
    performance_metrics: Dict[str, Any]

class OptimizedChapterService:
    """
    High-performance chapter service with:
    1. Async pipeline processing
    2. Batch database operations
    3. Background vector embedding
    4. Smart caching
    5. Performance monitoring
    """
    
    def __init__(self):
        # Initialize components
        self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.embedding_model.to(self.device)
        
        # Thread pools for CPU-bound tasks
        self.summary_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="summary")
        self.vector_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="vector")
        
        # Performance tracking
        self.metrics = {
            'total_saves': 0,
            'avg_save_time': 0,
            'vector_generation_time': 0,
            'summary_generation_time': 0
        }
        
        logger.info(f"OptimizedChapterService initialized on device: {self.device}")

    async def save_chapter_optimized(
        self,
        chapter_data: Dict[str, Any],
        user_id: int,
        supabase_client
    ) -> ChapterSaveResult:
        """
        Optimized chapter save with async pipeline:
        1. Immediate chapter save (priority)
        2. Parallel summary + DNA + vector generation
        3. Batch update operations
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
            
            # STEP 3: PARALLEL ASYNC OPERATIONS
            summary_task = self._generate_summary_async(content, chapter_number, story_id)
            dna_task = self._generate_dna_async(content, chapter_number, previous_chapters, chapter_data.get('user_choice', ''))
            vector_task = self._generate_vectors_async(content, chapter_id)
            choices_task = self._extract_choices_async(chapter_data.get('choices', []))
            
            # Wait for all parallel operations
            summary_result, dna_result, vector_result, choices_result = await asyncio.gather(
                summary_task,
                dna_task,
                vector_task,
                choices_task,
                return_exceptions=True
            )
            
            # STEP 4: BATCH UPDATE OPERATIONS
            await self._batch_update_chapter_with_dna(
                chapter_id=chapter_id,
                story_id=story_id,  # FIXED: Pass story_id
                summary=summary_result if not isinstance(summary_result, Exception) else None,
                dna=dna_result if not isinstance(dna_result, Exception) else None,
                choices=choices_result if not isinstance(choices_result, Exception) else [],
                supabase_client=supabase_client
            )
            
            # STEP 5: BACKGROUND VECTOR STORAGE
            if not isinstance(vector_result, Exception):
                asyncio.create_task(
                    self._store_vectors_background(chapter_id, vector_result)
                )
            
            save_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(save_time, summary_result, vector_result)
            
            logger.info(f"✅ Chapter {chapter_number} saved with DNA and summaries in {save_time:.2f}s")
            
            return ChapterSaveResult(
                chapter_id=chapter_id,
                summary=summary_result.get('summary', '') if not isinstance(summary_result, Exception) else '',
                choices=choices_result if not isinstance(choices_result, Exception) else [],
                vector_chunks=len(vector_result) if not isinstance(vector_result, Exception) else 0,
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

    async def _generate_vectors_async(
        self, 
        content: str, 
        chapter_id: int
    ) -> List[Dict[str, Any]]:
        """Generate vector embeddings in background thread"""
        logger.info("🔢 Generating vectors asynchronously...")
        
        loop = asyncio.get_event_loop()
        
        def generate_vectors():
            # Split into chunks
            chunks = self._smart_chunk_text(content)
            
            # Generate embeddings in batches
            embeddings = self.embedding_model.encode(
                chunks,
                batch_size=16,
                device=self.device,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Prepare vector data
            vector_data = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_data.append({
                    'chapter_id': chapter_id,
                    'chunk_index': i,
                    'chunk_text': chunk[:2000],  # Limit text length
                    'embedding': embedding.tolist(),
                    'metadata': {
                        'chunk_length': len(chunk),
                        'position': i / len(chunks)
                    }
                })
            
            return vector_data
        
        vector_result = await loop.run_in_executor(
            self.vector_executor,
            generate_vectors
        )
        
        logger.info(f"✅ Generated {len(vector_result)} vector chunks")
        return vector_result

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
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.warning(f"Failed to parse DNA JSON: {e}")
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

    async def _batch_update_chapter(
        self,
        chapter_id: int,
        story_id: int,  # FIXED: Added story_id parameter
        summary: Optional[Dict[str, Any]],
        choices: List[Dict[str, Any]],
        supabase_client
    ):
        """Batch update chapter with summary and choices"""
        logger.info("📝 Batch updating chapter data...")
        
        # Update chapter with summary
        if summary and summary.get('summary'):
            update_data = {
                'summary': summary['summary'],
                'updated_at': datetime.utcnow().isoformat()
            }
            
            supabase_client.table("Chapters").update(update_data).eq('id', chapter_id).execute()
        
        # Save choices if available
        if choices:
            # Delete existing choices first
            supabase_client.table("story_choices").delete().eq('chapter_id', chapter_id).execute()
            
            # Insert new choices
            choice_records = []
            for choice in choices:
                choice_records.append({
                    'chapter_id': chapter_id,
                    'story_id': story_id,  # FIXED: Added story_id
                    'title': choice['title'],
                    'description': choice['description'],
                    'story_impact': choice['story_impact'],
                    'choice_type': choice['choice_type']
                })
            
            if choice_records:
                supabase_client.table("story_choices").insert(choice_records).execute()
        
        logger.info("✅ Batch update completed")

    async def _batch_update_chapter_with_dna(
        self,
        chapter_id: int,
        story_id: int,  # FIXED: Added story_id parameter
        summary: Optional[Dict[str, Any]],
        dna: Optional[Dict[str, Any]],
        choices: List[Dict[str, Any]],
        supabase_client
    ):
        """Batch update chapter with summary, DNA, and choices"""
        logger.info("📝 Batch updating chapter with DNA and summary...")
        
        # Prepare update data (removed updated_at as it doesn't exist in schema)
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
        if len(update_data) > 0:  # Has summary or DNA to update
            supabase_client.table("Chapters").update(update_data).eq('id', chapter_id).execute()
            logger.info(f"✅ Updated chapter with summary: {bool(summary)}, DNA: {bool(dna)}")
        
        # Save choices if available
        if choices:
            # Delete existing choices first
            supabase_client.table("story_choices").delete().eq('chapter_id', chapter_id).execute()
            
            # Insert new choices with story_id
            choice_records = []
            for choice in choices:
                choice_records.append({
                    'chapter_id': chapter_id,
                    'story_id': story_id,  # FIXED: Added story_id - THIS IS THE KEY FIX!
                    'title': choice['title'],
                    'description': choice['description'],
                    'story_impact': choice['story_impact'],
                    'choice_type': choice['choice_type']
                })
            
            if choice_records:
                supabase_client.table("story_choices").insert(choice_records).execute()
        
        logger.info("✅ Batch update with DNA completed")

    async def _store_vectors_background(
        self,
        chapter_id: int,
        vector_data: List[Dict[str, Any]]
    ):
        """Store vectors in background - lowest priority"""
        logger.info("🔄 Storing vectors in background...")
        
        try:
            # This runs in background - failures won't affect main save
            from sqlalchemy import create_engine
            engine = create_engine(settings.DATABASE_URL)
            
            with engine.connect() as conn:
                # Ensure table exists
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS chapter_vectors (
                        id SERIAL PRIMARY KEY,
                        chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
                        chunk_index INTEGER,
                        chunk_text TEXT,
                        embedding vector(768),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                
                # Insert vectors in batch
                for vector in vector_data:
                    conn.execute(
                        text("""
                            INSERT INTO chapter_vectors 
                            (chapter_id, chunk_index, chunk_text, embedding, metadata)
                            VALUES (:chapter_id, :chunk_index, :chunk_text, :embedding, :metadata)
                        """),
                        vector
                    )
                
                conn.commit()
            
            logger.info(f"✅ Stored {len(vector_data)} vectors for chapter {chapter_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Vector storage failed (non-critical): {e}")

    def _smart_chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 128) -> List[str]:
        """Smart text chunking with sentence boundary preservation"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > chunk_size and current_chunk:
                # Finalize current chunk
                chunks.append('. '.join(current_chunk) + '.')
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
        
        return chunks

    def _update_metrics(self, save_time: float, summary_result: Any, vector_result: Any):
        """Update performance metrics"""
        self.metrics['total_saves'] += 1
        self.metrics['avg_save_time'] = (
            (self.metrics['avg_save_time'] * (self.metrics['total_saves'] - 1) + save_time) 
            / self.metrics['total_saves']
        )

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        memory_info = psutil.Process().memory_info()
        
        return {
            'total_saves': self.metrics['total_saves'],
            'avg_save_time': round(self.metrics['avg_save_time'], 2),
            'memory_usage_mb': round(memory_info.rss / 1024 / 1024, 2),
            'device': self.device,
            'embedding_model': 'all-mpnet-base-v2'
        }

# Global instance
optimized_chapter_service = OptimizedChapterService()