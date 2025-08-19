import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useSearchParams, useLocation, useNavigate } from 'react-router-dom';
import { supabase } from './supabaseClient';
import { useAuth } from './AuthContext';
import RichTextEditor from './components/RichTextEditor';
import { createApiUrl, API_ENDPOINTS } from './config';
import StoryCover from './components/StoryCover';
import { ArrowLeft, Save, Sparkles, Edit3, MessageSquare, Lightbulb, Zap, Type, Bold as BoldIcon, Italic as ItalicIcon, Image as ImageIcon, Minus, Plus, RefreshCw, Feather } from 'lucide-react';
import RightSidebar from './components/RightSidebar';

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
  // Writing animations & states
  const [isGenerating, setIsGenerating] = useState(false);
  const [pageFlip, setPageFlip] = useState(false);
  const [isRewriting, setIsRewriting] = useState(false);
  const [previousHtml, setPreviousHtml] = useState('');
  const [showUndo, setShowUndo] = useState(false);
  const [wiping, setWiping] = useState(false);

  const triggerPageFlip = useCallback(() => {
    setPageFlip(true);
    setTimeout(() => setPageFlip(false), 350);
  }, []);
  const [sidebarChapters, setSidebarChapters] = useState([]); // [{chapter_number, title, exists, id?}]
  const chapter1TriggeredRef = useRef(false);
  // Track editor instance and selection for Improve Writing
  const editorRef = useRef(null);
  const selectionRef = useRef({ text: '', from: 0, to: 0 });

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

  // Trigger Chapter 1 generation when arriving from StoryCreator with outline (non-streaming)
  const generateChapter1FromOutline = useCallback(async () => {
    if (!story?.id || !story?.story_outline || !session?.access_token) return;
    try {
      setIsGenerating(true);
      // Call non-streaming endpoint to generate and save Chapter 1
      const res = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_CHAPTER), {
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
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // After backend saves, refresh chapters and show content
      await fetchData();
      triggerPageFlip();
    } catch (e) {
      console.warn('Error generating Chapter 1:', e);
    } finally {
      setIsGenerating(false);
    }
  }, [story?.id, story?.story_outline, session?.access_token, fetchData, convertTextToHtml, triggerPageFlip]);

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
  // Which chapter number is being generated (for sidebar indicator)
  const generatingChapterNumber = useMemo(() => {
    if (!isGenerating) return null;
    return (activeChapter?.chapter_number || 0) + 1;
  }, [isGenerating, activeChapter?.chapter_number]);

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
    setIsGenerating(true);
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
      triggerPageFlip();
      setSelectedChoiceId(null);
      await fetchChoices();
    } catch (e) {
      setChoicesError('Failed to continue with the selected choice.');
    } finally {
      setGenerateWithChoiceLoading(false);
      setIsGenerating(false);
    }
  }, [selectedChoiceId, story?.id, session?.access_token, activeChapter, choices, fetchData, fetchChoices]);

  // Normal next chapter (no choice) via quick action
  const handleGenerateNextChapter = useCallback(async () => {
    if (!storyId || !session?.access_token || !activeChapter) return;
    try {
      setIsGenerating(true);
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
      triggerPageFlip();
      if (gameMode) await fetchChoices();
    } catch (e) {
      console.warn('Failed to generate next chapter:', e);
    }
    finally {
      setIsGenerating(false);
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
  // Prefer persisted chapter.title; fallback to outline sidebar title; else generic
  const activeChapterTitle = useMemo(() => {
    const num = activeChapter?.chapter_number;
    const fromSidebar = sidebarChapters.find(ch => ch.chapter_number === num)?.title;
    const isGeneric = (t) => !!t && /^\s*chapter\s+\d+\s*$/i.test(String(t));
    // Prefer outline/sidebar title if present and non-generic
    if (fromSidebar && String(fromSidebar).trim() && !isGeneric(fromSidebar)) return fromSidebar;
    // Otherwise use DB title if non-generic
    if (activeChapter?.title && String(activeChapter.title).trim() && !isGeneric(activeChapter.title)) return activeChapter.title;
    // Fallbacks
    return num ? `Chapter ${num}` : 'Chapter 1';
  }, [activeChapter?.title, activeChapter?.chapter_number, sidebarChapters]);

  // Toolbar actions for TipTap editor
  const applyBold = () => editorRef.current?.chain().focus().toggleBold().run();
  const applyItalic = () => editorRef.current?.chain().focus().toggleItalic().run();
  const [fontSizeRem, setFontSizeRem] = useState(1.0); // selection font size multiplier
  const applyFontSize = (rem) => {
    const editor = editorRef.current;
    if (!editor) return;
    if (Math.abs(rem - 1.0) < 0.01) {
      editor.chain().focus().unsetMark('textStyle').run();
    } else {
      editor.chain().focus().setMark('textStyle', { fontSize: `${rem}rem` }).run();
    }
  };
  const increaseFont = () => {
    setFontSizeRem((prev) => {
      const next = Math.min(1.5, +(prev + 0.05).toFixed(2));
      applyFontSize(next);
      return next;
    });
  };
  const decreaseFont = () => {
    setFontSizeRem((prev) => {
      const next = Math.max(0.85, +(prev - 0.05).toFixed(2));
      applyFontSize(next);
      return next;
    });
  };
  const resetFont = () => {
    setFontSizeRem(1.0);
    const editor = editorRef.current;
    editor?.chain().focus().unsetMark('textStyle').run();
  };

  const handleInsertImage = async () => {
    try {
      console.log('🖼️ Starting image upload...');

      // Create a hidden file input for image selection
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/png,image/jpeg,image/webp';
      input.onchange = async () => {
        const file = input.files?.[0];
        if (!file) {
          console.log('❌ No file selected');
          return;
        }

        console.log('📁 File selected:', file.name, file.size, file.type);

        // Ask for alt text
        const alt = window.prompt('Alt text for accessibility (required):', '') || '';
        if (!alt) {
          console.warn('⚠️ Proceeding without alt text');
        }

        // Basic size cap (client-side)
        if (file.size > 8 * 1024 * 1024) {
          alert('Please choose an image under 8MB.');
          return;
        }

        // Insert a temporary base64 image immediately
        const reader = new FileReader();
        reader.onload = async () => {
          const tempSrc = String(reader.result || '');
          console.log('🖼️ Base64 image created, length:', tempSrc.length);

          const editor = editorRef.current;
          if (!editor) {
            console.error('❌ Editor not available');
            return;
          }

          // Insert base64 image
          editor.chain().focus().setImage({ src: tempSrc, alt }).run();
          console.log('✅ Base64 image inserted into editor');

          // Try to upload to Supabase Storage and swap the src once available
          try {
            console.log('☁️ Starting Supabase upload...');

            const userId = user?.id;
            const storyId = story?.id || storyIdFromPath || sp.get('story');
            console.log('👤 User ID:', userId, '📚 Story ID:', storyId);

            const ext = (file.name.split('.').pop() || 'jpg').toLowerCase();
            const path = `editor-assets/${userId || 'anon'}/${storyId || 'unknown'}/${Date.now()}-${Math.random().toString(36).slice(2)}.${ext}`;
            console.log('📂 Upload path:', path);

            console.log('🔧 Supabase client available:', !!supabase, 'storage:', !!supabase?.storage);

            const { data: up, error: upErr } = await supabase.storage
              .from('editor-assets')
              .upload(path, file, {
                cacheControl: '3600',
                upsert: true,
                contentType: file.type || 'image/jpeg'
              });

            if (upErr) {
              console.error('❌ Upload error:', upErr);
              return;
            }

            console.log('✅ Upload successful:', up);

            const pub = supabase.storage.from('editor-assets').getPublicUrl(path);
            const publicUrl = pub?.data?.publicUrl;

            if (!publicUrl) {
              console.error('❌ Failed to get public URL');
              return;
            }

            console.log('🔗 Public URL:', publicUrl);

            // Replace temp src with public URL
            editor.chain().focus().command(({ tr, state }) => {
              let replaced = false;
              state.doc.descendants((node, pos) => {
                if (node.type.name === 'image' && node.attrs.src === tempSrc) {
                  tr.setNodeMarkup(pos, undefined, { ...node.attrs, src: publicUrl });
                  replaced = true;
                  return false;
                }
                return true;
              });
              return true;
            }).run();

            console.log('✅ Image URL replaced with Supabase URL');
          } catch (uploadError) {
            console.error('❌ Upload process failed:', uploadError);
          }
        };
        reader.onerror = (e) => console.error('❌ FileReader error:', e);
        reader.readAsDataURL(file);
      };
      input.click();
    } catch (error) {
      console.error('❌ Image upload failed:', error);
    }
  };

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
    <div className="h-screen w-screen relative overflow-hidden bg-gradient-to-b from-[#0a0f1a] to-[#0b1220] text-[#E6E9F2] flex flex-col">
      {/* Atmosphere */}
      <div className="starfield absolute inset-0 opacity-20 pointer-events-none" />
      <div className="glow glow-violet" />
      <div className="glow glow-cyan" />

      {/* TopBar */}
      <div className="sticky top-0 z-40 px-4 h-14 backdrop-blur-xl bg-white/5 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-white/10 rounded" aria-label="Back">
            <ArrowLeft className="w-4 h-4 text-off" />
          </button>
          <div className="text-sm text-[#A9B1C7]">{activeChapterTitle}</div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-sm text-[#A9B1C7] truncate">
            <span className="font-semibold text-[#E6E9F2]">{title}</span>
            <span className="mx-3 text-white/30">|</span>
            <span>{wordCount} words</span>
            <span className="mx-3 text-white/30">|</span>
            <span>{readMinutes} min read</span>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-xs text-[#A9B1C7]">Game Mode</span>
            <button
              onClick={() => setGameMode(v => !v)}
              aria-label="Toggle Game Mode"
              aria-pressed={gameMode}
              className={`relative w-12 h-6 rounded-full border border-violet-400/40 transition-all focus:outline-none focus:ring-2 focus:ring-violet-400/40 ${gameMode ? 'bg-violet-500/60' : 'bg-violet-500/20'}`}
            >
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${gameMode ? 'translate-x-6' : ''}`} />
            </button>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-[#A9B1C7]">Focus</span>
            <button
              onClick={() => setFocus(v => !v)}
              aria-label="Toggle Focus Mode"
              aria-pressed={focus}
              className={`relative w-12 h-6 rounded-full border border-violet-400/40 transition-all focus:outline-none focus:ring-2 focus:ring-violet-400/40 ${focus ? 'bg-violet-500/60' : 'bg-violet-500/20'}`}
            >
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${focus ? 'translate-x-6' : ''}`} />
            </button>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-3 py-1.5 rounded bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-sm font-medium text-white flex items-center space-x-2 shadow-[0_8px_40px_rgba(0,0,0,0.45)]"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving…' : 'Save'}</span>
          </button>
        </div>
      </div>

      <div className="h-px bg-white/10" />
      {/* Story Beam progress line */}
      {isGenerating && (
        <div className="relative h-[2px] bg-transparent">
          <div className="story-beam" />
        </div>
      )}

      <div className={`flex-1 flex overflow-hidden transition-all ${focus ? 'bg-black/20' : ''}`}>
        {/* Left Sidebar */}
        <div className={`w-[280px] border-r border-white/10 p-4 overflow-y-auto no-scrollbar ${focus ? 'hidden lg:block opacity-0 scale-95 translate-y-1' : ''}`}>
          <div className="bg-white/5 border border-white/10 rounded-2xl p-4 backdrop-blur-md shadow-[0_8px_40px_rgba(0,0,0,0.45)]">
          <StoryCover 
            storyId={story?.id || (storyId ? parseInt(storyId) : undefined)} 
            storyTitle={title} 
          />

          <div className="mt-6">
            <div className="text-sm font-semibold mb-2 text-off">Progress</div>
            <div className="text-xs text-white/60 mb-2">{progressPct}%</div>
            <div className="w-full h-2 bg-white/10 rounded">
              <div className="h-2 rounded bg-violet-500 transition-all" style={{ width: `${progressPct}%` }} />
            </div>
            <div className="mt-2 text-xs text-white/60">
              {chaptersCount}/{totalChapters} chapters
            </div>
          </div>

          <DNASection title={<span className="text-white/70">Story DNA</span>}>
            {Array.isArray(characters) && characters.length > 0 && (
              <div>
                <div className="text-xs text-white/60 mb-1">Characters</div>
                <div className="flex flex-wrap gap-2">
                  {characters.map((c, i) => (
                    <span key={i} className="px-2 py-1 bg-white/10 border border-white/10 rounded text-xs text-off">{c?.name || c}</span>
                  ))}
                </div>
              </div>
            )}
            {setting && (
              <div className="mt-3">
                <div className="text-xs text-white/60 mb-1">Setting</div>
                <div className="text-sm text-off/90">{typeof setting === 'string' ? setting : JSON.stringify(setting)}</div>
              </div>
            )}
          </DNASection>

          {/* Planned Chapters from Outline */}
          {sidebarChapters.length > 0 && (
            <div className="mt-8">
              <div className="text-sm font-semibold mb-1 text-off">Chapters</div>
              {isGenerating && (
                <div className="mb-2 text-xs text-violet-300 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
                  <span>Writing Chapter {generatingChapterNumber}…</span>
                </div>
              )}
              <div className="space-y-1">
                {sidebarChapters.map(ch => (
                  <button
                    key={ch.chapter_number}
                    onClick={() => handleLoadChapter(ch.chapter_number)}
                    className={`relative w-full text-left px-3 py-2 rounded border backdrop-blur-md ${
                      activeChapter?.chapter_number === ch.chapter_number
                        ? 'bg-white/10 border-violet-400/40 text-off'
                        : ch.exists
                          ? 'bg-white/5 border-white/10 text-off hover:bg-white/10'
                          : 'bg-transparent border-white/10 text-white/60 hover:bg-white/5'
                    }`}
                    title={ch.exists ? 'Open chapter' : 'Planned (not yet written)'}
                  >
                    {isGenerating && ch.chapter_number === generatingChapterNumber ? (
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full bg-violet-500/90 animate-pulse" />
                        <span className="text-sm text-off">Generating chapter…</span>
                      </div>
                    ) : (
                      <>
                        <span className="text-sm">Chapter {ch.chapter_number}: {ch.title}</span>
                        {!ch.exists && <span className="ml-2 text-xs text-yellow-300/90">(planned)</span>}
                      </>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
          </div>
        </div>

        {/* Editor Center */}
        <div className="flex-1 p-8 md:p-10 overflow-y-auto no-scrollbar">
          {!activeChapter ? (
            isGenerating ? (
              <div className="relative border border-white/10 rounded-xl p-10 text-center bg-white/5 backdrop-blur-md shadow-[0_8px_40px_rgba(0,0,0,0.45)]" aria-busy="true">
                <div className="mx-auto w-14 h-14 rounded-lg bg-violet-500/15 flex items-center justify-center text-violet-400 mb-5">
                  <Feather className="w-6 h-6 animate-float" />
                </div>
                <div className="text-xl font-semibold mb-1 text-off">Your professional writer is crafting your opening…</div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-white/70 text-xs whisper-dots" aria-live="polite">
                  <span>Crafting Chapter 1</span>
                  <span className="dots" />
                </div>
                {/* Skeleton paragraphs */}
                <div className="mt-8 space-y-3">
                  <div className="skeleton-line" />
                  <div className="skeleton-line w-11/12" />
                  <div className="skeleton-line w-10/12" />
                  <div className="skeleton-line w-9/12" />
                  <div className="skeleton-line w-11/12" />
                </div>
                {/* Page-turn corner for when it completes */}
                <div className={`page-corner ${pageFlip ? 'page-corner--flip' : ''}`} aria-hidden="true" />
              </div>
            ) : (
              <div className="border border-white/10 rounded-xl p-12 text-center bg-white/5 backdrop-blur-md shadow-[0_8px_40px_rgba(0,0,0,0.45)]">
                <div className="mx-auto w-14 h-14 rounded-lg bg-violet-500/15 flex items-center justify-center text-violet-400 mb-6">
                  <BookIcon />
                </div>
                <div className="text-2xl font-semibold mb-2 text-off">Ready to Write Chapter 1?</div>
                <div className="text-white/70 mb-8">Generate your chapter with AI or start writing from scratch.</div>
                <div className="flex items-center justify-center gap-4">
                  <button
                    onClick={handleGenerateAI}
                    className="px-4 py-2 rounded bg-violet-600 hover:bg-violet-500 text-sm font-medium text-white flex items-center space-x-2 shadow-[0_8px_40px_rgba(0,0,0,0.45)]"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Generate with AI</span>
                  </button>
                  <button
                    onClick={handleStartScratch}
                    className="px-4 py-2 rounded bg-white/5 hover:bg-white/10 text-sm font-medium text-off flex items-center space-x-2 border border-white/10 backdrop-blur-md"
                  >
                    <Edit3 className="w-4 h-4" />
                    <span>Start from Scratch</span>
                  </button>
                </div>
              </div>
            )
          ) : (
            <div className={`${focus ? 'max-w-[900px]' : 'max-w-[820px]'} mx-auto`}>
              <div className="mb-6">
                <div className="mx-auto w-full max-w-[920px] px-2 sm:px-3">
                <h1 className="text-3xl font-semibold text-off">{title}</h1>
                  <div className="mt-1 text-sm text-white/70">{activeChapterTitle}</div>
                  {/* Inline Toolbar */}
                  <div className="mt-3 rounded-xl border border-white/10 bg-white/5 p-2 flex flex-wrap items-center gap-2">
                    <button onClick={applyBold} title="Bold (Ctrl+B)" aria-label="Bold" className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10">
                      <BoldIcon className="w-4 h-4" />
                    </button>
                    <button onClick={applyItalic} title="Italic (Ctrl+I)" aria-label="Italic" className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10">
                      <ItalicIcon className="w-4 h-4" />
                    </button>
                    <div className="h-6 w-px bg-white/10" />
                    <div className="flex items-center gap-2">
                      <Type className="w-4 h-4 text-white/70" />
                      <button onClick={decreaseFont} title="Decrease font" aria-label="Decrease font" className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10">
                        <Minus className="w-4 h-4" />
                      </button>
                      <span className="px-2 py-1 text-xs text-white/80 bg-white/5 border border-white/10 rounded min-w-[48px] text-center">{Math.round(fontSizeRem * 100)}%</span>
                      <button onClick={increaseFont} title="Increase font" aria-label="Increase font" className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10">
                        <Plus className="w-4 h-4" />
                      </button>
                      <button onClick={resetFont} title="Reset font" aria-label="Reset font" className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10">
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="h-6 w-px bg-white/10" />
                    <button onClick={handleInsertImage} title="Insert image" aria-label="Insert image" className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10">
                      <ImageIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              {/* Editor with optional wipe transition */}
              <div className={`${wiping ? 'transition duration-200 ease-out opacity-0 blur-[2px]' : ''}`}>
                <RichTextEditor
                  value={editorHtml}
                  onChange={(html) => {
                    setEditorHtml(html);
                    const text = html.replace(/<[^>]*>/g, '');
                    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
                    setWordCount(words);
                    setReadMinutes(Math.max(1, Math.ceil(words / 200)));
                  }}
                  onSelectionChange={(text, range) => { selectionRef.current = { text, ...range }; }}
                  onReady={(editor) => { editorRef.current = editor; }}
                  className={`${gameMode ? 'outline outline-1 outline-violet-400/40' : ''} editor-paragraphs relative w-full min-h-[700px] bg-white/5 border border-white/10 rounded-2xl p-8 text-off text-[18px] leading-8 focus:outline-none backdrop-blur-md before:content-[''] before:absolute before:inset-0 before:rounded-2xl before:pointer-events-none`}
                />
              </div>

              {/* Game Mode: Choices Under Editor */}
              {gameMode && (
                <div className="mt-8">
                  <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-md">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold text-off">Story Choices</h3>
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-violet-400 rounded-full animate-pulse"></div>
                        <span className="text-sm text-violet-300">Game Mode Active</span>
                      </div>
                    </div>

                    {choicesLoading && (
                      <div className="flex items-center justify-center py-8 text-white/70">
                        <div className="w-6 h-6 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mr-3"></div>
                        Loading choices...
                      </div>
                    )}

                    {choicesError && (
                      <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-lg p-4 mb-4">
                        {choicesError}
                      </div>
                    )}

                    {!choicesLoading && !choicesError && choices.length === 0 && (
                      <div className="text-center py-8 text-white/60">
                        No choices available for this chapter yet.
                      </div>
                    )}

                    {!choicesLoading && !choicesError && choices.length > 0 && (
                      <div className="space-y-3">
                        {choices.map((choice) => (
                          <button
                            key={choice.id}
                            onClick={() => setSelectedChoiceId(choice.id)}
                            className={`w-full text-left p-4 rounded-2xl border transition-colors backdrop-blur-md ${
                              selectedChoiceId === choice.id
                                ? 'border-violet-500/50 bg-violet-500/10'
                                : 'border-white/10 bg-white/5 hover:bg-white/10'
                            }`}
                          >
                            <div className="flex items-start space-x-3">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                                selectedChoiceId === choice.id ? 'bg-violet-600 text-white' : 'bg-white/10 text-off'
                              }`}>
                                {selectedChoiceId === choice.id ? '✓' : '?' }
                              </div>
                              <div>
                                <h4 className="text-off font-medium">{choice.title || 'Choice'}</h4>
                                {choice.description && (
                                  <p className="text-sm text-white/70 leading-relaxed">{choice.description}</p>
                                )}
                              </div>
                            </div>
                          </button>
                        ))}

                        {selectedChoiceId && (
                          <div className="mt-4 pt-4 border-t border-white/10">
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
              {/* Undo banner for rewrite */}
              {showUndo && (
                <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-white/10 border border-white/20 text-white/90 rounded-xl px-4 py-2 shadow-lg backdrop-blur-md flex items-center gap-3 z-50">
                  <span>New version saved.</span>
                  <button
                    className="px-2 py-1 text-xs rounded bg-white/15 hover:bg-white/25 border border-white/20"
                    onClick={() => {
                      setEditorHtml(previousHtml);
                      setShowUndo(false);
                    }}
                  >
                    Undo rewrite
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Sidebar */}
        <RightSidebar
          focusCollapsed={focus}
          onContinue={handleGenerateNextChapter}
          onImprove={async () => {
            try {
              const token = session?.access_token;
              if (!token) return;
              const selText = (selectionRef.current?.text || '').trim();
              if (!selText) return;
              const resp = await fetch(createApiUrl(API_ENDPOINTS.REWRITE_TEXT), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ selected_text: selText, story_context: {} })
              });
              if (!resp.ok) return;
              const data = await resp.json();
              const rewritten = (data && data.rewritten_text) ? String(data.rewritten_text) : '';
              if (!rewritten || !editorRef.current) return;
              const editor = editorRef.current;
              const { from, to } = selectionRef.current;
              editor.chain().focus().command(({ tr }) => { tr.insertText(rewritten, from, to); return true; }).run();
              const text = editor.getText();
              const words = text.trim() ? text.trim().split(/\s+/).length : 0;
              setWordCount(words);
              setReadMinutes(Math.max(1, Math.ceil(words / 200)));
            } catch {}
          }}
          onDialogue={() => {}}
          onBrainstorm={() => {}}
          onRewriteChapter={async () => {
            // Re-generate the current chapter content using backend next-chapter API with same chapter number
            if (!storyId || !session?.access_token || !activeChapter) return;
            try {
              // Prepare rewrite UX: page wipe + skeletons
              setPreviousHtml(editorHtml);
              setWiping(true);
              setTimeout(() => {
                setEditorHtml('');
                setWiping(false);
              }, 200);
              setIsRewriting(true);
              setIsGenerating(true);
              // Reuse generate_next_chapter with same chapter number to rewrite
              const resp = await fetch(createApiUrl(API_ENDPOINTS.GENERATE_NEXT_CHAPTER), {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${session.access_token}`
                },
                body: JSON.stringify({
                  story_id: parseInt(storyId),
                  chapter_number: activeChapter.chapter_number,
                  story_outline: story?.story_outline || ''
                })
              });
              if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
              await fetchData();
              // Ensure we reload the same chapter number if user switched
              await handleLoadChapter(activeChapter.chapter_number);
              triggerPageFlip();
              setShowUndo(true);
              setTimeout(() => setShowUndo(false), 30000);
            } catch (e) {
              console.warn('Failed to rewrite chapter:', e);
              // Restore previous content if error
              setEditorHtml(previousHtml);
            } finally {
              setIsGenerating(false);
              setIsRewriting(false);
            }
          }}
        />
      </div>
    </div>
  );
}


