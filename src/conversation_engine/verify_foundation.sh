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
