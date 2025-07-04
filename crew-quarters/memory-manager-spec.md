# Memory Manager Plugin Specification

## Overview
Create a simple Redis-based memory storage plugin for Riker. This plugin will handle storing and retrieving conversation context.

## Implementation Location
Create all files in: `src/plugins/memory_manager/`

## Required Files

### 1. `__init__.py`
Empty file for Python package initialization.

### 2. `plugin_interface.py`
Main plugin interface with the following functions:

```python
from typing import Optional, Dict, Any
import redis
import json
from datetime import datetime, timedelta

class MemoryManager:
    """Manages conversation memory using Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize connection to Redis"""
        # Connect to Redis
        # Handle connection errors gracefully
        pass
    
    def store_memory(self, conversation_id: str, memory_data: Dict[str, Any]) -> bool:
        """
        Store conversation memory with 24-hour expiration
        
        Args:
            conversation_id: Unique identifier for the conversation
            memory_data: Dictionary containing conversation context
            
        Returns:
            bool: True if stored successfully
        """
        # Store as JSON in Redis
        # Set expiration to 24 hours
        # Return success/failure
        pass
    
    def retrieve_memory(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve conversation memory
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Dictionary with memory data or None if not found
        """
        # Get from Redis
        # Parse JSON
        # Handle not found case
        pass
    
    def extend_memory_ttl(self, conversation_id: str, hours: int = 24) -> bool:
        """
        Extend the expiration time of a conversation
        
        Args:
            conversation_id: Unique identifier for the conversation
            hours: Number of hours to extend
            
        Returns:
            bool: True if extended successfully
        """
        # Check if key exists
        # Extend TTL
        # Return success/failure
        pass
    
    def clear_memory(self, conversation_id: str) -> bool:
        """
        Clear a specific conversation from memory
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            bool: True if cleared successfully
        """
        # Delete from Redis
        # Return success/failure
        pass
```

### 3. `test_memory_manager.py`
Basic test file:

```python
import pytest
from .plugin_interface import MemoryManager

def test_store_and_retrieve():
    """Test basic store and retrieve functionality"""
    # Create manager instance
    # Store test data
    # Retrieve and verify
    # Clean up
    pass

def test_memory_expiration():
    """Test that TTL extension works"""
    # Store data
    # Extend TTL
    # Verify extension worked
    pass

def test_clear_memory():
    """Test memory clearing"""
    # Store data
    # Clear it
    # Verify it's gone
    pass
```

## Implementation Requirements

1. **Error Handling**: All Redis operations should handle connection failures gracefully
2. **JSON Serialization**: Use json.dumps/loads for data serialization
3. **Type Hints**: Include proper type hints for all methods
4. **Docstrings**: Add clear docstrings explaining each method
5. **Redis Keys**: Use the pattern `riker:memory:{conversation_id}` for Redis keys
6. **Logging**: Add basic logging for debugging (use Python's logging module)

## Success Criteria

- [ ] All three files created in correct location
- [ ] MemoryManager class implements all specified methods
- [ ] Proper error handling for Redis connection issues
- [ ] Tests are runnable (even if Redis isn't available, they should fail gracefully)
- [ ] Code follows Python conventions (PEP 8)
- [ ] All methods have docstrings and type hints

## Dependencies

```txt
redis==5.0.1
pytest==7.4.3
```

## Example Usage

```python
# Initialize the manager
manager = MemoryManager("redis://localhost:6379")

# Store conversation context
context = {
    "user_request": "Build an auth system",
    "current_task": "Design database schema",
    "completed_steps": ["research_providers", "select_oauth2"],
    "timestamp": "2025-07-02T10:30:00"
}

success = manager.store_memory("conv-12345", context)

# Later, retrieve it
memory = manager.retrieve_memory("conv-12345")
if memory:
    print(f"Resuming from: {memory['current_task']}")
```

## Notes
- This is a minimal implementation for testing purposes
- In production, we'd add connection pooling, retries, and more robust error handling
- The 24-hour expiration is arbitrary and could be configurable later
