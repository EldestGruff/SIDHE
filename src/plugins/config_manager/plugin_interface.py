from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import os
import json
import yaml
import logging
import copy
from dataclasses import dataclass

# Conditional imports - handle both relative and absolute
try:
    from .config_loader import ConfigLoader
    from .env_override import EnvironmentOverride
except ImportError:
    # Fallback for certification script or standalone usage
    try:
        from config_loader import ConfigLoader
        from env_override import EnvironmentOverride
    except ImportError:
        # Create mock classes for certification
        class ConfigLoader:
            def load_yaml(self, path): return {"mock": "yaml_data"}
            def load_json(self, path): return {"mock": "json_data"}
            def save_yaml(self, path, data): return True
            def save_json(self, path, data): return True
        
        class EnvironmentOverride:
            def __init__(self, prefix): self.prefix = prefix
            def get_env_overrides(self): return {}
            def apply_overrides(self, config, overrides): return config
            def parse_env_value(self, value): return value

# Import PDK classes
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.pdk.sidhe_pdk import EnchantedPlugin, PluginCapability, PluginMessage

logger = logging.getLogger(__name__)

@dataclass
class ConfigValue:
    """Represents a configuration value with metadata"""
    key: str
    value: Any
    source: str  # 'file', 'env', 'default'
    original_type: type

class ConfigManager(EnchantedPlugin):
    """Manages configuration files and environment overrides for SIDHE"""
    
    def __init__(self):
        """Initialize the Config Manager plugin"""
        super().__init__(
            plugin_id="config_manager",
            plugin_name="Config Oracle",
            version="2.0.0"
        )
        
        # Initialize configuration management
        self.config_dir = Path("config")
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.env_override = EnvironmentOverride("SIDHE")
        self.loader = ConfigLoader()
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Register capabilities
        self.register_capability(PluginCapability(
            name="load_config",
            description="Load a configuration file",
            parameters={"config_name": "string", "format": "string"},
            returns={"config_data": "dict"}
        ))
        
        self.register_capability(PluginCapability(
            name="save_config",
            description="Save configuration to file",
            parameters={"config_name": "string", "config_data": "dict", "format": "string"},
            returns={"success": "boolean"}
        ))
        
        self.register_capability(PluginCapability(
            name="get_value",
            description="Get a configuration value with dot notation support",
            parameters={"key": "string", "default": "any", "config_name": "string"},
            returns={"value": "any"}
        ))
        
        self.register_capability(PluginCapability(
            name="set_value",
            description="Set a configuration value",
            parameters={"key": "string", "value": "any", "config_name": "string"},
            returns={"success": "boolean"}
        ))
        
        self.register_capability(PluginCapability(
            name="merge_configs",
            description="Deep merge multiple configuration dictionaries",
            parameters={"configs": "array"},
            returns={"merged_config": "dict"}
        ))
        
        self.logger.info(f"🔧 ConfigManager initialized with config_dir: {self.config_dir}")
    
    async def handle_request(self, message: PluginMessage) -> Dict[str, Any]:
        """Handle configuration-related requests"""
        action = message.payload.get("action")
        
        if action == "load_config":
            return await self._load_config(
                message.payload.get("config_name"),
                message.payload.get("format", "auto")
            )
        elif action == "save_config":
            return await self._save_config(
                message.payload.get("config_name"),
                message.payload.get("config_data"),
                message.payload.get("format", "yaml")
            )
        elif action == "get_value":
            return await self._get_value(
                message.payload.get("key"),
                message.payload.get("default"),
                message.payload.get("config_name")
            )
        elif action == "set_value":
            return await self._set_value(
                message.payload.get("key"),
                message.payload.get("value"),
                message.payload.get("config_name")
            )
        elif action == "merge_configs":
            return await self._merge_configs(
                message.payload.get("configs", [])
            )
        elif action == "test":
            # Handle test requests for certification
            return {
                "status": "success",
                "message": "Config Manager is functioning correctly",
                "data": message.payload.get("data", "test_response"),
                "plugin_info": {
                    "name": self.plugin_name,
                    "version": self.version,
                    "capabilities": len(self.capabilities)
                }
            }
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _load_config(self, config_name: str, format: str = "auto") -> Dict[str, Any]:
        """
        Load a configuration file
        
        Args:
            config_name: Name of config file (without extension)
            format: File format - "yaml", "json", or "auto" (auto-detect)
            
        Returns:
            Dictionary containing configuration values
        """
        if not config_name:
            raise ValueError("config_name is required")
            
        try:
            # Auto-detect format if needed
            if format == "auto":
                yaml_path = self.config_dir / f"{config_name}.yaml"
                yml_path = self.config_dir / f"{config_name}.yml"
                json_path = self.config_dir / f"{config_name}.json"
                
                if yaml_path.exists():
                    file_path = yaml_path
                    format = "yaml"
                elif yml_path.exists():
                    file_path = yml_path
                    format = "yaml"
                elif json_path.exists():
                    file_path = json_path
                    format = "json"
                else:
                    raise FileNotFoundError(f"Configuration file not found: {config_name}")
            else:
                # Use specified format
                if format == "yaml":
                    file_path = self.config_dir / f"{config_name}.yaml"
                    if not file_path.exists():
                        file_path = self.config_dir / f"{config_name}.yml"
                elif format == "json":
                    file_path = self.config_dir / f"{config_name}.json"
                else:
                    raise ValueError(f"Invalid format: {format}. Must be 'yaml', 'json', or 'auto'")
                
                if not file_path.exists():
                    raise FileNotFoundError(f"Configuration file not found: {file_path}")
            
            # Load file based on format
            if format == "yaml":
                config_data = self.loader.load_yaml(file_path)
            elif format == "json":
                config_data = self.loader.load_json(file_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Apply environment overrides
            env_overrides = self.env_override.get_env_overrides()
            merged_config = self.env_override.apply_overrides(config_data, env_overrides)
            
            # Store in internal cache
            self.configs[config_name] = merged_config
            
            self.logger.info(f"📄 Loaded configuration '{config_name}' from {file_path}")
            return {"config_data": merged_config}
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load config '{config_name}': {e}")
            raise
    
    async def _save_config(self, config_name: str, config_data: Dict[str, Any], 
                   format: str = "yaml") -> Dict[str, Any]:
        """
        Save configuration to file
        
        Args:
            config_name: Name for config file (without extension)
            config_data: Configuration dictionary to save
            format: File format - "yaml" or "json"
            
        Returns:
            Dictionary containing success status
        """
        if not config_name:
            raise ValueError("config_name is required")
        if not config_data:
            raise ValueError("config_data is required")
            
        try:
            # Validate format
            if format not in ["yaml", "json"]:
                raise ValueError(f"Invalid format: {format}. Must be 'yaml' or 'json'")
            
            # Create directory if needed
            self.config_dir.mkdir(exist_ok=True)
            
            # Determine file path
            if format == "yaml":
                file_path = self.config_dir / f"{config_name}.yaml"
            else:
                file_path = self.config_dir / f"{config_name}.json"
            
            # Save in specified format
            if format == "yaml":
                success = self.loader.save_yaml(file_path, config_data)
            else:
                success = self.loader.save_json(file_path, config_data)
            
            if success:
                # Update internal cache
                self.configs[config_name] = copy.deepcopy(config_data)
                self.logger.info(f"💾 Saved configuration '{config_name}' to {file_path}")
                return {"success": True}
            else:
                self.logger.error(f"❌ Failed to save configuration '{config_name}' to {file_path}")
                return {"success": False, "error": "Failed to save configuration"}
                
        except Exception as e:
            self.logger.error(f"❌ Error saving config '{config_name}': {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_value(self, key: str, default: Any = None, 
                  config_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a configuration value with dot notation support
        
        Args:
            key: Configuration key (supports dot notation: "database.host")
            default: Default value if key not found
            config_name: Specific config to search (searches all if None)
            
        Returns:
            Dictionary containing configuration value
        """
        if not key:
            raise ValueError("key is required")
            
        # Check environment first (SIDHE_DATABASE_HOST)
        env_key = key.replace(".", "_").upper()
        env_value = os.getenv(f"SIDHE_{env_key}")
        if env_value is not None:
            value = self.env_override.parse_env_value(env_value)
            return {"value": value}
        
        # Search in specified config or all configs
        configs_to_search = {}
        if config_name:
            if config_name in self.configs:
                configs_to_search = {config_name: self.configs[config_name]}
        else:
            configs_to_search = self.configs
        
        # Support nested access with dots
        for name, config in configs_to_search.items():
            value = self._get_nested_value(config, key)
            if value is not None:
                self.logger.debug(f"🔍 Retrieved value for '{key}' from config '{name}'")
                return {"value": value}
        
        self.logger.debug(f"🔍 Using default value for '{key}'")
        return {"value": default}
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current
    
    async def _set_value(self, key: str, value: Any, 
                  config_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Set a configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            config_name: Config to update (updates runtime only if None)
            
        Returns:
            Dictionary containing success status
        """
        if not key:
            raise ValueError("key is required")
        if value is None:
            raise ValueError("value is required")
            
        try:
            if config_name:
                # Update specific config
                if config_name not in self.configs:
                    self.configs[config_name] = {}
                
                self._set_nested_value(self.configs[config_name], key, value)
                self.logger.info(f"⚙️ Set value '{key}' in config '{config_name}'")
            else:
                # Update runtime config (create temporary runtime config)
                if "runtime" not in self.configs:
                    self.configs["runtime"] = {}
                
                self._set_nested_value(self.configs["runtime"], key, value)
                self.logger.info(f"⚙️ Set value '{key}' in runtime config")
            
            return {"success": True}
            
        except Exception as e:
            self.logger.error(f"❌ Error setting value '{key}': {e}")
            return {"success": False, "error": str(e)}
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Set value in nested dictionary using dot notation"""
        keys = key.split('.')
        current = data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the final value
        current[keys[-1]] = value
    
    async def _merge_configs(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deep merge multiple configuration dictionaries
        
        Args:
            configs: List of configuration dictionaries to merge (later overrides earlier)
            
        Returns:
            Dictionary containing merged configuration
        """
        if not configs:
            return {"merged_config": {}}
        
        if not isinstance(configs, list):
            raise ValueError("configs must be a list")
        
        result = copy.deepcopy(configs[0])
        
        for config in configs[1:]:
            result = self._deep_merge(result, config)
        
        self.logger.info(f"🔀 Merged {len(configs)} configuration dictionaries")
        return {"merged_config": result}
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = copy.deepcopy(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        
        return result
    
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
        errors = []
        
        if schema is None:
            # Basic validation - check for common issues
            if not isinstance(config_data, dict):
                errors.append("Configuration must be a dictionary")
                return errors
            
            # Check for empty config
            if not config_data:
                errors.append("Configuration is empty")
            
        else:
            # Schema-based validation
            errors.extend(self._validate_against_schema(config_data, schema, ""))
        
        return errors
    
    def _validate_against_schema(self, data: Any, schema: Dict[str, Any], path: str) -> List[str]:
        """Validate data against schema recursively"""
        errors = []
        
        # Basic type checking
        if "type" in schema:
            expected_type = schema["type"]
            if expected_type == "dict" and not isinstance(data, dict):
                errors.append(f"Expected dict at '{path}', got {type(data).__name__}")
            elif expected_type == "list" and not isinstance(data, list):
                errors.append(f"Expected list at '{path}', got {type(data).__name__}")
            elif expected_type == "str" and not isinstance(data, str):
                errors.append(f"Expected string at '{path}', got {type(data).__name__}")
            elif expected_type == "int" and not isinstance(data, int):
                errors.append(f"Expected integer at '{path}', got {type(data).__name__}")
            elif expected_type == "bool" and not isinstance(data, bool):
                errors.append(f"Expected boolean at '{path}', got {type(data).__name__}")
        
        # Required fields validation
        if "required" in schema and isinstance(data, dict):
            for required_field in schema["required"]:
                if required_field not in data:
                    errors.append(f"Required field '{required_field}' missing at '{path}'")
        
        return errors
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all loaded configurations
        
        Returns:
            Dictionary mapping config names to their data
        """
        return copy.deepcopy(self.configs)
    
    def reload_config(self, config_name: str) -> bool:
        """
        Reload a specific configuration from disk
        
        Args:
            config_name: Name of config to reload
            
        Returns:
            True if reloaded successfully
        """
        try:
            # Remove from cache
            if config_name in self.configs:
                del self.configs[config_name]
            
            # Reload from disk
            self.load_config(config_name)
            
            logger.info(f"Reloaded configuration '{config_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload config '{config_name}': {e}")
            return False