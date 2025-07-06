import { useState, useEffect, useRef } from 'react';

/**
 * Simple WebSocket hook without auto-reconnection
 */
export const useWebSocket = (url) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionError, setConnectionError] = useState(null);
  
  const wsRef = useRef(null);
  const mountedRef = useRef(true);
  
  useEffect(() => {
    mountedRef.current = true;
    
    // Only connect once on mount
    if (!wsRef.current) {
      connectWebSocket();
    }
    
    // Cleanup on unmount
    return () => {
      mountedRef.current = false;
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []); // Empty dependency array - only run once
  
  const connectWebSocket = () => {
    try {
      setConnectionStatus('connecting');
      setConnectionError(null);
      
      const ws = new WebSocket(url);
      wsRef.current = ws;
      
      ws.onopen = () => {
        if (!mountedRef.current) return;
        
        console.log('WebSocket connected');
        setSocket(ws);
        setIsConnected(true);
        setConnectionStatus('connected');
      };
      
      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        
        setLastMessage(event.data);
      };
      
      ws.onerror = (error) => {
        if (!mountedRef.current) return;
        
        console.error('WebSocket error:', error);
        setConnectionError('Connection failed');
      };
      
      ws.onclose = (event) => {
        if (!mountedRef.current) return;
        
        console.log('WebSocket closed:', event.code, event.reason);
        setSocket(null);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        wsRef.current = null;
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionError('Failed to connect');
    }
  };
  
  const sendMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  };
  
  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };
  
  return {
    socket,
    isConnected,
    connectionStatus,
    lastMessage,
    connectionError,
    sendMessage,
    connect: connectWebSocket,
    disconnect,
    queuedMessages: 0
  };
};