import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from .plugin_interface import ConfigManager, ConfigValue
from .config_loader import ConfigLoader
from .env_override import EnvironmentOverride


class TestConfigLoader:
    """Test the ConfigLoader class"""
    
    def test_detect_format_yaml(self):
        """Test format detection for YAML files"""
        loader = ConfigLoader()
        
        assert loader.detect_format(Path("config.yaml")) == "yaml"
        assert loader.detect_format(Path("config.yml")) == "yaml"
        assert loader.detect_format(Path("CONFIG.YAML")) == "yaml"
    
    def test_detect_format_json(self):
        """Test format detection for JSON files"""
        loader = ConfigLoader()
        
        assert loader.detect_format(Path("config.json")) == "json"
        assert loader.detect_format(Path("CONFIG.JSON")) == "json"
    
    def test_detect_format_unsupported(self):
        """Test format detection for unsupported files"""
        loader = ConfigLoader()
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            loader.detect_format(Path("config.txt"))
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_yaml_success(self, mock_yaml_load, mock_file):
        """Test successful YAML loading"""
        mock_yaml_load.return_value = {"database": {"host": "localhost", "port": 5432}, "debug": True}
        
        loader = ConfigLoader()
        result = loader.load_yaml(Path("test.yaml"))
        
        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == 5432
        assert result["debug"] is True
        mock_file.assert_called_once_with(Path("test.yaml"), 'r', encoding='utf-8')
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_yaml_empty_file(self, mock_yaml_load, mock_file):
        """Test loading empty YAML file"""
        mock_yaml_load.return_value = None
        
        loader = ConfigLoader()
        result = loader.load_yaml(Path("empty.yaml"))
        
        assert result == {}
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_yaml_invalid_structure(self, mock_yaml_load, mock_file):
        """Test loading YAML with invalid structure"""
        mock_yaml_load.return_value = ["not", "a", "dict"]
        
        loader = ConfigLoader()
        
        with pytest.raises(ValueError, match="YAML file must contain a dictionary"):
            loader.load_yaml(Path("invalid.yaml"))
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_load_json_success(self, mock_json_load, mock_file):
        """Test successful JSON loading"""
        mock_json_load.return_value = {"api": {"key": "secret", "timeout": 30}}
        
        loader = ConfigLoader()
        result = loader.load_json(Path("test.json"))
        
        assert result["api"]["key"] == "secret"
        assert result["api"]["timeout"] == 30
        mock_file.assert_called_once_with(Path("test.json"), 'r', encoding='utf-8')
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.dump")
    def test_save_yaml_success(self, mock_yaml_dump, mock_file):
        """Test successful YAML saving"""
        loader = ConfigLoader()
        test_data = {"database": {"host": "localhost"}}
        
        result = loader.save_yaml(Path("test.yaml"), test_data)
        
        assert result is True
        mock_file.assert_called_once_with(Path("test.yaml"), 'w', encoding='utf-8')
        mock_yaml_dump.assert_called_once()
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_json_success(self, mock_json_dump, mock_file):
        """Test successful JSON saving"""
        loader = ConfigLoader()
        test_data = {"api": {"timeout": 30}}
        
        result = loader.save_json(Path("test.json"), test_data)
        
        assert result is True
        mock_file.assert_called_once_with(Path("test.json"), 'w', encoding='utf-8')
        mock_json_dump.assert_called_once()


