import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  Heart, 
  MessageCircle, 
  Eye, 
  BookOpen, 
  User, 
  Clock,
  Star,
  Share2,
  Bookmark,
  MoreHorizontal,
  Play,
  Users,
  TrendingUp
} from 'lucide-react';

const EnhancedStoryCard = ({ story, onLike, onComment, onShare }) => {
  const [isLiked, setIsLiked] = useState(story.is_liked || false);
  const [likeCount, setLikeCount] = useState(story.like_count || 0);
  const [isHovered, setIsHovered] = useState(false);

  const handleLike = async () => {
    if (onLike) {
      const success = await onLike(story.id);
      if (success) {
        setIsLiked(!isLiked);
        setLikeCount(isLiked ? likeCount - 1 : likeCount + 1);
      }
    }
  };

  const getMoodColor = (genre) => {
    const moodColors = {
      'Fantasy': 'from-purple-500 to-pink-500',
      'Science Fiction': 'from-blue-500 to-cyan-500',
      'Mystery': 'from-gray-700 to-gray-900',
      'Romance': 'from-pink-500 to-red-500',
      'Thriller': 'from-red-600 to-orange-600',
      'Adventure': 'from-green-500 to-emerald-500',
      'Drama': 'from-indigo-500 to-purple-500',
      'Comedy': 'from-yellow-500 to-orange-500',
      'Horror': 'from-red-800 to-black',
      'Historical': 'from-amber-600 to-yellow-600'
    };
    return moodColors[genre] || 'from-gray-500 to-gray-700';
  };

  const getReadingTime = (wordCount) => {
    const wordsPerMinute = 200;
    const minutes = Math.ceil(wordCount / wordsPerMinute);
    if (minutes < 5) return 'Quick Read';
    if (minutes < 30) return `${minutes} min read`;
    if (minutes < 120) return 'Weekend Binge';
    return 'Epic Saga';
  };

  const getCompletionStatus = (totalChapters, completedChapters) => {
    if (completedChapters === 0) return 'New';
    if (completedChapters === totalChapters) return 'Completed';
    if (completedChapters > totalChapters * 0.8) return 'Nearly Done';
    return 'Ongoing';
  };

  const getCommunityBuzz = (views, likes, comments) => {
    const engagement = (likes + comments) / views;
    if (engagement > 0.1) return 'Trending';
    if (views > 10000) return 'Popular';
    if (engagement > 0.05) return 'Hidden Gem';
    return 'New';
  };

  return (
    <motion.div
      className={`relative group cursor-pointer overflow-hidden rounded-xl bg-gradient-to-br ${getMoodColor(story.genre)} border-2 border-white/20 shadow-xl`}
      whileHover={{ 
        scale: 1.02, 
        y: -8,
        rotateY: 5,
        transition: { duration: 0.3, ease: "easeOut" }
      }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Mood Indicator */}
      <div className="absolute top-3 left-3 z-10">
        <div className="flex items-center space-x-1 bg-black/30 backdrop-blur-sm rounded-full px-2 py-1">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
          <span className="text-xs text-white font-medium">{story.genre}</span>
        </div>
      </div>

      {/* Story Cover/Image */}
      <div className="relative h-48 bg-gradient-to-br from-black/20 to-transparent">
        {story.cover_image ? (
          <img 
            src={story.cover_image} 
            alt={story.story_title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <BookOpen className="w-16 h-16 text-white/50" />
          </div>
        )}
        
        {/* Overlay on hover */}
        <motion.div
          className="absolute inset-0 bg-black/50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: isHovered ? 1 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <Play className="w-12 h-12 text-white" />
        </motion.div>
      </div>

      {/* Story Content */}
      <div className="p-4 space-y-3">
        {/* Title and Author */}
        <div>
          <h3 className="text-lg font-bold text-white mb-1 line-clamp-2">
            {story.story_title}
          </h3>
          <div className="flex items-center space-x-2 text-white/80">
            <User className="w-4 h-4" />
            <span className="text-sm">{story.author_name || 'Anonymous'}</span>
          </div>
        </div>

        {/* Description */}
        <p className="text-white/90 text-sm line-clamp-3 leading-relaxed">
          {story.description || story.story_outline || 'A captivating story waiting to be discovered...'}
        </p>

        {/* Stats Row */}
        <div className="flex items-center justify-between text-white/70 text-xs">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              <Eye className="w-3 h-3" />
              <span>{story.views || 0}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Heart className="w-3 h-3" />
              <span>{likeCount}</span>
            </div>
            <div className="flex items-center space-x-1">
              <MessageCircle className="w-3 h-3" />
              <span>{story.comment_count || 0}</span>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <Clock className="w-3 h-3" />
            <span>{getReadingTime(story.word_count || 0)}</span>
          </div>
        </div>

        {/* Progress and Status */}
        <div className="space-y-2">
          {/* Reading Progress */}
          <div className="w-full bg-white/20 rounded-full h-2">
            <motion.div
              className="bg-white h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${(story.completed_chapters || 0) / (story.total_chapters || 1) * 100}%` }}
              transition={{ duration: 1, delay: 0.5 }}
            />
          </div>
          
          {/* Status Badges */}
          <div className="flex items-center space-x-2">
            <span className="px-2 py-1 bg-white/20 rounded-full text-xs text-white">
              {getCompletionStatus(story.total_chapters || 0, story.completed_chapters || 0)}
            </span>
            <span className="px-2 py-1 bg-white/20 rounded-full text-xs text-white">
              {getCommunityBuzz(story.views || 0, likeCount, story.comment_count || 0)}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center space-x-2">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleLike}
              className={`p-2 rounded-lg transition-colors ${
                isLiked 
                  ? 'bg-red-500/20 text-red-400' 
                  : 'bg-white/10 text-white/70 hover:bg-white/20'
              }`}
            >
              <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onComment && onComment(story.id)}
              className="p-2 rounded-lg bg-white/10 text-white/70 hover:bg-white/20 transition-colors"
            >
              <MessageCircle className="w-4 h-4" />
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onShare && onShare(story)}
              className="p-2 rounded-lg bg-white/10 text-white/70 hover:bg-white/20 transition-colors"
            >
              <Share2 className="w-4 h-4" />
            </motion.button>
          </div>
          
          <Link
            to={`/story/${story.id}`}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
          >
            <span>Read More</span>
            <BookOpen className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Hover Effects */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0"
        animate={{ opacity: isHovered ? 1 : 0 }}
        transition={{ duration: 0.2 }}
      />
    </motion.div>
  );
};

export default EnhancedStoryCard; 