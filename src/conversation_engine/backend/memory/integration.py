"""
Memory Integration - Integration with existing Memory Manager plugin
Handles conversation storage, context building, and memory retrieval
"""
import logging
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Memory Manager completely disabled for core conversation functionality
MemoryManager = None

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Integration with Memory Manager plugin for conversation storage and retrieval"""
    
    def __init__(self):
        """Initialize Memory Manager plugin integration"""
        # Memory Manager temporarily disabled - conversation will work without persistent memory
        logger.info("ConversationMemory initialized without Memory Manager (temporarily disabled)")
        self.memory_manager = None
    
    async def store_turn(self, conversation_id: str, turn_data: Dict[str, Any]) -> bool:
        """
        Store conversation turn with context
        
        Args:
            conversation_id: Unique conversation identifier
            turn_data: Turn data including user input and intent
            
        Returns:
            bool: True if stored successfully
        """
        try:
            if not self.memory_manager:
                logger.debug("Memory Manager not available, skipping turn storage")
                return True  # Return True to not block conversation flow
            
            # Generate turn ID
            turn_id = str(uuid.uuid4())
            
            # Prepare memory data with conversation structure
            memory_data = {
                "type": "conversation_turn",
                "conversation_id": conversation_id,
                "turn_id": turn_id,
                "timestamp": datetime.now().isoformat(),
                "user_input": turn_data.get("user_input", ""),
                "intent": turn_data.get("intent", {}),
                "system_response": turn_data.get("system_response"),
                "metadata": {
                    "session_id": turn_data.get("session_id"),
                    "user_id": turn_data.get("user_id"),
                    "processing_time": turn_data.get("processing_time")
                }
            }
            
            # Store in Memory Manager with conversation-specific key
            memory_key = f"conversation:{conversation_id}:turn:{turn_id}"
            success = self.memory_manager.store_memory(memory_key, memory_data)
            
            if success:
                logger.info(f"Stored conversation turn {turn_id} for conversation {conversation_id}")
                
                # Also update conversation metadata
                await self._update_conversation_metadata(conversation_id, turn_data)
                
            return success
            
        except Exception as e:
            logger.error(f"Error storing conversation turn: {e}")
            return False
    
    async def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history
        
        Args:
            conversation_id: Conversation to retrieve
            limit: Maximum number of turns to retrieve
            
        Returns:
            List of conversation turns
        """
        try:
            if not self.memory_manager:
                logger.warning("Memory Manager not available")
                return []
            
            # Get conversation metadata to find turn keys
            metadata_key = f"conversation:{conversation_id}:metadata"
            metadata = self.memory_manager.get_memory(metadata_key)
            
            if not metadata:
                logger.info(f"No conversation history found for {conversation_id}")
                return []
            
            # Get recent turns (simplified - in production would query by pattern)
            turns = []
            turn_ids = metadata.get("turn_ids", [])[-limit:]  # Get last N turns
            
            for turn_id in turn_ids:
                turn_key = f"conversation:{conversation_id}:turn:{turn_id}"
                turn_data = self.memory_manager.get_memory(turn_key)
                if turn_data:
                    turns.append(turn_data)
            
            logger.info(f"Retrieved {len(turns)} turns for conversation {conversation_id}")
            return turns
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    async def build_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Build conversation context for intent parsing
        
        Args:
            conversation_id: Conversation to build context for
            
        Returns:
            Context dictionary with recent history and metadata
        """
        try:
            # Get recent conversation history
            recent_turns = await self.get_conversation_history(conversation_id, limit=5)
            
            # Build context summary
            context = {
                "conversation_id": conversation_id,
                "recent_turns": recent_turns,
                "turn_count": len(recent_turns),
                "last_activity": recent_turns[-1]["timestamp"] if recent_turns else None,
                "topics": self._extract_topics(recent_turns),
                "active_intents": self._extract_recent_intents(recent_turns)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error building context: {e}")
            return {"conversation_id": conversation_id, "error": str(e)}
    
    async def _update_conversation_metadata(self, conversation_id: str, turn_data: Dict[str, Any]) -> bool:
        """Update conversation metadata with new turn information"""
        try:
            metadata_key = f"conversation:{conversation_id}:metadata"
            
            # Get existing metadata or create new
            metadata = self.memory_manager.get_memory(metadata_key) or {
                "conversation_id": conversation_id,
                "created_at": datetime.now().isoformat(),
                "turn_ids": [],
                "total_turns": 0,
                "last_activity": None
            }
            
            # Update metadata
            if "turn_id" in turn_data:
                metadata["turn_ids"].append(turn_data["turn_id"])
            
            metadata["total_turns"] += 1
            metadata["last_activity"] = datetime.now().isoformat()
            metadata["last_intent"] = turn_data.get("intent", {}).get("type")
            
            # Store updated metadata
            return self.memory_manager.store_memory(metadata_key, metadata)
            
        except Exception as e:
            logger.error(f"Error updating conversation metadata: {e}")
            return False
    
    def _extract_topics(self, turns: List[Dict[str, Any]]) -> List[str]:
        """Extract topics from conversation turns"""
        topics = set()
        
        for turn in turns:
            intent = turn.get("intent", {})
            if isinstance(intent, dict):
                # Extract entities as topics
                entities = intent.get("entities", {})
                for key, value in entities.items():
                    if isinstance(value, str):
                        topics.add(value)
                
                # Add intent type as topic
                intent_type = intent.get("type")
                if intent_type:
                    topics.add(intent_type)
        
        return list(topics)
    
    def _extract_recent_intents(self, turns: List[Dict[str, Any]]) -> List[str]:
        """Extract recent intent types from conversation"""
        intents = []
        
        for turn in turns:
            intent = turn.get("intent", {})
            if isinstance(intent, dict):
                intent_type = intent.get("type")
                if intent_type and intent_type not in intents:
                    intents.append(intent_type)
        
        return intents
    
    async def health_check(self) -> str:
        """Health check for memory integration"""
        return "disabled"