class TestEnvironmentOverride:
    """Test the EnvironmentOverride class"""
    
    def setup_method(self):
        """Set up test environment"""
        self.env_override = EnvironmentOverride("TEST")
        # Clean up any existing TEST_ environment variables
        for key in list(os.environ.keys()):
            if key.startswith("TEST_"):
                del os.environ[key]
    
    def teardown_method(self):
        """Clean up test environment"""
        for key in list(os.environ.keys()):
            if key.startswith("TEST_"):
                del os.environ[key]
    
    def test_parse_env_value_boolean(self):
        """Test parsing boolean values from environment"""
        assert self.env_override.parse_env_value("true") is True
        assert self.env_override.parse_env_value("True") is True
        assert self.env_override.parse_env_value("TRUE") is True
        assert self.env_override.parse_env_value("yes") is True
        assert self.env_override.parse_env_value("1") is True
        
        assert self.env_override.parse_env_value("false") is False
        assert self.env_override.parse_env_value("False") is False
        assert self.env_override.parse_env_value("no") is False
        assert self.env_override.parse_env_value("0") is False
    
    def test_parse_env_value_numeric(self):
        """Test parsing numeric values from environment"""
        assert self.env_override.parse_env_value("42") == 42
        assert self.env_override.parse_env_value("-17") == -17
        assert self.env_override.parse_env_value("3.14") == 3.14
        assert self.env_override.parse_env_value("-2.5") == -2.5
    
    def test_parse_env_value_string(self):
        """Test parsing string values from environment"""
        assert self.env_override.parse_env_value("hello") == "hello"
        assert self.env_override.parse_env_value("localhost") == "localhost"
        assert self.env_override.parse_env_value("") == ""
    
    def test_parse_env_value_special(self):
        """Test parsing special values from environment"""
        assert self.env_override.parse_env_value("null") is None
        assert self.env_override.parse_env_value("none") is None
        assert self.env_override.parse_env_value("None") is None
    
    def test_get_env_overrides(self):
        """Test getting environment overrides"""
        os.environ["TEST_DATABASE_HOST"] = "production.db"
        os.environ["TEST_DATABASE_PORT"] = "3306"
        os.environ["TEST_DEBUG"] = "true"
        
        overrides = self.env_override.get_env_overrides()
        
        assert overrides["database"]["host"] == "production.db"
        assert overrides["database"]["port"] == 3306
        assert overrides["debug"] is True
    
    def test_apply_overrides(self):
        """Test applying environment overrides to configuration"""
        base_config = {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "debug": False
        }
        
        overrides = {
            "database": {
                "host": "production.db"
            },
            "debug": True
        }
        
        result = self.env_override.apply_overrides(base_config, overrides)
        
        assert result["database"]["host"] == "production.db"
        assert result["database"]["port"] == 5432  # Preserved from base
        assert result["debug"] is True
        
        # Original should be unchanged
        assert base_config["database"]["host"] == "localhost"
    
    def test_get_env_value(self):
        """Test getting specific environment value"""
        os.environ["TEST_API_KEY"] = "secret123"
        
        value = self.env_override.get_env_value("api.key")
        assert value == "secret123"
        
        value = self.env_override.get_env_value("nonexistent.key")
        assert value is None


