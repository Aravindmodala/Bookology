import React from 'react';
import { 
  Eye, 
  EyeOff, 
  Save, 
  Undo, 
  Redo, 
  Bold, 
  Italic, 
  Underline, 
  List, 
  ListOrdered,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Sparkles,
  Focus,
  Target,
  BarChart3,
  Settings,
  Zap,
  Loader2,
  Gamepad2
} from 'lucide-react';

const EditorToolbar = ({
  isSidebarCollapsed,
  onToggleSidebar,
  onToggleAIPanel,
  isAIPanelOpen,
  onToggleFocusMode,
  isFocusMode,
  onGenerateSuggestion,
  isGeneratingSuggestion,
  wordCount,
  showWordCount,
  onToggleWordCount,
  gameMode,
  onToggleGameMode
}) => {
  const handleFormat = (command) => {
    document.execCommand(command, false, null);
  };

  const handleSave = () => {
    // Auto-save functionality
    console.log('Auto-saving...');
  };

  const handleUndo = () => {
    document.execCommand('undo', false, null);
  };

  const handleRedo = () => {
    document.execCommand('redo', false, null);
  };

  return (
    <div className="bg-gray-800 border-b border-gray-700 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Left Section */}
        <div className="flex items-center space-x-4">
          {/* Sidebar Toggle */}
          <button
            onClick={onToggleSidebar}
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            title="Toggle Sidebar"
          >
            <Eye className="w-4 h-4" />
          </button>

          {/* AI Panel Toggle */}
          <button
            onClick={onToggleAIPanel}
            className={`p-2 rounded-lg transition-colors ${
              isAIPanelOpen 
                ? 'text-blue-400 bg-blue-900/30' 
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
            title="Toggle AI Assistant"
          >
            <Sparkles className="w-4 h-4" />
          </button>

          {/* Focus Mode Toggle */}
          <button
            onClick={onToggleFocusMode}
            className={`p-2 rounded-lg transition-colors ${
              isFocusMode 
                ? 'text-green-400 bg-green-900/30' 
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
            title="Toggle Focus Mode (Ctrl+Shift+F)"
          >
            <Focus className="w-4 h-4" />
          </button>

          {/* Game Mode Toggle */}
          <button
            onClick={onToggleGameMode}
            className={`p-2 rounded-lg transition-colors ${
              gameMode 
                ? 'text-purple-400 bg-purple-900/30' 
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
            title="Toggle Game Mode"
          >
            <Gamepad2 className="w-4 h-4" />
          </button>

          {/* AI Suggestion Button */}
          <button
            onClick={onGenerateSuggestion}
            disabled={isGeneratingSuggestion}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white text-sm rounded-lg transition-colors disabled:cursor-not-allowed"
            title="Generate AI Suggestion (Ctrl+Enter)"
          >
            {isGeneratingSuggestion ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            <span>AI Suggestion</span>
          </button>
        </div>

        {/* Center Section - Formatting Tools */}
        <div className="flex items-center space-x-1">
          {/* Text Formatting */}
          <div className="flex items-center space-x-1 bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => handleFormat('bold')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded transition-colors"
              title="Bold (Ctrl+B)"
            >
              <Bold className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleFormat('italic')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded transition-colors"
              title="Italic (Ctrl+I)"
            >
              <Italic className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleFormat('underline')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded transition-colors"
              title="Underline (Ctrl+U)"
            >
              <Underline className="w-4 h-4" />
            </button>
          </div>

          {/* Alignment */}
          <div className="flex items-center space-x-1 bg-gray-700 rounded-lg p-1 ml-2">
            <button
              onClick={() => handleFormat('justifyLeft')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded transition-colors"
              title="Align Left"
            >
              <AlignLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleFormat('justifyCenter')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded transition-colors"
              title="Align Center"
            >
              <AlignCenter className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleFormat('justifyRight')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded transition-colors"
              title="Align Right"
            >
              <AlignRight className="w-4 h-4" />
            </button>
          </div>

          {/* Lists */}
          <div className="flex items-center space-x-1 bg-gray-700 rounded-lg p-1 ml-2">
            <button
              onClick={() => handleFormat('insertUnorderedList')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded transition-colors"
              title="Bullet List"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleFormat('insertOrderedList')}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded transition-colors"
              title="Numbered List"
            >
              <ListOrdered className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-4">
          {/* Word Count Toggle */}
          <button
            onClick={onToggleWordCount}
            className={`p-2 rounded-lg transition-colors ${
              showWordCount 
                ? 'text-blue-400 bg-blue-900/30' 
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
            title="Toggle Word Count (Ctrl+Shift+W)"
          >
            <BarChart3 className="w-4 h-4" />
          </button>

          {/* Word Count Display */}
          {showWordCount && (
            <div className="flex items-center space-x-2 text-sm text-gray-300">
              <span className="font-mono">{wordCount}</span>
              <span className="text-gray-500">words</span>
            </div>
          )}

          {/* Undo/Redo */}
          <div className="flex items-center space-x-1 bg-gray-700 rounded-lg p-1">
            <button
              onClick={handleUndo}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded transition-colors"
              title="Undo (Ctrl+Z)"
            >
              <Undo className="w-4 h-4" />
            </button>
            <button
              onClick={handleRedo}
              className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded transition-colors"
              title="Redo (Ctrl+Y)"
            >
              <Redo className="w-4 h-4" />
            </button>
          </div>

          {/* Auto-save indicator */}
          <div className="flex items-center space-x-2 text-xs text-gray-400">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Auto-saved</span>
          </div>

          {/* Settings */}
          <button
            className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Keyboard Shortcuts Help */}
      <div className="mt-2 text-xs text-gray-500 flex items-center justify-center space-x-4">
        <span>Ctrl+Enter: AI Suggestion</span>
        <span>Ctrl+Shift+F: Focus Mode</span>
        <span>Ctrl+Shift+W: Toggle Word Count</span>
        <span>Ctrl+Z: Undo</span>
        <span>Ctrl+Y: Redo</span>
      </div>
    </div>
  );
};

export default EditorToolbar; 