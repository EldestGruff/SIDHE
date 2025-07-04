"""
Pytest configuration and shared fixtures for Conversation Engine tests
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add the backend directory to Python path for imports
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Add plugins directory to path
plugins_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'plugins')
sys.path.insert(0, plugins_path)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    mock_settings = MagicMock()
    mock_settings.anthropic_api_key = "test_api_key"
    mock_settings.llm_model = "claude-3-haiku-20240307"
    mock_settings.llm_temperature = 0.7
    mock_settings.redis_url = "redis://localhost:6379"
    mock_settings.redis_db = 0
    mock_settings.message_timeout = 30
    mock_settings.host = "localhost"
    mock_settings.port = 8000
    mock_settings.debug = True
    mock_settings.log_level = "INFO"
    return mock_settings

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing"""
    client = AsyncMock()
    
    # Default response for intent parsing
    default_response = MagicMock()
    default_response.content = [
        MagicMock(text='{"type": "question", "confidence": 0.8, "entities": {}, "requires_plugins": [], "context_needed": [], "complexity": "simple", "estimated_response_time": 5, "requires_clarification": false}')
    ]
    client.messages.create.return_value = default_response
    
    return client

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    client = AsyncMock()
    client.ping = AsyncMock()
    client.publish = AsyncMock()
    client.close = AsyncMock()
    
    # Mock pubsub
    pubsub = AsyncMock()
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.listen = AsyncMock()
    pubsub.close = AsyncMock()
    client.pubsub.return_value = pubsub
    
    return client

@pytest.fixture
def mock_memory_manager():
    """Mock Memory Manager plugin"""
    manager = MagicMock()
    manager.store_memory = MagicMock(return_value=True)
    manager.get_memory = MagicMock(return_value=None)
    manager.clear_memory = MagicMock(return_value=True)
    manager.health_check = MagicMock(return_value="operational")
    return manager

@pytest.fixture
def sample_conversation_intent():
    """Sample conversation intent for testing"""
    from intent.models import ConversationIntent, IntentType, ComplexityLevel
    
    return ConversationIntent(
        type=IntentType.MISSION_REQUEST,
        confidence=0.85,
        entities={"system": "authentication", "technology": "OAuth2"},
        requires_plugins=["github_integration"],
        context_needed=[],
        complexity=ComplexityLevel.COMPLEX,
        estimated_response_time=15,
        requires_clarification=False
    )

@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing"""
    return {
        "conversation_id": "test_conv_123",
        "session_id": "test_session_456",
        "user_id": "test_user_789",
        "messages": [
            {
                "id": 1,
                "type": "user",
                "content": "Hello Riker",
                "timestamp": "2025-01-01T10:00:00Z",
                "intent": {"type": "greeting", "confidence": 0.9}
            },
            {
                "id": 2,
                "type": "assistant",
                "content": "Hello! How can I help you today?",
                "timestamp": "2025-01-01T10:00:01Z"
            }
        ]
    }

@pytest.fixture
def sample_turn_data():
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

@pytest.fixture(autouse=True)
def mock_environment_variables():
    """Mock environment variables for testing"""
    env_vars = {
        "ANTHROPIC_API_KEY": "test_api_key",
        "REDIS_URL": "redis://localhost:6379",
        "REDIS_DB": "0",
        "HOST": "localhost",
        "PORT": "8000",
        "DEBUG": "true",
        "LOG_LEVEL": "INFO"
    }
    
    with patch.dict(os.environ, env_vars):
        yield

@pytest.fixture
def temp_conversation_id():
    """Generate a temporary conversation ID for testing"""
    import uuid
    return f"test_conv_{uuid.uuid4().hex[:8]}"

@pytest.fixture
def freeze_time():
    """Fixture to freeze time for consistent testing"""
    from freezegun import freeze_time as _freeze_time
    return _freeze_time

# Async test helpers
@pytest.fixture
async def async_mock():
    """Helper to create async mocks"""
    return AsyncMock()

# Plugin test fixtures
@pytest.fixture
def mock_plugin_instances():
    """Mock plugin instances for registry testing"""
    return {
        "memory_manager": MagicMock(),
        "github_integration": MagicMock(),
        "config_manager": MagicMock()
    }

@pytest.fixture
def mock_plugin_data():
    """Mock plugin data structure"""
    return {
        "memory_manager": {
            "info": {
                "name": "Memory Manager",
                "description": "Conversation memory and context management",
                "module": "memory_manager.plugin_interface",
                "class": "MemoryManager",
                "capabilities": ["store_memory", "get_memory", "clear_memory"]
            },
            "status": "active",
            "instance": MagicMock(),
            "last_check": "2025-01-01T00:00:00Z"
        },
        "github_integration": {
            "info": {
                "name": "GitHub Integration",
                "description": "Away Mission management and GitHub operations",
                "module": "github_integration.plugin_interface", 
                "class": "GitHubManager",
                "capabilities": ["get_away_missions", "create_mission", "update_mission_progress"]
            },
            "status": "active",
            "instance": MagicMock(),
            "last_check": "2025-01-01T00:00:00Z"
        }
    }

# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )