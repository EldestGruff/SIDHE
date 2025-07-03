from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import os
import json
import yaml
import logging
import copy
from dataclasses import dataclass

from .config_loader import ConfigLoader
from .env_override import EnvironmentOverride

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
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.env_override = EnvironmentOverride("RIKER")
        self.loader = ConfigLoader()
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        logger.info(f"ConfigManager initialized with config_dir: {self.config_dir}")
    
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
            
            logger.info(f"Loaded configuration '{config_name}' from {file_path}")
            return merged_config
            
        except Exception as e:
            logger.error(f"Failed to load config '{config_name}': {e}")
            raise
    
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
                logger.info(f"Saved configuration '{config_name}' to {file_path}")
                return True
            else:
                logger.error(f"Failed to save configuration '{config_name}' to {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving config '{config_name}': {e}")
            return False
    
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
        env_key = key.replace(".", "_").upper()
        env_value = os.getenv(f"RIKER_{env_key}")
        if env_value is not None:
            return self.env_override.parse_env_value(env_value)
        
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
                return value
        
        return default
    
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
        try:
            if config_name:
                # Update specific config
                if config_name not in self.configs:
                    self.configs[config_name] = {}
                
                self._set_nested_value(self.configs[config_name], key, value)
            else:
                # Update runtime config (create temporary runtime config)
                if "runtime" not in self.configs:
                    self.configs["runtime"] = {}
                
                self._set_nested_value(self.configs["runtime"], key, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting value '{key}': {e}")
            return False
    
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
    
    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge multiple configuration dictionaries
        
        Args:
            *configs: Configuration dictionaries to merge (later overrides earlier)
            
        Returns:
            Merged configuration
        """
        if not configs:
            return {}
        
        result = copy.deepcopy(configs[0])
        
        for config in configs[1:]:
            result = self._deep_merge(result, config)
        
        return result
    
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