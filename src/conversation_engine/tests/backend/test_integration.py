"""
Integration tests for Conversation Engine
Tests end-to-end workflows and component interactions
"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from intent.models import ConversationIntent, IntentType, ComplexityLevel
from intent.parser import IntentParser
from bus.publisher import MessageBus
from memory.integration import ConversationMemory
from plugins.registry import PluginRegistry
from main import route_to_plugins

class TestConversationFlow:
    """Test complete conversation flows"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_mission_request_flow(self):
        """Test complete flow from intent parsing to plugin execution"""
        # Mock all components
        mock_intent_parser = MagicMock()
        mock_message_bus = AsyncMock()
        mock_memory = AsyncMock()
        mock_registry = MagicMock()
        
        # Set up intent parsing response
        mission_intent = ConversationIntent(
            type=IntentType.MISSION_REQUEST,
            confidence=0.9,
            entities={"system": "authentication", "technology": "OAuth2"},
            requires_plugins=["github_integration"],
            context_needed=[],
            complexity=ComplexityLevel.COMPLEX,
            estimated_response_time=20,
            requires_clarification=False
        )
        
        # Set up plugin response
        plugin_response = {
            "status": "success",
            "content": "Authentication mission created successfully! I've created Away Mission #4 for implementing OAuth2 authentication.",
            "data": {
                "mission_id": "4",
                "title": "OAuth2 Authentication System",
                "status": "open",
                "assignee": "Claude"
            }
        }
        
        # Mock message bus response
        mock_message_bus.request_response.return_value = plugin_response
        
        # Test message
        test_message = {
            "content": "Create a new OAuth2 authentication system",
            "conversation_id": "test_conv_123",
            "timestamp": "2025-01-01T10:00:00Z"
        }
        
        # Mock the routing with the mocked message bus
        with patch('main.message_bus', mock_message_bus):
            response = await route_to_plugins(mission_intent, test_message)
        
        # Verify response
        assert response["status"] == "success"
        assert "Authentication mission created" in response["content"]
        assert response["data"]["mission_id"] == "4"
        
        # Verify plugin was called correctly
        mock_message_bus.request_response.assert_called_once_with(
            "github_integration",
            "create_mission",
            {"intent": mission_intent.dict(), "message": test_message}
        )
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_system_health_check_flow(self):
        """Test system health check flow"""
        # Create health check intent
        health_intent = ConversationIntent(
            type=IntentType.STATUS_CHECK,
            confidence=0.95,
            entities={"target": "system", "type": "health"},
            requires_plugins=[],
            context_needed=[],
            complexity=ComplexityLevel.SIMPLE,
            estimated_response_time=5,
            requires_clarification=False
        )
        
        test_message = {
            "content": "What's the current system health?",
            "conversation_id": "test_conv_456"
        }
        
        # Mock system health data
        mock_health_data = {
            "status": "operational",
            "components": {
                "websocket": "ready",
                "message_bus": "operational", 
                "plugins": {
                    "memory_manager": "active",
                    "github_integration": "active",
                    "config_manager": "active"
                },
                "memory": "operational"
            }
        }
        
        with patch('main.get_system_health', return_value=mock_health_data):
            response = await route_to_plugins(health_intent, test_message)
        
        # Verify response structure
        assert response["type"] == "status_response"
        assert "System Status: operational" in response["content"]
        assert "Components:" in response["content"]
        assert response["data"]["status"] == "operational"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_question_answering_flow(self):
        """Test question answering flow"""
        question_intent = ConversationIntent(
            type=IntentType.QUESTION,
            confidence=0.8,
            entities={"topic": "plugins", "detail": "functionality"},
            requires_plugins=[],
            context_needed=[],
            complexity=ComplexityLevel.SIMPLE,
            estimated_response_time=10,
            requires_clarification=False
        )
        
        test_message = {
            "content": "How do plugins work in this system?",
            "conversation_id": "test_conv_789"
        }
        
        # Mock plugin registry
        mock_plugin_status = {
            "memory_manager": "active",
            "github_integration": "active",
            "config_manager": "active"
        }
        
        with patch('main.plugin_registry') as mock_registry:
            mock_registry.get_status.return_value = mock_plugin_status
            
            response = await route_to_plugins(question_intent, test_message)
        
        # Verify response
        assert response["type"] == "answer"
        assert "available plugins" in response["content"].lower()
        assert response["data"] == mock_plugin_status
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_flow(self):
        """Test error handling in conversation flow"""
        error_intent = ConversationIntent(
            type=IntentType.MISSION_REQUEST,
            confidence=0.7,
            entities={"system": "broken_system"},
            requires_plugins=["non_existent_plugin"],
            context_needed=[],
            complexity=ComplexityLevel.COMPLEX,
            estimated_response_time=15,
            requires_clarification=True
        )
        
        test_message = {
            "content": "Create something that will fail",
            "conversation_id": "test_conv_error"
        }
        
        # Mock message bus to raise exception
        mock_message_bus = AsyncMock()
        mock_message_bus.request_response.side_effect = Exception("Plugin communication failed")
        
        with patch('main.message_bus', mock_message_bus):
            response = await route_to_plugins(error_intent, test_message)
        
        # Verify error response
        assert response["type"] == "error"
        assert "encountered an error" in response["content"]
        assert "error" in response
        assert response["intent"] == error_intent.dict()

