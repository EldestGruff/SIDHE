#!/usr/bin/env python3
"""
SIDHE Plugin Development Kit (PDK)
==================================

The sacred foundation for all SIDHE plugins - providing the ancient rituals 
and protective wards necessary for proper plugin enchantment.

This base class handles all the mystical communication protocols, health 
monitoring incantations, and standardized interfaces required by the 
SIDHE ecosystem.

Usage:
    from sidhe_pdk import EnchantedPlugin
    
    class YourPlugin(EnchantedPlugin):
        def __init__(self):
            super().__init__(
                plugin_id="your_plugin",
                plugin_name="Your Magical Plugin",
                version="1.0.0"
            )

By the ancient magic, so mote it be!
"""

import asyncio
import json
import logging
import signal
import sys
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Set
from contextlib import asynccontextmanager

import redis.asyncio as redis
from pydantic import BaseModel, Field, ValidationError


# Magical Constants
REDIS_URL = "redis://localhost:6379"
MESSAGE_TIMEOUT = 30  # seconds
HEALTH_CHECK_INTERVAL = 60  # seconds
PLUGIN_STATUS_CHANNEL = "sidhe:plugin:status"
PLUGIN_DISCOVERY_CHANNEL = "sidhe:plugin:discovery"


class MessageType(str, Enum):
    """Types of mystical messages that flow through the enchanted realm"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    BROADCAST = "broadcast"
    HEALTH_CHECK = "health_check"
    DISCOVERY = "discovery"
    ERROR = "error"


class PluginStatus(str, Enum):
    """The life states of an enchanted plugin"""
    AWAKENING = "awakening"  # Starting up
    ACTIVE = "active"        # Ready for spells
    MEDITATING = "meditating"  # Processing
    HIBERNATING = "hibernating"  # Idle
    BANISHED = "banished"    # Shutting down
    CURSED = "cursed"        # Error state


class PluginMessage(BaseModel):
    """The sacred message format for all plugin communication"""
    type: MessageType
    source: str = Field(..., description="Source plugin identifier")
    target: Optional[str] = Field(None, description="Target plugin (None for broadcast)")
    payload: Dict[str, Any] = Field(default_factory=dict)
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = Field(None, description="For request/response pairing")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PluginCapability(BaseModel):
    """Describes a magical capability that a plugin provides"""
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None
    returns: Optional[Dict[str, Any]] = None


class PluginInfo(BaseModel):
    """Complete information about an enchanted plugin"""
    plugin_id: str
    plugin_name: str
    version: str
    status: PluginStatus
    capabilities: List[PluginCapability] = Field(default_factory=list)
    health_metrics: Dict[str, Any] = Field(default_factory=dict)
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EnchantedPlugin(ABC):
    """
    The sacred base class for all SIDHE plugins.
    
    This mystical foundation provides:
    - Automatic message bus integration with Redis
    - Health monitoring and heartbeat management
    - Standardized logging with magical formatting
    - Message validation and error handling
    - Plugin discovery and capability announcement
    - Graceful startup and shutdown rituals
    """
    
    def __init__(self, 
                 plugin_id: str,
                 plugin_name: str,
                 version: str = "1.0.0",
                 redis_url: str = REDIS_URL):
        """
        Initialize the enchanted plugin with its mystical properties.
        
        Args:
            plugin_id: Unique identifier for this plugin (e.g., "memory_crystal")
            plugin_name: Human-readable name (e.g., "Memory Crystal Manager")
            version: Plugin version following semantic versioning
            redis_url: Connection string to the Redis message realm
        """
        self.plugin_id = plugin_id
        self.plugin_name = plugin_name
        self.version = version
        self.redis_url = redis_url
        
        # Magical state management
        self.status = PluginStatus.AWAKENING
        self.capabilities: List[PluginCapability] = []
        self._message_handlers: Dict[MessageType, Callable] = {}
        self._running = False
        self._tasks: Set[asyncio.Task] = set()
        
        # Redis connections for the mystical message bus
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
        # Logging with magical formatting
        self.logger = self._setup_enchanted_logging()
        
        # Health metrics
        self.health_metrics = {
            "messages_processed": 0,
            "errors_encountered": 0,
            "uptime_seconds": 0,
            "last_error": None
        }
        
        # Register default message handlers
        self._register_default_handlers()
        
        self.logger.info(f"🌟 Plugin '{self.plugin_name}' awakening...")
    
    def _setup_enchanted_logging(self) -> logging.Logger:
        """Configure logging with mystical formatting"""
        logger = logging.getLogger(f"sidhe.plugins.{self.plugin_id}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _register_default_handlers(self):
        """Register the default mystical message handlers"""
        self._message_handlers[MessageType.HEALTH_CHECK] = self._handle_health_check
        self._message_handlers[MessageType.DISCOVERY] = self._handle_discovery
    
    async def _handle_health_check(self, message: PluginMessage) -> Dict[str, Any]:
        """Respond to health check incantations"""
        return {
            "status": self.status.value,
            "health_metrics": self.health_metrics,
            "uptime": self.health_metrics["uptime_seconds"]
        }
    
    async def _handle_discovery(self, message: PluginMessage) -> Dict[str, Any]:
        """Respond to discovery requests with plugin capabilities"""
        info = PluginInfo(
            plugin_id=self.plugin_id,
            plugin_name=self.plugin_name,
            version=self.version,
            status=self.status,
            capabilities=self.capabilities,
            health_metrics=self.health_metrics
        )
        return info.dict()
    
    def register_capability(self, capability: PluginCapability):
        """Register a magical capability that this plugin provides"""
        self.capabilities.append(capability)
        self.logger.info(f"✨ Registered capability: {capability.name}")
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a handler for a specific message type"""
        self._message_handlers[message_type] = handler
        self.logger.info(f"📜 Registered handler for {message_type.value} messages")
    
    async def initialize(self):
        """
        Perform plugin-specific initialization rituals.
        Override this method to set up your plugin's magical properties.
        """
        self.logger.info("🔮 Performing initialization rituals...")
    
    async def cleanup(self):
        """
        Perform plugin-specific cleanup before banishment.
        Override this method to properly close resources.
        """
        self.logger.info("🧹 Performing cleanup rituals...")
    
    @abstractmethod
    async def handle_request(self, message: PluginMessage) -> Dict[str, Any]:
        """
        Handle incoming spell requests.
        
        This is the main method that each plugin must implement to handle
        specific requests from other components.
        
        Args:
            message: The incoming plugin message
            
        Returns:
            Dictionary containing the response payload
            
        Raises:
            Exception: If the spell fails to cast
        """
        pass
    
    async def _connect_to_redis(self):
        """Establish connection to the mystical message realm"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            
            # Subscribe to plugin-specific and broadcast channels
            channels = [
                f"sidhe:plugin:{self.plugin_id}",  # Direct messages
                "sidhe:plugin:broadcast",           # Broadcast messages
                PLUGIN_DISCOVERY_CHANNEL,           # Discovery requests
            ]
            
            await self.pubsub.subscribe(*channels)
            self.logger.info(f"🔗 Connected to message realm on channels: {channels}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to message realm: {e}")
            self.status = PluginStatus.CURSED
            raise
    
    async def _disconnect_from_redis(self):
        """Sever connection from the message realm"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info("🔌 Disconnected from message realm")
    
    async def _message_listener(self):
        """Listen for messages from the mystical realm"""
        try:
            async for raw_message in self.pubsub.listen():
                if raw_message["type"] == "message":
                    await self._process_message(raw_message["data"])
                    
        except asyncio.CancelledError:
            self.logger.info("👂 Message listener cancelled")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error in message listener: {e}")
            self.health_metrics["errors_encountered"] += 1
            self.health_metrics["last_error"] = str(e)
    
    async def _process_message(self, raw_data: bytes):
        """Process an incoming mystical message"""
        try:
            # Decode and validate the message
            data = json.loads(raw_data.decode())
            message = PluginMessage(**data)
            
            # Check if message is for us or broadcast
            if message.target and message.target != self.plugin_id:
                return
            
            self.logger.debug(f"📨 Received {message.type.value} from {message.source}")
            self.health_metrics["messages_processed"] += 1
            
            # Route to appropriate handler
            if message.type == MessageType.REQUEST:
                await self._handle_request_wrapper(message)
            elif message.type in self._message_handlers:
                response_data = await self._message_handlers[message.type](message)
                if response_data and message.type == MessageType.HEALTH_CHECK:
                    await self._send_response(message, response_data)
            
        except ValidationError as e:
            self.logger.error(f"❌ Invalid message format: {e}")
        except Exception as e:
            self.logger.error(f"❌ Error processing message: {e}")
            self.health_metrics["errors_encountered"] += 1
            self.health_metrics["last_error"] = str(e)
    
    async def _handle_request_wrapper(self, message: PluginMessage):
        """Wrapper to handle requests with proper error handling"""
        try:
            self.status = PluginStatus.MEDITATING
            response_data = await self.handle_request(message)
            await self._send_response(message, response_data)
            self.status = PluginStatus.ACTIVE
            
        except Exception as e:
            self.logger.error(f"❌ Error handling request: {e}")
            error_data = {
                "error": str(e),
                "error_type": type(e).__name__
            }
            await self._send_error(message, error_data)
            self.status = PluginStatus.ACTIVE
    
    async def _send_response(self, request: PluginMessage, response_data: Dict[str, Any]):
        """Send a response through the mystical channels"""
        response = PluginMessage(
            type=MessageType.RESPONSE,
            source=self.plugin_id,
            target=request.source,
            payload=response_data,
            correlation_id=request.message_id
        )
        
        channel = f"sidhe:plugin:{request.source}"
        await self._publish_message(channel, response)
    
    async def _send_error(self, request: PluginMessage, error_data: Dict[str, Any]):
        """Send an error response when a spell fails"""
        error_response = PluginMessage(
            type=MessageType.ERROR,
            source=self.plugin_id,
            target=request.source,
            payload=error_data,
            correlation_id=request.message_id
        )
        
        channel = f"sidhe:plugin:{request.source}"
        await self._publish_message(channel, error_response)
    
    async def _publish_message(self, channel: str, message: PluginMessage):
        """Publish a message to the mystical realm"""
        try:
            message_json = message.json()
            await self.redis_client.publish(channel, message_json)
            self.logger.debug(f"📤 Published {message.type.value} to {channel}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to publish message: {e}")
            self.health_metrics["errors_encountered"] += 1
    
    async def broadcast_event(self, event_type: str, event_data: Dict[str, Any]):
        """Broadcast an event to all plugins in the realm"""
        event = PluginMessage(
            type=MessageType.EVENT,
            source=self.plugin_id,
            target=None,  # Broadcast
            payload={
                "event_type": event_type,
                "event_data": event_data
            }
        )
        
        await self._publish_message("sidhe:plugin:broadcast", event)
        self.logger.info(f"📢 Broadcast event: {event_type}")
    
    async def send_request(self, target_plugin: str, request_data: Dict[str, Any], 
                          timeout: int = MESSAGE_TIMEOUT) -> Optional[Dict[str, Any]]:
        """
        Send a request to another plugin and await the response.
        
        Args:
            target_plugin: ID of the target plugin
            request_data: Request payload
            timeout: Response timeout in seconds
            
        Returns:
            Response payload or None if timeout/error
        """
        request = PluginMessage(
            type=MessageType.REQUEST,
            source=self.plugin_id,
            target=target_plugin,
            payload=request_data
        )
        
        # Create response channel
        response_channel = f"sidhe:plugin:{self.plugin_id}:response:{request.message_id}"
        response_pubsub = self.redis_client.pubsub()
        
        try:
            # Subscribe to response channel
            await response_pubsub.subscribe(response_channel)
            
            # Send request
            target_channel = f"sidhe:plugin:{target_plugin}"
            await self._publish_message(target_channel, request)
            
            # Wait for response
            async def get_response():
                async for msg in response_pubsub.listen():
                    if msg["type"] == "message":
                        data = json.loads(msg["data"].decode())
                        response = PluginMessage(**data)
                        if response.correlation_id == request.message_id:
                            return response.payload
            
            response_data = await asyncio.wait_for(get_response(), timeout=timeout)
            return response_data
            
        except asyncio.TimeoutError:
            self.logger.warning(f"⏰ Request to {target_plugin} timed out")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error sending request: {e}")
            return None
        finally:
            await response_pubsub.unsubscribe()
            await response_pubsub.close()
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to show we're alive"""
        start_time = datetime.now(timezone.utc)
        
        while self._running:
            try:
                # Update uptime
                uptime = (datetime.now(timezone.utc) - start_time).total_seconds()
                self.health_metrics["uptime_seconds"] = int(uptime)
                
                # Send heartbeat
                heartbeat = PluginMessage(
                    type=MessageType.EVENT,
                    source=self.plugin_id,
                    target=None,
                    payload={
                        "event_type": "heartbeat",
                        "event_data": {
                            "status": self.status.value,
                            "uptime": uptime
                        }
                    }
                )
                
                await self._publish_message(PLUGIN_STATUS_CHANNEL, heartbeat)
                
                # Sleep until next heartbeat
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in heartbeat loop: {e}")
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)
    
    async def _announce_presence(self):
        """Announce our presence to the realm"""
        announcement = PluginMessage(
            type=MessageType.DISCOVERY,
            source=self.plugin_id,
            target=None,
            payload={
                "plugin_id": self.plugin_id,
                "plugin_name": self.plugin_name,
                "version": self.version,
                "status": self.status.value,
                "capabilities": [cap.dict() for cap in self.capabilities]
            }
        )
        
        await self._publish_message(PLUGIN_DISCOVERY_CHANNEL, announcement)
        self.logger.info(f"📣 Announced presence to the realm")
    
    def _handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"🛑 Received shutdown signal {signum}")
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
    
    async def start(self):
        """
        Begin the plugin's mystical journey.
        
        This method:
        1. Connects to the message realm
        2. Performs initialization rituals
        3. Announces presence
        4. Starts message listener and heartbeat
        5. Runs until shutdown
        """
        try:
            # Connect to Redis
            await self._connect_to_redis()
            
            # Perform custom initialization
            await self.initialize()
            
            # Update status
            self.status = PluginStatus.ACTIVE
            self._running = True
            
            # Announce our presence
            await self._announce_presence()
            
            # Start background tasks
            listener_task = asyncio.create_task(self._message_listener())
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            self._tasks.add(listener_task)
            self._tasks.add(heartbeat_task)
            
            # Set up signal handlers
            signal.signal(signal.SIGINT, self._handle_shutdown_signal)
            signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
            
            self.logger.info(f"✨ Plugin '{self.plugin_name}' is active and listening")
            
            # Wait for tasks to complete
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"❌ Fatal error in plugin: {e}")
            self.status = PluginStatus.CURSED
            raise
        
        finally:
            # Cleanup
            self.status = PluginStatus.BANISHED
            self.logger.info(f"🌙 Plugin '{self.plugin_name}' shutting down...")
            
            await self.cleanup()
            await self._disconnect_from_redis()
            
            self.logger.info(f"💤 Plugin '{self.plugin_name}' has been banished")
    
    def run(self):
        """Convenience method to run the plugin in the current event loop"""
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            self.logger.info("⌨️ Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"❌ Plugin crashed: {e}")
            sys.exit(1)


# Utility functions for plugin developers

def create_plugin_message(msg_type: MessageType, source: str, 
                         target: Optional[str] = None, 
                         payload: Optional[Dict[str, Any]] = None) -> PluginMessage:
    """Utility function to create a properly formatted plugin message"""
    return PluginMessage(
        type=msg_type,
        source=source,
        target=target,
        payload=payload or {}
    )


@asynccontextmanager
async def plugin_context(plugin_class, *args, **kwargs):
    """
    Context manager for running a plugin with automatic cleanup.
    
    Usage:
        async with plugin_context(MyPlugin) as plugin:
            # Plugin is running
            await plugin.send_request(...)
    """
    plugin = plugin_class(*args, **kwargs)
    
    # Start plugin in background
    task = asyncio.create_task(plugin.start())
    
    # Wait for plugin to be active
    while plugin.status != PluginStatus.ACTIVE:
        if plugin.status == PluginStatus.CURSED:
            raise RuntimeError(f"Plugin failed to start: {plugin.plugin_name}")
        await asyncio.sleep(0.1)
    
    try:
        yield plugin
    finally:
        # Shutdown plugin
        plugin._running = False
        await task


# Example plugin implementation for reference

class ExampleMemoryCrystal(EnchantedPlugin):
    """
    Example implementation of a memory storage plugin.
    
    This demonstrates how to create a plugin using the PDK.
    """
    
    def __init__(self):
        super().__init__(
            plugin_id="example_memory_crystal",
            plugin_name="Example Memory Crystal",
            version="1.0.0"
        )
        
        # Internal storage
        self.memories: Dict[str, Any] = {}
        
        # Register our magical capabilities
        self.register_capability(PluginCapability(
            name="store_memory",
            description="Store a memory in the crystal",
            parameters={"key": "string", "value": "any"},
            returns={"success": "boolean"}
        ))
        
        self.register_capability(PluginCapability(
            name="retrieve_memory",
            description="Retrieve a memory from the crystal",
            parameters={"key": "string"},
            returns={"value": "any", "found": "boolean"}
        ))
    
    async def initialize(self):
        """Perform initialization rituals"""
        await super().initialize()
        self.logger.info("💎 Memory crystal resonating...")
    
    async def handle_request(self, message: PluginMessage) -> Dict[str, Any]:
        """Handle memory storage requests"""
        action = message.payload.get("action")
        
        if action == "store":
            key = message.payload.get("key")
            value = message.payload.get("value")
            
            if not key:
                raise ValueError("Missing 'key' in request")
            
            self.memories[key] = value
            self.logger.info(f"💾 Stored memory: {key}")
            
            return {"success": True, "key": key}
        
        elif action == "retrieve":
            key = message.payload.get("key")
            
            if not key:
                raise ValueError("Missing 'key' in request")
            
            if key in self.memories:
                return {
                    "found": True,
                    "key": key,
                    "value": self.memories[key]
                }
            else:
                return {
                    "found": False,
                    "key": key,
                    "value": None
                }
        
        else:
            raise ValueError(f"Unknown action: {action}")


if __name__ == "__main__":
    # Example of running the plugin
    plugin = ExampleMemoryCrystal()
    plugin.run()
