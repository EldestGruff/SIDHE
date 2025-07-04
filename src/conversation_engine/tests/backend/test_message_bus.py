"""
Test suite for Message Bus
Tests Redis pub/sub functionality and plugin communication
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import redis.asyncio as redis

from bus.publisher import MessageBus

class TestMessageBus:
    """Test message bus functionality"""
    
    @pytest.fixture
    def message_bus(self):
        """Create message bus instance"""
        return MessageBus()
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client"""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        mock_client.publish = AsyncMock()
        mock_client.pubsub = MagicMock()
        return mock_client
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, message_bus, mock_redis_client):
        """Test successful message bus initialization"""
        with patch('redis.asyncio.from_url', return_value=mock_redis_client):
            await message_bus.initialize()
            
            assert message_bus.redis_client == mock_redis_client
            assert message_bus.pubsub is not None
            mock_redis_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, message_bus):
        """Test message bus initialization failure"""
        with patch('redis.asyncio.from_url', side_effect=redis.ConnectionError("Connection failed")):
            with pytest.raises(redis.ConnectionError):
                await message_bus.initialize()
    
    @pytest.mark.asyncio
    async def test_publish_message(self, message_bus, mock_redis_client):
        """Test message publishing"""
        message_bus.redis_client = mock_redis_client
        
        test_message = {
            "type": "test_message",
            "content": "Hello World",
            "data": {"key": "value"}
        }
        
        await message_bus.publish("test_topic", test_message)
        
        # Verify publish was called
        mock_redis_client.publish.assert_called_once()
        call_args = mock_redis_client.publish.call_args
        
        assert call_args[0][0] == "test_topic"
        
        # Parse the published message
        published_message = json.loads(call_args[0][1])
        assert published_message["type"] == "test_message"
        assert published_message["content"] == "Hello World"
        assert published_message["data"] == {"key": "value"}
        assert "timestamp" in published_message
        assert published_message["source"] == "conversation_engine"
    
    @pytest.mark.asyncio
    async def test_publish_without_redis(self, message_bus):
        """Test publishing when Redis is not initialized"""
        message_bus.redis_client = None
        
        test_message = {"type": "test"}
        await message_bus.publish("test_topic", test_message)
        
        # Should not raise exception, but should log error
        # In a real implementation, we'd capture logs to verify
    
    @pytest.mark.asyncio
    async def test_request_response_success(self, message_bus, mock_redis_client):
        """Test successful request/response pattern"""
        message_bus.redis_client = mock_redis_client
        
        # Mock pubsub
        mock_pubsub = AsyncMock()
        mock_redis_client.pubsub.return_value = mock_pubsub
        message_bus.pubsub = mock_pubsub
        
        # Mock the response
        test_response = {
            "message_id": "test_id",
            "status": "success",
            "data": {"result": "test_result"}
        }
        
        # Create a future that will be resolved with the response
        response_future = asyncio.Future()
        response_future.set_result(test_response)
        
        # Mock the pending requests tracking
        with patch.object(message_bus, 'pending_requests', {"test_id": response_future}):
            # Mock message ID generation
            with patch('uuid.uuid4', return_value=MagicMock(hex="test_id")):
                result = await message_bus.request_response(
                    "test_plugin", 
                    "test_action", 
                    {"param": "value"},
                    timeout=1
                )
        
        assert result == test_response
        
        # Verify subscription and publishing
        mock_pubsub.subscribe.assert_called_once()
        mock_redis_client.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_request_response_timeout(self, message_bus, mock_redis_client):
        """Test request/response timeout"""
        message_bus.redis_client = mock_redis_client
        
        # Mock pubsub
        mock_pubsub = AsyncMock()
        mock_redis_client.pubsub.return_value = mock_pubsub
        message_bus.pubsub = mock_pubsub
        
        # Mock the pending requests with a future that never resolves
        response_future = asyncio.Future()
        
        with patch.object(message_bus, 'pending_requests', {"test_id": response_future}):
            with patch('uuid.uuid4', return_value=MagicMock(hex="test_id")):
                result = await message_bus.request_response(
                    "test_plugin", 
                    "test_action", 
                    {"param": "value"},
                    timeout=0.1  # Very short timeout
                )
        
        assert result["status"] == "timeout"
        assert "did not respond" in result["error"]
        assert result["message_id"] == "test_id"
    
    @pytest.mark.asyncio
    async def test_request_response_no_redis(self, message_bus):
        """Test request/response when Redis is not initialized"""
        message_bus.redis_client = None
        
        result = await message_bus.request_response(
            "test_plugin", 
            "test_action", 
            {"param": "value"}
        )
        
        assert result["status"] == "error"
        assert "not initialized" in result["error"]
    
    @pytest.mark.asyncio
    async def test_response_listener(self, message_bus, mock_redis_client):
        """Test response listener functionality"""
        message_bus.redis_client = mock_redis_client
        
        # Mock pubsub with message stream
        mock_pubsub = AsyncMock()
        
        # Create mock messages
        mock_messages = [
            {"type": "message", "data": json.dumps({"message_id": "test_1", "status": "success"})},
            {"type": "message", "data": json.dumps({"message_id": "test_2", "status": "error"})},
            {"type": "subscribe", "data": "1"}  # Non-message type
        ]
        
        async def mock_listen():
            for msg in mock_messages:
                yield msg
        
        mock_pubsub.listen = mock_listen
        message_bus.pubsub = mock_pubsub
        
        # Mock pending requests
        future_1 = asyncio.Future()
        future_2 = asyncio.Future()
        message_bus.pending_requests = {
            "test_1": future_1,
            "test_2": future_2
        }
        
        # Start the listener (it will process the mock messages)
        listener_task = asyncio.create_task(message_bus._listen_for_responses())
        
        # Wait a bit for processing
        await asyncio.sleep(0.1)
        listener_task.cancel()
        
        # Verify futures were resolved
        assert future_1.done()
        assert future_2.done()
        assert future_1.result()["message_id"] == "test_1"
        assert future_2.result()["message_id"] == "test_2"
    
    @pytest.mark.asyncio
    async def test_publish_event(self, message_bus, mock_redis_client):
        """Test event publishing"""
        message_bus.redis_client = mock_redis_client
        
        event_data = {
            "mission_id": "123",
            "status": "created",
            "assignee": "Claude"
        }
        
        await message_bus.publish_event("mission_created", event_data)
        
        # Verify publish was called
        mock_redis_client.publish.assert_called_once()
        call_args = mock_redis_client.publish.call_args
        
        assert call_args[0][0] == "system:events"
        
        # Parse the published event
        published_event = json.loads(call_args[0][1])
        assert published_event["event_type"] == "mission_created"
        assert published_event["data"] == event_data
        assert "timestamp" in published_event
        assert published_event["source"] == "conversation_engine"
    
    @pytest.mark.asyncio
    async def test_health_check_operational(self, message_bus, mock_redis_client):
        """Test health check when operational"""
        message_bus.redis_client = mock_redis_client
        
        health_status = await message_bus.health_check()
        
        assert health_status == "operational"
        mock_redis_client.ping.assert_called_once()
        mock_redis_client.publish.assert_called_once()  # Health test publish
    
    @pytest.mark.asyncio
    async def test_health_check_disconnected(self, message_bus):
        """Test health check when disconnected"""
        message_bus.redis_client = None
        
        health_status = await message_bus.health_check()
        
        assert health_status == "disconnected"
    
    @pytest.mark.asyncio
    async def test_health_check_connection_error(self, message_bus, mock_redis_client):
        """Test health check with connection error"""
        message_bus.redis_client = mock_redis_client
        mock_redis_client.ping.side_effect = redis.ConnectionError("Connection failed")
        
        health_status = await message_bus.health_check()
        
        assert health_status == "connection_error"
    
    @pytest.mark.asyncio
    async def test_health_check_general_error(self, message_bus, mock_redis_client):
        """Test health check with general error"""
        message_bus.redis_client = mock_redis_client
        mock_redis_client.ping.side_effect = Exception("General error")
        
        health_status = await message_bus.health_check()
        
        assert health_status == "error"
    
    @pytest.mark.asyncio
    async def test_close(self, message_bus, mock_redis_client):
        """Test clean shutdown"""
        mock_pubsub = AsyncMock()
        message_bus.redis_client = mock_redis_client
        message_bus.pubsub = mock_pubsub
        
        await message_bus.close()
        
        mock_pubsub.close.assert_called_once()
        mock_redis_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_message_enrichment(self, message_bus, mock_redis_client):
        """Test that messages are properly enriched with metadata"""
        message_bus.redis_client = mock_redis_client
        
        original_message = {"type": "test", "content": "test"}
        await message_bus.publish("test_topic", original_message)
        
        # Get the published message
        call_args = mock_redis_client.publish.call_args
        published_message = json.loads(call_args[0][1])
        
        # Verify enrichment
        assert published_message["type"] == "test"
        assert published_message["content"] == "test"
        assert "timestamp" in published_message
        assert published_message["source"] == "conversation_engine"
        
        # Verify timestamp is valid ISO format
        from datetime import datetime
        timestamp = datetime.fromisoformat(published_message["timestamp"])
        assert isinstance(timestamp, datetime)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])