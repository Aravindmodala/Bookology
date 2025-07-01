import React from 'react';
import StoryChatbot from './StoryChatbot';
import { useAuth } from './AuthContext';

const ChatbotTest = () => {
  const { user } = useAuth();

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800 mb-4">Please log in to test the chatbot</h1>
          <p className="text-gray-600">You need to be authenticated to use the story chatbot.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-8 text-center">Story Chatbot Test</h1>
        <div className="bg-white rounded-lg shadow-lg p-6">
          <p className="text-gray-600 mb-6 text-center">
            Test the chatbot with a sample story. Replace the storyId with an actual story ID from your database.
          </p>
          <StoryChatbot 
            storyId="your-story-id-here" 
            storyTitle="Test Story Title"
          />
        </div>
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-800 mb-2">Test Instructions:</h3>
          <ul className="text-blue-700 text-sm space-y-1">
            <li>• Make sure your FastAPI backend is running at http://127.0.0.1:8000</li>
            <li>• Replace "your-story-id-here" with an actual story ID from your database</li>
            <li>• Try asking questions like "What happens in chapter 1?" or "Tell me about the main character"</li>
            <li>• The chatbot uses your chapter embeddings stored in the chapter_chunks table</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ChatbotTest; 