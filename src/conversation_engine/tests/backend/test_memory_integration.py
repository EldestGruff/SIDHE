"""
Test suite for Memory Integration
Tests conversation storage and retrieval with Memory Manager plugin
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from memory.integration import ConversationMemory

class TestConversationMemory:
    """Test conversation memory integration"""
    
    @pytest.fixture
    def conversation_memory(self):
        """Create conversation memory instance with mocked Memory Manager"""
        with patch('memory_manager.plugin_interface.MemoryManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            memory = ConversationMemory()
            memory.memory_manager = mock_instance
            return memory
    
    @pytest.fixture
    def sample_turn_data(self):
        """Sample conversation turn data"""
        return {
            "user_input": "Create a new authentication system",
            "intent": {
                "type": "mission_request",
                "confidence": 0.85,
                "entities": {"system": "authentication"},
                "requires_plugins": ["github_integration"]
            },
            "system_response": "I'll help you create an authentication system.",
            "session_id": "session_123",
            "user_id": "user_456",
            "processing_time": 1.5
        }
    
    @pytest.mark.asyncio
    async def test_store_turn_success(self, conversation_memory, sample_turn_data):
        """Test successful conversation turn storage"""
        conversation_memory.memory_manager.store_memory.return_value = True
        
        result = await conversation_memory.store_turn("conv_123", sample_turn_data)
        
        assert result is True
        
        # Verify store_memory was called
        conversation_memory.memory_manager.store_memory.assert_called()
        
        # Check the stored data structure
        call_args = conversation_memory.memory_manager.store_memory.call_args
        stored_key = call_args[0][0]
        stored_data = call_args[0][1]
        
        assert stored_key.startswith("conversation:conv_123:turn:")
        assert stored_data["type"] == "conversation_turn"
        assert stored_data["conversation_id"] == "conv_123"
        assert stored_data["user_input"] == sample_turn_data["user_input"]
        assert stored_data["intent"] == sample_turn_data["intent"]
        assert stored_data["system_response"] == sample_turn_data["system_response"]
        assert "timestamp" in stored_data
        assert "turn_id" in stored_data
        assert stored_data["metadata"]["session_id"] == "session_123"
        assert stored_data["metadata"]["user_id"] == "user_456"
        assert stored_data["metadata"]["processing_time"] == 1.5
    
    @pytest.mark.asyncio
    async def test_store_turn_failure(self, conversation_memory, sample_turn_data):
        """Test conversation turn storage failure"""
        conversation_memory.memory_manager.store_memory.return_value = False
        
        result = await conversation_memory.store_turn("conv_123", sample_turn_data)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_store_turn_no_memory_manager(self, sample_turn_data):
        """Test storing turn when memory manager is not available"""
        memory = ConversationMemory()
        memory.memory_manager = None
        
        result = await memory.store_turn("conv_123", sample_turn_data)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_store_turn_exception(self, conversation_memory, sample_turn_data):
        """Test handling exceptions during turn storage"""
        conversation_memory.memory_manager.store_memory.side_effect = Exception("Storage error")
        
        result = await conversation_memory.store_turn("conv_123", sample_turn_data)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self, conversation_memory):
        """Test successful conversation history retrieval"""
        # Mock metadata
        mock_metadata = {
            "conversation_id": "conv_123",
            "turn_ids": ["turn_1", "turn_2", "turn_3"],
            "total_turns": 3
        }
        
        # Mock turn data
        mock_turns = [
            {
                "turn_id": "turn_1",
                "user_input": "Hello",
                "intent": {"type": "greeting"},
                "timestamp": "2025-01-01T10:00:00Z"
            },
            {
                "turn_id": "turn_2", 
                "user_input": "How are you?",
                "intent": {"type": "question"},
                "timestamp": "2025-01-01T10:01:00Z"
            },
            {
                "turn_id": "turn_3",
                "user_input": "Create a mission",
                "intent": {"type": "mission_request"},
                "timestamp": "2025-01-01T10:02:00Z"
            }
        ]
        
        def mock_get_memory(key):
            if "metadata" in key:
                return mock_metadata
            elif "turn:turn_1" in key:
                return mock_turns[0]
            elif "turn:turn_2" in key:
                return mock_turns[1]
            elif "turn:turn_3" in key:
                return mock_turns[2]
            return None
        
        conversation_memory.memory_manager.get_memory.side_effect = mock_get_memory
        
        history = await conversation_memory.get_conversation_history("conv_123", limit=10)
        
        assert len(history) == 3
        assert history[0]["turn_id"] == "turn_1"
        assert history[1]["turn_id"] == "turn_2"
        assert history[2]["turn_id"] == "turn_3"
        assert history[0]["user_input"] == "Hello"
        assert history[2]["intent"]["type"] == "mission_request"
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_no_metadata(self, conversation_memory):
        """Test conversation history retrieval when no metadata exists"""
        conversation_memory.memory_manager.get_memory.return_value = None
        
        history = await conversation_memory.get_conversation_history("conv_123")
        
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_no_memory_manager(self):
        """Test conversation history retrieval when memory manager is not available"""
        memory = ConversationMemory()
        memory.memory_manager = None
        
        history = await memory.get_conversation_history("conv_123")
        
        assert history == []
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_with_limit(self, conversation_memory):
        """Test conversation history retrieval with limit"""
        mock_metadata = {
            "conversation_id": "conv_123",
            "turn_ids": ["turn_1", "turn_2", "turn_3", "turn_4", "turn_5"],
            "total_turns": 5
        }
        
        mock_turns = [
            {"turn_id": "turn_4", "user_input": "Turn 4"},
            {"turn_id": "turn_5", "user_input": "Turn 5"}
        ]
        
        def mock_get_memory(key):
            if "metadata" in key:
                return mock_metadata
            elif "turn:turn_4" in key:
                return mock_turns[0]
            elif "turn:turn_5" in key:
                return mock_turns[1]
            return None
        
        conversation_memory.memory_manager.get_memory.side_effect = mock_get_memory
        
        history = await conversation_memory.get_conversation_history("conv_123", limit=2)
        
        assert len(history) == 2
        assert history[0]["turn_id"] == "turn_4"
        assert history[1]["turn_id"] == "turn_5"
    
    @pytest.mark.asyncio
    async def test_build_context_success(self, conversation_memory):
        """Test successful context building"""
        # Mock recent turns
        mock_turns = [
            {
                "turn_id": "turn_1",
                "user_input": "Hello",
                "intent": {"type": "greeting", "entities": {"emotion": "friendly"}},
                "timestamp": "2025-01-01T10:00:00Z"
            },
            {
                "turn_id": "turn_2",
                "user_input": "Create auth system",
                "intent": {"type": "mission_request", "entities": {"system": "authentication"}},
                "timestamp": "2025-01-01T10:01:00Z"
            }
        ]
        
        # Mock get_conversation_history
        with patch.object(conversation_memory, 'get_conversation_history', return_value=mock_turns):
            context = await conversation_memory.build_context("conv_123")
        
        assert context["conversation_id"] == "conv_123"
        assert context["recent_turns"] == mock_turns
        assert context["turn_count"] == 2
        assert context["last_activity"] == "2025-01-01T10:01:00Z"
        assert "greeting" in context["topics"]
        assert "authentication" in context["topics"]
        assert "mission_request" in context["topics"]
        assert "greeting" in context["active_intents"]
        assert "mission_request" in context["active_intents"]
    
    @pytest.mark.asyncio
    async def test_build_context_no_history(self, conversation_memory):
        """Test context building with no history"""
        with patch.object(conversation_memory, 'get_conversation_history', return_value=[]):
            context = await conversation_memory.build_context("conv_123")
        
        assert context["conversation_id"] == "conv_123"
        assert context["recent_turns"] == []
        assert context["turn_count"] == 0
        assert context["last_activity"] is None
        assert context["topics"] == []
        assert context["active_intents"] == []
    
    @pytest.mark.asyncio
    async def test_update_conversation_metadata(self, conversation_memory):
        """Test conversation metadata updates"""
        # Mock existing metadata
        existing_metadata = {
            "conversation_id": "conv_123",
            "created_at": "2025-01-01T09:00:00Z",
            "turn_ids": ["turn_1"],
            "total_turns": 1,
            "last_activity": "2025-01-01T09:01:00Z"
        }
        
        def mock_get_memory(key):
            if "metadata" in key:
                return existing_metadata
            return None
        
        conversation_memory.memory_manager.get_memory.side_effect = mock_get_memory
        conversation_memory.memory_manager.store_memory.return_value = True
        
        turn_data = {
            "turn_id": "turn_2",
            "intent": {"type": "question"}
        }
        
        result = await conversation_memory._update_conversation_metadata("conv_123", turn_data)
        
        assert result is True
        
        # Verify store_memory was called
        conversation_memory.memory_manager.store_memory.assert_called()
        
        # Check updated metadata
        call_args = conversation_memory.memory_manager.store_memory.call_args
        stored_metadata = call_args[0][1]
        
        assert stored_metadata["conversation_id"] == "conv_123"
        assert "turn_2" in stored_metadata["turn_ids"]
        assert stored_metadata["total_turns"] == 2
        assert stored_metadata["last_intent"] == "question"
        assert "last_activity" in stored_metadata
    
    @pytest.mark.asyncio
    async def test_update_conversation_metadata_new_conversation(self, conversation_memory):
        """Test metadata update for new conversation"""
        conversation_memory.memory_manager.get_memory.return_value = None
        conversation_memory.memory_manager.store_memory.return_value = True
        
        turn_data = {
            "turn_id": "turn_1",
            "intent": {"type": "greeting"}
        }
        
        result = await conversation_memory._update_conversation_metadata("conv_123", turn_data)
        
        assert result is True
        
        # Check new metadata structure
        call_args = conversation_memory.memory_manager.store_memory.call_args
        stored_metadata = call_args[0][1]
        
        assert stored_metadata["conversation_id"] == "conv_123"
        assert stored_metadata["turn_ids"] == ["turn_1"]
        assert stored_metadata["total_turns"] == 1
        assert stored_metadata["last_intent"] == "greeting"
        assert "created_at" in stored_metadata
        assert "last_activity" in stored_metadata
    
    def test_extract_topics(self, conversation_memory):
        """Test topic extraction from conversation turns"""
        turns = [
            {
                "intent": {
                    "type": "mission_request",
                    "entities": {
                        "system": "authentication",
                        "technology": "OAuth2",
                        "database": "PostgreSQL"
                    }
                }
            },
            {
                "intent": {
                    "type": "question",
                    "entities": {
                        "topic": "plugins"
                    }
                }
            }
        ]
        
        topics = conversation_memory._extract_topics(turns)
        
        assert "authentication" in topics
        assert "OAuth2" in topics
        assert "PostgreSQL" in topics
        assert "plugins" in topics
        assert "mission_request" in topics
        assert "question" in topics
    
    def test_extract_recent_intents(self, conversation_memory):
        """Test recent intent extraction"""
        turns = [
            {"intent": {"type": "greeting"}},
            {"intent": {"type": "mission_request"}},
            {"intent": {"type": "question"}},
            {"intent": {"type": "mission_request"}}  # Duplicate
        ]
        
        intents = conversation_memory._extract_recent_intents(turns)
        
        assert "greeting" in intents
        assert "mission_request" in intents
        assert "question" in intents
        assert len(intents) == 3  # No duplicates
    
    @pytest.mark.asyncio
    async def test_health_check_operational(self, conversation_memory):
        """Test health check when operational"""
        conversation_memory.memory_manager.store_memory.return_value = True
        conversation_memory.memory_manager.get_memory.return_value = {"timestamp": "2025-01-01T00:00:00Z"}
        
        health = await conversation_memory.health_check()
        
        assert health == "operational"
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self, conversation_memory):
        """Test health check when degraded"""
        conversation_memory.memory_manager.store_memory.return_value = True
        conversation_memory.memory_manager.get_memory.return_value = None
        
        health = await conversation_memory.health_check()
        
        assert health == "degraded"
    
    @pytest.mark.asyncio
    async def test_health_check_error(self, conversation_memory):
        """Test health check with error"""
        conversation_memory.memory_manager.store_memory.return_value = False
        
        health = await conversation_memory.health_check()
        
        assert health == "error"
    
    @pytest.mark.asyncio
    async def test_health_check_disconnected(self):
        """Test health check when disconnected"""
        memory = ConversationMemory()
        memory.memory_manager = None
        
        health = await memory.health_check()
        
        assert health == "disconnected"
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, conversation_memory):
        """Test health check with exception"""
        conversation_memory.memory_manager.store_memory.side_effect = Exception("Memory error")
        
        health = await conversation_memory.health_check()
        
        assert health == "error"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])