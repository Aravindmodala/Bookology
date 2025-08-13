import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../AuthContext';
import { createApiUrl, API_ENDPOINTS } from '../config';
import {
  Heart,
  MessageCircle,
  Eye,
  BookOpen,
  User,
  Calendar,
  ChevronLeft,
  Share2,
  Bookmark,
  MoreHorizontal,
  Loader2,
  ArrowLeft,
  Clock,
  Star,
  Globe,
  Lock
} from 'lucide-react';

const StoryView = () => {
  const { storyId } = useParams();
  const navigate = useNavigate();
  const { user, session } = useAuth();
  const [story, setStory] = useState(null);
  const [chapters, setChapters] = useState([]);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLiked, setIsLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [commentCount, setCommentCount] = useState(0);
  const [newComment, setNewComment] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [currentChapterIndex, setCurrentChapterIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    fetchStoryDetails();
  }, [storyId]);

  const fetchStoryDetails = async () => {
    try {
      setLoading(true);
      
      // Fetch story details
      const storyResponse = await fetch(createApiUrl(API_ENDPOINTS.GET_STORY_DETAILS.replace('{story_id}', storyId)));
      if (!storyResponse.ok) {
        throw new Error('Story not found');
      }
      const storyData = await storyResponse.json();
      setStory(storyData);

      // Fetch chapters
      const chaptersResponse = await fetch(createApiUrl(API_ENDPOINTS.GET_STORY_CHAPTERS.replace('{story_id}', storyId)));
      if (chaptersResponse.ok) {
        const chaptersData = await chaptersResponse.json();
        setChapters(chaptersData.chapters || []);
      }

      // Fetch likes and comments
      await fetchStoryStats();

    } catch (err) {
      console.error('Error fetching story details:', err);
      setError('Failed to load story. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStoryStats = async () => {
    try {
      // Fetch likes (only attach auth header if we have a valid session token)
      const token = session?.access_token;
      const likesResponse = await fetch(
        createApiUrl(API_ENDPOINTS.GET_STORY_LIKES.replace('{story_id}', storyId)),
        {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        }
      );
      
      if (likesResponse.ok) {
        const likesData = await likesResponse.json();
        setLikeCount(likesData.like_count || 0);
        setIsLiked(likesData.user_liked || false);
      }

      // Fetch comments
      const commentsResponse = await fetch(createApiUrl(API_ENDPOINTS.GET_STORY_COMMENTS.replace('{story_id}', storyId)));
      if (commentsResponse.ok) {
        const commentsData = await commentsResponse.json();
        setComments(commentsData.comments || []);
        setCommentCount(commentsData.total || 0);
      }
    } catch (err) {
      console.error('Error fetching story stats:', err);
    }
  };

  const handleLike = async () => {
    if (!user || !session) {
      navigate('/login');
      return;
    }

    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.TOGGLE_STORY_LIKE.replace('{story_id}', storyId)), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setIsLiked(data.liked);
        setLikeCount(data.like_count);
      } else {
        console.error('Failed to toggle like');
      }
    } catch (error) {
      console.error('Error toggling like:', error);
    }
  };

  const handleComment = async (e) => {
    e.preventDefault();
    if (!user || !session) {
      navigate('/login');
      return;
    }

    if (!newComment.trim()) return;

    try {
      setSubmittingComment(true);
      const response = await fetch(createApiUrl(API_ENDPOINTS.ADD_STORY_COMMENT.replace('{story_id}', storyId)), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ comment: newComment.trim() })
      });

      if (response.ok) {
        const data = await response.json();
        setComments(prev => [data.comment, ...prev]);
        setCommentCount(data.comment_count);
        setNewComment('');
      } else {
        console.error('Failed to add comment');
      }
    } catch (error) {
      console.error('Error adding comment:', error);
    } finally {
      setSubmittingComment(false);
    }
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

  // compute current chapter safely
  const currentChapter = useMemo(() => chapters[currentChapterIndex] || null, [chapters, currentChapterIndex]);

  // reading progress based on scroll within main content
  useEffect(() => {
    const onScroll = () => {
      const el = document.getElementById('reader-main');
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const total = rect.height - window.innerHeight;
      const passed = Math.min(Math.max(-rect.top, 0), total > 0 ? total : 0);
      const pct = total > 0 ? (passed / total) * 100 : 0;
      setProgress(pct);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, [currentChapterIndex]);

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

  if (loading) {
    return (
      <div className="min-h-screen bg-page">
        <div className="flex items-center justify-center min-h-screen">
          <div className="flex items-center space-x-3">
            <Loader2 className="w-6 h-6 text-white animate-spin" />
            <span className="text-white text-lg">Loading story...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-page">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-white mb-4">Story Not Found</h1>
            <p className="text-gray-400 mb-6">{error}</p>
            <Link
              to="/explore"
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-200"
            >
              Back to Explore
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-page">
      {/* Header */}
      <div className="glass">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white">{story?.story_title}</h1>
                <p className="text-gray-400 text-sm">by {story?.author_name || 'Anonymous Author'}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="hidden md:flex items-center text-white/70 text-sm">
                <span className="mr-3">Chapter {currentChapterIndex + 1} / {chapters.length || 1}</span>
              </div>
              <button
                onClick={handleLike}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  isLiked ? 'text-red-400 bg-red-400/10' : 'text-gray-400 hover:text-red-400 hover:bg-red-400/10'
                }`}
              >
                <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
                <span>{likeCount}</span>
              </button>
              <button className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors">
                <Share2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Story Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 mb-8"
            >
              <div className="flex items-start space-x-4 mb-6">
                {story?.cover_image_url ? (
                  <img
                    src={story.cover_image_url}
                    alt={story.story_title}
                    className="w-24 h-32 object-cover rounded-lg"
                  />
                ) : (
                  <div className={`w-24 h-32 rounded-lg bg-gradient-to-br ${getGenreColor(story?.genre)} flex items-center justify-center`}>
                    <BookOpen className="w-8 h-8 text-white/80" />
                  </div>
                )}
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-white mb-2">{story?.story_title}</h2>
                  <p className="text-gray-300 mb-4">{story?.story_outline || story?.summary}</p>
                  <div className="flex items-center space-x-4 text-sm text-gray-400">
                    <span className="flex items-center space-x-1">
                      <Eye className="w-4 h-4" />
                      <span>{chapters.length} chapters</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Star className="w-4 h-4" />
                      <span>{story?.estimated_total_words || 0} words</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDate(story?.published_at || story?.created_at)}</span>
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Reader: Single chapter view */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="glass rounded-xl p-6" id="reader-main"
            >
              {chapters.length === 0 ? (
                <div className="text-center py-12">
                  <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-400">No chapters available yet.</p>
                </div>
              ) : (
                <div>
                  <h4 className="text-xl font-semibold text-white mb-2 tracking-wide">
                    {(chapters[currentChapterIndex]?.title) || `Chapter ${chapters[currentChapterIndex]?.chapter_number}`}
                  </h4>
                  <div className="prose-novel text-white/90">
                    <p className="drop-cap">{(chapters[currentChapterIndex]?.content || '').split('\n\n')[0]}</p>
                    {((chapters[currentChapterIndex]?.content || '').split('\n\n').slice(1)).map((para, i) => (
                      <p key={i}>{para}</p>
                    ))}
                  </div>
                  <div className="mt-6 flex items-center justify-between">
                    <button
                      disabled={currentChapterIndex === 0}
                      onClick={() => setCurrentChapterIndex(i => Math.max(0, i - 1))}
                      className="px-3 py-2 rounded-lg border border-white/10 text-white/80 hover:bg-white/10 disabled:opacity-40"
                    >
                      Previous
                    </button>
                    <button
                      disabled={currentChapterIndex >= chapters.length - 1}
                      onClick={() => setCurrentChapterIndex(i => Math.min(chapters.length - 1, i + 1))}
                      className="px-3 py-2 rounded-lg border border-white/10 text-white/80 hover:bg-white/10 disabled:opacity-40"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Author Info */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="glass rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4">About the Author</h3>
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                  {story?.author_name ? story.author_name.charAt(0).toUpperCase() : 'A'}
                </div>
                <div>
                  <p className="text-white font-medium">{story?.author_name || 'Anonymous Author'}</p>
                  <p className="text-gray-400 text-sm">Member since {formatDate(story?.created_at)}</p>
                </div>
              </div>
            </motion.div>

            {/* TOC */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.25 }}
              className="glass rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Chapters</h3>
              <div className="space-y-2">
                {chapters.map((c, idx) => (
                  <button
                    key={c.id}
                    onClick={() => setCurrentChapterIndex(idx)}
                    className={`w-full text-left px-3 py-2 rounded-lg ${idx === currentChapterIndex ? 'bg-white/10 text-white' : 'text-white/80 hover:bg-white/5'}`}
                  >
                    {c.title || `Chapter ${c.chapter_number}`}
                  </button>
                ))}
              </div>
            </motion.div>

            {/* Comments */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="glass rounded-xl p-6"
            >
              <h3 className="text-lg font-semibold text-white mb-4">Comments ({commentCount})</h3>
              
              {/* Add Comment */}
              {user && (
                <form onSubmit={handleComment} className="mb-4">
                  <textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add a comment..."
                    className="w-full p-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                    rows={3}
                  />
                  <button
                    type="submit"
                    disabled={submittingComment || !newComment.trim()}
                    className="mt-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm font-medium rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submittingComment ? 'Posting...' : 'Post Comment'}
                  </button>
                </form>
              )}

              {/* Comments List */}
              <div className="space-y-4">
                {comments.length === 0 ? (
                  <p className="text-gray-400 text-center py-4">No comments yet. Be the first to comment!</p>
                ) : (
                  comments.map((comment) => (
                    <div key={comment.id} className="border-b border-white/10 pb-4 last:border-b-0">
                      <div className="flex items-start space-x-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center text-white text-sm font-bold">
                          {comment.user?.full_name ? comment.user.full_name.charAt(0).toUpperCase() : 'U'}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <p className="text-white font-medium text-sm">
                              {comment.user?.full_name || 'Anonymous User'}
                            </p>
                            <span className="text-gray-400 text-xs">
                              {formatDate(comment.created_at)}
                            </span>
                          </div>
                          <p className="text-gray-300 text-sm">{comment.comment}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StoryView; 