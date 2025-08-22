import pytest
import asyncio
from datetime import timedelta
from unittest.mock import patch

# Adjust path to import the app module
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.cache_service import CacheService

@pytest.fixture
def cache():
    """Provides a fresh CacheService instance for each test."""
    return CacheService(max_memory_items=3)

@pytest.mark.asyncio
async def test_set_and_get_item(cache: CacheService):
    """Test that we can set and get an item from the cache."""
    key = "test_key"
    value = {"data": "my_test_data"}
    await cache.set(key, value)

    retrieved_value = await cache.get(key)
    assert retrieved_value == value

@pytest.mark.asyncio
async def test_get_non_existent_key(cache: CacheService):
    """Test that getting a non-existent key returns None."""
    retrieved_value = await cache.get("non_existent_key")
    assert retrieved_value is None

@pytest.mark.asyncio
async def test_cache_expiration(cache: CacheService):
    """Test that a cached item expires after its TTL."""
    key = "expiring_key"
    value = "i will expire"
    ttl = timedelta(seconds=0.1)

    await cache.set(key, value, ttl=ttl)

    # Item should be present immediately
    retrieved_value = await cache.get(key)
    assert retrieved_value == value

    # Wait for the item to expire
    await asyncio.sleep(0.2)

    # Item should now be None
    expired_value = await cache.get(key)
    assert expired_value is None

@pytest.mark.asyncio
async def test_lru_eviction(cache: CacheService):
    """Test that the least recently used item is evicted when the cache is full."""
    # The cache size is 3
    await cache.set("key1", "value1")
    await asyncio.sleep(0.01) # ensure creation times are different
    await cache.set("key2", "value2")
    await asyncio.sleep(0.01)
    await cache.set("key3", "value3")

    # All keys should be present
    assert await cache.get("key1") == "value1"
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"

    # Add a 4th key, which should evict key1 (the oldest)
    await cache.set("key4", "value4")

    # key1 should be gone, others should be present
    assert await cache.get("key1") is None
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"
    assert await cache.get("key4") == "value4"

@pytest.mark.asyncio
async def test_delete_key(cache: CacheService):
    """Test that we can delete a key from the cache."""
    key = "deletable_key"
    value = "to be deleted"
    await cache.set(key, value)

    assert await cache.get(key) == value

    await cache.delete(key)

    assert await cache.get(key) is None

@pytest.mark.asyncio
async def test_clear_pattern(cache: CacheService):
    """Test clearing keys based on a pattern."""
    await cache.set("user:1:profile", {"name": "Alice"})
    await cache.set("user:2:profile", {"name": "Bob"})
    await cache.set("story:1:details", {"title": "A Great Story"})

    await cache.clear_pattern("user:")

    assert await cache.get("user:1:profile") is None
    assert await cache.get("user:2:profile") is None
    assert await cache.get("story:1:details") is not None

@pytest.mark.asyncio
async def test_cached_decorator(cache: CacheService):
    """Test the @cached decorator by checking call counts."""

    call_count = 0

    @cache.cached(ttl=timedelta(seconds=2))
    async def my_expensive_func(arg: str) -> str:
        """A dummy expensive function that tracks its calls."""
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01) # simulate work
        return f"Result for {arg}"

    # First call should execute the function
    res1 = await my_expensive_func("test_arg")
    assert res1 == "Result for test_arg"
    assert call_count == 1

    # Second call with same arg should hit the cache
    res2 = await my_expensive_func("test_arg")
    assert res2 == "Result for test_arg"
    assert call_count == 1

    # Call with a different arg should execute the function again
    res3 = await my_expensive_func("another_arg")
    assert res3 == "Result for another_arg"
    assert call_count == 2
