# GitHub Integration Component Specification

## Overview
Create a GitHub integration component that enables SIDHE to read Quests (issues), create implementations, and manage the full development workflow through GitHub.

## Implementation Location
Create all files in: `src/plugins/quest_tracker/`

## Configuration
The component will use environment variables for configuration:
- `GITHUB_TOKEN`: Personal Access Token for authentication
- `GITHUB_REPO`: Repository in format "owner/repo" (e.g., "EldestGruff/sidhe")

## Required Files

### 1. `__init__.py`
Empty file for Python package initialization.

### 2. `plugin_interface.py`
Main GitHub integration interface:

```python
from typing import List, Dict, Any, Optional
import os
from github import Github, GithubException
import re
import logging

logger = logging.getLogger(__name__)

class QuestTracker:
    """Manages all GitHub operations for SIDHE"""
    
    def __init__(self, token: Optional[str] = None, repo_name: Optional[str] = None):
        """
        Initialize GitHub connection
        
        Args:
            token: GitHub Personal Access Token (or from GITHUB_TOKEN env var)
            repo_name: Repository name as "owner/repo" (or from GITHUB_REPO env var)
        """
        # Get token and repo from args or environment
        # Initialize PyGithub client
        # Get repository object
        # Verify access
        pass
    
    def get_away_quests(self, state: str = "open") -> List[Dict[str, Any]]:
        """
        Fetch all Quests (issues with 'quest' label)
        
        Args:
            state: Issue state - "open", "closed", or "all"
            
        Returns:
            List of quest dictionaries with parsed data
        """
        # Get issues with 'quest' label
        # Parse each issue into quest format
        # Return structured data
        pass
    
    def get_quest_details(self, quest_number: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific quest
        
        Args:
            quest_number: GitHub issue number
            
        Returns:
            Parsed quest data including objectives, specs, criteria
        """
        # Get specific issue
        # Parse quest format from body
        # Extract referenced specifications
        # Return complete quest data
        pass
    
    def create_feature_branch(self, quest_number: int, quest_title: str) -> str:
        """
        Create a new branch for the quest
        
        Args:
            quest_number: GitHub issue number
            quest_title: Quest title for branch name
            
        Returns:
            Branch name created
        """
        # Generate branch name: quest-{number}-{slugified-title}
        # Create branch from main
        # Return branch name
        pass
    
    def create_pull_request(self, quest_number: int, branch_name: str, 
                          changes_summary: str) -> int:
        """
        Create a PR for completed quest
        
        Args:
            quest_number: GitHub issue number
            branch_name: Source branch for PR
            changes_summary: Description of changes made
            
        Returns:
            PR number created
        """
        # Create PR from branch to main
        # Link to original issue
        # Add appropriate labels
        # Return PR number
        pass
    
    def update_quest_progress(self, quest_number: int, status: str, 
                               details: str = "") -> bool:
        """
        Update quest progress via issue comment
        
        Args:
            quest_number: GitHub issue number
            status: Current status (e.g., "in-progress", "blocked", "complete")
            details: Additional details about progress
            
        Returns:
            Success boolean
        """
        # Create formatted progress comment
        # Post to issue
        # Update labels if needed
        # Return success status
        pass
    
    def get_specification(self, spec_path: str) -> str:
        """
        Read a specification file from the repository
        
        Args:
            spec_path: Path to spec file (e.g., "grimoire/conversation-engine.md")
            
        Returns:
            Specification content
        """
        # Get file content from repository
        # Decode and return
        pass
```

### 3. `quest_parser.py`
Parse Quest format from GitHub issues:

```python
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class MissionObjective:
    """Represents a quest objective"""
    description: str
    is_primary: bool
    sub_objectives: List[str] = None

@dataclass
class AcceptanceCriteria:
    """Represents an acceptance criterion"""
    description: str
    is_complete: bool = False

@dataclass
class ParsedMission:
    """Complete parsed quest data"""
    number: int
    title: str
    quest_id: str
    classification: str
    quest_type: str
    objectives: List[MissionObjective]
    technical_specs: Dict[str, Any]
    acceptance_criteria: List[AcceptanceCriteria]
    captains_notes: Optional[str]
    referenced_docs: List[str]

class QuestParser:
    """Parse Quest format from issue body"""
    
    def parse_quest(self, issue_number: int, issue_title: str, 
                     issue_body: str) -> ParsedMission:
        """
        Parse GitHub issue into structured quest data
        
        Args:
            issue_number: GitHub issue number
            issue_title: Issue title
            issue_body: Issue body in markdown
            
        Returns:
            Parsed quest object
        """
        # Extract quest ID
        # Parse classification (priority level)
        # Extract objectives section
        # Parse technical specifications
        # Extract acceptance criteria
        # Find referenced documentation
        # Return structured data
        pass
    
    def extract_objectives(self, body: str) -> List[MissionObjective]:
        """Extract and parse quest objectives"""
        pass
    
    def extract_acceptance_criteria(self, body: str) -> List[AcceptanceCriteria]:
        """Extract and parse acceptance criteria"""
        pass
    
    def extract_referenced_docs(self, body: str) -> List[str]:
        """Find all referenced specification documents"""
        pass
```

### 4. `cli.py`
Command-line interface for GitHub operations:

