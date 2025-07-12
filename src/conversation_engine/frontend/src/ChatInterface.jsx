import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Bot, User, Sparkles, Zap, AlertCircle, CheckCircle, Loader, Send, Gem } from 'lucide-react';

// Enhanced WebSocket Hook with Fixed Message Handling
function useWebSocket(url = 'ws://localhost:8000/ws') {
  const [socket, setSocket] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [isConnected, setIsConnected] = useState(false);
  
  const connect = useCallback(() => {
    if (socket?.readyState === WebSocket.OPEN) return;

    try {
      setConnectionStatus('connecting');
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('🧙‍♂️ SIDHE WebSocket Connection Established');
        setConnectionStatus('connected');
        setIsConnected(true);
        setSocket(ws);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📨 SIDHE Received:', message);
          
          // Trigger custom event for message handling
          window.dispatchEvent(new CustomEvent('sidhe-message', { detail: message }));
        } catch (error) {
          console.error('🚨 SIDHE Message Parse Error:', error);
        }
      };

      ws.onclose = () => {
        console.log('🌙 SIDHE WebSocket Connection Closed');
        setConnectionStatus('disconnected');
        setIsConnected(false);
        setSocket(null);
      };

      ws.onerror = (error) => {
        console.error('🚨 SIDHE WebSocket Error:', error);
        setConnectionStatus('error');
      };

    } catch (error) {
      console.error('🚨 SIDHE WebSocket Connection Failed:', error);
      setConnectionStatus('error');
    }
  }, [url, socket?.readyState]);

  const sendMessage = useCallback((message) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      console.warn('🚨 SIDHE WebSocket not connected');
      return false;
    }

    try {
      const formattedMessage = {
        type: 'user_message',
        content: message.content || message,
        conversation_id: message.conversation_id || `conv_${Date.now()}`,
        timestamp: new Date().toISOString(),
        ...message
      };

      console.log('📤 SIDHE Sending:', formattedMessage);
      socket.send(JSON.stringify(formattedMessage));
      return true;
    } catch (error) {
      console.error('🚨 SIDHE Send Message Error:', error);
      return false;
    }
  }, [socket]);

  useEffect(() => {
    connect();
    return () => {
      if (socket) socket.close();
    };
  }, [connect, socket]);

  return { socket, connectionStatus, isConnected, sendMessage, connect };
}

