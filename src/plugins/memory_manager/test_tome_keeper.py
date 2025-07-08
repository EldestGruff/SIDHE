import pytest
import json
from unittest.mock import Mock, patch
from .plugin_interface import MemoryManager


def test_store_and_retrieve():
    """Test basic store and retrieve functionality"""
    # Mock Redis client
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.setex.return_value = True
    mock_redis.get.return_value = json.dumps({"test": "data"})
    
    with patch('redis.from_url', return_value=mock_redis):
        manager = MemoryManager()
        
        # Test store
        test_data = {"user_request": "test", "current_task": "testing"}
        result = manager.store_memory("test-conv-1", test_data)
        assert result is True
        
        # Test retrieve
        retrieved_data = manager.retrieve_memory("test-conv-1")
        assert retrieved_data == {"test": "data"}
        
        # Verify Redis calls
        mock_redis.setex.assert_called_once()
        mock_redis.get.assert_called_once_with("sidhe:memory:test-conv-1")


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