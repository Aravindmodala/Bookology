// Cache service for Bookology frontend
const CACHE_KEYS = {
  SAVED_STORIES: 'bookology_saved_stories',
  SELECTED_STORY: 'bookology_selected_story',
  CHAPTERS: 'bookology_chapters',
  CHOICE_HISTORY: 'bookology_choice_history',
  USER_PREFERENCES: 'bookology_user_preferences',
  STORY_OUTLINE: 'bookology_story_outline'
};

const DEFAULT_TTL = 3600000; // 1 hour in milliseconds

class CacheService {
  static set(key, data, ttl = DEFAULT_TTL) {
    const item = {
      data,
      timestamp: Date.now(),
      ttl
    };
    localStorage.setItem(key, JSON.stringify(item));
  }

  static get(key) {
    const item = localStorage.getItem(key);
    if (!item) return null;

    const parsed = JSON.parse(item);
    if (Date.now() > parsed.timestamp + parsed.ttl) {
      localStorage.removeItem(key);
      return null;
    }
    return parsed.data;
  }

  static remove(key) {
    localStorage.removeItem(key);
  }

  static clear() {
    Object.values(CACHE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
  }
}

export { CacheService, CACHE_KEYS };
