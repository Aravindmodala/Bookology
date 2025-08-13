"""
Smart embedding service with async operations and intelligent caching.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import timedelta

from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from app.core.config import settings
from app.models.story_models import StoryWithChapters, EmbeddingChunk
from app.core.logger_config import setup_logger
from app.services.story_service_with_dna import StoryService
from app.services.cache_service import cache_service


logger = setup_logger(__name__)

class EmbeddingService:
    """
    High-performance embedding service with smart caching and async operations.
    Handles embedding generation, storage, and retrieval with optimization.
    """
    
    def __init__(self):
        self.story_service = StoryService()
        self.cache = cache_service
        self._embeddings = None
        self._vectorstore = None
        self._text_splitter = None
        self._initialization_lock = asyncio.Lock()
    
    async def _ensure_initialized(self):
        """Ensure embeddings and vectorstore are initialized."""
        if self._embeddings and self._vectorstore:
            return
        
        async with self._initialization_lock:
            # Double-check pattern
            if self._embeddings and self._vectorstore:
                return
            
            logger.info("Initializing embedding service...")
            
            # Initialize embeddings
            self._embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model="text-embedding-ada-002"
            )
            
            # Initialize vectorstore
            self._vectorstore = PGVector(
                embeddings=self._embeddings,
                connection=settings.get_postgres_connection_string(),
                collection_name=settings.VECTOR_COLLECTION_NAME,
                use_jsonb=True
            )
            
            # Initialize text splitter
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            logger.info("Embedding service initialized successfully")
    
    @cache_service.cached(ttl=timedelta(hours=24), key_prefix="embedding_exists")
    async def embeddings_exist(self, story_id: int) -> bool:
        """
        Check if embeddings exist for a story (cached).
        """
        await self._ensure_initialized()
        try:
            results = self._vectorstore.similarity_search(
                query="test",
                k=1,
                filter={"story_id": str(story_id)},
            )
            exists = len(results) > 0
            logger.debug(f"Embeddings exist for story {story_id}: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking embeddings for story {story_id}: {e}")
            return False
    
    async def get_embedding_count(self, story_id: int) -> int:
        """Get number of embedding chunks for a story."""
        await self._ensure_initialized()
        try:
            results = self._vectorstore.similarity_search(
                query="count",
                k=1000,
                filter={"story_id": str(story_id)},
            )
            return len(results)
        except Exception as e:
            logger.error(f"Error counting embeddings for story {story_id}: {e}")
            return 0
    
    async def create_embeddings_async(self, story_id: int, force_recreate: bool = False) -> bool:
        """Create embeddings for a story asynchronously."""
        logger.info(f"Creating embeddings for story {story_id} (force_recreate={force_recreate})")
        try:
            await self._ensure_initialized()
            if not force_recreate and await self.embeddings_exist(story_id):
                logger.info(f"Embeddings already exist for story {story_id}")
                return True
            story_with_Chapters = await self.story_service.get_story_with_Chapters(story_id)
            if not story_with_Chapters or not story_with_Chapters.Chapters:
                logger.warning(f"No Chapters found for story {story_id}")
                return False
            if force_recreate:
                await self._delete_embeddings(story_id)
            all_documents = []
            for chapter in story_with_Chapters.Chapters:
                chunks = self._text_splitter.split_text(chapter.content)
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            "story_id": str(story_id),
                            "chapter_id": str(chapter.id),
                            "chapter_number": str(chapter.chapter_number),
                            "chapter_title": chapter.title or f"Chapter {chapter.chapter_number}",
                            "story_title": story_with_Chapters.story.title,
                            "chunk_index": i,
                            "chunk_type": "chapter_content",
                            "source_table": chapter.source_table,
                        },
                    )
                    all_documents.append(doc)
            batch_size = 50
            for i in range(0, len(all_documents), batch_size):
                batch = all_documents[i : i + batch_size]
                await asyncio.to_thread(self._vectorstore.add_documents, batch)
            await self.cache.delete(f"embedding_exists:embeddings_exist:{story_id}")
            logger.info(f"Successfully created embeddings for story {story_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating embeddings for story {story_id}: {e}")
            return False
    
    async def _delete_embeddings(self, story_id: int):
        """Delete existing embeddings for a story."""
        logger.info(f"Deleting existing embeddings for story {story_id}")
        try:
            import psycopg
            connection_string = settings.get_postgres_connection_string()
            if "postgresql+psycopg://" in connection_string:
                connection_string = connection_string.replace("postgresql+psycopg://", "postgresql://")
            def delete_from_db():
                with psycopg.connect(connection_string) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "DELETE FROM langchain_pg_embedding WHERE cmetadata->>'story_id' = %s",
                            [str(story_id)],
                        )
                        deleted_count = cur.rowcount
                        conn.commit()
                        return deleted_count
            await asyncio.to_thread(delete_from_db)
        except Exception as e:
            logger.error(f"Error deleting embeddings for story {story_id}: {e}")
    
    async def ensure_embeddings(self, story_id: int) -> Dict[str, Any]:
        """Ensure embeddings exist for a story, creating them if necessary."""
        logger.info(f"Ensuring embeddings for story {story_id}")
        try:
            if await self.embeddings_exist(story_id):
                count = await self.get_embedding_count(story_id)
                return {"status": "exists", "message": f"Embeddings already exist for story {story_id}", "embedding_count": count, "action": "none"}
            success = await self.create_embeddings_async(story_id)
            if success:
                count = await self.get_embedding_count(story_id)
                return {"status": "created", "message": f"Embeddings created for story {story_id}", "embedding_count": count, "action": "created"}
            else:
                return {"status": "error", "message": f"Failed to create embeddings for story {story_id}", "embedding_count": 0, "action": "failed"}
        except Exception as e:
            logger.error(f"Error ensuring embeddings for story {story_id}: {e}")
            return {"status": "error", "message": f"Error ensuring embeddings: {str(e)}", "embedding_count": 0, "action": "error"}
    
    def get_vectorstore(self):
        """Get the vectorstore for direct access (sync)."""
        if not self._vectorstore:
            self._embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY,
                model="text-embedding-ada-002",
            )
            self._vectorstore = PGVector(
                embeddings=self._embeddings,
                connection=settings.get_postgres_connection_string(),
                collection_name=settings.VECTOR_COLLECTION_NAME,
                use_jsonb=True,
            )
        return self._vectorstore
    
    async def get_service_stats(self) -> Dict[str, Any]:
        await self._ensure_initialized()
        cache_stats = self.cache.get_cache_stats()
        return {
            "initialized": self._embeddings is not None and self._vectorstore is not None,
            "cache": cache_stats,
            "text_splitter_chunk_size": getattr(self._text_splitter, "chunk_size", 800) if self._text_splitter else None,
            "vectorstore_collection": settings.VECTOR_COLLECTION_NAME,
        }

# Global embedding service instance
embedding_service = EmbeddingService()





