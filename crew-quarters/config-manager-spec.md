# Config Manager Plugin Specification

## Overview
Create a configuration management plugin that handles reading, writing, and validating configuration files for Riker. This plugin will be the central point for all configuration needs across the system.

## Implementation Location
Create all files in: `src/plugins/config_manager/`

## Core Requirements

The Config Manager must handle:
1. Multiple configuration formats (YAML and JSON)
2. Nested configuration structures
3. Environment variable overrides
4. Type validation
5. Default values
6. Configuration merging (base + overrides)

## Required Files

### 1. `__init__.py`
Empty file for Python package initialization.

### 2. `plugin_interface.py`
Main configuration management interface:

```python
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import os
import json
import yaml
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConfigValue:
    """Represents a configuration value with metadata"""
    key: str
    value: Any
    source: str  # 'file', 'env', 'default'
    original_type: type

class ConfigManager:
    """Manages configuration files and environment overrides for Riker"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the config manager
        
        Args:
            config_dir: Base directory for config files (default: ./config)
        """
        # Set up config directory
        # Initialize internal config store
        # Set up environment prefix (e.g., RIKER_)
        pass
    
    def load_config(self, config_name: str, format: str = "auto") -> Dict[str, Any]:
        """
        Load a configuration file
        
        Args:
            config_name: Name of config file (without extension)
            format: File format - "yaml", "json", or "auto" (auto-detect)
            
        Returns:
            Dictionary of configuration values
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If format is invalid or can't be parsed
        """
        # Auto-detect format if needed
        # Load file based on format
        # Apply environment overrides
        # Return merged configuration
        pass
    
    def save_config(self, config_name: str, config_data: Dict[str, Any], 
                   format: str = "yaml") -> bool:
        """
        Save configuration to file
        
        Args:
            config_name: Name for config file (without extension)
            config_data: Configuration dictionary to save
            format: File format - "yaml" or "json"
            
        Returns:
            True if saved successfully
        """
        # Validate config data
        # Create directory if needed
        # Save in specified format
        # Preserve formatting/structure
        pass
    
    def get_value(self, key: str, default: Any = None, 
                  config_name: Optional[str] = None) -> Any:
        """
        Get a configuration value with dot notation support
        
        Args:
            key: Configuration key (supports dot notation: "database.host")
            default: Default value if key not found
            config_name: Specific config to search (searches all if None)
            
        Returns:
            Configuration value or default
        """
        # Check environment first (RIKER_DATABASE_HOST)
        # Check loaded configs
        # Support nested access with dots
        # Return default if not found
        pass
    
    def set_value(self, key: str, value: Any, 
                  config_name: Optional[str] = None) -> bool:
        """
        Set a configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            config_name: Config to update (updates runtime only if None)
            
        Returns:
            True if set successfully
        """
        # Update runtime config
        # If config_name specified, update that file
        # Handle nested keys with dot notation
        pass
    
    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge multiple configuration dictionaries
        
        Args:
            *configs: Configuration dictionaries to merge (later overrides earlier)
            
        Returns:
            Merged configuration
        """
        # Implement deep merge
        # Later configs override earlier ones
        # Handle nested dictionaries properly
        pass
    
    def validate_config(self, config_data: Dict[str, Any], 
                       schema: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Validate configuration against schema
        
        Args:
            config_data: Configuration to validate
            schema: Validation schema (optional)
            
        Returns:
            List of validation errors (empty if valid)
        """
        # Basic type checking
        # Required fields validation
        # Format validation (if schema provided)
        # Return list of errors
        pass
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all loaded configurations
        
        Returns:
            Dictionary mapping config names to their data
        """
        # Return all loaded configs
        pass
    
    def reload_config(self, config_name: str) -> bool:
        """
        Reload a specific configuration from disk
        
        Args:
            config_name: Name of config to reload
            
        Returns:
            True if reloaded successfully
        """
        # Re-read from disk
        # Apply environment overrides
        # Update internal store
        pass
```

### 3. `config_loader.py`
Handles file loading and format detection:

```python
from pathlib import Path
from typing import Dict, Any, Optional
import json
import yaml

class ConfigLoader:
    """Handles loading configuration files in various formats"""
    
    @staticmethod
    def detect_format(file_path: Path) -> str:
        """Detect configuration file format from extension"""
        # Check file extension
        # Return "yaml", "json", or raise ValueError
        pass
    
    @staticmethod
    def load_yaml(file_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file"""
        # Load with safe loader
        # Handle YAML-specific features
        # Return parsed data
        pass
    
    @staticmethod
    def load_json(file_path: Path) -> Dict[str, Any]:
        """Load JSON configuration file"""
        # Load with proper encoding
        # Handle JSON-specific features
        # Return parsed data
        pass
    
    @staticmethod
    def save_yaml(file_path: Path, data: Dict[str, Any]) -> bool:
        """Save data as YAML with nice formatting"""
        # Save with proper formatting
        # Preserve order if possible
        # Handle special types
        pass
    
    @staticmethod
    def save_json(file_path: Path, data: Dict[str, Any]) -> bool:
        """Save data as JSON with nice formatting"""
        # Save with indentation
        # Handle non-serializable types
        # Preserve order if possible
        pass
```

