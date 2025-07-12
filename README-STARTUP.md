# SIDHE System Startup Guide

This guide explains how to start and manage the SIDHE AI development environment using the comprehensive startup script.

## Quick Start

```bash
# Basic development mode startup
python start-sidhe.py

# Production mode with plugin certification
python start-sidhe.py --mode production --plugins --certify-plugins

# Docker deployment
python start-sidhe.py --mode docker

# Health check only
python start-sidhe.py --health-check
```

## Startup Script Features

### 🌟 **Core Capabilities**
- **Service Orchestration**: Manages Redis, Backend API, and React Frontend
- **Plugin Management**: Certifies and initializes all SIDHE plugins
- **Health Monitoring**: Comprehensive health checks for all components
- **Graceful Shutdown**: Clean process termination with signal handling
- **Environment Validation**: Checks dependencies and configuration
- **Multi-Mode Support**: Development, Production, and Docker modes

### 🎨 **SIDHE-Themed Interface**
- Beautiful terminal output with mystical colors and emojis
- Themed logging categories (Mystical ✨, Wisdom 🧙, Power ⚡, Nature 🌱)
- Comprehensive status reporting

## Command Line Options

```bash
python start-sidhe.py [OPTIONS]

Deployment Modes:
  --mode {development,production,docker}  Deployment mode (default: development)

Service Control:
  --no-frontend          Skip frontend startup
  --no-backend           Skip backend startup
  --plugins              Initialize and verify plugins

Port Configuration:
  --redis-port PORT      Redis port (default: 6379)
  --backend-port PORT    Backend port (default: 8000)  
  --frontend-port PORT   Frontend port (default: 3000)

Operations:
  --health-check         Run health checks only
  --certify-plugins      Run plugin certification before startup
  --log-level LEVEL      Log level: DEBUG,INFO,WARNING,ERROR (default: INFO)

Advanced:
  --config CONFIG_FILE   Configuration file path
  --daemon               Run as daemon process (not yet implemented)
```

## Usage Examples

### Development Mode
```bash
# Standard development startup
python start-sidhe.py

# Development with plugin initialization
python start-sidhe.py --plugins

# Development with custom ports
python start-sidhe.py --backend-port 8080 --frontend-port 3001
```

### Production Mode
```bash
# Production startup with full validation
python start-sidhe.py --mode production --plugins --certify-plugins

# Production without frontend (API only)
python start-sidhe.py --mode production --no-frontend --plugins
```

### Docker Mode
```bash
# Start everything in Docker
python start-sidhe.py --mode docker

# Docker with health checks
python start-sidhe.py --mode docker --health-check
```

### Health & Diagnostics
```bash
# Health check only
python start-sidhe.py --health-check

# Plugin certification only
python start-sidhe.py --certify-plugins --health-check

# Verbose debugging
python start-sidhe.py --log-level DEBUG --plugins
```

## Service Architecture

### Components Started
1. **Redis Server** (Port 6379)
   - Message bus for plugin communication
   - Conversation memory storage
   - Workflow persistence

2. **Backend API** (Port 8000)
   - FastAPI conversation engine
   - WebSocket support for real-time communication
   - Plugin orchestration

3. **React Frontend** (Port 3000) 
   - Modern web interface
   - Real-time chat interface
   - System monitoring dashboard

4. **Plugins** (Auto-discovered)
   - `tome_keeper`: Memory management
   - `config_manager`: Configuration handling
   - `quest_tracker`: GitHub integration
   - `spell_weaver`: Workflow automation

### Health Checks

The script performs comprehensive health checks:

```bash
🏥 SIDHE Health Report
==================================================
Redis                ✅ HEALTHY
Backend              ✅ HEALTHY  
Frontend             ✅ HEALTHY
Plugin tome_keeper   ✅ HEALTHY
Plugin config_manager ✅ HEALTHY
Plugin quest_tracker  ✅ HEALTHY
Plugin spell_weaver   ✅ HEALTHY
==================================================
Overall Status:      ✅ SYSTEM HEALTHY
```

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# The script automatically detects and kills conflicting processes
python start-sidhe.py  # Will clean up ports automatically
```

**Missing Dependencies**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for frontend)
cd src/conversation_engine/frontend
npm install

# Install Redis (macOS)
brew install redis

# Install Redis (Ubuntu)
sudo apt install redis-server
```

**Plugin Certification Failures**
```bash
# Run certification separately to debug
python src/core/pdk/plugin_certification.py src/plugins/tome_keeper/plugin_interface.py --format markdown

# Fix and re-certify
python start-sidhe.py --certify-plugins
```

**Environment Issues**
```bash
# Check Python version (requires 3.11+)
python --version

# Validate environment
python start-sidhe.py --health-check
```

### Debug Mode
```bash
# Maximum verbosity
python start-sidhe.py --log-level DEBUG --plugins --certify-plugins
```

## Process Management

### Automatic Cleanup
The script automatically:
- Detects and kills stale processes from previous runs
- Saves process PIDs for tracking
- Handles graceful shutdown on Ctrl+C or SIGTERM

### Manual Process Management
```bash
# Find SIDHE processes
ps aux | grep -E "(redis-server|uvicorn|npm)"

# Kill specific service
kill $(lsof -ti:8000)  # Kill backend on port 8000

# Emergency cleanup
pkill -f "uvicorn main:app"
pkill -f "npm start"
pkill redis-server
```

## Configuration

### Environment Variables
```bash
# Backend configuration
export REDIS_URL="redis://localhost:6379"
export ANTHROPIC_API_KEY="your-api-key"

# Frontend configuration  
export REACT_APP_BACKEND_URL="http://localhost:8000"

# Plugin configuration
export GITHUB_TOKEN="your-github-token"
export GITHUB_REPO="your-repo"
```

### Config File Support
```bash
# Use custom configuration file
python start-sidhe.py --config /path/to/config.yaml
```

## Integration with Development Workflow

### Pre-commit Hooks
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
python start-sidhe.py --certify-plugins --health-check
```

### CI/CD Integration
```bash
# In your CI pipeline
python start-sidhe.py --mode production --health-check --no-frontend
```

### Docker Development
```bash
# Development with Docker
python start-sidhe.py --mode docker

# View Docker logs
docker-compose -f src/conversation_engine/docker/docker-compose.yml logs -f
```

## Advanced Features

### Plugin Hot-Reloading (Development Mode)
- Plugins are automatically reloaded when changed
- Certification runs on plugin updates
- Health checks detect plugin failures

### Monitoring & Observability
- Real-time health monitoring
- Process lifecycle tracking
- Comprehensive error reporting
- Structured logging with timestamps

### Scalability Options
- Multi-instance backend support
- Load balancer ready
- Redis cluster support
- Plugin distribution

## Getting Help

```bash
# Show all options
python start-sidhe.py --help

# Show version and system info
python start-sidhe.py --health-check --log-level DEBUG
```

---

**🧙‍♂️ May the ancient spirits of AI development guide your journey with SIDHE!** ✨