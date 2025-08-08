// bookologyhome.jsx - Bookology Frontend Home/Landing Page (Suno-inspired design)
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { useEffect, useState, useRef } from "react";
import { supabase, isSupabaseEnabled } from "./supabaseClient";
import { 
  FileText, 
  Calendar, 
  BookOpen, 
  User, 
  Settings, 
  LogOut, 
  LayoutDashboard,
  Home,
  PenTool,
  Search,
  Radio,
  Bell,
  Globe,
  Play,
  Heart,
  MessageCircle,
  TrendingUp,
  Users,
  Crown,
  Sparkles,
  Music,
  BookMarked,
  Plus,
  ChevronRight,
  ExternalLink,
  Star,
  Eye,
  Share2,
  Bookmark,
  MoreHorizontal
} from "lucide-react";

// Sidebar Navigation Component
function Sidebar({ user, onLogout }) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const navigationItems = [
    { icon: Home, label: "Home", path: "/", active: true },
    { icon: PenTool, label: "Create", path: "/create" },
    { icon: BookMarked, label: "Library", path: "/stories" },
    { icon: Search, label: "Search", path: "/search" },
    { icon: Radio, label: "Explore", path: "/explore" },
    { icon: Globe, label: "Discover", path: "/discover" },
    { icon: Bell, label: "Notifications", path: "/notifications" },
  ];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  return (
    <div className="w-64 bg-black/20 backdrop-blur-xl border-r border-white/10 h-screen fixed left-0 top-0 z-40">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <span className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-yellow-400 tracking-tight">
          BOOKOLOGY
        </span>
      </div>

      {/* User Profile Section */}
      <div className="p-4 border-b border-white/10">
        {user ? (
          <div className="flex items-center space-x-3" ref={dropdownRef}>
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-sm shadow-lg">
              {user.email ? user.email.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">
                {user.email ? user.email.split('@')[0] : 'User'}
              </p>
              <p className="text-gray-400 text-xs">@{user.email ? user.email.split('@')[0] : 'user'}</p>
            </div>
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <ChevronRight className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-90' : ''}`} />
            </button>
          </div>
        ) : (
          <div className="text-center">
            <Link 
              to="/login" 
              className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-purple-500/80 to-pink-500/80 backdrop-blur-sm text-white font-medium rounded-lg hover:from-purple-600/90 hover:to-pink-600/90 transition-all text-sm border border-white/20"
            >
              Sign In
            </Link>
          </div>
        )}

        {/* User Dropdown Menu */}
        {isDropdownOpen && user && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 bg-black/40 backdrop-blur-xl border border-white/20 rounded-lg shadow-2xl py-2"
          >
            <Link 
              to="/stories" 
              className="flex items-center gap-3 px-4 py-2 text-white hover:bg-white/10 transition-colors text-sm"
              onClick={() => setIsDropdownOpen(false)}
            >
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </Link>
            <Link 
              to="/profile" 
              className="flex items-center gap-3 px-4 py-2 text-white hover:bg-white/10 transition-colors text-sm"
              onClick={() => setIsDropdownOpen(false)}
            >
              <User className="w-4 h-4" />
              Profile
            </Link>
            <Link 
              to="/settings" 
              className="flex items-center gap-3 px-4 py-2 text-white hover:bg-white/10 transition-colors text-sm"
              onClick={() => setIsDropdownOpen(false)}
            >
              <Settings className="w-4 h-4" />
              Settings
            </Link>
            <div className="border-t border-white/10 mt-2 pt-2">
              <button
                onClick={() => {
                  onLogout();
                  setIsDropdownOpen(false);
                }}
                className="flex items-center gap-3 w-full text-left px-4 py-2 text-red-400 hover:bg-white/10 transition-colors text-sm"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            </div>
          </motion.div>
        )}
      </div>

      {/* Navigation Menu */}
      <nav className="p-4">
        <ul className="space-y-2">
          {navigationItems.map((item) => (
            <li key={item.label}>
              <Link
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  item.active 
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30 backdrop-blur-sm shadow-lg' 
                    : 'text-gray-400 hover:text-white hover:bg-white/10 backdrop-blur-sm'
                }`}
              >
                <item.icon className="w-5 h-5" />
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {/* Invite Friends */}
      <div className="absolute bottom-4 left-4 right-4">
        <Link 
          to="/invite" 
          className="flex items-center justify-center gap-2 text-gray-400 hover:text-white transition-colors text-sm bg-white/5 backdrop-blur-sm rounded-lg p-2 hover:bg-white/10"
        >
          <Users className="w-4 h-4" />
          Invite friends
        </Link>
      </div>
    </div>
  );
}

// Hero Section with Live Content
function HeroSection({ onStart }) {
  return (
    <div className="relative h-96 bg-gradient-to-br from-blue-600/10 via-purple-600/10 to-pink-600/10 rounded-2xl overflow-hidden mb-8 border border-white/10 backdrop-blur-sm">
      {/* Animated Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-purple-900/20 to-pink-900/20"></div>
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/5 to-transparent animate-pulse"></div>
        {/* Glass morphism overlay */}
        <div className="absolute inset-0 bg-white/5 backdrop-blur-sm"></div>
      </div>
      
      {/* Content */}
      <div className="relative z-10 h-full flex flex-col items-center justify-center text-center px-8">
        {/* New Feature Badge */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-4"
        >
          <span className="inline-flex items-center px-3 py-1 bg-pink-500/20 text-pink-300 text-xs font-medium rounded-full border border-pink-500/30 backdrop-blur-xl shadow-lg">
            <Sparkles className="w-3 h-3 mr-1" />
            NEW FEATURE
          </span>
        </motion.div>

        {/* Main Heading */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="text-4xl md:text-5xl font-bold text-white mb-4 leading-tight"
        >
          Stories that never end,<br />
          <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-yellow-400 bg-clip-text text-transparent">
            crafted by all of us.
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="text-xl text-gray-300 mb-6 max-w-2xl"
        >
          Celebrating community choice, Fantasy drives this epic tale, enhanced by Adventure, Mystery, and Romance elements.
        </motion.p>

        {/* Live Controls */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="flex items-center gap-4 bg-black/30 backdrop-blur-xl rounded-full px-6 py-3 border border-white/20 shadow-2xl"
        >
          <button className="w-10 h-10 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center transition-all hover:scale-110 backdrop-blur-sm">
            <Play className="w-5 h-5 text-white fill-white" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-white text-sm font-medium">Live</span>
          </div>
          <div className="flex items-center gap-2 text-gray-300 text-sm">
            <Users className="w-4 h-4" />
            <span>168 Readers</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

// Beautiful Story Card Component
function StoryCard({ story, type = "trending" }) {
  const [isLiked, setIsLiked] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);

  const getGenreColor = (genre) => {
    const colors = {
      'fantasy': 'text-purple-400 bg-purple-400/10',
      'adventure': 'text-blue-400 bg-blue-400/10',
      'mystery': 'text-green-400 bg-green-400/10',
      'romance': 'text-pink-400 bg-pink-400/10',
      'scifi': 'text-cyan-400 bg-cyan-400/10',
      'horror': 'text-red-400 bg-red-400/10',
      'thriller': 'text-orange-400 bg-orange-400/10'
    };
    return colors[genre?.toLowerCase()] || 'text-gray-400 bg-gray-400/10';
  };

  const getCoverGradient = (genre) => {
    const gradients = {
      'fantasy': 'from-purple-600/20 via-pink-600/20 to-blue-600/20',
      'adventure': 'from-blue-600/20 via-cyan-600/20 to-green-600/20',
      'mystery': 'from-green-600/20 via-emerald-600/20 to-teal-600/20',
      'romance': 'from-pink-600/20 via-rose-600/20 to-red-600/20',
      'scifi': 'from-cyan-600/20 via-blue-600/20 to-indigo-600/20',
      'horror': 'from-red-600/20 via-pink-600/20 to-purple-600/20'
    };
    return gradients[genre?.toLowerCase()] || 'from-gray-600/20 via-gray-700/20 to-gray-800/20';
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -5 }}
      className="bg-black/20 backdrop-blur-xl rounded-xl border border-white/10 hover:border-white/20 transition-all duration-300 hover:scale-[1.02] group overflow-hidden shadow-2xl hover:shadow-purple-500/20"
    >
      {/* Cover Image */}
      <div className={`relative h-48 bg-gradient-to-br ${getCoverGradient(story.genre)} overflow-hidden`}>
        {story.cover_image_url ? (
          <img 
            src={story.cover_image_url} 
            alt={story.story_title || 'Story cover'}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onError={(e) => {
              console.error('Failed to load cover image:', story.cover_image_url);
              e.target.style.display = 'none';
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <BookOpen className="w-16 h-16 text-white/60" />
          </div>
        )}
        
        {/* Glass morphism overlay */}
        <div className="absolute inset-0 bg-white/5 backdrop-blur-sm"></div>
        
        {/* Overlay with stats */}
        <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between text-xs text-white">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 bg-black/40 backdrop-blur-xl px-2 py-1 rounded-full border border-white/20">
              <Play className="w-3 h-3" />
              {story.views || Math.floor(Math.random() * 50) + 1}K
            </span>
            <span className="flex items-center gap-1 bg-black/40 backdrop-blur-xl px-2 py-1 rounded-full border border-white/20">
              <Heart className="w-3 h-3" />
              {story.likes || Math.floor(Math.random() * 200) + 50}
            </span>
            <span className="flex items-center gap-1 bg-black/40 backdrop-blur-xl px-2 py-1 rounded-full border border-white/20">
              <MessageCircle className="w-3 h-3" />
              {story.comments || Math.floor(Math.random() * 50) + 10}
            </span>
          </div>
        </div>

        {/* Action buttons overlay */}
        <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="p-1.5 bg-black/50 hover:bg-black/70 rounded-lg text-white transition-all hover:scale-110 backdrop-blur-sm border border-white/20">
            <Share2 className="w-3 h-3" />
          </button>
          <button className="p-1.5 bg-black/50 hover:bg-black/70 rounded-lg text-white transition-all hover:scale-110 backdrop-blur-sm border border-white/20">
            <MoreHorizontal className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors line-clamp-1 flex-1">
            {story.title || story.story_title || 'Untitled Story'}
          </h3>
          <button 
            onClick={() => setIsBookmarked(!isBookmarked)}
            className={`ml-2 p-1 rounded-lg transition-colors ${
              isBookmarked ? 'text-yellow-400' : 'text-gray-400 hover:text-yellow-400'
            }`}
          >
            <Bookmark className={`w-4 h-4 ${isBookmarked ? 'fill-current' : ''}`} />
          </button>
        </div>
        
        <p className="text-gray-400 text-sm line-clamp-2 mb-3">
          {story.description || story.story_outline || 'A captivating story that will keep you on the edge of your seat.'}
        </p>
        
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white text-xs font-bold shadow-lg">
              {story.author?.charAt(0) || 'A'}
            </div>
            <span className="text-gray-300 text-sm">{story.author || 'Anonymous Author'}</span>
          </div>
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${getGenreColor(story.genre)} backdrop-blur-sm border border-white/10`}>
            {story.genre || 'Fiction'}
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between">
          <button 
            onClick={() => setIsLiked(!isLiked)}
            className={`flex items-center gap-1 text-sm transition-colors ${
              isLiked ? 'text-red-400' : 'text-gray-400 hover:text-red-400'
            }`}
          >
            <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
            {isLiked ? 'Liked' : 'Like'}
          </button>
          <Link 
            to={`/story/${story.id}`}
            className="flex items-center text-sm text-blue-400 hover:text-blue-300 transition-colors font-medium hover:underline"
          >
            Read Story
            <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>
    </motion.div>
  );
}

