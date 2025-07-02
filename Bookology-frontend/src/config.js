// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Helper function to create API URLs
export const createApiUrl = (endpoint) => {
  // Ensure endpoint starts with /
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${API_BASE_URL}${cleanEndpoint}`;
};

// Export common API endpoints
export const API_ENDPOINTS = {
  GENERATE_OUTLINE: '/lc_generate_outline',
  GENERATE_CHAPTER: '/lc_generate_chapter',
  SAVE_STORY: '/stories/save',
  GENERATE_NEXT_CHAPTER: '/generate_next_chapter',
  SAVE_CHAPTER: '/save_chapter_with_summary',
  STORY_CHAT: '/story_chat',
  HEALTH: '/health',
  GET_STORIES: '/stories',
  ENSURE_EMBEDDINGS: '/stories/{story_id}/ensure_embeddings'
};