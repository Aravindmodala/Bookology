"""
Simple In-Memory Cache Service for Performance Optimization
"""

import time
from typing import Any, Dict, Optional
from threading import Lock

class SimpleCache:
    """
    Simple thread-safe in-memory cache with TTL support
    """
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self.lock:
            if key not in self.cache:
                return None
                
            entry = self.cache[key]
            if time.time() > entry['expires_at']:
                del self.cache[key]
                return None
                
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        with self.lock:
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        with self.lock:
            self.cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_entries = len(self.cache)
            expired_entries = sum(
                1 for entry in self.cache.values() 
                if time.time() > entry['expires_at']
            )
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries
            }

# Global cache instance
cache = SimpleCache(default_ttl=300)  # 5 minutes default TTL 