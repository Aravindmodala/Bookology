import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { createApiUrl, API_ENDPOINTS } from '../config';
import { 
  Heart, 
  MessageCircle, 
  Eye, 
  BookOpen, 
  User, 
  Calendar,
  Filter,
  Search,
  TrendingUp,
  Clock,
  Star,
  Share2,
  Bookmark,
  MoreHorizontal,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Sparkles,
  Users,
  Zap,
  Target
} from 'lucide-react';
import EnhancedStoryCard from './EnhancedStoryCard';
import AdvancedFilters from './AdvancedFilters';

const ExplorePage = () => {
  const { user, session } = useAuth();
  const navigate = useNavigate();
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Enhanced filter states
  const [selectedGenre, setSelectedGenre] = useState('');
  const [selectedMood, setSelectedMood] = useState('all');
  const [selectedReadingTime, setSelectedReadingTime] = useState('all');
  const [selectedCompletion, setSelectedCompletion] = useState('all');
  const [selectedCommunity, setSelectedCommunity] = useState('all');
  const [sortBy, setSortBy] = useState('published_at');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchPublicStories = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '12',
        sort_by: sortBy
      });

      // Add all filter parameters
      if (selectedGenre && selectedGenre !== 'All') {
        params.append('genre', selectedGenre);
      }
      if (selectedMood !== 'all') {
        params.append('mood', selectedMood);
      }
      if (selectedReadingTime !== 'all') {
        params.append('reading_time', selectedReadingTime);
      }
      if (selectedCompletion !== 'all') {
        params.append('completion_status', selectedCompletion);
      }
      if (selectedCommunity !== 'all') {
        params.append('community_filter', selectedCommunity);
      }
      if (searchQuery.trim()) {
        params.append('search', searchQuery.trim());
      }

      const response = await fetch(createApiUrl(`${API_ENDPOINTS.GET_PUBLIC_STORIES}?${params}`));
      
      if (!response.ok) {
        throw new Error('Failed to fetch stories');
      }

      const data = await response.json();
      setStories(data.stories || []);
      setTotalPages(data.total_pages || 1);
      setError(null);
    } catch (err) {
      console.error('Error fetching public stories:', err);
      setError('Failed to load stories. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPublicStories();
  }, [page, selectedGenre, selectedMood, selectedReadingTime, selectedCompletion, selectedCommunity, sortBy, searchQuery]);

  const handleLike = async (storyId) => {
    if (!user || !session) {
      navigate('/login');
      return false;
    }

    try {
      console.log('Toggling like for story:', storyId);
      
      const response = await fetch(createApiUrl(API_ENDPOINTS.TOGGLE_STORY_LIKE.replace('{story_id}', storyId)), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('Like response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Like response data:', data);
        
        // Update the story in the list
        setStories(prevStories => 
          prevStories.map(story => 
            story.id === storyId 
              ? { 
                  ...story, 
                  is_liked: !story.is_liked,
                  like_count: story.is_liked ? story.like_count - 1 : story.like_count + 1
                }
              : story
          )
        );
        
        return true;
      } else {
        console.error('Failed to toggle like');
        return false;
      }
    } catch (err) {
      console.error('Error toggling like:', err);
      return false;
    }
  };

  const handleComment = async (storyId) => {
    if (!user || !session) {
      navigate('/login');
      return;
    }

    try {
      // For now, just navigate to the story page where comments can be made
      navigate(`/story/${storyId}#comments`);
    } catch (err) {
      console.error('Error handling comment:', err);
    }
  };

  const handleShare = (story) => {
    try {
      const shareData = {
        title: story.story_title,
        text: story.description || story.story_outline,
        url: `${window.location.origin}/story/${story.id}`
      };

      if (navigator.share) {
        navigator.share(shareData);
      } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(shareData.url);
        // You could add a toast notification here
        console.log('Story URL copied to clipboard');
      }
    } catch (err) {
      console.error('Error sharing story:', err);
    }
  };

  const LoadingSkeleton = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {[...Array(8)].map((_, index) => (
        <motion.div
          key={index}
          className="bg-white/5 rounded-xl h-80 animate-pulse"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <div className="h-48 bg-white/10 rounded-t-xl"></div>
          <div className="p-4 space-y-3">
            <div className="h-4 bg-white/10 rounded"></div>
            <div className="h-3 bg-white/10 rounded w-3/4"></div>
            <div className="h-3 bg-white/10 rounded w-1/2"></div>
          </div>
        </motion.div>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-pink-900">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-xl border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white">Explore Stories</h1>
                <p className="text-gray-400 text-sm">Discover amazing stories from our community</p>
              </div>
            </div>
            {user && (
              <Link
                to="/create"
                className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-200"
              >
                Create Story
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Advanced Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <AdvancedFilters
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          selectedGenre={selectedGenre}
          setSelectedGenre={setSelectedGenre}
          selectedMood={selectedMood}
          setSelectedMood={setSelectedMood}
          selectedReadingTime={selectedReadingTime}
          setSelectedReadingTime={setSelectedReadingTime}
          selectedCompletion={selectedCompletion}
          setSelectedCompletion={setSelectedCompletion}
          selectedCommunity={selectedCommunity}
          setSelectedCommunity={setSelectedCommunity}
          sortBy={sortBy}
          setSortBy={setSortBy}
        />
      </div>

      {/* Stories Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg"
          >
            <p className="text-red-400">{error}</p>
          </motion.div>
        )}

        {/* Loading State */}
        {loading ? (
          <LoadingSkeleton />
        ) : (
          <>
            {/* Stories Count */}
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center space-x-2 text-white/60">
                <BookOpen className="w-4 h-4" />
                <span>{stories.length} stories found</span>
              </div>
              <div className="flex items-center space-x-2 text-white/60">
                <Sparkles className="w-4 h-4" />
                <span>Enhanced Discovery</span>
              </div>
            </div>

            {/* Stories Grid */}
            {stories.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-12"
              >
                <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No stories found</h3>
                <p className="text-gray-400">Try adjusting your filters or check back later for new stories.</p>
              </motion.div>
            ) : (
              <motion.div
                className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
              >
                <AnimatePresence>
                  {stories.map((story, index) => (
                    <motion.div
                      key={story.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ delay: index * 0.1, duration: 0.5 }}
                    >
                      <EnhancedStoryCard
                        story={story}
                        onLike={handleLike}
                        onComment={handleComment}
                        onShare={handleShare}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </motion.div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 flex items-center justify-center space-x-2">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="p-2 rounded-lg bg-white/10 text-white/70 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-5 h-5" />
                </motion.button>
                
                <span className="text-white/60 px-4">
                  Page {page} of {totalPages}
                </span>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="p-2 rounded-lg bg-white/10 text-white/70 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-5 h-5" />
                </motion.button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ExplorePage; 