from typing import Optional, Dict, Any
import redis
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages conversation memory using Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize connection to Redis"""
        import traceback
        logger.info(f"MemoryManager.__init__ called with redis_url={redis_url}")
        logger.info(f"Call stack: {traceback.format_stack()[-3:-1]}")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self.redis_client = None
    
    def store_memory(self, conversation_id: str, memory_data: Dict[str, Any]) -> bool:
        """
        Store conversation memory with 24-hour expiration
        
        Args:
            conversation_id: Unique identifier for the conversation
            memory_data: Dictionary containing conversation context
            
        Returns:
            bool: True if stored successfully
        """
        if not self.redis_client:
            logger.error("Redis client not available")
            return False
            
        try:
            key = f"riker:memory:{conversation_id}"
            serialized_data = json.dumps(memory_data)
            
            # Store with 24-hour expiration
            success = self.redis_client.setex(
                key, 
                timedelta(hours=24), 
                serialized_data
            )
            
            if success:
                logger.info(f"Stored memory for conversation {conversation_id}")
                return True
            else:
                logger.error(f"Failed to store memory for conversation {conversation_id}")
                return False
                
        except json.JSONEncodeError as e:
            logger.error(f"Failed to serialize memory data: {e}")
            return False
        except redis.RedisError as e:
            logger.error(f"Redis error while storing memory: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing memory: {e}")
            return False
    
    def retrieve_memory(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve conversation memory
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Dictionary with memory data or None if not found
        """
        if not self.redis_client:
            logger.error("Redis client not available")
            return None
            
        try:
            key = f"riker:memory:{conversation_id}"
            serialized_data = self.redis_client.get(key)
            
            if serialized_data is None:
                logger.info(f"No memory found for conversation {conversation_id}")
                return None
                
            memory_data = json.loads(serialized_data)
            logger.info(f"Retrieved memory for conversation {conversation_id}")
            return memory_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize memory data: {e}")
            return None
        except redis.RedisError as e:
            logger.error(f"Redis error while retrieving memory: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving memory: {e}")
            return None
    
    def extend_memory_ttl(self, conversation_id: str, hours: int = 24) -> bool:
        """
        Extend the expiration time of a conversation
        
        Args:
            conversation_id: Unique identifier for the conversation
            hours: Number of hours to extend
            
        Returns:
            bool: True if extended successfully
        """
        if not self.redis_client:
            logger.error("Redis client not available")
            return False
            
        try:
            key = f"riker:memory:{conversation_id}"
            
            # Check if key exists
            if not self.redis_client.exists(key):
                logger.warning(f"Cannot extend TTL: conversation {conversation_id} not found")
                return False
                
            # Extend TTL
            success = self.redis_client.expire(key, timedelta(hours=hours))
            
            if success:
                logger.info(f"Extended TTL for conversation {conversation_id} by {hours} hours")
                return True
            else:
                logger.error(f"Failed to extend TTL for conversation {conversation_id}")
                return False
                
        except redis.RedisError as e:
            logger.error(f"Redis error while extending TTL: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error extending TTL: {e}")
            return False
    
    def clear_memory(self, conversation_id: str) -> bool:
        """
        Clear a specific conversation from memory
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            bool: True if cleared successfully
        """
        if not self.redis_client:
            logger.error("Redis client not available")
            return False
            
        try:
            key = f"riker:memory:{conversation_id}"
            deleted_count = self.redis_client.delete(key)
            
            if deleted_count > 0:
                logger.info(f"Cleared memory for conversation {conversation_id}")
                return True
            else:
                logger.warning(f"No memory found to clear for conversation {conversation_id}")
                return False
                
        except redis.RedisError as e:
            logger.error(f"Redis error while clearing memory: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error clearing memory: {e}")
            return False