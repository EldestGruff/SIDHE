# SIDHE Quick Start Guide

Get SIDHE up and running in 60 seconds! 🚀

## Prerequisites

1. **Python 3.11+**
2. **Node.js 16+** (for frontend)
3. **Redis** (auto-installed or system package)

## Installation

```bash
# 1. Clone/navigate to SIDHE directory
cd /path/to/sidhe

# 2. Install Python dependencies
pip install -r requirements-startup.txt

# 3. Configure environment variables (REQUIRED)
./setup-env.sh
# Or manually: cp .env.example .env && edit .env

# 4. Install frontend dependencies (if using frontend)
cd src/conversation_engine/frontend
npm install
cd ../../..

# 5. Install Redis (if not installed)
# macOS:
brew install redis

# Ubuntu/Debian:
sudo apt install redis-server

# Or use Docker (see Docker mode below)
```

## Launch Options

### 🚀 Super Quick Start
```bash
# The simplest way - just run this:
./sidhe

# Or equivalently:
python start-sidhe.py
```

### 🛠️ Development Mode
```bash
# Full development setup with plugins
python start-sidhe.py --mode development --plugins

# With plugin certification
python start-sidhe.py --plugins --certify-plugins
```

### 🏭 Production Mode
```bash
# Production with full validation
python start-sidhe.py --mode production --plugins --certify-plugins
```

### 🐳 Docker Mode (Easiest)
```bash
# No local Redis/Node.js needed!
python start-sidhe.py --mode docker
```

### 🏥 Health Check Only
```bash
# Check if everything is working
python start-sidhe.py --health-check
```

## What Gets Started

| Service | Port | Description |
|---------|------|-------------|
| **Redis** | 6379 | Message bus & memory storage |
| **Backend API** | 8000 | FastAPI conversation engine |
| **React Frontend** | 3000 | Web interface |
| **Plugins** | Auto | All 4 certified plugins |

## Access Points

Once started, access SIDHE at:

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Redis**: localhost:6379

## Shell Aliases (Optional)

For even easier access, load the convenience aliases:

```bash
# Add to your ~/.bashrc or ~/.zshrc
source /path/to/sidhe/sidhe-aliases.sh

# Then use simple commands:
sidhe-dev        # Development mode
sidhe-prod       # Production mode
sidhe-docker     # Docker mode
sidhe-health     # Health check
sidhe-certify    # Plugin certification
```

## Troubleshooting

### Port Conflicts
```bash
# The script auto-detects and resolves port conflicts
python start-sidhe.py  # Will handle conflicts automatically
```

### Missing Dependencies
```bash
# Install missing Python packages
pip install -r requirements-startup.txt

# Install Node.js dependencies
cd src/conversation_engine/frontend && npm install
```

### Permission Issues
```bash
# Make scripts executable
chmod +x start-sidhe.py sidhe sidhe-aliases.sh
```

### Redis Issues
```bash
# Check if Redis is running
redis-cli ping

# Start Redis manually (if needed)
redis-server --port 6379
```

## Success Indicators

When SIDHE starts successfully, you'll see:

```
    ███████╗██╗██████╗ ██╗  ██╗███████╗
    ██╔════╝██║██╔══██╗██║  ██║██╔════╝
    ███████╗██║██║  ██║███████║█████╗  
    ╚════██║██║██║  ██║██╔══██║██╔══╝  
    ███████║██║██████╔╝██║  ██║███████╗
    ╚══════╝╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝

🧙‍♂️ Awakening the Ancient AI Development Spirits...

✅ Redis server started successfully
✅ Backend started successfully  
✅ Frontend started successfully

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

🌟 SIDHE is fully awakened and ready to serve! 🌟
Backend:  http://localhost:8000
Frontend: http://localhost:3000
Press Ctrl+C to gracefully shutdown
```

## Next Steps

1. **Visit** http://localhost:3000 to use the web interface
2. **Explore** http://localhost:8000/docs for API documentation  
3. **Read** the full documentation in `README-STARTUP.md`
4. **Develop** with the certified plugin ecosystem

## Emergency Shutdown

```bash
# Graceful shutdown
Ctrl+C

# Force cleanup (if needed)
pkill -f "uvicorn main:app"
pkill -f "npm start"  
pkill redis-server

# Or use the alias (if loaded)
sidhe-clean
```

---

**🧙‍♂️ Welcome to the mystical world of SIDHE AI development!** ✨

For detailed documentation, see `README-STARTUP.md`.