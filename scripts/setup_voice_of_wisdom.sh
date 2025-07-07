#!/bin/bash

# Conversation Engine Foundation Setup Script
# Creates structure and guides artifact enchantment for when you're not feeling sharp
# 
# Usage: bash setup_voice_of_wisdom.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}[Step $1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Verify we're in the right place
if [[ ! -d ".git" ]] || [[ ! -f "README.md" ]] || [[ ! -d "src" ]]; then
    print_error "This doesn't look like the root of your SIDHE project."
    echo "Please run this script from the SIDHE project root directory."
    exit 1
fi

echo "🚀 SIDHE Conversation Engine Foundation Setup"
echo "============================================="
echo "Setting up foundation structure and guiding artifact enchantment..."
echo ""

# Step 1: Create directory structure
print_step "1" "Creating complete directory structure..."

mkdir -p src/voice_of_wisdom/{docs,docker}
mkdir -p src/voice_of_wisdom/backend/{config,websocket,intent,bus,memory,plugins}
mkdir -p src/voice_of_wisdom/frontend/{public,src/{components/{Chat,Dashboard},hooks,services}}
mkdir -p src/voice_of_wisdom/tests/{backend,frontend,integration}

# Create Python package files
touch src/voice_of_wisdom/backend/__init__.py
touch src/voice_of_wisdom/backend/config/__init__.py
touch src/voice_of_wisdom/backend/websocket/__init__.py
touch src/voice_of_wisdom/backend/intent/__init__.py
touch src/voice_of_wisdom/backend/bus/__init__.py
touch src/voice_of_wisdom/backend/memory/__init__.py
touch src/voice_of_wisdom/backend/plugins/__init__.py

print_success "Directory structure created"

# Step 2: Create artifact enchantment guide
print_step "2" "Creating artifact enchantment guide..."

cat > src/voice_of_wisdom/ARTIFACT_DEPLOYMENT.md << 'EOF'
# Artifact Deployment Guide

Copy each Claude artifact to its designated location:

## 📋 Artifact → File Mapping

| Artifact Name | Copy To Location |
|---------------|------------------|
| `voice_of_wisdom_spec` | `grimoire/conversation-engine-spec.md` |
| `claude_handoff_guide` | `src/voice_of_wisdom/docs/claude-handoff.md` |
| `away_quest_template` | `.github/ISSUE_TEMPLATE/conversation-engine-quest.md` |
| `backend_main_py` | `src/voice_of_wisdom/backend/main.py` |
| `backend_settings` | `src/voice_of_wisdom/backend/config/settings.py` |
| `backend_requirements` | `src/voice_of_wisdom/backend/requirements.txt` |
| `intent_models` | `src/voice_of_wisdom/backend/intent/models.py` |
| `websocket_connection` | `src/voice_of_wisdom/backend/websocket/connection.py` |
| `backend_test_example` | `src/voice_of_wisdom/tests/backend/test_main.py` |
| `frontend_package_json` | `src/voice_of_wisdom/frontend/package.json` |
| `frontend_app_jsx` | `src/voice_of_wisdom/frontend/src/App.jsx` |
| `chat_interface` | `src/voice_of_wisdom/frontend/src/components/Chat/ChatInterface.jsx` |
| `message_list` | `src/voice_of_wisdom/frontend/src/components/Chat/MessageList.jsx` |
| `message_input` | `src/voice_of_wisdom/frontend/src/components/Chat/MessageInput.jsx` |
| `typing_indicator` | `src/voice_of_wisdom/frontend/src/components/Chat/TypingIndicator.jsx` |
| `websocket_hook` | `src/voice_of_wisdom/frontend/src/hooks/useWebSocket.js` |
| `conversation_hook` | `src/voice_of_wisdom/frontend/src/hooks/useConversation.js` |
| `docker_compose_config` | `src/voice_of_wisdom/docker/docker-compose.yml` |
| `dockerfile_backend` | `src/voice_of_wisdom/docker/Dockerfile.backend` |
| `dockerfile_frontend` | `src/voice_of_wisdom/docker/Dockerfile.frontend` |

## ✅ After copying all artifacts, run: bash verify_foundation.sh
EOF

print_success "Artifact enchantment guide created"

# Step 3: Create missing essential files
print_step "3" "Creating essential framework files..."

# Intent parser placeholder
cat > src/voice_of_wisdom/backend/intent/parser.py << 'EOF'
"""
Intent Parser - For Claude Code to implement
LLM-based intent parsing with structured outputs
"""
from typing import Optional
from .models import ConversationIntent, ConversationContext

