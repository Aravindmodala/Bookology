"""
Vector Search Service for Enhanced Context Retrieval

Production note:
- Heavy ML dependencies (torch, sentence-transformers) are optional and gated by
  settings.ENABLE_LOCAL_VECTOR_SEARCH. When disabled, the service becomes a no-op
  that returns empty results instead of importing heavy packages.
"""

import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from typing import TYPE_CHECKING, List

from app.core.config import settings
from app.core.logger_config import setup_logger

logger = setup_logger(__name__)

class VectorSearchService:
    """Enhanced vector search for finding relevant context from previous chapters"""
    
    def __init__(self):
        self.enabled = bool(settings.ENABLE_LOCAL_VECTOR_SEARCH)
        self.model = None
        self.device = 'cpu'
        self.engine = None
        if self.enabled:
            try:
                # Import heavy deps lazily only when enabled
                from sentence_transformers import SentenceTransformer  # type: ignore
                import torch  # type: ignore
                self.device = 'cuda' if getattr(torch, 'cuda', None) and torch.cuda.is_available() else 'cpu'
                self.model = SentenceTransformer('all-mpnet-base-v2')
                self.model.to(self.device)
                if getattr(settings, 'DATABASE_URL', None):
                    self.engine = create_engine(settings.DATABASE_URL)
                logger.info(f"VectorSearchService initialized (enabled) on device: {self.device}")
            except Exception as e:
                # If initialization fails, disable gracefully
                self.enabled = False
                self.model = None
                self.engine = None
                logger.warning(f"VectorSearchService disabled (initialization failed): {e}")
        else:
            logger.info("VectorSearchService disabled (ENABLE_LOCAL_VECTOR_SEARCH is false)")

    async def find_relevant_context(
        self,
        query_text: str,
        story_id: int,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find most relevant chapter chunks for a given query"""
        if not self.enabled or not self.model or not self.engine:
            return []
        try:
            query_embedding = self.model.encode(query_text, convert_to_tensor=False)
            results = await asyncio.to_thread(
                self._search_vectors, query_embedding, story_id, top_k, similarity_threshold
            )
            return results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def _search_vectors(
        self,
        query_embedding: List[float],
        story_id: int,
        top_k: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """Synchronous vector search"""
        if not self.enabled or not self.engine:
            return []
        try:
            with self.engine.connect() as conn:
                if not isinstance(story_id, int) or story_id <= 0:
                    raise ValueError("Invalid story_id: must be positive integer")
                if not isinstance(top_k, int) or top_k <= 0 or top_k > 100:
                    raise ValueError("Invalid top_k: must be positive integer <= 100")
                if not isinstance(similarity_threshold, (int, float)) or not (0 <= similarity_threshold <= 1):
                    raise ValueError("Invalid similarity_threshold: must be between 0 and 1")
                results = conn.execute(
                    text(
                        """
                        SELECT 
                            cv.chunk_text,
                            cv.metadata,
                            cv.chunk_index,
                            c.chapter_number,
                            c.title as chapter_title,
                            1 - (cv.embedding <=> :query_embedding::vector) as similarity_score
                        FROM chapter_vectors cv
                        JOIN chapters c ON cv.chapter_id = c.id
                        WHERE c.story_id = :story_id
                        AND c.is_active = true
                        AND (1 - (cv.embedding <=> :query_embedding::vector)) >= :threshold
                        ORDER BY cv.embedding <=> :query_embedding::vector
                        LIMIT :top_k
                        """
                    ),
                    {
                        "query_embedding": query_embedding,
                        "story_id": story_id,
                        "threshold": similarity_threshold,
                        "top_k": top_k,
                    },
                )
                return [
                    {
                        "chunk_text": row.chunk_text,
                        "metadata": row.metadata,
                        "chunk_index": row.chunk_index,
                        "chapter_number": row.chapter_number,
                        "chapter_title": row.chapter_title,
                        "similarity_score": float(row.similarity_score),
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f"Database vector search failed: {e}")
            return []

    async def get_chapter_context_enhanced(
        self,
        current_scene: str,
        story_id: int,
        max_context_length: int = 4000,
    ) -> str:
        """Get enhanced context for next chapter generation using vector similarity"""
        relevant_chunks = await self.find_relevant_context(
            query_text=current_scene, story_id=story_id, top_k=10, similarity_threshold=0.6
        )
        if not relevant_chunks:
            return "No previous context available."
        relevant_chunks.sort(key=lambda x: (-x["similarity_score"], x["chapter_number"]))
        context_parts, current_length = [], 0
        for chunk in relevant_chunks:
            chapter_header = f"\n--- Chapter {chunk['chapter_number']}: {chunk['chapter_title']} ---\n"
            chunk_text = chunk["chunk_text"]
            estimated_length = len(chapter_header) + len(chunk_text) + 50
            if current_length + estimated_length > max_context_length:
                break
            context_parts.append(f"{chapter_header}{chunk_text}")
            current_length += estimated_length
        if not context_parts:
            return "No relevant context found within length limits."
        context = "\n".join(context_parts)
        context_header = (
            f"RELEVANT CONTEXT FROM PREVIOUS CHAPTERS ({len(context_parts)} chunks):\n"
            f"Context Selection: Vector similarity search (threshold: 0.6)\n"
            f"Total Context Length: {len(context)} characters\n\n"
        )
        return context_header + context

# Global instance
vector_search_service = VectorSearchService()





