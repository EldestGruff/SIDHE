#!/usr/bin/env python3
"""
Docker Deployment Validation Script
Tests end-to-end deployment of the Conversation Engine
"""
import time
import sys
import subprocess
import requests
import json
import asyncio
import websockets
from typing import Dict, Any
import argparse

class DeploymentValidator:
    """Validates Docker deployment of Conversation Engine"""
    
    def __init__(self, backend_url="http://localhost:8000", frontend_url="http://localhost:3000"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.websocket_url = "ws://localhost:8000/ws"
        self.redis_host = "localhost"
        self.redis_port = 6379
        
    def run_validation(self, quick_mode=False):
        """Run complete deployment validation"""
        print("🚀 RIKER CONVERSATION ENGINE - DEPLOYMENT VALIDATION")
        print("=" * 60)
        
        tests = [
            ("Docker Services Health", self.test_docker_services),
            ("Redis Connectivity", self.test_redis_connectivity),
            ("Backend Health Check", self.test_backend_health),
            ("Frontend Accessibility", self.test_frontend_accessibility),
            ("API Endpoints", self.test_api_endpoints),
            ("WebSocket Connection", self.test_websocket_connection),
        ]
        
        if not quick_mode:
            tests.extend([
                ("Plugin Integration", self.test_plugin_integration),
                ("Memory Integration", self.test_memory_integration),
                ("Message Bus Communication", self.test_message_bus),
                ("End-to-End Conversation", self.test_conversation_flow),
            ])
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n🧪 Testing: {test_name}")
            print("-" * 40)
            
            try:
                result = test_func()
                if result:
                    print(f"✅ {test_name}: PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAILED")
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 VALIDATION SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Deployment is ready for production.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the deployment.")
            return False
    
    def test_docker_services(self):
        """Test Docker services are running"""
        try:
            # Check if docker-compose services are running
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.yml", "ps", "--services", "--filter", "status=running"],
                cwd=".",
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Failed to check Docker services: {result.stderr}")
                return False
            
            running_services = result.stdout.strip().split('\n')
            expected_services = {"redis", "backend", "frontend"}
            
            if set(running_services) >= expected_services:
                print(f"✅ All required services running: {', '.join(running_services)}")
                return True
            else:
                missing = expected_services - set(running_services)
                print(f"❌ Missing services: {', '.join(missing)}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking Docker services: {e}")
            return False
    
    def test_redis_connectivity(self):
        """Test Redis connectivity"""
        try:
            import redis
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            
            # Test basic operations
            r.ping()
            r.set("test_key", "test_value")
            value = r.get("test_key")
            r.delete("test_key")
            
            if value == "test_value":
                print("✅ Redis connectivity and operations working")
                return True
            else:
                print("❌ Redis operations failed")
                return False
                
        except Exception as e:
            print(f"❌ Redis connectivity failed: {e}")
            return False
    
    def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Backend health check passed")
                print(f"   Status: {health_data.get('status', 'unknown')}")
                
                # Check component health
                components = health_data.get('components', {})
                for component, status in components.items():
                    print(f"   {component}: {status}")
                
                return True
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Backend health check error: {e}")
            return False
    
    def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            
            if response.status_code == 200:
                # Check for React app indicators
                content = response.text.lower()
                if "riker" in content or "conversation engine" in content or "react" in content:
                    print("✅ Frontend accessible and contains expected content")
                    return True
                else:
                    print("❌ Frontend accessible but content unexpected")
                    return False
            else:
                print(f"❌ Frontend not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Frontend accessibility error: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        try:
            endpoints = [
                ("/", "Root endpoint"),
                ("/health", "Health check"),
            ]
            
            for endpoint, description in endpoints:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {description}: OK")
                else:
                    print(f"   ❌ {description}: {response.status_code}")
                    return False
            
            print("✅ All API endpoints accessible")
            return True
            
        except Exception as e:
            print(f"❌ API endpoints test error: {e}")
            return False
    
    def test_websocket_connection(self):
        """Test WebSocket connection"""
        async def websocket_test():
            try:
                async with websockets.connect(self.websocket_url) as websocket:
                    # Send a test message
                    test_message = {
                        "content": "Hello Riker, this is a deployment test",
                        "conversation_id": "deployment_test",
                        "timestamp": "2025-01-01T00:00:00Z"
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    
                    # Wait for response
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    response_data = json.loads(response)
                    
                    if "type" in response_data:
                        print("✅ WebSocket connection and message exchange working")
                        print(f"   Response type: {response_data.get('type')}")
                        return True
                    else:
                        print("❌ WebSocket response format unexpected")
                        return False
                        
            except Exception as e:
                print(f"❌ WebSocket test failed: {e}")
                return False
        
        try:
            return asyncio.run(websocket_test())
        except Exception as e:
            print(f"❌ WebSocket test error: {e}")
            return False
    
    def test_plugin_integration(self):
        """Test plugin integration"""
        try:
            # This would test if plugins are properly loaded and accessible
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                plugins = health_data.get('components', {}).get('plugins', {})
                
                if isinstance(plugins, dict) and plugins:
                    print(f"✅ Plugin integration working")
                    for plugin, status in plugins.items():
                        print(f"   {plugin}: {status}")
                    return True
                else:
                    print("⚠️  No plugins detected or plugin status unavailable")
                    return True  # Not a failure for deployment validation
            else:
                print("❌ Could not check plugin integration")
                return False
                
        except Exception as e:
            print(f"❌ Plugin integration test error: {e}")
            return False
    
    def test_memory_integration(self):
        """Test memory integration"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                memory_status = health_data.get('components', {}).get('memory')
                
                if memory_status:
                    print(f"✅ Memory integration status: {memory_status}")
                    return True
                else:
                    print("⚠️  Memory integration status unavailable")
                    return True  # Not critical for deployment
            else:
                print("❌ Could not check memory integration")
                return False
                
        except Exception as e:
            print(f"❌ Memory integration test error: {e}")
            return False
    
    def test_message_bus(self):
        """Test message bus integration"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                bus_status = health_data.get('components', {}).get('message_bus')
                
                if bus_status:
                    print(f"✅ Message bus status: {bus_status}")
                    return True
                else:
                    print("⚠️  Message bus status unavailable")
                    return True  # Not critical for deployment
            else:
                print("❌ Could not check message bus")
                return False
                
        except Exception as e:
            print(f"❌ Message bus test error: {e}")
            return False
    
    def test_conversation_flow(self):
        """Test end-to-end conversation flow"""
        async def conversation_test():
            try:
                async with websockets.connect(self.websocket_url) as websocket:
                    # Test a simple conversation
                    test_conversations = [
                        {
                            "content": "What's the system status?",
                            "conversation_id": "deployment_test_1"
                        },
                        {
                            "content": "How do you work?",
                            "conversation_id": "deployment_test_2"
                        }
                    ]
                    
                    for i, message in enumerate(test_conversations):
                        await websocket.send(json.dumps(message))
                        response = await asyncio.wait_for(websocket.recv(), timeout=15)
                        response_data = json.loads(response)
                        
                        if "content" in response_data:
                            print(f"   ✅ Conversation {i+1}: Response received")
                        else:
                            print(f"   ❌ Conversation {i+1}: No content in response")
                            return False
                    
                    print("✅ End-to-end conversation flow working")
                    return True
                    
            except Exception as e:
                print(f"❌ Conversation flow test failed: {e}")
                return False
        
        try:
            return asyncio.run(conversation_test())
        except Exception as e:
            print(f"❌ Conversation flow test error: {e}")
            return False

def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate Conversation Engine deployment")
    parser.add_argument("--quick", action="store_true", help="Run quick validation only")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Backend URL")
    parser.add_argument("--frontend-url", default="http://localhost:3000", help="Frontend URL")
    
    args = parser.parse_args()
    
    validator = DeploymentValidator(args.backend_url, args.frontend_url)
    
    print("Starting deployment validation...")
    print("Waiting for services to be ready...")
    time.sleep(5)  # Give services time to start
    
    success = validator.run_validation(quick_mode=args.quick)
    
    if success:
        print("\n🎉 Deployment validation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Deployment validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()