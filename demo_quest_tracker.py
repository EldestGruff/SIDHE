#!/usr/bin/env python3
"""
Demo script for SIDHE GitHub Integration

This script demonstrates the GitHub Integration component functionality:
1. Listing open issues with the 'quest' label
2. Parsing quest format from an issue body
3. Showing how the CLI commands would work

Note: This demo uses mock data to demonstrate functionality without requiring
actual GitHub API access.
"""

import json
import os
from datetime import datetime
from unittest.mock import Mock, patch
from src.plugins.quest_tracker.plugin_interface import QuestTracker
from src.plugins.quest_tracker.quest_parser import QuestParser
from src.plugins.quest_tracker.cli import cli

# Sample quest data for demonstration
SAMPLE_MISSION_BODY = """
# Quest Brief: Implement Conversation Engine

**Quest ID:** QUEST-001
**Classification:** 🔴 Priority One
**Type:** Feature Implementation

## 🎯 Quest Objectives

### Primary Objective
Implement a conversation engine that can handle multi-turn conversations with context awareness and memory management.

### Secondary Objectives
- [ ] Design conversation state management
- [ ] Implement context window optimization
- [ ] Add conversation history persistence
- [ ] Create conversation branching support
- [ ] Add conversation analytics

## 🔧 Technical Specifications
- **Framework:** Python with async/await
- **Storage:** SQLite for conversation history
- **Memory:** Redis for session state
- **API:** RESTful endpoints with WebSocket support

## 📋 Acceptance Criteria
- [ ] Can maintain conversation context across multiple turns
- [ ] Supports concurrent conversations
- [ ] Conversation history is persisted
- [ ] Memory usage stays within defined limits
- [ ] All endpoints have proper error handling
- [ ] Comprehensive test coverage (>90%)
- [ ] Documentation is complete

## 👨‍✈️ Archmage's Notes
This is a foundational component for the SIDHE system. The conversation engine
will be used by multiple other components, so it needs to be robust and well-tested.

Pay special attention to memory management and performance optimization.

## Referenced Documents
- [Conversation Engine Spec](grimoire/conversation-engine-spec.md)
- [Memory Management Guidelines](grimoire/memory-management.md)
- [API Design Standards](grimoire/api-standards.md)
"""

def create_mock_issue(number, title, body, state="open"):
    """Create a mock GitHub issue for demonstration"""
    mock_issue = Mock()
    mock_issue.number = number
    mock_issue.title = title
    mock_issue.body = body
    mock_issue.state = state
    mock_issue.html_url = f"https://github.com/EldestGruff/sidhe/issues/{number}"
    mock_issue.created_at = Mock()
    mock_issue.created_at.isoformat.return_value = "2023-07-01T10:00:00Z"
    mock_issue.updated_at = Mock()
    mock_issue.updated_at.isoformat.return_value = "2023-07-02T15:30:00Z"
    # Create proper mock label
    mock_label = Mock()
    mock_label.name = 'quest'
    mock_issue.labels = [mock_label]
    return mock_issue

def demo_quest_parsing():
    """Demonstrate quest parsing functionality"""
    print("🎯 DEMO: Quest Parsing")
    print("=" * 50)
    
    parser = QuestParser()
    
    # Parse the sample quest
    parsed_quest = parser.parse_quest(1, "Implement Conversation Engine", SAMPLE_MISSION_BODY)
    
    print(f"Quest Number: {parsed_quest.number}")
    print(f"Title: {parsed_quest.title}")
    print(f"Quest ID: {parsed_quest.quest_id}")
    print(f"Classification: {parsed_quest.classification}")
    print(f"Type: {parsed_quest.quest_type}")
    
    print(f"\nObjectives ({len(parsed_quest.objectives)}):")
    for i, obj in enumerate(parsed_quest.objectives, 1):
        marker = "🎯 PRIMARY" if obj.is_primary else "  • Secondary"
        print(f"  {i}. {marker}: {obj.description}")
    
    print(f"\nTechnical Specifications:")
    for key, value in parsed_quest.technical_specs.items():
        print(f"  {key}: {value}")
    
    print(f"\nAcceptance Criteria ({len(parsed_quest.acceptance_criteria)}):")
    for i, ac in enumerate(parsed_quest.acceptance_criteria, 1):
        status = "✅" if ac.is_complete else "❌"
        print(f"  {i}. {status} {ac.description}")
    
    print(f"\nCaptain's Notes:")
    print(f"  {parsed_quest.captains_notes}")
    
    print(f"\nReferenced Documents ({len(parsed_quest.referenced_docs)}):")
    for doc in parsed_quest.referenced_docs:
        print(f"  • {doc}")
    
    print("\n" + "=" * 50)
    return parsed_quest

