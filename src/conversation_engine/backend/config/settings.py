"""
Application settings with Pydantic
Integrates with existing Config Manager plugin for configuration management

Architecture Decision: Uses Pydantic Settings for type safety and validation
while leveraging the existing Config Manager for file-based configuration.
"""
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Optional
import sys
import os

# Add the plugins directory to path for importing Config Manager
sys.path.append(os.path.join(os.path.dirname(__file__), "../..", "plugins"))

from config_manager.plugin_interface import ConfigManager

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Server configuration
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    
    # Redis configuration (for message bus and memory)
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # LLM configuration
    anthropic_api_key: Optional[str] = None
    llm_model: str = "claude-3-sonnet-20240229"
    llm_temperature: float = 0.1
    max_context_tokens: int = 4000
    
    # Memory configuration
    memory_ttl_days: int = 30
    context_window_size: int = 10
    
    # Message bus configuration
    message_timeout: int = 30
    max_retries: int = 3
    
    # Plugin configuration
    plugin_discovery_paths: list = ["../plugins"]
    
    # Frontend configuration
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        env_prefix = "CONVERSATION_ENGINE_"
        case_sensitive = False

# Initialize settings instance
settings = Settings()

# Integration with existing Config Manager
config_manager = ConfigManager()

def load_from_config_manager():
    """Load additional configuration from Config Manager plugin"""
    try:
        # Load conversation engine specific config if it exists
        config = config_manager.load_config("conversation_engine")
        
        # Override settings with values from config file
        for key, value in config.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
                
    except FileNotFoundError:
        # No config file found, use defaults
        pass
    except Exception as e:
        print(f"Warning: Could not load config from Config Manager: {e}")

# Load configuration on import
load_from_config_manager()