class IntentParser:
    """LLM-based intent parser - Implementation needed by Claude Code"""
    
    def __init__(self):
        # TODO: Initialize LLM client (Anthropic API)
        pass
    
    async def parse_intent(self, user_input: str, conversation_id: Optional[str] = None) -> ConversationIntent:
        """
        Parse user input into structured intent
        
        TODO: Implement using Anthropic API with structured outputs
        Returns ConversationIntent with type, confidence, entities, etc.
        """
        # Placeholder implementation for Claude Code
        return ConversationIntent(
            type="question",
            confidence=0.0,
            entities={},
            requires_plugins=[],
            complexity="simple"
        )
EOF

# Message bus placeholder
cat > src/voice_of_wisdom/backend/bus/publisher.py << 'EOF'
"""
Message Bus Publisher - Basic structure for Claude Code to implement
Redis pub/sub message bus for plugin communication
"""
import redis.asyncio as redis
import json
import asyncio
import logging
from typing import Dict, Any, Optional

class MessageBus:
    """Redis-based message bus for plugin communication"""
    
    def __init__(self):
        self.redis_client = None
        self.pubsub = None
    
    async def initialize(self):
        """Initialize Redis connection - Implementation needed by Claude Code"""
        # TODO: Implement Redis connection setup
        logging.info("Message bus initialization - TODO for Claude Code")
    
    async def publish(self, topic: str, message: Dict[str, Any]):
        """Publish message - Implementation needed by Claude Code"""
        # TODO: Implement message publishing
        pass
    
    async def request_response(self, plugin_id: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Request/response pattern - Implementation needed by Claude Code"""
        # TODO: Implement request/response pattern
        return {"status": "todo", "message": "Implementation needed by Claude Code"}
    
    async def health_check(self) -> str:
        """Health check - Implementation needed by Claude Code"""
        return "todo"
EOF

# Memory integration placeholder
cat > src/voice_of_wisdom/backend/memory/integration.py << 'EOF'
"""
Memory Integration - Basic structure for Claude Code to implement
Integration with existing Memory Manager plugin
"""
import logging
from typing import Dict, Any, List

class ConversationMemory:
    """Integration with Memory Manager plugin"""
    
    def __init__(self):
        # TODO: Initialize Memory Manager plugin integration
        pass
    
    async def store_turn(self, conversation_id: str, turn_data: Dict[str, Any]) -> bool:
        """Store conversation turn - Implementation needed by Claude Code"""
        # TODO: Implement conversation storage
        logging.info(f"Storing turn for {conversation_id} - TODO for Claude Code")
        return True
    
    async def health_check(self) -> str:
        """Health check - Implementation needed by Claude Code"""
        return "todo"
EOF

# Plugin registry placeholder  
cat > src/voice_of_wisdom/backend/plugins/registry.py << 'EOF'
"""
Plugin Registry - Basic structure for Claude Code to implement
Discovery and communication with existing plugins
"""
import logging
from typing import Dict, Any

class PluginRegistry:
    """Registry for plugin discovery and management"""
    
    def __init__(self):
        self.plugins = {}
    
    async def discover_plugins(self):
        """Discover plugins - Implementation needed by Claude Code"""
        # TODO: Implement plugin discovery
        logging.info("Plugin discovery - TODO for Claude Code")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get plugin status - Implementation needed by Claude Code"""
        return {"status": "todo", "plugins": []}
EOF

# React index.js
cat > src/voice_of_wisdom/frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# React index.html
cat > src/voice_of_wisdom/frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>SIDHE Conversation Engine</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

# Basic CSS
cat > src/voice_of_wisdom/frontend/src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
EOF

cat > src/voice_of_wisdom/frontend/src/App.css << 'EOF'
.App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
}
EOF

print_success "Essential framework files created"

# Step 4: Create environment configuration
print_step "4" "Setting up environment configuration..."

cat > src/voice_of_wisdom/.env.example << 'EOF'
# Conversation Engine Environment Variables
# Copy this file to .env and update with your values

# Required: Anthropic API Key
ANTHROPIC_API_KEY=your_api_key_here

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Application Configuration
CONVERSATION_ENGINE_DEBUG=true
CONVERSATION_ENGINE_LOG_LEVEL=INFO
CONVERSATION_ENGINE_HOST=localhost
CONVERSATION_ENGINE_PORT=8000

