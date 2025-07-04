#!/bin/bash
# File: scripts/implement-mission.sh
# Description: Implement a specific Away Mission

MISSION_NUMBER=$1

if [ -z "$MISSION_NUMBER" ]; then
    echo "Usage: $0 <mission-number>"
    echo "Example: $0 2"
    exit 1
fi

echo "📋 Away Mission Implementation Protocol"
echo "======================================"
echo "Mission Number: #$MISSION_NUMBER"
echo ""

# Check prerequisites
if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_REPO" ]; then
    echo "⚠️  Error: GitHub environment variables not set"
    echo "   Please run:"
    echo "   export GITHUB_TOKEN=your-personal-access-token"
    echo "   export GITHUB_REPO=owner/repo"
    exit 1
fi

echo "🔍 Phase 1: Mission Analysis"
echo "----------------------------"

# Use Python to get mission details and create implementation plan
python3 -c "
import os
import sys
import json
sys.path.append('src')

from plugins.github_integration.plugin_interface import GitHubManager
from plugins.github_integration.mission_parser import MissionParser

mission_number = $MISSION_NUMBER

try:
    manager = GitHubManager()
    
    # Get mission details
    print(f'Retrieving Away Mission #{mission_number}...')
    mission = manager.get_mission_details(mission_number)
    
    if not mission:
        print(f'Error: Mission #{mission_number} not found')
        sys.exit(1)
    
    print(f\"Mission Title: {mission['title']}\")
    print(f\"Classification: {mission.get('classification', 'Standard')}\")
    
    # Extract specification reference
    spec_refs = mission.get('referenced_docs', [])
    if spec_refs:
        print(f\"\\nReferenced Specifications:\")
        for spec in spec_refs:
            print(f\"  - {spec}\")
    
    # Save mission data for next phase
    with open('.mission_data.json', 'w') as f:
        json.dump(mission, f)
    
    print(\"\\n✅ Mission analysis complete\")
    
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Mission analysis failed. Aborting."
    exit 1
fi

echo ""
echo "🛠️  Phase 2: Implementation Instructions"
echo "---------------------------------------"
echo ""
echo "Claude Code should now:"
echo ""
echo "1. Read the mission details from GitHub issue #$MISSION_NUMBER"
echo "2. Locate the specification in crew-quarters/"
echo "3. Create a feature branch: away-mission-$MISSION_NUMBER-[title]"
echo "4. Implement the component according to the specification"
echo "5. Run tests to verify implementation"
echo "6. Commit changes with message: 'Away Mission #$MISSION_NUMBER: [description]'"
echo "7. Create a Pull Request linking back to issue #$MISSION_NUMBER"
echo "8. Update the issue with completion status"
echo ""
echo "Example implementation command for Claude Code:"
echo ""
cat << 'EOF'
# Create and checkout feature branch
git checkout -b away-mission-$MISSION_NUMBER-config-manager

# After implementation, commit changes
git add -A
git commit -m "Away Mission #$MISSION_NUMBER: Implement Config Manager plugin"

# Push branch
git push origin away-mission-$MISSION_NUMBER-config-manager

# Create PR using GitHub CLI (if available)
gh pr create --title "Away Mission #$MISSION_NUMBER: Config Manager Implementation" \
             --body "Implements Config Manager plugin as specified in #$MISSION_NUMBER" \
             --base main
EOF

echo ""
echo "🚀 Ready for implementation!"
echo ""

# Clean up temporary file
rm -f .mission_data.json

