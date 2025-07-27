import React, { useState, useEffect } from 'react';
import { Image, RefreshCw, AlertCircle, Loader2 } from 'lucide-react';
import { createApiUrl, API_ENDPOINTS } from '../config';
import { useAuth } from '../AuthContext';
import ImageModal from './ImageModal';
import { CacheService } from '../services/cacheService';

const StoryCover = ({ storyId, storyTitle = "Untitled Story" }) => {
  const { session } = useAuth();
  const [coverImageUrl, setCoverImageUrl] = useState(null);
  const [imageWidth, setImageWidth] = useState(null);
  const [imageHeight, setImageHeight] = useState(null);
  const [aspectRatio, setAspectRatio] = useState(null);
  const [generationStatus, setGenerationStatus] = useState('none');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [lastGenerated, setLastGenerated] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Cache key for localStorage
  const cacheKey = `cover_cache_${storyId}`;

  // Load from cache immediately on mount
  useEffect(() => {
    if (storyId) {
      loadFromCache();
    }
  }, [storyId]);

  // Load cached data immediately for instant display
  const loadFromCache = () => {
    try {
      const cachedData = CacheService.get(cacheKey);
      if (cachedData) {
        setCoverImageUrl(cachedData.cover_image_url);
        setImageWidth(cachedData.image_width);
        setImageHeight(cachedData.image_height);
        setAspectRatio(cachedData.aspect_ratio);
        setGenerationStatus(cachedData.status || 'none');
        setLastGenerated(cachedData.generated_at);
        setIsLoading(false);
        return true; // Cache was used
      }
    } catch (error) {
      console.warn('Failed to load cover from cache:', error);
    }
    return false; // No cache used
  };

  // Save to cache for future instant loading
  const saveToCache = (data) => {
    try {
      const cacheData = {
        cover_image_url: data.cover_image_url,
        image_width: data.image_width,
        image_height: data.image_height,
        aspect_ratio: data.aspect_ratio,
        status: data.status,
        generated_at: data.generated_at
      };
      CacheService.set(cacheKey, cacheData, 5 * 60 * 1000); // 5 min TTL
      console.log('💾 Cover data cached for future instant loading');
    } catch (error) {
      console.warn('Failed to cache cover data:', error);
    }
  };

  // Fetch cover status from backend
  useEffect(() => {
    if (storyId && session?.access_token) {
      // If we didn't load from cache, show loading
      const usedCache = loadFromCache();
      if (!usedCache) {
        setIsLoading(true);
      }
      
      // Always fetch fresh data, but don't block UI if we have cache
      fetchCoverStatus();
    }
  }, [storyId, session?.access_token]);

  // Poll for status updates when generating
  useEffect(() => {
    let pollInterval;
    
    if (generationStatus === 'generating') {
      setIsGenerating(true);
      pollInterval = setInterval(fetchCoverStatus, 3000); // Poll every 3 seconds
    } else {
      setIsGenerating(false);
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [generationStatus]);

  const fetchCoverStatus = async () => {
    try {
      console.log('🔍 Fetching cover status for story', storyId);
      const response = await fetch(
        createApiUrl(API_ENDPOINTS.GET_COVER_STATUS.replace('{story_id}', storyId)),
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Cover status received:', {
          hasUrl: !!data.cover_image_url,
          status: data.status,
          dimensions: data.image_width && data.image_height ? `${data.image_width}x${data.image_height}` : 'none'
        });

        // Update state
        setCoverImageUrl(data.cover_image_url);
        setImageWidth(data.image_width);
        setImageHeight(data.image_height);
        setAspectRatio(data.aspect_ratio);
        setGenerationStatus(data.status || 'none');
        setLastGenerated(data.generated_at);
        setError('');
        setIsLoading(false);

        // Cache the data for future instant loading
        if (data.cover_image_url) {
          saveToCache(data);
        }
      } else {
        console.error('Failed to fetch cover status:', response.status);
        setIsLoading(false);
      }
    } catch (err) {
      console.error('Error fetching cover status:', err);
      setIsLoading(false);
    }
  };

  const handleGenerateCover = async () => {
    if (!session?.access_token || isGenerating) return;

    setIsGenerating(true);
    setError('');
    setGenerationStatus('generating');

    try {
      console.log('🎨 Starting cover generation for story', storyId);
      const response = await fetch(
        createApiUrl(API_ENDPOINTS.GENERATE_COVER.replace('{story_id}', storyId)),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const data = await response.json();

      if (response.ok && data.success) {
        setCoverImageUrl(data.cover_image_url);
        setImageWidth(data.image_width);
        setImageHeight(data.image_height);
        setAspectRatio(data.aspect_ratio);
        setGenerationStatus('completed');
        setLastGenerated(new Date().toISOString());
        console.log('✅ Cover generated successfully:', data.cover_image_url);
        console.log('📐 Image dimensions:', `${data.image_width}x${data.image_height}`);

        // Cache the new image data
        saveToCache({
          cover_image_url: data.cover_image_url,
          image_width: data.image_width,
          image_height: data.image_height,
          aspect_ratio: data.aspect_ratio,
          status: 'completed',
          generated_at: new Date().toISOString()
        });
      } else {
        setError(data.detail || 'Failed to generate cover');
        setGenerationStatus('failed');
        console.error('Cover generation failed:', data);
      }
    } catch (err) {
      setError('Network error while generating cover');
      setGenerationStatus('failed');
      console.error('Error generating cover:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'generating': return 'text-blue-400';
      case 'failed': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Cover ready';
      case 'generating': return 'Generating...';
      case 'failed': return 'Generation failed';
      default: return 'No cover';
    }
  };

  return (
    <div className="mb-6 bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-white">Book Cover</h3>
        <div className={`text-xs font-medium ${getStatusColor(generationStatus)}`}>
          {getStatusText(generationStatus)}
        </div>
      </div>

      {/* Cover Image Display */}
      <div className="relative mb-4">
        {isLoading && !coverImageUrl ? (
          <div className="w-full h-48 bg-gray-700/50 rounded-lg border-2 border-dashed border-gray-600 flex flex-col items-center justify-center text-gray-400">
            <Loader2 className="w-6 h-6 animate-spin mb-2" />
            <span className="text-sm">Loading cover...</span>
          </div>
        ) : coverImageUrl ? (
          <div className="relative group cursor-pointer">
            <img
              src={coverImageUrl}
              alt={`Cover for ${storyTitle}`}
              className="w-full h-auto rounded-lg shadow-lg transition-transform duration-300 group-hover:scale-105"
              style={{
                maxHeight: '300px',
                aspectRatio: aspectRatio || 'auto'
              }}
              onClick={() => setIsModalOpen(true)}
              onError={(e) => {
                console.error('Failed to load cover image:', coverImageUrl);
                setCoverImageUrl(null);
                setError('Failed to load cover image');
                // Clear cache if image fails to load
                CacheService.remove(cacheKey);
              }}
            />
            {/* Overlay on hover */}
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-lg flex flex-col items-center justify-center">
              <span className="text-white text-sm font-medium mb-2">Click to view full size</span>
              {imageWidth && imageHeight && (
                <span className="text-white/80 text-xs">{imageWidth} × {imageHeight} pixels</span>
              )}
            </div>
          </div>
        ) : (
          <div className="w-full h-48 bg-gray-700/50 rounded-lg border-2 border-dashed border-gray-600 flex flex-col items-center justify-center text-gray-400">
            <Image className="w-12 h-12 mb-2 opacity-50" />
            <span className="text-sm font-medium">No cover image</span>
            <span className="text-xs text-gray-500 mt-1">Generate an AI cover</span>
          </div>
        )}

        {/* Loading Overlay for Generation */}
        {isGenerating && (
          <div className="absolute inset-0 bg-black/70 rounded-lg flex flex-col items-center justify-center">
            <Loader2 className="w-8 h-8 text-blue-400 animate-spin mb-2" />
            <span className="text-white text-sm font-medium">Generating cover...</span>
            <span className="text-gray-300 text-xs mt-1">This may take 30-60 seconds</span>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {lastGenerated && generationStatus === 'completed' && (
            <div className="text-xs text-gray-500">
              {new Date(lastGenerated).toLocaleDateString()}
            </div>
          )}
        </div>

        <button
          onClick={handleGenerateCover}
          disabled={isGenerating}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
            isGenerating
              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          <RefreshCw className={`w-3 h-3 ${isGenerating ? 'animate-spin' : ''}`} />
          <span>{coverImageUrl ? 'Regenerate' : 'Generate Cover'}</span>
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-3 flex items-center space-x-2 text-red-400 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Image Modal */}
      <ImageModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        imageUrl={coverImageUrl}
        imageTitle={`Cover for ${storyTitle}`}
        imageWidth={imageWidth}
        imageHeight={imageHeight}
      />
    </div>
  );
};

export default StoryCover; 