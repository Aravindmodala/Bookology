import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useSearchParams, useLocation, useNavigate } from 'react-router-dom';
import { supabase } from './supabaseClient';
import { useAuth } from './AuthContext';
import RichTextEditor from './components/RichTextEditor';
import { createApiUrl, API_ENDPOINTS } from './config';
import StoryCover from './components/StoryCover';
import {
  ArrowLeft,
  Save,
  Image as ImageIcon,
  Sparkles,
  Edit3,
  MessageSquare,
  Lightbulb,
  Zap,
  Type
} from 'lucide-react';

function DNASection({ title, children }) {
  return (
    <div className="mt-6">
      <div className="text-xs uppercase tracking-wider text-slate-600 mb-2">{title}</div>
      <div className="space-y-2 text-sm text-slate-700">{children}</div>
    </div>
  );
}

function ActionButton({ icon: Icon, label, small, onClick, disabled }) {
  const cls = small
    ? 'w-full px-3 py-2 rounded bg-gray-100 hover:bg-gray-200 text-xs font-medium flex items-center gap-2 text-slate-800 border border-gray-200 disabled:opacity-50'
    : 'w-full px-3 py-2 rounded bg-white hover:bg-gray-100 text-sm font-medium flex items-center gap-2 text-slate-800 border border-gray-200 disabled:opacity-50';
  return (
    <button className={cls} onClick={onClick} disabled={disabled}>
      <Icon className="w-4 h-4 text-blue-500" />
      <span className="truncate">{label}</span>
    </button>
  );
}

function BookIcon() {
  return (
    <svg viewBox="0 0 24 24" className="w-7 h-7 text-blue-400" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M3 5.5A2.5 2.5 0 0 1 5.5 3H21v15.5A2.5 2.5 0 0 1 18.5 21H5.5A2.5 2.5 0 0 0 3 18.5V5.5Z"/>
      <path d="M3 5.5A2.5 2.5 0 0 1 5.5 3H21"/>
    </svg>
  );
}

