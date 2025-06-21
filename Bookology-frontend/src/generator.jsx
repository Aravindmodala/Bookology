import React, { useState } from 'react';

export default function Generator() {
  const [idea, setIdea] = useState('');
  const [format, setFormat] = useState('book');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [chapter, setChapter] = useState('');
  const [chapterLoading, setChapterLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setResult('');
    setChapter('');
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

  return (
    <div className="min-h-screen w-screen bg-black flex items-center justify-center">
      <div className="bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl p-10 w-full max-w-md border border-white/20 flex flex-col items-center">
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
          </div>
        )}
      </div>
    </div>
  );
}