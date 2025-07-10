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
  const [nextChapterText, setNextChapterText] = useState('');
  const [currentChapterNumber, setCurrentChapterNumber] = useState(2); // Assuming chapter 1 is already generated
  const [saveChapterLoading, setSaveChapterLoading] = useState(false);
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
        console.log('🔍 CHAPTER FETCH - Starting fetch for story:', selectedStory.id, selectedStory.story_title);
        setFetchingChapters(true);
        
        try {
          const { data: Chapters, error } = await supabase
            .from('Chapters')
            .select('*')
            .eq('story_id', selectedStory.id)
            .order('chapter_number', { ascending: true });
          
          console.log('📊 CHAPTER FETCH - Query result:', { 
            Chapters: Chapters?.length || 0, 
            error: error?.message,
            storyId: selectedStory.id 
          });
          
          if (error) {
            console.error('❌ CHAPTER FETCH - Error:', error);
            setAllChapters([]);
          } else {
            console.log('✅ CHAPTER FETCH - Success:', Chapters?.length || 0, 'Chapters found');
            if (Chapters && Chapters.length > 0) {
              console.log('📖 CHAPTER FETCH - Chapters:', Chapters.map(c => `Ch${c.chapter_number}: ${c.title || 'Untitled'}`));
            }
            setAllChapters(Chapters || []);
          }
        } catch (fetchError) {
          console.error('❌ CHAPTER FETCH - Exception:', fetchError);
          setAllChapters([]);
        }
        
        setFetchingChapters(false);

        // Also fetch choice history when opening a story
        fetchChoiceHistory(selectedStory.id);
      }
    };
    fetchChapters();
  }, [selectedStory]);

  // Reset state when switching Stories or Chapters
  useEffect(() => {
    if (selectedStory) {
      // CRITICAL: Reset ALL story-specific state when switching Stories
      setNextChapterText('');
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
      // Re-fetch Chapters after a successful save
      (async () => {
        const { data: Chapters, error } = await supabase
          .from('Chapters')
          .select('*')
          .eq('story_id', selectedStory.id)
          .order('chapter_number', { ascending: true });
        if (!error) setAllChapters(Chapters || []);
      })();
    }
  }, [saveChaptersuccess, selectedStory]);

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
    
    // CRITICAL: Complete state reset to prevent cross-story data contamination
    setAllChapters([]);
    setAvailableChoices([]);
    setShowChoices(false);
    setSelectedChoiceId(null);
    setChoicesError('');
    setChoiceHistory([]);
    setChoiceHistoryError('');
    setNextChapterText('');
    setCurrentChapterNumber(1);
    setStoryId(null);
    
    // Get the user's JWT token from AuthContext
    const token = session?.access_token;
    
    try {
      const headers = { 'Content-Type': 'application/json' };
      
      // Add auth header if user is logged in (for auto-save functionality)
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
      
      if (data.expanded_prompt) {
        setResult(data.expanded_prompt);
        
        // Store the JSON data for editing
        if (data.outline_json) {
          setOutlineJson(data.outline_json);
          // Populate editable characters and locations
          setEditableCharacters(data.characters || []);
          setEditableLocations(data.locations || []);
        }
        
        // Note: No auto-save anymore - user must manually save
        if (token) {
          setSaveSuccess('✨ Outline generated! You can edit character/location names and then save.');
        }
        
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
    setNextChapterText('');
    setCurrentChapterNumber(1);
    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ outline: result })
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

    if (!outlineJson) {
      setSaveOutlineError('No outline data to save.');
      return;
    }

    setSaveOutlineLoading(true);
    setSaveOutlineError('');

    try {
      // Update the outline JSON with edited characters and locations
      const updatedOutlineJson = {
        ...outlineJson,
        main_characters: editableCharacters,
        key_locations: editableLocations
      };

      // Generate updated formatted text (we'll use the original for now, but could regenerate)
      const formattedText = result; // Using existing formatted text

      const response = await fetch(createApiUrl(API_ENDPOINTS.SAVE_OUTLINE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          outline_json: updatedOutlineJson,
          formatted_text: formattedText
        })
      });

      const data = await response.json();

      if (data.success) {
        setOutlineSaved(true);
        setStoryId(data.story_id); // Store story ID for chapter generation
        // Update the displayed outline with the new character names
        if (data.updated_formatted_text) {
          setResult(data.updated_formatted_text);
        }
        setSaveSuccess(`✅ Outline saved as "${data.story_title}"! Generating Chapter 1...`);
        setSaveError(''); // Clear any previous errors

        // Immediately fetch Chapter 1 and its choices
        try {
          const chapterRes = await fetch(createApiUrl(`/story/${data.story_id}/Chapters`), {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${session.access_token}`
            }
          });
          const chapterData = await chapterRes.json();
          if (Array.isArray(chapterData) && chapterData.length > 0) {
            const chapter1 = chapterData.find(c => c.chapter_number === 1);
            if (chapter1) {
              setChapter(chapter1.content);
              setCurrentChapterNumber(1);
              // Fetch choices for Chapter 1
              const choicesRes = await fetch(createApiUrl(`/story/${data.story_id}/choice_history`), {
                method: 'GET',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${session.access_token}`
                }
              });
              const choicesData = await choicesRes.json();
              if (choicesData && choicesData.choice_history && choicesData.choice_history.length > 0) {
                const chapter1Choices = choicesData.choice_history.find(ch => ch.chapter_number === 1);
                if (chapter1Choices && chapter1Choices.choices) {
                  setAvailableChoices(chapter1Choices.choices);
                  setShowChoices(true);
                  setSelectedChoiceId(null);
                }
              }
            }
          }
        } catch (fetchErr) {
          setSaveError('Outline saved, but failed to fetch Chapter 1. Please refresh.');
        }
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

  // Delete story from Supabase (will cascade delete Chapters if FK is set to CASCADE)
  const handleDeleteStory = async (storyId) => {
    setDeleteLoading(true);
    setDeleteError('');
    const { error } = await supabase.from('Stories').delete().eq('id', storyId);
    if (error) {
      setDeleteError(error.message);
    } else {
      setSelectedStory(null);
      // Refresh Stories list
      setSavedStories((prev) => prev.filter((s) => s.id !== storyId));
    }
    setDeleteLoading(false);
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
    setNextChapterText('');
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
    setNextChapterText('');
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
      console.log('🚀 SAVED STORY CHOICE - Generating chapter for story:', selectedStory.id, 'choice:', choiceId);
      
      // Log complete choice data
      console.log('📊 CHOICE DATA BEING SENT:', {
        choiceId,
        selectedChoice,
        choiceIdType: typeof choiceId,
        selectedChoiceId: selectedChoice.id,
        selectedChoiceIdType: typeof selectedChoice.id,
        currentChapterNumber
      });

      // Calculate the correct next chapter number for saved Stories
      const nextChapterNumber = (allChapters?.length || 0) + 1;
      
      const requestBody = {
        story_id: selectedStory.id,
        choice_id: choiceId,
        choice_data: selectedChoice,
        next_chapter_num: nextChapterNumber,
        token: session.access_token
      };
      
      console.log('📊 SAVED STORY CHAPTER CALCULATION:', {
        allChaptersLength: allChapters?.length || 0,
        currentChapterNumber,
        calculatedNextChapterNumber: nextChapterNumber
      });

      console.log('📨 COMPLETE REQUEST BODY:', requestBody);

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

        // Set the new chapter content to display
        setNextChapterText(data.chapter_content);

        // Fetch the updated chapters list and update state
        const { data: Chapters, error } = await supabase
          .from('Chapters')
          .select('*')
          .eq('story_id', selectedStory.id)
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
        
        // Clear the preview text since it's now saved
        setNextChapterText('');
        
        // Refresh the Chapters list to show the new chapter
        const { data: Chapters, error } = await supabase
          .from('Chapters')
          .select('*')
          .eq('story_id', selectedStory.id)
          .order('chapter_number', { ascending: true });
        
        if (!error) {
          console.log('✅ Refreshed Chapters list, found', Chapters?.length || 0, 'Chapters');
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

  // Handler for saving a generated chapter (not chapter 1)
  const handleSaveChapter = async () => {
    setSaveChapterLoading(true);
    setSaveChaptersuccess('');
    setSaveChapterError('');
    
    // Get the user's JWT token from AuthContext
    const token = session?.access_token;
    
    try {
      const headers = { 'Content-Type': 'application/json' };
      
      // Add auth header for authenticated request
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      } else {
        setSaveChapterError('You must be logged in to save Chapters.');
        setSaveChapterLoading(false);
        return;
      }
      
      const response = await fetch(createApiUrl(API_ENDPOINTS.SAVE_CHAPTER), {
        method: 'POST',
        headers,
        body: JSON.stringify({
          story_id: selectedStory.id,
          chapter_number: currentChapterNumber,
          content: nextChapterText,
        }),
      });
      const data = await response.json();
      if (response.ok) {
        setSaveChaptersuccess('Chapter saved successfully!');
        setNextChapterText('');
        setCurrentChapterNumber(prev => prev + 1);
        
        // Auto-generate choices for the next chapter after saving
        setTimeout(() => {
          handleGenerateChoices(nextChapterText, currentChapterNumber);
        }, 1500);
      } else {
        setSaveChapterError(data.detail || 'Error saving chapter.');
      }
    } catch (err) {
      setSaveChapterError('Error connecting to backend.');
    } finally {
      setSaveChapterLoading(false);
    }
  };

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
      const response = await fetch(createApiUrl(`/story/${storyId}/choice_history`), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        }
      });

      const data = await response.json();

      if (data.success) {
        console.log('✅ Choice history fetched:', data.choice_history.length, 'Chapters');
        
        // CRITICAL FIX: Normalize choice IDs to ensure every choice has an 'id' field
        const normalizedChoiceHistory = data.choice_history.map(chapterHistory => ({
          ...chapterHistory,
          choices: chapterHistory.choices ? chapterHistory.choices.map(choice => ({
            ...choice,
            id: choice.id || choice.choice_id, // Ensure id field exists
            choice_id: choice.choice_id || choice.id // Maintain both for compatibility
          })) : []
        }));
        
        console.log('🔧 Choice history normalized:', normalizedChoiceHistory.map(ch => ({
          chapter: ch.chapter_number,
          choiceCount: ch.choices.length,
          choiceIds: ch.choices.map(c => c.id)
        })));
        
        setChoiceHistory(normalizedChoiceHistory);
        setChoiceHistoryError('');
      } else {
        const errorMsg = data.detail || 'Failed to fetch choice history';
        console.error('❌ Failed to fetch choice history:', errorMsg);
        setChoiceHistoryError(errorMsg);
        setChoiceHistory([]);
      }
    } catch (err) {
      console.error('❌ Error fetching choice history:', err);
      setChoiceHistoryError('Error connecting to server');
      setChoiceHistory([]);
    } finally {
      setChoiceHistoryLoading(false);
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
      logicReason: showNewChoices ? 'showNewChoices=true' : (selectedStory && isCurrentChapter) ? 'saved story + current chapter' : 'no match'
    });
    
    return (
      <div className={`relative ${isCurrentChapter ? 'ring-2 ring-blue-500' : ''}`}>
        {/* Chapter Content Card */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-white">
              📖 Chapter {chapter.chapter_number}
            </h3>
            {isCurrentChapter && (
              <span className="text-xs px-3 py-1 bg-blue-900/50 text-blue-300 rounded-full">
                Current
              </span>
            )}
          </div>
          
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
    console.log('🎭 RENDER PROGRESSION - allChapters:', allChapters?.length || 0, 'Chapters');
    console.log('🎭 RENDER PROGRESSION - selectedStory:', selectedStory?.id);
    
    if (!allChapters || allChapters.length === 0) {
      console.log('⚠️ RENDER PROGRESSION - No Chapters available');
      return (
        <div className="text-gray-400 text-center py-8">
          No Chapters available yet.
        </div>
      );
    }

    console.log('✅ RENDER PROGRESSION - Rendering', allChapters.length, 'Chapters');
    console.log('📚 RENDER PROGRESSION - Chapter titles:', allChapters.map(c => `Ch${c.chapter_number}: ${c.title || 'Untitled'}`));

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
        
        {/* Show generated next chapter if available */}
        {nextChapterText && (
          <div className="card">
            <h3 className="text-xl font-bold text-white mb-4">
              📖 Chapter {currentChapterNumber} (Preview)
            </h3>
            <div className="text-gray-200 whitespace-pre-wrap leading-relaxed mb-6">
              {nextChapterText}
            </div>
            <div className="flex flex-col items-center gap-3">
              <button
                onClick={handleSaveChapter}
                disabled={saveChapterLoading}
                className="btn-primary"
              >
                {saveChapterLoading ? 'Saving...' : 'Save Chapter'}
              </button>
              {saveChaptersuccess && (
                <div className="text-green-400 text-sm">{saveChaptersuccess}</div>
              )}
              {saveChapterError && (
                <div className="text-red-400 text-sm">{saveChapterError}</div>
              )}
            </div>
          </div>
        )}
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

  return (
    <div className="min-h-screen w-screen bg-black flex items-center justify-center relative">
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
                    renderStoryProgression()
                  )}

                  {/* Action Buttons */}
                  <div className="flex flex-col sm:flex-row gap-4 mt-8 pt-6 border-t border-gray-800">
                    {/* Only show Generate Choices button if the current chapter doesn't have choices already */}
                    {!nextChapterText && !showChoices && !choicesLoading && allChapters.length > 0 && (() => {
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
                    {/* Only show Try Different Choices if the current chapter has existing choices */}
                    {allChapters.length > 0 && (() => {
                      const currentChapter = allChapters[allChapters.length - 1];
                      const currentChapterChoices = choiceHistory.find(ch => ch.chapter_number === currentChapter?.chapter_number);
                      const hasExistingChoices = currentChapterChoices && currentChapterChoices.choices && currentChapterChoices.choices.length > 0;
                      
                      return hasExistingChoices;
                    })() && (
                      <button
                        className="btn-secondary"
                        onClick={handleGenerateChoicesForSavedStory}
                        disabled={choicesLoading}
                      >
                        {choicesLoading ? 'Generating...' : '🔄 Try Different Choices'}
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
                  {/* Editable Outline Display */}
                  <div className="card">
                    <h3 className="text-lg font-semibold text-white mb-4">
                      ✏️ Edit Your Outline
                    </h3>
                    <p className="text-gray-300 text-sm mb-4">
                      Click on character names to edit them directly!
                    </p>
                    
                    <div className="text-gray-200 leading-relaxed">
                      {/* Render the outline with inline editing for character names */}
                      {renderEditableOutline()}
                    </div>
                  </div>

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