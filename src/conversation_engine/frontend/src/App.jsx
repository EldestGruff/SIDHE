import React, { useState, useEffect } from 'react';
import './App.css';

// Components
import ChatInterface from './components/Chat/ChatInterface';
import Dashboard from './components/Dashboard/Dashboard';

// Custom hooks
import { useWebSocket } from './hooks/useWebSocket';
import { useConversation } from './hooks/useConversation';

/**
 * Main Riker Conversation Engine Frontend
 * 
 * Architecture Decision: Single-page application with real-time WebSocket communication
 * integrating with the FastAPI backend for conversational AI interactions.
 */
function App() {
  const [currentView, setCurrentView] = useState('chat');
  const [systemHealth, setSystemHealth] = useState({});
  
  // WebSocket connection management
  const { 
    isConnected, 
    connectionStatus, 
    sendMessage, 
    lastMessage,
    connectionError 
  } = useWebSocket(`ws://${window.location.host}/ws`);
  
  // Conversation state management
  const {
    conversations,
    currentConversation,
    addMessage,
    createConversation,
    switchConversation
  } = useConversation();
  
  // Handle incoming messages from backend
  useEffect(() => {
    if (lastMessage) {
      try {
        const messageData = JSON.parse(lastMessage);
        
        if (messageData.type === 'connection_established') {
          console.log('Connection established with backend');
        } else if (messageData.type === 'response' || messageData.type.endsWith('_response') || messageData.type === 'answer') {
          // Add assistant response to conversation
          addMessage(currentConversation, {
            id: Date.now(),
            type: 'assistant',
            content: messageData.content,
            timestamp: new Date().toISOString(),
            intent: messageData.intent
          });
        } else if (messageData.type === 'system_update') {
          setSystemHealth(messageData.data);
        }
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    }
  }, [lastMessage, currentConversation, addMessage]);
  
  // Handle sending messages to backend
  const handleSendMessage = (message) => {
    if (isConnected && message.trim()) {
      // Add user message to conversation
      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: message,
        timestamp: new Date().toISOString()
      };
      
      addMessage(currentConversation, userMessage);
      
      // Send to backend
      sendMessage(JSON.stringify({
        content: message,
        conversation_id: currentConversation,
        timestamp: new Date().toISOString()
      }));
    }
  };
  
  const getConnectionStatusClass = () => {
    return isConnected ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200';
  };
  
  const getConnectionStatusText = () => {
    return isConnected ? '🟢 Connected' : '🔴 Disconnected';
  };
  
  const getViewButtonClass = (view) => {
    return currentView === view 
      ? 'bg-blue-600 text-white' 
      : 'bg-gray-700 text-gray-300 hover:bg-gray-600';
  };
  
  return (
    <div className="App min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-blue-400">
              🚀 Riker Conversation Engine
            </h1>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getConnectionStatusClass()}`}>
              {getConnectionStatusText()}
            </span>
          </div>
          
          <nav className="flex space-x-4">
            <button 
              onClick={() => setCurrentView('chat')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${getViewButtonClass('chat')}`}
            >
              Chat
            </button>
            <button 
              onClick={() => setCurrentView('dashboard')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${getViewButtonClass('dashboard')}`}
            >
              Dashboard
            </button>
          </nav>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="flex-1">
        {connectionError && (
          <div className="bg-red-900 text-red-200 px-6 py-3 border-b border-red-800">
            <p className="font-medium">Connection Error:</p>
            <p className="text-sm">{connectionError}</p>
          </div>
        )}
        
        {currentView === 'chat' ? (
          <ChatInterface 
            conversation={conversations[currentConversation] || { messages: [] }}
            onSendMessage={handleSendMessage}
            isConnected={isConnected}
            connectionStatus={connectionStatus}
          />
        ) : (
          <Dashboard 
            systemHealth={systemHealth}
            conversations={conversations}
            isConnected={isConnected}
          />
        )}
      </main>
    </div>
  );
}

export default App;