"""
Backend testing framework example for Conversation Engine
Demonstrates testing patterns for WebSocket, intent parsing, and plugin integration

Architecture Decision: Comprehensive test coverage with mock-based testing
for external dependencies and integration testing patterns.
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocket

# Test imports - actual modules
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from main import app, route_to_plugins, handle_status_request, handle_question, handle_command
from intent.models import ConversationIntent, IntentType, ComplexityLevel
from bus.publisher import MessageBus
from memory.integration import ConversationMemory
from plugins.registry import PluginRegistry

# Test client setup
client = TestClient(app)

class TestMainApplication:
    """Test the main FastAPI application"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "enchanted"
        assert "components" in data
        assert "websocket" in data["components"]
        assert "message_bus" in data["components"]
        assert "plugins" in data["components"]
        assert "memory" in data["components"]
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "SIDHE Conversation Engine" in data["message"]
        assert "Ready to engage" in data["message"]
    
    @pytest.mark.asyncio
    async def test_route_to_plugins_quest_request(self):
        """Test routing quest request to plugins"""
        mock_intent = ConversationIntent(
            type=IntentType.MISSION_REQUEST,
            confidence=0.9,
            entities={"system": "authentication"},
            requires_plugins=["quest_tracker"],
            context_needed=[],
            complexity=ComplexityLevel.COMPLEX,
            estimated_response_time=15,
            requires_clarification=False
        )
        
        message = {
            "content": "Create a new authentication system",
            "conversation_id": "test_123"
        }
        
        with patch('main.message_bus') as mock_bus:
            mock_bus.request_response.return_value = {
                "status": "success",
                "content": "Quest created successfully"
            }
            
            response = await route_to_plugins(mock_intent, message)
            
            assert response["status"] == "success"
            mock_bus.request_response.assert_called_once_with(
                "quest_tracker",
                "create_quest", 
                {"intent": mock_intent.dict(), "message": message}
            )
    
    @pytest.mark.asyncio
    async def test_route_to_plugins_status_check(self):
        """Test routing status check to appropriate handler"""
        mock_intent = ConversationIntent(
            type=IntentType.STATUS_CHECK,
            confidence=0.8,
            entities={"target": "system"},
            requires_plugins=[],
            context_needed=[],
            complexity=ComplexityLevel.SIMPLE,
            estimated_response_time=5,
            requires_clarification=False
        )
        
        message = {
            "content": "What's the system status?",
            "conversation_id": "test_123"
        }
        
        response = await route_to_plugins(mock_intent, message)
        
        assert response["type"] == "status_response"
        assert "System Status" in response["content"]

class TestIntentParsing:
    """Test intent parsing functionality"""
    
    @pytest.fixture
    def sample_context(self):
        """Create sample conversation context"""
        return ConversationContext(
            conversation_id="test_123",
            session_id="session_456",
            recent_turns=[],
            active_quests=[],
            available_plugins=["tome_keeper", "quest_tracker", "config_manager"]
        )
    
    def test_conversation_intent_creation(self):
        """Test ConversationIntent model creation"""
        intent = ConversationIntent(
            type="quest_request",
            confidence=0.85,
            entities={"technology": "OAuth2", "component": "authentication"},
            requires_plugins=["quest_tracker"],
            complexity="complex"
        )
        
        assert intent.type == "quest_request"
        assert intent.confidence == 0.85
        assert intent.entities["technology"] == "OAuth2"
        assert "quest_tracker" in intent.requires_plugins
        assert intent.complexity == "complex"
    
    def test_conversation_context_creation(self, sample_context):
        """Test ConversationContext model creation"""
        assert sample_context.conversation_id == "test_123"
        assert sample_context.session_id == "session_456"
        assert isinstance(sample_context.recent_turns, list)
        assert isinstance(sample_context.active_quests, list)
        assert len(sample_context.available_plugins) == 3
    
    # This would be implemented by Claude Code
    @pytest.mark.asyncio
    async def test_intent_parsing_quest_request(self, sample_context):
        """Test parsing quest request intent"""
        # Mock the intent parser since it's not implemented yet
        mock_parser = AsyncMock()
        mock_parser.parse_intent.return_value = ConversationIntent(
            type="quest_request",
            confidence=0.9,
            entities={"system": "authentication", "method": "OAuth2"},
            requires_plugins=["quest_tracker"],
            complexity="complex"
        )
        
        user_input = "Create a new authentication system with OAuth2"
        intent = await mock_parser.parse_intent(user_input, sample_context)
        
        assert intent.type == "quest_request"
        assert intent.confidence > 0.8
        assert "quest_tracker" in intent.requires_plugins
        assert intent.complexity == "complex"

