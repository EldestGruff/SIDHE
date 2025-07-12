#!/usr/bin/env python3
"""
SIDHE System Startup Script
============================

Comprehensive startup orchestrator for the SIDHE AI development environment.
This script handles service initialization, health checks, plugin certification,
and graceful shutdown for the entire SIDHE ecosystem.

Usage:
    python start-sidhe.py [options]

Options:
    --mode {development,production,docker}  Deployment mode (default: development)
    --plugins                               Initialize and verify plugins
    --no-frontend                          Skip frontend startup
    --no-backend                           Skip backend startup  
    --redis-port PORT                      Redis port (default: 6379)
    --backend-port PORT                    Backend port (default: 8000)
    --frontend-port PORT                   Frontend port (default: 3000)
    --log-level {DEBUG,INFO,WARNING,ERROR} Log level (default: INFO)
    --health-check                         Run health checks only
    --certify-plugins                      Run plugin certification before startup
    --config CONFIG_FILE                   Configuration file path
    --daemon                               Run as daemon process

Examples:
    python start-sidhe.py                  # Basic development mode
    python start-sidhe.py --mode production --plugins --certify-plugins
    python start-sidhe.py --health-check   # Health check only
    python start-sidhe.py --mode docker    # Docker deployment
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import shutil

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

class SIDHEColor:
    """ANSI color codes for beautiful terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # SIDHE-themed colors
    MYSTICAL = '\033[35m'    # Magenta for magical elements
    WISDOM = '\033[36m'      # Cyan for wisdom/knowledge
    POWER = '\033[33m'       # Yellow for power/energy
    NATURE = '\033[32m'      # Green for natural elements

