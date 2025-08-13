import React, { useEffect } from 'react';
import { X, Download, ZoomIn, ZoomOut } from 'lucide-react';

const ImageModal = ({ 
  isOpen, 
  onClose, 
  imageUrl, 
  imageTitle = "Image", 
  imageWidth = null, 
  imageHeight = null 
}) => {
  // Close modal on Escape key press
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent background scrolling when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // Don't render if not open
  if (!isOpen || !imageUrl) return null;

  // Handle download functionality
  const handleDownload = async () => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${imageTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_cover.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download image:', error);
    }
  };

  // Calculate maximum dimensions for the modal (90% of viewport)
  const maxWidth = Math.min(window.innerWidth * 0.9, imageWidth || 800);
  const maxHeight = Math.min(window.innerHeight * 0.9, imageHeight || 600);

  // Calculate aspect ratio to maintain proportions
  let displayWidth = maxWidth;
  let displayHeight = maxHeight;

  if (imageWidth && imageHeight) {
    const aspectRatio = imageWidth / imageHeight;
    
    if (aspectRatio > maxWidth / maxHeight) {
      // Image is wider relative to container
      displayWidth = maxWidth;
      displayHeight = maxWidth / aspectRatio;
    } else {
      // Image is taller relative to container
      displayHeight = maxHeight;
      displayWidth = maxHeight * aspectRatio;
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Modal Content */}
      <div 
        className="relative bg-gray-800 rounded-xl shadow-2xl max-w-full max-h-full overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: displayWidth,
          height: 'auto'
        }}
      >
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/60 to-transparent z-10 p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-semibold text-lg truncate pr-4">
              {imageTitle}
            </h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleDownload}
                className="p-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
                title="Download Image"
              >
                <Download className="w-5 h-5" />
              </button>
              <button
                onClick={onClose}
                className="p-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
                title="Close (Escape)"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Image */}
        <div className="relative">
          <img
            src={imageUrl}
            alt={imageTitle}
            className="w-full h-auto block rounded-xl"
            style={{
              maxWidth: displayWidth,
              maxHeight: displayHeight
            }}
            width={imageWidth || undefined}
            height={imageHeight || undefined}
            loading="lazy"
            decoding="async"
            onLoad={() => {
              // Optional: Add loading state handling here
            }}
            onError={() => {
              console.error('Failed to load image in modal:', imageUrl);
            }}
          />
          
          {/* Loading overlay could be added here if needed */}
        </div>

        {/* Footer with image info */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent z-10 p-4">
          <div className="text-white/80 text-sm text-center">
            {imageWidth && imageHeight && (
              <span>{imageWidth} × {imageHeight} pixels</span>
            )}
            <span className="mx-2">•</span>
            <span>Click outside or press Escape to close</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageModal; 