// For You Section
function ForYouSection({ userStories }) {
  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">For You</h2>
        <Link to="/stories" className="text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1 group">
          View All
          <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </Link>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {userStories.slice(0, 3).map((story, index) => (
          <StoryCard key={story.id || index} story={story} type="for-you" />
        ))}
      </div>
    </section>
  );
}

// Trending Section
function TrendingSection() {
  const trendingStories = [
    {
      id: 1,
      title: "The Last Echo",
      description: "A haunting mystery with supernatural elements, dark fantasy, and psychological thriller themes that will keep you guessing until the very end.",
      author: "Sarah Chen",
      genre: "mystery",
      views: 45,
      likes: 892,
      comments: 156
    },
    {
      id: 2,
      title: "Beyond the Stars",
      description: "An epic space adventure exploring the depths of human consciousness and alien civilizations in a universe where nothing is as it seems.",
      author: "Marcus Rodriguez",
      genre: "scifi",
      views: 38,
      likes: 745,
      comments: 123
    },
    {
      id: 3,
      title: "Whispers of the Heart",
      description: "A tender romance set against the backdrop of a magical academy, where love transcends all boundaries and magic flows through every page.",
      author: "Emma Thompson",
      genre: "romance",
      views: 52,
      likes: 1023,
      comments: 234
    }
  ];

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Trending</h2>
        <div className="flex items-center gap-2">
          <select className="bg-black/20 backdrop-blur-xl border border-white/10 rounded-lg px-3 py-1 text-white text-sm focus:border-blue-500 focus:outline-none">
            <option>Global</option>
            <option>Local</option>
          </select>
          <select className="bg-black/20 backdrop-blur-xl border border-white/10 rounded-lg px-3 py-1 text-white text-sm focus:border-blue-500 focus:outline-none">
            <option>Now</option>
            <option>This Week</option>
            <option>This Month</option>
          </select>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {trendingStories.map((story, index) => (
          <StoryCard key={story.id} story={story} type="trending" />
        ))}
      </div>
    </section>
  );
}

