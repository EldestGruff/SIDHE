#!/bin/bash
# File: scripts/implement-quest.sh
# Description: Implement a specific Quest

MISSION_NUMBER=$1

if [ -z "$MISSION_NUMBER" ]; then
    echo "Usage: $0 <quest-number>"
    echo "Example: $0 2"
    exit 1
fi

echo "📋 Quest Implementation Protocol"
echo "======================================"
echo "Quest Number: #$MISSION_NUMBER"
echo ""

# Check prerequisites
if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_REPO" ]; then
    echo "⚠️  Error: GitHub environment variables not set"
    echo "   Please run:"
    echo "   export GITHUB_TOKEN=your-personal-access-token"
    echo "   export GITHUB_REPO=owner/repo"
    exit 1
fi

echo "🔍 Phase 1: Quest Analysis"
echo "----------------------------"

# Use Python to get quest details and create implementation plan
python3 -c "
import os
import sys
import json
sys.path.append('src')

from plugins.quest_tracker.plugin_interface import QuestTracker
from plugins.quest_tracker.quest_parser import QuestParser

quest_number = $MISSION_NUMBER

try:
    manager = QuestTracker()
    
    # Get quest details
    print(f'Retrieving Quest #{quest_number}...')
    quest = manager.get_quest_details(quest_number)
    
    if not quest:
        print(f'Error: Quest #{quest_number} not found')
        sys.exit(1)
    
    print(f\"Quest Title: {quest['title']}\")
    print(f\"Classification: {quest.get('classification', 'Standard')}\")
    
    # Extract specification reference
    spec_refs = quest.get('referenced_docs', [])
    if spec_refs:
        print(f\"\\nReferenced Specifications:\")
        for spec in spec_refs:
            print(f\"  - {spec}\")
    
    # Save quest data for next phase
    with open('.quest_data.json', 'w') as f:
        json.dump(quest, f)
    
    print(\"\\n✅ Quest analysis complete\")
    
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Quest analysis failed. Aborting."
    exit 1
fi

echo ""
echo "🛠️  Phase 2: Implementation Instructions"
echo "---------------------------------------"
echo ""
echo "Claude Code should now:"
echo ""
echo "1. Read the quest details from GitHub issue #$MISSION_NUMBER"
echo "2. Locate the specification in grimoire/"
echo "3. Create a feature branch: quest-$MISSION_NUMBER-[title]"
echo "4. Implement the component according to the specification"
echo "5. Run tests to verify implementation"
echo "6. Commit changes with message: 'Quest #$MISSION_NUMBER: [description]'"
echo "7. Create a Pull Request linking back to issue #$MISSION_NUMBER"
echo "8. Update the issue with completion status"
echo ""
echo "Example implementation command for Claude Code:"
echo ""
cat << 'EOF'
# Create and checkout feature branch
git checkout -b quest-$MISSION_NUMBER-config-manager

# After implementation, commit changes
git add -A
git commit -m "Quest #$MISSION_NUMBER: Implement Config Manager plugin"

# Push branch
git push origin quest-$MISSION_NUMBER-config-manager

# Create PR using GitHub CLI (if available)
gh pr create --title "Quest #$MISSION_NUMBER: Config Manager Implementation" \
             --body "Implements Config Manager plugin as specified in #$MISSION_NUMBER" \
             --base main
EOF

echo ""
echo "🚀 Ready for implementation!"
echo ""

# Clean up temporary file
rm -f .quest_data.json

