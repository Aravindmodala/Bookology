import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, BookOpen, Wand2, Save, RefreshCw, Sparkles, PenTool, Brain, Zap } from 'lucide-react';
import { useAuth } from './AuthContext';
import { createApiUrl, API_ENDPOINTS } from './config';

const StoryCreator = () => {
  const navigate = useNavigate();
  const { user, session } = useAuth();

  // Flow state
  const [selectedFlow, setSelectedFlow] = useState(null); // 'ai' or 'manual'
  const [recentIdeas, setRecentIdeas] = useState([]);

  // Form state
  const [idea, setIdea] = useState('');
  // Removed format toggle (book/movie) per request

  // Generation state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState('');

  // Outline state
  const [storyTitle, setStoryTitle] = useState('');
  const [storyGenre, setStoryGenre] = useState('');
  const [storyTone, setStoryTone] = useState('');
  const [chapterTitles, setChapterTitles] = useState([]);
  const [mainCharacters, setMainCharacters] = useState([]);
  const [keyLocations, setKeyLocations] = useState([]);
  const [outlineSaved, setOutlineSaved] = useState(false);
  const [saveOutlineLoading, setSaveOutlineLoading] = useState(false);
  const [saveOutlineError, setSaveOutlineError] = useState('');
  const [storyId, setStoryId] = useState(null);

  // Success state
  const [saveSuccess, setSaveSuccess] = useState('');

  // Load recent ideas from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('bookology_recent_ideas');
    if (saved) {
      try {
        setRecentIdeas(JSON.parse(saved));
      } catch (e) {
        console.warn('Failed to load recent ideas:', e);
      }
    }
  }, []);

  // Save idea to recent ideas
  const saveIdeaToRecent = (newIdea) => {
    if (!newIdea.trim()) return;
    
    const updated = [newIdea, ...recentIdeas.filter(idea => idea !== newIdea)].slice(0, 5);
    setRecentIdeas(updated);
    localStorage.setItem('bookology_recent_ideas', JSON.stringify(updated));
  };

  // Handle flow selection
  const handleFlowSelection = (flow) => {
    setSelectedFlow(flow);
    // Cache user preference
    localStorage.setItem('bookology_preferred_flow', flow);
  };

  // Handle manual story creation
  const handleManualStory = async () => {
    if (!user || !session?.access_token) {
      setError('Please log in to create a story.');
      return;
    }

    try {
      setLoading(true);
      
      // Create a new blank story
      const response = await fetch(createApiUrl(API_ENDPOINTS.SAVE_OUTLINE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          summary: 'This is a blank story ready for your creativity. You can start writing from scratch and let your imagination flow freely. The story will develop as you write, and you can always use AI assistance later if you need help with suggestions or continuing your story.',
          genre: 'Fiction',
          tone: 'Creative',
          title: 'Untitled Story',
          chapters: [{ chapter_number: 1, title: 'Chapter 1' }],
          reflection: '',
          is_optimized: false,
          main_characters: [],
          key_locations: []
        })
      });

      const data = await response.json();

      if (data.success) {
        // Navigate directly to editor with blank story
        navigate('/editor', { 
          state: { 
            story: {
              id: data.story_id,
              story_title: 'Untitled Story',
              story_outline: 'A blank story ready for your creativity.',
              genre: 'Fiction',
              tone: 'Creative',
              chapter_titles: ['Chapter 1'],
              created_at: new Date().toISOString()
            },
            mode: 'manual_creation' // Tell editor this is a manual story
          } 
        });
      } else {
        throw new Error(data.detail || 'Failed to create story');
      }
    } catch (err) {
      setError('Failed to create story: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Generate story outline
  const handleGenerate = async () => {
    if (!idea.trim()) {
      setError('Please enter a story idea');
      return;
    }

    setLoading(true);
    setError('');
    setResult('');
    setSaveSuccess('');
    setOutlineSaved(false);
    setSaveOutlineError('');
    setStoryId(null);
    setStoryGenre('');
    setStoryTone('');
    setChapterTitles([]);
    setStoryTitle('');

    // Save idea to recent
    saveIdeaToRecent(idea);

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

      if (data.summary) {
        setResult(data.summary);
        
        // Set story title
        if (data.title) {
          setStoryTitle(data.title);
        } else {
          const firstSentence = data.summary.split('.')[0];
          const autoTitle = firstSentence.length > 50 ? firstSentence.substring(0, 50) + '...' : firstSentence;
          setStoryTitle(autoTitle);
        }
        
        // Set additional details
        if (data.genre) setStoryGenre(data.genre);
        if (data.tone) setStoryTone(data.tone);
        if (data.chapters && Array.isArray(data.chapters)) {
          const titles = data.chapters.map(chapter => 
            chapter.title || chapter.chapter_title || `Chapter ${chapter.chapter_number}`
          );
          setChapterTitles(titles);
        }
        
        // 🔧 STORE CHARACTERS AND LOCATIONS FROM API RESPONSE
        if (data.main_characters && Array.isArray(data.main_characters)) {
          setMainCharacters(data.main_characters);
          console.log('📊 Frontend received main_characters:', data.main_characters);
        }
        if (data.key_locations && Array.isArray(data.key_locations)) {
          setKeyLocations(data.key_locations);
          console.log('📊 Frontend received key_locations:', data.key_locations);
        }

        setSaveSuccess('✨ Outline generated! Edit the title below and save to continue.');
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

  // Save outline
  const handleSaveOutline = async () => {
    if (!user || !session?.access_token) {
      setSaveOutlineError('Please log in to save your outline.');
      return;
    }

    if (!result) {
      setSaveOutlineError('No outline data to save.');
      return;
    }

    setSaveOutlineLoading(true);
    setSaveOutlineError('');

    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.SAVE_OUTLINE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          summary: result,
          genre: storyGenre,
          tone: storyTone,
          title: storyTitle,
          chapters: chapterTitles.map((title, index) => ({
            chapter_number: index + 1,
            title: title
          })),
          reflection: '',
          is_optimized: true,
          main_characters: mainCharacters, // 🔧 ADD MISSING FIELD
          key_locations: keyLocations      // 🔧 ADD MISSING FIELD
        })
      });

      const data = await response.json();

      if (data.success) {
        setOutlineSaved(true);
        setStoryId(data.story_id);
        setSaveSuccess(`✅ Outline saved as "${data.story_title}"! Now you can generate Chapter 1.`);
        setSaveOutlineError('');
      } else {
        setSaveOutlineError(data.detail || 'Failed to save outline');
      }
    } catch (err) {
      setSaveOutlineError('Error connecting to server');
    } finally {
      setSaveOutlineLoading(false);
    }
  };

  // Navigate to StoryEditor for Chapter 1 generation
  const handleGenerateChapter = () => {
    if (!outlineSaved || !storyId) {
      setError('Please save your outline first.');
      return;
    }

    // Navigate to StoryEditor with the story data
    navigate('/editor', { 
      state: { 
        story: {
          id: storyId,
          story_title: storyTitle,
          story_outline: result,
          genre: storyGenre,
          tone: storyTone,
          chapter_titles: chapterTitles,
          created_at: new Date().toISOString()
        },
        mode: 'generate_chapter_1' // Tell editor to start with Chapter 1 generation
      } 
    });
  };

  // Reset form
  const handleReset = () => {
    setSelectedFlow(null);
    setIdea('');
    setResult('');
    setStoryTitle('');
    setStoryGenre('');
    setStoryTone('');
    setChapterTitles([]);
    setOutlineSaved(false);
    setStoryId(null);
    setError('');
    setSaveSuccess('');
    setSaveOutlineError('');
  };

  // Flow Selection Screen
  if (!selectedFlow) {
    return (
      <div className="deep-space starfield text-off">
        {/* Glow layers */}
        <div className="glow glow-violet" />
        <div className="glow glow-cyan" />

        <div className="container py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/stories')}
                className="flex items-center space-x-2 text-off-70 hover:text-off transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Stories</span>
              </button>
            </div>
            
            <button
              onClick={handleReset}
              className="flex items-center space-x-2 text-off-70 hover:text-off transition-colors"
            >
              <RefreshCw className="w-5 h-5" />
              <span>Start Over</span>
            </button>
          </div>

          <div className="max-w-6xl mx-auto">
            {/* Main Content */}
            <div className="text-center mb-12">
              <h1 className="font-sora text-4xl font-bold text-off mb-4">Create Your Story</h1>
              <p className="text-off-70 text-xl">Choose how you'd like to start your creative journey</p>
            </div>

            {/* Flow Selection Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {/* Start with AI */}
              <div 
                onClick={() => handleFlowSelection('ai')}
                className="card-soft rounded-2xl p-8 transition-all duration-300 hover:scale-105 hover:border-white/20 cursor-pointer group"
              >
                <div className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-r from-violet-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
                    <Sparkles className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-off mb-4">Start with AI</h3>
                  <p className="text-off-70 mb-6">
                    Let AI help you develop your story idea into a compelling outline. Perfect for when you have a concept but need help expanding it.
                  </p>
                  <div className="flex items-center justify-center space-x-2 text-violet-300">
                    <Brain className="w-4 h-4" />
                    <span className="text-sm">AI-powered story development</span>
                  </div>
                </div>
              </div>

              {/* Write My Own Story */}
              <div 
                onClick={() => handleFlowSelection('manual')}
                className="card-soft rounded-2xl p-8 transition-all duration-300 hover:scale-105 hover:border-white/20 cursor-pointer group"
              >
                <div className="text-center">
                  <div className="w-16 h-16 bg-gradient-to-r from-cyan-500 to-teal-500 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
                    <PenTool className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-off mb-4">Write My Own Story</h3>
                  <p className="text-off-70 mb-6">
                    Start with a blank canvas and let your creativity flow. You have full control over every aspect of your story.
                  </p>
                  <div className="flex items-center justify-center space-x-2 text-cyan-300">
                    <Zap className="w-4 h-4" />
                    <span className="text-sm">Complete creative freedom</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Ideas */}
            {recentIdeas.length > 0 && (
              <div className="mt-12 max-w-4xl mx-auto">
                <h3 className="text-lg font-semibold text-off mb-4">Recent Ideas</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {recentIdeas.map((idea, index) => (
                    <div 
                      key={index}
                      onClick={() => {
                        setIdea(idea);
                        handleFlowSelection('ai');
                      }}
                      className="card-soft rounded-lg p-4 transition-all cursor-pointer hover:scale-105 hover:border-white/20"
                    >
                      <p className="text-off-70 text-sm line-clamp-2">{idea}</p>
                      <p className="text-off-60 text-xs mt-2">Click to use with AI</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // AI Flow - Original form
  if (selectedFlow === 'ai') {
    return (
      <div className="deep-space starfield text-off">
        {/* Glow layers */}
        <div className="glow glow-violet" />
        <div className="glow glow-cyan" />

        <div className="container py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSelectedFlow(null)}
                className="flex items-center space-x-2 text-off-70 hover:text-off transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Options</span>
              </button>
            </div>
            
            <button
              onClick={handleReset}
              className="flex items-center space-x-2 text-off-70 hover:text-off transition-colors"
            >
              <RefreshCw className="w-5 h-5" />
              <span>Start Over</span>
            </button>
          </div>

          <div className="max-w-4xl mx-auto">
            {/* Main Content */}
            <div className="card-soft p-8">
              <div className="text-center mb-8">
                <div className="flex items-center justify-center space-x-3 mb-4">
                  <Sparkles className="w-8 h-8 text-violet-400" />
                  <h1 className="font-sora text-4xl font-bold text-off">Start with AI</h1>
                </div>
                <p className="text-off-70">Transform your ideas into compelling narratives with AI assistance</p>
              </div>

              {/* Step 1: Story Idea */}
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-off-80 mb-3">
                    What's your story idea?
                  </label>
                  <textarea
                    placeholder="Enter your story idea... Be as detailed or brief as you like!"
                    value={idea}
                    onChange={e => setIdea(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-off placeholder-off-60 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 resize-none"
                    rows={4}
                  />
                </div>

                {/* Format selector removed */}

                {/* Generate Button */}
                <div className="text-center pt-6">
                  <button
                    onClick={handleGenerate}
                    disabled={loading || !idea.trim()}
                    className="btn-violet disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed disabled:hover:scale-100 px-8 py-4 text-lg flex items-center space-x-3 mx-auto"
                  >
                    {loading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Generating...</span>
                      </>
                    ) : (
                      <>
                        <Wand2 className="w-5 h-5" />
                        <span>Generate Story Outline</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Error Display */}
                {error && (
                  <div className="text-center">
                    <div className="text-red-400 text-sm p-3 bg-red-900/20 border border-red-800 rounded-lg">
                      {error}
                    </div>
                  </div>
                )}
              </div>

              {/* Generated Result */}
                {result && (
                <div className="mt-8 space-y-6">
                  <hr className="border-white/10" />
                  
                  {/* Story Title */}
                  <div>
                    <h3 className="text-lg font-semibold text-off mb-4">📖 Story Title</h3>
                    <input
                      type="text"
                      value={storyTitle}
                      onChange={(e) => setStoryTitle(e.target.value)}
                      placeholder="Enter your story title..."
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-off placeholder-off-60 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500"
                      maxLength={100}
                    />
                      <p className="text-off-60 text-xs mt-2">{storyTitle.length}/100 characters</p>
                  </div>

                  {/* Story Details */}
                  {(storyGenre || storyTone || chapterTitles.length > 0) && (
                    <div>
                        <h3 className="text-lg font-semibold text-off mb-4">📋 Story Details</h3>
                        <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-3">
                        {storyGenre && (
                          <div>
                              <span className="text-sm font-medium text-off-80">Genre:</span>
                              <span className="ml-2 px-3 py-1 bg-violet-600 text-white text-sm rounded-full">
                              {storyGenre}
                            </span>
                          </div>
                        )}
                        {storyTone && (
                          <div>
                              <span className="text-sm font-medium text-off-80">Tone:</span>
                              <span className="ml-2 px-3 py-1 bg-violet-600 text-white text-sm rounded-full">
                              {storyTone}
                            </span>
                          </div>
                        )}
                        {chapterTitles.length > 0 && (
                          <div>
                              <span className="text-sm font-medium text-off-80 block mb-2">
                              Chapter Breakdown ({chapterTitles.length} chapters):
                            </span>
                            <div className="space-y-1">
                              {chapterTitles.map((title, index) => (
                                  <div key={index} className="flex items-center text-off-80">
                                    <span className="text-violet-400 font-mono text-sm w-8">{index + 1}.</span>
                                  <span className="text-sm">{title}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Story Outline */}
                  <div>
                      <h3 className="text-lg font-semibold text-off mb-4">📝 Story Outline</h3>
                      <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                        <p className="text-off-80 leading-relaxed whitespace-pre-wrap">{result}</p>
                    </div>
                  </div>

                  {/* Save Outline */}
                  {!outlineSaved ? (
                    <div className="text-center">
                      <button 
                        onClick={handleSaveOutline} 
                        disabled={saveOutlineLoading || !user}
                        className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-200 hover:scale-105 flex items-center space-x-2 mx-auto disabled:cursor-not-allowed disabled:hover:scale-100"
                      >
                        <Save className="w-5 h-5" />
                        <span>{saveOutlineLoading ? 'Saving...' : 'Save Outline & Continue'}</span>
                      </button>
                      {!user && (
                        <p className="text-yellow-400 text-sm mt-2">Please log in to save your outline.</p>
                      )}
                      {saveOutlineError && (
                        <div className="text-red-400 text-sm mt-3 p-3 bg-red-900/20 border border-red-800 rounded-lg">
                          {saveOutlineError}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center">
                      <p className="text-green-400 font-medium mb-4">✅ Outline saved! Ready to start writing your story.</p>
                      <button 
                        onClick={handleGenerateChapter} 
                        className="btn-violet px-6 py-3 text-lg flex items-center space-x-2 mx-auto"
                      >
                        <BookOpen className="w-5 h-5" />
                        <span>Generate Chapter 1</span>
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Success Messages */}
              {saveSuccess && (
                <div className="mt-6 text-center">
                  <div className="text-green-400 text-sm p-3 bg-green-900/20 border border-green-800 rounded-lg">
                    {saveSuccess}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Manual Flow - Direct to editor
  if (selectedFlow === 'manual') {
    return (
      <div className="deep-space starfield text-off">
        {/* Glow layers */}
        <div className="glow glow-violet" />
        <div className="glow glow-cyan" />

        <div className="container py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSelectedFlow(null)}
                className="flex items-center space-x-2 text-off-70 hover:text-off transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Options</span>
              </button>
            </div>
            
            <button
              onClick={handleReset}
              className="flex items-center space-x-2 text-off-70 hover:text-off transition-colors"
            >
              <RefreshCw className="w-5 h-5" />
              <span>Start Over</span>
            </button>
          </div>

          <div className="max-w-4xl mx-auto">
            {/* Main Content */}
            <div className="card-soft p-8">
              <div className="text-center mb-8">
                <div className="flex items-center justify-center space-x-3 mb-4">
                  <PenTool className="w-8 h-8 text-cyan-400" />
                  <h1 className="font-sora text-4xl font-bold text-off">Write My Own Story</h1>
                </div>
                <p className="text-off-70">Start with a blank canvas and let your creativity flow</p>
              </div>

              <div className="text-center space-y-6">
                <div className="card-soft p-8">
                  <div className="w-16 h-16 bg-gradient-to-r from-cyan-500 to-teal-500 rounded-full flex items-center justify-center mx-auto mb-6">
                    <PenTool className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-off mb-4">Ready to Create?</h3>
                  <p className="text-off-70 mb-6">
                    You'll start with a blank story and can write freely. You can always use AI assistance later if you need help with suggestions or continuing your story.
                  </p>
                  <button
                    onClick={handleManualStory}
                    disabled={loading}
                    className="btn-violet px-8 py-4 text-lg flex items-center space-x-3 mx-auto disabled:cursor-not-allowed disabled:hover:scale-100"
                  >
                    {loading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Creating...</span>
                      </>
                    ) : (
                      <>
                        <BookOpen className="w-5 h-5" />
                        <span>Start Writing</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Error Display */}
                {error && (
                  <div className="text-center">
                    <div className="text-red-400 text-sm p-3 bg-red-900/20 border border-red-800 rounded-lg">
                      {error}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default StoryCreator;