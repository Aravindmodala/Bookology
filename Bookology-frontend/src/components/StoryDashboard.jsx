import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BookOpen, 
  PenTool, 
  Clock, 
  ChevronRight,
  Plus,
  FileText,
  Calendar,
  User,
  Search,
  Filter,
  MoreVertical,
  Edit3,
  Trash2,
  Eye,
  Palette
} from 'lucide-react';
import { useAuth } from '../AuthContext';
import { supabase, isSupabaseEnabled } from '../supabaseClient';
import { createApiUrl, API_ENDPOINTS } from '../config';
import { Menu, Transition } from '@headlessui/react';

const StoryDashboard = ({ onStartNewStory }) => {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('created_at'); // Changed from 'updated_at' to 'created_at'
  const { user, session } = useAuth();
  const navigate = useNavigate();

  // Navigation handlers
  const handleContinueReading = (story) => {
    // Navigate to story editor with story data
    navigate('/editor', { state: { story } });
  };

  const handleViewStory = (story) => {
    // Navigate to read-only view or editor
    navigate('/editor', { state: { story, mode: 'view' } });
  };

  const handleEditStory = (story) => {
    // Navigate to editor in edit mode
    navigate('/editor', { state: { story, mode: 'edit' } });
  };

  const handleDeleteStory = async (story) => {
    if (!window.confirm(`Are you sure you want to delete the story "${story.story_title}" and all its chapters? This action cannot be undone.`)) return;
    try {
      setLoading(true);
      // Delete the story from Supabase (will cascade if FK is set)
      const { error } = await supabase
        .from('Stories')
        .delete()
        .eq('id', story.id);
      if (error) throw error;
      // Refresh stories list
      setStories(prev => prev.filter(s => s.id !== story.id));
    } catch (err) {
      setError('Failed to delete story: ' + (err.message || err));
    } finally {
      setLoading(false);
    }
  };

  // Fixed data fetching with proper error handling and fallback
  useEffect(() => {
    const fetchStories = async () => {
      if (!user) {
        console.log('No user found, setting empty stories');
        setStories([]);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        console.log('🔍 Fetching stories for user:', user.id);
        console.log('🔧 Supabase client status:', !!supabase);
        console.log('🔧 isSupabaseEnabled:', isSupabaseEnabled);
        
        // Method 1: Try the same approach as Generator (direct Supabase)
        if (supabase) {
          try {
            const { data: Stories, error: StoriesError } = await supabase
              .from('Stories')
              .select('*')
              .eq('user_id', user.id)
              .order(sortBy, { ascending: false });

            console.log('📦 Supabase response:', { data: Stories, error: StoriesError });

            if (StoriesError) {
              console.error('❌ Supabase error:', StoriesError);
              throw new Error(`Supabase error: ${StoriesError.message || JSON.stringify(StoriesError)}`);
            }

            console.log('✅ Successfully fetched stories via Supabase:', Stories?.length || 0);
            setStories(Stories || []);
            setError(null);
            return; // Success, exit here
            
          } catch (supabaseErr) {
            console.error('❌ Supabase method failed:', supabaseErr);
            // Continue to fallback method
          }
        }

        // Method 2: Fallback - try backend API if available
        if (session?.access_token) {
          try {
            console.log('🔄 Trying backend API fallback...');
            const response = await fetch(createApiUrl('/stories'), {
              headers: {
                'Authorization': `Bearer ${session.access_token}`,
                'Content-Type': 'application/json'
              }
            });

            if (response.ok) {
              const data = await response.json();
              console.log('✅ Successfully fetched via backend API:', data?.stories?.length || 0);
              setStories(data.stories || []);
              setError(null);
              return; // Success, exit here
            } else {
              console.error('❌ Backend API failed with status:', response.status);
            }
          } catch (apiErr) {
            console.error('❌ Backend API method failed:', apiErr);
          }
        }

        // If we reach here, all methods failed
        throw new Error('All data fetching methods failed. Please check your connection and try again.');
        
      } catch (err) {
        console.error('❌ Final error in fetchStories:', err);
        setError(`Failed to load stories: ${err.message}`);
        setStories([]);
      } finally {
        setLoading(false);
      }
    };

    fetchStories();
  }, [user, sortBy, session]); // React to user, sortBy, and session changes

  const filteredStories = stories.filter(story => {
    const searchLower = searchTerm.toLowerCase();
    return (
      (story.story_title || '').toLowerCase().includes(searchLower) ||
      (story.story_outline || '').toLowerCase().includes(searchLower) ||
      (story.genre || '').toLowerCase().includes(searchLower)
    );
  });

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-400 bg-green-400/20';
      case 'in_progress': return 'text-blue-400 bg-blue-400/20';
      case 'draft': return 'text-yellow-400 bg-yellow-400/20';
      default: return 'text-gray-400 bg-gray-400/20';
    }
  };

  const StoryCard = ({ story }) => {
    const [coverImage, setCoverImage] = useState(null);
    const [coverLoading, setCoverLoading] = useState(false);
    const [showImageModal, setShowImageModal] = useState(false);

    // Fetch cover image on component mount
    useEffect(() => {
      const fetchCoverImage = async () => {
        if (!story.id || !session?.access_token) return;
        
        try {
          const response = await fetch(
            createApiUrl(API_ENDPOINTS.GET_COVER_STATUS.replace('{story_id}', story.id)),
            {
              headers: {
                'Authorization': `Bearer ${session.access_token}`,
                'Content-Type': 'application/json'
              }
            }
          );
          
          if (response.ok) {
            const data = await response.json();
            if (data.success && data.cover_image_url) {
              setCoverImage(data.cover_image_url);
            }
          }
        } catch (err) {
          console.log('No cover image found for story:', story.id);
        }
      };

      fetchCoverImage();
    }, [story.id, session]);

    // Generate cover image
    const handleGenerateCover = async () => {
      if (!story.id || !session?.access_token || coverLoading) return;
      
      setCoverLoading(true);
      try {
        const response = await fetch(
          createApiUrl(API_ENDPOINTS.GENERATE_COVER.replace('{story_id}', story.id)),
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.cover_image_url) {
            setCoverImage(data.cover_image_url);
          }
        }
      } catch (err) {
        console.error('Failed to generate cover:', err);
      } finally {
        setCoverLoading(false);
      }
    };

    return (
      <div className="bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition-all duration-200 hover:scale-[1.02] group overflow-hidden">
        {/* Cover Image Section */}
        <div className="relative h-48 bg-gradient-to-br from-gray-700 via-gray-800 to-gray-900 overflow-hidden">
          {coverImage ? (
            <img 
              src={coverImage} 
              alt={story.story_title || 'Story cover'}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 cursor-pointer"
              onClick={() => setShowImageModal(true)}
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-blue-600/20 via-purple-600/20 to-pink-600/20">
              <BookOpen className="w-12 h-12 text-gray-400 mb-2" />
              <span className="text-gray-400 text-sm mb-3">No cover image</span>
              <button
                onClick={handleGenerateCover}
                disabled={coverLoading}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white text-xs rounded-lg transition-colors flex items-center space-x-1"
              >
                {coverLoading ? (
                  <>
                    <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <Palette className="w-3 h-3" />
                    <span>Generate Cover</span>
                  </>
                )}
              </button>
            </div>
          )}
          
          {/* Overlay with action buttons */}
          <div className="absolute top-2 right-2 flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button 
              className="p-1.5 bg-black/50 hover:bg-black/70 rounded-lg text-white transition-all"
              onClick={() => handleViewStory(story)}
              title="View Story"
            >
              <Eye className="w-3 h-3" />
            </button>
            <button 
              className="p-1.5 bg-black/50 hover:bg-black/70 rounded-lg text-white transition-all"
              onClick={() => handleEditStory(story)}
              title="Edit Story"
            >
              <Edit3 className="w-3 h-3" />
            </button>
          </div>

          {/* Status badge */}
          <div className="absolute top-2 left-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(story.status)}`}>
              {story.status?.replace('_', ' ') || 'draft'}
            </span>
          </div>
        </div>

        {/* Content Section */}
        <div className="p-4">
          <div className="flex justify-between items-start mb-3">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors line-clamp-1">
                {story.story_title || 'Untitled Story'}
              </h3>
              <p className="text-gray-400 text-sm line-clamp-2">
                {story.story_outline || 'No description available'}
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between mb-4 text-sm text-gray-400">
            <div className="flex items-center space-x-3">
              <span className="flex items-center">
                <FileText className="w-3 h-3 mr-1" />
                {story.total_chapters || 0}
              </span>
              <span className="flex items-center">
                <Calendar className="w-3 h-3 mr-1" />
                {formatDate(story.created_at)}
              </span>
            </div>
            <span className="text-blue-400 font-medium text-xs">
              {story.genre || 'Fiction'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <button 
              className="flex items-center text-sm text-blue-400 hover:text-blue-300 transition-colors font-medium"
              onClick={() => handleContinueReading(story)}
            >
              Continue Reading
              <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
            </button>
            
            {/* More options menu */}
            <Menu as="div" className="relative">
              <Menu.Button className="p-1 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-all">
                <MoreVertical className="w-4 h-4" />
              </Menu.Button>
              <Transition
                as={React.Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items className="absolute right-0 z-10 mt-2 w-36 origin-top-right rounded-md bg-gray-900 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <div className="py-1">
                    {!coverImage && (
                      <Menu.Item>
                        {({ active }) => (
                          <button
                            onClick={handleGenerateCover}
                            disabled={coverLoading}
                            className={`w-full flex items-center px-4 py-2 text-sm text-left ${active ? 'bg-blue-600 text-white' : 'text-blue-400'} disabled:opacity-50`}
                          >
                            <Palette className="w-4 h-4 mr-2" /> Generate Cover
                          </button>
                        )}
                      </Menu.Item>
                    )}
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={() => handleDeleteStory(story)}
                          className={`w-full flex items-center px-4 py-2 text-sm text-left ${active ? 'bg-red-600 text-white' : 'text-red-400'}`}
                        >
                          <Trash2 className="w-4 h-4 mr-2" /> Delete
                        </button>
                      )}
                    </Menu.Item>
                  </div>
                </Menu.Items>
              </Transition>
            </Menu>
          </div>
        </div>

        {/* Cover Image Modal */}
        {showImageModal && coverImage && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={() => setShowImageModal(false)}>
            <div className="max-w-4xl max-h-[90vh] p-4">
              <img 
                src={coverImage} 
                alt={story.story_title || 'Story cover'}
                className="w-full h-full object-contain rounded-lg"
                onClick={(e) => e.stopPropagation()}
              />
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
            <BookOpen className="w-8 h-8 text-white" />
          </div>
          <p className="text-gray-400">Loading your stories...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Development Notice - Show if no user */}
      {!user && (
        <div className="bg-yellow-600/20 border-b border-yellow-500/50 text-yellow-200 px-4 py-2 text-center text-sm">
          ⚠️ Please log in to see your generated stories. 
          <a href="/login" className="underline ml-2 hover:text-yellow-100">Click here to login</a>
        </div>
      )}
      
      {/* Error Notice */}
      {error && (
        <div className="bg-red-600/20 border-b border-red-500/50 text-red-200 px-4 py-2 text-center text-sm">
          ❌ {error}
        </div>
      )}
      
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-6">
              <div>
                <h1 className="text-4xl font-bold text-white mb-2">Your Stories</h1>
                <p className="text-gray-400">
                  Welcome back! Continue your literary journey or start a new adventure.
                </p>
                {/* Debug info for development */}
                {process.env.NODE_ENV === 'development' && (
                  <div className="text-xs text-gray-500 mt-2">
                    Debug: User: {user ? '✅' : '❌'} | Stories: {stories.length} | Loading: {loading ? 'Yes' : 'No'}
                  </div>
                )}
              </div>
              
              <button
                onClick={onStartNewStory}
                className="mt-4 lg:mt-0 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-200 hover:scale-105 flex items-center space-x-2 shadow-lg"
              >
                <Plus className="w-5 h-5" />
                <span>Start New Story</span>
              </button>
            </div>

            {/* Search and Filter Bar */}
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search stories..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-xl pl-10 pr-4 py-3 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none transition-colors"
                />
              </div>
              
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition-colors"
              >
                <option value="created_at">Date Created</option>
                <option value="story_title">Title</option>
                <option value="total_chapters">Chapter Count</option>
              </select>
            </div>
          </div>

          {/* Stories Grid */}
          {filteredStories.length === 0 ? (
            <div className="text-center py-16">
              <div className="w-24 h-24 bg-gray-800 rounded-3xl flex items-center justify-center mx-auto mb-6">
                <BookOpen className="w-12 h-12 text-gray-400" />
              </div>
              <h3 className="text-2xl font-semibold text-white mb-2">
                {searchTerm ? 'No stories found' : stories.length === 0 ? 'No stories yet' : 'No matching stories'}
              </h3>
              <p className="text-gray-400 mb-6 max-w-md mx-auto">
                {searchTerm 
                  ? 'Try adjusting your search terms or filters.'
                  : stories.length === 0 
                    ? 'Your creative journey starts here. Create your first story and bring your imagination to life.'
                    : 'No stories match your current search.'
                }
              </p>
              {!searchTerm && stories.length === 0 && (
                <button
                  onClick={onStartNewStory}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-semibold transition-all duration-200 hover:scale-105 flex items-center space-x-2 mx-auto"
                >
                  <PenTool className="w-5 h-5" />
                  <span>Create Your First Story</span>
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredStories.map((story) => (
                <StoryCard key={story.id} story={story} />
              ))}
            </div>
          )}

          {/* Stats Footer */}
          {filteredStories.length > 0 && (
            <div className="mt-12 bg-gray-800 rounded-xl p-6 border border-gray-700">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
                <div>
                  <div className="text-3xl font-bold text-blue-400 mb-1">
                    {stories.length}
                  </div>
                  <div className="text-gray-400 text-sm">Total Stories</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-green-400 mb-1">
                    {stories.reduce((sum, story) => sum + (story.total_chapters || 0), 0)}
                  </div>
                  <div className="text-gray-400 text-sm">Chapters Written</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-purple-400 mb-1">
                    {stories.filter(story => story.status === 'completed').length}
                  </div>
                  <div className="text-gray-400 text-sm">Completed Stories</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StoryDashboard;