/**
 * Frontend Cache Service for localStorage-based caching
 */

// Cache key constants
export const CACHE_KEYS = {
  EDITOR_CACHE: 'editor_cache_',
  STORY_CACHE: 'story_cache_',
  CHAPTER_CACHE: 'chapter_cache_',
  CHOICES_CACHE: 'choices_cache_',
  USER_PREFERENCES: 'user_preferences',
  THEME_SETTINGS: 'theme_settings',
  EDITOR_STATE: 'editor_state'
};

class CacheService {
  constructor() {
    this.defaultTTL = 5 * 60 * 1000; // 5 minutes in milliseconds
  }

  /**
   * Set a value in localStorage with TTL
   * @param {string} key - Cache key
   * @param {any} value - Value to cache
   * @param {number} ttl - Time to live in milliseconds
   */
  set(key, value, ttl = this.defaultTTL) {
    try {
      const cacheItem = {
        value,
        timestamp: Date.now(),
        ttl
      };
      localStorage.setItem(key, JSON.stringify(cacheItem));
    } catch (error) {
      console.warn('Cache set failed:', error);
      // Fallback: try to clear some space and retry
      this.clearOldItems();
      try {
        const cacheItem = {
          value,
          timestamp: Date.now(),
          ttl
        };
        localStorage.setItem(key, JSON.stringify(cacheItem));
      } catch (retryError) {
        console.error('Cache set retry failed:', retryError);
      }
    }
  }

  /**
   * Get a value from localStorage
   * @param {string} key - Cache key
   * @returns {any|null} - Cached value or null if not found/expired
   */
  get(key) {
    try {
      const cached = localStorage.getItem(key);
      if (!cached) return null;

      const cacheItem = JSON.parse(cached);
      const now = Date.now();
      const age = now - cacheItem.timestamp;

      // Check if expired
      if (age > cacheItem.ttl) {
        localStorage.removeItem(key);
        return null;
      }

      return cacheItem.value;
    } catch (error) {
      console.warn('Cache get failed:', error);
      // Clean up corrupted cache entry
      try {
        localStorage.removeItem(key);
      } catch (cleanupError) {
        console.error('Cache cleanup failed:', cleanupError);
      }
      return null;
    }
  }

  /**
   * Remove a specific cache entry
   * @param {string} key - Cache key to remove
   */
  delete(key) {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.warn('Cache delete failed:', error);
    }
  }

  /**
   * Clear all cache entries with a specific prefix
   * @param {string} prefix - Prefix to match
   */
  clearPattern(prefix) {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith(prefix)) {
          localStorage.removeItem(key);
        }
      });
    } catch (error) {
      console.warn('Cache clear pattern failed:', error);
    }
  }

  /**
   * Clear all cache entries
   */
  clear() {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith(CACHE_KEYS.EDITOR_CACHE) ||
            key.startsWith(CACHE_KEYS.STORY_CACHE) ||
            key.startsWith(CACHE_KEYS.CHAPTER_CACHE) ||
            key.startsWith(CACHE_KEYS.CHOICES_CACHE)) {
          localStorage.removeItem(key);
        }
      });
    } catch (error) {
      console.warn('Cache clear failed:', error);
    }
  }

  /**
   * Clear old cache items to free up space
   */
  clearOldItems() {
    try {
      const keys = Object.keys(localStorage);
      const now = Date.now();
      
      keys.forEach(key => {
        if (key.startsWith(CACHE_KEYS.EDITOR_CACHE) ||
            key.startsWith(CACHE_KEYS.STORY_CACHE) ||
            key.startsWith(CACHE_KEYS.CHAPTER_CACHE) ||
            key.startsWith(CACHE_KEYS.CHOICES_CACHE)) {
          
          try {
            const cached = localStorage.getItem(key);
            if (cached) {
              const cacheItem = JSON.parse(cached);
              const age = now - cacheItem.timestamp;
              
              // Remove if older than 1 hour
              if (age > 60 * 60 * 1000) {
                localStorage.removeItem(key);
              }
            }
          } catch (parseError) {
            // Remove corrupted entries
            localStorage.removeItem(key);
          }
        }
      });
    } catch (error) {
      console.warn('Cache cleanup failed:', error);
    }
  }

  /**
   * Get cache statistics
   * @returns {Object} - Cache stats
   */
  getStats() {
    try {
      const keys = Object.keys(localStorage);
      const cacheKeys = keys.filter(key => 
        key.startsWith(CACHE_KEYS.EDITOR_CACHE) ||
        key.startsWith(CACHE_KEYS.STORY_CACHE) ||
        key.startsWith(CACHE_KEYS.CHAPTER_CACHE) ||
        key.startsWith(CACHE_KEYS.CHOICES_CACHE)
      );

      let totalSize = 0;
      let expiredCount = 0;
      const now = Date.now();

      cacheKeys.forEach(key => {
        try {
          const cached = localStorage.getItem(key);
          if (cached) {
            totalSize += cached.length;
            const cacheItem = JSON.parse(cached);
            const age = now - cacheItem.timestamp;
            if (age > cacheItem.ttl) {
              expiredCount++;
            }
          }
        } catch (error) {
          expiredCount++;
        }
      });

      return {
        totalEntries: cacheKeys.length,
        expiredEntries: expiredCount,
        totalSize: totalSize,
        activeEntries: cacheKeys.length - expiredCount
      };
    } catch (error) {
      console.warn('Cache stats failed:', error);
      return {
        totalEntries: 0,
        expiredEntries: 0,
        totalSize: 0,
        activeEntries: 0
      };
    }
  }
}

// Create and export singleton instance
export const cacheService = new CacheService();

// Also export the class for testing
export { CacheService };
