import { useState, useEffect, useRef, useCallback } from 'react';
import { createApiUrl, API_ENDPOINTS } from '../config';

/**
 * Real-time auto-save hook with undo/redo and queueing for race-free saves
 * @param {string} content - The content to auto-save
 * @param {number} chapterId - The chapter ID
 * @param {number} storyId - The story ID
 * @param {object} options - Configuration options
 * @returns {object} Auto-save state and functions
 */
const useAutoSave = (content, chapterId, storyId, options = {}) => {
  const {
    enabled = true
  } = options;

  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState('saved');
  const [lastSaved, setLastSaved] = useState(content);
  const [error, setError] = useState(null);
  const [undoStack, setUndoStack] = useState([]);
  const [redoStack, setRedoStack] = useState([]);
  const saveQueueRef = useRef([]);
  const isSavingRef = useRef(false);
  const sessionRef = useRef(null);

  // Get session from localStorage or context
  useEffect(() => {
    const session = JSON.parse(localStorage.getItem('supabase.auth.token') || '{}');
    sessionRef.current = session;
  }, []);

  // Save to DB immediately on every content change
  useEffect(() => {
    if (!enabled || !chapterId || !storyId || !sessionRef.current?.access_token) return;
    if (content === lastSaved) return;
    // Add to save queue
    saveQueueRef.current.push(content);
    // Start processing if not already
    if (!isSavingRef.current) {
      processSaveQueue();
    }
  }, [content, chapterId, storyId, enabled]);

  // Process the save queue (race-free)
  const processSaveQueue = useCallback(async () => {
    if (isSavingRef.current || saveQueueRef.current.length === 0) return;
    isSavingRef.current = true;
    setIsSaving(true);
    setSaveStatus('saving');
    setError(null);
    try {
      // Only save the latest content in the queue
      const latestContent = saveQueueRef.current[saveQueueRef.current.length - 1];
      saveQueueRef.current = [];
      const saveData = {
        story_id: parseInt(storyId),
        chapter_id: chapterId,
        content: latestContent,
        word_count: latestContent.trim().split(/\s+/).length
      };
      const response = await fetch(createApiUrl(API_ENDPOINTS.UPDATE_CHAPTER_CONTENT), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionRef.current.access_token}`
        },
        body: JSON.stringify(saveData)
      });
      if (response.ok) {
        setSaveStatus('saved');
        setLastSaved(latestContent);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Save failed: ${response.status}`);
      }
    } catch (saveError) {
      setSaveStatus('error');
      setError(saveError.message);
    } finally {
      setIsSaving(false);
      isSavingRef.current = false;
      // If new content was queued while saving, process again
      if (saveQueueRef.current.length > 0) {
        processSaveQueue();
      }
    }
  }, [chapterId, storyId, enabled]);

  // Undo/Redo logic
  const pushUndo = useCallback((prevContent) => {
    setUndoStack((stack) => [...stack, prevContent]);
    setRedoStack([]); // Clear redo on new change
  }, []);

  const undo = useCallback(() => {
    setUndoStack((stack) => {
      if (stack.length === 0) return stack;
      setRedoStack((redo) => [content, ...redo]);
      const prev = stack[stack.length - 1];
      setLastSaved(prev);
      return stack.slice(0, -1);
    });
  }, [content]);

  const redo = useCallback(() => {
    setRedoStack((redo) => {
      if (redo.length === 0) return redo;
      setUndoStack((stack) => [...stack, content]);
      const next = redo[0];
      setLastSaved(next);
      return redo.slice(1);
    });
  }, [content]);

  // Expose undo/redo, save status, and isSaving
  return {
    isSaving,
    saveStatus,
    error,
    hasUnsavedChanges: content !== lastSaved,
    undo,
    redo,
    canUndo: undoStack.length > 0,
    canRedo: redoStack.length > 0,
    pushUndo
  };
};

export default useAutoSave; 