"""
Test suite for Intent Parser
Tests LLM-based intent parsing functionality with mock Anthropic API
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

from intent.parser import IntentParser
from intent.models import ConversationIntent, IntentType, ComplexityLevel

class TestIntentParser:
    """Test intent parsing functionality"""
    
    @pytest.fixture
    def intent_parser(self):
        """Create intent parser instance with mocked API"""
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            
            parser = IntentParser()
            parser.client = mock_client
            return parser
    
    @pytest.fixture
    def sample_claude_response(self):
        """Sample Claude API response"""
        return {
            "content": [
                {
                    "text": json.dumps({
                        "type": "mission_request",
                        "confidence": 0.85,
                        "entities": {"technology": "OAuth2", "component": "authentication"},
                        "requires_plugins": ["github_integration"],
                        "context_needed": [],
                        "complexity": "complex",
                        "estimated_response_time": 15,
                        "requires_clarification": False
                    })
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_parse_mission_request_intent(self, intent_parser, sample_claude_response):
        """Test parsing mission request intent"""
        # Mock Claude API response
        intent_parser.client.messages.create.return_value = sample_claude_response
        
        user_input = "Create a new authentication system with OAuth2"
        result = await intent_parser.parse_intent(user_input, "test_conversation")
        
        assert isinstance(result, ConversationIntent)
        assert result.type == IntentType.MISSION_REQUEST
        assert result.confidence == 0.85
        assert result.entities["technology"] == "OAuth2"
        assert "github_integration" in result.requires_plugins
        assert result.complexity == ComplexityLevel.COMPLEX
        
        # Verify Claude API was called
        intent_parser.client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_status_check_intent(self, intent_parser):
        """Test parsing status check intent"""
        # Mock Claude API response for status check
        status_response = {
            "content": [
                {
                    "text": json.dumps({
                        "type": "status_check",
                        "confidence": 0.9,
                        "entities": {"target": "system"},
                        "requires_plugins": [],
                        "context_needed": [],
                        "complexity": "simple",
                        "estimated_response_time": 5,
                        "requires_clarification": False
                    })
                }
            ]
        }
        intent_parser.client.messages.create.return_value = status_response
        
        user_input = "What's the current system status?"
        result = await intent_parser.parse_intent(user_input, "test_conversation")
        
        assert result.type == IntentType.STATUS_CHECK
        assert result.confidence == 0.9
        assert result.entities["target"] == "system"
        assert result.complexity == ComplexityLevel.SIMPLE
    
    @pytest.mark.asyncio
    async def test_parse_question_intent(self, intent_parser):
        """Test parsing general question intent"""
        question_response = {
            "content": [
                {
                    "text": json.dumps({
                        "type": "question",
                        "confidence": 0.8,
                        "entities": {"topic": "plugins"},
                        "requires_plugins": [],
                        "context_needed": [],
                        "complexity": "simple",
                        "estimated_response_time": 10,
                        "requires_clarification": False
                    })
                }
            ]
        }
        intent_parser.client.messages.create.return_value = question_response
        
        user_input = "How do plugins work in this system?"
        result = await intent_parser.parse_intent(user_input, "test_conversation")
        
        assert result.type == IntentType.QUESTION
        assert result.confidence == 0.8
        assert result.entities["topic"] == "plugins"
    
    @pytest.mark.asyncio
    async def test_fallback_intent_on_json_error(self, intent_parser):
        """Test fallback intent when JSON parsing fails"""
        # Mock Claude API to return invalid JSON
        invalid_response = {
            "content": [
                {
                    "text": "This is not valid JSON"
                }
            ]
        }
        intent_parser.client.messages.create.return_value = invalid_response
        
        user_input = "Create a new feature"
        result = await intent_parser.parse_intent(user_input, "test_conversation")
        
        assert isinstance(result, ConversationIntent)
        assert result.confidence == 0.5  # Low confidence for fallback
        assert result.requires_clarification is True
    
    @pytest.mark.asyncio
    async def test_fallback_intent_on_api_error(self, intent_parser):
        """Test fallback intent when API call fails"""
        # Mock Claude API to raise an exception
        intent_parser.client.messages.create.side_effect = Exception("API Error")
        
        user_input = "What's the status?"
        result = await intent_parser.parse_intent(user_input, "test_conversation")
        
        assert isinstance(result, ConversationIntent)
        assert result.type == IntentType.STATUS_CHECK  # Based on heuristic
        assert result.confidence == 0.5
        assert result.requires_clarification is True
    
    def test_fallback_intent_heuristics(self, intent_parser):
        """Test fallback intent heuristics"""
        # Test mission request detection
        mission_intent = intent_parser._fallback_intent("Create a new authentication system")
        assert mission_intent.type == IntentType.MISSION_REQUEST
        assert "github_integration" in mission_intent.requires_plugins
        
        # Test status check detection
        status_intent = intent_parser._fallback_intent("What's the status of mission 3?")
        assert status_intent.type == IntentType.STATUS_CHECK
        assert "github_integration" in status_intent.requires_plugins
        
        # Test question detection
        question_intent = intent_parser._fallback_intent("How does this work?")
        assert question_intent.type == IntentType.QUESTION
        assert len(question_intent.requires_plugins) == 0
        
        # Test discussion detection
        discussion_intent = intent_parser._fallback_intent("Let's discuss the architecture")
        assert discussion_intent.type == IntentType.DISCUSSION
        assert len(discussion_intent.requires_plugins) == 0
    
    def test_build_intent_prompt(self, intent_parser):
        """Test intent prompt building"""
        user_input = "Create a new feature"
        prompt = intent_parser._build_intent_prompt(user_input)
        
        assert user_input in prompt
        assert "question" in prompt
        assert "mission_request" in prompt
        assert "status_check" in prompt
        assert "command" in prompt
        assert "discussion" in prompt
        assert "troubleshooting" in prompt
        assert "github_integration" in prompt
        assert "memory_manager" in prompt
        assert "config_manager" in prompt
        assert "JSON object" in prompt
    
    @pytest.mark.asyncio
    async def test_conversation_context_usage(self, intent_parser):
        """Test that conversation context is properly utilized"""
        context_response = {
            "content": [
                {
                    "text": json.dumps({
                        "type": "question",
                        "confidence": 0.9,
                        "entities": {"context": "previous_mission"},
                        "requires_plugins": ["memory_manager"],
                        "context_needed": ["conversation_history"],
                        "complexity": "simple",
                        "estimated_response_time": 8,
                        "requires_clarification": False
                    })
                }
            ]
        }
        intent_parser.client.messages.create.return_value = context_response
        
        user_input = "What was the result of that last mission?"
        result = await intent_parser.parse_intent(user_input, "test_conversation_123")
        
        assert result.type == IntentType.QUESTION
        assert "memory_manager" in result.requires_plugins
        assert "conversation_history" in result.context_needed
        
        # Verify conversation_id was passed to the parsing logic
        intent_parser.client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complex_intent_parsing(self, intent_parser):
        """Test parsing complex multi-step intents"""
        complex_response = {
            "content": [
                {
                    "text": json.dumps({
                        "type": "mission_request",
                        "confidence": 0.95,
                        "entities": {
                            "system": "authentication",
                            "features": ["OAuth2", "JWT", "2FA"],
                            "database": "PostgreSQL"
                        },
                        "requires_plugins": ["github_integration", "config_manager"],
                        "context_needed": ["project_requirements", "existing_auth"],
                        "complexity": "multi_step",
                        "estimated_response_time": 30,
                        "requires_clarification": True
                    })
                }
            ]
        }
        intent_parser.client.messages.create.return_value = complex_response
        
        user_input = "Build a complete authentication system with OAuth2, JWT tokens, 2FA, and PostgreSQL integration"
        result = await intent_parser.parse_intent(user_input, "test_conversation")
        
        assert result.type == IntentType.MISSION_REQUEST
        assert result.confidence == 0.95
        assert "OAuth2" in result.entities["features"]
        assert "JWT" in result.entities["features"]
        assert "2FA" in result.entities["features"]
        assert result.entities["database"] == "PostgreSQL"
        assert "github_integration" in result.requires_plugins
        assert "config_manager" in result.requires_plugins
        assert result.complexity == ComplexityLevel.MULTI_STEP
        assert result.estimated_response_time == 30
        assert result.requires_clarification is True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])