"""
Plugin Registry - Discovery and management of existing plugins
Registers available plugins and manages their health status
"""
import logging
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add plugins directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../..", "plugins"))

logger = logging.getLogger(__name__)

class PluginRegistry:
    """Registry for plugin discovery and management"""
    
    def __init__(self):
        self.plugins = {}
        self.plugin_health = {}
    
    async def discover_plugins(self):
        """Discover available plugins and register them"""
        try:
            # Known plugins in the system
            known_plugins = {
                "memory_manager": {
                    "name": "Memory Manager",
                    "description": "Conversation memory and context management",
                    "module": "memory_manager.plugin_interface",
                    "class": "MemoryManager",
                    "capabilities": ["store_memory", "get_memory", "clear_memory"]
                },
                "github_integration": {
                    "name": "GitHub Integration", 
                    "description": "Away Mission management and GitHub operations",
                    "module": "github_integration.plugin_interface",
                    "class": "GitHubManager", 
                    "capabilities": ["get_away_missions", "create_mission", "update_mission_progress"]
                },
                "config_manager": {
                    "name": "Config Manager",
                    "description": "Configuration and settings management",
                    "module": "config_manager.plugin_interface", 
                    "class": "ConfigManager",
                    "capabilities": ["load_config", "save_config", "get_value", "set_value"]
                }
            }
            
            # Try to import and register each plugin
            for plugin_id, plugin_info in known_plugins.items():
                try:
                    # Attempt to import the plugin
                    module_name = plugin_info["module"]
                    class_name = plugin_info["class"]
                    
                    module = __import__(module_name, fromlist=[class_name])
                    plugin_class = getattr(module, class_name)
                    
                    # Test instantiation
                    plugin_instance = plugin_class()
                    
                    # Register the plugin
                    self.plugins[plugin_id] = {
                        "info": plugin_info,
                        "instance": plugin_instance,
                        "status": "active",
                        "last_check": datetime.now().isoformat()
                    }
                    
                    logger.info(f"Registered plugin: {plugin_id} ({plugin_info['name']})")
                    
                except ImportError as e:
                    logger.warning(f"Plugin {plugin_id} not available: {e}")
                    self.plugins[plugin_id] = {
                        "info": plugin_info,
                        "instance": None,
                        "status": "not_available",
                        "error": str(e),
                        "last_check": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"Error registering plugin {plugin_id}: {e}")
                    self.plugins[plugin_id] = {
                        "info": plugin_info,
                        "instance": None,
                        "status": "error",
                        "error": str(e),
                        "last_check": datetime.now().isoformat()
                    }
            
            logger.info(f"Plugin discovery complete. {len(self.plugins)} plugins registered")
            await self._check_plugin_health()
            
        except Exception as e:
            logger.error(f"Error during plugin discovery: {e}")
    
    async def get_status(self) -> Dict[str, str]:
        """Get current status of all plugins"""
        status = {}
        
        for plugin_id, plugin_data in self.plugins.items():
            plugin_status = plugin_data.get("status", "unknown")
            
            # Add health status if available
            if plugin_id in self.plugin_health:
                health = self.plugin_health[plugin_id]
                if health != "operational":
                    plugin_status = f"{plugin_status}:{health}"
            
            status[plugin_id] = plugin_status
        
        return status
    
    async def get_plugin_info(self, plugin_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific plugin"""
        if plugin_id not in self.plugins:
            return {"error": f"Plugin {plugin_id} not found"}
        
        plugin_data = self.plugins[plugin_id]
        return {
            "id": plugin_id,
            "info": plugin_data["info"],
            "status": plugin_data["status"],
            "health": self.plugin_health.get(plugin_id, "unknown"),
            "last_check": plugin_data["last_check"],
            "available": plugin_data["instance"] is not None
        }
    
    async def get_available_plugins(self) -> List[str]:
        """Get list of available (successfully loaded) plugins"""
        return [
            plugin_id for plugin_id, plugin_data in self.plugins.items()
            if plugin_data["status"] == "active" and plugin_data["instance"] is not None
        ]
    
    async def is_plugin_available(self, plugin_id: str) -> bool:
        """Check if a specific plugin is available"""
        return (
            plugin_id in self.plugins and 
            self.plugins[plugin_id]["status"] == "active" and
            self.plugins[plugin_id]["instance"] is not None
        )
    
    async def get_plugin_capabilities(self, plugin_id: str) -> List[str]:
        """Get capabilities of a specific plugin"""
        if plugin_id not in self.plugins:
            return []
        
        return self.plugins[plugin_id]["info"].get("capabilities", [])
    
    async def _check_plugin_health(self):
        """Check health status of all plugins"""
        for plugin_id, plugin_data in self.plugins.items():
            try:
                if plugin_data["instance"] is None:
                    self.plugin_health[plugin_id] = "not_available"
                    continue
                
                instance = plugin_data["instance"]
                
                # Try to call health check method if available
                if hasattr(instance, 'health_check'):
                    health_result = instance.health_check()
                    
                    # Handle async health checks
                    if hasattr(health_result, '__await__'):
                        health_result = await health_result
                    
                    self.plugin_health[plugin_id] = health_result or "operational"
                else:
                    # If no health check method, assume operational if instance exists
                    self.plugin_health[plugin_id] = "operational"
                    
            except Exception as e:
                logger.warning(f"Health check failed for {plugin_id}: {e}")
                self.plugin_health[plugin_id] = "degraded"
    
    async def refresh_health(self):
        """Refresh health status of all plugins"""
        await self._check_plugin_health()
        logger.info("Plugin health status refreshed")
    
    def get_plugin_instance(self, plugin_id: str):
        """Get plugin instance for direct usage (use carefully)"""
        if plugin_id not in self.plugins:
            return None
        
        plugin_data = self.plugins[plugin_id]
        if plugin_data["status"] != "active":
            return None
            
        return plugin_data["instance"]
