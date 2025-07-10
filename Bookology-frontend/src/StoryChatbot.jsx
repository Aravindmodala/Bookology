import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from './AuthContext';
import { createApiUrl, API_ENDPOINTS } from './config';

const StoryChatbot = ({ storyId, storyTitle }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const { user, session } = useAuth();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Ensure embeddings exist for this story when component mounts
  useEffect(() => {
    const ensureEmbeddings = async () => {
      if (!storyId || !session?.access_token) return;
      
      try {
        const response = await fetch(
          createApiUrl(API_ENDPOINTS.ENSURE_EMBEDDINGS.replace('{story_id}', storyId)), 
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${session.access_token}`,
              'Content-Type': 'application/json'
            }
          }
        );
        
        if (response.ok) {
          const data = await response.json();
          console.log('Embeddings status:', data.message);
        }
      } catch (error) {
        console.warn('Could not ensure embeddings:', error);
      }
    };

    ensureEmbeddings();
  }, [storyId, session?.access_token]);

  useEffect(() => {
    // Add welcome message when component loads
    setMessages([
      {
        id: Date.now(),
        type: 'bot',
        content: `Hi! I'm your story assistant for "${storyTitle}". You can ask me questions about your story, request modifications, or explore multiverse connections with your other Stories. What would you like to know?`,
        timestamp: new Date().toLocaleTimeString()
      }
    ]);
  }, [storyTitle]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const token = session?.access_token;
      console.log('Sending request with token:', token ? 'Token present' : 'No token');
      
      if (!token) {
        throw new Error('No authentication token available. Please log in.');
      }

      const response = await fetch(createApiUrl(API_ENDPOINTS.STORY_CHAT), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_id: user.id,
          story_id: storyId,
          message: inputMessage,
          session_id: `session_${user.id}_${storyId}`
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.content || data.message || 'I received your message but had trouble processing it.',
        timestamp: new Date().toLocaleTimeString(),
        intent: data.intent,
        sources: data.sources
      };

      setMessages(prev => [...prev, botMessage]);

    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, I encountered an error. Please try again later.',
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getMessageIcon = (type, intent) => {
    if (type === 'user') return '👤';
    if (intent === 'query') return '🔍';
    if (intent === 'modify') return '✏️';
    if (intent === 'multiverse') return '🌌';
    return '🤖';
  };

  return (
    <div className="story-chatbot bg-gray-900 border border-gray-800 rounded-lg flex flex-col h-96 max-w-2xl mx-auto">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 text-white p-4 rounded-t-lg">
        <h3 className="font-semibold text-lg text-white">Story Assistant</h3>
        <p className="text-sm text-gray-300">Chatting about: {storyTitle}</p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.type === 'user'
                  ? 'bg-white text-black border border-gray-600'
                  : message.isError
                  ? 'bg-red-900/20 text-red-400 border border-red-800'
                  : 'bg-gray-800 text-gray-200 border border-gray-700'
              }`}
            >
              <div className="flex items-start space-x-2">
                <span className="text-lg">
                  {getMessageIcon(message.type, message.intent)}
                </span>
                <div className="flex-1">
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-2 text-xs text-gray-400">
                      <p>Sources: {message.sources.length} chapter(s)</p>
                    </div>
                  )}
                  <p className="text-xs mt-1 text-gray-400">{message.timestamp}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 text-gray-200 border border-gray-700 px-4 py-2 rounded-lg max-w-xs">
              <div className="flex items-center space-x-2">
                <span className="text-lg">🤖</span>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 text-red-400 px-4 py-2 text-sm">
          {error}
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about your story, request changes, or explore connections..."
            className="textarea-field flex-1 text-sm resize-none"
            rows="2"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="btn-primary px-4 py-2 text-sm font-medium flex items-center space-x-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <>
                <span>Send</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </>
            )}
          </button>
        </div>
        
        {/* Helper Text */}
        <div className="mt-2 text-xs text-gray-400">
          💡 Try: "What happens in chapter 2?" • "Change the main character's name to Alex" • "Connect this story with my other Stories"
        </div>
      </div>
    </div>
  );
};

export default StoryChatbot;
