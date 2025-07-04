import React, { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import TypingIndicator from './TypingIndicator';

/**
 * Main chat interface component
 * Handles user interaction and message display for conversational AI
 * 
 * Architecture Decision: Stateful component managing chat-specific state
 * while receiving conversation data and send handlers from parent.
 */
const ChatInterface = ({ 
  conversation, 
  onSendMessage, 
  isConnected, 
  connectionStatus 
}) => {
  const [isTyping, setIsTyping] = useState(false);
  const [typingTimeout, setTypingTimeout] = useState(null);
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [conversation.messages]);
  
  // Handle typing indicator
  useEffect(() => {
    if (conversation.messages.length > 0) {
      const lastMessage = conversation.messages[conversation.messages.length - 1];
      if (lastMessage.type === 'user') {
        setIsTyping(true);
        
        // Clear existing timeout
        if (typingTimeout) {
          clearTimeout(typingTimeout);
        }
        
        // Set new timeout to hide typing indicator
        const timeout = setTimeout(() => {
          setIsTyping(false);
        }, 3000);
        
        setTypingTimeout(timeout);
      } else {
        setIsTyping(false);
      }
    }
  }, [conversation.messages]);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  const handleSendMessage = (message) => {
    if (isConnected && message.trim()) {
      onSendMessage(message);
      setIsTyping(true);
    }
  };
  
  const getConnectionStatusClass = () => {
    return isConnected ? 'bg-green-500' : 'bg-red-500';
  };
  
  return (
    <div className="flex flex-col h-[calc(100vh-80px)]">
      {/* Chat Header */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">
              Conversation with Riker
            </h2>
            <p className="text-sm text-gray-400">
              Your AI development companion
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-400">
              {conversation.messages.length} messages
            </span>
            <div className={`w-2 h-2 rounded-full ${getConnectionStatusClass()}`} />
          </div>
        </div>
      </div>
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto bg-gray-900 p-6">
        <div className="max-w-4xl mx-auto">
          {conversation.messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🚀</div>
              <h3 className="text-xl font-semibold text-white mb-2">
                Welcome to Riker!
              </h3>
              <p className="text-gray-400 mb-6">
                Your AI development companion is ready to help you build, plan, and manage your projects.
              </p>
              <div className="bg-gray-800 rounded-lg p-4 text-left max-w-md mx-auto">
                <p className="text-sm text-gray-300 mb-2">Try asking:</p>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• "Show me the current system status"</li>
                  <li>• "Create a new authentication system"</li>
                  <li>• "What are my active missions?"</li>
                  <li>• "Help me debug this error"</li>
                </ul>
              </div>
            </div>
          ) : (
            <MessageList messages={conversation.messages} />
          )}
          
          {/* Typing Indicator */}
          {isTyping && isConnected && (
            <TypingIndicator />
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      {/* Message Input */}
      <div className="bg-gray-800 border-t border-gray-700 p-6">
        <div className="max-w-4xl mx-auto">
          <MessageInput 
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
            placeholder={isConnected ? "Message Riker..." : "Connecting..."}
          />
          
          {!isConnected && (
            <div className="mt-2 text-center">
              <span className="text-sm text-red-400">
                {connectionStatus === 'connecting' ? 'Connecting to Riker...' : 'Connection lost. Attempting to reconnect...'}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;