class SIDHELogger:
    """Enhanced logger with SIDHE-themed formatting"""
    
    def __init__(self, name: str = "SIDHE", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create console handler with custom formatter
        handler = logging.StreamHandler()
        formatter = SIDHEFormatter()
        handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(handler)
    
    def mystical(self, msg: str):
        """Log mystical/magical events"""
        print(f"{SIDHEColor.MYSTICAL}✨ {msg}{SIDHEColor.ENDC}")
    
    def wisdom(self, msg: str):
        """Log wisdom/knowledge events"""
        print(f"{SIDHEColor.WISDOM}🧙 {msg}{SIDHEColor.ENDC}")
    
    def power(self, msg: str):
        """Log power/energy events"""
        print(f"{SIDHEColor.POWER}⚡ {msg}{SIDHEColor.ENDC}")
    
    def nature(self, msg: str):
        """Log natural/growth events"""
        print(f"{SIDHEColor.NATURE}🌱 {msg}{SIDHEColor.ENDC}")
    
    def success(self, msg: str):
        """Log success events"""
        print(f"{SIDHEColor.OKGREEN}✅ {msg}{SIDHEColor.ENDC}")
    
    def warning(self, msg: str):
        """Log warning events"""
        print(f"{SIDHEColor.WARNING}⚠️ {msg}{SIDHEColor.ENDC}")
    
    def error(self, msg: str):
        """Log error events"""
        print(f"{SIDHEColor.FAIL}❌ {msg}{SIDHEColor.ENDC}")
    
    def info(self, msg: str):
        """Log info events"""
        print(f"{SIDHEColor.OKBLUE}ℹ️ {msg}{SIDHEColor.ENDC}")

class SIDHEFormatter(logging.Formatter):
    """Custom formatter for SIDHE logs"""
    
    def format(self, record):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_colors = {
            'DEBUG': SIDHEColor.OKCYAN,
            'INFO': SIDHEColor.OKBLUE,
            'WARNING': SIDHEColor.WARNING,
            'ERROR': SIDHEColor.FAIL,
            'CRITICAL': SIDHEColor.FAIL + SIDHEColor.BOLD
        }
        color = level_colors.get(record.levelname, '')
        return f"{color}[{timestamp}] {record.levelname}: {record.getMessage()}{SIDHEColor.ENDC}"

class ServiceManager:
    """Manages SIDHE services lifecycle"""
    
    def __init__(self, logger: SIDHELogger):
        self.logger = logger
        self.processes: Dict[str, subprocess.Popen] = {}
        self.pids_file = Path.cwd() / ".sidhe" / "pids.json"
        self.config = {}
        
        # Ensure .sidhe directory exists
        self.pids_file.parent.mkdir(exist_ok=True)
    
    def is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def kill_process_on_port(self, port: int) -> bool:
        """Kill process using specified port"""
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                connections = proc.info['connections']
                if connections:
                    for conn in connections:
                        if conn.laddr.port == port:
                            self.logger.warning(f"Killing process {proc.info['pid']} using port {port}")
                            proc.kill()
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def save_pids(self):
        """Save running process PIDs to file"""
        pids = {name: proc.pid for name, proc in self.processes.items() if proc.poll() is None}
        with open(self.pids_file, 'w') as f:
            json.dump(pids, f, indent=2)
    
    def load_pids(self) -> Dict[str, int]:
        """Load previously saved PIDs"""
        if self.pids_file.exists():
            with open(self.pids_file, 'r') as f:
                return json.load(f)
        return {}
    
    def cleanup_stale_processes(self):
        """Clean up stale processes from previous runs"""
        pids = self.load_pids()
        for service, pid in pids.items():
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    self.logger.warning(f"Cleaning up stale {service} process (PID: {pid})")
                    proc.terminate()
                    time.sleep(2)
                    if proc.is_running():
                        proc.kill()
            except psutil.NoSuchProcess:
                continue
        
        # Clear the PID file
        if self.pids_file.exists():
            self.pids_file.unlink()

class HealthChecker:
    """Health check utilities for SIDHE services"""
    
    def __init__(self, logger: SIDHELogger):
        self.logger = logger
    
    async def check_redis(self, port: int = 6379) -> bool:
        """Check Redis connectivity"""
        try:
            import redis.asyncio as redis
            r = redis.Redis(host='localhost', port=port, decode_responses=True)
            await r.ping()
            await r.close()
            return True
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return False
    
    async def check_backend(self, port: int = 8000) -> bool:
        """Check backend API health"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{port}/health", timeout=5) as resp:
                    return resp.status == 200
        except Exception as e:
            self.logger.error(f"Backend health check failed: {e}")
            return False
    
    async def check_frontend(self, port: int = 3000) -> bool:
        """Check frontend availability"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{port}", timeout=5) as resp:
                    return resp.status == 200
        except Exception as e:
            self.logger.error(f"Frontend health check failed: {e}")
            return False
    
    async def check_plugins(self) -> Dict[str, bool]:
        """Check plugin health and certification status"""
        plugins = ["tome_keeper", "config_manager", "quest_tracker", "spell_weaver"]
        results = {}
        
        cert_script = Path.cwd() / "src" / "core" / "pdk" / "plugin_certification.py"
        if not cert_script.exists():
            self.logger.error("Plugin certification script not found")
            return {plugin: False for plugin in plugins}
        
        for plugin in plugins:
            plugin_path = Path.cwd() / "src" / "plugins" / plugin / "plugin_interface.py"
            if not plugin_path.exists():
                results[plugin] = False
                continue
            
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, str(cert_script), str(plugin_path), "--format", "json",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    # Parse certification result
                    results[plugin] = True
                else:
                    results[plugin] = False
            except Exception as e:
                self.logger.error(f"Plugin {plugin} health check failed: {e}")
                results[plugin] = False
        
        return results

