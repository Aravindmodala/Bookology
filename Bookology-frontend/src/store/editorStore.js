import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { CacheService, CACHE_KEYS } from '../services/cacheService';

export const useEditorStore = create(
  persist(
    (set, get) => ({
      // Cached data
      cachedStoryId: null,
      cachedStory: null,
      cachedChapters: [],
      cachedChoices: {}, // { [chapterId]: { choices: [...], selected_choice: {...}, timestamp: number } }
      lastUpdated: null,
      
      // Cache management
      setStoryCache: (storyId, story, chapters, choices = {}) => {
        console.log('📦 Caching story data:', story?.title);
        set({
          cachedStoryId: storyId,
          cachedStory: story,
          cachedChapters: chapters,
          cachedChoices: choices,
          lastUpdated: Date.now()
        });
        // Also cache in localStorage for persistence
        CacheService.set(
          `editor_cache_${storyId}`,
          { story, chapters, choices },
          5 * 60 * 1000 // 5 min TTL
        );
      },
      
      // Get cached data for a story
      getCachedData: (storyId) => {
        // Try localStorage first for instant reloads
        const cached = CacheService.get(`editor_cache_${storyId}`);
        if (cached) {
          return {
            story: cached.story,
            chapters: cached.chapters,
            choices: cached.choices,
            isCached: true,
            isStale: false // TTL already checked by CacheService
          };
        }
        // Fallback to in-memory state
        const state = get();
        if (state.cachedStoryId === storyId) {
          const cacheAge = Date.now() - (state.lastUpdated || 0);
          const isStale = cacheAge > 5 * 60 * 1000; // 5 minutes
          
          return {
            story: state.cachedStory,
            chapters: state.cachedChapters,
            choices: state.cachedChoices,
            isCached: true,
            isStale
          };
        }
        return {
          story: null,
          chapters: [],
          choices: {},
          isCached: false,
          isStale: false
        };
      },

      // === CHOICES CACHING METHODS ===
      
      // Set choices for a specific chapter
      setChapterChoices: (chapterId, choicesData) => {
        const state = get();
        console.log(`📦 Caching choices for chapter ${chapterId}:`, choicesData?.choices?.length || 0);
        
        const updatedChoices = {
          ...state.cachedChoices,
          [chapterId]: {
            choices: choicesData?.choices || [],
            selected_choice: choicesData?.selected_choice || null,
            timestamp: Date.now()
          }
        };
        
        set({
          cachedChoices: updatedChoices,
          lastUpdated: Date.now()
        });
      },
      
      // Get cached choices for a specific chapter
      getCachedChoices: (chapterId) => {
        const state = get();
        const cachedChoice = state.cachedChoices[chapterId];
        
        if (!cachedChoice) {
          return { choices: [], selected_choice: null, isCached: false, isStale: false };
        }
        
        const cacheAge = Date.now() - (cachedChoice.timestamp || 0);
        const isStale = cacheAge > 5 * 60 * 1000; // 5 minutes
        
        return {
          choices: cachedChoice.choices || [],
          selected_choice: cachedChoice.selected_choice || null,
          isCached: true,
          isStale
        };
      },
      
      // Update choice selection for a chapter
      updateChoiceSelection: (chapterId, selectedChoiceId) => {
        const state = get();
        const cachedChoice = state.cachedChoices[chapterId];
        
        if (cachedChoice) {
          const updatedChoices = cachedChoice.choices.map(choice => ({
            ...choice,
            is_selected: choice.id === selectedChoiceId
          }));
          
          const selectedChoice = updatedChoices.find(c => c.id === selectedChoiceId) || null;
          
          const updatedChoicesCache = {
            ...state.cachedChoices,
            [chapterId]: {
              ...cachedChoice,
              choices: updatedChoices,
              selected_choice: selectedChoice,
              timestamp: Date.now()
            }
          };
          
          console.log(`✅ Updated choice selection for chapter ${chapterId}:`, selectedChoice?.title);
          
          set({
            cachedChoices: updatedChoicesCache,
            lastUpdated: Date.now()
          });
        }
      },
      
      // Check if we have valid choices cache for a chapter
      hasValidChoicesCache: (chapterId) => {
        const cachedChoice = get().cachedChoices[chapterId];
        if (!cachedChoice) return false;
        
        const cacheAge = Date.now() - (cachedChoice.timestamp || 0);
        return cacheAge < 5 * 60 * 1000; // Less than 5 minutes old
      },
      
      // Add choices for a new chapter (when generating new chapters)
      addChoicesForChapter: (chapterId, choicesData) => {
        const state = get();
        const updatedChoices = {
          ...state.cachedChoices,
          [chapterId]: {
            choices: choicesData?.choices || [],
            selected_choice: choicesData?.selected_choice || null,
            timestamp: Date.now()
          }
        };
        
        console.log(`➕ Added choices for new chapter ${chapterId}:`, choicesData?.choices?.length || 0);
        
        set({
          cachedChoices: updatedChoices,
          lastUpdated: Date.now()
        });
      },
      
      // === END CHOICES CACHING METHODS ===
      
      // Update specific chapter content
      updateChapterContent: (chapterId, content) => {
        const state = get();
        const updatedChapters = state.cachedChapters.map(chapter =>
          chapter.id === chapterId 
            ? { ...chapter, content, word_count: content.split(' ').length }
            : chapter
        );
        
        set({
          cachedChapters: updatedChapters,
          lastUpdated: Date.now()
        });
      },
      
      // Add new chapter to cache
      addChapterToCache: (newChapter) => {
        const state = get();
        const updatedChapters = [...state.cachedChapters, newChapter];
        
        set({
          cachedChapters: updatedChapters,
          lastUpdated: Date.now()
        });
      },
      
      // Clear cache
      clearCache: () => {
        console.log('🗑️ Clearing editor cache');
        set({
          cachedStoryId: null,
          cachedStory: null,
          cachedChapters: [],
          cachedChoices: {},
          lastUpdated: null
        });
      },
      
      // Check if we have valid cache for a story
      hasValidCache: (storyId) => {
        const state = get();
        return state.cachedStoryId === storyId && 
               state.cachedStory && 
               state.cachedChapters.length > 0;
      },

      // Game Mode state
      gameMode: true, // default to Game mode (true = Game, false = Normal)
      setGameMode: (mode) => {
        console.log('🎮 Game mode changed to:', mode ? 'Game' : 'Normal');
        set({ gameMode: mode });
      }
    }),
    {
      name: 'bookology-editor-cache', // localStorage key
      partialize: (state) => ({
        // Only persist essential data, not functions
        cachedStoryId: state.cachedStoryId,
        cachedStory: state.cachedStory,
        cachedChapters: state.cachedChapters,
        cachedChoices: state.cachedChoices,
        lastUpdated: state.lastUpdated,
        gameMode: state.gameMode // persist game mode preference
      })
    }
  )
); 