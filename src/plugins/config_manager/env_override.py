import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class EnvironmentOverride:
    """Handles environment variable overrides for configuration"""
    
    def __init__(self, prefix: str = "RIKER"):
        """
        Initialize with environment variable prefix
        
        Args:
            prefix: Prefix for environment variables (e.g., "RIKER")
        """
        self.prefix = prefix.upper()
        logger.debug(f"EnvironmentOverride initialized with prefix: {self.prefix}")
    
    def get_env_overrides(self) -> Dict[str, Any]:
        """
        Get all environment overrides matching prefix
        
        Returns:
            Dictionary of overrides from environment variables
        """
        overrides = {}
        prefix_with_underscore = f"{self.prefix}_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix_with_underscore):
                # Remove prefix and convert to nested structure
                config_key = key[len(prefix_with_underscore):].lower()
                nested_key = config_key.replace('_', '.')
                
                # Parse the value to appropriate type
                parsed_value = self.parse_env_value(value)
                
                # Set nested value in overrides dict
                self._set_nested_override(overrides, nested_key, parsed_value)
                
                logger.debug(f"Environment override: {nested_key} = {parsed_value} (from {key})")
        
        return overrides
    
    def _set_nested_override(self, overrides: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested value in overrides dictionary using dot notation"""
        keys = key.split('.')
        current = overrides
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                # If there's a conflict, convert to dict
                logger.warning(f"Converting non-dict value to dict for key '{k}' due to nested override")
                current[k] = {}
            current = current[k]
        
        # Set the final value
        current[keys[-1]] = value
    
    def apply_overrides(self, config: Dict[str, Any], 
                       overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment overrides to configuration
        
        Args:
            config: Base configuration dictionary
            overrides: Override values from environment
            
        Returns:
            Merged configuration with overrides applied
        """
        # Create a deep copy to avoid modifying original
        result = self._deep_copy(config)
        
        # Apply overrides using deep merge
        self._deep_merge_overrides(result, overrides)
        
        return result
    
    def _deep_copy(self, obj: Any) -> Any:
        """Create a deep copy of an object"""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj
    
    def _deep_merge_overrides(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source into target (modifies target in place)"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                self._deep_merge_overrides(target[key], value)
            else:
                # Override the value
                target[key] = value
                logger.debug(f"Applied override: {key} = {value}")
    
    def parse_env_value(self, value: str) -> Any:
        """
        Parse environment variable value to appropriate type
        
        Args:
            value: String value from environment variable
            
        Returns:
            Parsed value with appropriate type
        """
        # Handle empty values
        if not value:
            return ""
        
        # Try to parse as boolean (case-insensitive)
        value_lower = value.lower()
        if value_lower in ['true', 'yes', 'on', '1']:
            return True
        elif value_lower in ['false', 'no', 'off', '0']:
            return False
        
        # Try to parse as integer
        try:
            # Check if it looks like an integer (no decimal point)
            if '.' not in value and value.lstrip('-').isdigit():
                return int(value)
        except ValueError:
            pass
        
        # Try to parse as float
        try:
            # Only if it contains a decimal point
            if '.' in value:
                return float(value)
        except ValueError:
            pass
        
        # Handle special string values
        if value_lower == 'null' or value_lower == 'none':
            return None
        
        # Default to string
        return value
    
    def get_env_value(self, key: str) -> Optional[Any]:
        """
        Get a specific environment variable value for a config key
        
        Args:
            key: Configuration key in dot notation (e.g., "database.host")
            
        Returns:
            Parsed environment variable value or None if not set
        """
        env_key = f"{self.prefix}_{key.replace('.', '_').upper()}"
        env_value = os.getenv(env_key)
        
        if env_value is not None:
            parsed_value = self.parse_env_value(env_value)
            logger.debug(f"Environment value for {key}: {parsed_value} (from {env_key})")
            return parsed_value
        
        return None
    
    def set_env_value(self, key: str, value: Any) -> None:
        """
        Set an environment variable for a config key (for testing purposes)
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        env_key = f"{self.prefix}_{key.replace('.', '_').upper()}"
        
        # Convert value to string for environment variable
        if isinstance(value, bool):
            env_value = 'true' if value else 'false'
        elif value is None:
            env_value = 'null'
        else:
            env_value = str(value)
        
        os.environ[env_key] = env_value
        logger.debug(f"Set environment variable {env_key} = {env_value}")
    
    def clear_env_overrides(self) -> None:
        """Clear all environment variables with the configured prefix (for testing)"""
        prefix_with_underscore = f"{self.prefix}_"
        keys_to_remove = [key for key in os.environ.keys() if key.startswith(prefix_with_underscore)]
        
        for key in keys_to_remove:
            del os.environ[key]
            logger.debug(f"Removed environment variable: {key}")
    
    def list_env_overrides(self) -> Dict[str, str]:
        """
        List all current environment overrides
        
        Returns:
            Dictionary of environment variable names to their raw string values
        """
        overrides = {}
        prefix_with_underscore = f"{self.prefix}_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix_with_underscore):
                overrides[key] = value
        
        return overrides