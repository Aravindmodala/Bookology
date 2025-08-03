import React from 'react';
import { motion } from 'framer-motion';
import { 
  Filter,
  Search,
  TrendingUp,
  Clock,
  Star,
  Heart,
  Users,
  BookOpen,
  Calendar,
  Zap,
  Target,
  Sparkles
} from 'lucide-react';

const AdvancedFilters = ({ 
  searchQuery, 
  setSearchQuery, 
  selectedGenre, 
  setSelectedGenre, 
  selectedMood, 
  setSelectedMood,
  selectedReadingTime,
  setSelectedReadingTime,
  selectedCompletion,
  setSelectedCompletion,
  selectedCommunity,
  setSelectedCommunity,
  sortBy,
  setSortBy
}) => {
  const genres = [
    'All', 'Fantasy', 'Science Fiction', 'Mystery', 'Romance', 
    'Thriller', 'Adventure', 'Drama', 'Comedy', 'Horror', 'Historical'
  ];

  const moods = [
    { value: 'all', label: 'All Moods', icon: Sparkles, color: 'from-purple-500 to-pink-500' },
    { value: 'adventure', label: 'Adventure', icon: Zap, color: 'from-green-500 to-emerald-500' },
    { value: 'romance', label: 'Romance', icon: Heart, color: 'from-pink-500 to-red-500' },
    { value: 'mystery', label: 'Mystery', icon: Target, color: 'from-gray-700 to-gray-900' },
    { value: 'comedy', label: 'Comedy', icon: Star, color: 'from-yellow-500 to-orange-500' }
  ];

  const readingTimes = [
    { value: 'all', label: 'Any Length', icon: BookOpen },
    { value: 'quick', label: 'Quick Read (< 5 min)', icon: Clock },
    { value: 'medium', label: 'Medium Read (5-30 min)', icon: Calendar },
    { value: 'long', label: 'Weekend Binge (30+ min)', icon: TrendingUp }
  ];

  const completionStatus = [
    { value: 'all', label: 'All Stories', icon: BookOpen },
    { value: 'completed', label: 'Completed', icon: Star },
    { value: 'ongoing', label: 'Ongoing', icon: Clock },
    { value: 'new', label: 'Recently Updated', icon: Zap }
  ];

  const communityFilters = [
    { value: 'all', label: 'All Stories', icon: Users },
    { value: 'trending', label: 'Trending', icon: TrendingUp },
    { value: 'popular', label: 'Most Popular', icon: Heart },
    { value: 'hidden-gems', label: 'Hidden Gems', icon: Sparkles }
  ];

  const sortOptions = [
    { value: 'published_at', label: 'Latest', icon: Calendar },
    { value: 'created_at', label: 'Newest', icon: Clock },
    { value: 'story_title', label: 'Title', icon: BookOpen },
    { value: 'total_chapters', label: 'Most Chapters', icon: TrendingUp },
    { value: 'views', label: 'Most Viewed', icon: Users },
    { value: 'likes', label: 'Most Liked', icon: Heart }
  ];

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Search stories by title, author, or genre..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
        />
      </div>

      {/* Filter Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        
        {/* Genre Filter */}
        <div className="space-y-2">
          <label className="flex items-center space-x-2 text-white/80 text-sm font-medium">
            <Filter className="w-4 h-4" />
            <span>Genre</span>
          </label>
          <select
            value={selectedGenre}
            onChange={(e) => setSelectedGenre(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e")`,
              backgroundPosition: 'right 0.5rem center',
              backgroundRepeat: 'no-repeat',
              backgroundSize: '1.5em 1.5em',
              paddingRight: '2.5rem'
            }}
          >
            {genres.map((genre) => (
              <option key={genre} value={genre === 'All' ? '' : genre} className="bg-gray-800 text-white">
                {genre}
              </option>
            ))}
          </select>
        </div>

        {/* Mood Filter */}
        <div className="space-y-2">
          <label className="flex items-center space-x-2 text-white/80 text-sm font-medium">
            <Sparkles className="w-4 h-4" />
            <span>Mood</span>
          </label>
          <select
            value={selectedMood}
            onChange={(e) => setSelectedMood(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e")`,
              backgroundPosition: 'right 0.5rem center',
              backgroundRepeat: 'no-repeat',
              backgroundSize: '1.5em 1.5em',
              paddingRight: '2.5rem'
            }}
          >
            {moods.map((mood) => (
              <option key={mood.value} value={mood.value} className="bg-gray-800 text-white">
                {mood.label}
              </option>
            ))}
          </select>
        </div>

        {/* Reading Time Filter */}
        <div className="space-y-2">
          <label className="flex items-center space-x-2 text-white/80 text-sm font-medium">
            <Clock className="w-4 h-4" />
            <span>Reading Time</span>
          </label>
          <select
            value={selectedReadingTime}
            onChange={(e) => setSelectedReadingTime(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e")`,
              backgroundPosition: 'right 0.5rem center',
              backgroundRepeat: 'no-repeat',
              backgroundSize: '1.5em 1.5em',
              paddingRight: '2.5rem'
            }}
          >
            {readingTimes.map((time) => (
              <option key={time.value} value={time.value} className="bg-gray-800 text-white">
                {time.label}
              </option>
            ))}
          </select>
        </div>

        {/* Completion Status Filter */}
        <div className="space-y-2">
          <label className="flex items-center space-x-2 text-white/80 text-sm font-medium">
            <Star className="w-4 h-4" />
            <span>Status</span>
          </label>
          <select
            value={selectedCompletion}
            onChange={(e) => setSelectedCompletion(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e")`,
              backgroundPosition: 'right 0.5rem center',
              backgroundRepeat: 'no-repeat',
              backgroundSize: '1.5em 1.5em',
              paddingRight: '2.5rem'
            }}
          >
            {completionStatus.map((status) => (
              <option key={status.value} value={status.value} className="bg-gray-800 text-white">
                {status.label}
              </option>
            ))}
          </select>
        </div>

        {/* Community Filter */}
        <div className="space-y-2">
          <label className="flex items-center space-x-2 text-white/80 text-sm font-medium">
            <Users className="w-4 h-4" />
            <span>Community</span>
          </label>
          <select
            value={selectedCommunity}
            onChange={(e) => setSelectedCommunity(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e")`,
              backgroundPosition: 'right 0.5rem center',
              backgroundRepeat: 'no-repeat',
              backgroundSize: '1.5em 1.5em',
              paddingRight: '2.5rem'
            }}
          >
            {communityFilters.map((filter) => (
              <option key={filter.value} value={filter.value} className="bg-gray-800 text-white">
                {filter.label}
              </option>
            ))}
          </select>
        </div>

        {/* Sort Options */}
        <div className="space-y-2">
          <label className="flex items-center space-x-2 text-white/80 text-sm font-medium">
            <TrendingUp className="w-4 h-4" />
            <span>Sort By</span>
          </label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full px-3 py-2 bg-gray-800/50 border border-gray-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e")`,
              backgroundPosition: 'right 0.5rem center',
              backgroundRepeat: 'no-repeat',
              backgroundSize: '1.5em 1.5em',
              paddingRight: '2.5rem'
            }}
          >
            {sortOptions.map((option) => (
              <option key={option.value} value={option.value} className="bg-gray-800 text-white">
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Filters Display */}
      {(selectedGenre || selectedMood !== 'all' || selectedReadingTime !== 'all' || selectedCompletion !== 'all' || selectedCommunity !== 'all') && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-wrap gap-2"
        >
          <span className="text-white/60 text-sm">Active filters:</span>
          {selectedGenre && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="px-2 py-1 bg-purple-500/20 text-purple-300 text-xs rounded-full"
            >
              Genre: {selectedGenre}
            </motion.span>
          )}
          {selectedMood !== 'all' && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="px-2 py-1 bg-pink-500/20 text-pink-300 text-xs rounded-full"
            >
              Mood: {moods.find(m => m.value === selectedMood)?.label}
            </motion.span>
          )}
          {selectedReadingTime !== 'all' && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded-full"
            >
              Time: {readingTimes.find(t => t.value === selectedReadingTime)?.label}
            </motion.span>
          )}
          {selectedCompletion !== 'all' && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="px-2 py-1 bg-green-500/20 text-green-300 text-xs rounded-full"
            >
              Status: {completionStatus.find(s => s.value === selectedCompletion)?.label}
            </motion.span>
          )}
          {selectedCommunity !== 'all' && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="px-2 py-1 bg-orange-500/20 text-orange-300 text-xs rounded-full"
            >
              Community: {communityFilters.find(c => c.value === selectedCommunity)?.label}
            </motion.span>
          )}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              setSelectedGenre('');
              setSelectedMood('all');
              setSelectedReadingTime('all');
              setSelectedCompletion('all');
              setSelectedCommunity('all');
            }}
            className="px-2 py-1 bg-red-500/20 text-red-300 text-xs rounded-full hover:bg-red-500/30 transition-colors"
          >
            Clear All
          </motion.button>
        </motion.div>
      )}
    </div>
  );
};

export default AdvancedFilters; 