class TestConfigManager:
    """Test the ConfigManager class"""
    
    def setup_method(self):
        """Set up test environment"""
        # Create temporary directory for config files
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = ConfigManager(config_dir=self.temp_dir)
        
        # Clean up environment variables
        for key in list(os.environ.keys()):
            if key.startswith("RIKER_"):
                del os.environ[key]
    
    def teardown_method(self):
        """Clean up test environment"""
        # Clean up environment variables
        for key in list(os.environ.keys()):
            if key.startswith("RIKER_"):
                del os.environ[key]
    
    @patch.object(ConfigLoader, 'load_yaml')
    def test_load_config_yaml_auto_detect(self, mock_load_yaml):
        """Test loading YAML config with auto-detection"""
        # Create fake YAML file
        yaml_file = self.temp_dir / "settings.yaml"
        yaml_file.touch()
        
        mock_load_yaml.return_value = {
            "database": {"host": "localhost", "port": 5432},
            "debug": True
        }
        
        result = self.config_manager.load_config("settings")
        
        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == 5432
        assert result["debug"] is True
        mock_load_yaml.assert_called_once_with(yaml_file)
    
    @patch.object(ConfigLoader, 'load_json')
    def test_load_config_json_auto_detect(self, mock_load_json):
        """Test loading JSON config with auto-detection"""
        # Create fake JSON file
        json_file = self.temp_dir / "settings.json"
        json_file.touch()
        
        mock_load_json.return_value = {
            "api": {"timeout": 30},
            "cache": {"enabled": False}
        }
        
        result = self.config_manager.load_config("settings")
        
        assert result["api"]["timeout"] == 30
        assert result["cache"]["enabled"] is False
        mock_load_json.assert_called_once_with(json_file)
    
    def test_load_config_file_not_found(self):
        """Test loading non-existent config file"""
        with pytest.raises(FileNotFoundError):
            self.config_manager.load_config("nonexistent")
    
    @patch.object(ConfigLoader, 'load_yaml')
    def test_load_config_with_env_overrides(self, mock_load_yaml):
        """Test loading config with environment variable overrides"""
        # Create fake YAML file
        yaml_file = self.temp_dir / "settings.yaml"
        yaml_file.touch()
        
        mock_load_yaml.return_value = {
            "database": {"host": "localhost", "port": 5432}
        }
        
        # Set environment override
        os.environ["RIKER_DATABASE_HOST"] = "production.db"
        
        result = self.config_manager.load_config("settings")
        
        assert result["database"]["host"] == "production.db"
        assert result["database"]["port"] == 5432
    
    @patch.object(ConfigLoader, 'save_yaml')
    def test_save_config_yaml(self, mock_save_yaml):
        """Test saving config as YAML"""
        mock_save_yaml.return_value = True
        
        test_data = {"database": {"host": "localhost"}}
        result = self.config_manager.save_config("test", test_data, "yaml")
        
        assert result is True
        mock_save_yaml.assert_called_once()
    
    @patch.object(ConfigLoader, 'save_json')
    def test_save_config_json(self, mock_save_json):
        """Test saving config as JSON"""
        mock_save_json.return_value = True
        
        test_data = {"api": {"timeout": 30}}
        result = self.config_manager.save_config("test", test_data, "json")
        
        assert result is True
        mock_save_json.assert_called_once()
    
    def test_get_value_dot_notation(self):
        """Test getting values with dot notation"""
        # Manually set up config data
        self.config_manager.configs["test"] = {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "debug": True
        }
        
        assert self.config_manager.get_value("database.host", config_name="test") == "localhost"
        assert self.config_manager.get_value("database.port", config_name="test") == 5432
        assert self.config_manager.get_value("debug", config_name="test") is True
        assert self.config_manager.get_value("nonexistent.key", default="default") == "default"
    
    def test_get_value_env_override(self):
        """Test getting values with environment override"""
        self.config_manager.configs["test"] = {
            "database": {"host": "localhost"}
        }
        
        os.environ["RIKER_DATABASE_HOST"] = "override.db"
        
        # Environment should take precedence
        assert self.config_manager.get_value("database.host") == "override.db"
    
    def test_set_value_runtime(self):
        """Test setting runtime values"""
        result = self.config_manager.set_value("new.key", "value")
        
        assert result is True
        assert self.config_manager.get_value("new.key") == "value"
    
    def test_set_value_specific_config(self):
        """Test setting values in specific config"""
        self.config_manager.configs["test"] = {}
        
        result = self.config_manager.set_value("database.host", "newhost", config_name="test")
        
        assert result is True
        assert self.config_manager.configs["test"]["database"]["host"] == "newhost"
    
    def test_merge_configs(self):
        """Test configuration merging"""
        base_config = {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "debug": False
        }
        
        override_config = {
            "database": {
                "host": "production.db"
            },
            "cache": {
                "enabled": True
            }
        }
        
        result = self.config_manager.merge_configs(base_config, override_config)
        
        # Should merge nested structures
        assert result["database"]["host"] == "production.db"
        assert result["database"]["port"] == 5432  # Preserved from base
        assert result["debug"] is False
        assert result["cache"]["enabled"] is True
    
    def test_validate_config_basic(self):
        """Test basic configuration validation"""
        valid_config = {"key": "value"}
        errors = self.config_manager.validate_config(valid_config)
        assert errors == []
        
        invalid_config = "not a dict"
        errors = self.config_manager.validate_config(invalid_config)
        assert len(errors) > 0
        assert "must be a dictionary" in errors[0]
    
    def test_validate_config_with_schema(self):
        """Test configuration validation with schema"""
        config = {"name": "test", "count": 42}
        schema = {
            "required": ["name", "count"],
            "type": "dict"
        }
        
        errors = self.config_manager.validate_config(config, schema)
        assert errors == []
        
        # Test missing required field
        incomplete_config = {"name": "test"}
        errors = self.config_manager.validate_config(incomplete_config, schema)
        assert len(errors) > 0
        assert "Required field 'count' missing" in errors[0]
    
    def test_get_all_configs(self):
        """Test getting all loaded configurations"""
        self.config_manager.configs["config1"] = {"key1": "value1"}
        self.config_manager.configs["config2"] = {"key2": "value2"}
        
        all_configs = self.config_manager.get_all_configs()
        
        assert "config1" in all_configs
        assert "config2" in all_configs
        assert all_configs["config1"]["key1"] == "value1"
        assert all_configs["config2"]["key2"] == "value2"
        
        # Should be a copy, not reference
        all_configs["config1"]["key1"] = "modified"
        assert self.config_manager.configs["config1"]["key1"] == "value1"
    
    @patch.object(ConfigManager, 'load_config')
    def test_reload_config(self, mock_load_config):
        """Test reloading configuration"""
        # Set up existing config
        self.config_manager.configs["test"] = {"old": "value"}
        
        mock_load_config.return_value = {"new": "value"}
        
        result = self.config_manager.reload_config("test")
        
        assert result is True
        mock_load_config.assert_called_once_with("test")


