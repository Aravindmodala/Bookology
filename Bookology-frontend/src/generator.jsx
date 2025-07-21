// generator.jsx - Bookology Frontend Story Generator
//
// This file implements the main UI for generating, viewing, and saving Stories in Bookology.
// It handles user input, calls backend API endpoints to generate outlines/Chapters, and saves Stories by POSTing to /Stories/save.
// Data Flow:
// - User enters a story idea and generates an outline/chapter via backend endpoints.
// - When saving, the story and chapter 1 are sent to the backend, which handles chunking/embedding.
// - Saved Stories and Chapters are fetched from Supabase for display.
//
// Each function is commented with its purpose and where it is used.
//
// (Add or update function-level comments throughout the file)
import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import { useAuth } from './AuthContext';
import StoryChatbot from './StoryChatbot';
import { createApiUrl, API_ENDPOINTS } from './config';

export default function Generator() {
  const { user, session } = useAuth();
  const [idea, setIdea] = useState('');
  const [format, setFormat] = useState('book');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [chapter, setChapter] = useState('');
  const [chapterLoading, setChapterLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('generate'); // 'generate' or 'saved'
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState('');
  const [savedStories, setSavedStories] = useState([]);
  const [fetchingStories, setFetchingStories] = useState(false);
  const [fetchStoriesError, setFetchStoriesError] = useState('');
  const [selectedStory, setSelectedStory] = useState(null); // For modal
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState('');
  const [storyId, setStoryId] = useState(null);
  const [nextChapterLoading, setNextChapterLoading] = useState(false);
  const [nextChapterError, setNextChapterError] = useState('');
  const [currentChapterNumber, setCurrentChapterNumber] = useState(2); // Assuming chapter 1 is already generated
  const [saveChaptersuccess, setSaveChaptersuccess] = useState('');
  const [saveChapterError, setSaveChapterError] = useState('');
  const [allChapters, setAllChapters] = useState([]);
  const [fetchingChapters, setFetchingChapters] = useState(false);
  const [showChatbot, setShowChatbot] = useState(false);
  
  // New state for editable outline feature
  const [outlineJson, setOutlineJson] = useState(null); // Store the JSON data for editing
  const [editableCharacters, setEditableCharacters] = useState([]); // Editable character list
  const [editableLocations, setEditableLocations] = useState([]); // Editable location list
  const [outlineSaved, setOutlineSaved] = useState(false); // Track if outline is saved
  const [saveOutlineLoading, setSaveOutlineLoading] = useState(false); // Loading state for save
  const [saveOutlineError, setSaveOutlineError] = useState(''); // Error state for save

  // New state for branching choices feature
  const [showChoices, setShowChoices] = useState(false); // Show choice selection UI
  const [availableChoices, setAvailableChoices] = useState([]); // Generated choices
  const [choicesLoading, setChoicesLoading] = useState(false); // Loading choices
  const [choicesError, setChoicesError] = useState(''); // Error loading choices
  const [selectedChoiceId, setSelectedChoiceId] = useState(null); // User's selected choice
  const [generateWithChoiceLoading, setGenerateWithChoiceLoading] = useState(false); // Generating next chapter with choice

  // New state for choice history feature
  const [choiceHistory, setChoiceHistory] = useState([]); // Complete choice history for all Chapters
  const [choiceHistoryLoading, setChoiceHistoryLoading] = useState(false); // Loading choice history
  const [choiceHistoryError, setChoiceHistoryError] = useState(''); // Error loading choice history

  // New state for interactive branching feature
  const [showInteractiveTimeline, setShowInteractiveTimeline] = useState(false); // Show interactive chapter timeline
  const [branchingFromChapter, setBranchingFromChapter] = useState(null); // Chapter user wants to branch from
  const [branchingLoading, setBranchingLoading] = useState(false); // Loading state for branching operation

  // New state for draft comparison feature
  const [draftComparison, setDraftComparison] = useState(null); // Holds both original and preview versions
  const [showDraftModal, setShowDraftModal] = useState(false); // Show/hide draft comparison modal
  const [previewLoading, setPreviewLoading] = useState(false); // Loading state for preview generation

  // New state for tree visualization
  const [showTreeVisualization, setShowTreeVisualization] = useState(false); // Show tree visualization modal
  
  // New state for chapter versioning
  const [chapterVersions, setChapterVersions] = useState({}); // Store versions for each chapter {story_id_chapter_number: versions[]}
  const [versionLoading, setVersionLoading] = useState({}); // Loading state for version fetching
  const [activeVersions, setActiveVersions] = useState({}); // Track which version is active for each chapter

  // New state for story outline details
  const [storyGenre, setStoryGenre] = useState(''); // Genre from backend
  const [storyTone, setStoryTone] = useState(''); // Tone from backend
  const [chapterTitles, setChapterTitles] = useState([]); // Chapter titles from backend
  const [storyTitle, setStoryTitle] = useState(''); // Story title (auto-generated or user-edited)

  // Fetch saved Stories and their first chapter from Supabase when switching to 'saved' tab
  useEffect(() => {
    const fetchStories = async () => {
      if (activeTab === 'saved' && user) {
        setFetchingStories(true);
        setFetchStoriesError('');
        // Fetch Stories for this user
        const { data: Stories, error: StoriesError } = await supabase
          .from('Stories')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });
        if (StoriesError) {
          setFetchStoriesError(StoriesError.message);
          setFetchingStories(false);
          return;
        }
        // For each story, fetch its first chapter
        const storyIds = Stories.map(s => s.id);
        let Chapters = [];
        if (storyIds.length > 0) {
          const { data: ChaptersData, error: ChaptersError } = await supabase
            .from('Chapters')
            .select('*')
            .in('story_id', storyIds)
            .eq('chapter_number', 1);
          if (ChaptersError) {
            setFetchStoriesError(ChaptersError.message);
            setFetchingStories(false);
            return;
          }
          Chapters = ChaptersData;
        }
        // Merge Stories and their first chapter
        const merged = Stories.map(story => {
          const chapter1 = Chapters.find(c => c.story_id === story.id && c.chapter_number === 1);
          return {
            ...story,
            chapter_1_content: chapter1 ? chapter1.content : '',
            chapter_1_id: chapter1 ? chapter1.id : null,
            chapter_1_created_at: chapter1 ? chapter1.created_at : null,
          };
        });
        setSavedStories(merged);
        setFetchingStories(false);
      }
    };
    fetchStories();
  }, [activeTab, user]);

  // Fetch all Chapters for the selected story when modal opens
  useEffect(() => {
    const fetchChapters = async () => {
      if (selectedStory) {
        console.log('📖 Fetching chapters for story:', selectedStory.story_title);
        setFetchingChapters(true);
        
        try {
          // Only fetch active chapters (is_active = true)
          const { data: Chapters, error } = await supabase
            .from('Chapters')
            .select('*')
            .eq('story_id', selectedStory.id)
            .eq('is_active', true)  // Only get active versions
            .order('chapter_number', { ascending: true });
          
          if (error) {
            console.error('❌ Chapter fetch error:', error);
            setAllChapters([]);
                  } else {
          console.log('✅ Found', Chapters?.length || 0, 'active chapters');
          setAllChapters(Chapters || []);
          
          // Fetch versions for each chapter
          for (const chapter of Chapters || []) {
            await fetchChapterVersions(selectedStory.id, chapter.chapter_number);
          }
          
          // Fetch choice history using the freshly fetched chapters (not state)
          if ((Chapters || []).length > 0) {
            console.log('📋 Fetching choice history for', Chapters.length, 'chapters...');
            await fetchChoiceHistoryWithChapters(selectedStory.id, Chapters);
          }
        }
      } catch (fetchError) {
        console.error('❌ CHAPTER FETCH - Exception:', fetchError);
        setAllChapters([]);
      }
      
      setFetchingChapters(false);
    }
  };
  fetchChapters();
  }, [selectedStory]);

  // Reset state when switching Stories or Chapters
  useEffect(() => {
    if (selectedStory) {
      // CRITICAL: Reset ALL story-specific state when switching Stories
      setSaveChaptersuccess('');
      setSaveChapterError('');
      // Don't set currentChapterNumber here - wait for Chapters to load
      
      // NEW: Complete state isolation for story switching
      setAvailableChoices([]); // Clear choices from previous story
      setShowChoices(false);   // Hide choice UI
      setSelectedChoiceId(null); // Clear selected choice
      setChoicesError('');     // Clear choice errors
      setChoiceHistory([]);    // Clear choice history from previous story
      setChoiceHistoryError(''); // Clear choice history errors
      
      // Clear any chapter generation state
      setNextChapterLoading(false);
      setNextChapterError('');
      setChoicesLoading(false);
      setGenerateWithChoiceLoading(false);
      
      // Clear chatbot state if needed
      setShowChatbot(false);
      
      // Clear draft comparison state
      setDraftComparison(null);
      setShowDraftModal(false);
      setPreviewLoading(false);
      
      console.log('🧹 State reset for story switch:', selectedStory.id, selectedStory.story_title);
    }
  }, [selectedStory]); // Remove allChapters dependency to prevent loops

  // Separate effect for chapter count updates to avoid interfering with story switching
  useEffect(() => {
    if (selectedStory && allChapters.length > 0) {
      setCurrentChapterNumber(allChapters.length + 1);
    }
  }, [allChapters, selectedStory]);

  // After saving a chapter, refresh the chapter list
  useEffect(() => {
    if (selectedStory && saveChaptersuccess) {
      // Re-fetch active Chapters after a successful save
      (async () => {
        const { data: Chapters, error } = await supabase
          .from('Chapters')
          .select('*')
          .eq('story_id', selectedStory.id)
          .eq('is_active', true)  // Only get active versions
          .order('chapter_number', { ascending: true });
        if (!error) setAllChapters(Chapters || []);
      })();
    }
  }, [saveChaptersuccess, selectedStory]);

  // Fetch chapter versions when chapters are loaded
  useEffect(() => {
    if (selectedStory && allChapters.length > 0) {
      // Fetch versions for each chapter that doesn't have versions loaded yet
      allChapters.forEach(chapter => {
        const key = `${selectedStory.id}_${chapter.chapter_number}`;
        if (!chapterVersions[key] && !versionLoading[key]) {
          fetchChapterVersions(selectedStory.id, chapter.chapter_number);
        }
      });
    }
  }, [selectedStory, allChapters]);

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setResult('');
    setChapter('');
    setSaveSuccess('');
    setSaveError('');
    // Reset outline editing state
    setOutlineJson(null);
    setEditableCharacters([]);
    setEditableLocations([]);
    setOutlineSaved(false);
    setSaveOutlineError('');
    setAllChapters([]);
    setAvailableChoices([]);
    setShowChoices(false);
    setSelectedChoiceId(null);
    setChoicesError('');
    setChoiceHistory([]);
    setChoiceHistoryError('');
    setCurrentChapterNumber(1);
    setStoryId(null);
    // Reset new state variables
    setStoryGenre('');
    setStoryTone('');
    setChapterTitles([]);
    setStoryTitle('');

    const token = session?.access_token;

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_OUTLINE), {
        method: 'POST',
        headers,
        body: JSON.stringify({
          idea,
          story_id: storyId
        })
      });
      const data = await response.json();

      // Updated: match backend response
      if (data.summary) {
        setResult(data.summary); // Show the summary in the UI
        
        // Use backend-generated title or fall back to auto-generation
        if (data.title) {
          setStoryTitle(data.title);
        } else {
          // Fallback: auto-generate title from the first sentence of the summary
          const firstSentence = data.summary.split('.')[0];
          const autoTitle = firstSentence.length > 50 ? firstSentence.substring(0, 50) + '...' : firstSentence;
          setStoryTitle(autoTitle);
        }
        
        // Extract and set genre and chapter titles
        if (data.genre) {
          setStoryGenre(data.genre);
        }
        if (data.tone) {
          setStoryTone(data.tone);
        }
        if (data.chapters && Array.isArray(data.chapters)) {
          // Extract just the titles from the chapters array
          const titles = data.chapters.map(chapter => chapter.title || chapter.chapter_title || `Chapter ${chapter.chapter_number}`);
          setChapterTitles(titles);
        }
        setSaveSuccess('✨ Outline generated! You can edit character/location names and then save.');
      } else if (data.error) {
        setError(data.error);
      } else {
        setError('Unexpected response from backend');
      }
    } catch (err) {
      setError('Error connecting to backend');
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async () => {
    // Check if outline is saved first
    if (!outlineSaved) {
      setError('Please save your outline first before generating Chapter 1.');
      return;
    }

    setChapterLoading(true);
    setError('');
    setSaveSuccess('');
    setSaveError('');
    
    // CRITICAL: Complete state reset to prevent cross-story data contamination during chapter 1 generation
    setAllChapters([]);
    setAvailableChoices([]);
    setShowChoices(false);
    setSelectedChoiceId(null);
    setChoicesError('');
    setChoiceHistory([]);
    setChoiceHistoryError('');
    setCurrentChapterNumber(1);
    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER), {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.access_token}`
        },
        body: JSON.stringify({ 
          outline: result,
          story_id: storyId  // Pass the story_id that was set when saving the outline
        })
      });
      const data = await response.json();
      if (data.chapter_1) {
        setChapter(data.chapter_1);
        
                  // Use automatic choices from the response instead of generating separately
        if (data.choices && data.choices.length > 0) {
          console.log('✅ Automatic choices received:', data.choices.length);
          // Normalize choice data structure - ensure all choices have both id and choice_id
          const normalizedChoices = data.choices.map(choice => ({
            ...choice,
            id: choice.id || choice.choice_id,
            choice_id: choice.choice_id || choice.id
          }));
          setAvailableChoices(normalizedChoices);
          setShowChoices(true);
          setSelectedChoiceId(null);
          setChoicesError('');
        } else {
          console.log('⚠️ No choices in response, trying old endpoint...');
          // Fallback to old method if no choices in response
          setTimeout(() => {
            handleGenerateChoices(data.chapter_1, 1);
          }, 1500);
        }
        
      } else if (data.error) {
        setError(data.error);
      } else {
        setError('Unexpected response from backend');
      }
    } catch (err) {
      setError('Error connecting to backend');
    } finally {
      setChapterLoading(false);
    }
  };

  const handleDislike = () => {
    handleGenerate();
  };

  // New function to handle saving the edited outline
  const handleSaveOutline = async () => {
    if (!user || !session?.access_token) {
      setSaveOutlineError('Please log in to save your outline.');
      return;
    }

    // Check if we have the new format data from the backend
    if (!result) {
      setSaveOutlineError('No outline data to save.');
      return;
    }

    setSaveOutlineLoading(true);
    setSaveOutlineError('');

    try {
      // Use the new format from the enhanced outline generator
      const response = await fetch(createApiUrl(API_ENDPOINTS.SAVE_OUTLINE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          summary: result,  // The story summary
          genre: storyGenre,  // The detected genre
          tone: storyTone,  // The detected tone
          title: storyTitle,  // The user-edited title
          chapters: chapterTitles.map((title, index) => ({
            chapter_number: index + 1,
            title: title
          })),  // Convert titles to chapter objects
          reflection: '',  // We don't have reflection in frontend state yet
          is_optimized: true  // Assume optimized since it's from enhanced generator
        })
      });

      const data = await response.json();

      if (data.success) {
        setOutlineSaved(true);
        setStoryId(data.story_id); // Store story ID for chapter generation
        setSaveSuccess(`✅ Outline saved as "${data.story_title}"! Now you can generate Chapter 1.`);
        setSaveError(''); // Clear any previous errors

        // Don't try to fetch Chapter 1 - it doesn't exist yet
        // The user needs to click "Generate Chapter 1" to create it
      } else {
        setSaveOutlineError(data.detail || 'Failed to save outline');
      }
    } catch (err) {
      setSaveOutlineError('Error connecting to server');
    } finally {
      setSaveOutlineLoading(false);
    }
  };

  // Functions to handle editing characters and locations
  const updateCharacterName = (index, newName) => {
    setEditableCharacters(prev => 
      prev.map((char, i) => 
        i === index ? { ...char, name: newName } : char
      )
    );
  };

  const updateLocationName = (index, newName) => {
    setEditableLocations(prev => 
      prev.map((loc, i) => 
        i === index ? { ...loc, name: newName } : loc
      )
    );
  };

  // Function to render the outline with inline editable character names
  const renderEditableOutline = () => {
    if (!result || !editableCharacters.length) {
      // If no characters to edit, just show the original outline
      return <div className="whitespace-pre-wrap">{result}</div>;
    }

    // Split the outline by lines to process each one
    const lines = result.split('\n');
    
    return (
      <div className="space-y-2">
        {lines.map((line, lineIndex) => {
          // Check if this line contains character information (starts with "• **")
          if (line.includes('• **') && line.includes('**')) {
            // Extract character name from the line (between ** markers)
            const match = line.match(/• \*\*(.+?)\*\* - (.+)/);
            if (match) {
              const [, originalName, description] = match;
              
              // Find the character in our editable list
              const charIndex = editableCharacters.findIndex(char => 
                char.name === originalName || char.name === originalName.trim()
              );
              
              if (charIndex >= 0) {
                const character = editableCharacters[charIndex];
                return (
                  <div key={lineIndex} className="flex items-center">
                    <span className="text-gray-200">• </span>
                    <input
                      type="text"
                      value={character.name || originalName}
                      onChange={(e) => updateCharacterName(charIndex, e.target.value)}
                      className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white font-bold focus:outline-none focus:ring-2 focus:ring-blue-500 mx-1"
                      style={{ width: `${Math.max(character.name?.length || 8, 8)}ch` }}
                    />
                    <span className="text-gray-200"> - {description}</span>
                  </div>
                );
              }
            }
          }
          
          // For all other lines, render as-is
          return (
            <div key={lineIndex} className="text-gray-200">
              {line || '\u00A0'} {/* Non-breaking space for empty lines */}
            </div>
          );
        })}
      </div>
    );
  };

  // Function to generate choices after a chapter is completed
  const handleGenerateChoices = async (chapterContent, chapterNumber) => {
    console.log('🎯 handleGenerateChoices called with:', {
      chapterContentLength: chapterContent?.length,
      chapterNumber,
      storyId: storyId || selectedStory?.id,
      hasUser: !!user,
      hasToken: !!session?.access_token
    });

    const currentStoryId = storyId || selectedStory?.id;
    
    if (!user || !session?.access_token || !currentStoryId) {
      const errorMsg = 'Please log in and save your story first.';
      setChoicesError(errorMsg);
      console.error('❌', errorMsg, { user: !!user, token: !!session?.access_token, storyId: currentStoryId });
      return;
    }

    // CRITICAL: Verify we're operating on the correct story
    console.log('🔍 STORY ISOLATION CHECK - Generating choices for story:', currentStoryId);
    if (selectedStory && selectedStory.id !== currentStoryId) {
      const errorMsg = `Story ID mismatch: selected=${selectedStory.id}, target=${currentStoryId}`;
      setChoicesError(errorMsg);
      console.error('❌ STORY ISOLATION VIOLATION:', errorMsg);
      return;
    }

    setChoicesLoading(true);
    setChoicesError('');
    setShowChoices(false);

    try {
      console.log('🚀 Making request to generate choices...');
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHOICES), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          story_id: currentStoryId,
          current_chapter_content: chapterContent,
          current_chapter_num: chapterNumber
        })
      });

      console.log('📡 Response status:', response.status);
      const data = await response.json();
      console.log('📦 Response data:', data);

      if (data.success && data.choices) {
        console.log('✅ Choices generated successfully:', data.choices.length);
        
        // CRITICAL: Verify response is for the correct story
        if (data.story_id && data.story_id !== currentStoryId) {
          const errorMsg = `Response story ID mismatch: expected=${currentStoryId}, received=${data.story_id}`;
          console.error('❌ BACKEND STORY ISOLATION VIOLATION:', errorMsg);
          setChoicesError('Server returned data for wrong story. Please refresh.');
          return;
        }
        
        // Normalize choice data structure
        const normalizedChoices = data.choices.map(choice => ({
          ...choice,
          id: choice.id || choice.choice_id,
          choice_id: choice.choice_id || choice.id,
          story_id: currentStoryId // Ensure story_id is set
        }));
        setAvailableChoices(normalizedChoices);
        setShowChoices(true);
        setSelectedChoiceId(null);
      } else {
        const errorMsg = data.detail || 'Failed to generate choices';
        console.error('❌ Failed to generate choices:', errorMsg);
        setChoicesError(errorMsg);
      }
    } catch (err) {
      console.error('❌ Error in handleGenerateChoices:', err);
      setChoicesError('Error connecting to server');
    } finally {
      setChoicesLoading(false);
    }
  };

  // Function to handle user choice selection and generate next chapter
  const handleChoiceSelection = async (choiceId) => {
    if (!user || !session?.access_token || !storyId) {
      setChoicesError('Please log in first.');
      return;
    }

    // CRITICAL: Story isolation validation
    console.log('🔍 CHOICE SELECTION - Story isolation check:', { storyId, selectedStory: selectedStory?.id });
    
    const selectedChoice = availableChoices.find(choice => choice.id === choiceId);
    if (!selectedChoice) {
      console.error('❌ CHOICE NOT FOUND:', { choiceId, availableChoices });
      setChoicesError('Invalid choice selected.');
      return;
    }

    // CRITICAL: Verify choice belongs to current story
    if (selectedChoice.story_id && selectedChoice.story_id !== storyId) {
      const errorMsg = `Choice belongs to wrong story: choice=${selectedChoice.story_id}, current=${storyId}`;
      console.error('❌ CHOICE STORY ISOLATION VIOLATION:', errorMsg);
      setChoicesError('Selected choice belongs to different story. Please refresh.');
      return;
    }

    setGenerateWithChoiceLoading(true);
    setChoicesError('');

    try {
      // Determine next chapter number (current + 1)
      const nextChapterNum = Math.max(2, (chapter ? 2 : 1)); // Simple logic for now

      console.log('🚀 CHOICE SELECTION - Generating chapter for story:', storyId, 'choice:', choiceId);
      
      // Log complete choice data
      console.log('📊 NEW STORY CHOICE DATA BEING SENT:', {
        choiceId,
        selectedChoice,
        choiceIdType: typeof choiceId,
        selectedChoiceId: selectedChoice.id,
        selectedChoiceIdType: typeof selectedChoice.id,
        nextChapterNum
      });

      const requestBody = {
        story_id: storyId,
        choice_id: choiceId,
        choice_data: selectedChoice,
        next_chapter_num: nextChapterNum,
        token: session.access_token
      };

      console.log('📨 NEW STORY COMPLETE REQUEST BODY:', requestBody);

      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER_WITH_CHOICE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (data.success) {
        // CRITICAL: Verify response is for correct story
        if (data.story_id && data.story_id !== storyId) {
          const errorMsg = `Response story ID mismatch: expected=${storyId}, received=${data.story_id}`;
          console.error('❌ BACKEND STORY ISOLATION VIOLATION:', errorMsg);
          setChoicesError('Server returned data for wrong story. Please refresh.');
          return;
        }

        // Add the new chapter to the display
        setChapter(prev => prev + '\n\n' + '='.repeat(50) + '\n\n' + 
                  `**Chapter ${data.chapter_number}**\n\n${data.chapter_content}`);
        
        // Hide choices and show success message
        setShowChoices(false);
        setSaveSuccess(`✅ Chapter ${data.chapter_number} generated based on your choice: "${selectedChoice.title}"!`);
        
        // Use automatic choices if available, otherwise use old method
        if (data.choices && data.choices.length > 0) {
          console.log('✅ New automatic choices received for Chapter', data.chapter_number + 1, ':', data.choices.length);
          setTimeout(() => {
            // Normalize choice data structure with story isolation
            const normalizedChoices = data.choices.map(choice => ({
              ...choice,
              id: choice.id || choice.choice_id,
              choice_id: choice.choice_id || choice.id,
              story_id: storyId // Ensure story_id is set correctly
            }));
            setAvailableChoices(normalizedChoices);
            setShowChoices(true);
            setSelectedChoiceId(null);
            setChoicesError('');
            // Fetch updated choice history after generating the chapter
            fetchChoiceHistory(storyId);
          }, 2000);
        } else {
          // Fallback to old method if no choices in response
          setTimeout(() => {
            handleGenerateChoices(data.chapter_content, data.chapter_number);
            // Fetch updated choice history after generating the chapter
            fetchChoiceHistory(storyId);
          }, 2000);
        }
        
      } else {
        const errorMessage = typeof data.detail === 'string' ? data.detail : 
                           Array.isArray(data.detail) ? data.detail.map(e => e.msg || e).join(', ') :
                           'Failed to generate chapter with choice';
        console.error('❌ Backend error response:', data);
        setChoicesError(errorMessage);
      }
    } catch (err) {
      console.error('❌ Network/parsing error:', err);
      setChoicesError('Error connecting to server');
    } finally {
      setGenerateWithChoiceLoading(false);
    }
  };

  // Save story to Supabase (Stories + Chapters)
  const handleSaveStory = async () => {
    setSaveLoading(true);
    setSaveError('');
    setSaveSuccess('');
    if (!user) {
      setSaveError('You must be logged in to save Stories.');
      setSaveLoading(false);
      return;
    }

    // CRITICAL DEBUG: Log what choices we have before saving
    console.log('💾 SAVE STORY - Choices to save:', {
      availableChoicesCount: availableChoices?.length || 0,
      choices: availableChoices?.map(c => ({ id: c.id, title: c.title })) || 'None'
    });

    // Get the user's JWT token from AuthContext
    const token = session?.access_token;

    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.SAVE_STORY), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          story_outline: result,      // The outline text
          chapter_1_content: chapter, // The generated chapter 1 text
          story_title: idea,          // The story title
          // CRITICAL FIX: Include the generated choices
          chapter_1_choices: availableChoices || [], // Send the choices that were generated
          // Include outline JSON if available (from saved outline)
          outline_json: outlineJson,  // The JSON outline data if available
        }),
      });
      const data = await response.json();
      if (response.ok) {
        // Enhanced success message with choice information
        let successMsg = 'Story saved successfully!';
        if (data.choices_saved && data.choices_saved > 0) {
          successMsg += ` ${data.choices_saved} choices saved.`;
        }
        setSaveSuccess(successMsg);
        setStoryId(data.story_id);
        
        // Fetch choice history for the newly saved story if it has choices
        if (data.story_id) {
          setTimeout(() => {
            fetchChoiceHistory(data.story_id);
          }, 1000); // Give the backend time to save choices
        }
      } else {
        setSaveError(data.detail || 'Error saving story.');
      }
    } catch (err) {
      setSaveError('Error connecting to backend.');
    } finally {
      setSaveLoading(false);
    }
  };

  // Delete story using backend endpoint (handles cascade deletion properly)
  const handleDeleteStory = async (storyId) => {
    if (!session?.access_token) {
      setDeleteError('Please log in to delete stories.');
      return;
    }

    setDeleteLoading(true);
    setDeleteError('');
    
    try {
      const response = await fetch(createApiUrl(`/story/${storyId}`), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setSelectedStory(null);
        // Refresh Stories list
        setSavedStories((prev) => prev.filter((s) => s.id !== storyId));
        console.log('✅ Story deleted successfully:', data.message);
      } else {
        setDeleteError(data.detail || 'Failed to delete story');
      }
    } catch (error) {
      console.error('❌ Delete story error:', error);
      setDeleteError('Error connecting to server');
    } finally {
      setDeleteLoading(false);
    }
  };

  // Function to generate the next chapter for a saved story
  const handleContinueStory = async (story) => {
    setChapterLoading(true);
    setError('');
    setSaveSuccess('');
    setSaveError('');
    try {
      // Call backend to generate the next chapter using the story's outline
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          outline: story.story_outline, // Send the outline for context
          // Optionally, send previous Chapters for more context
        }),
      });
      const data = await response.json();
      if (data.chapter_1) {
        // For now, show the generated chapter in an alert
        alert('Next chapter generated:\n\n' + data.chapter_1);
        // TODO: Add UI to edit/save as Chapter 2
      } else if (data.error) {
        setError(data.error);
      } else {
        setError('Unexpected response from backend');
      }
    } catch (err) {
      setError('Error connecting to backend');
    } finally {
      setChapterLoading(false);
    }
  };

  // Modal close handler
  const closeModal = () => {
    setSelectedStory(null);
    setShowChatbot(false);
    
    // CRITICAL: Complete state cleanup when closing modal
    setAvailableChoices([]);
    setShowChoices(false);
    setSelectedChoiceId(null);
    setChoicesError('');
    setChoiceHistory([]);
    setChoiceHistoryError('');
    // DON'T clear allChapters when closing modal - only when switching Stories
    // setAllChapters([]);  // REMOVED
    setNextChapterLoading(false);
    setNextChapterError('');
    setSaveChaptersuccess('');
    setSaveChapterError('');
    setChoicesLoading(false);
    setGenerateWithChoiceLoading(false);
    
    console.log('🧹 Complete state cleanup on modal close');
  };

  // CRITICAL: Safe story selection with complete state isolation
  const handleStorySelection = (story) => {
    console.log('🔄 STORY SWITCH - Selecting story:', story.id, story.story_title);
    
    // First, completely clear all state EXCEPT allChapters (which will be set by fetchChapters)
    setAvailableChoices([]);
    setShowChoices(false);
    setSelectedChoiceId(null);
    setChoicesError('');
    setChoiceHistory([]);
    setChoiceHistoryError('');
    // DON'T clear allChapters here - let fetchChapters handle it
    // setAllChapters([]); // REMOVED
    setNextChapterLoading(false);
    setNextChapterError('');
    setSaveChaptersuccess('');
    setSaveChapterError('');
    setChoicesLoading(false);
    setGenerateWithChoiceLoading(false);
    setShowChatbot(false);
    
    // Then set the new story - this will trigger fetchChapters
    setSelectedStory(story);
    
    console.log('✅ STORY SWITCH - State cleared, story selected:', story.id);
  };

  // Helper to count Chapters in outline
  function getTotalChaptersFromOutline(outline) {
    if (!outline) return 0;
    const matches = outline.match(/Chapter\s+\d+/g);
    return matches ? matches.length : 0;
  }

  const totalChapters = selectedStory ? getTotalChaptersFromOutline(selectedStory.story_outline) : 0;

  // Handler for "Generate Choices" for saved Stories  
  const handleGenerateChoicesForSavedStory = async () => {
    console.log('🎯 Generate choices clicked for saved story:', selectedStory?.story_title);
    console.log('📚 Available Chapters:', allChapters.length);
    console.log('🔢 Current chapter number:', currentChapterNumber);
    
    if (!selectedStory || !session?.access_token) {
      setNextChapterError('Please log in and select a story.');
      console.error('❌ No story selected or not logged in');
      return;
    }

    // Get the last chapter content for choice generation
    const lastChapter = allChapters[allChapters.length - 1];
    console.log('📖 Last chapter:', lastChapter ? 'Found' : 'Not found');
    
    if (!lastChapter) {
      setNextChapterError('No Chapters found to generate choices from.');
      console.error('❌ No Chapters available');
      return;
    }

    console.log('🚀 Calling handleGenerateChoices with:', {
      content: lastChapter.content?.substring(0, 100) + '...',
      chapterNum: currentChapterNumber - 1
    });

    await handleGenerateChoices(lastChapter.content, currentChapterNumber - 1);
  };

  // Handler for choice selection in saved Stories
  const handleChoiceSelectionForSavedStory = async (choiceId) => {
    if (!selectedStory || !session?.access_token) {
      setChoicesError('Please log in and select a story.');
      return;
    }

    // CRITICAL: Story isolation validation for saved Stories
    console.log('🔍 SAVED STORY CHOICE SELECTION - Story isolation check:', { 
      selectedStoryId: selectedStory.id, 
      choiceId,
      availableChoicesCount: availableChoices.length,
      choiceHistoryCount: choiceHistory.length
    });

    // Find the choice in the current chapter's choice history (not availableChoices)
    let selectedChoice = null;
    let currentChapterChoices = null;
    
    // Find the current chapter (last chapter)
    if (allChapters && allChapters.length > 0) {
      const currentChapter = allChapters[allChapters.length - 1];
      currentChapterChoices = choiceHistory.find(ch => ch.chapter_number === currentChapter.chapter_number);
      if (currentChapterChoices && currentChapterChoices.choices) {
        selectedChoice = currentChapterChoices.choices.find(choice => choice.id === choiceId);
      }
    }
    
    console.log('🔍 CHOICE SEARCH RESULT:', {
      currentChapterChoices: currentChapterChoices?.choices?.length || 0,
      selectedChoice: selectedChoice ? 'FOUND' : 'NOT FOUND',
      searchChoiceId: choiceId,
      availableChoiceIds: currentChapterChoices?.choices?.map(c => c.id) || []
    });

    if (!selectedChoice) {
      console.error('❌ CHOICE NOT FOUND in choice history:', { 
        choiceId, 
        choiceHistory: choiceHistory.map(ch => ({ 
          chapter: ch.chapter_number, 
          choices: ch.choices?.map(c => ({ id: c.id, title: c.title })) || [] 
        }))
      });
      setChoicesError('Invalid choice selected.');
      return;
    }

    // CRITICAL: Verify choice belongs to current story
    if (selectedChoice.story_id && selectedChoice.story_id !== selectedStory.id) {
      const errorMsg = `Choice belongs to wrong story: choice=${selectedChoice.story_id}, current=${selectedStory.id}`;
      console.error('❌ SAVED STORY CHOICE ISOLATION VIOLATION:', errorMsg);
      setChoicesError('Selected choice belongs to different story. Please refresh.');
      return;
    }

    setGenerateWithChoiceLoading(true);
    setChoicesError('');

    try {
      console.log('🎯 Generating chapter with choice:', selectedChoice.title);
      
      // Calculate the correct next chapter number for saved Stories
      const nextChapterNumber = (allChapters?.length || 0) + 1;
      
      const requestBody = {
        story_id: selectedStory.id,
        choice_id: choiceId,
        choice_data: selectedChoice,
        next_chapter_num: nextChapterNumber,
        token: session.access_token
      };

      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER_WITH_CHOICE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(requestBody)
      });

      console.log('📡 Response status:', response.status);
      const data = await response.json();
      console.log('📦 Response data:', data);

      if (data.success) {
        // CRITICAL: Verify response is for correct story
        if (data.story_id && data.story_id !== selectedStory.id) {
          const errorMsg = `Response story ID mismatch: expected=${selectedStory.id}, received=${data.story_id}`;
          console.error('❌ BACKEND STORY ISOLATION VIOLATION:', errorMsg);
          setChoicesError('Server returned data for wrong story. Please refresh.');
          return;
        }

        // Chapter content is automatically saved to database, no need to show preview

        // Fetch the updated chapters list and update state (only active versions)
        const { data: Chapters, error } = await supabase
          .from('Chapters')
          .select('*')
          .eq('story_id', selectedStory.id)
          .eq('is_active', true)  // Only get active versions
          .order('chapter_number', { ascending: true });
        if (!error) setAllChapters(Chapters || []);

        // Hide choices and show success message
        setShowChoices(false);
        setSaveChaptersuccess(`✅ Chapter ${data.chapter_number} generated based on your choice: "${selectedChoice.title}"!`);
        
        // Check if new choices were returned for the next chapter
        if (data.choices && data.choices.length > 0) {
          console.log('✅ New automatic choices received for next chapter:', data.choices.length);
          setTimeout(() => {
            // Normalize choice data structure with story isolation
            const normalizedChoices = data.choices.map(choice => ({
              ...choice,
              id: choice.id || choice.choice_id,
              choice_id: choice.choice_id || choice.id,
              story_id: selectedStory.id // Ensure story_id is set correctly
            }));
            setAvailableChoices(normalizedChoices);
            setShowChoices(true);
            setSelectedChoiceId(null);
            setChoicesError('');
            // Fetch updated choice history after generating the chapter
            fetchChoiceHistory(selectedStory.id);
          }, 2000); // Show choices after 2 seconds
        } else {
          // Even if no new choices, fetch choice history to show completed choices
          setTimeout(() => {
            fetchChoiceHistory(selectedStory.id);
          }, 2000);
        }
        
      } else {
        const errorMessage = typeof data.detail === 'string' ? data.detail : 
                           Array.isArray(data.detail) ? data.detail.map(e => e.msg || e).join(', ') :
                           'Failed to generate chapter with choice';
        console.error('❌ Backend error response:', data);
        setChoicesError(errorMessage);
      }
    } catch (err) {
      setChoicesError('Error connecting to server');
    } finally {
      setGenerateWithChoiceLoading(false);
    }
  };

  // Generate and automatically save chapter to database
  const handleGenerateNextChapter = async () => {
    setNextChapterLoading(true);
    setNextChapterError('');
    
    // Get the user's JWT token from AuthContext
    const token = session?.access_token;
    
    try {
      const headers = { 'Content-Type': 'application/json' };
      
      // Add auth header for authenticated request
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      } else {
        setNextChapterError('You must be logged in to generate Chapters.');
        setNextChapterLoading(false);
        return;
      }
      
      console.log('🚀 Generating and saving Chapter', currentChapterNumber, 'for story', selectedStory.id);
      
      // Use the generate_and_save_chapter endpoint that both generates AND saves
      const response = await fetch(createApiUrl('/generate_and_save_chapter'), {
        method: 'POST',
        headers,
        body: JSON.stringify({
          story_id: selectedStory.id,
          chapter_number: currentChapterNumber,
          story_outline: selectedStory.story_outline,
        }),
      });
      const data = await response.json();
      if (response.ok) {
        console.log('✅ Chapter generated and saved successfully!');
        
        // Chapter is now saved automatically
        
        // Refresh the Chapters list to show the new chapter (only active versions)
        const { data: Chapters, error } = await supabase
          .from('Chapters')
          .select('*')
          .eq('story_id', selectedStory.id)
          .eq('is_active', true)  // Only get active versions
          .order('chapter_number', { ascending: true });
        
        if (!error) {
          console.log('✅ Refreshed active Chapters list, found', Chapters?.length || 0, 'Chapters');
          setAllChapters(Chapters || []);
          setCurrentChapterNumber(prev => prev + 1);
          
          // Auto-generate choices for the new chapter if it's Chapter 1
          if (currentChapterNumber === 1 && Chapters?.length > 0) {
            const newChapter = Chapters.find(ch => ch.chapter_number === currentChapterNumber);
            if (newChapter) {
              console.log('🎯 Auto-generating choices for Chapter 1...');
              setTimeout(() => {
                handleGenerateChoices(newChapter.content, currentChapterNumber);
              }, 2000);
            }
          }
        }
        
        // Show success message
        setSaveChaptersuccess(`✅ Chapter ${currentChapterNumber} generated and saved!`);
        setTimeout(() => setSaveChaptersuccess(''), 3000);
        
      } else {
        setNextChapterError(data.detail || 'Error generating next chapter.');
      }
    } catch (err) {
      setNextChapterError('Error connecting to backend.');
    } finally {
      setNextChapterLoading(false);
    }
  };

  // Handler for saving a generated chapter (not chapter 1) - REMOVED
  // Chapters are now automatically saved when generated with choices

  // Function to fetch choice history for a story
  const fetchChoiceHistory = async (storyId) => {
    console.log('📋 CHOICE HISTORY - Fetching for story:', storyId);
    setChoiceHistoryLoading(true);
    setChoiceHistoryError('');
    
    if (!storyId || !session?.access_token) {
      setChoiceHistoryError('Story ID or authentication required');
      setChoiceHistoryLoading(false);
      return;
    }
    
    // CRITICAL: Reset choice selection state when fetching new history
    setSelectedChoiceId(null);
    console.log('🔄 CHOICE SELECTION RESET for history fetch');
    
    try {
      // NEW APPROACH: Fetch choices for each active chapter using chapter_id
      const choiceHistoryForActiveChapters = [];
      
      for (const chapter of allChapters) {
        if (chapter.is_active !== false) { // Only fetch for active chapters
          const choicesResponse = await fetch(createApiUrl(API_ENDPOINTS.GET_CHAPTER_CHOICES.replace('{chapter_id}', chapter.id)), {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${session.access_token}`
            }
          });
          
          if (choicesResponse.ok) {
            const choicesData = await choicesResponse.json();
            if (choicesData.success && choicesData.choices) {
              choiceHistoryForActiveChapters.push({
                chapter_number: chapter.chapter_number,
                chapter_id: chapter.id,
                choices: choicesData.choices.map(choice => ({
                  ...choice,
                  id: choice.id || choice.choice_id,
                  choice_id: choice.choice_id || choice.id
                })),
                selected_choice: choicesData.choices.find(c => c.is_selected) || null
              });
            }
          }
        }
      }
      
      // Sort by chapter number
      choiceHistoryForActiveChapters.sort((a, b) => a.chapter_number - b.chapter_number);
      
      console.log('✅ Choice history fetched using chapter_id:', choiceHistoryForActiveChapters.length, 'Chapters');
      console.log('🔧 Choice history data:', choiceHistoryForActiveChapters.map(ch => ({
        chapter: ch.chapter_number,
        chapter_id: ch.chapter_id,
        choiceCount: ch.choices.length,
        choiceIds: ch.choices.map(c => c.id)
      })));
      
      setChoiceHistory(choiceHistoryForActiveChapters);
      setChoiceHistoryError('');
      
    } catch (err) {
      console.error('❌ Error fetching choice history:', err);
      setChoiceHistoryError('Error connecting to server');
      setChoiceHistory([]);
    } finally {
      setChoiceHistoryLoading(false);
    }
  };

  // Function to fetch choices using provided chapters (avoids race condition with state)
  const fetchChoiceHistoryWithChapters = async (storyId, chapters) => {
    console.log('📋 CHOICE HISTORY WITH CHAPTERS - Fetching for story:', storyId, 'with', chapters.length, 'chapters');
    setChoiceHistoryLoading(true);
    setChoiceHistoryError('');
    
    if (!storyId || !session?.access_token || !chapters || chapters.length === 0) {
      setChoiceHistoryError('Story ID, authentication, or chapters required');
      setChoiceHistoryLoading(false);
      return;
    }
    
    // CRITICAL: Reset choice selection state when fetching new history
    setSelectedChoiceId(null);
    console.log('🔄 CHOICE SELECTION RESET for history fetch');
    
    try {
      // Fetch choices for each active chapter using chapter_id
      const choiceHistoryForActiveChapters = [];
      
      for (const chapter of chapters) {
        if (chapter.is_active !== false) { // Only fetch for active chapters
          console.log('🔍 Fetching choices for chapter:', chapter.chapter_number, 'ID:', chapter.id);
          
          const choicesResponse = await fetch(createApiUrl(API_ENDPOINTS.GET_CHAPTER_CHOICES.replace('{chapter_id}', chapter.id)), {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${session.access_token}`
            }
          });
          
          if (choicesResponse.ok) {
            const choicesData = await choicesResponse.json();
            console.log('📦 Choices response for chapter', chapter.chapter_number, ':', choicesData);
            
            if (choicesData.success && choicesData.choices) {
              choiceHistoryForActiveChapters.push({
                chapter_number: chapter.chapter_number,
                chapter_id: chapter.id,
                choices: choicesData.choices.map(choice => ({
                  ...choice,
                  id: choice.id || choice.choice_id,
                  choice_id: choice.choice_id || choice.id
                })),
                selected_choice: choicesData.choices.find(c => c.is_selected) || null
              });
              console.log('✅ Added', choicesData.choices.length, 'choices for chapter', chapter.chapter_number);
            } else {
              console.log('ℹ️ No choices found for chapter', chapter.chapter_number);
            }
          } else {
            console.error('❌ Failed to fetch choices for chapter', chapter.chapter_number, 'Status:', choicesResponse.status);
          }
        }
      }
      
      // Sort by chapter number
      choiceHistoryForActiveChapters.sort((a, b) => a.chapter_number - b.chapter_number);
      
      console.log('✅ Choice history fetched using provided chapters:', choiceHistoryForActiveChapters.length, 'Chapters with choices');
      console.log('🔧 Choice history data:', choiceHistoryForActiveChapters.map(ch => ({
        chapter: ch.chapter_number,
        chapter_id: ch.chapter_id,
        choiceCount: ch.choices.length,
        choiceIds: ch.choices.map(c => c.id)
      })));
      
      setChoiceHistory(choiceHistoryForActiveChapters);
      setChoiceHistoryError('');
      
    } catch (err) {
      console.error('❌ Error fetching choice history with chapters:', err);
      setChoiceHistoryError('Error connecting to server');
      setChoiceHistory([]);
    } finally {
      setChoiceHistoryLoading(false);
    }
  };

  // Helper function to fetch choices for a specific chapter by chapter_id
  const fetchChoicesForChapter = async (chapterId) => {
    console.log('🎯 Fetching choices for chapter ID:', chapterId);
    
    if (!chapterId || !session?.access_token) {
      console.error('❌ Missing chapter ID or authentication');
      return [];
    }
    
    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.GET_CHAPTER_CHOICES.replace('{chapter_id}', chapterId)), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        }
      });

      if (!response.ok) {
        console.error('❌ Failed to fetch choices for chapter:', response.status);
        return [];
      }

      const data = await response.json();
      
      if (data.success && data.choices) {
        console.log('✅ Choices fetched for chapter:', data.choices.length);
        return data.choices.map(choice => ({
          ...choice,
          id: choice.id || choice.choice_id,
          choice_id: choice.choice_id || choice.id
        }));
      } else {
        console.error('❌ No choices found for chapter:', chapterId);
        return [];
      }
    } catch (err) {
      console.error('❌ Error fetching choices for chapter:', err);
      return [];
    }
  };

  // Component to render a single chapter with its choices (game-like progression)
  const renderChapterCard = (chapter, chapterChoices, isCurrentChapter = false, showNewChoices = false) => {
    const hasChoices = chapterChoices && chapterChoices.choices && chapterChoices.choices.length > 0;
    const selectedChoice = chapterChoices?.selected_choice;
    
    // For saved Stories, allow choice selection in these cases:
    // 1. showNewChoices = true (new choices generated)
    // 2. selectedStory exists, it's current chapter, and this is the last chapter (user can try different paths)
    const allowChoiceSelection = showNewChoices || (selectedStory && isCurrentChapter);
    
    // Get version data for this chapter
    const key = selectedStory ? `${selectedStory.id}_${chapter.chapter_number}` : null;
    const versions = key ? chapterVersions[key] || [] : [];
    const activeVersionId = key ? activeVersions[key] : null;
    const isLoadingVersions = key ? versionLoading[key] : false;
    
    console.log('🎮 CHOICE INTERACTION - Chapter', chapter.chapter_number, {
      selectedStory: !!selectedStory,
      isCurrentChapter,
      hasSelectedChoice: !!selectedChoice,
      showNewChoices,
      allowChoiceSelection,
      hasChoices,
      currentSelectedChoiceId: selectedChoiceId,
      choicesCount: chapterChoices?.choices?.length || 0,
      choiceIds: chapterChoices?.choices?.map(c => c.id) || [],
      logicReason: showNewChoices ? 'showNewChoices=true' : (selectedStory && isCurrentChapter) ? 'saved story + current chapter' : 'no match',
      versionsCount: versions.length
    });
    
    return (
      <div className={`relative ${isCurrentChapter ? 'ring-2 ring-blue-500' : ''}`}>
        {/* Chapter Content Card */}
        <div className="card">
          {/* Chapter Header with Version Dropdown */}
          <div className="flex justify-between items-start mb-4">
            <div className="flex-1">
              <h3 className="text-xl font-bold text-white">
                📖 Chapter {chapter.chapter_number}
              </h3>
              <div className="flex items-center gap-4 text-sm text-gray-400 mt-1">
                <span>📝 {chapter.word_count || 0} words</span>
                <span>📅 {new Date(chapter.created_at).toLocaleDateString()}</span>
                {chapter.user_choice_title && (
                  <span className="bg-blue-900/30 px-2 py-1 rounded text-blue-300">
                    Choice: {chapter.user_choice_title}
                  </span>
                )}
                {isCurrentChapter && (
                  <span className="text-xs px-3 py-1 bg-blue-900/50 text-blue-300 rounded-full">
                    Current
                  </span>
                )}
              </div>
            </div>
            
            {/* Version Dropdown */}
            {versions.length > 1 && (
              <div className="relative min-w-[200px]">
                <select
                  className="bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={activeVersionId || ''}
                  onChange={(e) => {
                    const versionId = parseInt(e.target.value);
                    if (versionId !== activeVersionId) {
                      switchChapterVersion(selectedStory.id, chapter.chapter_number, versionId);
                    }
                  }}
                  disabled={isLoadingVersions}
                >
                  {isLoadingVersions ? (
                    <option>Loading versions...</option>
                  ) : (
                    versions.map(version => (
                      <option key={version.id} value={version.id}>
                        Version {version.version_number}
                        {version.is_active ? ' (Active)' : ''}
                        {version.user_choice_title ? ` - ${version.user_choice_title}` : ''}
                      </option>
                    ))
                  )}
                </select>
                <div className="text-xs text-gray-500 mt-1">
                  {versions.length} version{versions.length !== 1 ? 's' : ''} available
                </div>
              </div>
            )}
          </div>

          {/* Version History Info */}
          {versions.length > 1 && (
            <div className="mb-4 p-3 bg-gray-900/50 rounded border border-gray-700">
              <h4 className="text-sm font-medium text-gray-300 mb-2">📚 Version History</h4>
              <div className="space-y-2">
                {versions.slice(0, 3).map(version => (
                  <div key={version.id} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${version.is_active ? 'bg-green-500' : 'bg-gray-500'}`}></span>
                      <span className="text-gray-400">Version {version.version_number}</span>
                      {version.user_choice_title && (
                        <span className="text-blue-400">→ {version.user_choice_title}</span>
                      )}
                    </div>
                    <span className="text-gray-500">
                      {new Date(version.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
                {versions.length > 3 && (
                  <div className="text-xs text-gray-500">... and {versions.length - 3} more versions</div>
                )}
              </div>
            </div>
          )}
          
          <div className="text-gray-200 whitespace-pre-wrap leading-relaxed mb-6">
            {chapter.content}
          </div>
          
          {/* Chapter Choices Section */}
          {hasChoices && (
            <div className="border-t border-gray-700 pt-6">
              <h4 className="text-lg font-semibold text-white mb-4">
                {selectedChoice ? "Your Choice Path:" : "Choose Your Path:"}
              </h4>
              
              {/* Helpful guidance for users */}
              {allowChoiceSelection && (
                <div className="mb-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg text-sm text-blue-200">
                  💡 <strong>Interactive Mode:</strong> Click any choice to explore different story paths. 
                  All choices are available for you to try and see how the story unfolds differently.
                </div>
              )}
              
              <div className="space-y-3">
                {chapterChoices.choices.map((choice) => {
                  const isCurrentlySelected = allowChoiceSelection && selectedChoiceId === choice.id;
                  // Debug choice selection issues
                  console.log('🔍 CHOICE DEBUG:', {
                    choiceId: choice.id,
                    choiceTitle: choice.title,
                    isCurrentlySelected,
                    selectedChoiceId,
                    allowChoiceSelection,
                    isSelected: choice.is_selected,
                    choiceIdType: typeof choice.id,
                    selectedChoiceIdType: typeof selectedChoiceId
                  });
                  
                  return (
                  <div
                    key={choice.id}
                    className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                      isCurrentlySelected
                        ? 'border-blue-500 bg-blue-900/30 ring-2 ring-blue-400/50'  // Currently selected by user
                        : 'border-gray-600 bg-gray-800/30'   // Default state for all choices
                    } ${allowChoiceSelection ? 'cursor-pointer hover:border-gray-500' : ''}`}
                    onClick={allowChoiceSelection ? (e) => {
                      e.stopPropagation(); // Prevent event bubbling
                      console.log('🎯 CHOICE CLICKED:', {
                        choiceId: choice.id,
                        choiceTitle: choice.title,
                        currentSelectedId: selectedChoiceId,
                        allowChoiceSelection,
                        isSelected: choice.is_selected,
                        clickedSameChoice: selectedChoiceId === choice.id
                      });
                      
                      // Convert both to strings to ensure proper comparison
                      const choiceIdStr = String(choice.id);
                      const selectedIdStr = String(selectedChoiceId);
                      
                      // Toggle selection: if clicking the same choice, deselect it
                      if (selectedIdStr === choiceIdStr) {
                        setSelectedChoiceId(null);
                        console.log('🔄 CHOICE DESELECTED');
                      } else {
                        setSelectedChoiceId(choice.id);
                        console.log('✅ CHOICE STATE UPDATED to:', choice.id);
                      }
                    } : undefined}
                  >
                    <div className="flex items-start">
                      <div className={`w-6 h-6 rounded-full border-2 mr-3 mt-1 flex-shrink-0 ${
                        isCurrentlySelected
                          ? 'border-blue-500 bg-blue-500'      // Currently selected by user
                          : 'border-gray-500'                  // Default state for all choices
                      }`}>
                        {isCurrentlySelected && (
                          <div className="w-2 h-2 bg-white rounded-full m-auto mt-1"></div>
                        )}
                      </div>
                      <div className="flex-1">
                        <h5 className={`font-semibold mb-2 ${
                          allowChoiceSelection 
                            ? 'text-white'     // All choices are white when selectable
                            : 'text-gray-300'  // All choices are gray when not selectable
                        }`}>
                          {choice.title}
                        </h5>
                        <p className="text-gray-300 text-sm leading-relaxed mb-3">
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
                  );
                })}
              </div>
              
              {/* Action buttons for current chapter */}
              {allowChoiceSelection && selectedChoiceId && (
                <div className="text-center mt-6">
                  <button
                    onClick={() => {
                      if (selectedStory) {
                        handleChoiceSelectionForSavedStory(selectedChoiceId);
                      } else {
                        handleChoiceSelection(selectedChoiceId);
                      }
                    }}
                    disabled={generateWithChoiceLoading}
                    className="btn-primary"
                  >
                    {generateWithChoiceLoading ? 'Generating next chapter...' : 'Continue with this choice'}
                  </button>
                  
                  {/* Debug button to reset selection */}
                  <button
                    onClick={() => {
                      setSelectedChoiceId(null);
                      console.log('🔄 MANUAL CHOICE RESET');
                    }}
                    className="ml-3 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm"
                  >
                    Reset Selection
                  </button>
                </div>
              )}
              
              {/* Debug info for developers */}
              {allowChoiceSelection && (
                <div className="mt-4 p-3 bg-gray-800/50 rounded text-xs text-gray-400 border border-blue-500/30">
                  <div className="font-semibold text-blue-300 mb-2">🔧 Debug Info:</div>
                  <div>selectedChoiceId = {selectedChoiceId || 'null'}</div>
                  <div>allowChoiceSelection = {String(allowChoiceSelection)}</div>
                  <div>choices count = {chapterChoices?.choices?.length || 0}</div>
                  <div>isCurrentChapter = {String(isCurrentChapter)}</div>
                  <div>showNewChoices = {String(showNewChoices)}</div>
                  <div>selectedStory exists = {String(!!selectedStory)}</div>
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Visual connector arrow (except for last chapter) */}
        {hasChoices && selectedChoice && (
          <div className="flex justify-center py-4">
            <div className="flex items-center space-x-2 text-gray-400">
              <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Component to render the complete story progression
  const renderStoryProgression = () => {
    if (!allChapters || allChapters.length === 0) {
      return (
        <div className="text-gray-400 text-center py-8">
          No Chapters available yet.
        </div>
      );
    }

    return (
      <div className="space-y-0">
        {allChapters.map((chapter, index) => {
          const chapterChoices = choiceHistory.find(ch => ch.chapter_number === chapter.chapter_number);
          const isLastChapter = index === allChapters.length - 1;
          const showNewChoices = isLastChapter && showChoices && availableChoices.length > 0;
          
          // For the last chapter, if we have new choices, use those instead of history
          const displayChoices = showNewChoices 
            ? { choices: availableChoices, chapter_number: chapter.chapter_number }
            : chapterChoices;

          return (
            <div key={chapter.id}>
              {renderChapterCard(chapter, displayChoices, isLastChapter, showNewChoices)}
            </div>
          );
        })}
        

      </div>
    );
  };

  // Component for new story generation progression
  const renderNewStoryProgression = () => {
    if (!chapter) return null;

    // Create a mock chapter object for the new story flow
    const chapter1 = {
      id: 'chapter-1-new',
      chapter_number: 1,
      content: chapter
    };

    // Create choices object if available
    const chapter1Choices = (showChoices && availableChoices.length > 0) ? {
      choices: availableChoices,
      chapter_number: 1,
      selected_choice: null
    } : (storyId && choiceHistory.length > 0) ? choiceHistory.find(ch => ch.chapter_number === 1) : null;

    return (
      <div className="space-y-0">
        {renderChapterCard(chapter1, chapter1Choices, true, showChoices && availableChoices.length > 0)}
        
        {/* Show any additional Chapters that were generated via choices */}
        {storyId && allChapters.length > 1 && allChapters.slice(1).map((chap, index) => {
          const chapterChoices = choiceHistory.find(ch => ch.chapter_number === chap.chapter_number);
          const isLastChapter = index === allChapters.length - 2; // -2 because we're slicing from index 1
          const showNewChoices = isLastChapter && showChoices && availableChoices.length > 0;
          
          const displayChoices = showNewChoices 
            ? { choices: availableChoices, chapter_number: chap.chapter_number }
            : chapterChoices;

          return (
            <div key={chap.id}>
              {renderChapterCard(chap, displayChoices, isLastChapter, showNewChoices)}
            </div>
          );
        })}
      </div>
    );
  };

  // Function to handle branching from a previous choice
  const handleBranchFromChoice = async (chapterNumber, choiceId, choiceData) => {
    if (!selectedStory || !session?.access_token) {
      setChoicesError('Please log in and select a story.');
      return;
    }

    console.log('🌿 BRANCH: Starting branch operation', {
      storyId: selectedStory.id,
      chapterNumber,
      choiceId,
      choiceTitle: choiceData?.title
    });

    setBranchingLoading(true);
    setChoicesError('');

    try {
      const requestBody = {
        story_id: selectedStory.id,
        chapter_number: chapterNumber,
        choice_id: choiceId,
        choice_data: choiceData
      };

      console.log('📨 BRANCH: Request payload:', requestBody);

      const response = await fetch(createApiUrl(API_ENDPOINTS.BRANCH_FROM_CHOICE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();
      console.log('📦 BRANCH: Response data:', data);

      if (data.success) {
        // Show success message
        setSaveChaptersuccess(`🌿 Branched from Chapter ${chapterNumber}! New Chapter ${data.chapter_number} generated based on your choice: "${choiceData.title}"`);
        
        // Refresh the chapters list to show the new branched content (only active versions)
        const { data: updatedChapters, error } = await supabase
          .from('Chapters')
          .select('*')
          .eq('story_id', selectedStory.id)
          .eq('is_active', true)  // Only get active versions
          .order('chapter_number', { ascending: true });
        
        if (!error && updatedChapters) {
          setAllChapters(updatedChapters);
        }

        // Refresh choice history to show the updated choices
        await fetchChoiceHistory(selectedStory.id);

        // Hide interactive timeline and reset branching state
        setShowInteractiveTimeline(false);
        setBranchingFromChapter(null);

        // Clear any current choice selection state
        setShowChoices(false);
        setSelectedChoiceId(null);
        setAvailableChoices([]);

      } else {
        const errorMsg = data.detail || 'Failed to branch from choice';
        console.error('❌ BRANCH: Failed:', errorMsg);
        setChoicesError(errorMsg);
        return false;
      }
    } catch (err) {
      console.error('❌ BRANCH: Error:', err);
      setChoicesError('Error connecting to server');
      return false;
    } finally {
      setBranchingLoading(false);
    }
    
    return true;
  };

  // Function to handle tree node clicks
  const handleTreeNodeClick = (nodeData) => {
    console.log('🌳 Tree node clicked:', nodeData);
    
    // Close the tree visualization
    setShowTreeVisualization(false);
    
    // Show chapter details in a simple modal or navigate to that chapter
    // For now, we'll show an alert with chapter info - this can be enhanced later
    const chapterInfo = `Chapter ${nodeData.chapter_number}: ${nodeData.title}\n\nBranch: ${nodeData.branch_name}\nWord Count: ${nodeData.word_count}\n\nContent Preview:\n${nodeData.content.substring(0, 200)}...`;
    
    // You could replace this with a proper modal or navigation
    if (window.confirm(`${chapterInfo}\n\nWould you like to view this chapter in the story timeline?`)) {
      // Close tree and show interactive timeline focused on this chapter
      setShowInteractiveTimeline(true);
    }
  };

  // Function to handle tree edge (choice) clicks
  const handleTreeEdgeClick = (edgeData) => {
    console.log('🌳 Tree edge clicked:', edgeData);
    
    // Close the tree visualization
    setShowTreeVisualization(false);
    
    // Show choice details and offer to branch/preview
    const choiceInfo = `Choice: ${edgeData.choice_title}\n\nDescription: ${edgeData.choice_description}\nImpact: ${edgeData.story_impact}\nCurrently Selected: ${edgeData.is_selected ? 'Yes' : 'No'}`;
    
    if (!edgeData.is_selected) {
      if (window.confirm(`${choiceInfo}\n\nWould you like to explore this choice path?`)) {
        // Open interactive timeline and potentially trigger branching
        setShowInteractiveTimeline(true);
        // Could also trigger the branch preview functionality here
      }
    } else {
      alert(`${choiceInfo}\n\nThis is the currently selected path in your story.`);
    }
  };

  // Function to handle accepting a preview with proper versioning
  const handleAcceptPreview = async (chapterNumber, choiceId, choiceData) => {
    if (!selectedStory || !session?.access_token) {
      setChoicesError('Please log in and select a story.');
      return;
    }

    console.log('✅ ACCEPT-PREVIEW: Starting accept preview operation with versioning', {
      storyId: selectedStory.id,
      chapterNumber,
      choiceId,
      choiceTitle: choiceData?.title
    });

    setBranchingLoading(true);
    setChoicesError('');

    try {
      const requestBody = {
        story_id: selectedStory.id,
        chapter_number: chapterNumber,
        choice_id: choiceId,
        choice_data: choiceData
      };

      // Use the new versioning endpoint
      const response = await fetch(createApiUrl(API_ENDPOINTS.ACCEPT_PREVIEW_WITH_VERSIONING), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();
      console.log('📦 ACCEPT-PREVIEW: Response data:', data);

      if (data.success) {
        // Show success message
        setSaveChaptersuccess(data.message);
        
        // Refresh the chapters list (using the same logic as in useEffect)
        try {
          const { data: Chapters, error } = await supabase
            .from('Chapters')
            .select('*')
            .eq('story_id', selectedStory.id)
            .eq('is_active', true)  // Only get active versions
            .order('chapter_number', { ascending: true });
          
          if (!error && Chapters) {
            setAllChapters(Chapters);
          }
        } catch (fetchError) {
          console.error('❌ Failed to refresh chapters:', fetchError);
        }
        
        // Fetch versions for the new chapter
        await fetchChapterVersions(selectedStory.id, data.chapter_number);
        
        // Refresh choice history
        await fetchChoiceHistory(selectedStory.id);
        
        // Clear any current choice selection state
        setShowChoices(false);
        setSelectedChoiceId(null);
        setAvailableChoices([]);
        
      } else {
        throw new Error(data.detail || 'Failed to accept preview');
      }

    } catch (err) {
      console.error('❌ ACCEPT-PREVIEW: Error:', err);
      setChoicesError(`Error accepting preview: ${err.message}`);
    } finally {
      setBranchingLoading(false);
    }
  };

  // Function to handle preview of branching from a previous choice (without saving to DB)
  const handlePreviewBranchFromChoice = async (chapterNumber, choiceId, choiceData) => {
    if (!selectedStory || !session?.access_token) {
      setChoicesError('Please log in and select a story.');
      return;
    }

    // Do NOT increment chapterNumber in the request payload
    const previewedChapterNumber = chapterNumber + 1;

    console.log('👀 PREVIEW: Starting preview operation', {
      storyId: selectedStory.id,
      currentChapterNumber: chapterNumber,
      previewedChapterNumber,
      choiceId,
      choiceTitle: choiceData?.title
    });

    setPreviewLoading(true);
    setChoicesError('');

    try {
      const requestBody = {
        story_id: selectedStory.id,
        chapter_number: chapterNumber, // Send the chapter where the choice was made
        choice_id: choiceId,
        choice_data: choiceData
      };

      console.log('📨 PREVIEW: Request payload:', requestBody);

      const response = await fetch(createApiUrl(API_ENDPOINTS.BRANCH_PREVIEW), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();
      console.log('📦 PREVIEW: Response data:', data);

      if (data.success) {
        // Find the original chapter that would be replaced
        const originalChapter = allChapters.find(c => c.chapter_number === data.chapter_number);
        
        // Store both versions for comparison
        setDraftComparison({
          original: originalChapter,
          preview: {
            chapter_number: data.chapter_number,
            content: data.chapter_content,
            summary: data.chapter_summary || '',  // Store the generated summary
            choices: data.choices,
            title: `Chapter ${data.chapter_number} (Preview)`
          },
          commitParams: { chapterNumber: previewedChapterNumber, choiceId, choiceData }, // Store next chapter number for saving
          selectedChoice: choiceData
        });
        
        setShowDraftModal(true);
        console.log('✅ PREVIEW: Comparison modal opened');
        
      } else {
        const errorMsg = data.detail || 'Failed to generate preview';
        console.error('❌ PREVIEW: Failed:', errorMsg);
        setChoicesError(errorMsg);
      }
    } catch (err) {
      console.error('❌ PREVIEW: Error:', err);
      setChoicesError('Error connecting to server during preview');
    } finally {
      setPreviewLoading(false);
    }
  };

  // Function to fetch all versions of a specific chapter
  const fetchChapterVersions = async (storyId, chapterNumber) => {
    if (!session?.access_token) return;
    
    const key = `${storyId}_${chapterNumber}`;
    setVersionLoading(prev => ({ ...prev, [key]: true }));
    
    try {
      const response = await fetch(
        createApiUrl(API_ENDPOINTS.GET_CHAPTER_VERSIONS.replace('{story_id}', storyId).replace('{chapter_number}', chapterNumber)),
        {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setChapterVersions(prev => ({ ...prev, [key]: data.versions }));
        setActiveVersions(prev => ({ ...prev, [key]: data.active_version?.id }));
      }
    } catch (error) {
      console.error('Error fetching chapter versions:', error);
    } finally {
      setVersionLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  // Function to switch chapter versions
  const switchChapterVersion = async (storyId, chapterNumber, versionId) => {
    if (!session?.access_token) return;
    
    try {
      const response = await fetch(
        createApiUrl(API_ENDPOINTS.SWITCH_CHAPTER_VERSION.replace('{story_id}', storyId).replace('{chapter_number}', chapterNumber)),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ version_id: versionId })
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setSaveChaptersuccess(data.message);
        
        // Refresh chapters and versions
        await fetchChapters();
        await fetchChapterVersions(storyId, chapterNumber);
      }
    } catch (error) {
      console.error('Error switching version:', error);
      setSaveChapterError('Failed to switch version');
    }
  };

  // Interactive Timeline Component for Branching
  const renderInteractiveTimeline = () => {
    if (!allChapters || allChapters.length === 0 || !choiceHistory || choiceHistory.length === 0) {
      return (
        <div className="text-gray-400 text-center py-8">
          <p>No chapters with choices available for branching yet.</p>
          <p className="text-sm mt-2">Generate some chapters first, then you can explore different story paths!</p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div className="text-center mb-6">
          <h3 className="text-xl font-bold text-white mb-2">📍 Interactive Story Timeline</h3>
          <p className="text-gray-300">Click on any choice from the previous chapter to preview alternatives, or click older chapter choices to branch permanently</p>
        </div>

        {allChapters.map((chapter, index) => {
          const chapterChoices = choiceHistory.find(ch => ch.chapter_number === chapter.chapter_number);
          const hasChoices = chapterChoices && chapterChoices.choices && chapterChoices.choices.length > 0;
          
          if (!hasChoices) return null; // Only show chapters that have choices

          return (
            <div key={chapter.id} className="relative">
              {/* Chapter Header */}
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold mr-4">
                  {chapter.chapter_number}
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-white">
                    {chapter.title || `Chapter ${chapter.chapter_number}`}
                  </h4>
                  <p className="text-gray-300 text-sm">
                    {chapter.content?.substring(0, 100)}...
                  </p>
                </div>
              </div>

              {/* Chapter Choices */}
              <div className="ml-14 space-y-3">
                <h5 className="text-md font-medium text-gray-200 mb-3">
                  Available Choices:
                </h5>
                
                {chapterChoices.choices.map((choice) => {
                  const isSelected = choice.is_selected;
                  const isBranchingFromThisChapter = branchingFromChapter === chapter.chapter_number;
                  
                  // Determine if this is the previous chapter (only previous chapter choices should trigger preview)
                  const currentChapterNumber = allChapters.length; // Current chapter number based on existing chapters
                  const isPreviousChapter = chapter.chapter_number === currentChapterNumber - 1;
                  
                  return (
                    <div
                      key={choice.id}
                      className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                        isSelected 
                          ? isPreviousChapter 
                            ? 'border-green-500 bg-green-900/20 cursor-pointer hover:border-green-400' // Selected in previous chapter - clickable for preview
                            : 'border-green-500 bg-green-900/20 cursor-default' // Selected in older chapters - not clickable
                          : (isBranchingFromThisChapter && branchingLoading) || previewLoading
                            ? 'border-gray-600 bg-gray-800/50 opacity-50 cursor-not-allowed' // Disabled during branching/preview
                            : 'border-gray-600 bg-gray-800/30 hover:border-blue-500 hover:bg-blue-900/20 cursor-pointer transform hover:scale-[1.02] hover:shadow-lg' // Available to select - enhanced hover
                      }`}
                      onClick={() => {
                        if (branchingLoading || previewLoading) return; // Prevent clicks during loading
                        
                        if (isPreviousChapter) {
                          // Previous chapter - any choice (selected or not) opens preview
                          handlePreviewBranchFromChoice(chapter.chapter_number, choice.id, choice);
                        } else if (!isSelected) {
                          // Older chapters - only non-selected choices trigger full branch
                          handleBranchFromChoice(chapter.chapter_number, choice.id, choice);
                        }
                        // If it's the selected choice in an older chapter, do nothing
                      }}
                    >
                      <div className="flex items-start">
                        <div className={`w-6 h-6 rounded-full border-2 mr-3 mt-1 flex-shrink-0 ${
                          isSelected
                            ? 'border-green-500 bg-green-500' // Currently selected
                            : 'border-gray-500 hover:border-blue-400' // Available
                        }`}>
                          {isSelected && (
                            <div className="w-2 h-2 bg-white rounded-full m-auto mt-1"></div>
                          )}
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h6 className={`font-semibold mb-1 ${
                              isSelected ? 'text-green-300' : 'text-white'
                            }`}>
                              {choice.title}
                              {isSelected && <span className="ml-2 text-xs bg-green-800 px-2 py-1 rounded">Current Path</span>}
                            </h6>
                            
                            {!isSelected && (
                              <div className="text-xs text-blue-400 font-medium pointer-events-none">
                                {branchingLoading && isBranchingFromThisChapter ? '🔄 Branching...' : 
                                 previewLoading ? '👀 Generating preview...' :
                                 isPreviousChapter ? '👀 Click to preview this path' : '🌿 Click to explore this path'}
                              </div>
                            )}
                            {isSelected && isPreviousChapter && (
                              <div className="text-xs text-green-400 font-medium pointer-events-none">
                                {previewLoading ? '👀 Generating preview...' : '👀 Click to preview alternative'}
                              </div>
                            )}
                          </div>
                          
                          <p className="text-gray-300 text-sm leading-relaxed mb-2">
                            {choice.description}
                          </p>
                          
                          <div className="flex items-center space-x-2">
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
                          
                          {isSelected && choice.selected_at && (
                            <p className="text-xs text-gray-400 mt-2">
                              Selected on {new Date(choice.selected_at).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Connection line to next chapter (except for last) */}
              {index < allChapters.length - 1 && (
                <div className="flex justify-center py-6">
                  <div className="w-0.5 h-8 bg-gray-600"></div>
                        </div>
      )}

      {/* Draft Comparison Modal */}
      {showDraftModal && draftComparison && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-lg w-full max-w-6xl max-h-[90vh] shadow-xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-gray-800">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold text-white mb-2">
                    📊 Compare Chapter Drafts
                  </h3>
                  <p className="text-gray-300">
                    Comparing Chapter {draftComparison.preview.chapter_number} based on choice: 
                    <span className="font-semibold text-blue-300 ml-2">"{draftComparison.selectedChoice?.title}"</span>
                  </p>
                </div>
                <button
                  className="btn-icon"
                  onClick={() => {
                    setShowDraftModal(false);
                    setDraftComparison(null);
                  }}
                  aria-label="Close"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 max-h-[calc(90vh-200px)] overflow-y-auto">
              {/* Current Version */}
              <div className="border border-gray-700 rounded-lg overflow-hidden">
                <div className="bg-green-900/20 border-b border-green-700/50 p-4">
                  <h4 className="font-semibold text-green-300 flex items-center">
                    <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                    Current Version
                  </h4>
                  <p className="text-sm text-green-200 mt-1">
                    {draftComparison.original ? 'The existing chapter in your story' : 'No existing chapter'}
                  </p>
                </div>
                <div className="p-4 max-h-96 overflow-y-auto">
                  <div className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
                    {draftComparison.original?.content || 'No existing chapter found. This would be a new chapter.'}
                  </div>
                </div>
              </div>

              {/* Preview Version */}
              <div className="border border-gray-700 rounded-lg overflow-hidden">
                <div className="bg-blue-900/20 border-b border-blue-700/50 p-4">
                  <h4 className="font-semibold text-blue-300 flex items-center">
                    <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
                    Preview Version
                  </h4>
                  <p className="text-sm text-blue-200 mt-1">
                    How the chapter would look with your selected choice
                  </p>
                </div>
                <div className="p-4 max-h-96 overflow-y-auto">
                  <div className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
                    {draftComparison.preview.content}
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="border-t border-gray-800 p-6">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="text-sm text-gray-400">
                  <p>💡 <strong>Keep Original:</strong> No changes will be made to your story</p>
                  <p>🌿 <strong>Accept Preview:</strong> This will replace the current chapter and affect all future chapters</p>
                </div>
                <div className="flex space-x-3">
                  <button
                    className="px-6 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-100 transition-colors"
                    onClick={() => {
                      setShowDraftModal(false);
                      setDraftComparison(null);
                    }}
                  >
                    Keep Original
                  </button>
                  <button
                    className="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors"
                    onClick={async () => {
                      // Save the previewed content, not regenerate
                      const { chapterNumber, choiceId, choiceData } = draftComparison.commitParams;
                      const previewContent = draftComparison.preview.content;
                      const previewSummary = draftComparison.preview.summary;
                      const previewChoices = draftComparison.preview.choices;
                      setShowDraftModal(false);
                      setDraftComparison(null);
                      await savePreviewedChapter({
                        chapterNumber,
                        choiceId,
                        choiceData,
                        content: previewContent,
                        summary: previewSummary,
                        choices: previewChoices
                      });
                    }}
                  >
                    Accept Preview
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
})}
        
        {/* Close Timeline Button */}
        <div className="text-center pt-6">
          <button
            onClick={() => setShowInteractiveTimeline(false)}
            className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
          >
            Close Timeline
          </button>
        </div>
      </div>
    );
  };

  // Function to save the previewed chapter as a new version
  const savePreviewedChapter = async ({ chapterNumber, choiceId, choiceData, content, summary, choices }) => {
    if (!selectedStory || !session?.access_token) return;
    setBranchingLoading(true);
    setChoicesError('');

    try {
      const requestBody = {
        story_id: selectedStory.id,
        chapter_number: chapterNumber,
        choice_id: choiceId,
        choice_data: choiceData,
        content, // The previewed chapter content
        summary, // The previewed chapter summary
        choices // The previewed choices (if needed)
      };

      // Call the new backend endpoint to save the previewed chapter
      const response = await fetch(createApiUrl(API_ENDPOINTS.SAVE_PREVIEWED_CHAPTER), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();
      if (data.success) {
        setSaveChaptersuccess(data.message);
        // Refresh chapters and choices
        try {
          const { data: Chapters, error } = await supabase
            .from('Chapters')
            .select('*')
            .eq('story_id', selectedStory.id)
            .eq('is_active', true)
            .order('chapter_number', { ascending: true });
          if (!error && Chapters) setAllChapters(Chapters);
        } catch (fetchError) {
          console.error('❌ Failed to refresh chapters:', fetchError);
        }
        await fetchChapterVersions(selectedStory.id, chapterNumber);
        await fetchChoiceHistory(selectedStory.id);
        setShowChoices(false);
        setSelectedChoiceId(null);
        setAvailableChoices([]);
      } else {
        throw new Error(data.detail || 'Failed to save previewed chapter');
      }
    } catch (err) {
      console.error('❌ SAVE-PREVIEWED-CHAPTER: Error:', err);
      setChoicesError(`Error saving previewed chapter: ${err.message}`);
    } finally {
      setBranchingLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-black flex items-center justify-center relative">
      {/* Story Tree Visualization Modal */}
      {showTreeVisualization && selectedStory && (
        <StoryTreeVisualization
          storyId={selectedStory.id}
          onClose={() => setShowTreeVisualization(false)}
          onNodeClick={handleTreeNodeClick}
          onEdgeClick={handleTreeEdgeClick}
        />
      )}

      {/* Modal for viewing full story - render at root level for proper overlay */}
      {selectedStory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="modal-content animate-slide-in-bottom">
            {/* Header with proper button spacing */}
            <div className="flex items-center justify-between p-6 border-b border-gray-800">
              <h2 className="text-2xl font-bold text-white">
                {selectedStory.story_title}
              </h2>
              <div className="flex items-center space-x-3">
                <button
                  className="btn-icon"
                  onClick={() => setShowChatbot(!showChatbot)}
                  aria-label="Toggle Chat"
                  title="Chat with your story"
                >
                  💬
                </button>
                <button
                  className="btn-icon"
                  onClick={closeModal}
                  aria-label="Close"
                >
                  ✕
                </button>
              </div>
            </div>
            
            {/* Main Content Area */}
            <div className={`flex ${showChatbot ? 'flex-row' : 'flex-col'} h-full max-h-[80vh]`}>
              {/* Story Content Panel */}
              <div className={`${showChatbot ? 'w-1/2 border-r border-gray-800' : 'w-full'} flex flex-col overflow-hidden`}>
                <div className="p-6 flex-1 overflow-y-auto scrollbar-thin">
                  {/* Story Outline */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-300 mb-3">Outline</h3>
                    <div className="card">
                      <p className="text-gray-200 whitespace-pre-wrap leading-relaxed">
                        {selectedStory.story_outline}
                      </p>
                    </div>
                  </div>

                  {/* Story Progression - Chapters with Choices */}
                  {choiceHistoryLoading ? (
                    <div className="card">
                      <div className="text-gray-300 text-center py-6">
                        📚 Loading story progression...
                      </div>
                    </div>
                  ) : (
                    showInteractiveTimeline ? renderInteractiveTimeline() : renderStoryProgression()
                  )}

                  {/* Action Buttons */}
                  <div className="flex flex-col sm:flex-row gap-4 mt-8 pt-6 border-t border-gray-800">
                    {/* Only show Generate Choices button if the current chapter doesn't have choices already */}
                    {!showChoices && !choicesLoading && allChapters.length > 0 && (() => {
                      const currentChapter = allChapters[allChapters.length - 1];
                      const currentChapterChoices = choiceHistory.find(ch => ch.chapter_number === currentChapter?.chapter_number);
                      const hasExistingChoices = currentChapterChoices && currentChapterChoices.choices && currentChapterChoices.choices.length > 0;
                      
                      return !hasExistingChoices;
                    })() && (
                      <button
                        className="btn-primary flex-1"
                        onClick={handleGenerateChoicesForSavedStory}
                        disabled={choicesLoading}
                      >
                        {choicesLoading ? 'Generating Choices...' : `🎯 Generate Choices for Chapter ${allChapters.length}`}
                      </button>
                    )}
                    {allChapters.length === 0 && currentChapterNumber <= totalChapters && (
                      <button
                        className="btn-primary flex-1"
                        onClick={handleGenerateNextChapter}
                        disabled={nextChapterLoading}
                      >
                        {nextChapterLoading ? 'Generating & Saving...' : `📖 Generate Chapter 1`}
                      </button>
                    )}

                    {/* Interactive Timeline Button - Show if story has chapters with choices */}
                    {allChapters.length > 0 && choiceHistory.length > 0 && (
                      <button
                        className="btn-secondary"
                        onClick={() => setShowInteractiveTimeline(!showInteractiveTimeline)}
                        disabled={branchingLoading}
                      >
                        {showInteractiveTimeline ? '📖 Show Story' : '🌿 Explore Paths'}
                      </button>
                    )}
                    
                    {/* Story Tree Visualization Button - Show if story has chapters */}
                    {allChapters.length > 0 && (
                      <button
                        className="btn-secondary"
                        onClick={() => setShowTreeVisualization(true)}
                        disabled={branchingLoading}
                      >
                        🌳 View Story Tree
                      </button>
                    )}
                    <button
                      className="btn-secondary"
                      onClick={() => handleDeleteStory(selectedStory.id)}
                      disabled={deleteLoading}
                    >
                      {deleteLoading ? 'Deleting...' : 'Delete Story'}
                    </button>
                  </div>

                  {/* Loading state for choices */}
                  {choicesLoading && (
                    <div className="card mt-6">
                      <div className="text-center py-6">
                        <div className="text-gray-300 mb-2">🎯 Generating choices for what happens next...</div>
                        <div className="w-full bg-gray-800 rounded-full h-2">
                          <div className="bg-blue-500 h-2 rounded-full animate-pulse w-2/3"></div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Error Messages */}
                  {nextChapterError && (
                    <div className="card mt-6">
                      <div className="text-red-400 text-sm p-3 bg-red-900/20 border border-red-800 rounded-lg">
                        {nextChapterError}
                      </div>
                    </div>
                  )}
                  {deleteError && (
                    <div className="card mt-6">
                      <div className="text-red-400 text-sm p-3 bg-red-900/20 border border-red-800 rounded-lg">
                        {deleteError}
                      </div>
                    </div>
                  )}
                  {choicesError && (
                    <div className="card mt-6">
                      <div className="text-red-400 text-sm p-3 bg-red-900/20 border border-red-800 rounded-lg">
                        {choicesError}
                      </div>
                    </div>
                  )}

                  {/* Story Stats */}
                  <div className="text-xs text-gray-500 mt-6 text-center border-t border-gray-800 pt-4 space-y-2">
                    <div>
                      📖 {allChapters.length} Chapter{allChapters.length !== 1 ? 's' : ''} • 
                      🎯 {choiceHistory.reduce((total, ch) => total + (ch.choices?.length || 0), 0)} Total Choices Available
                    </div>
                    <div>
                      Created on {new Date(selectedStory.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>

              {/* Chatbot Section */}
              {showChatbot && (
                <div className="w-1/2 flex flex-col overflow-hidden">
                  <div className="p-6 border-b border-gray-800">
                    <h3 className="text-lg font-semibold text-white">Story Assistant</h3>
                    <p className="text-sm text-gray-400">Chat about your story</p>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <StoryChatbot 
                      storyId={selectedStory.id} 
                      storyTitle={selectedStory.story_title}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Main Generator Interface */}
      <div className="container">
        <div className="card max-w-2xl mx-auto">
          {/* Tab Navigation */}
          <div className="flex mb-8 bg-gray-800 rounded-lg p-1">
            <button
              className={`flex-1 py-3 px-6 rounded-md font-medium transition-all duration-300 ${
                activeTab === 'generate' 
                  ? 'bg-white text-black' 
                  : 'text-gray-300 hover:text-white'
              }`}
              onClick={() => setActiveTab('generate')}
            >
              Generate Story
            </button>
            <button
              className={`flex-1 py-3 px-6 rounded-md font-medium transition-all duration-300 ${
                activeTab === 'saved' 
                  ? 'bg-white text-black' 
                  : 'text-gray-300 hover:text-white'
              }`}
              onClick={() => setActiveTab('saved')}
            >
              Saved Stories
            </button>
          </div>

          {activeTab === 'generate' ? (
            <div className="space-y-6">
              <div className="text-center">
                <h1 className="text-3xl font-bold text-white mb-2">Story Generator</h1>
                <p className="text-gray-400">Transform your ideas into compelling Stories</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Story Idea
                </label>
                <textarea
                  placeholder="Enter your story idea... Be as detailed or brief as you like!"
                  value={idea}
                  onChange={e => setIdea(e.target.value)}
                  className="textarea-field h-24"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Format
                </label>
                <div className="space-y-3">
                  <label className="flex items-center cursor-pointer group">
                    <input
                      type="radio"
                      name="format"
                      value="book"
                      checked={format === 'book'}
                      onChange={() => setFormat('book')}
                      className="w-4 h-4 text-white bg-gray-800 border-gray-600 focus:ring-white focus:ring-2"
                    />
                    <span className="ml-3 text-gray-200 group-hover:text-white transition-colors">
                      📚 Book
                    </span>
                  </label>
                  <label className="flex items-center cursor-pointer group">
                    <input
                      type="radio"
                      name="format"
                      value="movie"
                      checked={format === 'movie'}
                      onChange={() => setFormat('movie')}
                      className="w-4 h-4 text-white bg-gray-800 border-gray-600 focus:ring-white focus:ring-2"
                    />
                    <span className="ml-3 text-gray-200 group-hover:text-white transition-colors">
                      🎬 Movie
                    </span>
                  </label>
                </div>
              </div>

              <button
                onClick={handleGenerate}
                disabled={loading || !idea}
                className="btn-primary w-full"
              >
                {loading ? 'Generating...' : 'Generate Story'}
              </button>

              {error && (
                <div className="text-red-400 text-sm mt-4 p-3 bg-red-900/20 border border-red-800 rounded-lg">
                  {error}
                </div>
              )}

              {result && (
                <div className="space-y-6 mt-6">
                  {/* Story Title Input */}
                  <div className="card">
                    <h3 className="text-lg font-semibold text-white mb-4">
                      📖 Story Title
                    </h3>
                    <p className="text-gray-300 text-sm mb-4">
                      Edit your story title (auto-generated from the summary):
                    </p>
                    
                    <input
                      type="text"
                      value={storyTitle}
                      onChange={(e) => setStoryTitle(e.target.value)}
                      placeholder="Enter your story title..."
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                      maxLength={100}
                    />
                    <p className="text-gray-400 text-xs mt-2">
                      {storyTitle.length}/100 characters
                    </p>
                  </div>

                  {/* Story Summary Display */}
                  <div className="card">
                    <h3 className="text-lg font-semibold text-white mb-4">
                      📝 Story Summary
                    </h3>
                    <p className="text-gray-300 text-sm mb-4">
                      The complete story summary generated from your idea:
                    </p>
                    
                    <div className="bg-gray-800 border border-gray-600 rounded-lg p-4">
                      <p className="text-gray-200 leading-relaxed whitespace-pre-wrap">
                        {result}
                      </p>
                    </div>
                  </div>

                  {/* Genre and Chapter Titles Display */}
                  {(storyGenre || chapterTitles.length > 0) && (
                    <div className="card">
                      <h3 className="text-lg font-semibold text-white mb-4">
                        📋 Story Details
                      </h3>
                      
                      {/* Genre Display */}
                      {storyGenre && (
                        <div className="mb-4">
                          <span className="text-sm font-medium text-gray-300">Genre:</span>
                          <span className="ml-2 px-3 py-1 bg-blue-600 text-white text-sm rounded-full">
                            {storyGenre}
                          </span>
                        </div>
                      )}
                      
                      {/* Tone Display */}
                      {storyTone && (
                        <div className="mb-4">
                          <span className="text-sm font-medium text-gray-300">Tone:</span>
                          <span className="ml-2 px-3 py-1 bg-purple-600 text-white text-sm rounded-full">
                            {storyTone}
                          </span>
                        </div>
                      )}
                      
                      {/* Chapter Titles Display */}
                      {chapterTitles.length > 0 && (
                        <div>
                          <span className="text-sm font-medium text-gray-300 block mb-2">
                            Chapter Breakdown ({chapterTitles.length} chapters):
                          </span>
                          <div className="space-y-1">
                            {chapterTitles.map((title, index) => (
                              <div key={index} className="flex items-center text-gray-200">
                                <span className="text-blue-400 font-mono text-sm w-8">
                                  {index + 1}.
                                </span>
                                <span className="text-sm">{title}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Save & Continue Section */}
                  <div className="text-center">
                    {!outlineSaved ? (
                      <div>
                        <p className="text-gray-300 font-medium mb-4">
                          📝 Ready to save your outline? You can edit character names by clicking on them above.
                        </p>
                        <div className="flex gap-4 justify-center">
                          <button 
                            onClick={handleSaveOutline} 
                            disabled={saveOutlineLoading || !user}
                            className="btn-primary"
                          >
                            {saveOutlineLoading ? 'Saving...' : '💾 Save & Continue'}
                          </button>
                          <button 
                            onClick={handleDislike} 
                            disabled={loading}
                            className="btn-secondary"
                          >
                            🔄 Generate New Outline
                          </button>
                        </div>
                        {!user && (
                          <p className="text-yellow-400 text-sm mt-2">
                            Please log in to save your outline.
                          </p>
                        )}
                        {saveOutlineError && (
                          <div className="text-red-400 text-sm mt-3 p-3 bg-red-900/20 border border-red-800 rounded-lg">
                            {saveOutlineError}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div>
                        <p className="text-green-400 font-medium mb-4">
                          ✅ Outline saved! Now you can generate Chapter 1.
                        </p>
                        <div className="flex gap-4 justify-center">
                          <button 
                            onClick={handleLike} 
                            disabled={chapterLoading}
                            className="btn-primary"
                          >
                            📖 Generate Chapter 1
                          </button>
                          <button 
                            onClick={handleDislike} 
                            disabled={loading}
                            className="btn-secondary"
                          >
                            🔄 Generate New Outline
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {chapterLoading && (
                <div className="mt-6 text-center">
                  <div className="text-gray-300">Generating Chapter 1...</div>
                  <div className="mt-2 w-full bg-gray-800 rounded-full h-2">
                    <div className="bg-white h-2 rounded-full animate-pulse w-1/2"></div>
                  </div>
                </div>
              )}

              {/* New Story Progression */}
              {chapter && (
                <div className="mt-6">
                  {renderNewStoryProgression()}
                  
                  {/* Story Actions */}
                  <div className="card mt-6">
                    <div className="text-center">
                      <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <button
                          onClick={handleSaveStory}
                          disabled={saveLoading}
                          className="btn-primary"
                        >
                          {saveLoading ? 'Saving...' : 'Save Complete Story'}
                        </button>
                        {!showChoices && !choicesLoading && !storyId && (
                          <button
                            onClick={() => handleGenerateChoices(chapter, 1)}
                            disabled={choicesLoading}
                            className="btn-secondary"
                          >
                            🎯 Generate Choices
                          </button>
                        )}
                      </div>
                      {saveError && (
                        <div className="text-red-400 text-sm mt-3">{saveError}</div>
                      )}
                      {saveSuccess && (
                        <div className="text-green-400 text-sm mt-3">{saveSuccess}</div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Loading state for choices */}
              {choicesLoading && (
                <div className="card mt-6">
                  <div className="text-center py-6">
                    <div className="text-gray-300 mb-2">🎯 Generating choices for what happens next...</div>
                    <div className="w-full bg-gray-800 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full animate-pulse w-2/3"></div>
                    </div>
                  </div>
                </div>
              )}

              {/* Error display */}
              {choicesError && (
                <div className="card mt-6">
                  <div className="text-red-400 text-sm p-3 bg-red-900/20 border border-red-800 rounded-lg">
                    {choicesError}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-white mb-2">Your Stories</h2>
                <p className="text-gray-400">Manage and explore your saved Stories</p>
              </div>

              {fetchingStories ? (
                <div className="text-center py-12">
                  <div className="text-gray-300">Loading your Stories...</div>
                  <div className="mt-4 w-32 mx-auto bg-gray-800 rounded-full h-2">
                    <div className="bg-white h-2 rounded-full animate-pulse w-3/4"></div>
                  </div>
                </div>
              ) : fetchStoriesError ? (
                <div className="text-center py-12">
                  <div className="text-red-400 p-4 bg-red-900/20 border border-red-800 rounded-lg">
                    {fetchStoriesError}
                  </div>
                </div>
              ) : savedStories.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-gray-400 mb-4">No saved Stories yet</div>
                  <button
                    onClick={() => setActiveTab('generate')}
                    className="btn-primary"
                  >
                    Create Your First Story
                  </button>
                </div>
              ) : (
                <div className="grid gap-4">
                  {savedStories.map(story => (
                    <div
                      key={story.id}
                      className="card cursor-pointer hover:bg-gray-800 transition-all duration-300 group"
                      onClick={() => handleStorySelection(story)}
                    >
                      <div className="flex justify-between items-start mb-3">
                        <h3 className="font-bold text-lg text-white group-hover:text-gray-200 transition-colors">
                          {story.story_title || story.title}
                        </h3>
                        <div className="text-xs text-gray-500">
                          {new Date(story.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <p className="text-gray-300 text-sm leading-relaxed">
                        {(story.story_outline || story.outline || 'No outline available').slice(0, 150)}
                        {(story.story_outline || story.outline || '').length > 150 ? '...' : ''}
                      </p>
                      <div className="mt-3 text-xs text-gray-500">
                        Click to view full story
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}