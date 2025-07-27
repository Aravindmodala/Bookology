// bookologyhome.jsx - Bookology Frontend Home/Landing Page
//
// This file implements the main landing page for Bookology, including hero, how-it-works, demo, genres, and footer.
// It provides navigation to the story generator UI and introduces the app to new users.
// Data Flow:
// - User lands here, can navigate to generator via the Start a Story button.
// - No backend calls are made from this file directly.
//
// (Add or update section/component-level comments throughout the file)
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { useAuth } from "./AuthContext";
import Navbar from "./Navbar";
import { useEffect, useState } from "react";
import { supabase, isSupabaseEnabled } from "./supabaseClient";
import { FileText, Calendar, BookOpen, Palette } from "lucide-react";

// 1. Header (with Bookology as logo)
function Header() {
  return (
    <header className="flex items-center justify-between px-8 py-4 bg-black border-b border-white/10">
      <span className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-yellow-400 tracking-tight select-none">
        Bookology
      </span>
      <nav className="hidden md:flex gap-8 text-white/80 text-lg">
        <Link to="/" className="hover:text-white">Home</Link>
        <Link to="/stories" className="hover:text-white">Explore</Link>
        <Link to="/create" className="hover:text-white">Create</Link>
        <a href="#community" className="hover:text-white">Community</a>
        <a href="#about" className="hover:text-white">About</a>
        <a href="#contact" className="hover:text-white">Contact</a>
      </nav>
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-white font-bold">A</div>
      </div>
    </header>
  );
}

// 2. Hero Section
function HeroSection({ onStart }) {
  return (
    <section className="min-h-[60vh] flex flex-col items-center justify-center bg-gradient-to-br from-black via-purple-900 to-black text-center px-4">
      <motion.h1
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl md:text-6xl font-extrabold text-white mb-6 drop-shadow-lg"
      >
        Every great story begins with a whisper…
      </motion.h1>
      <p className="text-xl md:text-2xl text-white/80 mb-8 max-w-2xl mx-auto">
        Join a vibrant community of storytellers. Write, share, and collaborate on books that inspire the world.
      </p>
      <div className="flex gap-4 justify-center">
        <button
          onClick={onStart}
          className="px-8 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold rounded-full shadow-lg hover:scale-105 transition-all text-lg"
        >
          Start a Story
        </button>
        <Link to="/stories" className="px-8 py-3 bg-white/10 text-white font-bold rounded-full border border-white/20 hover:bg-white/20 transition-all text-lg">
          Explore Stories
        </Link>
      </div>
    </section>
  );
}

