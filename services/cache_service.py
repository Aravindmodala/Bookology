"""
Smart caching service with multiple backends.
"""

import json
import asyncio
from typing import Any, Optional, Union, Dict
from datetime import datetime, timedelta
import hashlib
from functools import wraps
from app.core.logger_config import setup_logger

logger = setup_logger(__name__)

class CacheService:
    """
    Multi-tier caching service with memory and optional Redis backend.
    Provides smart caching for embeddings, Stories, and database queries.
    """
    
    def __init__(self, max_memory_items: int = 1000):
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._max_memory_items = max_memory_items
        self._redis_client = None
        
    async def initialize_redis(self, redis_url: Optional[str] = None):
        """Initialize Redis backend if available."""
        if not redis_url:
            logger.info("No Redis URL provided, using memory-only cache")
            return
            
        try:
            import redis.asyncio as redis
            self._redis_client = redis.from_url(redis_url)
            await self._redis_client.ping()
            logger.info("Redis cache backend initialized")
        except ImportError:
            logger.warning("Redis not available, using memory-only cache")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}, using memory-only cache")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = f"{prefix}:{':'.join(map(str, args))}"
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_data += f":{':'.join(f'{k}={v}' for k, v in sorted_kwargs)}"
        
        # Hash long keys
        if len(key_data) > 200:
            key_data = f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
        
        return key_data
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Try memory cache first
        if key in self._memory_cache:
            cache_item = self._memory_cache[key]
            if datetime.now() < cache_item["expires_at"]:
                logger.debug(f"Cache hit (memory): {key}")
                return cache_item["value"]
            else:
                # Expired
                del self._memory_cache[key]
        
        # Try Redis if available
        if self._redis_client:
            try:
                value = await self._redis_client.get(key)
                if value:
                    logger.debug(f"Cache hit (Redis): {key}")
                    decoded_value = json.loads(value)
                    # Store in memory for faster access
                    self._set_memory_cache(key, decoded_value, timedelta(minutes=5))
                    return decoded_value
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl: timedelta = timedelta(hours=1)):
        """Set value in cache."""
        # Store in memory
        self._set_memory_cache(key, value, ttl)
        
        # Store in Redis if available
        if self._redis_client:
            try:
                serialized_value = json.dumps(value, default=str)
                await self._redis_client.setex(
                    key, 
                    int(ttl.total_seconds()), 
                    serialized_value
                )
                logger.debug(f"Cached in Redis: {key}")
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")
    
    def _set_memory_cache(self, key: str, value: Any, ttl: timedelta):
        """Set value in memory cache with LRU eviction."""
        # LRU eviction
        if len(self._memory_cache) >= self._max_memory_items:
            # Remove oldest item
            oldest_key = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k]["created_at"]
            )
            del self._memory_cache[oldest_key]
        
        self._memory_cache[key] = {
            "value": value,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + ttl
        }
        logger.debug(f"Cached in memory: {key}")
    
    async def delete(self, key: str):
        """Delete value from cache."""
        # Remove from memory
        if key in self._memory_cache:
            del self._memory_cache[key]
        
        # Remove from Redis
        if self._redis_client:
            try:
                await self._redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis cache delete error: {e}")
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern."""
        # Clear from memory
        keys_to_delete = [k for k in self._memory_cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self._memory_cache[key]
        
        # Clear from Redis
        if self._redis_client:
            try:
                keys = await self._redis_client.keys(f"*{pattern}*")
                if keys:
                    await self._redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis pattern clear error: {e}")
    
    def cached(self, ttl: timedelta = timedelta(hours=1), key_prefix: str = "func"):
        """Decorator for caching function results."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(
                    f"{key_prefix}:{func.__name__}", 
                    *args, 
                    **kwargs
                )
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Cache result
                await self.set(cache_key, result, ttl)
                return result
            
            return wrapper
        return decorator
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        memory_items = len(self._memory_cache)
        memory_expired = sum(
            1 for item in self._memory_cache.values()
            if datetime.now() >= item["expires_at"]
        )
        
        return {
            "memory_items": memory_items,
            "memory_expired": memory_expired,
            "memory_active": memory_items - memory_expired,
            "redis_available": self._redis_client is not None
        }

# Global cache service instance
cache_service = CacheService()