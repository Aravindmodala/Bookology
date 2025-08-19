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
  SAVE_OUTLINE: '/save_outline',  // New endpoint for saving edited outline
  GENERATE_CHAPTER: '/lc_generate_chapter',
  SAVE_STORY: '/stories/save',
  GENERATE_NEXT_CHAPTER: '/generate_next_chapter',
  SAVE_CHAPTER: '/save_chapter_with_summary',
  STORY_CHAT: '/story_chat',
  HEALTH: '/health',
  GET_Stories: '/Stories',
  ENSURE_EMBEDDINGS: '/Stories/{story_id}/ensure_embeddings',
  // New branching choices endpoints
  GENERATE_CHOICES: '/generate_choices',
  GENERATE_CHAPTER_WITH_CHOICE: '/generate_chapter_with_choice',
  CHOICE_HISTORY: '/story/{story_id}/choice_history',
  BRANCH_FROM_CHOICE: '/branch_from_choice',
  BRANCH_PREVIEW: '/branch_preview',
  // New branching endpoints
  CREATE_BRANCH: '/create_branch',
  GET_BRANCHES: '/story/{story_id}/branches',
  GET_BRANCH_CHAPTERS: '/story/{story_id}/branch/{branch_id}/chapters',
  GET_STORY_TREE: '/story/{story_id}/tree',
  SET_MAIN_BRANCH: '/set_main_branch',
  // New versioning endpoints
  ACCEPT_PREVIEW_WITH_VERSIONING: '/accept_preview_with_versioning',
  GET_CHAPTER_VERSIONS: '/story/{story_id}/chapter/{chapter_number}/versions',
  SWITCH_CHAPTER_VERSION: '/story/{story_id}/chapter/{chapter_number}/switch_version',
  SAVE_PREVIEWED_CHAPTER: '/save_previewed_chapter', // New endpoint for saving previewed chapter
  // Chapter-specific choice endpoint
  GET_CHAPTER_CHOICES: '/chapter/{chapter_id}/choices', // New endpoint for fetching choices by chapter_id
  // Cover generation endpoints
  GENERATE_COVER: '/story/{story_id}/generate_cover',
  GET_COVER_STATUS: '/story/{story_id}/cover_status',
  UPLOAD_COVER: '/story/{story_id}/upload_cover',
  REMOVE_COVER: '/story/{story_id}/cover',
  // Rewrite functionality
  REWRITE_TEXT: '/rewrite_text',
  SUGGEST_CONTINUE: '/suggest_continue',
  // Story visibility endpoints
  UPDATE_STORY_VISIBILITY: '/story/{story_id}/visibility',
  GET_PUBLIC_STORIES: '/stories/public',
  // Like and comment endpoints
  TOGGLE_STORY_LIKE: '/story/{story_id}/like',
  ADD_STORY_COMMENT: '/story/{story_id}/comment',
  GET_STORY_LIKES: '/story/{story_id}/likes',
  GET_STORY_COMMENTS: '/story/{story_id}/comments',
  // Public story viewing endpoints
  GET_STORY_DETAILS: '/story/{story_id}',
  GET_STORY_CHAPTERS: '/story/{story_id}/chapters',
  UPDATE_CHAPTER_CONTENT: '/update_chapter_content' // Real-time save endpoint
};