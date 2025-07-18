import React from 'react';
import { 
  Sparkles, 
  BookOpen, 
  PenTool, 
  FileText, 
  Users,
  Target
} from 'lucide-react';

const WelcomeScreen = ({ onStartWriting, onOpenStory }) => {
  const features = [
    {
      icon: Sparkles,
      title: 'AI-Powered Writing',
      description: 'Get intelligent suggestions and continue your story with AI assistance'
    },
    {
      icon: Users,
      title: 'Character Management',
      description: 'Track characters, relationships, and story elements automatically'
    },
    {
      icon: Target,
      title: 'Story Analysis',
      description: 'Real-time feedback on pacing, emotion, and writing quality'
    },
    {
      icon: FileText,
      title: 'Rich Text Editor',
      description: 'Professional writing tools with Word-like formatting capabilities'
    }
  ];

  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="max-w-4xl mx-auto text-center">
        {/* Hero Section */}
        <div className="mb-12">
          <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <PenTool className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">
            Welcome to Bookology Editor
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            Create compelling stories with our AI-powered writing assistant. 
            Professional tools meet intelligent automation for the ultimate writing experience.
          </p>
          
          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <button
              onClick={onStartWriting}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl font-semibold transition-all duration-200 hover:scale-105 flex items-center justify-center space-x-2"
            >
              <PenTool className="w-5 h-5" />
              <span>Start New Story</span>
            </button>
            <button
              onClick={onOpenStory}
              className="bg-gray-700 hover:bg-gray-600 text-white px-8 py-4 rounded-xl font-semibold transition-all duration-200 hover:scale-105 flex items-center justify-center space-x-2"
            >
              <BookOpen className="w-5 h-5" />
              <span>Open Existing Story</span>
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="bg-gray-800 rounded-xl p-6 border border-gray-700 hover:border-gray-600 transition-all duration-200"
              >
                <div className="w-12 h-12 bg-gray-700 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-400 text-sm">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>

        {/* Quick Tips */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center justify-center">
            <Sparkles className="w-5 h-5 mr-2 text-yellow-400" />
            Quick Tips
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-300">
            <div className="text-center">
              <div className="font-medium text-white mb-1">Keyboard Shortcuts</div>
              <div>Ctrl+S to save, Ctrl+B for bold</div>
            </div>
            <div className="text-center">
              <div className="font-medium text-white mb-1">AI Assistance</div>
              <div>Ctrl+Enter to continue writing</div>
            </div>
            <div className="text-center">
              <div className="font-medium text-white mb-1">Organization</div>
              <div>Drag chapters to reorder</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm">
          Bookology Editor • Built for writers, by writers
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen; 