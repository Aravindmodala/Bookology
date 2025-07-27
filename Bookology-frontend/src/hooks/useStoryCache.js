import { useState, useEffect } from 'react';
import { CacheService, CACHE_KEYS } from '../services/cacheService';

export function useStoryCache() {
  const [cachedStories, setCachedStories] = useState(null);
  const [lastSelectedStory, setLastSelectedStory] = useState(null);

  useEffect(() => {
    // Load cached stories on mount
    const stories = CacheService.get(CACHE_KEYS.SAVED_STORIES);
    if (stories) {
      setCachedStories(stories);
    }

    // Load last selected story
    const lastStory = CacheService.get(CACHE_KEYS.SELECTED_STORY);
    if (lastStory) {
      setLastSelectedStory(lastStory);
    }
  }, []);

  const cacheStories = (stories) => {
    CacheService.set(CACHE_KEYS.SAVED_STORIES, stories);
    setCachedStories(stories);
  };

  const cacheSelectedStory = (story) => {
    CacheService.set(CACHE_KEYS.SELECTED_STORY, story);
    setLastSelectedStory(story);
  };

  const clearStoriesCache = () => {
    CacheService.remove(CACHE_KEYS.SAVED_STORIES);
    CacheService.remove(CACHE_KEYS.SELECTED_STORY);
    setCachedStories(null);
    setLastSelectedStory(null);
  };

  return {
    cachedStories,
    lastSelectedStory,
    cacheStories,
    cacheSelectedStory,
    clearStoriesCache
  };
}
