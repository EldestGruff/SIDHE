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
    ["crew-quarters/conversation-engine-spec.md"]="Specification"
    ["src/conversation_engine/docs/claude-handoff.md"]="Handoff Guide"
    ["src/conversation_engine/backend/main.py"]="Backend Main"
    ["src/conversation_engine/backend/config/settings.py"]="Backend Settings"
    ["src/conversation_engine/backend/requirements.txt"]="Backend Requirements"
    ["src/conversation_engine/backend/intent/models.py"]="Intent Models"
    ["src/conversation_engine/backend/websocket/connection.py"]="WebSocket Connection"
    ["src/conversation_engine/frontend/package.json"]="Frontend Package"
    ["src/conversation_engine/frontend/src/App.jsx"]="Frontend App"
    ["src/conversation_engine/frontend/src/components/Chat/ChatInterface.jsx"]="Chat Interface"
    ["src/conversation_engine/docker/docker-compose.yml"]="Docker Compose"
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
    echo "2. Create Away Mission from: .github/ISSUE_TEMPLATE/conversation-engine-mission.md"
    echo "3. Read handoff guide: src/conversation_engine/docs/claude-handoff.md"
    echo ""
    echo "🚀 Ready for Claude Code implementation!"
else
    echo -e "${RED}❌ Foundation incomplete: $MISSING files missing${NC}"
    echo "Please copy the missing artifacts and run this script again."
fi