```python
import click
import json
from .plugin_interface import QuestTracker
from .quest_parser import QuestParser

@click.group()
def cli():
    """SIDHE GitHub Integration CLI"""
    pass

@cli.command()
@click.option('--state', default='open', help='Quest state: open, closed, all')
def list_quests(state):
    """List all Quests"""
    manager = QuestTracker()
    missions = manager.get_away_quests(state)
    
    for quest in missions:
        click.echo(f"Quest #{quest['number']}: {quest['title']}")
        click.echo(f"  Status: {quest['state']}")
        click.echo(f"  Priority: {quest['classification']}")
        click.echo()

@cli.command()
@click.argument('quest_number', type=int)
def show_quest(quest_number):
    """Show detailed quest information"""
    manager = QuestTracker()
    quest = manager.get_quest_details(quest_number)
    
    # Pretty print quest details
    click.echo(json.dumps(quest, indent=2))

@cli.command()
@click.argument('quest_number', type=int)
def start_quest(quest_number):
    """Start working on a quest (create branch, update status)"""
    manager = QuestTracker()
    
    # Get quest details
    quest = manager.get_quest_details(quest_number)
    
    # Create feature branch
    branch_name = manager.create_feature_branch(
        quest_number, 
        quest['title']
    )
    
    # Update quest status
    manager.update_quest_progress(
        quest_number,
        "in-progress",
        f"Apprentice has begun implementation on branch `{branch_name}`"
    )
    
    click.echo(f"Quest #{quest_number} started on branch: {branch_name}")

@cli.command()
@click.argument('quest_number', type=int)
@click.option('--summary', prompt='Changes summary', help='Summary of changes made')
def complete_quest(quest_number, summary):
    """Complete a quest (create PR, update status)"""
    # Implementation here
    pass

if __name__ == '__main__':
    cli()
```

### 5. `test_quest_tracker.py`
Test file with mocked GitHub API:

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from .plugin_interface import QuestTracker
from .quest_parser import QuestParser, ParsedMission

# Test QuestTracker
def test_github_manager_init():
    """Test GitHub manager initialization"""
    with patch('github.Github') as mock_github:
        manager = QuestTracker(token="test-token", repo_name="test/repo")
        mock_github.assert_called_once_with("test-token")

def test_get_away_quests():
    """Test fetching quests"""
    # Mock GitHub API responses
    # Test filtering by label
    # Test parsing of issues
    pass

def test_create_feature_branch():
    """Test branch creation"""
    # Mock git operations
    # Test branch naming
    # Test error handling
    pass

# Test QuestParser
def test_parse_quest():
    """Test parsing of quest format"""
    parser = QuestParser()
    
    sample_body = """
# Quest Brief: Implement Test Feature

**Quest ID:** QUEST-001  
**Classification:** 🔴 Priority One  

## 🎯 Quest Objectives

### Primary Objective
Implement the test feature

### Secondary Objectives
- [ ] Write tests
- [ ] Update documentation

## 📋 Acceptance Criteria
- [ ] Feature works as expected
- [ ] All tests pass
    """
    
    result = parser.parse_quest(1, "Test Quest", sample_body)
    
    assert result.quest_id == "QUEST-001"
    assert result.classification == "🔴 Priority One"
    assert len(result.objectives) > 0
    assert len(result.acceptance_criteria) == 2

# Add more tests for each component
```

## Implementation Requirements

1. **Authentication**: Use PyGithub library for GitHub API access
2. **Error Handling**: Graceful handling of API rate limits and network errors
3. **Branch Naming**: Consistent format: `quest-{number}-{slugified-title}`
4. **Progress Updates**: Use markdown formatting for issue comments
5. **Quest Parsing**: Robust regex patterns to handle variations in format

## Dependencies

```txt
PyGithub==2.1.1
click==8.1.7
python-slugify==8.0.1
```

## Usage Examples

### From Python:
```python
# Initialize manager
manager = QuestTracker()

# Get open missions
missions = manager.get_away_quests("open")

# Start working on quest #5
quest = manager.get_quest_details(5)
branch = manager.create_feature_branch(5, quest['title'])
manager.update_quest_progress(5, "in-progress", "Beginning implementation")

# After implementation, create PR
pr_number = manager.create_pull_request(
    quest_number=5,
    branch_name=branch,
    changes_summary="Implemented conversation engine as specified"
)
```

### From CLI:
```bash
# List all open missions
python -m src.plugins.quest_tracker.cli list-missions

# Show details for quest #5
python -m src.plugins.quest_tracker.cli show-quest 5

# Start working on quest #5
python -m src.plugins.quest_tracker.cli start-quest 5

# Complete quest #5
python -m src.plugins.quest_tracker.cli complete-quest 5
```

## Success Criteria

- [ ] Can authenticate with GitHub using PAT
- [ ] Can list and filter Quests
- [ ] Can parse quest format into structured data
- [ ] Can create feature branches programmatically
- [ ] Can create PRs with proper linking
- [ ] Can update issue status via comments
- [ ] CLI provides easy access to all functions
- [ ] Comprehensive error handling for API issues
- [ ] All methods have proper logging

## Integration with Claude Code

Once implemented, Claude Code can use this component to:
1. Read its assigned missions: `manager.get_away_quests()`
2. Get specification details: `manager.get_specification(spec_path)`
3. Create implementation branch: `manager.create_feature_branch()`
4. Update progress: `manager.update_quest_progress()`
5. Submit PR when complete: `manager.create_pull_request()`

This creates the full autonomous development loop!
