import React from 'react';
import { Check, AlertCircle, Loader2, Clock } from 'lucide-react';

/**
 * Save status indicator component
 * Shows current save status with visual feedback
 */
const SaveStatusIndicator = ({ 
  saveStatus = 'saved', 
  isSaving = false, 
  hasUnsavedChanges = false,
  error = null,
  className = ''
}) => {
  const getStatusConfig = () => {
    switch (saveStatus) {
      case 'saving':
        return {
          icon: <Loader2 className="w-4 h-4 animate-spin" />,
          text: 'Saving...',
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-500/10',
          borderColor: 'border-yellow-500/20'
        };
      
      case 'saved':
        return {
          icon: <Check className="w-4 h-4" />,
          text: hasUnsavedChanges ? 'All changes saved' : 'Saved',
          color: 'text-green-500',
          bgColor: 'bg-green-500/10',
          borderColor: 'border-green-500/20'
        };
      
      case 'error':
        return {
          icon: <AlertCircle className="w-4 h-4" />,
          text: error || 'Save failed',
          color: 'text-red-500',
          bgColor: 'bg-red-500/10',
          borderColor: 'border-red-500/20'
        };
      
      case 'unsaved':
        return {
          icon: <Clock className="w-4 h-4" />,
          text: 'Unsaved changes',
          color: 'text-orange-500',
          bgColor: 'bg-orange-500/10',
          borderColor: 'border-orange-500/20'
        };
      
      default:
        return {
          icon: <Clock className="w-4 h-4" />,
          text: 'Ready',
          color: 'text-gray-500',
          bgColor: 'bg-gray-500/10',
          borderColor: 'border-gray-500/20'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className={`flex items-center space-x-2 px-3 py-2 rounded-md border ${config.bgColor} ${config.borderColor} ${className}`}>
      <div className={`${config.color}`}>
        {config.icon}
      </div>
      <span className={`text-sm font-medium ${config.color}`}>
        {config.text}
      </span>
      
      {/* Show unsaved indicator */}
      {hasUnsavedChanges && saveStatus === 'saved' && (
        <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse" />
      )}
    </div>
  );
};

export default SaveStatusIndicator; 