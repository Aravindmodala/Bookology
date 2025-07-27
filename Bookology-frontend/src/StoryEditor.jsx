import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useSearchParams, useLocation, useNavigate } from 'react-router-dom';
import { supabase } from './supabaseClient';
import { useAuth } from './AuthContext';
import { createApiUrl, API_ENDPOINTS } from './config';
import { useEditorStore } from './store/editorStore';
// OPTIMIZATION: Import icons more efficiently to reduce bundle size
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
  Users,
  ArrowLeft,
  TreePine,
  X,
  Sparkles
} from 'lucide-react';
import EditorToolbar from './components/EditorToolbar';
import AIAssistantPanel from './components/AIAssistantPanel';
// OPTIMIZATION: Lazy load heavy components
const StoryTree = React.lazy(() => import('./components/StoryTree'));
const StoryCover = React.lazy(() => import('./components/StoryCover'));
import GameModeToggle from './components/GameModeToggle';

const StoryEditor = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { user, session } = useAuth();
  
  // Get story data from either URL params or route state (from dashboard OR StoryCreator)
  const urlStoryId = searchParams.get('story');
  const routeStoryData = location.state?.story;
  const creationMode = location.state?.mode; // 'generate_chapter_1' from StoryCreator
  const storyId = urlStoryId || routeStoryData?.id;
  
  // NEW: Chapter 1 generation state
  const [isGeneratingChapter1, setIsGeneratingChapter1] = useState(false);
  const [chapter1Generated, setChapter1Generated] = useState(false);
  const [generationError, setGenerationError] = useState('');
  const [chapter1GenerationComplete, setChapter1GenerationComplete] = useState(false);
  const [saveInProgress, setSaveInProgress] = useState(false); // Track save operations
  
  // NEW: Success notification state
  const [chapterGenerationSuccess, setChapterGenerationSuccess] = useState('');
  
  // NEW: Focus mode state
  const [isFocusMode, setIsFocusMode] = useState(false);
  const [showWordCount, setShowWordCount] = useState(true);
  const [showProgressBar, setShowProgressBar] = useState(true);
  
  // NEW: AI suggestion state
  const [aiSuggestion, setAiSuggestion] = useState('');
  const [isGeneratingSuggestion, setIsGeneratingSuggestion] = useState(false);
  const [suggestionError, setSuggestionError] = useState('');
  
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
    addChoicesForChapter,
    gameMode,
    setGameMode
  } = useEditorStore();
  
  const [content, setContent] = useState('');
  const [selectedText, setSelectedText] = useState('');
  const [selectedTextRange, setSelectedTextRange] = useState(null); // Store selection range for replacement
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);
  
  // Rewrite functionality state
  const [isRewriting, setIsRewriting] = useState(false);
  const [rewriteError, setRewriteError] = useState('');
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
  const [selectedChoiceForContinuation, setSelectedChoiceForContinuation] = useState(null);
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

  // FIXED: Utility function to convert text with \n\n to HTML paragraphs
  const convertTextToHtml = useCallback((text) => {
    if (!text) return '';
    
    // If text already contains HTML tags, return as-is
    if (text.includes('<div') || text.includes('<p>')) {
      return text;
    }
    
    // Convert \n\n to paragraph breaks
    const paragraphs = text
      .split('\n\n')
      .map(paragraph => paragraph.trim())
      .filter(paragraph => paragraph.length > 0);
    
    // If no paragraph breaks found, try single \n
    if (paragraphs.length === 1 && text.includes('\n')) {
      const singleLineParagraphs = text
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);
      
      return singleLineParagraphs
        .map((line, index) => {
          const isLast = index === singleLineParagraphs.length - 1;
          const marginStyle = isLast ? '' : 'margin-bottom: 1.5rem;';
          return `<div style="${marginStyle}">${line}</div>`;
        })
        .join('');
    }
    
    // Wrap each paragraph in a div with margin-bottom, except the last one
    return paragraphs
      .map((paragraph, index) => {
        const isLast = index === paragraphs.length - 1;
        const marginStyle = isLast ? '' : 'margin-bottom: 1.5rem;';
        return `<div style="${marginStyle}">${paragraph}</div>`;
      })
      .join('');
  }, []);

  // FIX 1: Add missing loadStoryData function
  const loadStoryData = useCallback(async () => {
    if (!storyId || !user || !session?.access_token) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      
      // 1. CHECK CACHE FIRST
      const cachedData = getCachedData(storyId);
      console.log('🔍 Checking cache for story:', storyId, 'Cached:', cachedData.isCached, 'Stale:', cachedData.isStale);
      
      // 2. If we have valid cached data, use it
      if (cachedData.isCached && !cachedData.isStale) {
        console.log('✅ Using cached story data');
        setStoryData(cachedData.story);
        setChapters(cachedData.chapters);
        
        // Build story structure from cached data
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

        // FIXED: Set active chapter and content with proper HTML formatting
        if (cachedData.chapters.length > 0) {
          const firstChapterKey = `chapter-${cachedData.chapters[0].chapter_number}`;
          setActiveChapter(firstChapterKey);
          const htmlContent = convertTextToHtml(cachedData.chapters[0].content || '');
          setContent(htmlContent);
          setChapter1GenerationComplete(true);
        }
        
        setLoading(false);
        return;
      }
      
      // 3. If no valid cache, fetch from backend
      console.log('🔄 Cache miss or stale, fetching from backend');
      let chapters = [];
      let story = null;
      
      if (routeStoryData) {
        story = {
          id: routeStoryData.id,
          story_title: routeStoryData.story_title || routeStoryData.title,
          story_outline: routeStoryData.story_outline || routeStoryData.description,
          genre: routeStoryData.genre,
          chapter_count: routeStoryData.chapter_count,
          created_at: routeStoryData.created_at,
          status: routeStoryData.status
        };
      } else {
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
      chapters = chaptersData.chapters || [];

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

      // 💾 4. SAVE TO CACHE after successful fetch
      setStoryCache(storyId, story, chapters);

      // FIXED: If chapters exist, show the first one and set generation complete with proper HTML formatting
      if (chapters.length > 0) {
        const firstChapterKey = `chapter-${chapters[0].chapter_number}`;
        setActiveChapter(firstChapterKey);
        const htmlContent = convertTextToHtml(chapters[0].content || '');
        setContent(htmlContent);
        setChapter1GenerationComplete(true); // Prevent further generation
        // Fetch choices for chapters
        await fetchChoicesForChapters(chapters);
        return;
      }

      // If no chapters, and creationMode is 'generate_chapter_1', and not already complete, generate it
      // Only trigger generation if this is the initial load from StoryCreator
      if (creationMode === 'generate_chapter_1' && routeStoryData && !chapter1GenerationComplete && !isGeneratingChapter1) {
        console.log('🎯 Triggering Chapter 1 generation from useEffect (initial load from StoryCreator)');
        setTimeout(() => {
          generateChapter1FromOutline();
        }, 500);
        return;
      }

    } catch (err) {
      console.error('Error loading story data:', err);
      setError(err.message || 'Failed to load story data');
    } finally {
      setLoading(false);
    }
  }, [storyId, user, session, routeStoryData, creationMode, chapter1GenerationComplete, isGeneratingChapter1, getCachedData, setStoryCache, convertTextToHtml]);

  // NEW: Generate Chapter 1 from outline data
  const generateChapter1FromOutline = useCallback(async () => {
    if (!routeStoryData || !session?.access_token) {
      setGenerationError('Missing story data or authentication');
      return;
    }

    // Only block if a chapter already exists or save is in progress
    if (isGeneratingChapter1 || saveInProgress || Object.keys(storyStructure.chapters).length > 0) {
      console.log('⚠️ Chapter 1 generation already in progress, save in progress, or completed');
      return;
    }

    console.log('🚀 GENERATING CHAPTER 1 from outline data:', routeStoryData);
    
    setIsGeneratingChapter1(true);
    setGenerationError('');
    
    // Show generating state in editor
    setContent('');
    if (editorRef.current) {
      editorRef.current.innerHTML = `
        <div style="color: #3b82f6; text-align: center; padding: 4rem; border: 2px dashed #3b82f6; border-radius: 12px; background: rgba(59, 130, 246, 0.1);">
          <div style="font-size: 3rem; margin-bottom: 1rem;">✨</div>
          <div style="font-size: 1.5rem; margin-bottom: 1rem; font-weight: bold;">AI is crafting Chapter 1...</div>
          <div style="color: #9ca3af; font-size: 1rem; line-height: 1.6;">
            Using your outline to create an engaging opening chapter.<br/>
            This may take 30-60 seconds. The chapter will appear here when ready.
          </div>
        </div>
      `;
    }

    try {
      // Call the backend to generate Chapter 1 from outline
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          outline: routeStoryData.story_outline, // The outline text
          chapter_number: 1,
          story_id: routeStoryData.id // Include story ID for saving
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('📦 Chapter 1 generation response:', data);

      if (data.chapter_1 || data.chapter) {
        const chapterContent = data.chapter_1 || data.chapter;
        const choices = data.choices || [];
        
        console.log('✅ Chapter 1 generated successfully!');
        console.log('📊 Content length:', chapterContent.length);
        console.log('🎯 Choices generated:', choices.length);
        
        // FIXED: Convert text to HTML paragraphs and update both state and editor
        const htmlContent = convertTextToHtml(chapterContent);
        setContent(htmlContent); // Set HTML content in state
        if (editorRef.current) {
          safeUpdateEditorContent(htmlContent);
        }
        
        // Create Chapter 1 in story structure
        const chapter1Key = 'chapter-1';
        const chapter1Data = {
          id: `temp-chapter-1-${Date.now()}`, // Temporary ID until saved
          title: 'Chapter 1',
          content: chapterContent,
          wordCount: chapterContent.trim().split(/\s+/).length,
          chapterNumber: 1,
          createdAt: new Date().toISOString(),
          isNew: true // Mark as new for saving
        };

        setStoryStructure(prev => ({
          ...prev,
          chapters: {
            [chapter1Key]: chapter1Data
          }
        }));

        setActiveChapter(chapter1Key);
        setChapter1Generated(true);
        setChapter1GenerationComplete(true); // Prevent re-generation

        // Cache choices if available
        if (choices.length > 0) {
          const choicesData = {
            choices: choices.map(choice => ({
              ...choice,
              id: choice.id || choice.choice_id,
              choice_id: choice.choice_id || choice.id
            })),
            selected_choice: null
          };
          
          // Use temporary ID for caching until we get real chapter ID
          addChoicesForChapter(chapter1Data.id, choicesData);
          console.log('💾 Cached', choices.length, 'choices for Chapter 1');
        }

        // Auto-save the generated chapter (only if not already saved)
        if (!data.metadata?.already_saved) {
          console.log('💾 AUTO-SAVING Chapter 1...');
          await autoSaveChapter1(chapterContent, choices, chapter1Data);
        } else {
          console.log('✅ Chapter 1 already saved during generation, skipping auto-save');
          // Update state with real chapter ID from generation
          const realChapterId = data.metadata.chapter_id;
          if (realChapterId && choices.length > 0) {
            addChoicesForChapter(realChapterId, {
              choices: choices.map(choice => ({
                ...choice,
                id: choice.id || choice.choice_id,
                choice_id: choice.choice_id || choice.id
              })),
              selected_choice: null
            });
          }
        }

      } else {
        throw new Error(data.error || 'Failed to generate Chapter 1');
      }
    } catch (err) {
      console.error('❌ Chapter 1 generation failed:', err);
      setGenerationError(err.message || 'Failed to generate Chapter 1');
      
      // Show error in editor
      if (editorRef.current) {
        editorRef.current.innerHTML = `
          <div style="color: #ef4444; text-align: center; padding: 4rem; border: 2px dashed #ef4444; border-radius: 12px; background: rgba(239, 68, 68, 0.1);">
            <div style="font-size: 2rem; margin-bottom: 1rem;">❌</div>
            <div style="font-size: 1.2rem; margin-bottom: 1rem; font-weight: bold;">Chapter Generation Failed</div>
            <div style="color: #9ca3af; font-size: 0.9rem;">${err.message}</div>
            <button onclick="window.location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer;">
              Try Again
            </button>
          </div>
        `;
      }
    } finally {
      setIsGeneratingChapter1(false);
    }
  }, [routeStoryData, session, isGeneratingChapter1, saveInProgress, storyStructure.chapters]);

  // NEW: Auto-save Chapter 1 after generation
  const autoSaveChapter1 = useCallback(async (chapterContent, choices, tempChapterData) => {
    console.log('💾 AUTO-SAVE: Starting Chapter 1 save...');
    
    // Check if chapter already exists in current chapters state
    const existingChapter = chapters.find(c => c.chapter_number === 1);
    if (existingChapter) {
      console.log('✅ Chapter 1 already exists in state with ID:', existingChapter.id);
      console.log('⏭️ Skipping duplicate save');
      return existingChapter.id;
    }
    
    // Set save in progress to prevent concurrent saves
    if (saveInProgress) {
      console.log('⚠️ Save already in progress, skipping duplicate save');
      return;
    }
    
    try {
      setSaveInProgress(true);
      
      // Save chapter to database using the correct endpoint
      const response = await fetch(createApiUrl('/save_chapter_with_summary'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': session?.access_token ? `Bearer ${session.access_token}` : undefined,
        },
        body: JSON.stringify({
          story_id: routeStoryData.id,
          chapter_number: 1,
          content: chapterContent,
          title: 'Chapter 1',
          choices: choices, // Pass choices for chapter 1
        }),
      });
      
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to save chapter');
      
      const realChapterId = data.chapter_id || data.id;
      console.log('✅ AUTO-SAVE: Chapter 1 saved with ID:', realChapterId);
      
      // Cache choices with real chapter ID from save response
      if (realChapterId && data.choices && data.choices.length > 0) {
        console.log('💾 Caching choices from save response for real chapter ID:', realChapterId);
        addChoicesForChapter(realChapterId, {
          choices: data.choices.map(choice => ({
            ...choice,
            id: choice.id || choice.choice_id,
            choice_id: choice.choice_id || choice.id
          })),
          selected_choice: null
        });
        console.log('✅ Cached', data.choices.length, 'choices from save response');
      }

      // Refresh data after save
      await loadStoryData();
      
      return realChapterId;
    } catch (err) {
      console.error('Error auto-saving chapter:', err);
      throw err;
    } finally {
      setSaveInProgress(false);
    }
  }, [chapters, saveInProgress, session, routeStoryData, addChoicesForChapter, loadStoryData]);

  // FIX 2: Memoize fetchChoicesForChapters to prevent infinite loops
  const fetchChoicesForChapters = useCallback(async (chaptersData, forceRefresh = false) => {
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
  }, [session, getCachedChoices, setChapterChoices]);

  // FIX 3: Simplify and fix the main useEffect
  useEffect(() => {
    loadStoryData();
  }, [storyId, user, session, routeStoryData, creationMode]); // Removed problematic dependencies

  // FIX 4: Separate useEffect for chapter 1 generation to prevent infinite loops
  useEffect(() => {
    // Only trigger Chapter 1 generation once on initial load
    if (
      creationMode === 'generate_chapter_1' && 
      routeStoryData && 
      !chapter1GenerationComplete && 
      !isGeneratingChapter1 &&
      Object.keys(storyStructure.chapters).length === 0 &&
      !loading
    ) {
      console.log('🎯 Triggering Chapter 1 generation (separate useEffect)');
      const timer = setTimeout(() => {
        generateChapter1FromOutline();
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [
    creationMode, 
    routeStoryData, 
    chapter1GenerationComplete, 
    isGeneratingChapter1, 
    storyStructure.chapters, 
    loading,
    generateChapter1FromOutline
  ]);

  // Handle choice selection and generate next chapter
  const handleChoiceSelection = async (choiceId, choice, fromChapterNumber) => {
    if (!storyData || !session?.access_token) {
      setChoicesError('Please log in to continue the story.');
      return;
    }

    setGenerateWithChoiceLoading(true);
    setChoicesError('');
    setGenerationError(''); // CLEAR ANY PREVIOUS GENERATION ERRORS
    setError(''); // CLEAR ANY GENERAL ERRORS

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
            isGenerating: true,
            id: `temp-${nextChapterNumber}-${Date.now()}` // Add temporary ID
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
          choice_id: choice.choice_id || choiceId, // Use choice.choice_id first, fallback to choiceId
          choice_data: choice,
          next_chapter_num: nextChapterNumber
        })
      });

      const data = await response.json();
      console.log('📦 Chapter generation response:', data);

      if (data.success) {
        console.log('✅ Chapter generation successful!');
        
        // CLEAR ALL ERROR STATES ON SUCCESS
        setChoicesError('');
        setGenerationError('');
        setError('');
        
        // SHOW SUCCESS NOTIFICATION
        setChapterGenerationSuccess(`✅ Chapter ${nextChapterNumber} generated successfully!`);
        
        // Auto-clear success notification after 5 seconds
        setTimeout(() => {
          setChapterGenerationSuccess('');
        }, 5000);
        
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

        // FIXED: Switch to the new chapter and update content with proper HTML formatting
        setActiveChapter(newChapterKey);
        const htmlContent = convertTextToHtml(data.chapter_content || '');
        setContent(htmlContent);
        
        // Update editor content immediately
        if (editorRef.current && data.chapter_content) {
          safeUpdateEditorContent(htmlContent);
        }
        
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

        // Force refresh chapters and choices after success
        console.log('🔄 Force refreshing chapters and choices after successful generation...');
        await loadStoryData();

      } else {
        console.error('❌ Chapter generation failed:', data);
        
        // Remove the pending chapter on error
        setStoryStructure(prev => {
          const newChapters = { ...prev.chapters };
          delete newChapters[newChapterKey];
          return {
            ...prev,
            chapters: newChapters
          };
        });
        
        // Set appropriate error message
        const errorMessage = data.detail || data.message || 'Failed to generate chapter with choice';
        setChoicesError(errorMessage);
        setGenerationError(errorMessage);
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

  // New handlers for choice selection without immediate generation
  const handleChoiceClick = (choiceId, choice) => {
    setSelectedChoiceId(choiceId);
    setSelectedChoiceForContinuation({ choiceId, choice });
  };

  const handleContinueWithChoice = async () => {
    if (!selectedChoiceForContinuation) {
      setChoicesError('Please select a choice first.');
      return;
    }

    const { choiceId, choice } = selectedChoiceForContinuation;
    const currentChapterData = currentStoryStructure.chapters[activeChapter];
    
    // Call the existing generation logic
    await handleChoiceSelection(choiceId, choice, currentChapterData.chapterNumber);
    
    // Clear the selected choice after generation
    setSelectedChoiceForContinuation(null);
    setSelectedChoiceId(null);
  };

  // Handle continue story in Normal mode (without choices)
  const handleContinueStoryNormal = async () => {
    if (!session?.access_token || !storyId) {
      console.error('❌ No access token or story ID for normal continuation');
      return;
    }

    const currentChapterData = currentStoryStructure.chapters[activeChapter];
    if (!currentChapterData) {
      console.error('❌ No current chapter data for normal continuation');
      return;
    }

    const nextChapterNumber = currentChapterData.chapterNumber + 1;
    
    try {
      // Clear any existing errors
      setGenerationError('');
      setChoicesError('');
      setError('');
      
      // Set loading state
      setGenerateWithChoiceLoading(true);
      
      console.log('🎮 NORMAL MODE: Generating chapter', nextChapterNumber, 'for story', storyId);
      
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_NEXT_CHAPTER), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          story_id: parseInt(storyId),
          chapter_number: nextChapterNumber,
          story_outline: storyData?.story_outline || ''
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ NORMAL MODE: Chapter generated successfully:', data);

      if (data.success) {
        // Show success notification
        setChapterGenerationSuccess(`Chapter ${nextChapterNumber} generated successfully!`);
        
        // Auto-clear success notification after 3 seconds
        setTimeout(() => setChapterGenerationSuccess(''), 3000);

        // Force refresh to get the new chapter
        await loadStoryData();
        
        // Switch to the new chapter
        setActiveChapter(`chapter-${nextChapterNumber}`);
        
        console.log('🎮 NORMAL MODE: Successfully generated and switched to chapter', nextChapterNumber);
      } else {
        throw new Error(data.message || 'Failed to generate chapter');
      }
      
    } catch (error) {
      console.error('❌ NORMAL MODE: Chapter generation failed:', error);
      setGenerationError(`Failed to generate next chapter: ${error.message}`);
    } finally {
      setGenerateWithChoiceLoading(false);
    }
  };

  // FIXED: Helper function to safely update editor content while preserving text selection
  const safeUpdateEditorContent = useCallback((newHtmlContent) => {
    if (!editorRef.current) return;
    
    // Check if there's an active text selection
    const selection = window.getSelection();
    const hasActiveSelection = selection && selection.toString().trim().length > 0;
    
    if (hasActiveSelection) {
      console.log('🔒 Preserving text selection - skipping content update');
      return false; // Indicate that update was skipped
    }
    
    // Safe to update content
    editorRef.current.innerHTML = newHtmlContent;
    lastContentRef.current = newHtmlContent;
    return true; // Indicate that update was successful
  }, []);

  // FIX 5: Improve editor content update effect with better dependency management
  useEffect(() => {
    if (editorRef.current && activeChapter && storyStructure.chapters[activeChapter]) {
      const chapterData = storyStructure.chapters[activeChapter];
      let newContent = chapterData.content || '';
      
      // CRITICAL FIX: If content contains error message, fetch fresh data from backend
      if (newContent.includes('Error') || newContent.includes('Failed to generate') || newContent === 'Generating chapter...') {
        console.log('🔄 Detected stale/error content, fetching fresh chapter data...');
        
        // Don't update with stale content immediately, let loadStoryData handle it
        // REMOVED: loadStoryData() call from here to prevent infinite loops
        return;
      }
      
      // Only update if content actually changed to avoid cursor jumping
      if (editorRef.current.innerHTML !== newContent) {
        // FIXED: Convert text to proper HTML paragraphs
        const htmlContent = convertTextToHtml(newContent);
        const wasUpdated = safeUpdateEditorContent(htmlContent);
        
        if (wasUpdated) {
          setContent(htmlContent);
          
          // Update counts using the original text (not HTML)
          const text = newContent.replace(/<[^>]*>/g, '');
          const words = text.trim() ? text.trim().split(/\s+/).length : 0;
          setWordCount(words);
          setCharCount(text.length);
        }
      }
    }
  }, [activeChapter, storyStructure.chapters, convertTextToHtml, safeUpdateEditorContent]); // ADD safeUpdateEditorContent to dependencies

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

  // Handle editor input with improved event handling
  const handleEditorInput = useCallback((e) => {
    if (storyStructure.chapters[activeChapter]?.isGenerating) return;
    handleContentChange(e.target.innerHTML);
  }, [activeChapter, storyStructure, handleContentChange]);

  // Handle text selection for rewrite functionality
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    const selectedContent = selection.toString().trim();
    
    if (selectedContent && selectedContent.length > 0) {
      // Store the selected text and range for replacement
      setSelectedText(selectedContent);
      
      // Store selection range for accurate replacement
      if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        // Store range information for replacement
        setSelectedTextRange({
          startContainer: range.startContainer,
          endContainer: range.endContainer,
          startOffset: range.startOffset,
          endOffset: range.endOffset,
          range: range.cloneRange() // Clone to preserve original
        });
      }
    } else {
      // Clear selection if nothing is selected
      setSelectedText('');
      setSelectedTextRange(null);
    }
  }, []);

  // Rewrite selected text function
  const handleRewriteSelectedText = useCallback(async () => {
    if (!selectedText || !selectedTextRange) {
      setRewriteError('Please select some text to rewrite.');
      return;
    }

    try {
      setIsRewriting(true);
      setRewriteError('');
      
      // Get story context for better rewrites
      const storyContext = {
        title: storyData?.story_title || '',
        genre: storyData?.genre || '',
        outline: storyData?.story_outline || '',
        currentChapter: activeChapter,
        chapterContent: content
      };

      // Call rewrite API endpoint
      const response = await fetch(createApiUrl(API_ENDPOINTS.REWRITE_TEXT), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': session?.access_token ? `Bearer ${session.access_token}` : undefined,
        },
        body: JSON.stringify({
          selected_text: selectedText,
          story_context: storyContext
        })
      });

      if (!response.ok) {
        throw new Error(`Rewrite request failed: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && data.rewritten_text) {
        // Replace the selected text with the rewritten version
        replaceSelectedText(data.rewritten_text);
        
        // Clear selection
        setSelectedText('');
        setSelectedTextRange(null);
        
        // Clear any selection in the DOM
        window.getSelection().removeAllRanges();
        
      } else {
        throw new Error(data.error || 'Failed to rewrite text');
      }
      
    } catch (err) {
      console.error('❌ Rewrite failed:', err);
      setRewriteError(err.message || 'Failed to rewrite text. Please try again.');
    } finally {
      setIsRewriting(false);
    }
  }, [selectedText, selectedTextRange, storyData, activeChapter, content, session]);

  // Replace selected text in editor
  const replaceSelectedText = useCallback((newText) => {
    if (!selectedTextRange || !editorRef.current) return;

    try {
      // Create a new range from stored range data
      const range = selectedTextRange.range;
      
      // Verify range is still valid
      if (range && range.startContainer && range.endContainer) {
        // Remove the selected content
        range.deleteContents();
        
        // Create text node with new content
        const textNode = document.createTextNode(newText);
        
        // Insert the new text
        range.insertNode(textNode);
        
        // Update content state
        handleContentChange(editorRef.current.innerHTML);
        
        // Move cursor to end of inserted text
        range.setStartAfter(textNode);
        range.setEndAfter(textNode);
        
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
      }
    } catch (err) {
      console.error('❌ Failed to replace text:', err);
      setRewriteError('Failed to replace text in editor.');
    }
  }, [selectedTextRange, handleContentChange]);

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
    if (!activeChapter || !content || !storyId || !session?.access_token) {
      setError('Cannot save: Missing story data or authentication');
      return;
    }
    
    // Don't save if already saving
    if (saveInProgress) {
      console.log('Save already in progress, skipping...');
      return;
    }

    const chapterData = currentStoryStructure.chapters[activeChapter];
    if (!chapterData) {
      setError('Cannot save: Chapter data not found');
      return;
    }

    try {
      setSaveInProgress(true);
      setError(''); // Clear any previous errors
      
      console.log('💾 Saving chapter to database...', {
        chapterId: chapterData.id,
        contentLength: content.length,
        storyId: storyId
      });

      // Prepare the save request
      const saveData = {
        story_id: parseInt(storyId),
        chapter_id: chapterData.id,
        chapter_number: chapterData.chapterNumber || 1,
        title: chapterData.title || `Chapter ${chapterData.chapterNumber || 1}`,
        content: content, // Current editor content overwrites previous version
        word_count: content.trim().split(/\s+/).length
      };

      // Call the backend save endpoint
      const response = await fetch(createApiUrl(API_ENDPOINTS.SAVE_CHAPTER), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(saveData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Save failed: ${response.status}`);
      }

      const result = await response.json();
      console.log('✅ Chapter saved successfully:', result);

      // 💾 Update local cache immediately after successful save
      const updatedChapter = {
        ...chapterData,
        content: content,
        word_count: saveData.word_count,
        updated_at: new Date().toISOString()
      };

      // Update the chapter in the cached chapters array
      const updatedChapters = chapters.map(chapter => 
        chapter.id === chapterData.id ? updatedChapter : chapter
      );

      // Update cache with the new content
      setStoryCache(storyId, storyData, updatedChapters);
      
      // Update local story structure
      setStoryStructure(prev => ({
        ...prev,
        chapters: {
          ...prev.chapters,
          [activeChapter]: {
            ...prev.chapters[activeChapter],
            content: content,
            wordCount: saveData.word_count
          }
        }
      }));

      // Update chapters state
      setChapters(updatedChapters);

      // Show success feedback
      setChapterGenerationSuccess('Chapter saved successfully!');
      setTimeout(() => setChapterGenerationSuccess(''), 3000); // Clear after 3 seconds

    } catch (err) {
      console.error('❌ Error saving chapter:', err);
      setError(`Failed to save chapter: ${err.message}`);
    } finally {
      setSaveInProgress(false);
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

  // NEW: Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+Enter: Generate AI suggestion
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        handleGenerateAISuggestion();
      }
      
      // Ctrl+Shift+F: Toggle focus mode
      if (e.ctrlKey && e.shiftKey && e.key === 'F') {
        e.preventDefault();
        setIsFocusMode(!isFocusMode);
      }
      
      // Ctrl+Shift+W: Toggle word count
      if (e.ctrlKey && e.shiftKey && e.key === 'W') {
        e.preventDefault();
        setShowWordCount(!showWordCount);
      }
      
      // Escape: Exit focus mode
      if (e.key === 'Escape' && isFocusMode) {
        setIsFocusMode(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isFocusMode, showWordCount]);

  // NEW: Generate AI suggestion
  const handleGenerateAISuggestion = async () => {
    if (!session?.access_token || !content.trim()) {
      setSuggestionError('Please log in and have some content to continue.');
      return;
    }

    setIsGeneratingSuggestion(true);
    setSuggestionError('');
    setAiSuggestion('');

    try {
      const response = await fetch(createApiUrl('/suggest_continue'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          current_content: content,
          story_title: storyData?.story_title || 'Untitled Story',
          story_genre: storyData?.genre || 'Fiction',
          chapter_title: activeChapter
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.suggestion) {
        setAiSuggestion(data.suggestion);
      } else {
        throw new Error(data.error || 'No suggestion received');
      }
    } catch (err) {
      console.error('Error generating suggestion:', err);
      setSuggestionError('Failed to generate suggestion. Please try again.');
    } finally {
      setIsGeneratingSuggestion(false);
    }
  };

  // NEW: Accept AI suggestion
  const handleAcceptSuggestion = () => {
    if (aiSuggestion) {
      const newContent = content + '\n\n' + aiSuggestion;
      const htmlContent = convertTextToHtml(newContent);
      setContent(htmlContent);
      if (editorRef.current) {
        safeUpdateEditorContent(htmlContent);
      }
      setAiSuggestion('');
    }
  };

  // NEW: Reject AI suggestion
  const handleRejectSuggestion = () => {
    setAiSuggestion('');
  };

  // NEW: Focus mode component
  const FocusModeOverlay = () => {
    if (!isFocusMode) return null;

    return (
      <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center">
        <div className="w-full max-w-4xl mx-4">
          <div className="bg-gray-900 rounded-xl p-8 border border-gray-700">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Focus Mode</h2>
              <button
                onClick={() => setIsFocusMode(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Word Count</span>
                <span className="text-white font-mono">{wordCount}</span>
              </div>
              
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min((wordCount / 1000) * 100, 100)}%` }}
                />
              </div>
              
              <div className="text-center text-gray-400 text-sm">
                {wordCount < 1000 ? `${1000 - wordCount} words to go` : 'Great progress!'}
              </div>
            </div>
            
            <div className="mt-8">
              <div
                ref={editorRef}
                contentEditable
                className="w-full h-96 bg-transparent text-white text-lg leading-relaxed focus:outline-none resize-none overflow-y-auto"
                onInput={(e) => setContent(e.target.innerHTML)}
                onSelect={handleTextSelection}
                dangerouslySetInnerHTML={{ __html: content }}
              />
            </div>
            
            {/* AI Suggestion in Focus Mode */}
            {aiSuggestion && (
              <div className="mt-6 p-4 bg-blue-900/20 border border-blue-700 rounded-lg">
                <p className="text-blue-200 text-sm mb-3">{aiSuggestion}</p>
                <div className="flex space-x-2">
                  <button
                    onClick={handleAcceptSuggestion}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors"
                  >
                    Accept
                  </button>
                  <button
                    onClick={handleRejectSuggestion}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}
            
            <div className="mt-6 flex items-center justify-between text-sm text-gray-400">
              <span>Press Ctrl+Enter for AI suggestion</span>
              <span>Press Escape to exit</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-screen bg-gray-900 text-white flex">
      {/* Focus Mode Overlay */}
      <FocusModeOverlay />
      
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
      {(error || generationError) && (
        <div className="fixed top-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          {error || generationError}
          <button
            onClick={() => {
              setError('');
              setGenerationError('');
            }}
            className="ml-2 text-red-200 hover:text-white"
          >
            ×
          </button>
        </div>
      )}

      {/* NEW: AI Suggestion Notification */}
      {aiSuggestion && !isFocusMode && (
        <div className="fixed top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 max-w-md">
          <div className="flex items-start space-x-3">
            <Sparkles className="w-5 h-5 text-blue-200 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm mb-2">{aiSuggestion}</p>
              <div className="flex space-x-2">
                <button
                  onClick={handleAcceptSuggestion}
                  className="px-2 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors"
                >
                  Accept
                </button>
                <button
                  onClick={handleRejectSuggestion}
                  className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
                >
                  Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* NEW: Chapter 1 Generation Success Notification */}
      {chapter1Generated && (
        <div className="fixed top-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          ✅ Chapter 1 generated and saved successfully!
          <button
            onClick={() => setChapter1Generated(false)}
            className="ml-2 text-green-200 hover:text-white"
          >
            ×
          </button>
        </div>
      )}

      {/* NEW: Chapter Generation Success Notification */}
      {chapterGenerationSuccess && (
        <div className="fixed top-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg z-50">
          {chapterGenerationSuccess}
          <button
            onClick={() => setChapterGenerationSuccess('')}
            className="ml-2 text-green-200 hover:text-white"
          >
            ×
          </button>
        </div>
      )}

      {/* Sidebar - Story Structure */}
      <div className={`${isSidebarCollapsed ? 'w-12' : 'w-56'} bg-gray-800 border-r border-gray-700 transition-all duration-300 flex flex-col`}>
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          {!isSidebarCollapsed && (
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                {/* NEW: Back to Stories button */}
                <button
                  onClick={() => navigate('/stories')}
                  className="p-1 hover:bg-gray-700 rounded transition-colors"
                  title="Back to Stories"
                >
                  <ArrowLeft className="w-4 h-4 text-gray-400" />
                </button>
                <div>
                  <h2 className="text-lg font-semibold text-white">{storyTitle}</h2>
                  <p className="text-sm text-gray-400">{storyGenre}</p>
                </div>
              </div>
              {/* NEW: Generation status indicator */}
              {isGeneratingChapter1 && (
                <div className="mt-2 flex items-center space-x-2 text-yellow-400">
                  <div className="w-3 h-3 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-xs">Generating Chapter 1...</span>
                </div>
              )}
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
            {/* Story Cover */}
            {storyData && (
              <React.Suspense fallback={<div className="p-4 text-gray-400">Loading cover...</div>}>
                <StoryCover 
                  storyId={storyData.id} 
                  storyTitle={storyData.story_title || storyData.title || "Untitled Story"} 
                />
              </React.Suspense>
            )}
            
            {/* Outline Option */}
            <div>
              <button
                onClick={() => setActiveChapter('outline')}
                className={`flex items-center w-full text-left text-sm font-medium px-3 py-2 rounded-lg mb-2 ${activeChapter === 'outline' ? 'bg-blue-600 text-white' : 'text-gray-300 hover:text-white hover:bg-gray-700'}`}
              >
                <FileText className="w-4 h-4 mr-2" />
                Outline
              </button>
            </div>
            
            {/* Story Tree Option */}
            <div>
              <button
                onClick={() => setActiveChapter('story-tree')}
                className={`flex items-center w-full text-left text-sm font-medium px-3 py-2 rounded-lg mb-2 ${activeChapter === 'story-tree' ? 'bg-blue-600 text-white' : 'text-gray-300 hover:text-white hover:bg-gray-700'}`}
              >
                <TreePine className="w-4 h-4 mr-2" />
                Story Tree
              </button>
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
                        {/* NEW: Show if chapter is newly generated */}
                        {chapter.isNew && (
                          <span className="text-xs px-1 py-0.5 bg-green-600 text-white rounded">NEW</span>
                        )}
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
                  
                  {/* Start the Journey Button - show when no chapters exist */}
                  {Object.keys(currentStoryStructure.chapters).length === 0 && storyData?.story_outline && (
                    <button
                      onClick={generateChapter1FromOutline}
                      disabled={isGeneratingChapter1 || chapter1GenerationComplete}
                      className={`flex items-center w-full text-sm py-3 px-4 rounded-lg transition-colors ${
                        isGeneratingChapter1 
                          ? 'bg-yellow-600/20 text-yellow-400 cursor-not-allowed' 
                          : chapter1GenerationComplete
                          ? 'bg-green-600/20 text-green-400 cursor-not-allowed'
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                      }`}
                    >
                      {isGeneratingChapter1 ? (
                        <>
                          <div className="w-4 h-4 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin mr-2"></div>
                          Generating Chapter 1...
                        </>
                      ) : chapter1GenerationComplete ? (
                        <>
                          <FileText className="w-4 h-4 mr-2" />
                          Chapter 1 Generated ✓
                        </>
                      ) : (
                        <>
                          <Zap className="w-4 h-4 mr-2" />
                          Start the Journey
                        </>
                      )}
                    </button>
                  )}
                  
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
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Editor Toolbar */}
        <EditorToolbar
          isSidebarCollapsed={isSidebarCollapsed}
          onToggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          onToggleAIPanel={() => setIsAIPanelOpen(!isAIPanelOpen)}
          isAIPanelOpen={isAIPanelOpen}
          onToggleFocusMode={() => setIsFocusMode(!isFocusMode)}
          isFocusMode={isFocusMode}
          onGenerateSuggestion={handleGenerateAISuggestion}
          isGeneratingSuggestion={isGeneratingSuggestion}
          wordCount={wordCount}
          showWordCount={showWordCount}
          onToggleWordCount={() => setShowWordCount(!showWordCount)}
          gameMode={gameMode}
          onToggleGameMode={() => setGameMode(!gameMode)}
        />

        {/* Progress Bar */}
        {showProgressBar && (
          <div className="h-1 bg-gray-700">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
              style={{ width: `${Math.min((wordCount / 1000) * 100, 100)}%` }}
            />
          </div>
        )}

        {/* Editor Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Main Editor */}
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="max-w-5xl mx-auto">
              {/* Story Title */}
              <div className="mb-6">
                <h1 className="text-3xl font-bold text-white mb-2">
                  {storyData?.story_title || 'Untitled Story'}
                </h1>
                <div className="flex items-center space-x-4 text-sm text-gray-400">
                  <span>{storyData?.genre || 'Fiction'}</span>
                  <span>•</span>
                  <span>{wordCount} words</span>
                  <span>•</span>
                  <span>{charCount} characters</span>
                </div>
              </div>

              {/* Editor */}
              <div className="relative">
                <div
                  ref={editorRef}
                  contentEditable
                  className="w-full min-h-[700px] bg-gray-800 border border-gray-700 rounded-lg p-8 text-white text-lg leading-relaxed focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none transition-all duration-200"
                  onInput={(e) => setContent(e.target.innerHTML)}
                  onSelect={handleTextSelection}
                  dangerouslySetInnerHTML={{ __html: content }}
                />
                
                {/* AI Suggestion Overlay */}
                {aiSuggestion && (
                  <div className="absolute bottom-4 right-4 bg-blue-900/90 backdrop-blur-sm border border-blue-700 rounded-lg p-4 max-w-md shadow-xl">
                    <div className="flex items-start space-x-3">
                      <Sparkles className="w-5 h-5 text-blue-200 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-blue-200 text-sm mb-3">{aiSuggestion}</p>
                        <div className="flex space-x-2">
                          <button
                            onClick={handleAcceptSuggestion}
                            className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors"
                          >
                            Accept
                          </button>
                          <button
                            onClick={handleRejectSuggestion}
                            className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Writing Stats */}
              {showWordCount && (
                <div className="mt-6 flex items-center justify-between text-sm text-gray-400">
                  <div className="flex items-center space-x-4">
                    <span>Words: {wordCount}</span>
                    <span>Characters: {charCount}</span>
                    <span>Reading time: {Math.ceil(wordCount / 200)} min</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>Press Ctrl+Enter for AI suggestion</span>
                    <span>•</span>
                    <span>Press Ctrl+Shift+F for focus mode</span>
                  </div>
                </div>
              )}

              {/* Game Mode Choices Section */}
              {gameMode && activeChapter && (
                <div className="mt-8">
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Story Choices</h3>
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                        <span className="text-sm text-purple-400">Game Mode Active</span>
                      </div>
                    </div>

                    {/* Choices Loading State */}
                    {choicesLoading && (
                      <div className="flex items-center justify-center py-8">
                        <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mr-3"></div>
                        <span className="text-gray-400">Loading choices...</span>
                      </div>
                    )}

                    {/* Choices Error State */}
                    {choicesError && (
                      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 mb-4">
                        <p className="text-red-200 text-sm">{choicesError}</p>
                      </div>
                    )}

                    {/* Choices Display */}
                    {!choicesLoading && !choicesError && (() => {
                      const currentChapterData = storyStructure.chapters[activeChapter];
                      if (!currentChapterData) return null;
                      
                      const cachedChoices = getCachedChoices(currentChapterData.id);
                      const choices = cachedChoices.choices || [];
                      
                      if (choices.length === 0) {
                        return (
                          <div className="text-center py-8">
                            <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-3">
                              <span className="text-gray-400 text-xl">?</span>
                            </div>
                            <p className="text-gray-400 text-sm">No choices available for this chapter</p>
                            <p className="text-gray-500 text-xs mt-1">Choices will appear when you reach decision points</p>
                          </div>
                        );
                      }

                      return (
                        <div className="space-y-3">
                          {choices.map((choice, index) => (
                            <button
                              key={choice.id || index}
                              onClick={() => handleChoiceClick(choice.id, choice)}
                              className={`w-full text-left p-4 rounded-lg border transition-all duration-200 hover:scale-[1.02] ${
                                selectedChoiceId === choice.id
                                  ? 'bg-purple-600/20 border-purple-500 text-white'
                                  : 'bg-gray-700 border-gray-600 hover:border-gray-500 text-gray-200'
                              }`}
                            >
                              <div className="flex items-start space-x-3">
                                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                                  selectedChoiceId === choice.id
                                    ? 'border-purple-400 bg-purple-400 text-purple-900'
                                    : 'border-gray-500 text-gray-400'
                                }`}>
                                  {selectedChoiceId === choice.id ? (
                                    <span className="text-xs font-bold">✓</span>
                                  ) : (
                                    <span className="text-xs">{index + 1}</span>
                                  )}
                                </div>
                                <div className="flex-1">
                                  <h4 className="font-medium mb-1">{choice.title}</h4>
                                  <p className="text-sm text-gray-400 leading-relaxed">{choice.description}</p>
                                </div>
                              </div>
                            </button>
                          ))}
                          
                          {/* Continue with Choice Button */}
                          {selectedChoiceId && (
                            <div className="mt-6 pt-4 border-t border-gray-700">
                              <button
                                onClick={handleContinueWithChoice}
                                disabled={generateWithChoiceLoading}
                                className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 ${
                                  generateWithChoiceLoading
                                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                                    : 'bg-purple-600 hover:bg-purple-700 text-white hover:scale-[1.02]'
                                }`}
                              >
                                {generateWithChoiceLoading ? (
                                  <div className="flex items-center justify-center space-x-2">
                                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                    <span>Generating Chapter...</span>
                                  </div>
                                ) : (
                                  <div className="flex items-center justify-center space-x-2">
                                    <span>Continue with Choice</span>
                                    <span className="text-purple-200">→</span>
                                  </div>
                                )}
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* Normal Mode Continue Button */}
              {!gameMode && activeChapter && (
                <div className="mt-8">
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-white">Continue Story</h3>
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span className="text-sm text-blue-400">Normal Mode</span>
                      </div>
                    </div>
                    
                    <p className="text-gray-400 text-sm mb-4">
                      Continue the story in normal mode. The next chapter will be generated automatically.
                    </p>
                    
                    <button
                      onClick={handleContinueStoryNormal}
                      disabled={generateWithChoiceLoading}
                      className={`w-full py-3 px-4 rounded-lg font-medium transition-all duration-200 ${
                        generateWithChoiceLoading
                          ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                          : 'bg-blue-600 hover:bg-blue-700 text-white hover:scale-[1.02]'
                      }`}
                    >
                      {generateWithChoiceLoading ? (
                        <div className="flex items-center justify-center space-x-2">
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          <span>Generating Chapter...</span>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center space-x-2">
                          <span>Continue Story</span>
                          <span className="text-blue-200">→</span>
                        </div>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* AI Assistant Panel */}
          {isAIPanelOpen && (
            <div className="w-72 border-l border-gray-700">
              <AIAssistantPanel
              isOpen={isAIPanelOpen}
              onClose={() => setIsAIPanelOpen(false)}
              selectedText={selectedText}
              onRewriteSelectedText={handleRewriteSelectedText}
              isRewriting={isRewriting}
              rewriteError={rewriteError}
              storyContext={{
                content,
                storyTitle: storyData?.story_title,
                storyGenre: storyData?.genre,
                activeChapter
              }}
              onAcceptSuggestion={handleAcceptSuggestion}
              onRejectSuggestion={handleRejectSuggestion}
              aiSuggestion={aiSuggestion}
              isGeneratingSuggestion={isGeneratingSuggestion}
              suggestionError={suggestionError}
              onGenerateSuggestion={handleGenerateAISuggestion}
            />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StoryEditor;