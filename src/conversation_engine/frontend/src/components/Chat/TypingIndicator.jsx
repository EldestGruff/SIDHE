import React from 'react';

/**
 * TypingIndicator component
 * Shows animated typing indicator when assistant is processing
 * 
 * Architecture Decision: Simple animated component for user feedback
 * during processing delays
 */
const TypingIndicator = () => {
  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-3xl">
        {/* Header */}
        <div className="flex items-center mb-2">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-gray-700 text-gray-200 flex items-center justify-center text-sm font-medium">
              🚀
            </div>
            <div className="text-sm text-gray-400">
              <span className="font-medium">Riker</span>
              <span className="ml-2 text-gray-500">is thinking...</span>
            </div>
          </div>
        </div>
        
        {/* Typing Animation */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-3">
          <div className="flex items-center space-x-1">
            <div className="flex space-x-1">
              <div 
                className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" 
                style={{ animationDelay: '0ms' }}
              ></div>
              <div 
                className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" 
                style={{ animationDelay: '150ms' }}
              ></div>
              <div 
                className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" 
                style={{ animationDelay: '300ms' }}
              ></div>
            </div>
            <span className="text-sm text-gray-400 ml-2">Processing your request</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;