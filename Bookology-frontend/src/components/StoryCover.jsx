import React, { useState, useEffect, useRef } from 'react';
import { Image, Loader2, RefreshCw, AlertCircle } from 'lucide-react';
import { createApiUrl, API_ENDPOINTS } from '../config';
import { useAuth } from '../AuthContext';
import ImageModal from './ImageModal';
import CacheService from '../services/cacheService';

const StoryCover = ({ storyId, storyTitle = "Untitled Story" }) => {
  const { session } = useAuth();
  const [coverImageUrl, setCoverImageUrl] = useState(null);
  const [imageWidth, setImageWidth] = useState(null);
  const [imageHeight, setImageHeight] = useState(null);
  const [aspectRatio, setAspectRatio] = useState(null);
  const [generationStatus, setGenerationStatus] = useState('none');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastGenerated, setLastGenerated] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Add ref to track if we're already polling
  const isPollingRef = useRef(false);

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

  // Fetch cover status from backend - ONE TIME ONLY on mount
  useEffect(() => {
    if (storyId && session?.access_token) {
      // If we didn't load from cache, show loading
      const usedCache = loadFromCache();
      if (!usedCache) {
        setIsLoading(true);
      }
      
      // Only fetch once if not currently generating
      if (generationStatus !== 'generating' && generationStatus !== 'pending') {
        console.log('📋 Initial fetch of cover status (not generating)');
        fetchCoverStatus();
      } else {
        console.log('⏭️ Skipping initial fetch - already generating');
      }
    }
  }, [storyId, session?.access_token]); // Removed generationStatus from deps to prevent loops

  // Poll for status updates when generating
  useEffect(() => {
    let pollInterval;
    let pollAttempts = 0;
    let consecutiveFailures = 0;
    const maxPollAttempts = 20; // Maximum 1 minute of polling (20 * 3 seconds)
    const maxConsecutiveFailures = 3;
    
    const pollCoverStatus = async () => {
      try {
        pollAttempts++;
        console.log(`🔍 Polling cover status (attempt ${pollAttempts}/${maxPollAttempts}) for story ${storyId}`);
        
        // FORCE STOP after max attempts
        if (pollAttempts >= maxPollAttempts) {
          console.log('🛑 FORCE STOPPING - Max attempts reached');
          if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
          }
          isPollingRef.current = false;
          setIsGenerating(false);
          setGenerationStatus('none');
          setIsLoading(false);
          setError('Cover generation timed out. Please try refreshing.');
          return;
        }
        
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

          // Reset consecutive failures on success
          consecutiveFailures = 0;

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

          // ✅ STOP POLLING when generation is complete, failed, or not generating
          if (data.status === 'completed' || data.status === 'failed' || data.status === 'none' || !data.status) {
            console.log(`🛑 STOPPING polling - Status: ${data.status}`);
            if (pollInterval) {
              clearInterval(pollInterval);
              pollInterval = null;
            }
            isPollingRef.current = false;
            setIsGenerating(false);
            return; // Exit early to prevent further polling
          }
        } else {
          consecutiveFailures++;
          console.error(`Failed to fetch cover status (${consecutiveFailures}/${maxConsecutiveFailures}):`, response.status);
          
          // ✅ STOP POLLING on repeated failures
          if (consecutiveFailures >= maxConsecutiveFailures) {
            console.log('🛑 STOPPING polling - Too many failures');
            if (pollInterval) {
              clearInterval(pollInterval);
              pollInterval = null;
            }
            isPollingRef.current = false;
            setIsGenerating(false);
            setGenerationStatus('none');
            setIsLoading(false);
            setError('Failed to check cover status. Please refresh.');
            return;
          }
        }
      } catch (err) {
        consecutiveFailures++;
        console.error(`Error polling cover status (${consecutiveFailures}/${maxConsecutiveFailures}):`, err);
        
        // ✅ STOP POLLING on error
        if (consecutiveFailures >= maxConsecutiveFailures) {
          console.log('🛑 STOPPING polling - Network errors');
          if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
          }
          isPollingRef.current = false;
          setIsGenerating(false);
          setGenerationStatus('none');
          setIsLoading(false);
          setError('Network error while checking cover status.');
          return;
        }
      }
    };
    
    // Only start polling if status is specifically 'generating' or 'pending' AND we're not already polling
    if ((generationStatus === 'generating' || generationStatus === 'pending') && session?.access_token && storyId && !isPollingRef.current) {
      console.log(`🔄 Starting polling for cover generation with status: ${generationStatus}`);
      isPollingRef.current = true;
      setIsGenerating(true);
      
      // Start polling immediately, then every 3 seconds
      pollCoverStatus();
      pollInterval = setInterval(pollCoverStatus, 3000);
    } else {
      console.log(`❌ Not starting polling - Status: ${generationStatus}, Auth: ${!!session?.access_token}, StoryId: ${!!storyId}, Already Polling: ${isPollingRef.current}`);
    }

    return () => {
      if (pollInterval) {
        console.log('🧹 Cleaning up polling interval');
        clearInterval(pollInterval);
        isPollingRef.current = false;
      }
    };
  }, [session?.access_token, storyId, generationStatus]); // Added generationStatus to trigger polling when status changes

  // Force stop polling after 2 minutes as a safety net
  useEffect(() => {
    let forceStopTimer;
    
    if (generationStatus === 'generating' || generationStatus === 'pending') {
      console.log('⏰ Setting 2-minute force stop timer');
      forceStopTimer = setTimeout(() => {
        console.log('🛑 FORCE STOPPING polling after 2 minutes');
        setGenerationStatus('none');
        setIsGenerating(false);
        setIsLoading(false);
        setError('Cover generation timed out. Please try again.');
      }, 120000); // 2 minutes
    }

    return () => {
      if (forceStopTimer) {
        console.log('🧹 Cleaning up force stop timer');
        clearTimeout(forceStopTimer);
      }
    };
  }, [generationStatus]);

  // Global cleanup effect - ensures all intervals are cleared on unmount
  useEffect(() => {
    return () => {
      console.log('🧹 Component unmounting - clearing all timers');
      // Force stop any ongoing generation
      setGenerationStatus('none');
      setIsGenerating(false);
      isPollingRef.current = false;
    };
  }, []);

  const fetchCoverStatus = async (shouldStopPolling = false) => {
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

        // ✅ Return status so caller can decide whether to continue polling
        return data.status;
      } else {
        console.error('Failed to fetch cover status:', response.status);
        setIsLoading(false);
        return 'failed';
      }
    } catch (err) {
      console.error('Error fetching cover status:', err);
      setIsLoading(false);
      return 'failed';
    }
  };

  const handleGenerateCover = async () => {
    if (!session?.access_token || isGenerating) return;

    setIsGenerating(true);
    setError('');
    setGenerationStatus('generating');
    console.log('🎨 generateCover → status set to:', 'generating');

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
         setIsGenerating(false);      // ← NEW
         setIsLoading(false);         // ← NEW
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
      } else if (response.ok && !data.success && data.status === 'generating') {
        // Backend says generation is already in progress - start polling
        console.log('🔄 Cover generation already in progress, starting polling');
        setGenerationStatus('generating');
        // Don't set isGenerating to false - let the polling useEffect handle it
        return; // Exit early, let polling handle the rest
      } else {
        setError(data.detail || data.message || 'Failed to generate cover');
        setGenerationStatus('failed');
        console.error('Cover generation failed:', data);
        setIsGenerating(false);
      }
    } catch (err) {
      setError('Network error while generating cover');
      setGenerationStatus('failed');
      console.error('Error generating cover:', err);
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