// Message Component
function Message({ message }) {
  const isUser = message.sender === 'user';
  const isSystem = message.sender === 'system';

  const getMessageIcon = () => {
    if (isUser) return <User className="w-4 h-4" />;
    if (isSystem) return <Zap className="w-4 h-4" />;
    return <Bot className="w-4 h-4" />;
  };

  const getMessageStyle = () => {
    if (isUser) {
      return 'bg-gradient-to-r from-purple-600 to-pink-600 text-white ml-auto';
    }
    if (isSystem) {
      return 'bg-gradient-to-r from-slate-700 to-slate-600 text-purple-200 border border-purple-500/30';
    }
    return 'bg-gradient-to-r from-indigo-700 to-purple-700 text-white border border-purple-400/30';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${getMessageStyle()}`}>
        <div className="flex items-start space-x-2">
          <div className="mt-0.5 opacity-75">
            {getMessageIcon()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="prose prose-sm text-current">
              <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                {message.content}
              </p>
            </div>
            
            {/* Metadata Display */}
            {message.metadata && (
              <div className="mt-2 space-y-1 text-xs opacity-75">
                {message.metadata.intent && (
                  <div className="flex items-center space-x-1">
                    <Sparkles className="w-3 h-3" />
                    <span>Intent: {message.metadata.intent}</span>
                  </div>
                )}
                {message.metadata.confidence && (
                  <div className="flex items-center space-x-1">
                    <CheckCircle className="w-3 h-3" />
                    <span>Confidence: {(message.metadata.confidence * 100).toFixed(0)}%</span>
                  </div>
                )}
                {message.metadata.plugin && (
                  <div className="flex items-center space-x-1">
                    <Zap className="w-3 h-3" />
                    <span>Plugin: {message.metadata.plugin}</span>
                  </div>
                )}
              </div>
            )}
            
            {/* Error indicator */}
            {message.isError && (
              <div className="mt-2 flex items-center space-x-1 text-xs text-red-300">
                <AlertCircle className="w-3 h-3" />
                <span>Error occurred</span>
              </div>
            )}
            
            {/* Timestamp */}
            <div className="mt-2 text-xs opacity-50">
              {formatTimestamp(message.timestamp)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Typing Indicator Component
function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="bg-gradient-to-r from-indigo-700 to-purple-700 text-white border border-purple-400/30 px-4 py-3 rounded-2xl">
        <div className="flex items-center space-x-2">
          <Bot className="w-4 h-4 text-purple-300" />
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-purple-300 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-purple-300 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
            <div className="w-2 h-2 bg-purple-300 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
          </div>
          <span className="text-sm text-purple-200">SIDHE is weaving wisdom...</span>
        </div>
      </div>
    </div>
  );
}

// Connection Status Component
function ConnectionStatus({ status, isConnected }) {
  const getStatusColor = () => {
    switch (status) {
      case 'connected': return 'text-green-400';
      case 'connecting': return 'text-yellow-400';
      case 'disconnected': case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'connected': return <CheckCircle className="w-4 h-4" />;
      case 'connecting': return <Loader className="w-4 h-4 animate-spin" />;
      case 'disconnected': case 'error': return <AlertCircle className="w-4 h-4" />;
      default: return <div className="w-4 h-4" />;
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
      {getStatusIcon()}
      <span className="text-sm font-medium capitalize">
        {status === 'connected' ? 'SIDHE Awakened' : 
         status === 'connecting' ? 'Awakening SIDHE...' :
         'SIDHE Slumbers'}
      </span>
    </div>
  );
}

// Main Chat Interface Component
export default function SIDHEChatInterface() {
  const { isConnected, connectionStatus, sendMessage } = useWebSocket();
  const [messages, setMessages] = useState([
    {
      id: '1',
      type: 'system',
      sender: 'system',
      content: '🧙‍♂️ SIDHE awakens... The ancient AI wisdom flows through the digital realm.',
      timestamp: new Date().toISOString()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Handle incoming WebSocket messages
  useEffect(() => {
    const handleMessage = (event) => {
      const message = event.detail;
      
      // Process all message types from backend
      const processedMessage = {
        id: Date.now().toString(),
        timestamp: message.timestamp || new Date().toISOString(),
        ...message
      };

      // Map different response types to standardized format
      if (message.type === 'assistant_response' || 
          message.type === 'answer' || 
          message.type === 'plugin_response' ||
          message.type === 'intent_response') {
        
        processedMessage.sender = 'assistant';
        processedMessage.content = message.content || message.response || message.answer;
        
        processedMessage.metadata = {
          intent: message.intent || message.metadata?.intent,
          confidence: message.confidence || message.metadata?.confidence,
          plugin: message.plugin || message.source,
          original_type: message.type
        };
      } else if (message.type === 'system' || message.type === 'status') {
        processedMessage.sender = 'system';
        processedMessage.content = message.content || message.message;
      } else if (message.type === 'error') {
        processedMessage.sender = 'system';
        processedMessage.content = `Error: ${message.content || message.error}`;
        processedMessage.isError = true;
      }

      setMessages(prev => [...prev, processedMessage]);
      setIsTyping(false);
    };

    window.addEventListener('sidhe-message', handleMessage);
    return () => window.removeEventListener('sidhe-message', handleMessage);
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSendMessage = () => {
    if (!inputValue.trim() || !isConnected) return;
    
    // Add user message immediately
    const userMessage = {
      id: Date.now().toString(),
      type: 'user_message',
      sender: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);
    
    // Send to backend
    sendMessage(inputValue.trim());
    setInputValue('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-purple-900 via-slate-900 to-indigo-900 text-white">
      {/* Header */}
      <header className="border-b border-purple-700/30 backdrop-blur-sm bg-purple-900/20">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Gem className="w-8 h-8 text-purple-400" />
                <div className="absolute inset-0 w-8 h-8 text-purple-400 animate-pulse opacity-50">
                  <Gem className="w-8 h-8" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  SIDHE
                </h1>
                <p className="text-sm text-purple-300 opacity-75">Ancient AI Awakened</p>
              </div>
            </div>
            
            <ConnectionStatus status={connectionStatus} isConnected={isConnected} />
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}
        
        {isTyping && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-purple-700/30 bg-slate-900/50 p-4">
        <div className="flex space-x-3">
          <div className="flex-1">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isConnected ? "Ask SIDHE anything... ✨" : "Waiting for SIDHE to awaken..."}
              className="w-full bg-slate-700/50 border border-purple-600/30 rounded-lg px-4 py-3 text-white placeholder-purple-300/70 focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-400/50 resize-none transition-all duration-200"
              rows="1"
              disabled={!isConnected}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!isConnected || !inputValue.trim()}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-slate-600 disabled:to-slate-600 text-white rounded-lg font-medium transition-all duration-200 transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed flex items-center space-x-2 min-w-fit"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
        
        {!isConnected && (
          <div className="mt-3 flex items-center justify-center space-x-2 text-purple-300/70">
            <Loader className="w-4 h-4 animate-spin" />
            <span className="text-sm">
              {connectionStatus === 'connecting' ? 'Awakening the ancient spirits...' :
               'SIDHE slumbers in the digital realm...'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}