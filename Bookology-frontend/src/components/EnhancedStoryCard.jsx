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
    if (minutes < 5) return 'Quick';
    if (minutes < 30) return `${minutes}m`;
    if (minutes < 120) return 'Long';
    return 'Epic';
  };

  return (
    <motion.div
      className={`relative group cursor-pointer overflow-hidden rounded-none bg-gradient-to-br ${getMoodColor(story.genre)} border border-white/10 shadow-lg`}
      whileHover={{ 
        scale: 1.05, 
        y: -4,
        transition: { duration: 0.2, ease: "easeOut" }
      }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Story Cover/Image - Netflix style rectangular */}
      <div className="relative h-32 bg-gradient-to-br from-black/20 to-transparent">
        {story.cover_image_url ? (
          <img 
            src={story.cover_image_url} 
            alt={story.story_title}
            className="w-full h-full object-cover"
            loading="lazy"
            decoding="async"
            fetchpriority="low"
            onError={(e) => {
              console.error('Failed to load cover image:', story.cover_image_url);
              e.target.style.display = 'none';
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <BookOpen className="w-8 h-8 text-white/50" />
          </div>
        )}
        
        {/* Netflix-style overlay on hover */}
        <motion.div
          className="absolute inset-0 bg-black/60 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: isHovered ? 1 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <div className="flex items-center space-x-3">
            <button className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors">
              <Play className="w-5 h-5 text-white" />
            </button>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleLike}
              className={`p-2 rounded-full transition-colors ${
                isLiked 
                  ? 'bg-red-500/80 text-white' 
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
            </motion.button>
          </div>
        </motion.div>

        {/* Genre Badge - Top Left */}
        <div className="absolute top-2 left-2">
          <span className="px-2 py-1 bg-black/70 text-white text-xs rounded font-medium">
            {story.genre || 'Fiction'}
          </span>
        </div>

        {/* Stats - Top Right */}
        <div className="absolute top-2 right-2 flex items-center space-x-1">
          <div className="flex items-center space-x-1 bg-black/70 px-2 py-1 rounded text-xs text-white">
            <Eye className="w-3 h-3" />
            <span>{story.views || 0}</span>
          </div>
        </div>
      </div>

      {/* Bottom bar: only Title and Read */}
      <div className="p-2 flex items-center justify-between bg-black/30">
        <h3 className="text-sm font-semibold text-white line-clamp-1 flex-1 mr-2">
          {story.story_title}
        </h3>
        <Link
          to={`/story/${story.id}`}
          className="px-2 py-1 text-xs bg-white/20 hover:bg-white/30 text-white rounded-sm"
        >
          Read
        </Link>
      </div>

      {/* Hover Effects */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent opacity-0"
        animate={{ opacity: isHovered ? 1 : 0 }}
        transition={{ duration: 0.2 }}
      />
    </motion.div>
  );
};

export default EnhancedStoryCard; 