# LLM Configuration
LLM_MODEL=claude-3-sonnet-20240229
LLM_TEMPERATURE=0.1
MAX_CONTEXT_TOKENS=4000

# Frontend Configuration
REACT_APP_BACKEND_URL=http://localhost:8000
EOF

if [[ ! -f "src/voice_of_wisdom/.env" ]]; then
    cp src/voice_of_wisdom/.env.example src/voice_of_wisdom/.env
    print_warning "Created .env file - please update ANTHROPIC_API_KEY"
else
    print_warning ".env file already exists - verify configuration"
fi

print_success "Environment configuration ready"

# Step 5: Create verification script
print_step "5" "Creating foundation verification script..."

cat > src/voice_of_wisdom/verify_foundation.sh << 'EOF'
#!/bin/bash

# Foundation Verification Script
# Run this after copying all artifacts

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Verifying Conversation Engine Foundation"
echo "=========================================="

MISSING=0

# Check artifacts
declare -A files=(
    ["grimoire/conversation-engine-spec.md"]="Specification"
    ["src/voice_of_wisdom/docs/claude-handoff.md"]="Handoff Guide"
    ["src/voice_of_wisdom/backend/main.py"]="Backend Main"
    ["src/voice_of_wisdom/backend/config/settings.py"]="Backend Settings"
    ["src/voice_of_wisdom/backend/requirements.txt"]="Backend Requirements"
    ["src/voice_of_wisdom/backend/intent/models.py"]="Intent Models"
    ["src/voice_of_wisdom/backend/websocket/connection.py"]="WebSocket Connection"
    ["src/voice_of_wisdom/frontend/package.json"]="Frontend Package"
    ["src/voice_of_wisdom/frontend/src/App.jsx"]="Frontend App"
    ["src/voice_of_wisdom/frontend/src/components/Chat/ChatInterface.jsx"]="Chat Interface"
    ["src/voice_of_wisdom/docker/docker-compose.yml"]="Docker Compose"
)

for file in "${!files[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅${NC} ${files[$file]}: $file"
    else
        echo -e "${RED}❌${NC} ${files[$file]}: $file"
        ((MISSING++))
    fi
done

echo ""
if [[ $MISSING -eq 0 ]]; then
    echo -e "${GREEN}🎉 Foundation verification complete! All artifacts deployed.${NC}"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Update .env file with your Anthropic API key"
    echo "2. Create Quest from: .github/ISSUE_TEMPLATE/conversation-engine-quest.md"
    echo "3. Read handoff guide: src/voice_of_wisdom/docs/claude-handoff.md"
    echo ""
    echo "🚀 Ready for Claude Code implementation!"
else
    echo -e "${RED}❌ Foundation incomplete: $MISSING files missing${NC}"
    echo "Please copy the missing artifacts and run this script again."
fi
EOF

chmod +x src/voice_of_wisdom/verify_foundation.sh

print_success "Verification script created"

# Final instructions
echo ""
echo "🎉 Foundation Structure Setup Complete!"
echo "======================================"
echo ""
echo "📋 Next Steps:"
echo ""
print_step "A" "Copy all 20 artifacts using the enchantment guide:"
echo "    📄 src/voice_of_wisdom/ARTIFACT_DEPLOYMENT.md"
echo ""
print_step "B" "Verify foundation after copying artifacts:"
echo "    🔍 bash src/voice_of_wisdom/verify_foundation.sh"
echo ""
print_step "C" "Update environment configuration:"
echo "    📝 src/voice_of_wisdom/.env"
echo ""
print_step "D" "Install dependencies (optional):"
echo "    🐍 cd src/voice_of_wisdom/backend && pip install -r requirements.txt"
echo "    📦 cd src/voice_of_wisdom/frontend && npm install"
echo ""
print_step "E" "Create Quest for Claude Code:"
echo "    🚀 Use template: .github/ISSUE_TEMPLATE/conversation-engine-quest.md"
echo ""
echo "📖 Documentation:"
echo "   • Specification: grimoire/conversation-engine-spec.md"
echo "   • Handoff Guide: src/voice_of_wisdom/docs/claude-handoff.md"
echo "   • Deployment Guide: src/voice_of_wisdom/ARTIFACT_DEPLOYMENT.md"
echo ""
echo "🖖 Foundation structure ready - just copy the artifacts and verify!"
echo "   Run: bash src/voice_of_wisdom/verify_foundation.sh"