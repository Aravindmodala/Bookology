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

export default function Generator() {
  const { user } = useAuth();
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

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setResult('');
    setChapter('');
    setSaveSuccess('');
    setSaveError('');
    try {
      const response = await fetch('http://127.0.0.1:8000/lc_generate_outline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea })
      });
      const data = await response.json();
      if (data.expanded_prompt) {
        setResult(data.expanded_prompt);
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
      const response = await fetch('http://127.0.0.1:8000/lc_generate_chapter', {
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

    // Get the user's JWT token from Supabase Auth
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

    try {
      const response = await fetch('http://localhost:8000/stories/save', {
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
      const response = await fetch('http://localhost:8000/lc_generate_chapter', {
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
  const closeModal = () => setSelectedStory(null);

  return (
    <div className="min-h-screen w-screen bg-black flex items-center justify-center relative">
      {/* Modal for viewing full story - render at root level for proper overlay */}
      {selectedStory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <div className="bg-[#18181b] rounded-3xl shadow-2xl p-8 max-w-2xl w-full border border-white/20 relative flex flex-col max-h-[90vh] overflow-y-auto">
            <button
              className="absolute top-4 right-4 text-white text-3xl font-bold hover:text-red-400 bg-black/40 rounded-full w-10 h-10 flex items-center justify-center transition"
              onClick={closeModal}
              aria-label="Close"
            >
              &times;
            </button>
            <h2 className="text-3xl font-bold text-white mb-4 text-center break-words">{selectedStory.story_title}</h2>
            <div className="mb-6">
              <div className="text-white/70 mb-2 font-semibold">Outline:</div>
              <div className="text-white/80 whitespace-pre-wrap mb-6 bg-black/30 p-4 rounded-xl border border-white/10 max-h-40 overflow-y-auto">{selectedStory.story_outline}</div>
              <div className="text-white/70 mb-2 font-semibold">Chapter 1:</div>
              <div className="text-white/80 whitespace-pre-wrap bg-black/30 p-4 rounded-xl border border-white/10 max-h-60 overflow-y-auto">{selectedStory.chapter_1_content}</div>
            </div>
            <div className="flex flex-col items-center gap-2 mt-2">
              <button
                className="px-6 py-2 rounded-full bg-red-600/80 text-white font-bold shadow hover:bg-red-700 transition-all border border-red-500"
                onClick={() => handleDeleteStory(selectedStory.id)}
                disabled={deleteLoading}
              >
                {deleteLoading ? 'Deleting...' : 'Delete Story'}
              </button>
              <button
                className="px-6 py-2 rounded-full bg-blue-600/80 text-white font-bold shadow hover:bg-blue-700 transition-all border border-blue-500"
                onClick={() => handleContinueStory(selectedStory)}
                disabled={chapterLoading}
              >
                {chapterLoading ? 'Generating...' : 'Generate Next Chapter'}
              </button>
              {deleteError && <div className="text-red-400 text-center">{deleteError}</div>}
            </div>
            <div className="text-xs text-white/40 mt-2 text-center">Saved on {new Date(selectedStory.created_at).toLocaleString()}</div>
          </div>
        </div>
      )}
      <div className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl p-10 w-full max-w-md border border-white/20 flex flex-col items-center">
        {/* Toggle Switch */}
        <div className="flex w-full mb-8">
          <button
            className={`flex-1 py-2 rounded-l-full font-bold ${activeTab === 'generate' ? 'bg-white/30 text-black' : 'bg-black/40 text-white'} transition`}
            onClick={() => setActiveTab('generate')}
          >
            Generate a Story
          </button>
          <button
            className={`flex-1 py-2 rounded-r-full font-bold ${activeTab === 'saved' ? 'bg-white/30 text-black' : 'bg-black/40 text-white'} transition`}
            onClick={() => setActiveTab('saved')}
          >
            Saved Stories
          </button>
        </div>

        {activeTab === 'generate' ? (
          <>
            <h1 className="text-4xl font-serif font-bold text-white mb-8">Story Generator</h1>
            <input
              type="text"
              placeholder="Enter your story idea..."
              value={idea}
              onChange={e => setIdea(e.target.value)}
              className="w-full mb-6 px-4 py-3 rounded-lg bg-black/40 text-white placeholder-white/60 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/30"
            />
            <div className="flex gap-6 mb-6">
              <label className="flex items-center text-white/80 cursor-pointer">
                <input
                  type="radio"
                  name="format"
                  value="book"
                  checked={format === 'book'}
                  onChange={() => setFormat('book')}
                  className="accent-white mr-2"
                />
                Book
              </label>
              <label className="flex items-center text-white/80 cursor-pointer">
                <input
                  type="radio"
                  name="format"
                  value="movie"
                  checked={format === 'movie'}
                  onChange={() => setFormat('movie')}
                  className="accent-white mr-2"
                />
                Movie
              </label>
            </div>
            <button
              onClick={handleGenerate}
              disabled={loading || !idea}
              className="w-full py-3 rounded-full bg-white/20 text-white font-bold shadow hover:bg-white/40 hover:text-black transition-all border border-white/30"
            >
              {loading ? 'Generating...' : 'Generate'}
            </button>
            {error && <div className="text-red-400 mt-4">{error}</div>}
            {result && (
              <>
                <div className="mt-8 w-full bg-black/60 text-white p-6 rounded-xl border border-white/20 shadow-inner whitespace-pre-wrap">
                  {result}
                </div>
                <div className="mt-6 text-center">
                  <span className="text-white font-semibold text-lg">Do you like the story?</span>
                  <div className="mt-3 flex justify-center gap-4">
                    <button onClick={handleLike} disabled={chapterLoading} className="px-6 py-2 rounded-full bg-white/20 text-white font-bold border border-white/30 hover:bg-white/40 hover:text-black transition-all">Yes</button>
                    <button onClick={handleDislike} disabled={loading} className="px-6 py-2 rounded-full bg-white/20 text-white font-bold border border-white/30 hover:bg-white/40 hover:text-black transition-all">No</button>
                  </div>
                </div>
              </>
            )}
            {chapterLoading && <div className="text-white mt-4">Generating Chapter 1...</div>}
            {chapter && (
              <div className="mt-8 w-full bg-black/80 text-white p-6 rounded-xl border border-white/20 shadow-inner whitespace-pre-wrap">
                <h2 className="text-2xl font-bold mb-4">Chapter 1</h2>
                {chapter}
                {/* Save Story Button */}
                <div className="mt-6 flex flex-col items-center">
                  <button
                    onClick={handleSaveStory}
                    disabled={saveLoading}
                    className="px-8 py-3 rounded-full bg-green-600/80 text-white font-bold shadow hover:bg-green-700 transition-all border border-green-500 mt-2"
                  >
                    {saveLoading ? 'Saving...' : 'Save Story'}
                  </button>
                  {saveError && <div className="text-red-400 mt-2">{saveError}</div>}
                  {saveSuccess && <div className="text-green-400 mt-2">{saveSuccess}</div>}
                </div>
              </div>
            )}
          </>
        ) : (
          // Saved Stories Tab
          <div className="w-full">
            <h1 className="text-3xl font-serif font-bold text-white mb-6">Saved Stories</h1>
            {fetchingStories ? (
              <div className="text-white/60">Loading...</div>
            ) : fetchStoriesError ? (
              <div className="text-red-400">{fetchStoriesError}</div>
            ) : savedStories.length === 0 ? (
              <div className="text-white/60">No saved stories yet.</div>
            ) : (
              <ul className="space-y-4">
                {savedStories.map(story => (
                  <li
                    key={story.id}
                    className="bg-black/60 p-4 rounded-xl border border-white/20 text-white cursor-pointer hover:bg-white/10 transition"
                    onClick={() => setSelectedStory(story)}
                  >
                    <div className="font-bold text-lg">{story.story_title}</div>
                    <div className="text-white/70 mb-2">{story.chapter_1_content?.slice(0, 120)}...</div>
                    <div className="text-xs text-white/40">Saved on {new Date(story.created_at).toLocaleString()}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
}