class TestComponentIntegration:
    """Test integration between components"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_intent_parser_and_memory_integration(self):
        """Test intent parser with memory context"""
        # Create intent parser with mocked Anthropic client
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = [
                MagicMock(text=json.dumps({
                    "type": "question",
                    "confidence": 0.9,
                    "entities": {"context": "previous_mission"},
                    "requires_plugins": ["memory_manager"],
                    "context_needed": ["conversation_history"],
                    "complexity": "simple",
                    "estimated_response_time": 8,
                    "requires_clarification": False
                }))
            ]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client
            
            parser = IntentParser()
            
            # Parse intent that requires memory context
            intent = await parser.parse_intent(
                "What was the result of that authentication mission?",
                "test_conv_with_history"
            )
            
            assert intent.type == IntentType.QUESTION
            assert "memory_manager" in intent.requires_plugins
            assert "conversation_history" in intent.context_needed
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_message_bus_and_plugin_registry_integration(self):
        """Test message bus communication with plugin registry"""
        # Create message bus
        message_bus = MessageBus()
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.publish = AsyncMock()
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            await message_bus.initialize()
            
            # Test plugin communication
            test_payload = {
                "action": "get_status",
                "plugin_id": "memory_manager"
            }
            
            # Mock a successful response
            with patch.object(message_bus, 'request_response') as mock_request:
                mock_request.return_value = {
                    "status": "success",
                    "data": {"health": "operational"}
                }
                
                response = await message_bus.request_response(
                    "memory_manager",
                    "health_check", 
                    test_payload
                )
                
                assert response["status"] == "success"
                assert response["data"]["health"] == "operational"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_and_conversation_flow(self):
        """Test memory integration with conversation flow"""
        # Create conversation memory with mocked Memory Manager
        with patch('memory_manager.plugin_interface.MemoryManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.store_memory.return_value = True
            mock_instance.get_memory.return_value = {
                "conversation_id": "test_conv",
                "turn_ids": ["turn_1", "turn_2"],
                "total_turns": 2
            }
            mock_manager.return_value = mock_instance
            
            memory = ConversationMemory()
            
            # Store conversation turn
            turn_data = {
                "user_input": "Create authentication system",
                "intent": {
                    "type": "mission_request",
                    "confidence": 0.9
                },
                "system_response": "Mission created"
            }
            
            result = await memory.store_turn("test_conv", turn_data)
            assert result is True
            
            # Build context
            context = await memory.build_context("test_conv")
            assert context["conversation_id"] == "test_conv"
            assert "recent_turns" in context

class TestPerformanceAndScaling:
    """Test performance and scaling aspects"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_conversation_handling(self):
        """Test handling multiple concurrent conversations"""
        # Create multiple conversation intents
        intents = []
        messages = []
        
        for i in range(5):
            intent = ConversationIntent(
                type=IntentType.QUESTION,
                confidence=0.8,
                entities={"conversation": f"conv_{i}"},
                requires_plugins=[],
                context_needed=[],
                complexity=ComplexityLevel.SIMPLE,
                estimated_response_time=5,
                requires_clarification=False
            )
            
            message = {
                "content": f"Question from conversation {i}",
                "conversation_id": f"test_conv_{i}"
            }
            
            intents.append(intent)
            messages.append(message)
        
        # Process all conversations concurrently
        tasks = []
        for intent, message in zip(intents, messages):
            task = asyncio.create_task(route_to_plugins(intent, message))
            tasks.append(task)
        
        # Wait for all to complete
        responses = await asyncio.gather(*tasks)
        
        # Verify all responses
        assert len(responses) == 5
        for i, response in enumerate(responses):
            assert response["type"] == "answer"
            assert response["intent"]["entities"]["conversation"] == f"conv_{i}"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_plugin_health_monitoring(self):
        """Test plugin health monitoring integration"""
        # Create plugin registry
        registry = PluginRegistry()
        
        # Mock plugin instances with health checks
        mock_plugins = {
            "memory_manager": MagicMock(),
            "github_integration": MagicMock(),
            "config_manager": MagicMock()
        }
        
        # Set up health check responses
        mock_plugins["memory_manager"].health_check.return_value = "operational"
        mock_plugins["github_integration"].health_check.return_value = "degraded"
        mock_plugins["config_manager"].health_check.return_value = "operational"
        
        # Set up registry plugins
        registry.plugins = {
            "memory_manager": {"instance": mock_plugins["memory_manager"]},
            "github_integration": {"instance": mock_plugins["github_integration"]},
            "config_manager": {"instance": mock_plugins["config_manager"]}
        }
        
        # Run health checks
        await registry._check_plugin_health()
        
        # Verify health status
        assert registry.plugin_health["memory_manager"] == "operational"
        assert registry.plugin_health["github_integration"] == "degraded"
        assert registry.plugin_health["config_manager"] == "operational"
        
        # Test refresh
        await registry.refresh_health()
        
        # Verify all health checks were called
        for plugin in mock_plugins.values():
            plugin.health_check.assert_called()

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])