### 4. `env_override.py`
Handles environment variable overrides:

```python
import os
from typing import Dict, Any, Optional

class EnvironmentOverride:
    """Handles environment variable overrides for configuration"""
    
    def __init__(self, prefix: str = "RIKER"):
        """Initialize with environment variable prefix"""
        self.prefix = prefix
    
    def get_env_overrides(self) -> Dict[str, Any]:
        """
        Get all environment overrides matching prefix
        
        Returns:
            Dictionary of overrides from environment
        """
        # Scan environment variables
        # Convert RIKER_DATABASE_HOST to database.host
        # Parse types (bool, int, float, string)
        # Return nested dictionary
        pass
    
    def apply_overrides(self, config: Dict[str, Any], 
                       overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment overrides to configuration"""
        # Deep merge overrides into config
        # Preserve original for non-overridden values
        # Return merged configuration
        pass
    
    def parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type"""
        # Try to parse as bool (true/false)
        # Try to parse as int
        # Try to parse as float
        # Default to string
        pass
```

### 5. `test_config_manager.py`
Comprehensive test suite:

```python
import pytest
import tempfile
from pathlib import Path
import os
import json
import yaml
from .plugin_interface import ConfigManager

def test_load_yaml_config(tmp_path):
    """Test loading YAML configuration"""
    # Create test YAML file
    config_data = {
        "database": {
            "host": "localhost",
            "port": 5432
        },
        "debug": True
    }
    
    config_file = tmp_path / "test.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    
    # Test loading
    manager = ConfigManager(config_dir=tmp_path)
    loaded = manager.load_config("test")
    
    assert loaded["database"]["host"] == "localhost"
    assert loaded["database"]["port"] == 5432
    assert loaded["debug"] is True

def test_load_json_config(tmp_path):
    """Test loading JSON configuration"""
    # Similar to YAML test but with JSON
    pass

def test_environment_override():
    """Test environment variable overrides"""
    # Set test environment variables
    os.environ["RIKER_DATABASE_HOST"] = "production.db"
    os.environ["RIKER_DATABASE_PORT"] = "3306"
    
    # Load config and verify overrides applied
    # Clean up environment
    pass

def test_get_value_dot_notation():
    """Test getting values with dot notation"""
    manager = ConfigManager()
    # Test nested access
    # Test missing keys
    # Test defaults
    pass

def test_merge_configs():
    """Test configuration merging"""
    # Test deep merge
    # Test override behavior
    # Test list handling
    pass

def test_save_config(tmp_path):
    """Test saving configurations"""
    # Test YAML save
    # Test JSON save
    # Test structure preservation
    pass

def test_validation():
    """Test configuration validation"""
    # Test type validation
    # Test required fields
    # Test custom schema
    pass

# Add more comprehensive tests...
```

## Example Usage

```python
# Initialize config manager
config = ConfigManager()

# Load main configuration
settings = config.load_config("settings")

# Get specific values with defaults
db_host = config.get_value("database.host", default="localhost")
db_port = config.get_value("database.port", default=5432)

# Environment override example
# If RIKER_DATABASE_HOST is set, it overrides the file value
actual_host = config.get_value("database.host")  # Returns env value if set

# Save updated configuration
settings["feature_flags"] = {"new_feature": True}
config.save_config("settings", settings)

# Merge multiple configs
base_config = config.load_config("base")
env_config = config.load_config("production")
merged = config.merge_configs(base_config, env_config)
```

## Configuration File Examples

### Example `config/settings.yaml`:
```yaml
# Riker main configuration
database:
  host: localhost
  port: 5432
  name: riker_db
  
redis:
  url: redis://localhost:6379
  
plugins:
  enabled:
    - memory_manager
    - github_integration
    - config_manager
    
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Example `config/development.json`:
```json
{
  "debug": true,
  "hot_reload": true,
  "database": {
    "host": "localhost",
    "port": 5432
  }
}
```

## Success Criteria

- [ ] Can load YAML and JSON configuration files
- [ ] Auto-detects file format from extension
- [ ] Environment variables override file values (RIKER_* prefix)
- [ ] Supports nested configuration with dot notation access
- [ ] Can save configurations preserving structure and formatting
- [ ] Deep merges multiple configuration sources correctly
- [ ] Provides helpful error messages for missing/invalid configs
- [ ] Handles type conversion for environment variables
- [ ] Validates configuration against optional schemas
- [ ] All tests pass with good coverage

## Dependencies

```txt
PyYAML==6.0.1
```

## Implementation Notes

1. **Environment Override Format**: `RIKER_SECTION_SUBSECTION_KEY` becomes `section.subsection.key`
2. **Type Detection**: Environment values "true"/"false" → bool, numeric strings → int/float
3. **File Organization**: Keep configs in a `config/` directory at project root
4. **Error Handling**: Always provide clear messages about what config is missing/invalid
5. **Performance**: Cache loaded configs, reload only when explicitly requested
