from pathlib import Path
from typing import Dict, Any, Optional
import json
import yaml
import logging

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Handles loading configuration files in various formats"""
    
    @staticmethod
    def detect_format(file_path: Path) -> str:
        """
        Detect configuration file format from extension
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Format string: "yaml" or "json"
            
        Raises:
            ValueError: If format cannot be determined
        """
        suffix = file_path.suffix.lower()
        
        if suffix in ['.yaml', '.yml']:
            return "yaml"
        elif suffix == '.json':
            return "json"
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Supported formats: .yaml, .yml, .json")
    
    @staticmethod
    def load_yaml(file_path: Path) -> Dict[str, Any]:
        """
        Load YAML configuration file
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Parsed configuration data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
                # Handle empty files
                if data is None:
                    return {}
                
                if not isinstance(data, dict):
                    raise ValueError(f"YAML file must contain a dictionary, got {type(data).__name__}")
                
                logger.debug(f"Successfully loaded YAML from {file_path}")
                return data
                
        except FileNotFoundError:
            logger.error(f"YAML file not found: {file_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {file_path}: {e}")
            raise ValueError(f"Invalid YAML format in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading YAML from {file_path}: {e}")
            raise
    
    @staticmethod
    def load_json(file_path: Path) -> Dict[str, Any]:
        """
        Load JSON configuration file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed configuration data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if not isinstance(data, dict):
                    raise ValueError(f"JSON file must contain an object, got {type(data).__name__}")
                
                logger.debug(f"Successfully loaded JSON from {file_path}")
                return data
                
        except FileNotFoundError:
            logger.error(f"JSON file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            raise ValueError(f"Invalid JSON format in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {e}")
            raise
    
    @staticmethod
    def save_yaml(file_path: Path, data: Dict[str, Any]) -> bool:
        """
        Save data as YAML with nice formatting
        
        Args:
            file_path: Path where to save the file
            data: Dictionary to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    indent=2,
                    sort_keys=False,
                    allow_unicode=True,
                    width=120
                )
            
            logger.debug(f"Successfully saved YAML to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving YAML to {file_path}: {e}")
            return False
    
    @staticmethod
    def save_json(file_path: Path, data: Dict[str, Any]) -> bool:
        """
        Save data as JSON with nice formatting
        
        Args:
            file_path: Path where to save the file
            data: Dictionary to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    ensure_ascii=False,
                    separators=(',', ': '),
                    sort_keys=False
                )
            
            logger.debug(f"Successfully saved JSON to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {e}")
            return False