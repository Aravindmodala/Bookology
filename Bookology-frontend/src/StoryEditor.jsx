import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useSearchParams, useLocation } from 'react-router-dom';
import { supabase } from './supabaseClient';
import { useAuth } from './AuthContext';
import { createApiUrl, API_ENDPOINTS } from './config';
import { useEditorStore } from './store/editorStore';
import { 
  Eye,
  EyeOff,
  BookOpen,
  FileText,
  ChevronRight,
  ChevronDown,
  Plus,
  MoreHorizontal,
  Loader2,
  Zap,
  Target,
  Users
} from 'lucide-react';
import EditorToolbar from './components/EditorToolbar';
import AIAssistantPanel from './components/AIAssistantPanel';

const StoryEditor = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const { user, session } = useAuth();
  
  // Get story data from either URL params or route state (from dashboard)
  const urlStoryId = searchParams.get('story');
  const routeStoryData = location.state?.story;
  const storyId = urlStoryId || routeStoryData?.id;
  
  // Zustand store for caching
  const { 
    getCachedData, 
    setStoryCache, 
    hasValidCache, 
    updateChapterContent,
    setChapterChoices,
    getCachedChoices,
    hasValidChoicesCache,
    updateChoiceSelection,
    addChoicesForChapter
  } = useEditorStore();
  
  const [content, setContent] = useState('');
  const [selectedText, setSelectedText] = useState('');
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isAIPanelOpen, setIsAIPanelOpen] = useState(true);
  const [activeChapter, setActiveChapter] = useState(null);
  const [showComments, setShowComments] = useState(false);
  const editorRef = useRef(null);

  // Debounced update refs
  const debounceTimeoutRef = useRef(null);
  const lastContentRef = useRef('');

  // Real data from Supabase
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [storyData, setStoryData] = useState(null);
  const [chapters, setChapters] = useState([]);

  // Choice system state (now using cached choices instead of state)
  const [choicesLoading, setChoicesLoading] = useState(false);
  const [selectedChoiceId, setSelectedChoiceId] = useState(null);
  const [generateWithChoiceLoading, setGenerateWithChoiceLoading] = useState(false);
  const [choicesError, setChoicesError] = useState('');

  // Chapter generation state
  const [generatingChapter, setGeneratingChapter] = useState(null); // Which chapter is being generated
  const [pendingChapter, setPendingChapter] = useState(null); // Data for chapter being generated

  // Story structure for sidebar
  const [storyStructure, setStoryStructure] = useState({
    frontMatter: {
      dedication: { title: 'Dedication', content: '' },
      prologue: { title: 'Prologue', content: '' }
    },
    chapters: {},
    backMatter: {
      epilogue: { title: 'Epilogue', content: '' },
      notes: { title: 'Author\'s Notes', content: '' }
    }
  });

  // Load story and chapters with caching for instant loading
  useEffect(() => {
    const loadStoryData = async () => {
      if (!storyId || !user || !session?.access_token) {
        console.log('❌ Missing required data:', { storyId, user: !!user, token: !!session?.access_token });
        setLoading(false);
        return;
      }

      console.log('📖 Loading story data for story:', storyId);

      // 🚀 STEP 1: Check cache first for instant loading
      const cachedData = getCachedData(storyId);
      
      if (cachedData.isCached) {
        console.log('⚡ Found cached data! Loading instantly...');
        
        // Load cached data immediately (no spinner!)
        setStoryData(cachedData.story);
        setChapters(cachedData.chapters);
        // Choices are already in cache, no need to set them again
        
        // Build story structure from cache
        const chaptersObject = {};
        cachedData.chapters.forEach(chapter => {
          const chapterKey = `chapter-${chapter.chapter_number}`;
          chaptersObject[chapterKey] = {
            id: chapter.id,
            title: chapter.title || `Chapter ${chapter.chapter_number}`,
            content: chapter.content || '',
            wordCount: chapter.content ? chapter.content.trim().split(/\s+/).length : 0,
            chapterNumber: chapter.chapter_number,
            createdAt: chapter.created_at
          };
        });

        setStoryStructure(prev => ({
          ...prev,
          chapters: chaptersObject
        }));

        // Set first chapter as active
        if (cachedData.chapters.length > 0) {
          const firstChapterKey = `chapter-${cachedData.chapters[0].chapter_number}`;
          setActiveChapter(firstChapterKey);
          setContent(cachedData.chapters[0].content || '');
        }
        
        setLoading(false); // Show content immediately!
        
        // Always fetch choices even from cache (choices might be updated)
        if (cachedData.chapters && cachedData.chapters.length > 0) {
          console.log('📋 Fetching choices for cached chapters...');
          await fetchChoicesForChapters(cachedData.chapters);
        }
        
        // If cache is fresh (< 5 minutes), we can skip the main background fetch
        if (!cachedData.isStale) {
          console.log('✅ Cache is fresh, skipping background fetch');
          return;
        }
        
        console.log('🔄 Cache is stale, fetching updates in background...');
      } else {
        // No cache available, show loading spinner
        setLoading(true);
        setError('');
        console.log('📡 No cache found, fetching fresh data...');
      }

      // 🔄 STEP 2: Fetch fresh data (either in background or as primary load)
      try {
        let story = null;
        
        // Get story data (from route or backend)
        if (routeStoryData) {
          console.log('✅ Using story data from route state:', routeStoryData.title);
          story = {
            id: routeStoryData.id,
            title: routeStoryData.title,
            description: routeStoryData.description,
            genre: routeStoryData.genre,
            chapter_count: routeStoryData.chapter_count,
            created_at: routeStoryData.created_at,
            status: routeStoryData.status
          };
        } else {
          console.log('🔍 Fetching story details from backend...');
          const storyResponse = await fetch(createApiUrl(`/story/${storyId}`), {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json'
            }
          });

          if (!storyResponse.ok) {
            throw new Error(`Failed to fetch story: ${storyResponse.status}`);
          }

          story = await storyResponse.json();
        }

        // Fetch chapters
        console.log('📚 Fetching chapters from backend...');
        const chaptersResponse = await fetch(createApiUrl(`/story/${storyId}/chapters`), {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!chaptersResponse.ok) {
          throw new Error(`Failed to fetch chapters: ${chaptersResponse.status}`);
        }

        const chaptersData = await chaptersResponse.json();
        const chapters = chaptersData.chapters || [];
        
        console.log(`✅ Loaded ${chapters.length} fresh chapters from backend`);

        // 📦 STEP 3: Update cache with fresh data
        setStoryCache(storyId, story, chapters, {});

        // 🎯 STEP 4: Update UI only if not already showing cached data
        if (!cachedData.isCached) {
          setStoryData(story);
          setChapters(chapters);

          // Build story structure
          const chaptersObject = {};
          chapters.forEach(chapter => {
            const chapterKey = `chapter-${chapter.chapter_number}`;
            chaptersObject[chapterKey] = {
              id: chapter.id,
              title: chapter.title || `Chapter ${chapter.chapter_number}`,
              content: chapter.content || '',
              wordCount: chapter.content ? chapter.content.trim().split(/\s+/).length : 0,
              chapterNumber: chapter.chapter_number,
              createdAt: chapter.created_at
            };
          });

          setStoryStructure(prev => ({
            ...prev,
            chapters: chaptersObject
          }));

          // Set first chapter as active
          if (chapters.length > 0) {
            const firstChapterKey = `chapter-${chapters[0].chapter_number}`;
            setActiveChapter(firstChapterKey);
            setContent(chapters[0].content || '');
          }
        } else {
          console.log('🔄 Updated cache in background, UI already showing cached data');
        }

        // Fetch choices for chapters
        if (chapters && chapters.length > 0) {
          console.log('📋 Fetching choices for', chapters.length, 'chapters...');
          await fetchChoicesForChapters(chapters);
        }

      } catch (err) {
        console.error('Error loading story:', err);
        setError(err.message || 'Failed to load story');
      } finally {
        setLoading(false);
      }
    };

    loadStoryData();
  }, [storyId, user, session, routeStoryData]);

  // Fetch choices for all chapters (cache-first approach)
  const fetchChoicesForChapters = async (chaptersData, forceRefresh = false) => {
    if (!session?.access_token) {
      console.log('❌ No access token for fetching choices');
      return;
    }

    setChoicesLoading(true);

    try {
      for (const chapter of chaptersData) {
        // Check cache first, unless forceRefresh is true
        const cachedChoices = getCachedChoices(chapter.id);
        if (!forceRefresh && cachedChoices.isCached && !cachedChoices.isStale) {
          console.log(`💨 Using cached choices for chapter ${chapter.chapter_number} (ID: ${chapter.id})`);
          console.log(`✅ Cached: ${cachedChoices.choices.length} choices, selected: ${cachedChoices.selected_choice?.title || 'none'}`);
          continue; // Skip API call, use cached data
        }

        // Fetch from API if not cached or stale, or if forceRefresh is true
        console.log(`🔍 Fetching choices for chapter ${chapter.chapter_number} (ID: ${chapter.id}) - ${!cachedChoices.isCached ? 'not cached' : 'cache stale or force refresh'}`);
        
        const response = await fetch(createApiUrl(API_ENDPOINTS.GET_CHAPTER_CHOICES.replace('{chapter_id}', chapter.id)), {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`
          }
        });

        console.log(`📡 Response for chapter ${chapter.id}:`, response.status);

        if (response.ok) {
          const data = await response.json();
          console.log(`📦 Choices data for chapter ${chapter.id}:`, data);
          
          if (data.success && data.choices && data.choices.length > 0) {
            const choicesData = {
              choices: data.choices.map(choice => ({
                ...choice,
                id: choice.id || choice.choice_id,
                choice_id: choice.choice_id || choice.id
              })),
              selected_choice: data.choices.find(c => c.is_selected) || null
            };

            // Cache the fetched choices
            setChapterChoices(chapter.id, choicesData);
            console.log(`✅ Found and cached ${data.choices.length} choices for chapter ${chapter.chapter_number}`);
          } else {
            // Cache empty result to avoid repeated API calls
            setChapterChoices(chapter.id, { choices: [], selected_choice: null });
            console.log(`ℹ️ No choices found for chapter ${chapter.chapter_number} - cached empty result`);
          }
        } else {
          console.log(`❌ Failed to fetch choices for chapter ${chapter.id}: ${response.status}`);
        }
      }
    } catch (err) {
      console.error('Error fetching choices:', err);
      setChoicesError('Failed to load chapter choices');
    } finally {
      setChoicesLoading(false);
    }
  };

  // Handle choice selection and generate next chapter
  const handleChoiceSelection = async (choiceId, choice, fromChapterNumber) => {
    if (!storyData || !session?.access_token) {
      setChoicesError('Please log in to continue the story.');
      return;
    }

    setGenerateWithChoiceLoading(true);
    setChoicesError('');

    try {
      // The next chapter number is always fromChapterNumber + 1
      const nextChapterNumber = fromChapterNumber + 1;
      
      // Set generating state for the new chapter
      setGeneratingChapter(nextChapterNumber);
      setPendingChapter({
        chapter_number: nextChapterNumber,
        title: `Chapter ${nextChapterNumber}`,
        content: '',
        wordCount: 0,
        isGenerating: true
      });

      // Add the pending chapter to the story structure immediately
      const newChapterKey = `chapter-${nextChapterNumber}`;
      setStoryStructure(prev => ({
        ...prev,
        chapters: {
          ...prev.chapters,
          [newChapterKey]: {
            title: `Chapter ${nextChapterNumber}`,
            content: 'Generating chapter...',
            wordCount: 0,
            chapterNumber: nextChapterNumber,
            isGenerating: true
          }
        }
      }));
      
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER_WITH_CHOICE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          story_id: storyData.id,
          choice_id: choiceId,
          choice_data: choice,
          next_chapter_num: nextChapterNumber
        })
      });

      const data = await response.json();

      if (data.success) {
        // Update the story structure with the generated chapter
        setStoryStructure(prev => ({
          ...prev,
          chapters: {
            ...prev.chapters,
            [newChapterKey]: {
              id: data.chapter_id || `new-${nextChapterNumber}`,
              title: `Chapter ${nextChapterNumber}`,
              content: data.chapter_content || '',
              wordCount: data.chapter_content ? data.chapter_content.trim().split(/\s+/).length : 0,
              chapterNumber: nextChapterNumber,
              createdAt: new Date().toISOString(),
              isGenerating: false
            }
          }
        }));

        // Switch to the new chapter
        setActiveChapter(newChapterKey);
        setContent(data.chapter_content || '');
        
        // Clear choice selection
        setSelectedChoiceId(null);
        
        // If there are new choices for this chapter, cache them
        if (data.choices && data.choices.length > 0) {
          const newChapterId = data.chapter_id || `new-${nextChapterNumber}`;
          const choicesData = {
            choices: data.choices.map(choice => ({
              ...choice,
              id: choice.id || choice.choice_id,
              choice_id: choice.choice_id || choice.id
            })),
            selected_choice: null
          };
          
          // Cache the new choices
          addChoicesForChapter(newChapterId, choicesData);
        }

        // --- FIX: Fetch updated chapters from backend and update cache/UI ---
        try {
          const chaptersResponse = await fetch(createApiUrl(`/story/${storyId}/chapters`), {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json'
            }
          });
          if (chaptersResponse.ok) {
            const chaptersData = await chaptersResponse.json();
            const chapters = chaptersData.chapters || [];
            setChapters(chapters);
            setStoryCache(storyId, storyData, chapters, {});
            // Update story structure
            const chaptersObject = {};
            chapters.forEach(chapter => {
              const chapterKey = `chapter-${chapter.chapter_number}`;
              chaptersObject[chapterKey] = {
                id: chapter.id,
                title: chapter.title || `Chapter ${chapter.chapter_number}`,
                content: chapter.content || '',
                wordCount: chapter.content ? chapter.content.trim().split(/\s+/).length : 0,
                chapterNumber: chapter.chapter_number,
                createdAt: chapter.created_at
              };
            });
            setStoryStructure(prev => ({
              ...prev,
              chapters: chaptersObject
            }));
          }
        } catch (refreshErr) {
          console.error('Error refreshing chapters after generation:', refreshErr);
        }
        // --- END FIX ---

      } else {
        // Remove the pending chapter on error
        setStoryStructure(prev => {
          const newChapters = { ...prev.chapters };
          delete newChapters[newChapterKey];
          return {
            ...prev,
            chapters: newChapters
          };
        });
        setChoicesError(data.detail || 'Failed to generate chapter with choice');
      }
    } catch (err) {
      console.error('Error generating chapter with choice:', err);
      // Remove the pending chapter on error
      const newChapterKey = `chapter-${fromChapterNumber + 1}`;
      setStoryStructure(prev => {
        const newChapters = { ...prev.chapters };
        delete newChapters[newChapterKey];
        return {
          ...prev,
          chapters: newChapters
        };
      });
      setChoicesError('Error connecting to server');
    } finally {
      setGenerateWithChoiceLoading(false);
      setGeneratingChapter(null);
      setPendingChapter(null);
    }
  };

  // Enhanced content update handler with cache sync and debouncing
  const handleContentChange = useCallback((newContent) => {
    // Don't update if content hasn't actually changed
    if (newContent === lastContentRef.current) return;
    lastContentRef.current = newContent;

    // Update word and character counts immediately for UI responsiveness
    const text = newContent.replace(/<[^>]*>/g, ''); // Strip HTML for counting
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    setWordCount(words);
    setCharCount(text.length);

    // Clear any existing debounce timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Debounce the actual state updates to avoid interfering with typing
    debounceTimeoutRef.current = setTimeout(() => {
      setContent(newContent);
      
      // Update cache if we have an active chapter
      if (activeChapter && storyStructure.chapters[activeChapter]) {
        const chapterData = storyStructure.chapters[activeChapter];
        updateChapterContent(chapterData.id, newContent);
        
        // Also update local story structure
        setStoryStructure(prev => ({
          ...prev,
          chapters: {
            ...prev.chapters,
            [activeChapter]: {
              ...prev.chapters[activeChapter],
              content: newContent,
              wordCount: words
            }
          }
        }));
      }
    }, 300); // 300ms debounce
  }, [activeChapter, storyStructure.chapters, updateChapterContent]);

  // Update editor content when active chapter changes
  useEffect(() => {
    if (editorRef.current && activeChapter && storyStructure.chapters[activeChapter]) {
      const chapterData = storyStructure.chapters[activeChapter];
      const newContent = chapterData.content || '';
      
      // Only update if content actually changed to avoid cursor jumping
      if (editorRef.current.innerHTML !== newContent) {
        editorRef.current.innerHTML = newContent;
        lastContentRef.current = newContent;
        setContent(newContent);
        
        // Update counts
        const text = newContent.replace(/<[^>]*>/g, '');
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        setWordCount(words);
        setCharCount(text.length);
      }
    }
  }, [activeChapter, storyStructure]);

  // Handle editor input with improved event handling
  const handleEditorInput = useCallback((e) => {
    if (storyStructure.chapters[activeChapter]?.isGenerating) return;
    handleContentChange(e.target.innerHTML);
  }, [activeChapter, storyStructure, handleContentChange]);

  // Handle editor paste to clean up formatting
  const handleEditorPaste = useCallback((e) => {
    if (storyStructure.chapters[activeChapter]?.isGenerating) {
      e.preventDefault();
      return;
    }
    
    e.preventDefault();
    const text = e.clipboardData.getData('text/plain');
    document.execCommand('insertText', false, text);
  }, [activeChapter, storyStructure]);

  // Cleanup debounce timeout on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
    };
  }, []);

  // Handle generating chapter display
  useEffect(() => {
    if (editorRef.current && storyStructure.chapters[activeChapter]?.isGenerating) {
      editorRef.current.innerHTML = `
        <div style="color: #fbbf24; text-align: center; padding: 2rem;">
          <div style="font-size: 2rem; margin-bottom: 1rem;">✨</div>
          <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">AI is crafting your next chapter...</div>
          <div style="color: #9ca3af;">This may take a few moments. The chapter will appear here when ready.</div>
        </div>
      `;
    }
  }, [activeChapter, storyStructure]);

  // Mock story structure for new blank stories
  const defaultStoryStructure = {
    frontMatter: {
      dedication: { title: 'Dedication', content: '' },
      prologue: { title: 'Prologue', content: '' }
    },
    chapters: {
      'chapter-1': { 
        title: 'Chapter 1: The Grand Beginning', 
        content: 'Start writing your story here...',
        wordCount: 0
      }
    },
    backMatter: {
      epilogue: { title: 'Epilogue', content: '' },
      notes: { title: 'Author\'s Notes', content: '' }
    }
  };

  // Use real data if available, otherwise use default structure
  const currentStoryStructure = storyId && storyData ? storyStructure : defaultStoryStructure;
  const storyTitle = storyData?.story_title || storyData?.title || 'Untitled Story';
  const storyGenre = storyData?.genre || 'Fiction';

  const [expandedSections, setExpandedSections] = useState({
    frontMatter: true,
    chapters: true,
    backMatter: false
  });

  // Update word count when content changes
  useEffect(() => {
    const words = content.trim() === '' ? 0 : content.trim().split(/\s+/).length;
    const chars = content.length;
    setWordCount(words);
    setCharCount(chars);
  }, [content]);

  // Set default active chapter for new stories
  useEffect(() => {
    if (!storyId && !activeChapter) {
      setActiveChapter('chapter-1');
      setContent('Start writing your story here...');
    }
  }, [storyId, activeChapter]);

  const formatText = (command, value = null) => {
    document.execCommand(command, false, value);
    editorRef.current?.focus();
  };

  const handleSave = async () => {
    if (!activeChapter || !content) return;
    
    // For real stories, save to database
    if (storyId && currentStoryStructure.chapters[activeChapter]) {
      try {
        const chapterData = currentStoryStructure.chapters[activeChapter];
        const { error } = await supabase
          .from('Chapters')
          .update({ content: content })
          .eq('id', chapterData.id);
        
        if (error) throw error;
        console.log('Chapter saved successfully');
      } catch (err) {
        console.error('Error saving chapter:', err);
        setError('Failed to save chapter');
      }
    } else {
      // For new stories, just log
      console.log('Saving chapter:', activeChapter, content);
    }
  };

  const handleUndo = () => {
    document.execCommand('undo', false, null);
  };

  const handleRedo = () => {
    document.execCommand('redo', false, null);
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const selectChapter = (chapterId) => {
    // Save current content before switching
    if (activeChapter && currentStoryStructure.chapters[activeChapter]) {
      // For real stories, update the content in the structure
      if (storyId) {
        setStoryStructure(prev => ({
          ...prev,
          chapters: {
            ...prev.chapters,
            [activeChapter]: {
              ...prev.chapters[activeChapter],
              content: content
            }
          }
        }));
      }
    }

    setActiveChapter(chapterId);
  };

  const addNewChapter = () => {
    const newChapterId = `chapter-${Object.keys(storyStructure.chapters).length + 1}`;
    setStoryStructure(prev => ({
      ...prev,
      chapters: {
        ...prev.chapters,
        [newChapterId]: {
          title: `Chapter ${Object.keys(prev.chapters).length + 1}: New Chapter`,
          content: '',
          wordCount: 0
        }
      }
    }));
  };

  return (
    <div className="h-screen bg-gray-900 text-white flex overflow-hidden">
      {/* Loading State */}
      {loading && (
        <div className="fixed inset-0 bg-gray-900 flex items-center justify-center z-50">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
            <p className="text-gray-400">Loading story...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="fixed top-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          {error}
          <button
            onClick={() => setError('')}
            className="ml-2 text-red-200 hover:text-white"
          >
            ×
          </button>
        </div>
      )}

      {/* Sidebar - Story Structure */}
      <div className={`${isSidebarCollapsed ? 'w-12' : 'w-80'} bg-gray-800 border-r border-gray-700 transition-all duration-300 flex flex-col`}>
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          {!isSidebarCollapsed && (
            <div>
              <h2 className="text-lg font-semibold text-white">{storyTitle}</h2>
              <p className="text-sm text-gray-400">{storyGenre}</p>
            </div>
          )}
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <BookOpen className="w-5 h-5" />
          </button>
        </div>

        {!isSidebarCollapsed && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Front Matter */}
            <div>
              <button
                onClick={() => toggleSection('frontMatter')}
                className="flex items-center w-full text-left text-sm font-medium text-gray-300 hover:text-white mb-2"
              >
                {expandedSections.frontMatter ? <ChevronDown className="w-4 h-4 mr-1" /> : <ChevronRight className="w-4 h-4 mr-1" />}
                Front Matter
              </button>
              {expandedSections.frontMatter && (
                <div className="ml-5 space-y-2">
                  {Object.entries(currentStoryStructure.frontMatter).map(([key, section]) => (
                    <div key={key} className="flex items-center text-sm text-gray-400 hover:text-white cursor-pointer py-1">
                      <FileText className="w-4 h-4 mr-2" />
                      {section.title}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Chapters */}
            <div>
              <button
                onClick={() => toggleSection('chapters')}
                className="flex items-center w-full text-left text-sm font-medium text-gray-300 hover:text-white mb-2"
              >
                {expandedSections.chapters ? <ChevronDown className="w-4 h-4 mr-1" /> : <ChevronRight className="w-4 h-4 mr-1" />}
                Chapters ({Object.keys(currentStoryStructure.chapters).length})
              </button>
              {expandedSections.chapters && (
                <div className="ml-5 space-y-2">
                  {Object.entries(currentStoryStructure.chapters).map(([chapterId, chapter]) => (
                    <div 
                      key={chapterId}
                      onClick={() => !chapter.isGenerating && selectChapter(chapterId)}
                      className={`flex items-center justify-between text-sm transition-colors ${
                        chapter.isGenerating 
                          ? 'cursor-not-allowed opacity-70 bg-yellow-900/20 border border-yellow-500/30 rounded-lg py-2 px-3'
                          : `cursor-pointer py-2 px-3 rounded-lg ${
                              activeChapter === chapterId 
                                ? 'bg-blue-600 text-white' 
                                : 'text-gray-400 hover:text-white hover:bg-gray-700'
                            }`
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        {chapter.isGenerating ? (
                          <div className="w-4 h-4 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                        ) : (
                          <FileText className="w-4 h-4 mr-2" />
                        )}
                        <span className={chapter.isGenerating ? 'text-yellow-400' : ''}>
                          {chapter.title}
                          {chapter.isGenerating && ' (Generating...)'}
                        </span>
                        {/* Choice indicator */}
                        {!chapter.isGenerating && (() => {
                          const chapterCachedChoices = getCachedChoices(chapter.id);
                          return chapterCachedChoices.choices.length > 0 && (
                            <div className="flex items-center space-x-1">
                              <Zap className="w-3 h-3 text-yellow-400" />
                              <span className="text-xs text-yellow-400">{chapterCachedChoices.choices.length}</span>
                            </div>
                          );
                        })()}
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="text-xs opacity-70">
                          {chapter.isGenerating ? (
                            <span className="text-yellow-400">...</span>
                          ) : (
                            `${chapter.wordCount || 0} words`
                          )}
                        </div>
                        {/* Delete button for real stories only */}
                        {storyId && !chapter.isGenerating && (
                          <button
                            className="ml-2 text-red-400 hover:text-red-600 focus:outline-none"
                            title="Delete Chapter"
                            onClick={async (e) => {
                              e.stopPropagation();
                              if (!window.confirm(`Are you sure you want to delete ${chapter.title}? This cannot be undone.`)) return;
                              try {
                                const response = await fetch(createApiUrl(`/story/${storyId}/chapter/${chapter.chapterNumber}`), {
                                  method: 'DELETE',
                                  headers: {
                                    'Authorization': `Bearer ${session.access_token}`,
                                    'Content-Type': 'application/json'
                                  }
                                });
                                const data = await response.json();
                                if (response.ok && data.success) {
                                  // Remove from UI
                                  setStoryStructure(prev => {
                                    const newChapters = { ...prev.chapters };
                                    delete newChapters[chapterId];
                                    return { ...prev, chapters: newChapters };
                                  });
                                  setChapters(prev => prev.filter(c => c.chapter_number !== chapter.chapterNumber));
                                  // Optionally, set active chapter to previous one
                                  const chapterKeys = Object.keys(currentStoryStructure.chapters).filter(k => k !== chapterId);
                                  if (chapterKeys.length > 0) setActiveChapter(chapterKeys[0]);

                                  // If this was the last chapter, clear selected_choice and re-fetch choices for the new last chapter
                                  if (chapterKeys.length > 0) {
                                    const lastChapterKey = chapterKeys[chapterKeys.length - 1];
                                    const lastChapter = currentStoryStructure.chapters[lastChapterKey];
                                    if (lastChapter && lastChapter.id) {
                                      // Clear selected_choice in cache
                                      setChapterChoices(lastChapter.id, prev => ({
                                        ...prev,
                                        selected_choice: null
                                      }));
                                      // Re-fetch choices from backend for this chapter
                                      fetchChoicesForChapters([{ id: lastChapter.id, chapter_number: lastChapter.chapterNumber }], true); // forceRefresh
                                    }
                                  }
                                } else {
                                  alert(data.detail || 'Failed to delete chapter');
                                }
                              } catch (err) {
                                alert('Error deleting chapter.');
                              }
                            }}
                          >
                            🗑️
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {/* Add Chapter Button - only show for new stories */}
                  {!storyId && (
                    <button
                      onClick={addNewChapter}
                      className="flex items-center w-full text-sm text-gray-500 hover:text-white py-2 px-3 rounded-lg hover:bg-gray-700 transition-colors"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Chapter
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Back Matter */}
            <div>
              <button
                onClick={() => toggleSection('backMatter')}
                className="flex items-center w-full text-left text-sm font-medium text-gray-300 hover:text-white mb-2"
              >
                {expandedSections.backMatter ? <ChevronDown className="w-4 h-4 mr-1" /> : <ChevronRight className="w-4 h-4 mr-1" />}
                Back Matter
              </button>
              {expandedSections.backMatter && (
                <div className="ml-5 space-y-2">
                  {Object.entries(currentStoryStructure.backMatter).map(([key, section]) => (
                    <div key={key} className="flex items-center text-sm text-gray-400 hover:text-white cursor-pointer py-1">
                      <FileText className="w-4 h-4 mr-2" />
                      {section.title}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <EditorToolbar
          onFormat={formatText}
          onSave={handleSave}
          onUndo={handleUndo}
          onRedo={handleRedo}
          onToggleComments={() => setShowComments(!showComments)}
          showComments={showComments}
          wordCount={wordCount}
          charCount={charCount}
        />

        {/* Editor Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Main Writing Area */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-4xl mx-auto p-8">
              {/* Chapter Header */}
              {activeChapter && currentStoryStructure.chapters[activeChapter] && (
                <div className="mb-6 pb-4 border-b border-gray-700">
                  <h1 className="text-2xl font-bold text-white mb-2">
                    {currentStoryStructure.chapters[activeChapter].title}
                    {currentStoryStructure.chapters[activeChapter].isGenerating && (
                      <span className="ml-3 text-yellow-400 text-lg">(Generating...)</span>
                    )}
                  </h1>
                  <div className="flex items-center space-x-4 text-sm text-gray-400">
                    <span>{wordCount} words</span>
                    <span>{charCount} characters</span>
                    {currentStoryStructure.chapters[activeChapter].createdAt && (
                      <span>Created: {new Date(currentStoryStructure.chapters[activeChapter].createdAt).toLocaleDateString()}</span>
                    )}
                    {currentStoryStructure.chapters[activeChapter].isGenerating && (
                      <span className="flex items-center space-x-2 text-yellow-400">
                        <div className="w-4 h-4 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                        <span>AI is crafting your next chapter...</span>
                      </span>
                    )}
                  </div>
                </div>
              )}

              <div
                ref={editorRef}
                contentEditable={!currentStoryStructure.chapters[activeChapter]?.isGenerating}
                className={`min-h-screen p-6 bg-gray-800 rounded-xl border border-gray-700 text-white leading-relaxed overflow-auto ${
                  currentStoryStructure.chapters[activeChapter]?.isGenerating 
                    ? 'opacity-70 cursor-not-allowed' 
                    : 'focus:outline-none focus:ring-2 focus:ring-blue-500'
                }`}
                style={{ 
                  fontSize: '16px',
                  lineHeight: '1.7',
                  fontFamily: 'Georgia, serif',
                  minHeight: '600px',
                  maxHeight: 'none',
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word'
                }}
                onInput={handleEditorInput}
                onPaste={handleEditorPaste}
                placeholder={activeChapter ? "Continue writing this chapter..." : "Start writing your story..."}
              />

              {/* Choices Section - Show ALL choices for every chapter */}
              {activeChapter && currentStoryStructure.chapters[activeChapter] && (
                <div className="mt-8">
                  {(() => {
                    const currentChapterData = currentStoryStructure.chapters[activeChapter];
                    const cachedChoices = getCachedChoices(currentChapterData.id);
                    const hasChoices = cachedChoices.choices && cachedChoices.choices.length > 0;
                    const selectedChoice = cachedChoices.selected_choice;
                    const isLastChapter = activeChapter === `chapter-${Math.max(...Object.keys(currentStoryStructure.chapters).map(k => parseInt(k.split('-')[1])))}`;

                    // Debug logging
                    console.log('🎯 CHOICES DEBUG:', {
                      activeChapter,
                      chapterDataId: currentChapterData?.id,
                      hasChoicesData: cachedChoices.isCached,
                      choicesCount: cachedChoices.choices?.length || 0,
                      hasChoices,
                      isLastChapter,
                      cacheStale: cachedChoices.isStale,
                      selectedChoiceTitle: selectedChoice?.title || 'none'
                    });

                    // Only show choices if they exist
                    if (!hasChoices) {
                      return null; // Don't show anything if no choices exist
                    }

                    return (
                      <>
                        <div className="bg-gray-750 rounded-xl border border-gray-600 p-6">
                          <div className="flex items-center space-x-3 mb-6">
                            <Zap className="w-6 h-6 text-yellow-400" />
                            <h3 className="text-xl font-bold text-white">Story Choices</h3>
                            <span className="text-sm text-gray-400">({cachedChoices.choices.length} options)</span>
                            {selectedChoice && (
                              <span className="text-sm px-2 py-1 bg-green-900/50 text-green-300 rounded">
                                Choice Made: {selectedChoice.title}
                              </span>
                            )}
                          </div>
                          <div className="grid gap-3">
                            {cachedChoices.choices.map((choice) => (
                              <div
                                key={choice.id}
                                className={`p-4 rounded-lg border-2 transition-all duration-300 cursor-pointer ${
                                  selectedChoiceId === choice.id
                                    ? 'border-blue-500 bg-blue-900/30 ring-2 ring-blue-400/50'
                                    : 'border-gray-600 bg-gray-800/30 hover:border-gray-500'
                                }`}
                                onClick={() => {
                                  setSelectedChoiceId(choice.id);
                                  handleChoiceSelection(choice.id, choice, currentChapterData.chapterNumber);
                                }}
                              >
                                <div className="flex items-start space-x-3">
                                  <div className={`w-6 h-6 rounded-full border-2 mt-1 flex-shrink-0 ${
                                    selectedChoiceId === choice.id
                                      ? 'border-blue-500 bg-blue-500'
                                      : 'border-gray-500'
                                  }`}>
                                    {selectedChoiceId === choice.id && (
                                      <div className="w-2 h-2 bg-white rounded-full m-auto mt-1"></div>
                                    )}
                                  </div>
                                  <div className="flex-1">
                                    <h4 className="text-lg font-semibold text-white mb-2">
                                      {choice.title}
                                    </h4>
                                    <p className="text-gray-300 mb-3 leading-relaxed">
                                      {choice.description}
                                    </p>
                                    <div className="flex items-center space-x-3">
                                      <span className={`text-xs px-2 py-1 rounded ${
                                        choice.story_impact === 'high' ? 'bg-red-900/50 text-red-300' :
                                        choice.story_impact === 'medium' ? 'bg-yellow-900/50 text-yellow-300' :
                                        'bg-green-900/50 text-green-300'
                                      }`}>
                                        {choice.story_impact} impact
                                      </span>
                                      <span className="text-xs px-2 py-1 rounded bg-purple-900/50 text-purple-300">
                                        {choice.choice_type}
                                      </span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                          {/* Choice Error Display */}
                          {choicesError && (
                            <div className="mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                              <p className="text-red-200 text-sm">{choicesError}</p>
                            </div>
                          )}
                        </div>
                      </>
                    );
                  })()}
                </div>
              )}
            </div>
          </div>

          {/* AI Assistant Panel */}
          <AIAssistantPanel
            isOpen={isAIPanelOpen}
            onClose={() => setIsAIPanelOpen(false)}
            selectedText={selectedText}
            storyContext={{
              activeChapter,
              storyStructure: currentStoryStructure,
              content,
              storyTitle,
              storyGenre
            }}
          />

          {/* Show AI Panel Button */}
          {!isAIPanelOpen && (
            <button
              onClick={() => setIsAIPanelOpen(true)}
              className="fixed right-4 top-1/2 transform -translate-y-1/2 p-3 bg-blue-600 hover:bg-blue-700 rounded-full shadow-lg transition-colors"
            >
              <Eye className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default StoryEditor;