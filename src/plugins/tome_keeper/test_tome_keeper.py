import pytest
import json
import asyncio
from unittest.mock import Mock, patch
from .plugin_interface import MemoryManager

# Import PDK test utilities
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.pdk.sidhe_pdk import PluginMessage, MessageType
from core.pdk.sidhe_pdk_test_utilities import mock_plugin


@pytest.fixture
def plugin():
    """Create a mock plugin for testing"""
    with mock_plugin(MemoryManager) as mock_manager:
        yield mock_manager


@pytest.mark.asyncio
async def test_store_and_retrieve(plugin):
    """Test basic store and retrieve functionality via PDK interface"""
    # Test store memory
    store_message = PluginMessage(
        type=MessageType.REQUEST,
        source="test_client",
        target="tome_keeper",
        payload={
            "action": "store_memory",
            "conversation_id": "test-conv-1",
            "memory_data": {"user_request": "test", "current_task": "testing"}
        }
    )
    
    store_result = await plugin.handle_request(store_message)
    assert store_result["success"] is True
    
    # Test retrieve memory
    retrieve_message = PluginMessage(
        type=MessageType.REQUEST,
        source="test_client",
        target="tome_keeper",
        payload={
            "action": "retrieve_memory",
            "conversation_id": "test-conv-1"
        }
    )
    
    retrieve_result = await plugin.handle_request(retrieve_message)
    assert retrieve_result["found"] is True
    assert retrieve_result["memory_data"] is not None


def test_memory_expiration():
    """Test that TTL extension works"""
    # Mock Redis client
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.exists.return_value = True
    mock_redis.expire.return_value = True
    
    with patch('redis.from_url', return_value=mock_redis):
        manager = MemoryManager()
        
        # Test TTL extension
        result = manager.extend_memory_ttl("test-conv-1", 48)
        assert result is True
        
        # Verify Redis calls
        mock_redis.exists.assert_called_once_with("sidhe:memory:test-conv-1")
        mock_redis.expire.assert_called_once()


def test_clear_memory():
    """Test memory clearing"""
    # Mock Redis client
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.delete.return_value = 1  # 1 key deleted
    
    with patch('redis.from_url', return_value=mock_redis):
        manager = MemoryManager()
        
        # Test clear
        result = manager.clear_memory("test-conv-1")
        assert result is True
        
        # Verify Redis calls
        mock_redis.delete.assert_called_once_with("sidhe:memory:test-conv-1")


def test_redis_connection_failure():
    """Test handling of Redis connection failures"""
    with patch('redis.from_url', side_effect=Exception("Connection failed")):
        manager = MemoryManager()
        
        # All operations should fail gracefully
        assert manager.store_memory("test", {"data": "test"}) is False
        assert manager.retrieve_memory("test") is None
        assert manager.extend_memory_ttl("test") is False
        assert manager.clear_memory("test") is False


def test_json_serialization_error():
    """Test handling of JSON serialization errors"""
    # Mock Redis client
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    
    with patch('redis.from_url', return_value=mock_redis):
        manager = MemoryManager()
        
        # Test with non-serializable data
        non_serializable = {"function": lambda x: x}
        result = manager.store_memory("test", non_serializable)
        assert result is False


def test_retrieve_nonexistent_memory():
    """Test retrieving memory that doesn't exist"""
    # Mock Redis client
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    
    with patch('redis.from_url', return_value=mock_redis):
        manager = MemoryManager()
        
        result = manager.retrieve_memory("nonexistent-conv")
        assert result is None


def test_extend_ttl_nonexistent_key():
    """Test extending TTL for non-existent key"""
    # Mock Redis client
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.exists.return_value = False
    
    with patch('redis.from_url', return_value=mock_redis):
        manager = MemoryManager()
        
        result = manager.extend_memory_ttl("nonexistent-conv")
        assert result is False


def test_clear_nonexistent_memory():
    """Test clearing non-existent memory"""
    # Mock Redis client
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.delete.return_value = 0  # 0 keys deleted
    
    with patch('redis.from_url', return_value=mock_redis):
        manager = MemoryManager()
        
        result = manager.clear_memory("nonexistent-conv")
        assert result is False