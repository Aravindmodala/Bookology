// generator.jsx - Bookology Frontend Story Generator
//
// This file implements the main UI for generating, viewing, and saving stories in Bookology.
// It handles user input, calls backend API endpoints to generate outlines/chapters, and saves stories by POSTing to /stories/save.
// Data Flow:
// - User enters a story idea and generates an outline/chapter via backend endpoints.
// - When saving, the story and chapter 1 are sent to the backend, which handles chunking/embedding.
// - Saved stories and chapters are fetched from Supabase for display.
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
  const [saveChapterSuccess, setSaveChapterSuccess] = useState('');
  const [saveChapterError, setSaveChapterError] = useState('');
  const [allChapters, setAllChapters] = useState([]);
  const [fetchingChapters, setFetchingChapters] = useState(false);
  const [showChatbot, setShowChatbot] = useState(false);

  // Fetch saved stories and their first chapter from Supabase when switching to 'saved' tab
  useEffect(() => {
    const fetchStories = async () => {
      if (activeTab === 'saved' && user) {
        setFetchingStories(true);
        setFetchStoriesError('');
        // Fetch stories for this user
        const { data: stories, error: storiesError } = await supabase
          .from('Stories')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });
        if (storiesError) {
          setFetchStoriesError(storiesError.message);
          setFetchingStories(false);
          return;
        }
        // For each story, fetch its first chapter
        const storyIds = stories.map(s => s.id);
        let chapters = [];
        if (storyIds.length > 0) {
          const { data: chaptersData, error: chaptersError } = await supabase
            .from('Chapters')
            .select('*')
            .in('story_id', storyIds)
            .eq('chapter_number', 1);
          if (chaptersError) {
            setFetchStoriesError(chaptersError.message);
            setFetchingStories(false);
            return;
          }
          chapters = chaptersData;
        }
        // Merge stories and their first chapter
        const merged = stories.map(story => {
          const chapter1 = chapters.find(c => c.story_id === story.id && c.chapter_number === 1);
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

  // Fetch all chapters for the selected story when modal opens
  useEffect(() => {
    const fetchChapters = async () => {
      if (selectedStory) {
        setFetchingChapters(true);
        const { data: chapters, error } = await supabase
          .from('Chapters')
          .select('*')
          .eq('story_id', selectedStory.id)
          .order('chapter_number', { ascending: true });
        if (!error) setAllChapters(chapters || []);
        else setAllChapters([]);
        setFetchingChapters(false);
      }
    };
    fetchChapters();
  }, [selectedStory]);

  // Reset state when switching stories or chapters
  useEffect(() => {
    if (selectedStory) {
      setNextChapterText('');
      setSaveChapterSuccess('');
      setSaveChapterError('');
      setCurrentChapterNumber(allChapters.length + 1);
    }
  }, [selectedStory, allChapters]);

  // After saving a chapter, refresh the chapter list
  useEffect(() => {
    if (selectedStory && saveChapterSuccess) {
      // Re-fetch chapters after a successful save
      (async () => {
        const { data: chapters, error } = await supabase
          .from('Chapters')
          .select('*')
          .eq('story_id', selectedStory.id)
          .order('chapter_number', { ascending: true });
        if (!error) setAllChapters(chapters || []);
      })();
    }
  }, [saveChapterSuccess, selectedStory]);

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setResult('');
    setChapter('');
    setSaveSuccess('');
    setSaveError('');
    
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
        
        // Handle auto-save feedback
        if (data.auto_saved) {
          setSaveSuccess('✅ Outline auto-saved! You can continue generating chapters.');
          if (data.story_id) {
            setStoryId(data.story_id);
          }
        } else if (token) {
          // User was authenticated but save failed
          setSaveError('⚠️ Outline generated but auto-save failed. You can still save manually later.');
        }
        // If no token, user is anonymous - no save message needed
        
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
    setChapterLoading(true);
    setError('');
    setSaveSuccess('');
    setSaveError('');
    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ outline: result })
      });
      const data = await response.json();
      if (data.chapter_1) {
        setChapter(data.chapter_1);
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

  // Save story to Supabase (Stories + Chapters)
  const handleSaveStory = async () => {
    setSaveLoading(true);
    setSaveError('');
    setSaveSuccess('');
    if (!user) {
      setSaveError('You must be logged in to save stories.');
      setSaveLoading(false);
      return;
    }

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
        }),
      });
      const data = await response.json();
      if (response.ok) {
        setSaveSuccess('Story saved successfully!');
        setStoryId(data.story_id);
      } else {
        setSaveError(data.detail || 'Error saving story.');
      }
    } catch (err) {
      setSaveError('Error connecting to backend.');
    } finally {
      setSaveLoading(false);
    }
  };

  // Delete story from Supabase (will cascade delete chapters if FK is set to CASCADE)
  const handleDeleteStory = async (storyId) => {
    setDeleteLoading(true);
    setDeleteError('');
    const { error } = await supabase.from('Stories').delete().eq('id', storyId);
    if (error) {
      setDeleteError(error.message);
    } else {
      setSelectedStory(null);
      // Refresh stories list
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
          // Optionally, send previous chapters for more context
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
  };

  // Helper to count chapters in outline
  function getTotalChaptersFromOutline(outline) {
    if (!outline) return 0;
    const matches = outline.match(/Chapter\s+\d+/g);
    return matches ? matches.length : 0;
  }

  const totalChapters = selectedStory ? getTotalChaptersFromOutline(selectedStory.story_outline) : 0;

  // Handler for "Generate Next Chapter"
  const handleGenerateNextChapter = async () => {
    setNextChapterLoading(true);
    setNextChapterError('');
    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_NEXT_CHAPTER), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          story_id: selectedStory.id,
          chapter_number: currentChapterNumber,
          story_outline: selectedStory.story_outline,
        }),
      });
      const data = await response.json();
      if (response.ok) {
        setNextChapterText(data.chapter);
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
    setSaveChapterSuccess('');
    setSaveChapterError('');
    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.SAVE_CHAPTER), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          story_id: selectedStory.id,
          chapter_number: currentChapterNumber,
          content: nextChapterText,
        }),
      });
      const data = await response.json();
      if (response.ok) {
        setSaveChapterSuccess('Chapter saved successfully!');
        setNextChapterText('');
        setCurrentChapterNumber(prev => prev + 1);
      } else {
        setSaveChapterError(data.detail || 'Error saving chapter.');
      }
    } catch (err) {
      setSaveChapterError('Error connecting to backend.');
    } finally {
      setSaveChapterLoading(false);
    }
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

                  {/* Chapters */}
                  <div className="space-y-6">
                    {allChapters.map(chap => (
                      <div key={chap.chapter_number} className="card">
                        <h4 className="text-lg font-semibold text-white mb-4">
                          Chapter {chap.chapter_number}
                        </h4>
                        <div className="text-gray-200 whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto scrollbar-thin">
                          {chap.content}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-col sm:flex-row gap-4 mt-8 pt-6 border-t border-gray-800">
                    {!nextChapterText && currentChapterNumber <= totalChapters && (
                      <button
                        className="btn-primary flex-1"
                        onClick={handleGenerateNextChapter}
                        disabled={nextChapterLoading}
                      >
                        {nextChapterLoading ? 'Generating...' : `Generate Chapter ${currentChapterNumber}`}
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

                  {/* Show generated next chapter if available */}
                  {nextChapterText && (
                    <div className="card mt-6">
                      <h4 className="text-xl font-bold text-white mb-4">
                        Chapter {currentChapterNumber}
                      </h4>
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
                        {saveChapterSuccess && (
                          <div className="text-green-400 text-sm">{saveChapterSuccess}</div>
                        )}
                        {saveChapterError && (
                          <div className="text-red-400 text-sm">{saveChapterError}</div>
                        )}
                      </div>
                    </div>
                  )}

                  {nextChapterError && (
                    <div className="text-red-400 text-sm mt-4">{nextChapterError}</div>
                  )}
                  {deleteError && (
                    <div className="text-red-400 text-sm mt-4">{deleteError}</div>
                  )}

                  <div className="text-xs text-gray-500 mt-6 text-center border-t border-gray-800 pt-4">
                    Created on {new Date(selectedStory.created_at).toLocaleString()}
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
                <p className="text-gray-400">Transform your ideas into compelling stories</p>
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
                  <div className="card">
                    <h3 className="text-lg font-semibold text-white mb-4">Generated Outline</h3>
                    <div className="text-gray-200 whitespace-pre-wrap leading-relaxed">
                      {result}
                    </div>
                  </div>

                  <div className="text-center">
                    <p className="text-gray-300 font-medium mb-4">
                      How does this look? Ready to continue?
                    </p>
                    <div className="flex gap-4 justify-center">
                      <button 
                        onClick={handleLike} 
                        disabled={chapterLoading}
                        className="btn-primary"
                      >
                        Continue with Chapter 1
                      </button>
                      <button 
                        onClick={handleDislike} 
                        disabled={loading}
                        className="btn-secondary"
                      >
                        Generate New Outline
                      </button>
                    </div>
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

              {chapter && (
                <div className="card mt-6">
                  <h3 className="text-xl font-bold text-white mb-4">Chapter 1</h3>
                  <div className="text-gray-200 whitespace-pre-wrap leading-relaxed mb-6">
                    {chapter}
                  </div>
                  <div className="text-center">
                    <button
                      onClick={handleSaveStory}
                      disabled={saveLoading}
                      className="btn-primary"
                    >
                      {saveLoading ? 'Saving...' : 'Save Complete Story'}
                    </button>
                    {saveError && (
                      <div className="text-red-400 text-sm mt-3">{saveError}</div>
                    )}
                    {saveSuccess && (
                      <div className="text-green-400 text-sm mt-3">{saveSuccess}</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-white mb-2">Your Stories</h2>
                <p className="text-gray-400">Manage and explore your saved stories</p>
              </div>

              {fetchingStories ? (
                <div className="text-center py-12">
                  <div className="text-gray-300">Loading your stories...</div>
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
                  <div className="text-gray-400 mb-4">No saved stories yet</div>
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
                      onClick={() => setSelectedStory(story)}
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