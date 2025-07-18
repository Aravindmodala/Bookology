import React, { useState } from 'react';
import { 
  Wand2, 
  Users, 
  Brain, 
  Target, 
  Lightbulb, 
  MessageCircle, 
  BarChart3, 
  EyeOff, 
  RefreshCw,
  Sparkles,
  Palette,
  BookOpenCheck,
  TrendingUp,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

const AIAssistantPanel = ({ isOpen, onClose, selectedText, storyContext }) => {
  const [activeTab, setActiveTab] = useState('write');
  const [isProcessing, setIsProcessing] = useState(false);

  const tabs = [
    { id: 'write', label: 'Write', icon: Wand2 },
    { id: 'analyze', label: 'Analyze', icon: Brain },
    { id: 'characters', label: 'Characters', icon: Users },
    { id: 'insights', label: 'Insights', icon: BarChart3 }
  ];

  const aiTasks = [
    { 
      id: 'continue', 
      label: 'Continue Writing', 
      icon: '✨', 
      description: 'Generate the next paragraph',
      shortcut: 'Ctrl+Enter'
    },
    { 
      id: 'rewrite', 
      label: 'Rewrite Selection', 
      icon: '🔄', 
      description: 'Improve selected text',
      disabled: !selectedText
    },
    { 
      id: 'dialogue', 
      label: 'Add Dialogue', 
      icon: '💬', 
      description: 'Generate character dialogue'
    },
    { 
      id: 'description', 
      label: 'Add Description', 
      icon: '🎨', 
      description: 'Enhance scene description'
    },
    { 
      id: 'action', 
      label: 'Add Action', 
      icon: '⚡', 
      description: 'Create action sequences'
    },
    { 
      id: 'emotion', 
      label: 'Deepen Emotion', 
      icon: '💗', 
      description: 'Add emotional depth'
    }
  ];

  const analysisResults = {
    readability: { score: 85, level: 'Advanced', status: 'good' },
    pacing: { score: 72, level: 'Moderate', status: 'warning' },
    emotionalImpact: { score: 91, level: 'High', status: 'excellent' },
    dialogue: { score: 78, level: 'Good', status: 'good' }
  };

  const storyElements = {
    characters: ['Clara', 'Ethan', 'Lisa (memory)'],
    setting: 'Bookstore café',
    mood: 'Contemplative, hopeful',
    tension: 'Medium',
    timeOfDay: 'Afternoon',
    weather: 'Sunny'
  };

  const writingInsights = [
    { type: 'strength', text: 'Strong character development in Clara', icon: CheckCircle },
    { type: 'suggestion', text: 'Consider adding more sensory details', icon: Lightbulb },
    { type: 'warning', text: 'Pacing could be improved in dialogue', icon: AlertCircle }
  ];

  const handleAITask = async (taskId) => {
    setIsProcessing(true);
    // Simulate AI processing
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsProcessing(false);
    
    // Here you would integrate with your AI backend
    console.log(`Executing AI task: ${taskId}`);
  };

  if (!isOpen) return null;

  return (
    <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Smart Writer</h3>
            <p className="text-xs text-gray-400">AI-Powered Assistant</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <EyeOff className="w-4 h-4" />
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
              className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-400 border-b-2 border-blue-400 bg-gray-750'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Icon className="w-3 h-3 mx-auto mb-1" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'write' && (
          <div className="space-y-4">
            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-2">
              {aiTasks.map((task) => (
                <button
                  key={task.id}
                  onClick={() => handleAITask(task.id)}
                  disabled={task.disabled || isProcessing}
                  className={`p-3 rounded-lg border text-left transition-all duration-200 hover:scale-105 ${
                    task.disabled 
                      ? 'border-gray-600 bg-gray-700/50 opacity-50 cursor-not-allowed'
                      : 'border-gray-600 bg-gray-700 hover:bg-gray-600 hover:border-blue-500'
                  }`}
                >
                  <div className="text-lg mb-1">{task.icon}</div>
                  <div className="text-sm font-medium text-white">{task.label}</div>
                  <div className="text-xs text-gray-400">{task.description}</div>
                  {task.shortcut && (
                    <div className="text-xs text-gray-500 mt-1">{task.shortcut}</div>
                  )}
                </button>
              ))}
            </div>

            {/* Custom Prompt */}
            <div className="bg-gray-700 rounded-lg p-4">
              <label className="block text-sm font-medium text-white mb-2">
                Custom AI Request
              </label>
              <textarea
                className="w-full h-20 bg-gray-600 border border-gray-500 rounded-lg px-3 py-2 text-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ask AI to help with anything..."
              />
              <button 
                onClick={() => handleAITask('custom')}
                disabled={isProcessing}
                className="mt-2 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white py-2 px-4 rounded-lg text-sm font-medium transition-colors flex items-center justify-center"
              >
                {isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-4 h-4 mr-2" />
                    Generate
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'analyze' && (
          <div className="space-y-4">
            {/* Analysis Metrics */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-white mb-3 flex items-center">
                <BarChart3 className="w-4 h-4 mr-2" />
                Writing Analysis
              </h4>
              <div className="space-y-3">
                {Object.entries(analysisResults).map(([key, data]) => (
                  <div key={key}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-300 capitalize">
                        {key.replace(/([A-Z])/g, ' $1')}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        data.status === 'excellent' ? 'bg-green-600 text-white' :
                        data.status === 'good' ? 'bg-blue-600 text-white' :
                        'bg-yellow-600 text-white'
                      }`}>
                        {data.level}
                      </span>
                    </div>
                    <div className="w-full bg-gray-600 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          data.status === 'excellent' ? 'bg-green-500' :
                          data.status === 'good' ? 'bg-blue-500' :
                          'bg-yellow-500'
                        }`}
                        style={{ width: `${data.score}%` }}
                      />
                    </div>
                    <div className="text-xs text-gray-400 mt-1">{data.score}/100</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Insights */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-white mb-3">Insights</h4>
              <div className="space-y-2">
                {writingInsights.map((insight, index) => {
                  const Icon = insight.icon;
                  return (
                    <div key={index} className="flex items-start space-x-2">
                      <Icon className={`w-4 h-4 mt-0.5 ${
                        insight.type === 'strength' ? 'text-green-400' :
                        insight.type === 'suggestion' ? 'text-blue-400' :
                        'text-yellow-400'
                      }`} />
                      <span className="text-sm text-gray-300">{insight.text}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'characters' && (
          <div className="space-y-4">
            {/* Character Profiles */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-white mb-3 flex items-center">
                <Users className="w-4 h-4 mr-2" />
                Active Characters
              </h4>
              <div className="space-y-3">
                {storyElements.characters.map((character, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-600 rounded">
                    <span className="text-sm text-white">{character}</span>
                    <button className="text-xs text-blue-400 hover:text-blue-300">
                      Edit
                    </button>
                  </div>
                ))}
                <button className="w-full p-2 border border-dashed border-gray-500 rounded text-sm text-gray-400 hover:text-white hover:border-gray-400 transition-colors">
                  + Add Character
                </button>
              </div>
            </div>

            {/* Story Elements */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-white mb-3">Story Elements</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(storyElements).filter(([key]) => key !== 'characters').map(([key, value]) => (
                  <div key={key} className="bg-gray-600 p-2 rounded">
                    <div className="text-xs text-gray-400 capitalize">{key}</div>
                    <div className="text-white">{value}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'insights' && (
          <div className="space-y-4">
            {/* Writing Progress */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-white mb-3 flex items-center">
                <TrendingUp className="w-4 h-4 mr-2" />
                Writing Progress
              </h4>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-300">Daily Goal</span>
                    <span className="text-white">1,470 / 2,000 words</span>
                  </div>
                  <div className="w-full bg-gray-600 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-full" style={{ width: '73.5%' }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-300">Story Progress</span>
                    <span className="text-white">1,470 / 4,000 words</span>
                  </div>
                  <div className="w-full bg-gray-600 rounded-full h-2">
                    <div className="bg-green-500 h-2 rounded-full" style={{ width: '36.75%' }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Reading Time */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-white mb-3">Reader Stats</h4>
              <div className="grid grid-cols-2 gap-3 text-center">
                <div>
                  <div className="text-2xl font-bold text-blue-400">6m</div>
                  <div className="text-xs text-gray-400">Reading Time</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-400">3</div>
                  <div className="text-xs text-gray-400">Chapters</div>
                </div>
              </div>
            </div>

            {/* Writing Streak */}
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-white mb-3">Writing Streak</h4>
              <div className="text-center">
                <div className="text-3xl font-bold text-orange-400 mb-1">7</div>
                <div className="text-sm text-gray-300">Days in a row</div>
                <div className="text-xs text-gray-400 mt-2">Keep it up! 🔥</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700">
        <div className="text-xs text-gray-400 text-center">
          Powered by AI • Last updated 2 min ago
        </div>
      </div>
    </div>
  );
};

export default AIAssistantPanel; 