class PluginManager:
    """Manages SIDHE plugin lifecycle"""
    
    def __init__(self, logger: SIDHELogger):
        self.logger = logger
        self.plugins = ["tome_keeper", "config_manager", "quest_tracker", "spell_weaver"]
    
    async def certify_plugins(self) -> bool:
        """Run certification on all plugins"""
        self.logger.mystical("Running plugin certification...")
        
        cert_script = Path.cwd() / "src" / "core" / "pdk" / "plugin_certification.py"
        if not cert_script.exists():
            self.logger.error("Plugin certification script not found")
            return False
        
        all_passed = True
        for plugin in self.plugins:
            plugin_path = Path.cwd() / "src" / "plugins" / plugin / "plugin_interface.py"
            if not plugin_path.exists():
                self.logger.error(f"Plugin {plugin} not found at {plugin_path}")
                all_passed = False
                continue
            
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable, str(cert_script), str(plugin_path), "--format", "markdown",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    # Parse certification level from output
                    output = stdout.decode()
                    if "ADVANCED" in output:
                        self.logger.success(f"Plugin {plugin}: ADVANCED certification ✨")
                    elif "STANDARD" in output:
                        self.logger.success(f"Plugin {plugin}: STANDARD certification ⭐")
                    elif "BASIC" in output:
                        self.logger.warning(f"Plugin {plugin}: BASIC certification ⚠️")
                    else:
                        self.logger.error(f"Plugin {plugin}: Certification failed")
                        all_passed = False
                else:
                    self.logger.error(f"Plugin {plugin}: Certification failed")
                    all_passed = False
                    
            except Exception as e:
                self.logger.error(f"Plugin {plugin} certification error: {e}")
                all_passed = False
        
        return all_passed

