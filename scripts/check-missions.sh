#!/bin/bash
# File: scripts/check-missions.sh
# Description: Check for open Quests assigned to SIDHE

echo "🚀 SIDHE Quest Status Check"
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
    echo "   Setting default: export GITHUB_REPO=EldestGruff/sidhe"
    export GITHUB_REPO="EldestGruff/sidhe"
fi

echo "📡 Scanning for Quests..."
echo ""

# Use Python GitHub integration to list missions
python3 -c "
import os
import sys
sys.path.append('src')

from plugins.quest_tracker.plugin_interface import QuestTracker

try:
    manager = QuestTracker()
    missions = manager.get_away_quests('open')
    
    if not missions:
        print('No open Quests found.')
    else:
        print(f'Found {len(missions)} open Quest(s):\n')
        for quest in missions:
            print(f\"Quest #{quest['number']}: {quest['title']}\")
            print(f\"  Priority: {quest.get('classification', 'Standard')}\")
            print(f\"  Status: {quest.get('state', 'Unknown')}\")
            print()
        
        print('\nTo implement a quest, run:')
        print('  ./scripts/implement-quest.sh <quest-number>')
        
except Exception as e:
    print(f'Error accessing GitHub: {e}')
    print('Please check your GITHUB_TOKEN and GITHUB_REPO settings.')
"

echo ""
echo "🖖 Apprentice standing by for orders."
