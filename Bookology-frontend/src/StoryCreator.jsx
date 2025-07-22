import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, BookOpen, Film, Wand2, Save, RefreshCw } from 'lucide-react';
import { useAuth } from './AuthContext';
import { createApiUrl, API_ENDPOINTS } from './config';

const StoryCreator = () => {
  const navigate = useNavigate();
  const { user, session } = useAuth();

  // Form state
  const [idea, setIdea] = useState('');
  const [format, setFormat] = useState('book');

  // Generation state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState('');

  // Outline state
  const [storyTitle, setStoryTitle] = useState('');
  const [storyGenre, setStoryGenre] = useState('');
  const [storyTone, setStoryTone] = useState('');
  const [chapterTitles, setChapterTitles] = useState([]);
  const [outlineSaved, setOutlineSaved] = useState(false);
  const [saveOutlineLoading, setSaveOutlineLoading] = useState(false);
  const [saveOutlineError, setSaveOutlineError] = useState('');
  const [storyId, setStoryId] = useState(null);

  // Success state
  const [saveSuccess, setSaveSuccess] = useState('');

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
          is_optimized: true
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

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/stories')}
              className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back to Stories</span>
            </button>
          </div>
          
          <button
            onClick={handleReset}
            className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
          >
            <RefreshCw className="w-5 h-5" />
            <span>Start Over</span>
          </button>
        </div>

        <div className="max-w-4xl mx-auto">
          {/* Main Content */}
          <div className="bg-gray-900 rounded-xl p-8 border border-gray-800">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-2">Create Your Story</h1>
              <p className="text-gray-400">Transform your ideas into compelling narratives</p>
            </div>

            {/* Step 1: Story Idea */}
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  What's your story idea?
                </label>
                <textarea
                  placeholder="Enter your story idea... Be as detailed or brief as you like!"
                  value={idea}
                  onChange={e => setIdea(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none"
                  rows={4}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  Format
                </label>
                <div className="flex space-x-4">
                  <label className="flex items-center cursor-pointer group">
                    <input
                      type="radio"
                      name="format"
                      value="book"
                      checked={format === 'book'}
                      onChange={() => setFormat('book')}
                      className="w-4 h-4 text-blue-600 bg-gray-800 border-gray-600 focus:ring-blue-500"
                    />
                    <BookOpen className="w-5 h-5 ml-3 mr-2 text-gray-400 group-hover:text-white" />
                    <span className="text-gray-200 group-hover:text-white transition-colors">
                      Book
                    </span>
                  </label>
                  <label className="flex items-center cursor-pointer group">
                    <input
                      type="radio"
                      name="format"
                      value="movie"
                      checked={format === 'movie'}
                      onChange={() => setFormat('movie')}
                      className="w-4 h-4 text-blue-600 bg-gray-800 border-gray-600 focus:ring-blue-500"
                    />
                    <Film className="w-5 h-5 ml-3 mr-2 text-gray-400 group-hover:text-white" />
                    <span className="text-gray-200 group-hover:text-white transition-colors">
                      Movie
                    </span>
                  </label>
                </div>
              </div>

              <button
                onClick={handleGenerate}
                disabled={loading || !idea.trim()}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-200 hover:scale-105 flex items-center justify-center space-x-2 shadow-lg disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                <Wand2 className="w-5 h-5" />
                <span>{loading ? 'Generating Outline...' : 'Generate Story Outline'}</span>
              </button>

              {error && (
                <div className="text-red-400 text-sm p-3 bg-red-900/20 border border-red-800 rounded-lg">
                  {error}
                </div>
              )}
            </div>

            {/* Step 2: Generated Outline */}
            {result && (
              <div className="mt-8 space-y-6">
                <hr className="border-gray-700" />
                
                {/* Story Title */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">📖 Story Title</h3>
                  <input
                    type="text"
                    value={storyTitle}
                    onChange={(e) => setStoryTitle(e.target.value)}
                    placeholder="Enter your story title..."
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    maxLength={100}
                  />
                  <p className="text-gray-400 text-xs mt-2">{storyTitle.length}/100 characters</p>
                </div>

                {/* Story Details */}
                {(storyGenre || storyTone || chapterTitles.length > 0) && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">📋 Story Details</h3>
                    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-3">
                      {storyGenre && (
                        <div>
                          <span className="text-sm font-medium text-gray-300">Genre:</span>
                          <span className="ml-2 px-3 py-1 bg-blue-600 text-white text-sm rounded-full">
                            {storyGenre}
                          </span>
                        </div>
                      )}
                      {storyTone && (
                        <div>
                          <span className="text-sm font-medium text-gray-300">Tone:</span>
                          <span className="ml-2 px-3 py-1 bg-purple-600 text-white text-sm rounded-full">
                            {storyTone}
                          </span>
                        </div>
                      )}
                      {chapterTitles.length > 0 && (
                        <div>
                          <span className="text-sm font-medium text-gray-300 block mb-2">
                            Chapter Breakdown ({chapterTitles.length} chapters):
                          </span>
                          <div className="space-y-1">
                            {chapterTitles.map((title, index) => (
                              <div key={index} className="flex items-center text-gray-200">
                                <span className="text-blue-400 font-mono text-sm w-8">{index + 1}.</span>
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
                  <h3 className="text-lg font-semibold text-white mb-4">📝 Story Outline</h3>
                  <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                    <p className="text-gray-200 leading-relaxed whitespace-pre-wrap">{result}</p>
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
                      className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-200 hover:scale-105 flex items-center space-x-2 mx-auto"
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
};

export default StoryCreator;