def demo_github_manager():
    """Demonstrate GitHub Manager functionality with mocked data"""
    print("\n🚀 DEMO: GitHub Manager")
    print("=" * 50)
    
    # Create mock data
    mock_issues = [
        create_mock_issue(1, "Implement Conversation Engine", SAMPLE_MISSION_BODY),
        create_mock_issue(2, "Add Memory Management", """
# Quest Brief: Memory Management System

**Quest ID:** QUEST-002
**Classification:** 🟠 Priority Two
**Type:** Feature Implementation

## 🎯 Quest Objectives

### Primary Objective
Implement memory management for conversation contexts

## 📋 Acceptance Criteria
- [ ] Memory usage tracking
- [ ] Automatic cleanup of old conversations
"""),
        create_mock_issue(3, "Fix Authentication Bug", """
# Quest Brief: Authentication Issue

**Quest ID:** QUEST-003
**Classification:** 🔴 Priority One
**Type:** Bug Fix

## 🎯 Quest Objectives

### Primary Objective
Fix the authentication timeout issue

## 📋 Acceptance Criteria
- [ ] Users can stay logged in for full session
- [ ] No unexpected logouts
""")
    ]
    
    # Mock the GitHub API calls
    with patch('src.plugins.quest_tracker.plugin_interface.Github') as mock_github:
        mock_repo = Mock()
        mock_repo.name = "sidhe"
        mock_repo.get_issues.return_value = mock_issues
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # Create manager (will use mocked data)
        manager = QuestTracker(token="demo-token", repo_name="EldestGruff/sidhe")
        
        print("Connected to GitHub repository: EldestGruff/sidhe")
        print(f"Found {len(mock_issues)} quests")
        
        # Get all quests
        missions = manager.get_away_quests("open")
        
        print(f"\n📋 Quests Summary:")
        for quest in missions:
            print(f"  #{quest['number']}: {quest['title']}")
            print(f"    Status: {quest['state']}")
            print(f"    Priority: {quest['classification']}")
            print(f"    Type: {quest['quest_type']}")
            print(f"    Objectives: {len(quest['objectives'])}")
            print(f"    Acceptance Criteria: {len(quest['acceptance_criteria'])}")
            print()
        
        # Get detailed quest info - fix the label issue
        mock_label = Mock()
        mock_label.name = 'quest'
        mock_issue_detail = mock_issues[0]
        mock_issue_detail.labels = [mock_label]
        mock_repo.get_issue.return_value = mock_issue_detail
        quest_details = manager.get_quest_details(1)
        
        print(f"📄 Detailed Quest #1:")
        print(f"  Quest ID: {quest_details['quest_id']}")
        print(f"  Classification: {quest_details['classification']}")
        if quest_details['objectives']:
            print(f"  Primary Objective: {quest_details['objectives'][0]['description']}")
        else:
            print("  Primary Objective: [Parsing failed - no objectives found]")
        print(f"  Total Acceptance Criteria: {len(quest_details['acceptance_criteria'])}")
        print(f"  Technical Specs: {len(quest_details['technical_specs'])} items")
        
    print("\n" + "=" * 50)
    return missions

