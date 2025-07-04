import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for WebSocket connection management
 * 
 * Architecture Decision: Centralized WebSocket state management
 * with automatic reconnection and message handling
 */
export const useWebSocket = (url) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionError, setConnectionError] = useState(null);
  const [messageHistory, setMessageHistory] = useState([]);
  
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;
  
  // Connect to WebSocket
  const connect = useCallback(() => {
    try {
      setConnectionStatus('connecting');
      setConnectionError(null);
      
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setSocket(ws);
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        
        // Send any queued messages
        if (messageHistory.length > 0) {
          messageHistory.forEach(msg => {
            ws.send(JSON.stringify(msg));
          });
          setMessageHistory([]);
        }
      };
      
      ws.onmessage = (event) => {
        setLastMessage(event.data);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('Connection failed');
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket closed:', event);
        setSocket(null);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // Attempt to reconnect if not a clean close
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          setConnectionStatus('reconnecting');
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect... (attempt #${reconnectAttemptsRef.current})`);
            connect();
          }, reconnectDelay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setConnectionError('Max reconnection attempts reached');
        }
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionError('Failed to connect');
    }
  }, [url, messageHistory]);
  
  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (socket) {
      socket.close(1000, 'User disconnected');
    }
    
    setSocket(null);
    setIsConnected(false);
    setConnectionStatus('disconnected');
    reconnectAttemptsRef.current = 0;
  }, [socket]);
  
  // Send message
  const sendMessage = useCallback((message) => {
    if (socket && isConnected) {
      socket.send(message);
    } else {
      // Queue message for when connection is restored
      setMessageHistory(prev => [...prev, JSON.parse(message)]);
      console.log('Message queued for sending when connection is restored');
    }
  }, [socket, isConnected]);
  
  // Initialize connection on mount
  useEffect(() => {
    connect();
    
    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);
  
  // Expose connection methods and state
  return {
    socket,
    isConnected,
    connectionStatus,
    lastMessage,
    connectionError,
    sendMessage,
    connect,
    disconnect,
    queuedMessages: messageHistory.length
  };
};