class TestConfigIntegration:
    """Integration tests for the complete config management system"""
    
    def setup_method(self):
        """Set up integration test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = ConfigManager(config_dir=self.temp_dir)
        
        # Clean up environment
        for key in list(os.environ.keys()):
            if key.startswith("RIKER_"):
                del os.environ[key]
    
    def teardown_method(self):
        """Clean up integration test environment"""
        for key in list(os.environ.keys()):
            if key.startswith("RIKER_"):
                del os.environ[key]
    
    def test_full_yaml_workflow(self):
        """Test complete YAML workflow: save, load, override"""
        # Create test configuration
        config_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "testdb"
            },
            "debug": True,
            "features": {
                "cache": {"enabled": False},
                "logging": {"level": "INFO"}
            }
        }
        
        # Save configuration
        success = self.config_manager.save_config("integration_test", config_data, "yaml")
        assert success is True
        
        # Verify file exists
        config_file = self.temp_dir / "integration_test.yaml"
        assert config_file.exists()
        
        # Load configuration
        loaded_config = self.config_manager.load_config("integration_test")
        assert loaded_config["database"]["host"] == "localhost"
        assert loaded_config["features"]["cache"]["enabled"] is False
        
        # Test environment override
        os.environ["RIKER_DATABASE_HOST"] = "production.example.com"
        os.environ["RIKER_FEATURES_CACHE_ENABLED"] = "true"
        
        # Reload with overrides
        reloaded_config = self.config_manager.load_config("integration_test")
        assert reloaded_config["database"]["host"] == "production.example.com"
        assert reloaded_config["database"]["port"] == 5432  # Original value preserved
        assert reloaded_config["features"]["cache"]["enabled"] is True
        
        # Test dot notation access
        assert self.config_manager.get_value("database.host") == "production.example.com"
        assert self.config_manager.get_value("features.logging.level") == "INFO"
    
    def test_full_json_workflow(self):
        """Test complete JSON workflow"""
        config_data = {
            "api": {
                "base_url": "https://api.example.com",
                "timeout": 30,
                "retries": 3
            },
            "auth": {
                "method": "token",
                "expires": 3600
            }
        }
        
        # Save as JSON
        success = self.config_manager.save_config("api_config", config_data, "json")
        assert success is True
        
        # Load and verify
        loaded_config = self.config_manager.load_config("api_config")
        assert loaded_config["api"]["base_url"] == "https://api.example.com"
        assert loaded_config["auth"]["method"] == "token"
        
        # Test value modification
        self.config_manager.set_value("api.timeout", 60, config_name="api_config")
        assert self.config_manager.configs["api_config"]["api"]["timeout"] == 60
    
    def test_config_merging_workflow(self):
        """Test configuration merging across multiple sources"""
        # Base configuration
        base_config = {
            "database": {"host": "localhost", "port": 5432},
            "cache": {"ttl": 300},
            "features": {"feature_a": True, "feature_b": False}
        }
        
        # Environment-specific overrides
        prod_config = {
            "database": {"host": "prod.example.com"},
            "cache": {"ttl": 600},
            "features": {"feature_b": True}
        }
        
        # Local development overrides
        dev_config = {
            "database": {"port": 5433},
            "debug": True
        }
        
        # Test merging
        merged = self.config_manager.merge_configs(base_config, prod_config, dev_config)
        
        # Verify merge results
        assert merged["database"]["host"] == "prod.example.com"  # From prod_config
        assert merged["database"]["port"] == 5433  # From dev_config
        assert merged["cache"]["ttl"] == 600  # From prod_config
        assert merged["features"]["feature_a"] is True  # From base_config
        assert merged["features"]["feature_b"] is True  # From prod_config
        assert merged["debug"] is True  # From dev_config


if __name__ == '__main__':
    pytest.main([__file__])