def demo_cli_commands():
    """Demonstrate CLI command usage"""
    print("\n💻 DEMO: CLI Commands")
    print("=" * 50)
    
    print("The following CLI commands would be available:")
    print()
    
    print("1. List all open quests:")
    print("   python -m src.plugins.quest_tracker.cli list-missions")
    print("   python -m src.plugins.quest_tracker.cli list-missions --state=all")
    print()
    
    print("2. Show detailed quest information:")
    print("   python -m src.plugins.quest_tracker.cli show-quest 1")
    print("   python -m src.plugins.quest_tracker.cli show-quest 1 --format=json")
    print()
    
    print("3. Start working on a quest:")
    print("   python -m src.plugins.quest_tracker.cli start-quest 1")
    print("   # This creates a branch and updates the issue status")
    print()
    
    print("4. Update quest status:")
    print("   python -m src.plugins.quest_tracker.cli update-status 1 in-progress")
    print("   python -m src.plugins.quest_tracker.cli update-status 1 blocked --details='Waiting for API documentation'")
    print()
    
    print("5. Complete a quest:")
    print("   python -m src.plugins.quest_tracker.cli complete-quest 1")
    print("   # This creates a PR and updates the issue status")
    print()
    
    print("6. Get specification file:")
    print("   python -m src.plugins.quest_tracker.cli get-spec grimoire/conversation-engine-spec.md")
    print()
    
    print("7. Test connection:")
    print("   python -m src.plugins.quest_tracker.cli test-connection")
    print()
    
    print("Environment variables needed:")
    print("  export GITHUB_TOKEN='your_personal_access_token'")
    print("  export GITHUB_REPO='EldestGruff/sidhe'")
    print()
    
    print("=" * 50)

def demo_workflow():
    """Demonstrate a complete workflow"""
    print("\n🔄 DEMO: Complete Workflow")
    print("=" * 50)
    
    print("Typical workflow for an quest:")
    print()
    
    print("1. 📋 List available missions:")
    print("   → Shows all open issues with 'quest' label")
    print("   → Engineer selects a quest to work on")
    print()
    
    print("2. 🎯 Get quest details:")
    print("   → Parse quest format from issue body")
    print("   → Review objectives and acceptance criteria")
    print("   → Check referenced specifications")
    print()
    
    print("3. 🚀 Start quest:")
    print("   → Create feature branch: quest-1-implement-conversation-engine")
    print("   → Update issue status to 'in-progress'")
    print("   → Post progress comment to issue")
    print()
    
    print("4. 💻 Implement solution:")
    print("   → Work on the code in the feature branch")
    print("   → Update progress as needed")
    print("   → Run tests and ensure quality")
    print()
    
    print("5. ✅ Complete quest:")
    print("   → Create pull request with quest summary")
    print("   → Link PR to original issue")
    print("   → Update issue status to 'complete'")
    print("   → Add appropriate labels")
    print()
    
    print("6. 👥 Review and merge:")
    print("   → Team reviews the PR")
    print("   → Quest is merged to main branch")
    print("   → Issue is automatically closed")
    print()
    
    print("=" * 50)

def main():
    """Run all demonstrations"""
    print("🚀 SIDHE GITHUB INTEGRATION DEMO")
    print("=" * 50)
    print()
    print("This demo shows the GitHub Integration component functionality")
    print("without requiring actual GitHub API access.")
    print()
    
    # Check if running with actual credentials
    if os.getenv('GITHUB_TOKEN') and os.getenv('GITHUB_REPO'):
        print("⚠️  GITHUB_TOKEN and GITHUB_REPO detected!")
        print("   This demo will use mock data for safety.")
        print("   To test with real data, use the CLI commands directly.")
        print()
    else:
        print("ℹ️  No GitHub credentials detected (this is expected for demo)")
        print("   Using mock data to demonstrate functionality.")
        print()
    
    try:
        # Run demonstrations
        parsed_quest = demo_quest_parsing()
        missions = demo_github_manager()
        demo_cli_commands()
        demo_workflow()
        
        print("\n🎉 DEMO COMPLETE!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("1. Set up GitHub credentials:")
        print("   export GITHUB_TOKEN='your_personal_access_token'")
        print("   export GITHUB_REPO='EldestGruff/sidhe'")
        print()
        print("2. Install dependencies:")
        print("   pip install PyGithub==2.1.1 click==8.1.7 python-slugify==8.0.1")
        print()
        print("3. Try the CLI commands:")
        print("   python -m src.plugins.quest_tracker.cli list-missions")
        print()
        print("4. Run the tests:")
        print("   python -m pytest src/plugins/quest_tracker/test_quest_tracker.py")
        print()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("This is expected if dependencies are not installed.")
        print()
        print("To run the demo successfully:")
        print("1. pip install PyGithub==2.1.1 click==8.1.7 python-slugify==8.0.1")
        print("2. python demo_quest_tracker.py")

if __name__ == "__main__":
    main()