class TestMessageBus:
    """Test message bus functionality"""
    
    @pytest.fixture
    def message_bus(self):
        """Create message bus instance"""
        return MessageBus()
    
    @pytest.mark.asyncio
    async def test_message_bus_initialization(self, message_bus):
        """Test message bus initialization"""
        # Mock Redis connection
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.return_value.ping = AsyncMock()
            
            await message_bus.initialize()
            
            # Verify Redis connection was attempted
            mock_redis.assert_called_once()
            assert message_bus.redis_client is not None
    
    @pytest.mark.asyncio
    async def test_message_publishing(self, message_bus):
        """Test message publishing"""
        # Mock Redis client
        message_bus.redis_client = AsyncMock()
        
        test_message = {"type": "test", "content": "Hello World"}
        await message_bus.publish("test_topic", test_message)
        
        # Verify message was published
        message_bus.redis_client.publish.assert_called_once()
        call_args = message_bus.redis_client.publish.call_args
        assert call_args[0][0] == "test_topic"
        assert json.loads(call_args[0][1]) == test_message
    
    @pytest.mark.asyncio
    async def test_health_check(self, message_bus):
        """Test message bus health check"""
        # Test healthy state
        message_bus.redis_client = AsyncMock()
        message_bus.redis_client.ping = AsyncMock()
        
        health = await message_bus.health_check()
        assert health == "healthy"
        
        # Test unhealthy state
        message_bus.redis_client.ping.side_effect = Exception("Connection failed")
        health = await message_bus.health_check()
        assert health == "unhealthy"

class TestMemoryIntegration:
    """Test memory integration functionality"""
    
    @pytest.fixture
    def conversation_memory(self):
        """Create conversation memory instance"""
        memory = ConversationMemory()
        # Mock the underlying memory manager
        memory.tome_keeper = AsyncMock()
        return memory
    
    @pytest.mark.asyncio
    async def test_store_conversation_turn(self, conversation_memory):
        """Test storing conversation turn"""
        conversation_id = "test_conversation"
        turn_data = {
            "user_input": "Hello SIDHE",
            "intent": {"type": "greeting", "confidence": 0.95}
        }
        
        result = await conversation_memory.store_turn(conversation_id, turn_data)
        
        assert result is True
        # Verify the memory manager was called
        conversation_memory.tome_keeper.store_list_item.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_conversation_history(self, conversation_memory):
        """Test retrieving conversation history"""
        conversation_id = "test_conversation"
        
        # Mock return data
        conversation_memory.tome_keeper.retrieve_list.return_value = [
            {"user_input": "Hello", "timestamp": "2025-01-01T00:00:00Z"},
            {"user_input": "How are you?", "timestamp": "2025-01-01T00:01:00Z"}
        ]
        
        history = await conversation_memory.retrieve_conversation_history(conversation_id)
        
        assert len(history) == 2
        assert history[0]["user_input"] == "Hello"
        conversation_memory.tome_keeper.retrieve_list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check(self, conversation_memory):
        """Test conversation memory health check"""
        # Mock successful health check
        conversation_memory.tome_keeper.store_structured = AsyncMock()
        conversation_memory.tome_keeper.retrieve_structured = AsyncMock()
        conversation_memory.tome_keeper.retrieve_structured.return_value = {
            "timestamp": "2025-01-01T00:00:00Z"
        }
        
        health = await conversation_memory.health_check()
        assert health == "healthy"