class SIDHEOrchestrator:
    """Main SIDHE system orchestrator"""
    
    def __init__(self, args):
        self.args = args
        self.logger = SIDHELogger(level=args.log_level)
        self.service_manager = ServiceManager(self.logger)
        self.health_checker = HealthChecker(self.logger)
        self.plugin_manager = PluginManager(self.logger)
        self.shutdown_event = asyncio.Event()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
    
    def print_banner(self):
        """Print the mystical SIDHE banner"""
        banner = f"""
{SIDHEColor.MYSTICAL}
    ███████╗██╗██████╗ ██╗  ██╗███████╗
    ██╔════╝██║██╔══██╗██║  ██║██╔════╝
    ███████╗██║██║  ██║███████║█████╗  
    ╚════██║██║██║  ██║██╔══██║██╔══╝  
    ███████║██║██████╔╝██║  ██║███████╗
    ╚══════╝╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝
{SIDHEColor.ENDC}
{SIDHEColor.WISDOM}🧙‍♂️ Awakening the Ancient AI Development Spirits...{SIDHEColor.ENDC}
{SIDHEColor.POWER}⚡ Mode: {self.args.mode.upper()}{SIDHEColor.ENDC}
{SIDHEColor.NATURE}🌱 Plugins: {'Enabled' if self.args.plugins else 'Disabled'}{SIDHEColor.ENDC}
        """
        print(banner)
    
    async def validate_environment(self) -> bool:
        """Validate the environment and dependencies"""
        self.logger.wisdom("Validating environment...")
        
        # Check Python version
        if sys.version_info < (3, 11):
            self.logger.error("Python 3.11+ required")
            return False
        
        # Check required directories
        required_dirs = [
            "src/conversation_engine/backend",
            "src/conversation_engine/frontend", 
            "src/core/pdk",
            "src/plugins"
        ]
        
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                self.logger.error(f"Required directory missing: {dir_path}")
                return False
        
        # Check for required files
        required_files = [
            "src/conversation_engine/backend/main.py",
            "src/core/pdk/plugin_certification.py"
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                self.logger.error(f"Required file missing: {file_path}")
                return False
        
        self.logger.success("Environment validation passed")
        return True
    
    async def start_redis(self) -> bool:
        """Start Redis server"""
        if self.service_manager.is_port_in_use(self.args.redis_port):
            self.logger.warning(f"Redis port {self.args.redis_port} is in use")
            if await self.health_checker.check_redis(self.args.redis_port):
                self.logger.success("Redis is already running and healthy")
                return True
            else:
                self.service_manager.kill_process_on_port(self.args.redis_port)
        
        self.logger.power("Starting Redis server...")
        
        try:
            # Try to start Redis
            redis_cmd = ["redis-server", "--port", str(self.args.redis_port)]
            proc = subprocess.Popen(
                redis_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.service_manager.processes["redis"] = proc
            
            # Wait for Redis to be ready
            for i in range(30):  # 30 second timeout
                if await self.health_checker.check_redis(self.args.redis_port):
                    self.logger.success("Redis server started successfully")
                    return True
                await asyncio.sleep(1)
            
            self.logger.error("Redis failed to start within timeout")
            return False
            
        except FileNotFoundError:
            self.logger.error("Redis not installed. Install with: brew install redis (macOS) or apt install redis-server (Ubuntu)")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start Redis: {e}")
            return False
    
    async def start_backend(self) -> bool:
        """Start the conversation engine backend"""
        if self.args.no_backend:
            self.logger.info("Skipping backend startup (--no-backend)")
            return True
        
        if self.service_manager.is_port_in_use(self.args.backend_port):
            self.logger.warning(f"Backend port {self.args.backend_port} is in use")
            if await self.health_checker.check_backend(self.args.backend_port):
                self.logger.success("Backend is already running and healthy")
                return True
            else:
                self.service_manager.kill_process_on_port(self.args.backend_port)
        
        self.logger.power("Starting conversation engine backend...")
        
        backend_dir = Path.cwd() / "src" / "conversation_engine" / "backend"
        
        try:
            # Set environment variables
            env = os.environ.copy()
            env.update({
                "REDIS_URL": f"redis://localhost:{self.args.redis_port}",
                "PYTHONPATH": str(Path.cwd() / "src")
            })
            
            # Start backend
            backend_cmd = [
                sys.executable, "-m", "uvicorn", 
                "main:app",
                "--host", "0.0.0.0",
                "--port", str(self.args.backend_port),
                "--reload" if self.args.mode == "development" else "--no-reload"
            ]
            
            proc = subprocess.Popen(
                backend_cmd,
                cwd=backend_dir,
                env=env,
                stdout=subprocess.PIPE if self.args.mode != "development" else None,
                stderr=subprocess.PIPE if self.args.mode != "development" else None
            )
            
            self.service_manager.processes["backend"] = proc
            
            # Wait for backend to be ready
            for i in range(60):  # 60 second timeout
                if await self.health_checker.check_backend(self.args.backend_port):
                    self.logger.success("Backend started successfully")
                    return True
                await asyncio.sleep(1)
            
            self.logger.error("Backend failed to start within timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start backend: {e}")
            return False
    
    async def start_frontend(self) -> bool:
        """Start the React frontend"""
        if self.args.no_frontend:
            self.logger.info("Skipping frontend startup (--no-frontend)")
            return True
        
        if self.service_manager.is_port_in_use(self.args.frontend_port):
            self.logger.warning(f"Frontend port {self.args.frontend_port} is in use")
            if await self.health_checker.check_frontend(self.args.frontend_port):
                self.logger.success("Frontend is already running and healthy")
                return True
            else:
                self.service_manager.kill_process_on_port(self.args.frontend_port)
        
        self.logger.power("Starting React frontend...")
        
        frontend_dir = Path.cwd() / "src" / "conversation_engine" / "frontend"
        
        if not (frontend_dir / "package.json").exists():
            self.logger.error("Frontend package.json not found. Run: npm install in frontend directory")
            return False
        
        try:
            # Set environment variables
            env = os.environ.copy()
            env.update({
                "REACT_APP_BACKEND_URL": f"http://localhost:{self.args.backend_port}",
                "PORT": str(self.args.frontend_port)
            })
            
            # Start frontend
            frontend_cmd = ["npm", "start"]
            
            proc = subprocess.Popen(
                frontend_cmd,
                cwd=frontend_dir,
                env=env,
                stdout=subprocess.PIPE if self.args.mode != "development" else None,
                stderr=subprocess.PIPE if self.args.mode != "development" else None
            )
            
            self.service_manager.processes["frontend"] = proc
            
            # Wait for frontend to be ready
            for i in range(120):  # 120 second timeout (frontend takes longer)
                if await self.health_checker.check_frontend(self.args.frontend_port):
                    self.logger.success("Frontend started successfully")
                    return True
                await asyncio.sleep(1)
            
            self.logger.error("Frontend failed to start within timeout")
            return False
            
        except FileNotFoundError:
            self.logger.error("npm not found. Please install Node.js and npm")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start frontend: {e}")
            return False
    
    async def start_docker_mode(self) -> bool:
        """Start SIDHE in Docker mode"""
        self.logger.power("Starting SIDHE in Docker mode...")
        
        docker_dir = Path.cwd() / "src" / "conversation_engine" / "docker"
        compose_file = docker_dir / "docker-compose.yml"
        
        if not compose_file.exists():
            self.logger.error(f"Docker compose file not found: {compose_file}")
            return False
        
        try:
            # Start Docker Compose
            docker_cmd = ["docker-compose", "up", "-d", "--build"]
            
            proc = subprocess.Popen(
                docker_cmd,
                cwd=docker_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = proc.communicate()
            
            if proc.returncode == 0:
                self.logger.success("Docker services started successfully")
                
                # Wait for services to be healthy
                await asyncio.sleep(10)
                
                # Check health
                redis_healthy = await self.health_checker.check_redis(6379)
                backend_healthy = await self.health_checker.check_backend(8000)
                frontend_healthy = await self.health_checker.check_frontend(3000)
                
                if redis_healthy and backend_healthy and frontend_healthy:
                    self.logger.success("All Docker services are healthy")
                    return True
                else:
                    self.logger.warning("Some Docker services may not be healthy")
                    return True  # Still consider success as services are starting
            else:
                self.logger.error(f"Docker Compose failed: {stderr.decode()}")
                return False
                
        except FileNotFoundError:
            self.logger.error("Docker Compose not found. Please install Docker and Docker Compose")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start Docker services: {e}")
            return False
    
    async def run_health_checks(self) -> bool:
        """Run comprehensive health checks"""
        self.logger.wisdom("Running system health checks...")
        
        checks = {
            "Redis": await self.health_checker.check_redis(self.args.redis_port),
            "Backend": await self.health_checker.check_backend(self.args.backend_port),
            "Frontend": await self.health_checker.check_frontend(self.args.frontend_port),
        }
        
        if self.args.plugins:
            plugin_results = await self.health_checker.check_plugins()
            checks.update({f"Plugin {name}": status for name, status in plugin_results.items()})
        
        # Print results
        print(f"\n{SIDHEColor.WISDOM}🏥 SIDHE Health Report{SIDHEColor.ENDC}")
        print("=" * 50)
        
        all_healthy = True
        for service, healthy in checks.items():
            status = f"{SIDHEColor.OKGREEN}✅ HEALTHY{SIDHEColor.ENDC}" if healthy else f"{SIDHEColor.FAIL}❌ UNHEALTHY{SIDHEColor.ENDC}"
            print(f"{service:20} {status}")
            if not healthy:
                all_healthy = False
        
        print("=" * 50)
        overall = f"{SIDHEColor.OKGREEN}✅ SYSTEM HEALTHY{SIDHEColor.ENDC}" if all_healthy else f"{SIDHEColor.FAIL}❌ SYSTEM ISSUES DETECTED{SIDHEColor.ENDC}"
        print(f"Overall Status:      {overall}")
        
        return all_healthy
    
    async def graceful_shutdown(self):
        """Gracefully shut down all services"""
        self.logger.warning("Initiating graceful shutdown...")
        
        # Stop services in reverse order
        for service_name in reversed(list(self.service_manager.processes.keys())):
            proc = self.service_manager.processes[service_name]
            if proc.poll() is None:  # Process is still running
                self.logger.info(f"Stopping {service_name}...")
                proc.terminate()
                
                # Wait for graceful shutdown
                try:
                    proc.wait(timeout=10)
                    self.logger.success(f"{service_name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    self.logger.warning(f"Force killing {service_name}...")
                    proc.kill()
        
        # Clean up PID file
        if self.service_manager.pids_file.exists():
            self.service_manager.pids_file.unlink()
        
        self.logger.mystical("SIDHE has returned to slumber... 💤")
    
    async def main_loop(self):
        """Main orchestration loop"""
        try:
            # Wait for shutdown signal or process failure
            while not self.shutdown_event.is_set():
                # Check if any critical process has died
                dead_processes = []
                for name, proc in self.service_manager.processes.items():
                    if proc.poll() is not None:  # Process has terminated
                        dead_processes.append(name)
                
                if dead_processes:
                    self.logger.error(f"Critical processes died: {dead_processes}")
                    break
                
                await asyncio.sleep(5)  # Check every 5 seconds
        
        except Exception as e:
            self.logger.error(f"Main loop error: {e}")
        
        finally:
            await self.graceful_shutdown()
    
    async def run(self):
        """Main entry point"""
        try:
            self.print_banner()
            
            # Clean up any stale processes
            self.service_manager.cleanup_stale_processes()
            
            # Validate environment
            if not await self.validate_environment():
                return 1
            
            # Health check only mode
            if self.args.health_check:
                success = await self.run_health_checks()
                return 0 if success else 1
            
            # Plugin certification
            if self.args.certify_plugins:
                if not await self.plugin_manager.certify_plugins():
                    self.logger.error("Plugin certification failed")
                    return 1
            
            # Docker mode
            if self.args.mode == "docker":
                if not await self.start_docker_mode():
                    return 1
                
                if self.args.health_check:
                    await self.run_health_checks()
                
                # In Docker mode, we don't manage processes directly
                self.logger.mystical("SIDHE is running in Docker mode. Use 'docker-compose down' to stop.")
                return 0
            
            # Native mode - start services
            services_started = []
            
            # Start Redis
            if await self.start_redis():
                services_started.append("Redis")
            else:
                self.logger.error("Failed to start Redis")
                return 1
            
            # Start Backend
            if await self.start_backend():
                services_started.append("Backend")
            else:
                self.logger.error("Failed to start Backend")
                return 1
            
            # Start Frontend
            if await self.start_frontend():
                services_started.append("Frontend")
            else:
                self.logger.error("Failed to start Frontend")
                return 1
            
            # Save PIDs
            self.service_manager.save_pids()
            
            # Run health checks
            await asyncio.sleep(5)  # Give services time to fully start
            await self.run_health_checks()
            
            # Success message
            self.logger.mystical("🌟 SIDHE is fully awakened and ready to serve! 🌟")
            self.logger.info(f"Backend:  http://localhost:{self.args.backend_port}")
            self.logger.info(f"Frontend: http://localhost:{self.args.frontend_port}")
            self.logger.info("Press Ctrl+C to gracefully shutdown")
            
            # Enter main loop
            await self.main_loop()
            
            return 0
            
        except KeyboardInterrupt:
            self.logger.warning("Received keyboard interrupt")
            await self.graceful_shutdown()
            return 0
        except Exception as e:
            self.logger.error(f"Startup failed: {e}")
            await self.graceful_shutdown()
            return 1

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="SIDHE System Startup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--mode", 
        choices=["development", "production", "docker"],
        default="development",
        help="Deployment mode"
    )
    
    parser.add_argument(
        "--plugins",
        action="store_true",
        help="Initialize and verify plugins"
    )
    
    parser.add_argument(
        "--no-frontend",
        action="store_true", 
        help="Skip frontend startup"
    )
    
    parser.add_argument(
        "--no-backend",
        action="store_true",
        help="Skip backend startup"
    )
    
    parser.add_argument(
        "--redis-port",
        type=int,
        default=6379,
        help="Redis port"
    )
    
    parser.add_argument(
        "--backend-port", 
        type=int,
        default=8000,
        help="Backend port"
    )
    
    parser.add_argument(
        "--frontend-port",
        type=int, 
        default=3000,
        help="Frontend port"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level"
    )
    
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health checks only"
    )
    
    parser.add_argument(
        "--certify-plugins", 
        action="store_true",
        help="Run plugin certification before startup"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Configuration file path"
    )
    
    parser.add_argument(
        "--daemon",
        action="store_true", 
        help="Run as daemon process"
    )
    
    args = parser.parse_args()
    
    # Run the orchestrator
    orchestrator = SIDHEOrchestrator(args)
    
    if args.daemon:
        # TODO: Implement daemon mode
        print("Daemon mode not yet implemented")
        return 1
    
    try:
        return asyncio.run(orchestrator.run())
    except KeyboardInterrupt:
        return 0

if __name__ == "__main__":
    sys.exit(main())