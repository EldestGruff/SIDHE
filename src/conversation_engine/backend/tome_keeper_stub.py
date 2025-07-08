"""
Stub replacement for memory manager to eliminate Redis connection errors
"""
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    """Stub MemoryManager that does nothing to avoid Redis errors"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize stub - no Redis connection"""
        logger.info("Using stub MemoryManager (no Redis)")
        self.redis_client = None
    
    def store_memory(self, conversation_id: str, memory_data: dict) -> bool:
        """Stub store - always returns True"""
        return True
    
    def get_memory(self, conversation_id: str) -> dict:
        """Stub get - always returns empty"""
        return {}