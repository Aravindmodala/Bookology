"""
Vector Search Service for Enhanced Context Retrieval
"""

import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
import numpy as np
import torch

from app.core.config import settings
from app.core.logger_config import setup_logger

logger = setup_logger(__name__)

class VectorSearchService:
    """
    Enhanced vector search for finding relevant context from previous chapters
    """
    
    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)
        self.engine = create_engine(settings.DATABASE_URL)
        
        logger.info(f"VectorSearchService initialized on device: {self.device}")

    async def find_relevant_context(
        self,
        query_text: str,
        story_id: int,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find most relevant chapter chunks for a given query
        """
        try:
            # Generate query embedding
            query_embedding = self.model.encode(query_text, convert_to_tensor=False)
            
            # Search in database
            async with asyncio.to_thread(self._search_vectors, query_embedding, story_id, top_k, similarity_threshold) as results:
                return results
                
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def _search_vectors(
        self,
        query_embedding: np.ndarray,
        story_id: int,
        top_k: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """Synchronous vector search"""
        try:
            with self.engine.connect() as conn:
                # SECURITY: Use parameterized queries to prevent SQL injection
                # Validate inputs before query execution
                if not isinstance(story_id, int) or story_id <= 0:
                    raise ValueError("Invalid story_id: must be positive integer")
                if not isinstance(top_k, int) or top_k <= 0 or top_k > 100:
                    raise ValueError("Invalid top_k: must be positive integer <= 100")
                if not isinstance(similarity_threshold, (int, float)) or similarity_threshold < 0 or similarity_threshold > 1:
                    raise ValueError("Invalid similarity_threshold: must be between 0 and 1")
                
                results = conn.execute(
                    text("""
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
                    """),
                    {
                        "query_embedding": query_embedding.tolist(),
                        "story_id": story_id,
                        "threshold": similarity_threshold,
                        "top_k": top_k
                    }
                )
                
                return [
                    {
                        "chunk_text": row.chunk_text,
                        "metadata": row.metadata,
                        "chunk_index": row.chunk_index,
                        "chapter_number": row.chapter_number,
                        "chapter_title": row.chapter_title,
                        "similarity_score": float(row.similarity_score)
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
        max_context_length: int = 4000
    ) -> str:
        """
        Get enhanced context for next chapter generation using vector similarity
        """
        # Find relevant chunks
        relevant_chunks = await self.find_relevant_context(
            query_text=current_scene,
            story_id=story_id,
            top_k=10,
            similarity_threshold=0.6
        )
        
        if not relevant_chunks:
            return "No previous context available."
        
        # Sort by chapter number and similarity
        relevant_chunks.sort(
            key=lambda x: (-x['similarity_score'], x['chapter_number'])
        )
        
        # Build context string within length limit
        context_parts = []
        current_length = 0
        
        for chunk in relevant_chunks:
            chapter_header = f"\n--- Chapter {chunk['chapter_number']}: {chunk['chapter_title']} ---\n"
            chunk_text = chunk['chunk_text']
            
            estimated_length = len(chapter_header) + len(chunk_text) + 50  # Buffer
            
            if current_length + estimated_length > max_context_length:
                break
                
            context_parts.append(f"{chapter_header}{chunk_text}")
            current_length += estimated_length
        
        if not context_parts:
            return "No relevant context found within length limits."
        
        context = "\n".join(context_parts)
        
        # Add metadata
        context_header = f"RELEVANT CONTEXT FROM PREVIOUS CHAPTERS ({len(context_parts)} chunks):\n"
        context_header += f"Context Selection: Vector similarity search (threshold: 0.6)\n"
        context_header += f"Total Context Length: {len(context)} characters\n\n"
        
        return context_header + context

    async def analyze_story_consistency(
        self,
        story_id: int
    ) -> Dict[str, Any]:
        """
        Analyze story consistency using vector embeddings
        """
        try:
            with self.engine.connect() as conn:
                # Get all chapter chunks
                results = conn.execute(
                    text("""
                        SELECT 
                            cv.embedding,
                            cv.chunk_text,
                            c.chapter_number
                        FROM chapter_vectors cv
                        JOIN chapters c ON cv.chapter_id = c.id
                        WHERE c.story_id = :story_id
                        AND c.is_active = true
                        ORDER BY c.chapter_number, cv.chunk_index
                    """),
                    {"story_id": story_id}
                )
                
                chunks = list(results)
                
                if len(chunks) < 2:
                    return {"consistency_score": 1.0, "analysis": "Insufficient data"}
                
                # Calculate average similarity between consecutive chapters
                similarities = []
                for i in range(len(chunks) - 1):
                    emb1 = np.array(chunks[i].embedding)
                    emb2 = np.array(chunks[i + 1].embedding)
                    
                    # Cosine similarity
                    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                    similarities.append(similarity)
                
                consistency_score = np.mean(similarities)
                
                return {
                    "consistency_score": float(consistency_score),
                    "analysis": "High consistency" if consistency_score > 0.8 else "Moderate consistency" if consistency_score > 0.6 else "Low consistency",
                    "chunk_count": len(chunks),
                    "similarity_range": [float(min(similarities)), float(max(similarities))]
                }
                
        except Exception as e:
            logger.error(f"Consistency analysis failed: {e}")
            return {"consistency_score": 0.0, "analysis": "Analysis failed", "error": str(e)}

# Global instance
vector_search_service = VectorSearchService() 