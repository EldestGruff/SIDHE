from typing import Optional, Dict, Any
import json
import logging
from datetime import datetime, timedelta

# Import PDK classes
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.pdk.sidhe_pdk import EnchantedPlugin, PluginCapability, PluginMessage

logger = logging.getLogger(__name__)


class MemoryManager(EnchantedPlugin):
    """Manages conversation memory using Redis"""
    
    def __init__(self):
        """Initialize the Memory Manager plugin"""
        super().__init__(
            plugin_id="tome_keeper",
            plugin_name="Memory Crystal Manager",
            version="2.0.0"
        )
        
        # Register capabilities
        self.register_capability(PluginCapability(
            name="store_memory",
            description="Store conversation memory with 24hr TTL",
            parameters={"conversation_id": "string", "memory_data": "dict"},
            returns={"success": "boolean"}
        ))
        
        self.register_capability(PluginCapability(
            name="retrieve_memory",
            description="Retrieve conversation memory",
            parameters={"conversation_id": "string"},
            returns={"memory_data": "dict", "found": "boolean"}
        ))
        
        self.register_capability(PluginCapability(
            name="extend_memory_ttl",
            description="Extend memory expiration time",
            parameters={"conversation_id": "string", "hours": "integer"},
            returns={"success": "boolean"}
        ))
        
        self.register_capability(PluginCapability(
            name="clear_memory",
            description="Clear conversation memory",
            parameters={"conversation_id": "string"},
            returns={"success": "boolean"}
        ))
    
    async def handle_request(self, message: PluginMessage) -> Dict[str, Any]:
        """Handle memory-related requests"""
        action = message.payload.get("action")
        
        if action == "store_memory":
            return await self._store_memory(
                message.payload.get("conversation_id"),
                message.payload.get("memory_data")
            )
        elif action == "retrieve_memory":
            return await self._retrieve_memory(
                message.payload.get("conversation_id")
            )
        elif action == "extend_memory_ttl":
            return await self._extend_memory_ttl(
                message.payload.get("conversation_id"),
                message.payload.get("hours", 24)
            )
        elif action == "clear_memory":
            return await self._clear_memory(
                message.payload.get("conversation_id")
            )
        elif action == "test":
            # Handle test requests for certification
            return {
                "status": "success",
                "message": "Plugin is functioning correctly",
                "data": message.payload.get("data", "test_response")
            }
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _store_memory(self, conversation_id: str, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store conversation memory with 24-hour expiration
        
        Args:
            conversation_id: Unique identifier for the conversation
            memory_data: Dictionary containing conversation context
            
        Returns:
            Dict containing success status
        """
        if not conversation_id:
            raise ValueError("conversation_id is required")
        if not memory_data:
            raise ValueError("memory_data is required")
            
        try:
            key = f"sidhe:memory:{conversation_id}"
            serialized_data = json.dumps(memory_data)
            
            # Store with 24-hour expiration
            success = await self.redis_client.setex(
                key, 
                timedelta(hours=24), 
                serialized_data
            )
            
            if success:
                self.logger.info(f"💾 Stored memory for conversation {conversation_id}")
                return {"success": True}
            else:
                self.logger.error(f"❌ Failed to store memory for conversation {conversation_id}")
                return {"success": False, "error": "Failed to store memory"}
                
        except json.JSONEncodeError as e:
            self.logger.error(f"❌ Failed to serialize memory data: {e}")
            return {"success": False, "error": f"Serialization error: {str(e)}"}
        except Exception as e:
            self.logger.error(f"❌ Unexpected error storing memory: {e}")
            return {"success": False, "error": f"Storage error: {str(e)}"}
    
    async def _retrieve_memory(self, conversation_id: str) -> Dict[str, Any]:
        """
        Retrieve conversation memory
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Dictionary with memory data and found status
        """
        if not conversation_id:
            raise ValueError("conversation_id is required")
            
        try:
            key = f"sidhe:memory:{conversation_id}"
            serialized_data = await self.redis_client.get(key)
            
            if serialized_data is None:
                self.logger.info(f"🔍 No memory found for conversation {conversation_id}")
                return {"found": False, "memory_data": None}
                
            memory_data = json.loads(serialized_data)
            self.logger.info(f"💎 Retrieved memory for conversation {conversation_id}")
            return {"found": True, "memory_data": memory_data}
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Failed to deserialize memory data: {e}")
            return {"found": False, "memory_data": None, "error": f"Deserialization error: {str(e)}"}
        except Exception as e:
            self.logger.error(f"❌ Unexpected error retrieving memory: {e}")
            return {"found": False, "memory_data": None, "error": f"Retrieval error: {str(e)}"}
    
    async def _extend_memory_ttl(self, conversation_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Extend the expiration time of a conversation
        
        Args:
            conversation_id: Unique identifier for the conversation
            hours: Number of hours to extend
            
        Returns:
            Dict containing success status
        """
        if not conversation_id:
            raise ValueError("conversation_id is required")
        if not isinstance(hours, int) or hours <= 0:
            raise ValueError("hours must be a positive integer")
            
        try:
            key = f"sidhe:memory:{conversation_id}"
            
            # Check if key exists
            exists = await self.redis_client.exists(key)
            if not exists:
                self.logger.warning(f"⚠️ Cannot extend TTL: conversation {conversation_id} not found")
                return {"success": False, "error": "Conversation not found"}
                
            # Extend TTL
            success = await self.redis_client.expire(key, timedelta(hours=hours))
            
            if success:
                self.logger.info(f"⏰ Extended TTL for conversation {conversation_id} by {hours} hours")
                return {"success": True}
            else:
                self.logger.error(f"❌ Failed to extend TTL for conversation {conversation_id}")
                return {"success": False, "error": "Failed to extend TTL"}
                
        except Exception as e:
            self.logger.error(f"❌ Unexpected error extending TTL: {e}")
            return {"success": False, "error": f"TTL extension error: {str(e)}"}
    
    async def _clear_memory(self, conversation_id: str) -> Dict[str, Any]:
        """
        Clear a specific conversation from memory
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Dict containing success status
        """
        if not conversation_id:
            raise ValueError("conversation_id is required")
            
        try:
            key = f"sidhe:memory:{conversation_id}"
            deleted_count = await self.redis_client.delete(key)
            
            if deleted_count > 0:
                self.logger.info(f"🧹 Cleared memory for conversation {conversation_id}")
                return {"success": True}
            else:
                self.logger.warning(f"⚠️ No memory found to clear for conversation {conversation_id}")
                return {"success": False, "error": "No memory found to clear"}
                
        except Exception as e:
            self.logger.error(f"❌ Unexpected error clearing memory: {e}")
            return {"success": False, "error": f"Clear memory error: {str(e)}"}