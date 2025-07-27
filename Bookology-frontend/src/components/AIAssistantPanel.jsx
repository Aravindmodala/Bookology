import React, { useState, useRef, useEffect } from 'react';
import { 
  X, 
  Sparkles, 
  RefreshCw, 
  MessageSquare, 
  Palette, 
  Zap, 
  Heart, 
  Users, 
  Target, 
  ChevronRight,
  Check,
  X as XIcon,
  Loader2,
  Plus
} from 'lucide-react';
import { createApiUrl, API_ENDPOINTS } from '../config';
import { useAuth } from '../AuthContext';

const AIAssistantPanel = ({ 
  isOpen, 
  onClose, 
  selectedText, 
  onRewriteSelectedText, 
  isRewriting, 
  rewriteError,
  storyContext, 
  onAcceptSuggestion,
  onRejectSuggestion,
  aiSuggestion,
  isGeneratingSuggestion,
  suggestionError,
  onGenerateSuggestion
}) => {
  const { session } = useAuth();
  const [activeTab, setActiveTab] = useState('write');
  const [acceptedSuggestions, setAcceptedSuggestions] = useState([]);
  const [rejectedSuggestions, setRejectedSuggestions] = useState([]);

  // Continue Writing Feature - now uses props from parent
  const handleContinueWriting = async () => {
    if (onGenerateSuggestion) {
      await onGenerateSuggestion();
    }
  };

  const handleAcceptSuggestion = () => {
    if (aiSuggestion) {
      setAcceptedSuggestions(prev => [...prev, aiSuggestion]);
      if (onAcceptSuggestion) {
        onAcceptSuggestion();
      }
    }
  };

  const handleRejectSuggestion = () => {
    if (aiSuggestion) {
      setRejectedSuggestions(prev => [...prev, aiSuggestion]);
      if (onRejectSuggestion) {
        onRejectSuggestion();
      }
    }
  };

  const handleRewriteSelectedText = async () => {
    if (!selectedText || !session?.access_token) {
      return;
    }

    try {
      const response = await fetch(createApiUrl(API_ENDPOINTS.REWRITE_TEXT), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          text: selectedText,
          context: storyContext?.content || ''
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.rewritten_text) {
        onRewriteSelectedText(data.rewritten_text);
      } else {
        throw new Error(data.error || 'No rewritten text received');
      }
    } catch (err) {
      console.error('Error rewriting text:', err);
    }
  };

  const writeActions = [
    {
      icon: Sparkles,
      title: 'Continue Writing',
      description: 'Generate the next paragraph',
      shortcut: 'Ctrl+Enter',
      action: handleContinueWriting,
      loading: isGeneratingSuggestion
    },
    { 
      icon: RefreshCw,
      title: 'Rewrite Selection',
      description: 'Improve selected text',
      action: handleRewriteSelectedText,
      loading: isRewriting,
      disabled: !selectedText
    },
    { 
      icon: MessageSquare,
      title: 'Add Dialogue',
      description: 'Generate character dialogue',
      action: () => console.log('Add dialogue'),
      disabled: !storyContext?.content
    },
    {
      icon: Palette,
      title: 'Add Description',
      description: 'Enhance scene description',
      action: () => console.log('Add description'),
      disabled: !storyContext?.content
    },
    {
      icon: Zap,
      title: 'Add Action',
      description: 'Create action sequences',
      action: () => console.log('Add action'),
      disabled: !storyContext?.content
    },
    {
      icon: Heart,
      title: 'Deepen Emotion',
      description: 'Add emotional depth',
      action: () => console.log('Deepen emotion'),
      disabled: !storyContext?.content
    }
  ];

  const analyzeActions = [
    {
      icon: Target,
      title: 'Pacing Analysis',
      description: 'Check story pacing',
      action: () => console.log('Analyze pacing')
    },
    {
      icon: Users,
      title: 'Character Development',
      description: 'Analyze character arcs',
      action: () => console.log('Analyze characters')
    },
    {
      icon: MessageSquare,
      title: 'Dialogue Quality',
      description: 'Review dialogue effectiveness',
      action: () => console.log('Analyze dialogue')
    }
  ];

  const characterActions = [
    {
      icon: Users,
      title: 'Character Profiles',
      description: 'View all characters',
      action: () => console.log('View characters')
    },
    {
      icon: Plus,
      title: 'Add Character',
      description: 'Create new character',
      action: () => console.log('Add character')
    }
  ];

  const insightActions = [
    {
      icon: Target,
      title: 'Story Insights',
      description: 'Get writing tips',
      action: () => console.log('Get insights')
    },
    {
      icon: Sparkles,
      title: 'Writing Prompts',
      description: 'Creative prompts',
      action: () => console.log('Get prompts')
    }
  ];

  const tabs = [
    { id: 'write', label: 'Write', icon: Sparkles },
    { id: 'analyze', label: 'Analyze', icon: Target },
    { id: 'characters', label: 'Characters', icon: Users },
    { id: 'insights', label: 'Insights', icon: Zap }
  ];

  const getActionsForTab = () => {
    switch (activeTab) {
      case 'write': return writeActions;
      case 'analyze': return analyzeActions;
      case 'characters': return characterActions;
      case 'insights': return insightActions;
      default: return writeActions;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="h-full bg-gray-800 flex flex-col">
      {/* Header */}
              <div className="flex items-center justify-between p-3 border-b border-gray-700">
        <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <h3 className="text-sm font-semibold text-white">AI Assistant</h3>
        </div>
        <button
          onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
        >
            <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-700">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center space-x-1 py-2 text-xs font-medium transition-colors ${
                activeTab === tab.id
                    ? 'text-blue-400 border-b-2 border-blue-400'
                    : 'text-gray-400 hover:text-gray-300'
              }`}
            >
                <Icon className="w-3 h-3" />
                <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Content */}
        <div className="flex-1 overflow-y-auto p-3">
        {/* Continue Writing Suggestion */}
        {activeTab === 'write' && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-white text-sm font-medium">Continue Writing</h4>
                <button
                onClick={handleContinueWriting}
                disabled={isGeneratingSuggestion}
                className="text-blue-400 hover:text-blue-300 text-xs flex items-center space-x-1 disabled:opacity-50"
              >
                {isGeneratingSuggestion ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <RefreshCw className="w-3 h-3" />
                )}
                <span>New</span>
              </button>
            </div>

            {suggestionError && (
              <div className="text-red-400 text-xs p-2 bg-red-900/20 border border-red-800 rounded mb-3">
                {suggestionError}
          </div>
        )}

            {aiSuggestion && (
              <div className="bg-gray-700 rounded p-3 border border-gray-600">
                <p className="text-gray-200 text-xs leading-relaxed mb-3">
                  {aiSuggestion}
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={handleAcceptSuggestion}
                    className="flex items-center space-x-1 px-2 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors"
                  >
                    <Check className="w-3 h-3" />
                    <span>Accept</span>
                  </button>
                  <button
                    onClick={handleRejectSuggestion}
                    className="flex items-center space-x-1 px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
                  >
                    <XIcon className="w-3 h-3" />
                    <span>Reject</span>
                    </button>
                  </div>
              </div>
            )}

            {!aiSuggestion && !isGeneratingSuggestion && (
              <div className="text-center py-4">
                <Sparkles className="w-6 h-6 text-gray-500 mx-auto mb-1" />
                <p className="text-gray-400 text-xs">
                  Click "New" to get AI suggestions
                </p>
              </div>
            )}
          </div>
        )}

        {/* Action Cards */}
        <div className="space-y-2">
          {getActionsForTab().map((action, index) => {
            const Icon = action.icon;
            return (
              <button
                key={index}
                onClick={action.action}
                disabled={action.disabled || action.loading}
                className="w-full text-left p-3 bg-gray-700 rounded border border-gray-600 hover:border-gray-500 transition-all duration-200 hover:scale-[1.01] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-start space-x-2">
                  <div className="flex-shrink-0">
                    {action.loading ? (
                      <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                    ) : (
                      <Icon className="w-4 h-4 text-blue-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <h4 className="text-white text-sm font-medium mb-1">{action.title}</h4>
                    <p className="text-gray-400 text-xs mb-1">{action.description}</p>
                    {action.shortcut && (
                      <span className="text-gray-500 text-xs bg-gray-800 px-1 py-0.5 rounded">
                        {action.shortcut}
                      </span>
                    )}
                  </div>
                  <ChevronRight className="w-3 h-3 text-gray-500 flex-shrink-0" />
                </div>
              </button>
            );
          })}
            </div>

        {/* Error Display */}
        {rewriteError && (
          <div className="mt-3 p-2 bg-red-900/20 border border-red-800 rounded">
            <p className="text-red-200 text-xs">{rewriteError}</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>AI Powered</span>
          <span>2 min ago</span>
        </div>
      </div>
    </div>
  );
};

export default AIAssistantPanel; 