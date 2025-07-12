#!/usr/bin/env python3
"""
SIDHE PDK Testing Utilities
===========================

Mystical testing tools for plugin developers to validate their enchantments.

This module provides:
- Test client for sending messages to plugins
- Mock Redis for unit testing
- Testing fixtures and utilities
- Performance benchmarking tools

By the ancient magic, may your tests always pass!
"""

import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from unittest.mock import MagicMock, AsyncMock

import click
import pytest
from pydantic import BaseModel

# Import from the PDK
from sidhe_pdk import (
    EnchantedPlugin, PluginMessage, MessageType, PluginStatus,
    PluginCapability, create_plugin_message
)


class MockRedis:
    """
    Mock Redis implementation for testing plugins without a real Redis instance.
    
    This enchanted mock provides all the Redis functionality needed for plugin
    testing while keeping everything in memory.
    """
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.pubsub_channels: Dict[str, List[Callable]] = {}
        self.connected = True
        self._message_queue: asyncio.Queue = asyncio.Queue()
    
    async def ping(self) -> bool:
        """Simulate Redis ping"""
        if not self.connected:
            raise ConnectionError("Mock Redis not connected")
        return True
    
    async def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        if channel in self.pubsub_channels:
            # Simulate message delivery to subscribers
            for callback in self.pubsub_channels[channel]:
                await self._message_queue.put({
                    "type": "message",
                    "channel": channel,
                    "data": message.encode()
                })
        return len(self.pubsub_channels.get(channel, []))
    
    async def close(self):
        """Close mock connection"""
        self.connected = False
    
    def pubsub(self):
        """Create a mock pubsub instance"""
        return MockPubSub(self)


class MockPubSub:
    """Mock Redis PubSub for testing"""
    
    def __init__(self, redis_mock: MockRedis):
        self.redis = redis_mock
        self.subscribed_channels: List[str] = []
        self._listening = False
    
    async def subscribe(self, *channels: str):
        """Subscribe to channels"""
        for channel in channels:
            if channel not in self.subscribed_channels:
                self.subscribed_channels.append(channel)
                if channel not in self.redis.pubsub_channels:
                    self.redis.pubsub_channels[channel] = []
                self.redis.pubsub_channels[channel].append(self._handle_message)
    
    async def unsubscribe(self, *channels: str):
        """Unsubscribe from channels"""
        for channel in channels:
            if channel in self.subscribed_channels:
                self.subscribed_channels.remove(channel)
    
    async def listen(self):
        """Listen for messages"""
        self._listening = True
        while self._listening:
            try:
                # Get messages from queue with timeout
                message = await asyncio.wait_for(
                    self.redis._message_queue.get(), 
                    timeout=0.1
                )
                if message["channel"] in self.subscribed_channels:
                    yield message
            except asyncio.TimeoutError:
                continue
    
    async def close(self):
        """Close pubsub"""
        self._listening = False
        await self.unsubscribe(*self.subscribed_channels)
    
    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming message"""
        pass


@pytest.fixture
def mock_redis():
    """Pytest fixture for mock Redis"""
    return MockRedis()


@pytest.fixture
async def mock_plugin(mock_redis):
    """
    Pytest fixture for creating a test plugin with mock Redis.
    
    Usage:
        async def test_my_plugin(mock_plugin):
            plugin = await mock_plugin(MyPlugin)
            # Test your plugin
    """
    created_plugins = []
    
    async def _create_plugin(plugin_class, *args, **kwargs):
        # Patch Redis connection
        import redis.asyncio as redis
        original_from_url = redis.from_url
        
        def mock_from_url(url):
            return mock_redis
        
        redis.from_url = mock_from_url
        
        try:
            # Create plugin instance
            plugin = plugin_class(*args, **kwargs)
            created_plugins.append(plugin)
            
            # Start plugin in background
            plugin._running = True
            plugin.redis_client = mock_redis
            plugin.pubsub = mock_redis.pubsub()
            
            # Mark as active
            plugin.status = PluginStatus.ACTIVE
            
            return plugin
            
        finally:
            # Restore original
            redis.from_url = original_from_url
    
    yield _create_plugin
    
    # Cleanup
    for plugin in created_plugins:
        plugin._running = False


class TestClient:
    """
    Test client for sending messages to plugins and validating responses.
    
    This mystical testing tool allows you to interact with plugins
    programmatically for testing purposes.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.client_id = f"test_client_{uuid.uuid4().hex[:8]}"
        self.redis_client = None
        self.pubsub = None
        self.response_timeout = 5  # seconds
    
    async def connect(self):
        """Connect to the message realm"""
        import redis.asyncio as redis
        self.redis_client = redis.from_url(self.redis_url)
        await self.redis_client.ping()
        self.pubsub = self.redis_client.pubsub()
        
        # Subscribe to our response channel
        await self.pubsub.subscribe(f"sidhe:plugin:{self.client_id}")
    
    async def disconnect(self):
        """Disconnect from the message realm"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
    
    async def send_request(self, target_plugin: str, action: str, 
                          payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a request to a plugin and wait for response.
        
        Args:
            target_plugin: Plugin ID to send request to
            action: Action to perform
            payload: Additional payload data
            
        Returns:
            Response payload from the plugin
        """
        request_payload = {"action": action}
        if payload:
            request_payload.update(payload)
        
        request = create_plugin_message(
            MessageType.REQUEST,
            source=self.client_id,
            target=target_plugin,
            payload=request_payload
        )
        
        # Send request
        channel = f"sidhe:plugin:{target_plugin}"
        await self.redis_client.publish(channel, request.json())
        
        # Wait for response
        start_time = time.time()
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                response_data = json.loads(message["data"].decode())
                response = PluginMessage(**response_data)
                
                if response.correlation_id == request.message_id:
                    if response.type == MessageType.ERROR:
                        raise Exception(f"Plugin error: {response.payload}")
                    return response.payload
            
            # Check timeout
            if time.time() - start_time > self.response_timeout:
                raise TimeoutError(f"No response from {target_plugin}")
    
    async def discover_plugins(self) -> List[Dict[str, Any]]:
        """Discover all active plugins in the realm"""
        discovery_request = create_plugin_message(
            MessageType.DISCOVERY,
            source=self.client_id,
            target=None
        )
        
        # Subscribe to discovery channel
        discovery_channel = "sidhe:plugin:discovery:response"
        await self.pubsub.subscribe(discovery_channel)
        
        # Send discovery request
        await self.redis_client.publish("sidhe:plugin:discovery", discovery_request.json())
        
        # Collect responses
        plugins = []
        start_time = time.time()
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message" and message["channel"] == discovery_channel:
                    response_data = json.loads(message["data"].decode())
                    plugins.append(response_data["payload"])
                
                # Stop after timeout
                if time.time() - start_time > 2:
                    break
                    
        finally:
            await self.pubsub.unsubscribe(discovery_channel)
        
        return plugins
    
    async def check_plugin_health(self, plugin_id: str) -> Dict[str, Any]:
        """Check the health of a specific plugin"""
        health_request = create_plugin_message(
            MessageType.HEALTH_CHECK,
            source=self.client_id,
            target=plugin_id
        )
        
        channel = f"sidhe:plugin:{plugin_id}"
        await self.redis_client.publish(channel, health_request.json())
        
        # Wait for health response
        start_time = time.time()
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                response_data = json.loads(message["data"].decode())
                response = PluginMessage(**response_data)
                
                if response.correlation_id == health_request.message_id:
                    return response.payload
            
            if time.time() - start_time > 3:
                return {"status": "unresponsive", "error": "Health check timeout"}


