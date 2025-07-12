# SIDHE Plugin Development Kit - Quick Start Guide

## 🌟 Welcome, Enchanter!

This guide will help you craft your first SIDHE plugin using the mystical Plugin Development Kit (PDK). With the PDK, you'll have all the protective wards and communication spells necessary to integrate seamlessly with the SIDHE ecosystem.

## 📦 Installation

### Prerequisites
- Python 3.11+
- Redis server (for the mystical message bus)
- SIDHE project repository

### Installing the PDK

1. **Place the PDK in your plugin directory:**
```bash
# From SIDHE root directory
mkdir -p src/plugins/your_plugin_name
cp scripts/sidhe_pdk.py src/plugins/your_plugin_name/
```

2. **Install dependencies:**
```bash
pip install redis[hiredis] pydantic
```

## 🚀 Creating Your First Plugin

### Step 1: Create Your Plugin Structure

```bash
src/plugins/your_plugin_name/
├── __init__.py
├── plugin_interface.py   # Your main plugin code
├── sidhe_pdk.py         # The PDK (copy from scripts/)
├── requirements.txt     # Plugin dependencies
└── test_your_plugin.py  # Plugin tests
```

### Step 2: Implement Your Plugin

Create `plugin_interface.py`:

```python
#!/usr/bin/env python3
"""
My Enchanted Plugin - A magical addition to SIDHE
"""

from sidhe_pdk import EnchantedPlugin, PluginCapability, PluginMessage
from typing import Dict, Any
import asyncio


class MyEnchantedPlugin(EnchantedPlugin):
    """
    An example plugin that performs mystical calculations
    """
    
    def __init__(self):
        super().__init__(
            plugin_id="enchanted_calculator",
            plugin_name="Enchanted Calculator",
            version="1.0.0"
        )
        
        # Register our magical capabilities
        self.register_capability(PluginCapability(
            name="calculate_power",
            description="Calculate the magical power level",
            parameters={"base": "number", "exponent": "number"},
            returns={"result": "number"}
        ))
        
        self.register_capability(PluginCapability(
            name="divine_number",
            description="Divine if a number is mystically significant",
            parameters={"number": "number"},
            returns={"is_significant": "boolean", "reason": "string"}
        ))
    
    async def initialize(self):
        """Perform initialization rituals"""
        await super().initialize()
        self.logger.info("🔮 Calculator crystals aligned...")
        
        # Initialize any resources your plugin needs
        self.mystical_constants = {
            3: "Trinity of power",
            7: "Number of completion",
            13: "Transformation catalyst",
            42: "Answer to everything"
        }
    
    async def handle_request(self, message: PluginMessage) -> Dict[str, Any]:
        """Handle calculation requests"""
        action = message.payload.get("action")
        
        if action == "calculate_power":
            base = message.payload.get("base", 0)
            exponent = message.payload.get("exponent", 1)
            
            result = base ** exponent
            self.logger.info(f"⚡ Calculated {base}^{exponent} = {result}")
            
            # Broadcast significant calculations
            if result > 1000:
                await self.broadcast_event(
                    "significant_calculation",
                    {"result": result, "formula": f"{base}^{exponent}"}
                )
            
            return {"result": result}
        
        elif action == "divine_number":
            number = message.payload.get("number", 0)
            
            is_significant = number in self.mystical_constants
            reason = self.mystical_constants.get(
                number, 
                "Number holds no special significance"
            )
            
            return {
                "is_significant": is_significant,
                "reason": reason,
                "number": number
            }
        
        else:
            raise ValueError(f"Unknown mystical action: {action}")
    
    async def cleanup(self):
        """Cleanup resources before banishment"""
        await super().cleanup()
        self.logger.info("🌙 Calculator crystals dimming...")


# CLI entry point for standalone execution
if __name__ == "__main__":
    plugin = MyEnchantedPlugin()
    plugin.run()
```

### Step 3: Test Your Plugin

Create `test_your_plugin.py`:

