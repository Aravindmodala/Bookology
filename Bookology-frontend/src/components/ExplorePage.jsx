import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
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
  Loader2
} from 'lucide-react';

const ExplorePage = () => {
  const { user, session } = useAuth();
  const navigate = useNavigate();
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedGenre, setSelectedGenre] = useState('');
  const [sortBy, setSortBy] = useState('published_at');
  const [searchQuery, setSearchQuery] = useState('');

  const genres = [
    'All', 'Fantasy', 'Science Fiction', 'Mystery', 'Romance', 
    'Thriller', 'Adventure', 'Drama', 'Comedy', 'Horror', 'Historical'
  ];

  const sortOptions = [
    { value: 'published_at', label: 'Latest', icon: Clock },
    { value: 'created_at', label: 'Newest', icon: Calendar },
    { value: 'story_title', label: 'Title', icon: BookOpen },
    { value: 'total_chapters', label: 'Most Chapters', icon: TrendingUp }
  ];

  const fetchPublicStories = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '12',
        sort_by: sortBy
      });

      if (selectedGenre && selectedGenre !== 'All') {
        params.append('genre', selectedGenre);
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
  }, [page, selectedGenre, sortBy]);

                const handleLike = async (storyId) => {
                if (!user || !session) {
                  navigate('/login');
                  return;
                }

                try {
                  console.log('Toggling like for story:', storyId);
                  console.log('User:', user?.id);
                  console.log('Session token:', session?.access_token ? 'Present' : 'Missing');
                  
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
                    setStories(prev => prev.map(story =>
                      story.id === storyId
                        ? { ...story, like_count: data.like_count, user_liked: data.liked }
                        : story
                    ));
                  } else {
                    const errorText = await response.text();
                    console.error('Failed to toggle like:', response.status, errorText);
                  }
                } catch (error) {
                  console.error('Error toggling like:', error);
                }
              };

                const handleComment = async (storyId) => {
                if (!user || !session) {
                  navigate('/login');
                  return;
                }

                const comment = prompt('Enter your comment:');
                if (!comment || comment.trim() === '') return;

                try {
                  const response = await fetch(createApiUrl(API_ENDPOINTS.ADD_STORY_COMMENT.replace('{story_id}', storyId)), {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${session.access_token}`,
                      'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ comment: comment.trim() })
                  });

      if (response.ok) {
        const data = await response.json();
        setStories(prev => prev.map(story => 
          story.id === storyId 
            ? { ...story, comment_count: data.comment_count }
            : story
        ));
        alert('Comment added successfully!');
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('Failed to add comment:', errorData);
        alert('Failed to add comment. Please try again.');
      }
    } catch (error) {
      console.error('Error adding comment:', error);
    }
  };

  const handleShare = (story) => {
    console.log('Share story:', story);
  };

  const getGenreColor = (genre) => {
    const colors = {
      'Fantasy': 'from-purple-500 to-pink-500',
      'Science Fiction': 'from-blue-500 to-cyan-500',
      'Mystery': 'from-gray-600 to-gray-800',
      'Romance': 'from-pink-500 to-red-500',
      'Thriller': 'from-red-600 to-orange-600',
      'Adventure': 'from-green-500 to-emerald-500',
      'Drama': 'from-indigo-500 to-purple-500',
      'Comedy': 'from-yellow-500 to-orange-500',
      'Horror': 'from-red-800 to-gray-900',
      'Historical': 'from-amber-600 to-orange-600'
    };
    return colors[genre] || 'from-gray-500 to-gray-700';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Recently';
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  };

  const truncateText = (text, maxLength = 150) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  const StoryCard = ({ story }) => {
    const [isLiked, setIsLiked] = useState(story.user_liked || false);
    const [isBookmarked, setIsBookmarked] = useState(false);
    const [likeCount, setLikeCount] = useState(story.like_count || 0);
    const [commentCount, setCommentCount] = useState(story.comment_count || 0);
    
    // Update local state when story props change
    useEffect(() => {
      setLikeCount(story.like_count || 0);
      setCommentCount(story.comment_count || 0);
      setIsLiked(story.user_liked || false);
    }, [story.like_count, story.comment_count, story.user_liked]);

                    return (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:bg-white/10 transition-all duration-300 group h-full flex flex-col"
                  >
        {/* Story Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-sm">
              {story.author_name ? story.author_name.charAt(0).toUpperCase() : 'A'}
            </div>
            <div>
              <p className="text-white font-medium text-sm">
                {story.author_name || 'Anonymous Author'}
              </p>
              <p className="text-gray-400 text-xs">
                {formatDate(story.published_at || story.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsBookmarked(!isBookmarked)}
              className={`p-2 rounded-lg transition-colors ${
                isBookmarked ? 'text-yellow-400 bg-yellow-400/10' : 'text-gray-400 hover:text-yellow-400 hover:bg-yellow-400/10'
              }`}
            >
              <Bookmark className="w-4 h-4" />
            </button>
            <button className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors">
              <MoreHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Story Cover/Image */}
        <div className="relative mb-4">
          {story.cover_image_url ? (
            <img
              src={story.cover_image_url}
              alt={story.story_title}
              className="w-full h-48 object-cover rounded-lg"
            />
          ) : (
            <div className={`w-full h-48 rounded-lg bg-gradient-to-br ${getGenreColor(story.genre)} flex items-center justify-center`}>
              <BookOpen className="w-12 h-12 text-white/80" />
            </div>
          )}
          <div className="absolute top-2 left-2">
            <span className="px-2 py-1 bg-black/50 backdrop-blur-sm text-white text-xs rounded-full">
              {story.genre || 'Fiction'}
            </span>
          </div>
        </div>

                            {/* Story Content */}
                    <div className="mb-4 flex-1">
                      <h3 className="text-white font-bold text-lg mb-2 line-clamp-2">
                        {story.story_title}
                      </h3>
                      <p className="text-gray-300 text-sm leading-relaxed line-clamp-3">
                        {truncateText(story.story_outline || story.summary || 'No description available')}
                      </p>
                    </div>

        {/* Story Stats */}
        <div className="flex items-center justify-between text-xs text-gray-400 mb-4">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <Eye className="w-3 h-3" />
              <span>{story.total_chapters || 0} chapters</span>
            </span>
            <span className="flex items-center space-x-1">
              <Star className="w-3 h-3" />
              <span>{story.estimated_total_words || 0} words</span>
            </span>
          </div>
        </div>

                            {/* Read More Button - Centered */}
                    <div className="flex justify-center mt-4 mb-4">
                      <Link
                        to={`/story/${story.id}`}
                        className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm font-medium rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-200 z-20 relative"
                      >
                        Read More
                      </Link>
                    </div>

                            {/* Action Buttons */}
                    <div className="flex items-center justify-center space-x-4 mt-4">
                      <button
                        onClick={async () => {
                          console.log('Like button clicked for story:', story.id);
                          console.log('Current like state:', isLiked);
                          console.log('Current like count:', likeCount);
                          
                          await handleLike(story.id);
                        }}
                        className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition-colors ${
                          isLiked ? 'text-red-400 bg-red-400/10' : 'text-gray-400 hover:text-red-400 hover:bg-red-400/10'
                        }`}
                      >
                        <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
                        <span className="text-xs">{likeCount > 0 ? likeCount : 'Like'}</span>
                      </button>
                      <button
                        onClick={() => handleComment(story.id)}
                        className="flex items-center space-x-1 px-3 py-2 rounded-lg text-gray-400 hover:text-blue-400 hover:bg-blue-400/10 transition-colors"
                      >
                        <MessageCircle className="w-4 h-4" />
                        <span className="text-xs">{commentCount > 0 ? commentCount : 'Comment'}</span>
                      </button>
                      <button
                        onClick={() => handleShare(story)}
                        className="flex items-center space-x-1 px-3 py-2 rounded-lg text-gray-400 hover:text-green-400 hover:bg-green-400/10 transition-colors"
                      >
                        <Share2 className="w-4 h-4" />
                        <span className="text-xs">Share</span>
                      </button>
                    </div>
      </motion.div>
    );
  };

  if (loading && stories.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-pink-900">
        <div className="flex items-center justify-center min-h-screen">
          <div className="flex items-center space-x-3">
            <Loader2 className="w-6 h-6 text-white animate-spin" />
            <span className="text-white text-lg">Loading stories...</span>
          </div>
        </div>
      </div>
    );
  }

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

      {/* Filters and Search */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col lg:flex-row gap-4 mb-6">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search stories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Genre Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={selectedGenre}
              onChange={(e) => setSelectedGenre(e.target.value)}
              className="px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {genres.map((genre) => (
                <option key={genre} value={genre === 'All' ? '' : genre}>
                  {genre}
                </option>
              ))}
            </select>
          </div>

          {/* Sort */}
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-gray-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-red-400">{error}</p>
          </div>
        )}

                            {/* Stories Grid */}
                    {stories.length === 0 && !loading ? (
                      <div className="text-center py-12">
                        <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-xl font-semibold text-white mb-2">No stories found</h3>
                        <p className="text-gray-400">Try adjusting your filters or check back later for new stories.</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-10">
                        {stories.map((story) => (
                          <StoryCard key={story.id} story={story} />
                        ))}
                      </div>
                    )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center space-x-2 mt-8">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            
            <div className="flex items-center space-x-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = i + 1;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      page === pageNum
                        ? 'bg-purple-500 text-white'
                        : 'text-gray-400 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExplorePage; 