export default function MinimalEditor() {
  const { storyId: storyIdFromPath } = useParams();
  const [sp] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { user, session } = useAuth();

  const routedStory = location.state?.story || null;
  const creationMode = location.state?.mode; // e.g., 'generate_chapter_1'
  const storyId = storyIdFromPath || sp.get('story') || routedStory?.id;

  const [story, setStory] = useState(routedStory);
  const [chaptersCount, setChaptersCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [gameMode, setGameMode] = useState(false);
  const [focus, setFocus] = useState(false);
  const [stories, setStories] = useState([]);
  const [editorHtml, setEditorHtml] = useState('');
  const [activeChapter, setActiveChapter] = useState(null); // { id, chapter_number, title }
  const [wordCount, setWordCount] = useState(0);
  const [readMinutes, setReadMinutes] = useState(0);
  const [choicesLoading, setChoicesLoading] = useState(false);
  const [choicesError, setChoicesError] = useState('');
  const [choices, setChoices] = useState([]);
  const [selectedChoiceId, setSelectedChoiceId] = useState(null);
  const [generateWithChoiceLoading, setGenerateWithChoiceLoading] = useState(false);
  const [sidebarChapters, setSidebarChapters] = useState([]); // [{chapter_number, title, exists, id?}]
  const chapter1TriggeredRef = useRef(false);

  const totalChapters = story?.total_chapters ?? 0;
  const progressPct = useMemo(() => {
    if (!totalChapters) return 0;
    return Math.min(100, Math.round((chaptersCount / totalChapters) * 100));
  }, [chaptersCount, totalChapters]);

  // Utility: convert text with newlines to safe HTML paragraphs
  // Note: Defined here so it is available to hooks declared below (e.g., fetchData, handleLoadChapter)
  const convertTextToHtml = useCallback((text) => {
    if (!text) return '';
    // If it already looks like HTML, return as-is (basic script stripping)
    if (text.includes('<p') || text.includes('<div')) {
      return text
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/on\w+\s*=\s*"[^"]*"/gi, '')
        .replace(/on\w+\s*=\s*'[^']*'/gi, '');
    }
    const escapeHtml = (str) => {
      const div = document.createElement('div');
      div.textContent = str;
      return div.innerHTML;
    };
    const parts = text.split(/\n\n/);
    if (parts.length > 1) {
      return parts
        .map((p) => `<div style="margin-bottom: 1.5rem;">${escapeHtml(p.trim())}</div>`) 
        .join('');
    }
    // Fallback: single newlines
    return text
      .split(/\n/)
      .map((line, i, arr) => `<div style="${i < arr.length - 1 ? 'margin-bottom: 1rem;' : ''}">${escapeHtml(line.trim())}</div>`)
      .join('');
  }, []);

  const fetchData = useCallback(async () => {
    if (!storyId || !supabase) return;
    setLoading(true);
    try {
      const { data: s, error: se } = await supabase
        .from('Stories')
        .select('*')
        .eq('id', storyId)
        .single();
      if (se) throw se;
      setStory(s);

      const { count, error: ce } = await supabase
        .from('Chapters')
        .select('id', { count: 'exact', head: true })
        .eq('story_id', storyId)
        .eq('is_active', true);
      if (ce) throw ce;
      setChaptersCount(count || 0);

      // Load first chapter content (by chapter_number) with secure join to satisfy RLS
      let first = null;
      let existingChapters = [];
      try {
        const { data: rows, error: fcErr } = await supabase
          .from('Chapters')
          .select('id, chapter_number, title, content, Stories!inner(user_id)')
          .eq('story_id', storyId)
          .eq('Stories.user_id', user?.id || '')
          .eq('is_active', true)
          .order('chapter_number', { ascending: true });
        if (fcErr) throw fcErr;
        existingChapters = Array.isArray(rows) ? rows : [];
        first = existingChapters.length > 0 ? existingChapters[0] : null;
      } catch (errJoin) {
        existingChapters = [];
        first = null;
      }

      if (!first) {
        // Fallback to backend API (same as legacy editor)
        try {
          const resp = await fetch(createApiUrl(`/story/${storyId}/chapters?_t=${Date.now()}`), {
            method: 'GET',
            headers: {
              'Authorization': session?.access_token ? `Bearer ${session.access_token}` : '',
              'Content-Type': 'application/json'
            }
          });
          if (resp.ok) {
            const data = await resp.json();
            const chapters = data.chapters || [];
            if (chapters.length > 0) {
              existingChapters = chapters.sort((a,b) => (a.chapter_number||0)-(b.chapter_number||0));
              first = existingChapters[0];
            }
          }
        } catch (e) {
          // swallow and leave first as null
        }
      }

      // Build sidebar chapters from outline + existing
      const outlineData = (() => {
        try {
          const raw = s?.outline_json ?? story?.outline_json;
          const obj = typeof raw === 'string' ? JSON.parse(raw) : raw || {};
          if (Array.isArray(obj?.chapters)) return obj.chapters;
          if (Array.isArray(obj)) return obj; // fallback if array stored
          return [];
        } catch { return []; }
      })();

      const total = s?.total_chapters || outlineData.length || (existingChapters[existingChapters.length-1]?.chapter_number || existingChapters.length) || 1;
      const existingByNumber = new Map(existingChapters.map(c => [c.chapter_number, c]));
      const mergedList = Array.from({ length: total }, (_, idx) => {
        const num = idx + 1;
        const fromOutline = outlineData.find(ch => (ch.chapter_number || ch.number) === num);
        const title = (fromOutline?.title) || `Chapter ${num}`;
        const existing = existingByNumber.get(num);
        return { chapter_number: num, title, exists: !!existing, id: existing?.id };
      });
      setSidebarChapters(mergedList);

      if (first) {
        setActiveChapter({ id: first.id, chapter_number: first.chapter_number, title: first.title });
        const html = convertTextToHtml(first.content || '');
        setEditorHtml(html);
        const text = (first.content || '').replace(/<[^>]*>/g, '');
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        setWordCount(words);
        setReadMinutes(Math.max(1, Math.ceil(words / 200)));
      } else {
        setActiveChapter(null);
        setEditorHtml('');
        setWordCount(0);
        setReadMinutes(0);
      }
    } catch (e) {
      console.error('Failed to load story:', e);
    } finally {
      setLoading(false);
    }
  }, [storyId, user?.id, session?.access_token]);

  // Always load when we have a storyId. The previous condition
  // (!story || !storyId) skipped fetches when both were present.
  useEffect(() => {
    if (storyId) fetchData();
  }, [fetchData, storyId]);

  // Trigger Chapter 1 generation when arriving from StoryCreator with outline
  const generateChapter1FromOutline = useCallback(async () => {
    if (!story?.id || !story?.story_outline || !session?.access_token) return;
    try {
      const resp = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          outline: story.story_outline,
          chapter_number: 1,
          story_id: story.id
        })
      });
      if (resp.ok) {
        await fetchData();
      } else {
        console.warn('Failed to generate Chapter 1:', resp.status);
      }
    } catch (e) {
      console.warn('Error generating Chapter 1 from outline:', e);
    }
  }, [story?.id, story?.story_outline, session?.access_token, fetchData]);

  useEffect(() => {
    if (
      creationMode === 'generate_chapter_1' &&
      chaptersCount === 0 &&
      story?.id &&
      story?.story_outline &&
      !chapter1TriggeredRef.current
    ) {
      chapter1TriggeredRef.current = true;
      generateChapter1FromOutline();
    }
  }, [creationMode, chaptersCount, story?.id, story?.story_outline, generateChapter1FromOutline]);

  // Fetch choices for active chapter (Game Mode)
  const fetchChoices = useCallback(async () => {
    if (!activeChapter?.id || !session?.access_token) return;
    try {
      setChoicesLoading(true);
      setChoicesError('');
      const url = createApiUrl(
        API_ENDPOINTS.GET_CHAPTER_CHOICES.replace('{chapter_id}', activeChapter.id)
      );
      const resp = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        }
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      const normalized = (data.choices || []).map(c => ({
        ...c,
        id: c.id || c.choice_id,
        choice_id: c.choice_id || c.id
      }));
      setChoices(normalized);
    } catch (e) {
      setChoices([]);
      setChoicesError('Failed to load choices.');
    } finally {
      setChoicesLoading(false);
    }
  }, [activeChapter?.id, session?.access_token]);

  useEffect(() => {
    if (gameMode) fetchChoices();
  }, [gameMode, fetchChoices]);

  const outline = useMemo(() => {
    try {
      return typeof story?.outline_json === 'string'
        ? JSON.parse(story.outline_json)
        : story?.outline_json || {};
    } catch {
      return {};
    }
  }, [story]);

  const characters = outline?.characters || outline?.dna?.characters || [];
  const setting = outline?.setting || outline?.dna?.setting || outline?.world || '';

  const handleGenerateAI = () => {
    if (!storyId) return;
    // TODO: In future, open an inline panel to generate content
  };

  const handleStartScratch = () => {
    if (!storyId) return;
    // TODO: Optionally clear content or create a blank chapter flow
  };

  const handleSave = async () => {
    if (!story?.id || !activeChapter?.id || !session?.access_token) return;
    setSaving(true);
    try {
      // Persist using the same endpoint as the legacy editor
      const response = await fetch(createApiUrl(API_ENDPOINTS.UPDATE_CHAPTER_CONTENT), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          story_id: parseInt(storyId),
          chapter_id: activeChapter.id,
          content: editorHtml,
          word_count: editorHtml.replace(/<[^>]*>/g, '').trim().split(/\s+/).filter(Boolean).length
        })
      });
      if (!response.ok) {
        console.warn('Save failed with status', response.status);
      }
    } finally {
      setSaving(false);
    }
  };

  // Continue with selected choice -> generate next chapter
  const handleContinueWithChoice = useCallback(async () => {
    if (!selectedChoiceId) {
      setChoicesError('Please select a choice first.');
      return;
    }
    if (!story?.id || !session?.access_token || !activeChapter) return;
    setGenerateWithChoiceLoading(true);
    try {
      // Compute next chapter number from activeChapter
      const nextChapterNumber = (activeChapter?.chapter_number || 0) + 1;
      const choice = choices.find(c => c.id === selectedChoiceId || c.choice_id === selectedChoiceId);
      const resp = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER_WITH_CHOICE), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          story_id: story.id,
          choice_id: choice?.choice_id || selectedChoiceId,
          choice_data: choice || null,
          next_chapter_num: nextChapterNumber
        })
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      // Refresh story and first chapter after generation
      await fetchData();
      setSelectedChoiceId(null);
      await fetchChoices();
    } catch (e) {
      setChoicesError('Failed to continue with the selected choice.');
    } finally {
      setGenerateWithChoiceLoading(false);
    }
  }, [selectedChoiceId, story?.id, session?.access_token, activeChapter, choices, fetchData, fetchChoices]);

  // Normal next chapter (no choice) via quick action
  const handleGenerateNextChapter = useCallback(async () => {
    if (!storyId || !session?.access_token || !activeChapter) return;
    try {
      const nextChapterNumber = (activeChapter?.chapter_number || 0) + 1;
      const resp = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_NEXT_CHAPTER), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          story_id: parseInt(storyId),
          chapter_number: nextChapterNumber,
          story_outline: story?.story_outline || ''
        })
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      await fetchData();
      if (gameMode) await fetchChoices();
    } catch (e) {
      console.warn('Failed to generate next chapter:', e);
    }
  }, [storyId, session?.access_token, activeChapter, story?.story_outline, fetchData, gameMode, fetchChoices]);

  // Load a specific chapter by number
  const handleLoadChapter = useCallback(async (chapterNumber) => {
    if (!storyId) return;
    // Try Supabase first
    try {
      const { data: rows, error } = await supabase
        .from('Chapters')
        .select('id, chapter_number, title, content, created_at, Stories!inner(user_id)')
        .eq('story_id', storyId)
        .eq('chapter_number', chapterNumber)
        .eq('Stories.user_id', user?.id || '')
        .eq('is_active', true)
        .order('created_at', { ascending: false })
        .limit(1);
      if (!error && Array.isArray(rows) && rows.length > 0) {
        const ch = rows[0];
        setActiveChapter({ id: ch.id, chapter_number: ch.chapter_number, title: ch.title });
        setEditorHtml(convertTextToHtml(ch.content || ''));
        const text = (ch.content || '').replace(/<[^>]*>/g, '');
        setWordCount(text.trim() ? text.trim().split(/\s+/).length : 0);
        setReadMinutes(Math.max(1, Math.ceil((text.trim().split(/\s+/).length || 0) / 200)));
        if (gameMode) fetchChoices();
        return;
      }
    } catch {}

    // Fallback to backend
    try {
      const resp = await fetch(createApiUrl(`/story/${storyId}/chapters?_t=${Date.now()}`), {
        method: 'GET',
        headers: {
          'Authorization': session?.access_token ? `Bearer ${session.access_token}` : '',
          'Content-Type': 'application/json'
        }
      });
      if (resp.ok) {
        const data = await resp.json();
        const chapters = data.chapters || [];
        const ch = chapters.find(c => c.chapter_number === chapterNumber);
        if (ch) {
          setActiveChapter({ id: ch.id, chapter_number: ch.chapter_number, title: ch.title });
          setEditorHtml(convertTextToHtml(ch.content || ''));
          const text = (ch.content || '').replace(/<[^>]*>/g, '');
          setWordCount(text.trim() ? text.trim().split(/\s+/).length : 0);
          setReadMinutes(Math.max(1, Math.ceil((text.trim().split(/\s+/).length || 0) / 200)));
          if (gameMode) fetchChoices();
        }
      }
    } catch {}
  }, [storyId, user?.id, session?.access_token, gameMode, fetchChoices, convertTextToHtml]);

  const title = story?.story_title || story?.title || 'Untitled Story';

  // Fetch stories for story picker
  useEffect(() => {
    const fetchStories = async () => {
      if (!user || !supabase) return;
      try {
        const { data, error } = await supabase
          .from('Stories')
          .select('id, story_title, title, created_at')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });
        if (!error) setStories(data || []);
      } catch (err) {
        console.warn('Failed to fetch stories for picker:', err);
      }
    };
    fetchStories();
  }, [user]);

  const handleStoryChange = (e) => {
    const newId = e.target.value;
    if (!newId) return;
    navigate(`/editor?story=${newId}`);
  };

  return (
    <div className="h-screen w-screen bg-[#F5EDE2] text-slate-900 flex flex-col">
      <div className="h-12 px-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded" aria-label="Back">
            <ArrowLeft className="w-4 h-4 text-slate-700" />
          </button>
          <div className="text-sm text-slate-600">Chapter {activeChapter?.chapter_number || 1}</div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-sm text-slate-700">
            <span className="font-semibold text-slate-900">{title}</span>
            <span className="mx-3 text-slate-400">|</span>
            <span className="text-slate-600">{wordCount} words</span>
            <span className="mx-3 text-slate-400">|</span>
            <span className="text-slate-600">{readMinutes} min read</span>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {/* Story Picker */}
          <select
            value={storyId || ''}
            onChange={handleStoryChange}
            className="text-sm border border-gray-300 rounded-lg px-2 py-1 bg-white text-slate-700"
            title="Switch story"
          >
            <option value="" disabled>Select story…</option>
            {stories.map(s => (
              <option key={s.id} value={s.id}>
                {s.story_title || s.title || `Story ${s.id}`}
              </option>
            ))}
          </select>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500">Game Mode</span>
            <button
              onClick={() => setGameMode(v => !v)}
              className={`w-10 h-6 rounded-full transition-colors ${gameMode ? 'bg-blue-600' : 'bg-gray-300'}`}
              aria-label="Toggle Game Mode"
            />
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500">Focus</span>
            <button
              onClick={() => setFocus(v => !v)}
              className={`w-10 h-6 rounded-full transition-colors ${focus ? 'bg-blue-600' : 'bg-gray-300'}`}
              aria-label="Toggle Focus Mode"
            />
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-sm font-medium text-white flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving…' : 'Save'}</span>
          </button>
        </div>
      </div>

      <div className="h-1 bg-blue-600" />

      <div className="flex-1 flex overflow-hidden">
        <div className="w-72 border-r border-gray-200 p-4 overflow-y-auto bg-[#F5EDE2]">
          <StoryCover 
            storyId={story?.id || (storyId ? parseInt(storyId) : undefined)} 
            storyTitle={title} 
          />

          <div className="mt-6">
            <div className="text-sm font-semibold mb-2 text-slate-800">Progress</div>
            <div className="text-xs text-slate-500 mb-2">{progressPct}%</div>
            <div className="w-full h-2 bg-gray-200 rounded">
              <div className="h-2 rounded bg-blue-600 transition-all" style={{ width: `${progressPct}%` }} />
            </div>
            <div className="mt-2 text-xs text-slate-500">
              {chaptersCount}/{totalChapters} chapters
            </div>
          </div>

          <DNASection title={<span className="text-slate-600">Story DNA</span>}>
            {Array.isArray(characters) && characters.length > 0 && (
              <div>
                <div className="text-xs text-slate-500 mb-1">Characters</div>
                <div className="flex flex-wrap gap-2">
                  {characters.map((c, i) => (
                    <span key={i} className="px-2 py-1 bg-gray-100 border border-gray-200 rounded text-xs text-slate-700">{c?.name || c}</span>
                  ))}
                </div>
              </div>
            )}
            {setting && (
              <div className="mt-3">
                <div className="text-xs text-slate-500 mb-1">Setting</div>
                <div className="text-sm text-slate-700">{typeof setting === 'string' ? setting : JSON.stringify(setting)}</div>
              </div>
            )}
          </DNASection>

          {/* Planned Chapters from Outline */}
          {sidebarChapters.length > 0 && (
            <div className="mt-8">
              <div className="text-sm font-semibold mb-2 text-slate-800">Chapters</div>
              <div className="space-y-1">
                {sidebarChapters.map(ch => (
                  <button
                    key={ch.chapter_number}
                    onClick={() => handleLoadChapter(ch.chapter_number)}
                    className={`w-full text-left px-3 py-2 rounded border ${
                      activeChapter?.chapter_number === ch.chapter_number
                        ? 'bg-white border-blue-500 text-slate-900'
                        : ch.exists
                          ? 'bg-white border-gray-200 text-slate-800 hover:bg-gray-50'
                          : 'bg-transparent border-gray-200 text-slate-600 hover:bg-white'
                    }`}
                    title={ch.exists ? 'Open chapter' : 'Planned (not yet written)'}
                  >
                    <span className="text-sm">Chapter {ch.chapter_number}: {ch.title}</span>
                    {!ch.exists && <span className="ml-2 text-xs text-yellow-700">(planned)</span>}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex-1 p-10 overflow-y-auto bg-[#F5EDE2]">
          {!activeChapter ? (
            <div className="border border-gray-200 rounded-xl p-12 text-center bg-white">
              <div className="mx-auto w-14 h-14 rounded-lg bg-blue-50 flex items-center justify-center text-blue-500 mb-6">
                <BookIcon />
              </div>
              <div className="text-2xl font-semibold mb-2 text-slate-900">Ready to Write Chapter 1?</div>
              <div className="text-slate-600 mb-8">Generate your chapter with AI or start writing from scratch.</div>
              <div className="flex items-center justify-center gap-4">
                <button
                  onClick={handleGenerateAI}
                  className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-sm font-medium text-white flex items-center space-x-2"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Generate with AI</span>
                </button>
                <button
                  onClick={handleStartScratch}
                  className="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 text-sm font-medium text-slate-800 flex items-center space-x-2 border border-gray-200"
                >
                  <Edit3 className="w-4 h-4" />
                  <span>Start from Scratch</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="max-w-5xl mx-auto">
              <div className="mb-6">
                <h1 className="text-3xl font-semibold text-slate-900">{title}</h1>
                <div className="mt-1 text-sm text-slate-600">Chapter {activeChapter.chapter_number}</div>
              </div>
              <RichTextEditor
                value={editorHtml}
                onChange={(html) => {
                  setEditorHtml(html);
                  const text = html.replace(/<[^>]*>/g, '');
                  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
                  setWordCount(words);
                  setReadMinutes(Math.max(1, Math.ceil(words / 200)));
                }}
                className="editor-light w-full min-h-[700px] bg-white border border-gray-200 rounded-lg p-8 text-slate-900 text-lg leading-relaxed focus:outline-none"
              />

              {/* Game Mode: Choices Under Editor */}
              {gameMode && (
                <div className="mt-8">
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-slate-900">Story Choices</h3>
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                        <span className="text-sm text-purple-700">Game Mode Active</span>
                      </div>
                    </div>

                    {choicesLoading && (
                      <div className="flex items-center justify-center py-8 text-slate-600">
                        <div className="w-6 h-6 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mr-3"></div>
                        Loading choices...
                      </div>
                    )}

                    {choicesError && (
                      <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-4">
                        {choicesError}
                      </div>
                    )}

                    {!choicesLoading && !choicesError && choices.length === 0 && (
                      <div className="text-center py-8 text-slate-500">
                        No choices available for this chapter yet.
                      </div>
                    )}

                    {!choicesLoading && !choicesError && choices.length > 0 && (
                      <div className="space-y-3">
                        {choices.map((choice) => (
                          <button
                            key={choice.id}
                            onClick={() => setSelectedChoiceId(choice.id)}
                            className={`w-full text-left p-4 rounded-lg border transition-colors ${
                              selectedChoiceId === choice.id
                                ? 'border-purple-600 bg-purple-50'
                                : 'border-gray-200 bg-white hover:bg-gray-50'
                            }`}
                          >
                            <div className="flex items-start space-x-3">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                selectedChoiceId === choice.id ? 'bg-purple-600 text-white' : 'bg-gray-100 text-slate-700'
                              }`}>
                                {selectedChoiceId === choice.id ? '✓' : '?' }
                              </div>
                              <div>
                                <h4 className="text-slate-900 font-medium">{choice.title || 'Choice'}</h4>
                                {choice.description && (
                                  <p className="text-sm text-slate-600 leading-relaxed">{choice.description}</p>
                                )}
                              </div>
                            </div>
                          </button>
                        ))}

                        {selectedChoiceId && (
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <ActionButton
                              icon={Zap}
                              label={generateWithChoiceLoading ? 'Continuing…' : 'Continue with Selected Choice'}
                              onClick={handleContinueWithChoice}
                              disabled={generateWithChoiceLoading}
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="w-80 border-l border-gray-200 p-4 overflow-y-auto bg-[#F5EDE2]">
          <div className="text-sm font-semibold mb-4 flex items-center gap-2 text-slate-800">
            <Sparkles className="w-4 h-4 text-blue-500" />
            AI Assistant
          </div>
          <div className="space-y-3">
            <ActionButton icon={Zap} label="Continue Chapter" onClick={handleGenerateNextChapter} />
            <ActionButton icon={Type} label="Improve Writing" />
            <ActionButton icon={MessageSquare} label="Add Dialogue" />
            <ActionButton icon={Lightbulb} label="Brainstorm Ideas" />
          </div>
          <div className="mt-6">
            <div className="text-sm font-semibold mb-3 text-slate-800">Quick Actions</div>
            <div className="space-y-2">
              <ActionButton small icon={Zap} label="Continue Chapter" onClick={handleGenerateNextChapter} />
              <ActionButton small icon={Type} label="Improve Writing" />
              <ActionButton small icon={MessageSquare} label="Add Dialogue" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