// 3. Features Section
function FeaturesSection() {
  const features = [
    {
      title: "Write & Create",
      desc: "Craft your own stories with powerful, intuitive tools.",
      icon: "✍️",
    },
    {
      title: "Share & Collaborate",
      desc: "Invite others to read, remix, and contribute to your books.",
      icon: "🤝",
    },
    {
      title: "Discover & Remix",
      desc: "Explore trending books and remix stories in new directions.",
      icon: "🔀",
    },
    {
      title: "Community Driven",
      desc: "Connect with passionate readers and writers worldwide.",
      icon: "🌍",
    },
  ];
  return (
    <section className="py-16 bg-black/90">
      <h2 className="text-3xl md:text-4xl font-bold text-center text-white mb-10">How Bookology Works</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8 max-w-6xl mx-auto px-4">
        {features.map((f, i) => (
          <div key={i} className="bg-white/10 rounded-2xl p-8 flex flex-col items-center text-center shadow-lg border border-white/10">
            <span className="text-4xl mb-4">{f.icon}</span>
            <h3 className="text-xl font-semibold text-white mb-2">{f.title}</h3>
            <p className="text-white/70">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

// 4. Community Highlights (placeholder data)
function CommunityHighlights() {
  const trendingBooks = [
    { title: "The Lost Pages", author: "Jane Doe" },
    { title: "Echoes of Tomorrow", author: "John Smith" },
    { title: "Remix: The Forest Path", author: "Ava Lin" },
  ];
  const topAuthors = ["Jane Doe", "John Smith", "Ava Lin", "Samir Patel"];
  return (
    <section id="community" className="py-16 bg-gradient-to-br from-black via-purple-950 to-black">
      <h2 className="text-3xl md:text-4xl font-bold text-center text-white mb-10">Community Highlights</h2>
      <div className="flex flex-col md:flex-row gap-12 max-w-6xl mx-auto px-4">
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-white mb-4">Trending Books</h3>
          <ul className="space-y-4">
            {trendingBooks.map((b, i) => (
              <li key={i} className="bg-white/10 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between border border-white/10">
                <span className="font-bold text-white">{b.title}</span>
                <span className="text-white/60 text-sm">by {b.author}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-white mb-4">Top Authors</h3>
          <ul className="flex flex-wrap gap-4">
            {topAuthors.map((a, i) => (
              <li key={i} className="bg-white/10 rounded-full px-6 py-2 text-white font-medium border border-white/10">
                {a}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

// 5. Join Prompt
function JoinPrompt() {
  return (
    <section className="py-12 bg-black/95 flex flex-col items-center justify-center text-center">
      <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">Join Bookology and start your story today!</h2>
      <Link to="/login" className="px-8 py-3 bg-gradient-to-r from-pink-500 to-yellow-400 text-black font-bold rounded-full shadow-lg hover:scale-105 transition-all text-lg">
        Sign Up / Log In
      </Link>
    </section>
  );
}

// 6. Footer
function Footer() {
  return (
    <footer className="bg-black border-t border-white/10 py-6 flex flex-col md:flex-row items-center justify-between px-8 text-white/60">
      <div className="flex gap-6 mb-4 md:mb-0">
        <a href="#about" className="hover:text-white transition">About</a>
        <a href="#contact" className="hover:text-white transition">Contact</a>
        <a href="#" className="hover:text-white transition">GitHub</a>
        <a href="#" className="hover:text-white transition">Privacy</a>
      </div>
      <div className="text-xs">© {new Date().getFullYear()} Bookology. All rights reserved.</div>
    </footer>
  );
}

// Your Books Section
function YourBooksSection({ user, session }) {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user || !isSupabaseEnabled || !supabase) {
      setBooks([]);
      setLoading(false);
      return;
    }
    let isMounted = true;
    const fetchBooks = async () => {
      setLoading(true);
      try {
        const { data: Stories, error } = await supabase
          .from('Stories')
          .select('*, Chapters(count)')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });
        if (error) throw error;
        const transformed = Stories?.map(story => ({
          ...story,
          chapter_count: story.Chapters?.[0]?.count || 0,
          title: story.story_title,
          outline: story.story_outline
        })) || [];
        if (isMounted) setBooks(transformed);
      } catch (err) {
        if (isMounted) setBooks([]);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchBooks();
    return () => { isMounted = false; };
  }, [user]);

  if (!user || !isSupabaseEnabled) return null;
  if (loading) return <div className="text-center text-white/60 py-8">Loading your books...</div>;
  if (!books.length) return <div className="text-center text-white/60 py-8">You haven't created any books yet. <Link to="/create" className="text-blue-400 underline">Start your first story!</Link></div>;

  return (
    <section className="py-16 bg-black/95">
      <h2 className="text-3xl md:text-4xl font-bold text-center text-white mb-10">Your Books</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto px-4">
        {books.slice(0, 6).map((story) => (
          <div key={story.id} className="bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition-all duration-200 hover:scale-[1.02] group z-50 relative overflow-visible">
            {/* Cover Image Section (placeholder) */}
            <div className="relative h-40 bg-gradient-to-br from-gray-700 via-gray-800 to-gray-900 overflow-hidden flex items-center justify-center">
              <BookOpen className="w-12 h-12 text-gray-400" />
            </div>
            {/* Content Section */}
            <div className="p-4 relative z-0">
              <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors line-clamp-1">
                {story.story_title || 'Untitled Story'}
              </h3>
              <p className="text-gray-400 text-sm line-clamp-2 mb-2">
                {story.story_outline || 'No description available'}
              </p>
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span className="flex items-center"><FileText className="w-3 h-3 mr-1" />{story.chapter_count || 0}</span>
                <span className="flex items-center"><Calendar className="w-3 h-3 mr-1" />{story.created_at ? new Date(story.created_at).toLocaleDateString() : 'Unknown'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// Main Home Component
export default function BookologyHome({ onStart }) {
  const { isSupabaseEnabled, user, session } = useAuth();
  return (
    <div className="min-h-screen w-screen bg-black text-white font-serif">
      <Header />
      {/* Development Notice */}
      {!isSupabaseEnabled && (
        <div className="bg-yellow-600/20 border border-yellow-500/50 text-yellow-200 px-4 py-2 text-center text-sm">
          ⚠️ Development Mode: Supabase not configured. Some features may be limited.
        </div>
      )}
      <HeroSection onStart={onStart} />
      <FeaturesSection />
      <YourBooksSection user={user} session={session} />
      <CommunityHighlights />
      <JoinPrompt />
      <Footer />
    </div>
  );
}
