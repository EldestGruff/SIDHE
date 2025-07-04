import React, { useState, useRef, useEffect } from 'react';

/**
 * MessageInput component
 * Handles user input with send functionality and keyboard shortcuts
 * 
 * Architecture Decision: Controlled component with auto-resize
 * and proper accessibility features
 */
const MessageInput = ({ onSendMessage, isConnected, placeholder = "Type a message..." }) => {
  const [message, setMessage] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const textareaRef = useRef(null);
  
  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  }, [message]);
  
  // Focus on mount
  useEffect(() => {
    if (textareaRef.current && isConnected) {
      textareaRef.current.focus();
    }
  }, [isConnected]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (message.trim() && isConnected && !isComposing) {
      onSendMessage(message.trim());
      setMessage('');
      
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };
  
  const handleKeyDown = (e) => {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSubmit(e);
    }
  };
  
  const handleCompositionStart = () => {
    setIsComposing(true);
  };
  
  const handleCompositionEnd = () => {
    setIsComposing(false);
  };
  
  const buttonDisabled = !message.trim() || !isConnected || isComposing;
  
  return (
    <form onSubmit={handleSubmit} className="flex items-end space-x-3">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          onCompositionStart={handleCompositionStart}
          onCompositionEnd={handleCompositionEnd}
          placeholder={placeholder}
          disabled={!isConnected}
          rows={1}
          className="w-full resize-none rounded-lg border border-gray-600 bg-gray-700 px-4 py-3 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ minHeight: '48px', maxHeight: '200px' }}
        />
        
        {/* Character count (appears when approaching limit) */}
        {message.length > 500 && (
          <div className="absolute bottom-1 right-1 text-xs text-gray-400">
            {message.length}/1000
          </div>
        )}
      </div>
      
      <button
        type="submit"
        disabled={buttonDisabled}
        className="flex items-center justify-center w-12 h-12 rounded-lg bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        title={buttonDisabled ? 'Enter a message to send' : 'Send message (Enter)'}
      >
        <svg 
          className="w-5 h-5" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" 
          />
        </svg>
      </button>
    </form>
  );
};

export default MessageInput;