@asynccontextmanager
async def test_client_context(redis_url: str = "redis://localhost:6379") -> AsyncGenerator[TestClient, None]:
    """
    Context manager for test client with automatic cleanup.
    
    Usage:
        async with test_client_context() as client:
            response = await client.send_request("my_plugin", "action")
    """
    client = TestClient(redis_url)
    await client.connect()
    
    try:
        yield client
    finally:
        await client.disconnect()


class PerformanceBenchmark:
    """
    Performance benchmarking tools for plugin testing.
    
    Helps measure plugin performance under various conditions.
    """
    
    def __init__(self, plugin: EnchantedPlugin):
        self.plugin = plugin
        self.results: List[Dict[str, Any]] = []
    
    async def benchmark_request(self, request: PluginMessage, 
                               iterations: int = 100) -> Dict[str, Any]:
        """Benchmark a single request type"""
        timings = []
        errors = 0
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            try:
                await self.plugin.handle_request(request)
                elapsed = time.perf_counter() - start_time
                timings.append(elapsed)
            except Exception as e:
                errors += 1
        
        if timings:
            avg_time = sum(timings) / len(timings)
            min_time = min(timings)
            max_time = max(timings)
            
            result = {
                "iterations": iterations,
                "errors": errors,
                "avg_time_ms": avg_time * 1000,
                "min_time_ms": min_time * 1000,
                "max_time_ms": max_time * 1000,
                "success_rate": (iterations - errors) / iterations * 100
            }
        else:
            result = {
                "iterations": iterations,
                "errors": errors,
                "success_rate": 0
            }
        
        self.results.append(result)
        return result
    
    async def stress_test(self, request_generator: Callable[[], PluginMessage],
                         duration_seconds: int = 60,
                         concurrent_requests: int = 10) -> Dict[str, Any]:
        """Run a stress test with concurrent requests"""
        start_time = time.time()
        total_requests = 0
        total_errors = 0
        
        async def send_requests():
            nonlocal total_requests, total_errors
            
            while time.time() - start_time < duration_seconds:
                request = request_generator()
                total_requests += 1
                
                try:
                    await self.plugin.handle_request(request)
                except Exception:
                    total_errors += 1
        
        # Run concurrent tasks
        tasks = [send_requests() for _ in range(concurrent_requests)]
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        return {
            "duration_seconds": elapsed,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "requests_per_second": total_requests / elapsed,
            "error_rate": total_errors / total_requests * 100 if total_requests > 0 else 0,
            "concurrent_requests": concurrent_requests
        }
    
    def generate_report(self) -> str:
        """Generate a performance report"""
        report = ["Performance Benchmark Report", "=" * 40, ""]
        
        for i, result in enumerate(self.results):
            report.append(f"Test {i + 1}:")
            for key, value in result.items():
                report.append(f"  {key}: {value}")
            report.append("")
        
        return "\n".join(report)


