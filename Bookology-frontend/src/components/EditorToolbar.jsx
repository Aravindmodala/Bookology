import React, { useState } from 'react';
import { 
  Bold, 
  Italic, 
  Underline, 
  List, 
  ListOrdered, 
  Quote, 
  Undo, 
  Redo, 
  Save,
  Search,
  MessageSquare,
  Settings,
  Type,
  Palette,
  Heading1,
  Heading2,
  Heading3,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Link,
  Image,
  Table,
  Minus,
  MoreHorizontal
} from 'lucide-react';

const EditorToolbar = ({ 
  onFormat, 
  onSave, 
  onUndo, 
  onRedo, 
  onToggleComments, 
  showComments, 
  wordCount, 
  charCount 
}) => {
  const [showFontMenu, setShowFontMenu] = useState(false);
  const [showHeadingMenu, setShowHeadingMenu] = useState(false);
  
  const formatText = (command, value = null) => {
    onFormat(command, value);
  };

  const headingOptions = [
    { label: 'Normal Text', command: 'formatBlock', value: 'p' },
    { label: 'Heading 1', command: 'formatBlock', value: 'h1' },
    { label: 'Heading 2', command: 'formatBlock', value: 'h2' },
    { label: 'Heading 3', command: 'formatBlock', value: 'h3' },
  ];

  const fontSizes = ['12px', '14px', '16px', '18px', '20px', '24px', '28px', '32px'];

  return (
    <div className="bg-gray-800 border-b border-gray-700 p-4">
      <div className="flex items-center space-x-4">
        {/* File Operations */}
        <div className="flex items-center space-x-1 border-r border-gray-600 pr-4">
          <button 
            onClick={onSave}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105 group" 
            title="Save (Ctrl+S)"
          >
            <Save className="w-5 h-5 group-hover:text-green-400" />
          </button>
          <button 
            onClick={onUndo}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Undo (Ctrl+Z)"
          >
            <Undo className="w-5 h-5" />
          </button>
          <button 
            onClick={onRedo}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Redo (Ctrl+Y)"
          >
            <Redo className="w-5 h-5" />
          </button>
        </div>

        {/* Text Style */}
        <div className="flex items-center space-x-1 border-r border-gray-600 pr-4">
          {/* Heading Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowHeadingMenu(!showHeadingMenu)}
              className="px-3 py-2 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors flex items-center"
            >
              <Type className="w-4 h-4 mr-2" />
              Normal
              <svg className="w-3 h-3 ml-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
            {showHeadingMenu && (
              <div className="absolute top-full left-0 mt-1 bg-gray-700 border border-gray-600 rounded-lg shadow-lg z-50 min-w-40">
                {headingOptions.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      formatText(option.command, option.value);
                      setShowHeadingMenu(false);
                    }}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-600 first:rounded-t-lg last:rounded-b-lg"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Font Size */}
          <div className="relative">
            <button
              onClick={() => setShowFontMenu(!showFontMenu)}
              className="px-3 py-2 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              16px
            </button>
            {showFontMenu && (
              <div className="absolute top-full left-0 mt-1 bg-gray-700 border border-gray-600 rounded-lg shadow-lg z-50">
                {fontSizes.map((size) => (
                  <button
                    key={size}
                    onClick={() => {
                      formatText('fontSize', size);
                      setShowFontMenu(false);
                    }}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-600 first:rounded-t-lg last:rounded-b-lg"
                  >
                    {size}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Text Formatting */}
        <div className="flex items-center space-x-1 border-r border-gray-600 pr-4">
          <button 
            onClick={() => formatText('bold')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105 group" 
            title="Bold (Ctrl+B)"
          >
            <Bold className="w-5 h-5 group-hover:text-blue-400" />
          </button>
          <button 
            onClick={() => formatText('italic')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105 group" 
            title="Italic (Ctrl+I)"
          >
            <Italic className="w-5 h-5 group-hover:text-blue-400" />
          </button>
          <button 
            onClick={() => formatText('underline')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105 group" 
            title="Underline (Ctrl+U)"
          >
            <Underline className="w-5 h-5 group-hover:text-blue-400" />
          </button>
        </div>

        {/* Alignment */}
        <div className="flex items-center space-x-1 border-r border-gray-600 pr-4">
          <button 
            onClick={() => formatText('justifyLeft')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Align Left"
          >
            <AlignLeft className="w-5 h-5" />
          </button>
          <button 
            onClick={() => formatText('justifyCenter')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Align Center"
          >
            <AlignCenter className="w-5 h-5" />
          </button>
          <button 
            onClick={() => formatText('justifyRight')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Align Right"
          >
            <AlignRight className="w-5 h-5" />
          </button>
        </div>

        {/* Lists & Elements */}
        <div className="flex items-center space-x-1 border-r border-gray-600 pr-4">
          <button 
            onClick={() => formatText('insertUnorderedList')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Bullet List"
          >
            <List className="w-5 h-5" />
          </button>
          <button 
            onClick={() => formatText('insertOrderedList')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Numbered List"
          >
            <ListOrdered className="w-5 h-5" />
          </button>
          <button 
            onClick={() => formatText('formatBlock', 'blockquote')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Quote"
          >
            <Quote className="w-5 h-5" />
          </button>
          <button 
            onClick={() => formatText('insertHorizontalRule')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Horizontal Line"
          >
            <Minus className="w-5 h-5" />
          </button>
        </div>

        {/* Insert Elements */}
        <div className="flex items-center space-x-1 border-r border-gray-600 pr-4">
          <button 
            onClick={() => {
              const url = prompt('Enter URL:');
              if (url) formatText('createLink', url);
            }}
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Insert Link"
          >
            <Link className="w-5 h-5" />
          </button>
          <button 
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Insert Image"
          >
            <Image className="w-5 h-5" />
          </button>
          <button 
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Insert Table"
          >
            <Table className="w-5 h-5" />
          </button>
        </div>

        {/* Tools */}
        <div className="flex items-center space-x-1 border-r border-gray-600 pr-4">
          <button 
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Find & Replace (Ctrl+F)"
          >
            <Search className="w-5 h-5" />
          </button>
          <button 
            onClick={onToggleComments}
            className={`p-2 rounded-lg transition-all duration-200 hover:scale-105 ${
              showComments ? 'bg-blue-600 text-white' : 'hover:bg-gray-700'
            }`} 
            title="Comments"
          >
            <MessageSquare className="w-5 h-5" />
          </button>
          <button 
            className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 hover:scale-105" 
            title="Settings"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>

        {/* Word Count - Always visible */}
        <div className="ml-auto bg-gray-700 px-4 py-2 rounded-lg">
          <div className="text-sm text-gray-300">
            <span className="font-medium text-white">{wordCount.toLocaleString()}</span> words
            <span className="mx-2 text-gray-500">•</span>
            <span className="text-gray-400">{charCount.toLocaleString()} characters</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditorToolbar; 