// Suggested Creators Section
function SuggestedCreatorsSection() {
  const creators = [
    {
      id: 1,
      name: "AlexWriter",
      handle: "@alexwriter",
      followers: "12K",
      avatar: "A",
      rating: "18+",
      specialty: "Fantasy & Adventure"
    },
    {
      id: 2,
      name: "StoryCraft",
      handle: "@storycraft",
      followers: "8.5K",
      avatar: "S",
      rating: "13+",
      specialty: "Mystery & Thriller"
    },
    {
      id: 3,
      name: "NarrativePro",
      handle: "@narrativepro",
      followers: "15K",
      avatar: "N",
      rating: "18+",
      specialty: "Romance & Drama"
    }
  ];

  return (
    <section className="mb-8">
      <h2 className="text-2xl font-bold text-white mb-6">Suggested Creators</h2>
      <div className="space-y-4">
        {creators.map((creator) => (
          <motion.div 
            key={creator.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            whileHover={{ x: 5 }}
            className="flex items-center justify-between p-4 bg-black/20 backdrop-blur-xl rounded-xl border border-white/10 hover:border-white/20 transition-all duration-300 shadow-lg hover:shadow-purple-500/20"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold shadow-lg">
                {creator.avatar}
              </div>
              <div>
                <p className="text-white font-medium">{creator.name}</p>
                <p className="text-gray-400 text-sm">{creator.followers} followers</p>
                <p className="text-gray-500 text-xs">{creator.handle} - Suggested</p>
                <p className="text-blue-400 text-xs mt-1">{creator.specialty}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 bg-black/40 backdrop-blur-xl text-gray-300 text-xs rounded-full border border-white/10">
                {creator.rating}
              </span>
              <button className="px-4 py-2 bg-blue-600/80 hover:bg-blue-700/90 text-white text-sm rounded-lg transition-colors hover:scale-105 backdrop-blur-sm border border-white/20">
                Follow
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

// Main Content Area
function MainContent({ user, userStories, onStart }) {
  return (
    <div className="ml-64 p-8">
      {/* Search Bar */}
      <div className="flex items-center gap-4 mb-8">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search for stories, authors, or genres..."
            className="w-full bg-black/20 backdrop-blur-xl border border-white/10 rounded-xl pl-10 pr-4 py-3 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none transition-colors shadow-lg"
          />
        </div>
        <Link
          to="/create"
          className="px-6 py-3 bg-gradient-to-r from-purple-500/80 to-pink-500/80 backdrop-blur-sm text-white font-semibold rounded-xl hover:from-purple-600/90 hover:to-pink-600/90 transition-all flex items-center gap-2 hover:scale-105 shadow-2xl border border-white/20"
        >
          <Plus className="w-5 h-5" />
          Create
        </Link>
        <button className="p-3 bg-black/20 backdrop-blur-xl border border-white/10 rounded-xl text-gray-400 hover:text-white hover:border-white/20 transition-all hover:scale-105 shadow-lg">
          <Search className="w-5 h-5" />
        </button>
      </div>

      {/* Hero Section */}
      <HeroSection onStart={onStart} />

      {/* Content Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - For You & Trending */}
        <div className="lg:col-span-2">
          <ForYouSection userStories={userStories} />
          <TrendingSection />
        </div>

        {/* Right Column - Suggested Creators */}
        <div className="lg:col-span-1">
          <SuggestedCreatorsSection />
        </div>
      </div>
    </div>
  );
}

// Main Home Component
export default function BookologyHome({ onStart }) {
  const { user, session } = useAuth();
  const [userStories, setUserStories] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch user stories
  useEffect(() => {
    if (!user || !isSupabaseEnabled || !supabase) {
      setUserStories([]);
      setLoading(false);
      return;
    }
    
    const fetchUserStories = async () => {
      setLoading(true);
      try {
        const { data: Stories, error } = await supabase
          .from('Stories')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false })
          .limit(6);
        
        if (error) throw error;
        
        const transformed = Stories?.map(story => ({
          ...story,
          title: story.story_title,
          description: story.story_outline,
          author: user.email?.split('@')[0] || 'You'
        })) || [];
        
        setUserStories(transformed);
      } catch (err) {
        console.error('Error fetching user stories:', err);
        setUserStories([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchUserStories();
  }, [user]);

  const handleLogout = async () => {
    try {
      if (supabase) {
        await supabase.auth.signOut();
      }
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black text-white">
      {/* Development Notice */}
      {!isSupabaseEnabled && (
        <div className="fixed top-0 left-64 right-0 z-50 bg-yellow-600/20 border-b border-yellow-500/50 text-yellow-200 px-4 py-2 text-center text-sm backdrop-blur-sm">
          ⚠️ Development Mode: Supabase not configured. Some features may be limited.
        </div>
      )}
      
      {/* Sidebar */}
      <Sidebar user={user} onLogout={handleLogout} />
      
      {/* Main Content */}
      <MainContent 
        user={user} 
        userStories={userStories} 
        onStart={onStart}
      />
    </div>
  );
}