# CLI for testing plugins

@click.group()
def cli():
    """SIDHE PDK Test Client - Send mystical messages to plugins"""
    pass


@cli.command()
@click.argument('plugin_id')
@click.argument('action')
@click.option('--payload', '-p', help='JSON payload for the request')
@click.option('--redis-url', default='redis://localhost:6379', help='Redis connection URL')
def send(plugin_id: str, action: str, payload: Optional[str], redis_url: str):
    """Send a request to a plugin and display the response"""
    async def _send():
        async with test_client_context(redis_url) as client:
            request_payload = {}
            if payload:
                request_payload = json.loads(payload)
            
            click.echo(f"🔮 Sending request to {plugin_id}...")
            
            try:
                response = await client.send_request(plugin_id, action, request_payload)
                click.echo("✨ Response received:")
                click.echo(json.dumps(response, indent=2))
            except TimeoutError:
                click.echo(f"⏰ Request timed out - plugin may be offline")
            except Exception as e:
                click.echo(f"❌ Error: {e}")
    
    asyncio.run(_send())


@cli.command()
@click.option('--redis-url', default='redis://localhost:6379', help='Redis connection URL')
def discover(redis_url: str):
    """Discover all active plugins in the realm"""
    async def _discover():
        async with test_client_context(redis_url) as client:
            click.echo("🔍 Discovering plugins...")
            
            plugins = await client.discover_plugins()
            
            if plugins:
                click.echo(f"\n✨ Found {len(plugins)} active plugin(s):\n")
                for plugin in plugins:
                    click.echo(f"Plugin: {plugin.get('plugin_name', 'Unknown')}")
                    click.echo(f"  ID: {plugin.get('plugin_id')}")
                    click.echo(f"  Version: {plugin.get('version')}")
                    click.echo(f"  Status: {plugin.get('status')}")
                    
                    capabilities = plugin.get('capabilities', [])
                    if capabilities:
                        click.echo("  Capabilities:")
                        for cap in capabilities:
                            click.echo(f"    - {cap.get('name')}: {cap.get('description')}")
                    click.echo()
            else:
                click.echo("❌ No active plugins found")
    
    asyncio.run(_discover())


@cli.command()
@click.argument('plugin_id')
@click.option('--redis-url', default='redis://localhost:6379', help='Redis connection URL')
def health(plugin_id: str, redis_url: str):
    """Check the health of a specific plugin"""
    async def _health():
        async with test_client_context(redis_url) as client:
            click.echo(f"🏥 Checking health of {plugin_id}...")
            
            health_data = await client.check_plugin_health(plugin_id)
            
            click.echo("\n📊 Health Status:")
            for key, value in health_data.items():
                click.echo(f"  {key}: {value}")
    
    asyncio.run(_health())


@cli.command()
@click.argument('plugin_id')
@click.argument('action')
@click.option('--iterations', '-n', default=100, help='Number of iterations')
@click.option('--payload', '-p', help='JSON payload for requests')
@click.option('--redis-url', default='redis://localhost:6379', help='Redis connection URL')
def benchmark(plugin_id: str, action: str, iterations: int, payload: Optional[str], redis_url: str):
    """Benchmark a plugin's performance"""
    async def _benchmark():
        async with test_client_context(redis_url) as client:
            click.echo(f"⚡ Benchmarking {plugin_id} with {iterations} iterations...")
            
            request_payload = {"action": action}
            if payload:
                request_payload.update(json.loads(payload))
            
            # Send requests and measure time
            timings = []
            errors = 0
            
            with click.progressbar(range(iterations)) as bar:
                for _ in bar:
                    start = time.perf_counter()
                    try:
                        await client.send_request(plugin_id, action, request_payload)
                        elapsed = time.perf_counter() - start
                        timings.append(elapsed)
                    except Exception:
                        errors += 1
            
            if timings:
                avg_time = sum(timings) / len(timings) * 1000
                min_time = min(timings) * 1000
                max_time = max(timings) * 1000
                
                click.echo(f"\n📊 Benchmark Results:")
                click.echo(f"  Total requests: {iterations}")
                click.echo(f"  Successful: {len(timings)}")
                click.echo(f"  Errors: {errors}")
                click.echo(f"  Average time: {avg_time:.2f}ms")
                click.echo(f"  Min time: {min_time:.2f}ms")
                click.echo(f"  Max time: {max_time:.2f}ms")
                click.echo(f"  Success rate: {len(timings)/iterations*100:.1f}%")
            else:
                click.echo("❌ All requests failed!")
    
    asyncio.run(_benchmark())


if __name__ == "__main__":
    cli()
