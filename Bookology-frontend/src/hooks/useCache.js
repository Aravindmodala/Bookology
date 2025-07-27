import { useState, useEffect } from 'react';
import { CacheService } from '../services/cacheService';

const CACHE_KEYS = {
    SAVED_STORIES: 'bookology_saved_stories',
    SELECTED_STORY: 'bookology_selected_story',
    CHAPTERS: 'bookology_chapters',
    CHOICE_HISTORY: 'bookology_choice_history',
    STORY_OUTLINE: 'bookology_story_outline',
    CURRENT_CHAPTER: 'bookology_current_chapter'
};

export function useCache(key, initialValue = null, ttl = 3600000) {
    const [cachedData, setCachedData] = useState(() => {
        try {
            const data = CacheService.get(key);
            return data !== null ? data : initialValue;
        } catch (error) {
            console.warn('Cache read failed:', error);
            return initialValue;
        }
    });

    const updateCache = (newData) => {
        try {
            CacheService.set(key, newData, ttl);
            setCachedData(newData);
        } catch (error) {
            console.warn('Cache write failed:', error);
        }
    };

    const clearCache = () => {
        try {
            CacheService.remove(key);
            setCachedData(initialValue);
        } catch (error) {
            console.warn('Cache clear failed:', error);
        }
    };

    return [cachedData, updateCache, clearCache];
}

export { CACHE_KEYS };
