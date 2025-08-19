"""
Concurrency control for Bookology Backend.

This module provides semaphores and rate limiting to ensure
the application can handle concurrent users effectively.
"""

import asyncio
import threading
from contextlib import contextmanager
from typing import Dict, Any
from app.core.config import settings
from app.core.logger_config import setup_logger

logger = setup_logger(__name__)

# Global semaphores for controlling concurrent operations
LLM_SEMAPHORE = asyncio.Semaphore(settings.MAX_CONCURRENT_LLM_CALLS)
DB_SEMAPHORE = asyncio.Semaphore(settings.MAX_CONCURRENT_DB_CONNECTIONS)

# Per-endpoint semaphores for fine-grained control
GENERATION_SEMAPHORE = asyncio.Semaphore(3)  # Limit heavy generation operations
IMAGE_GENERATION_SEMAPHORE = asyncio.Semaphore(2)  # Limit DALL-E calls

# Thread-level semaphore for synchronous LLM usage
LLM_THREAD_SEMAPHORE = threading.Semaphore(settings.MAX_CONCURRENT_LLM_CALLS)

@contextmanager
def acquire_llm_thread_semaphore():
    """Context manager to throttle synchronous LLM calls (non-async code paths)."""
    LLM_THREAD_SEMAPHORE.acquire()
    try:
        yield
    finally:
        LLM_THREAD_SEMAPHORE.release()

async def with_concurrency_limit(semaphore: asyncio.Semaphore, operation_name: str = "operation"):
    """
    Context manager for applying concurrency limits.
    
    Usage:
        async with with_concurrency_limit(LLM_SEMAPHORE, "chapter_generation"):
            # Your async operation here
            result = await generate_chapter()
    """
    try:
        logger.debug(f"Acquiring semaphore for {operation_name}")
        async with semaphore:
            logger.debug(f"Semaphore acquired for {operation_name}")
            yield
    finally:
        logger.debug(f"Released semaphore for {operation_name}")

class ConcurrencyMonitor:
    """Monitor concurrent operations for metrics and debugging."""
    
    def __init__(self):
        self.active_operations: Dict[str, int] = {}
        self.total_operations: Dict[str, int] = {}
        self._lock = asyncio.Lock()
    
    async def start_operation(self, operation_type: str):
        """Record the start of an operation."""
        async with self._lock:
            self.active_operations[operation_type] = self.active_operations.get(operation_type, 0) + 1
            self.total_operations[operation_type] = self.total_operations.get(operation_type, 0) + 1
            logger.info(f"Started {operation_type}. Active: {self.active_operations[operation_type]}")
    
    async def end_operation(self, operation_type: str):
        """Record the end of an operation."""
        async with self._lock:
            if operation_type in self.active_operations:
                self.active_operations[operation_type] -= 1
                logger.info(f"Ended {operation_type}. Active: {self.active_operations[operation_type]}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current concurrency statistics."""
        return {
            "active": dict(self.active_operations),
            "total": dict(self.total_operations),
            "limits": {
                "llm_calls": settings.MAX_CONCURRENT_LLM_CALLS,
                "db_connections": settings.MAX_CONCURRENT_DB_CONNECTIONS,
                "generation_ops": 3,
                "image_generation": 2
            }
        }

# Global monitor instance
concurrency_monitor = ConcurrencyMonitor()
