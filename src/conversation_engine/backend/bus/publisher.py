"""
Message Bus Publisher - Redis pub/sub message bus for plugin communication
Implements request/response patterns and event publishing for plugin orchestration
"""
import redis.asyncio as redis
import json
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)

class MessageBus:
    """Redis-based message bus for plugin communication"""
    
    def __init__(self):
        self.redis_client = None
        self.pubsub = None
        self.pending_requests = {}  # Track pending request/response
        self.response_timeout = settings.message_timeout
    
    async def initialize(self):
        """Initialize Redis connection and pubsub"""
        try:
            # Parse Redis URL from settings
            self.redis_client = redis.from_url(
                settings.redis_url,
                db=settings.redis_db,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Initialize pubsub for response handling
            self.pubsub = self.redis_client.pubsub()
            
            logger.info(f"Message bus initialized with Redis at {settings.redis_url}")
            
            # Start response listener
            asyncio.create_task(self._listen_for_responses())
            
        except Exception as e:
            logger.warning(f"Message bus initialization failed: {e}. Plugin communication disabled.")
            self.redis_client = None
            self.pubsub = None
    
    async def publish(self, topic: str, message: Dict[str, Any]):
        """
        Publish message to a topic
        
        Args:
            topic: Redis channel/topic name
            message: Message data to publish
        """
        try:
            if not self.redis_client:
                logger.error("Redis client not initialized")
                return
            
            # Add metadata to message
            enriched_message = {
                **message,
                "timestamp": datetime.now().isoformat(),
                "source": "conversation_engine"
            }
            
            # Publish to Redis
            await self.redis_client.publish(topic, json.dumps(enriched_message))
            logger.debug(f"Published message to {topic}")
            
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")
    
    async def request_response(self, plugin_id: str, action: str, payload: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Request/response pattern for plugin communication
        
        Args:
            plugin_id: Target plugin identifier
            action: Action to perform
            payload: Request payload
            timeout: Optional timeout override
            
        Returns:
            Response from plugin or timeout error
        """
        try:
            if not self.redis_client:
                logger.debug("Message bus not available, returning fallback response")
                return {
                    "status": "unavailable",
                    "error": "Message bus not initialized",
                    "fallback": True
                }
            
            # Generate unique message ID
            message_id = str(uuid.uuid4())
            request_timeout = timeout or self.response_timeout
            
            # Prepare request message
            request_message = {
                "message_id": message_id,
                "plugin_id": plugin_id,
                "action": action,
                "payload": payload,
                "timestamp": datetime.now().isoformat(),
                "timeout": request_timeout,
                "response_channel": f"response:{message_id}"
            }
            
            # Subscribe to response channel before sending request
            await self.pubsub.subscribe(f"response:{message_id}")
            
            # Track pending request
            response_future = asyncio.Future()
            self.pending_requests[message_id] = response_future
            
            # Publish request
            await self.publish(f"plugin:{plugin_id}", request_message)
            
            logger.info(f"Sent request {message_id} to {plugin_id}:{action}")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(response_future, timeout=request_timeout)
                return response
                
            except asyncio.TimeoutError:
                logger.warning(f"Request {message_id} to {plugin_id}:{action} timed out")
                return {
                    "status": "timeout",
                    "error": f"Plugin {plugin_id} did not respond within {request_timeout} seconds",
                    "message_id": message_id
                }
            
            finally:
                # Cleanup
                self.pending_requests.pop(message_id, None)
                await self.pubsub.unsubscribe(f"response:{message_id}")
                
        except Exception as e:
            logger.error(f"Error in request_response: {e}")
            return {
                "status": "error",
                "error": str(e),
                "plugin_id": plugin_id,
                "action": action
            }
    
    async def _listen_for_responses(self):
        """Background task to listen for plugin responses"""
        try:
            if not self.pubsub:
                return
            
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        # Parse response
                        response_data = json.loads(message["data"])
                        message_id = response_data.get("message_id")
                        
                        # Find pending request
                        if message_id in self.pending_requests:
                            future = self.pending_requests[message_id]
                            if not future.done():
                                future.set_result(response_data)
                                logger.debug(f"Received response for {message_id}")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in response: {e}")
                    except Exception as e:
                        logger.error(f"Error processing response: {e}")
                        
        except Exception as e:
            logger.error(f"Error in response listener: {e}")
    
    async def publish_event(self, event_type: str, data: Dict[str, Any]):
        """
        Publish system events
        
        Args:
            event_type: Type of event (e.g., 'mission_created', 'conversation_started')
            data: Event data
        """
        event_message = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "source": "conversation_engine"
        }
        
        await self.publish("system:events", event_message)
        logger.info(f"Published event: {event_type}")
    
    async def health_check(self) -> str:
        """Health check for message bus"""
        try:
            if not self.redis_client:
                return "disconnected"
            
            # Test Redis connection
            await self.redis_client.ping()
            
            # Test pub/sub functionality
            test_channel = "health_test"
            test_message = {"test": "ping", "timestamp": datetime.now().isoformat()}
            
            await self.redis_client.publish(test_channel, json.dumps(test_message))
            
            return "operational"
            
        except redis.ConnectionError:
            return "connection_error"
        except Exception as e:
            logger.error(f"Message bus health check failed: {e}")
            return "error"
    
    async def close(self):
        """Clean shutdown of message bus"""
        try:
            if self.pubsub:
                await self.pubsub.close()
            if self.redis_client:
                await self.redis_client.close()
            logger.info("Message bus closed")
        except Exception as e:
            logger.error(f"Error closing message bus: {e}")