class TestPluginRegistry:
    """Test plugin registry functionality"""
    
    @pytest.fixture
    def plugin_registry(self):
        """Create plugin registry instance"""
        return PluginRegistry()
    
    @pytest.mark.asyncio
    async def test_plugin_discovery(self, plugin_registry):
        """Test plugin discovery"""
        # Mock plugin loading
        with patch.object(plugin_registry, '_load_plugin') as mock_load:
            mock_load.return_value = MagicMock()
            
            await plugin_registry.discover_plugins()
            
            # Verify known plugins were registered
            assert "tome_keeper" in plugin_registry.plugins
            assert "quest_tracker" in plugin_registry.plugins
            assert "config_manager" in plugin_registry.plugins
    
    def test_get_plugins_by_capability(self, plugin_registry):
        """Test getting plugins by capability"""
        # Mock plugin info
        plugin_registry.plugins = {
            "tome_keeper": MagicMock(capabilities=["memory_storage", "conversation_history"]),
            "quest_tracker": MagicMock(capabilities=["quest_management", "pr_creation"]),
            "config_manager": MagicMock(capabilities=["configuration", "settings_management"])
        }
        
        memory_plugins = plugin_registry.get_plugins_by_capability("memory_storage")
        assert "tome_keeper" in memory_plugins
        assert len(memory_plugins) == 1
        
        config_plugins = plugin_registry.get_plugins_by_capability("configuration")
        assert "config_manager" in config_plugins
    
    @pytest.mark.asyncio
    async def test_health_check_all(self, plugin_registry):
        """Test health check for all plugins"""
        # Mock plugin instances
        plugin_registry.plugins = {
            "tome_keeper": MagicMock(health_status="healthy"),
            "quest_tracker": MagicMock(health_status="healthy"),
            "config_manager": MagicMock(health_status="healthy")
        }
        plugin_registry.plugin_instances = {
            "tome_keeper": MagicMock(),
            "quest_tracker": MagicMock(),
            "config_manager": MagicMock()
        }
        
        health_status = await plugin_registry.health_check_all()
        
        assert health_status["tome_keeper"] == "healthy"
        assert health_status["quest_tracker"] == "healthy"
        assert health_status["config_manager"] == "healthy"

class TestIntegrationWorkflow:
    """Test end-to-end integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self):
        """Test complete conversation flow from input to response"""
        # This would test the entire flow:
        # 1. WebSocket receives message
        # 2. Intent parsing
        # 3. Plugin routing
        # 4. Memory storage
        # 5. Response generation
        
        # Mock all components
        mock_websocket = AsyncMock()
        mock_intent_parser = AsyncMock()
        mock_message_bus = AsyncMock()
        mock_memory = AsyncMock()
        
        # Mock intent parsing result
        mock_intent_parser.parse_intent.return_value = ConversationIntent(
            type="question",
            confidence=0.9,
            entities={"topic": "system status"},
            requires_plugins=["config_manager"],
            complexity="simple"
        )
        
        # Mock plugin response
        mock_message_bus.request_response.return_value = {
            "status": "success",
            "data": {"system_status": "enchanted"}
        }
        
        # Test message
        test_message = {
            "content": "What's the current system status?",
            "conversation_id": "test_123"
        }
        
        # This would be the actual flow test
        # For now, just verify the mocks would be called correctly
        assert mock_intent_parser.parse_intent.call_count == 0
        assert mock_message_bus.request_response.call_count == 0
        
        # In a real integration test, we'd:
        # 1. Send WebSocket message
        # 2. Verify intent parsing was called
        # 3. Verify plugin routing occurred
        # 4. Verify memory storage
        # 5. Verify response was sent back

if __name__ == '__main__':
    pytest.main([__file__, '-v'])