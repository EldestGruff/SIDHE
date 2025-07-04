import { useState, useCallback } from 'react';

/**
 * Custom hook for conversation state management
 * 
 * Architecture Decision: Centralized conversation state
 * with support for multiple conversation threads
 */
export const useConversation = () => {
  const [conversations, setConversations] = useState({});
  const [currentConversation, setCurrentConversation] = useState('default');
  
  // Create a new conversation
  const createConversation = useCallback((conversationId = null) => {
    const id = conversationId || Date.now().toString();
    
    setConversations(prev => ({
      ...prev,
      [id]: {
        id,
        messages: [],
        createdAt: new Date().toISOString(),
        lastActivity: new Date().toISOString()
      }
    }));
    
    setCurrentConversation(id);
    return id;
  }, []);
  
  // Add message to conversation
  const addMessage = useCallback((conversationId, message) => {
    setConversations(prev => ({
      ...prev,
      [conversationId]: {
        ...prev[conversationId],
        messages: [...(prev[conversationId]?.messages || []), message],
        lastActivity: new Date().toISOString()
      }
    }));
  }, []);
  
  // Update message in conversation
  const updateMessage = useCallback((conversationId, messageId, updates) => {
    setConversations(prev => ({
      ...prev,
      [conversationId]: {
        ...prev[conversationId],
        messages: prev[conversationId]?.messages.map(msg => 
          msg.id === messageId ? { ...msg, ...updates } : msg
        ) || []
      }
    }));
  }, []);
  
  // Delete message from conversation
  const deleteMessage = useCallback((conversationId, messageId) => {
    setConversations(prev => ({
      ...prev,
      [conversationId]: {
        ...prev[conversationId],
        messages: prev[conversationId]?.messages.filter(msg => msg.id !== messageId) || []
      }
    }));
  }, []);
  
  // Switch to different conversation
  const switchConversation = useCallback((conversationId) => {
    if (conversations[conversationId]) {
      setCurrentConversation(conversationId);
    }
  }, [conversations]);
  
  // Clear conversation
  const clearConversation = useCallback((conversationId) => {
    setConversations(prev => ({
      ...prev,
      [conversationId]: {
        ...prev[conversationId],
        messages: []
      }
    }));
  }, []);
  
  // Delete conversation
  const deleteConversation = useCallback((conversationId) => {
    setConversations(prev => {
      const newConversations = { ...prev };
      delete newConversations[conversationId];
      return newConversations;
    });
    
    // Switch to default conversation if current was deleted
    if (currentConversation === conversationId) {
      setCurrentConversation('default');
    }
  }, [currentConversation]);
  
  // Get conversation summary
  const getConversationSummary = useCallback((conversationId) => {
    const conversation = conversations[conversationId];
    if (!conversation) return null;
    
    return {
      id: conversation.id,
      messageCount: conversation.messages.length,
      lastActivity: conversation.lastActivity,
      createdAt: conversation.createdAt,
      lastMessage: conversation.messages[conversation.messages.length - 1]
    };
  }, [conversations]);
  
  // Initialize default conversation if none exists
  if (!conversations[currentConversation]) {
    createConversation(currentConversation);
  }
  
  return {
    conversations,
    currentConversation,
    createConversation,
    addMessage,
    updateMessage,
    deleteMessage,
    switchConversation,
    clearConversation,
    deleteConversation,
    getConversationSummary
  };
};