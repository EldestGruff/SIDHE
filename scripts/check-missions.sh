#!/bin/bash
# File: scripts/check-missions.sh
# Description: Check for open Away Missions assigned to Riker

echo "🚀 Riker Mission Status Check"
echo "================================"
echo "Stardate: $(date +%Y.%m.%d)"
echo ""

# Check if GitHub token is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  Warning: GITHUB_TOKEN not set"
    echo "   Please run: export GITHUB_TOKEN=your-personal-access-token"
    exit 1
fi

# Check if repo is set
if [ -z "$GITHUB_REPO" ]; then
    echo "⚠️  Warning: GITHUB_REPO not set"
    echo "   Setting default: export GITHUB_REPO=EldestGruff/riker"
    export GITHUB_REPO="EldestGruff/riker"
fi

echo "📡 Scanning for Away Missions..."
echo ""

# Use Python GitHub integration to list missions
python3 -c "
import os
import sys
sys.path.append('src')

from plugins.github_integration.plugin_interface import GitHubManager

try:
    manager = GitHubManager()
    missions = manager.get_away_missions('open')
    
    if not missions:
        print('No open Away Missions found.')
    else:
        print(f'Found {len(missions)} open Away Mission(s):\n')
        for mission in missions:
            print(f\"Mission #{mission['number']}: {mission['title']}\")
            print(f\"  Priority: {mission.get('classification', 'Standard')}\")
            print(f\"  Status: {mission.get('state', 'Unknown')}\")
            print()
        
        print('\nTo implement a mission, run:')
        print('  ./scripts/implement-mission.sh <mission-number>')
        
except Exception as e:
    print(f'Error accessing GitHub: {e}')
    print('Please check your GITHUB_TOKEN and GITHUB_REPO settings.')
"

echo ""
echo "🖖 Number One standing by for orders."