```python
import pytest
import asyncio
from plugin_interface import MyEnchantedPlugin
from sidhe_pdk import PluginMessage, MessageType, plugin_context


@pytest.mark.asyncio
async def test_calculate_power():
    """Test the mystical power calculation"""
    async with plugin_context(MyEnchantedPlugin) as plugin:
        # Create a test request
        request = PluginMessage(
            type=MessageType.REQUEST,
            source="test_suite",
            target=plugin.plugin_id,
            payload={
                "action": "calculate_power",
                "base": 2,
                "exponent": 10
            }
        )
        
        # Process the request
        response = await plugin.handle_request(request)
        
        # Verify the result
        assert response["result"] == 1024


@pytest.mark.asyncio
async def test_divine_number():
    """Test number divination"""
    async with plugin_context(MyEnchantedPlugin) as plugin:
        # Test a mystical number
        request = PluginMessage(
            type=MessageType.REQUEST,
            source="test_suite",
            target=plugin.plugin_id,
            payload={
                "action": "divine_number",
                "number": 7
            }
        )
        
        response = await plugin.handle_request(request)
        
        assert response["is_significant"] is True
        assert "completion" in response["reason"].lower()
```

## 🔮 Advanced Features

### Inter-Plugin Communication

Your plugin can communicate with other plugins:

```python
# Inside your handle_request method
async def handle_request(self, message: PluginMessage) -> Dict[str, Any]:
    if message.payload.get("action") == "complex_calculation":
        # Request help from the memory plugin
        memory_response = await self.send_request(
            target_plugin="tome_keeper",
            request_data={
                "action": "retrieve",
                "key": "last_calculation"
            }
        )
        
        if memory_response and memory_response.get("found"):
            last_result = memory_response.get("value")
            # Use the retrieved value...
```

### Broadcasting Events

Notify other plugins of important events:

```python
# Broadcast a significant event
await self.broadcast_event(
    event_type="mystical_alignment",
    event_data={
        "planets": ["Mercury", "Venus", "Mars"],
        "power_level": 9000
    }
)
```

### Health Monitoring

The PDK automatically tracks:
- Messages processed
- Errors encountered
- Uptime
- Last error details

Access health metrics:
```python
health_data = self.health_metrics
self.logger.info(f"Processed {health_data['messages_processed']} spells")
```

## 🧪 Testing Your Plugin

### Unit Testing
```bash
# Run tests
pytest test_your_plugin.py -v
```

### Integration Testing
```bash
# Start Redis
redis-server

# In one terminal, run your plugin
python plugin_interface.py

# In another terminal, send test messages
python -m sidhe_pdk.test_client enchanted_calculator calculate_power --base 2 --exponent 8
```

## 📝 Configuration

### Environment Variables
```bash
# Redis connection
export SIDHE_REDIS_URL="redis://localhost:6379"

# Plugin-specific settings
export ENCHANTED_CALCULATOR_MAX_EXPONENT=100
```

### Loading Configuration
```python
import os

class MyEnchantedPlugin(EnchantedPlugin):
    def __init__(self):
        super().__init__(
            plugin_id="enchanted_calculator",
            plugin_name="Enchanted Calculator",
            redis_url=os.getenv("SIDHE_REDIS_URL", "redis://localhost:6379")
        )
        
        # Plugin-specific config
        self.max_exponent = int(os.getenv("ENCHANTED_CALCULATOR_MAX_EXPONENT", "100"))
```

## 🚨 Common Pitfalls & Solutions

### 1. Redis Connection Issues
**Problem**: "Failed to connect to message realm"
**Solution**: Ensure Redis is running: `redis-cli ping`

### 2. Message Not Received
**Problem**: Plugin doesn't receive messages
**Solution**: Check channel subscriptions match message targets

### 3. Async Errors
**Problem**: "RuntimeError: This event loop is already running"
**Solution**: Use `asyncio.create_task()` instead of `asyncio.run()` when already in async context

## 📚 Next Steps

1. **Study Existing Plugins**: Look at `tome_keeper`, `quest_tracker`, and `config_manager` for patterns
2. **Join the Circle**: Add your plugin to the plugin registry
3. **Document Your Magic**: Create a spec in `/grimoire/` for your plugin
4. **Share Your Spells**: Submit a PR with your enchanted creation!

## 🌟 Example Plugins Using PDK

### Memory Crystal Plugin
```python
class MemoryCrystal(EnchantedPlugin):
    """Stores and retrieves memories with 24-hour persistence"""
    # See src/plugins/tome_keeper for full implementation
```

### Quest Tracker Plugin
```python
class QuestTracker(EnchantedPlugin):
    """Manages GitHub issues as mystical quests"""
    # See src/plugins/quest_tracker for full implementation
```

### Config Oracle Plugin
```python
class ConfigOracle(EnchantedPlugin):
    """Divines configuration from multiple sources"""
    # See src/plugins/config_manager for full implementation
```

---

*May your plugins be bug-free and your spells compile on the first try!* ✨

**Need Help?** Consult the Archmage or post in the GitHub discussions!