"""
Test suite for Plugin Registry
Tests plugin discovery, health monitoring, and management
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from plugins.registry import PluginRegistry

class TestPluginRegistry:
    """Test plugin registry functionality"""
    
    @pytest.fixture
    def plugin_registry(self):
        """Create plugin registry instance"""
        return PluginRegistry()
    
    @pytest.fixture
    def mock_plugin_instance(self):
        """Mock plugin instance"""
        instance = MagicMock()
        instance.health_check = MagicMock(return_value="enchanted")
        return instance
    
    @pytest.mark.asyncio
    async def test_discover_plugins_success(self, plugin_registry):
        """Test successful plugin discovery"""
        # Mock successful plugin imports
        mock_tome_keeper = MagicMock()
        mock_github_manager = MagicMock()
        mock_config_manager = MagicMock()
        
        def mock_import(module_name, fromlist):
            if module_name == "tome_keeper.plugin_interface":
                mock_module = MagicMock()
                mock_module.MemoryManager = MagicMock(return_value=mock_tome_keeper)
                return mock_module
            elif module_name == "quest_tracker.plugin_interface":
                mock_module = MagicMock()
                mock_module.QuestTracker = MagicMock(return_value=mock_github_manager)
                return mock_module
            elif module_name == "config_manager.plugin_interface":
                mock_module = MagicMock()
                mock_module.ConfigManager = MagicMock(return_value=mock_config_manager)
                return mock_module
            return None
        
        with patch('builtins.__import__', side_effect=mock_import):
            await plugin_registry.discover_plugins()
        
        # Verify all plugins were registered
        assert "tome_keeper" in plugin_registry.plugins
        assert "quest_tracker" in plugin_registry.plugins
        assert "config_manager" in plugin_registry.plugins
        
        # Verify plugin status
        assert plugin_registry.plugins["tome_keeper"]["status"] == "active"
        assert plugin_registry.plugins["quest_tracker"]["status"] == "active"
        assert plugin_registry.plugins["config_manager"]["status"] == "active"
        
        # Verify plugin instances
        assert plugin_registry.plugins["tome_keeper"]["instance"] == mock_tome_keeper
        assert plugin_registry.plugins["quest_tracker"]["instance"] == mock_github_manager
        assert plugin_registry.plugins["config_manager"]["instance"] == mock_config_manager
    
    @pytest.mark.asyncio
    async def test_discover_plugins_import_error(self, plugin_registry):
        """Test plugin discovery with import errors"""
        def mock_import(module_name, fromlist):
            if module_name == "tome_keeper.plugin_interface":
                raise ImportError("Module not found")
            elif module_name == "quest_tracker.plugin_interface":
                mock_module = MagicMock()
                mock_module.QuestTracker = MagicMock(return_value=MagicMock())
                return mock_module
            else:
                raise ImportError("Module not found")
        
        with patch('builtins.__import__', side_effect=mock_import):
            await plugin_registry.discover_plugins()
        
        # Verify tome_keeper marked as not available
        assert plugin_registry.plugins["tome_keeper"]["status"] == "not_available"
        assert plugin_registry.plugins["tome_keeper"]["instance"] is None
        assert "error" in plugin_registry.plugins["tome_keeper"]
        
        # Verify quest_tracker loaded successfully
        assert plugin_registry.plugins["quest_tracker"]["status"] == "active"
        assert plugin_registry.plugins["quest_tracker"]["instance"] is not None
        
        # Verify config_manager marked as not available
        assert plugin_registry.plugins["config_manager"]["status"] == "not_available"
    
    @pytest.mark.asyncio
    async def test_discover_plugins_instantiation_error(self, plugin_registry):
        """Test plugin discovery with instantiation errors"""
        def mock_import(module_name, fromlist):
            if module_name == "tome_keeper.plugin_interface":
                mock_module = MagicMock()
                mock_module.MemoryManager = MagicMock(side_effect=Exception("Instantiation failed"))
                return mock_module
            return None
        
        with patch('builtins.__import__', side_effect=mock_import):
            await plugin_registry.discover_plugins()
        
        # Verify tome_keeper marked as error
        assert plugin_registry.plugins["tome_keeper"]["status"] == "error"
        assert plugin_registry.plugins["tome_keeper"]["instance"] is None
        assert "error" in plugin_registry.plugins["tome_keeper"]
    
    @pytest.mark.asyncio
    async def test_get_status(self, plugin_registry):
        """Test getting plugin status"""
        # Set up plugin data
        plugin_registry.plugins = {
            "tome_keeper": {
                "status": "active",
                "instance": MagicMock(),
                "last_check": "2025-01-01T00:00:00Z"
            },
            "quest_tracker": {
                "status": "not_available",
                "instance": None,
                "error": "Import error",
                "last_check": "2025-01-01T00:00:00Z"
            }
        }
        
        plugin_registry.plugin_health = {
            "tome_keeper": "enchanted",
            "quest_tracker": "not_available"
        }
        
        status = await plugin_registry.get_status()
        
        assert status["tome_keeper"] == "active"
        assert status["quest_tracker"] == "not_available"
    
    @pytest.mark.asyncio
    async def test_get_status_with_health_issues(self, plugin_registry):
        """Test getting plugin status with health issues"""
        plugin_registry.plugins = {
            "tome_keeper": {
                "status": "active",
                "instance": MagicMock(),
                "last_check": "2025-01-01T00:00:00Z"
            }
        }
        
        plugin_registry.plugin_health = {
            "tome_keeper": "degraded"
        }
        
        status = await plugin_registry.get_status()
        
        assert status["tome_keeper"] == "active:degraded"
    
    @pytest.mark.asyncio
    async def test_get_plugin_info_exists(self, plugin_registry):
        """Test getting plugin info for existing plugin"""
        plugin_registry.plugins = {
            "tome_keeper": {
                "info": {
                    "name": "Memory Manager",
                    "description": "Memory and context management",
                    "capabilities": ["store_memory", "get_memory"]
                },
                "status": "active",
                "instance": MagicMock(),
                "last_check": "2025-01-01T00:00:00Z"
            }
        }
        
        plugin_registry.plugin_health = {
            "tome_keeper": "enchanted"
        }
        
        info = await plugin_registry.get_plugin_info("tome_keeper")
        
        assert info["id"] == "tome_keeper"
        assert info["info"]["name"] == "Memory Manager"
        assert info["status"] == "active"
        assert info["health"] == "enchanted"
        assert info["available"] is True
    
    @pytest.mark.asyncio
    async def test_get_plugin_info_not_exists(self, plugin_registry):
        """Test getting plugin info for non-existent plugin"""
        info = await plugin_registry.get_plugin_info("non_existent")
        
        assert "error" in info
        assert "not found" in info["error"]
    
    @pytest.mark.asyncio
    async def test_get_available_plugins(self, plugin_registry):
        """Test getting available plugins"""
        plugin_registry.plugins = {
            "tome_keeper": {
                "status": "active",
                "instance": MagicMock()
            },
            "quest_tracker": {
                "status": "not_available",
                "instance": None
            },
            "config_manager": {
                "status": "active",
                "instance": MagicMock()
            }
        }
        
        available = await plugin_registry.get_available_plugins()
        
        assert "tome_keeper" in available
        assert "config_manager" in available
        assert "quest_tracker" not in available
        assert len(available) == 2
    
    @pytest.mark.asyncio
    async def test_is_plugin_available_true(self, plugin_registry):
        """Test checking if plugin is available - true case"""
        plugin_registry.plugins = {
            "tome_keeper": {
                "status": "active",
                "instance": MagicMock()
            }
        }
        
        available = await plugin_registry.is_plugin_available("tome_keeper")
        
        assert available is True
    
    @pytest.mark.asyncio
    async def test_is_plugin_available_false(self, plugin_registry):
        """Test checking if plugin is available - false cases"""
        plugin_registry.plugins = {
            "tome_keeper": {
                "status": "not_available",
                "instance": None
            },
            "quest_tracker": {
                "status": "active",
                "instance": None  # Status active but no instance
            }
        }
        
        # Plugin not available
        available1 = await plugin_registry.is_plugin_available("tome_keeper")
        assert available1 is False
        
        # Plugin active but no instance
        available2 = await plugin_registry.is_plugin_available("quest_tracker")
        assert available2 is False
        
        # Plugin doesn't exist
        available3 = await plugin_registry.is_plugin_available("non_existent")
        assert available3 is False
    
    @pytest.mark.asyncio
    async def test_get_plugin_capabilities(self, plugin_registry):
        """Test getting plugin capabilities"""
        plugin_registry.plugins = {
            "tome_keeper": {
                "info": {
                    "capabilities": ["store_memory", "get_memory", "clear_memory"]
                }
            }
        }
        
        capabilities = await plugin_registry.get_plugin_capabilities("tome_keeper")
        
        assert "store_memory" in capabilities
        assert "get_memory" in capabilities
        assert "clear_memory" in capabilities
        assert len(capabilities) == 3
    
    @pytest.mark.asyncio
    async def test_get_plugin_capabilities_not_exists(self, plugin_registry):
        """Test getting capabilities for non-existent plugin"""
        capabilities = await plugin_registry.get_plugin_capabilities("non_existent")
        
        assert capabilities == []
    
    @pytest.mark.asyncio
    async def test_check_plugin_health_success(self, plugin_registry):
        """Test plugin health check success"""
        mock_instance = MagicMock()
        mock_instance.health_check.return_value = "enchanted"
        
        plugin_registry.plugins = {
            "tome_keeper": {
                "instance": mock_instance
            }
        }
        
        await plugin_registry._check_plugin_health()
        
        assert plugin_registry.plugin_health["tome_keeper"] == "enchanted"
        mock_instance.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_plugin_health_async(self, plugin_registry):
        """Test plugin health check with async method"""
        mock_instance = MagicMock()
        async_health_check = AsyncMock(return_value="enchanted")
        mock_instance.health_check = async_health_check
        
        plugin_registry.plugins = {
            "tome_keeper": {
                "instance": mock_instance
            }
        }
        
        await plugin_registry._check_plugin_health()
        
        assert plugin_registry.plugin_health["tome_keeper"] == "enchanted"
        async_health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_plugin_health_no_method(self, plugin_registry):
        """Test plugin health check when no health_check method exists"""
        mock_instance = MagicMock()
        del mock_instance.health_check  # Remove health_check method
        
        plugin_registry.plugins = {
            "tome_keeper": {
                "instance": mock_instance
            }
        }
        
        await plugin_registry._check_plugin_health()
        
        # Should assume enchanted if no health check method
        assert plugin_registry.plugin_health["tome_keeper"] == "enchanted"
    
    @pytest.mark.asyncio
    async def test_check_plugin_health_no_instance(self, plugin_registry):
        """Test plugin health check when no instance exists"""
        plugin_registry.plugins = {
            "tome_keeper": {
                "instance": None
            }
        }
        
        await plugin_registry._check_plugin_health()
        
        assert plugin_registry.plugin_health["tome_keeper"] == "not_available"
    
    @pytest.mark.asyncio
    async def test_check_plugin_health_exception(self, plugin_registry):
        """Test plugin health check with exception"""
        mock_instance = MagicMock()
        mock_instance.health_check.side_effect = Exception("Health check failed")
        
        plugin_registry.plugins = {
            "tome_keeper": {
                "instance": mock_instance
            }
        }
        
        await plugin_registry._check_plugin_health()
        
        assert plugin_registry.plugin_health["tome_keeper"] == "degraded"
    
    @pytest.mark.asyncio
    async def test_refresh_health(self, plugin_registry):
        """Test refreshing plugin health"""
        mock_instance = MagicMock()
        mock_instance.health_check.return_value = "enchanted"
        
        plugin_registry.plugins = {
            "tome_keeper": {
                "instance": mock_instance
            }
        }
        
        await plugin_registry.refresh_health()
        
        assert plugin_registry.plugin_health["tome_keeper"] == "enchanted"
    
    def test_get_plugin_instance_success(self, plugin_registry):
        """Test getting plugin instance successfully"""
        mock_instance = MagicMock()
        
        plugin_registry.plugins = {
            "tome_keeper": {
                "status": "active",
                "instance": mock_instance
            }
        }
        
        instance = plugin_registry.get_plugin_instance("tome_keeper")
        
        assert instance == mock_instance
    
    def test_get_plugin_instance_not_exists(self, plugin_registry):
        """Test getting plugin instance that doesn't exist"""
        instance = plugin_registry.get_plugin_instance("non_existent")
        
        assert instance is None
    
    def test_get_plugin_instance_not_active(self, plugin_registry):
        """Test getting plugin instance that's not active"""
        plugin_registry.plugins = {
            "tome_keeper": {
                "status": "not_available",
                "instance": MagicMock()
            }
        }
        
        instance = plugin_registry.get_plugin_instance("tome_keeper")
        
        assert instance is None
    
    @pytest.mark.asyncio
    async def test_plugin_registration_metadata(self, plugin_registry):
        """Test that plugin registration includes proper metadata"""
        mock_tome_keeper = MagicMock()
        
        def mock_import(module_name, fromlist):
            if module_name == "tome_keeper.plugin_interface":
                mock_module = MagicMock()
                mock_module.MemoryManager = MagicMock(return_value=mock_tome_keeper)
                return mock_module
            return None
        
        with patch('builtins.__import__', side_effect=mock_import):
            await plugin_registry.discover_plugins()
        
        plugin_data = plugin_registry.plugins["tome_keeper"]
        
        # Verify metadata structure
        assert "info" in plugin_data
        assert "instance" in plugin_data
        assert "status" in plugin_data
        assert "last_check" in plugin_data
        
        # Verify plugin info
        assert plugin_data["info"]["name"] == "Memory Manager"
        assert plugin_data["info"]["description"] == "Conversation memory and context management"
        assert "store_memory" in plugin_data["info"]["capabilities"]
        assert "get_memory" in plugin_data["info"]["capabilities"]
        assert "clear_memory" in plugin_data["info"]["capabilities"]
        
        # Verify timestamp format
        from datetime import datetime
        timestamp = datetime.fromisoformat(plugin_data["last_check"])
        assert isinstance(timestamp, datetime)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])