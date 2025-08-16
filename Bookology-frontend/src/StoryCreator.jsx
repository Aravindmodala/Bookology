import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Wand2, PenTool, BookOpen, RefreshCw } from 'lucide-react';
import { useAuth } from './AuthContext';
import { createApiUrl, API_ENDPOINTS } from './config';

const StoryCreator = () => {
  const navigate = useNavigate();
  const { user, session } = useAuth();

  // Flow and form state
  const [selectedFlow, setSelectedFlow] = useState(null); // 'ai' | 'manual'
  const [idea, setIdea] = useState('');
  const [recentIdeas, setRecentIdeas] = useState([]);

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
  const [saveSuccess, setSaveSuccess] = useState('');
  const [storyId, setStoryId] = useState(null);

  // Load recent ideas
  useEffect(() => {
    const saved = localStorage.getItem('bookology_recent_ideas');
    if (!saved) return;
    try {
      setRecentIdeas(JSON.parse(saved));
    } catch (_) {
      // ignore
    }
  }, []);

  // Auto-select flow when navigated with state
  useEffect(() => {
    try {
      const navState = window.history?.state?.usr || null;
      const presetFlow = navState?.flow;
      if (presetFlow === 'ai' || presetFlow === 'manual') setSelectedFlow(presetFlow);
    } catch (_) {
      // ignore
    }
  }, []);

  const handleFlowSelection = (flow) => {
    setSelectedFlow(flow);
    localStorage.setItem('bookology_preferred_flow', flow);
  };

  const saveIdeaToRecent = (newIdea) => {
    if (!newIdea.trim()) return;
    const updated = [newIdea, ...recentIdeas.filter((i) => i !== newIdea)].slice(0, 5);
    setRecentIdeas(updated);
    localStorage.setItem('bookology_recent_ideas', JSON.stringify(updated));
  };

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

    saveIdeaToRecent(idea);

    const headers = { 'Content-Type': 'application/json' };
    if (session?.access_token) headers['Authorization'] = `Bearer ${session.access_token}`;
    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_OUTLINE), {
        method: 'POST',
        headers,
        body: JSON.stringify({ idea })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || 'Failed to generate');

      setResult(data.summary || '');
      setStoryTitle(data.title || (data.summary ? (data.summary.split('.')[0] || 'Untitled Story') : 'Untitled Story'));
      if (data.genre) setStoryGenre(data.genre);
      if (data.tone) setStoryTone(data.tone);
      if (Array.isArray(data.chapters)) setChapterTitles(data.chapters.map((c, i) => c.title || c.chapter_title || `Chapter ${i + 1}`));
      if (Array.isArray(data.main_characters)) setMainCharacters(data.main_characters);
      if (Array.isArray(data.key_locations)) setKeyLocations(data.key_locations);
    } catch (e) {
      setError(e.message || 'Error connecting to backend');
    } finally {
      setLoading(false);
    }
  };

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
          chapters: chapterTitles.map((t, i) => ({ chapter_number: i + 1, title: t })),
          reflection: '',
          is_optimized: true,
          main_characters: mainCharacters,
          key_locations: keyLocations
        })
      });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data?.detail || 'Failed to save outline');
      setOutlineSaved(true);
      setStoryId(data.story_id);
      setSaveSuccess(`Outline saved as "${data.story_title}"`);
    } catch (e) {
      setSaveOutlineError(e.message || 'Failed to save outline');
    } finally {
      setSaveOutlineLoading(false);
    }
  };

  const handleGenerateChapter = () => {
    if (!outlineSaved || !storyId) {
      setError('Please save your outline first.');
      return;
    }
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
        mode: 'generate_chapter_1'
      }
    });
  };

  const handleManualStory = async () => {
    if (!user || !session?.access_token) {
      setError('Please log in to create a story.');
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(createApiUrl(API_ENDPOINTS.SAVE_OUTLINE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          summary: 'Blank story',
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
      if (!response.ok || !data.success) throw new Error(data?.detail || 'Failed to create story');
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
          mode: 'manual_creation'
        }
      });
    } catch (e) {
      setError(e.message || 'Failed to create story');
    } finally {
      setLoading(false);
    }
  };

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

  // If no flow yet, default to AI to avoid extra click per memory 6217740
  if (!selectedFlow) {
    setSelectedFlow('ai');
    return null;
  }

  if (selectedFlow === 'manual') {
    return (
      <div className="deep-space starfield text-off">
        <div className="glow glow-violet" />
        <div className="glow glow-cyan" />
        <div className="container py-8">
          <div className="max-w-4xl mx-auto">
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
                    <BookOpen className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-off mb-4">Ready to Create?</h3>
                  <p className="text-off-70 mb-6">You'll start with a blank story and can write freely. You can always use AI assistance later.</p>
                  <button onClick={handleManualStory} disabled={loading} className="btn-violet px-8 py-4 text-lg flex items-center space-x-3 mx-auto disabled:cursor-not-allowed">
                    {loading ? 'Creating…' : 'Start Writing'}
                  </button>
                </div>
                {error && (
                  <div className="text-center">
                    <div className="text-red-400 text-sm p-3 bg-red-900/20 border border-red-800 rounded-lg">{error}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // AI flow
  return (
    <div className="deep-space starfield text-off">
      <div className="glow glow-violet" />
      <div className="glow glow-cyan" />
      <div className="container py-8">
        <div className="max-w-4xl mx-auto">
          <div className="card-soft p-8">
            <div className="text-center mb-8">
              <div className="flex items-center justify-center space-x-3 mb-4">
                <Sparkles className="w-8 h-8 text-violet-400" />
                <h1 className="font-sora text-4xl font-bold text-off">Start with AI</h1>
              </div>
              <p className="text-off-70">Transform your ideas into compelling narratives with AI assistance</p>
            </div>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-off-80 mb-3">What's your story idea?</label>
                <textarea
                  placeholder="Enter your story idea..."
                  value={idea}
                  onChange={(e) => setIdea(e.target.value)}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-off placeholder-off-60 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 resize-none"
                  rows={4}
                />
              </div>
              <div className="text-center pt-6">
                <button onClick={handleGenerate} disabled={loading || !idea.trim()} className="btn-violet px-8 py-4 text-lg flex items-center space-x-3 mx-auto disabled:cursor-not-allowed">
                  {loading ? 'Generating…' : (<><Wand2 className="w-5 h-5" /><span>Generate Story Outline</span></>)}
                </button>
              </div>
              {error && (
                <div className="text-center">
                  <div className="text-red-400 text-sm p-3 bg-red-900/20 border border-red-800 rounded-lg">{error}</div>
                </div>
              )}
            </div>

            {result && (
              <div className="mt-8 space-y-6">
                <div className="card-soft p-5 md:p-6">
                  <input
                    type="text"
                    value={storyTitle}
                    onChange={(e) => setStoryTitle(e.target.value)}
                    placeholder="Untitled Story"
                    className="bg-transparent w-full font-sora text-2xl md:text-3xl lg:text-4xl outline-none text-off text-center"
                    maxLength={100}
                  />
                </div>
                <div className="grid lg:grid-cols-[minmax(0,1fr)_360px] gap-10 lg:gap-16">
                  <div className="space-y-6">
                    <details open className="card-soft p-5">
                      <summary className="flex items-center justify-between cursor-pointer">
                        <span className="font-medium">Story Outline</span>
                      </summary>
                      <p className="text-off-80 leading-relaxed mt-4 whitespace-pre-wrap">{result}</p>
                    </details>
                    {chapterTitles.length > 0 && (
                      <div className="card-soft p-5">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="font-medium">Chapters</h3>
                        </div>
                        <div className="divide-y divide-white/10">
                          {chapterTitles.map((t, i) => (
                            <div key={`${i}-${t}`} className="py-3">
                              <div className="flex items-center gap-3 min-w-0">
                                <span className="text-violet-300 font-mono text-xs w-8 text-right">{String(i + 1).padStart(2, '0')}</span>
                                <span className="text-off truncate">{t}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <aside className="space-y-4 lg:sticky lg:top-24 h-fit">
                    {storyGenre && (
                      <div className="card-soft p-5">
                        <div className="text-sm text-off-70 mb-2">Genre</div>
                        <div className="text-off font-medium">{storyGenre}</div>
                      </div>
                    )}
                    <div className="card-soft p-5">
                      <div className="text-sm text-off-70 mb-2">Next</div>
                      <button className="btn-outline w-full mb-2" onClick={handleSaveOutline} disabled={saveOutlineLoading || !user}>
                        {saveOutlineLoading ? 'Saving…' : 'Save Outline'}
                      </button>
                      <button className="btn-violet w-full" onClick={handleGenerateChapter} disabled={!outlineSaved || !storyId}>
                        Go to Editor (Chapter 1)
                      </button>
                      {saveSuccess && <div className="text-green-400 text-xs mt-2">{saveSuccess}</div>}
                      {saveOutlineError && <div className="text-red-400 text-xs mt-2">{saveOutlineError}</div>}
                    </div>
                  </aside>
                </div>
              </div>
            )}
          </div>
          {/* Bottom action row removed per request */}
        </div>
      </div>
    </div>
  );
};

export default StoryCreator;


