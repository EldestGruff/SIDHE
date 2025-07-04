import React from 'react';

/**
 * MessageList component
 * Displays conversation messages with proper formatting and metadata
 * 
 * Architecture Decision: Pure component focused on message display
 * with proper accessibility and responsive design
 */
const MessageList = ({ messages }) => {
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };
  
  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    const alignmentClass = isUser ? 'justify-end' : 'justify-start';
    const headerAlignmentClass = isUser ? 'justify-end' : 'justify-start';
    const avatarOrderClass = isUser ? 'order-2' : 'order-1';
    const flexDirectionClass = isUser ? 'flex-row-reverse space-x-reverse' : '';
    const textAlignClass = isUser ? 'text-right' : 'text-left';
    const messageBgClass = isUser 
      ? 'bg-blue-600 text-white' 
      : 'bg-gray-800 text-gray-100 border border-gray-700';
    
    return (
      <div 
        key={message.id}
        className={`flex mb-6 ${alignmentClass}`}
      >
        <div className={`max-w-3xl ${avatarOrderClass}`}>
          {/* Message Header */}
          <div className={`flex items-center mb-2 ${headerAlignmentClass}`}>
            <div className={`flex items-center space-x-2 ${flexDirectionClass}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                isUser 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-200'
              }`}>
                {isUser ? '👤' : '🚀'}
              </div>
              <div className={`text-sm text-gray-400 ${textAlignClass}`}>
                <span className="font-medium">
                  {isUser ? 'You' : 'Riker'}
                </span>
                <span className="ml-2">
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
            </div>
          </div>
          
          {/* Message Content */}
          <div className={`rounded-lg px-4 py-3 ${messageBgClass}`}>
            <div className="prose prose-sm max-w-none">
              <p className="mb-0 whitespace-pre-wrap">{message.content}</p>
            </div>
            
            {/* Intent Information (for user messages) */}
            {message.intent && (
              <div className="mt-2 pt-2 border-t border-blue-500 border-opacity-30">
                <div className="text-xs text-blue-200">
                  Intent: {message.intent.type} 
                  {message.intent.confidence && (
                    <span className="ml-2">
                      ({Math.round(message.intent.confidence * 100)}% confidence)
                    </span>
                  )}
                </div>
              </div>
            )}
            
            {/* Processing Time (for assistant messages) */}
            {message.processing_time && (
              <div className="mt-2 pt-2 border-t border-gray-700 border-opacity-30">
                <div className="text-xs text-gray-400">
                  Processed in {message.processing_time}ms
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };
  
  if (!messages || messages.length === 0) {
    return null;
  }
  
  return (
    <div className="space-y-4">
      {messages.map(renderMessage)}
    </div>
  );
};

export default MessageList;