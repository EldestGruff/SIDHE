# GitHub Integration Component Specification

## Overview
Create a GitHub integration component that enables Riker to read Away Missions (issues), create implementations, and manage the full development workflow through GitHub.

## Implementation Location
Create all files in: `src/plugins/github_integration/`

## Configuration
The component will use environment variables for configuration:
- `GITHUB_TOKEN`: Personal Access Token for authentication
- `GITHUB_REPO`: Repository in format "owner/repo" (e.g., "EldestGruff/riker")

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

class GitHubManager:
    """Manages all GitHub operations for Riker"""
    
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
    
    def get_away_missions(self, state: str = "open") -> List[Dict[str, Any]]:
        """
        Fetch all Away Missions (issues with 'away-mission' label)
        
        Args:
            state: Issue state - "open", "closed", or "all"
            
        Returns:
            List of mission dictionaries with parsed data
        """
        # Get issues with 'away-mission' label
        # Parse each issue into mission format
        # Return structured data
        pass
    
    def get_mission_details(self, mission_number: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific mission
        
        Args:
            mission_number: GitHub issue number
            
        Returns:
            Parsed mission data including objectives, specs, criteria
        """
        # Get specific issue
        # Parse mission format from body
        # Extract referenced specifications
        # Return complete mission data
        pass
    
    def create_feature_branch(self, mission_number: int, mission_title: str) -> str:
        """
        Create a new branch for the mission
        
        Args:
            mission_number: GitHub issue number
            mission_title: Mission title for branch name
            
        Returns:
            Branch name created
        """
        # Generate branch name: away-mission-{number}-{slugified-title}
        # Create branch from main
        # Return branch name
        pass
    
    def create_pull_request(self, mission_number: int, branch_name: str, 
                          changes_summary: str) -> int:
        """
        Create a PR for completed mission
        
        Args:
            mission_number: GitHub issue number
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
    
    def update_mission_progress(self, mission_number: int, status: str, 
                               details: str = "") -> bool:
        """
        Update mission progress via issue comment
        
        Args:
            mission_number: GitHub issue number
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
            spec_path: Path to spec file (e.g., "crew-quarters/conversation-engine.md")
            
        Returns:
            Specification content
        """
        # Get file content from repository
        # Decode and return
        pass
```

### 3. `mission_parser.py`
Parse Away Mission format from GitHub issues:

```python
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class MissionObjective:
    """Represents a mission objective"""
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
    """Complete parsed mission data"""
    number: int
    title: str
    mission_id: str
    classification: str
    mission_type: str
    objectives: List[MissionObjective]
    technical_specs: Dict[str, Any]
    acceptance_criteria: List[AcceptanceCriteria]
    captains_notes: Optional[str]
    referenced_docs: List[str]

class MissionParser:
    """Parse Away Mission format from issue body"""
    
    def parse_mission(self, issue_number: int, issue_title: str, 
                     issue_body: str) -> ParsedMission:
        """
        Parse GitHub issue into structured mission data
        
        Args:
            issue_number: GitHub issue number
            issue_title: Issue title
            issue_body: Issue body in markdown
            
        Returns:
            Parsed mission object
        """
        # Extract mission ID
        # Parse classification (priority level)
        # Extract objectives section
        # Parse technical specifications
        # Extract acceptance criteria
        # Find referenced documentation
        # Return structured data
        pass
    
    def extract_objectives(self, body: str) -> List[MissionObjective]:
        """Extract and parse mission objectives"""
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
from .plugin_interface import GitHubManager
from .mission_parser import MissionParser

@click.group()
def cli():
    """Riker GitHub Integration CLI"""
    pass

@cli.command()
@click.option('--state', default='open', help='Mission state: open, closed, all')
def list_missions(state):
    """List all Away Missions"""
    manager = GitHubManager()
    missions = manager.get_away_missions(state)
    
    for mission in missions:
        click.echo(f"Mission #{mission['number']}: {mission['title']}")
        click.echo(f"  Status: {mission['state']}")
        click.echo(f"  Priority: {mission['classification']}")
        click.echo()

@cli.command()
@click.argument('mission_number', type=int)
def show_mission(mission_number):
    """Show detailed mission information"""
    manager = GitHubManager()
    mission = manager.get_mission_details(mission_number)
    
    # Pretty print mission details
    click.echo(json.dumps(mission, indent=2))

@cli.command()
@click.argument('mission_number', type=int)
def start_mission(mission_number):
    """Start working on a mission (create branch, update status)"""
    manager = GitHubManager()
    
    # Get mission details
    mission = manager.get_mission_details(mission_number)
    
    # Create feature branch
    branch_name = manager.create_feature_branch(
        mission_number, 
        mission['title']
    )
    
    # Update mission status
    manager.update_mission_progress(
        mission_number,
        "in-progress",
        f"Number One has begun implementation on branch `{branch_name}`"
    )
    
    click.echo(f"Mission #{mission_number} started on branch: {branch_name}")

@cli.command()
@click.argument('mission_number', type=int)
@click.option('--summary', prompt='Changes summary', help='Summary of changes made')
def complete_mission(mission_number, summary):
    """Complete a mission (create PR, update status)"""
    # Implementation here
    pass

if __name__ == '__main__':
    cli()
```

### 5. `test_github_integration.py`
Test file with mocked GitHub API:

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from .plugin_interface import GitHubManager
from .mission_parser import MissionParser, ParsedMission

# Test GitHubManager
def test_github_manager_init():
    """Test GitHub manager initialization"""
    with patch('github.Github') as mock_github:
        manager = GitHubManager(token="test-token", repo_name="test/repo")
        mock_github.assert_called_once_with("test-token")

def test_get_away_missions():
    """Test fetching away missions"""
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

# Test MissionParser
def test_parse_mission():
    """Test parsing of mission format"""
    parser = MissionParser()
    
    sample_body = """
# Away Mission Brief: Implement Test Feature

**Mission ID:** AWAY-001  
**Classification:** 🔴 Priority One  

## 🎯 Mission Objectives

### Primary Objective
Implement the test feature

### Secondary Objectives
- [ ] Write tests
- [ ] Update documentation

## 📋 Acceptance Criteria
- [ ] Feature works as expected
- [ ] All tests pass
    """
    
    result = parser.parse_mission(1, "Test Mission", sample_body)
    
    assert result.mission_id == "AWAY-001"
    assert result.classification == "🔴 Priority One"
    assert len(result.objectives) > 0
    assert len(result.acceptance_criteria) == 2

# Add more tests for each component
```

## Implementation Requirements

1. **Authentication**: Use PyGithub library for GitHub API access
2. **Error Handling**: Graceful handling of API rate limits and network errors
3. **Branch Naming**: Consistent format: `away-mission-{number}-{slugified-title}`
4. **Progress Updates**: Use markdown formatting for issue comments
5. **Mission Parsing**: Robust regex patterns to handle variations in format

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
manager = GitHubManager()

# Get open missions
missions = manager.get_away_missions("open")

# Start working on mission #5
mission = manager.get_mission_details(5)
branch = manager.create_feature_branch(5, mission['title'])
manager.update_mission_progress(5, "in-progress", "Beginning implementation")

# After implementation, create PR
pr_number = manager.create_pull_request(
    mission_number=5,
    branch_name=branch,
    changes_summary="Implemented conversation engine as specified"
)
```

### From CLI:
```bash
# List all open missions
python -m src.plugins.github_integration.cli list-missions

# Show details for mission #5
python -m src.plugins.github_integration.cli show-mission 5

# Start working on mission #5
python -m src.plugins.github_integration.cli start-mission 5

# Complete mission #5
python -m src.plugins.github_integration.cli complete-mission 5
```

## Success Criteria

- [ ] Can authenticate with GitHub using PAT
- [ ] Can list and filter Away Missions
- [ ] Can parse mission format into structured data
- [ ] Can create feature branches programmatically
- [ ] Can create PRs with proper linking
- [ ] Can update issue status via comments
- [ ] CLI provides easy access to all functions
- [ ] Comprehensive error handling for API issues
- [ ] All methods have proper logging

## Integration with Claude Code

Once implemented, Claude Code can use this component to:
1. Read its assigned missions: `manager.get_away_missions()`
2. Get specification details: `manager.get_specification(spec_path)`
3. Create implementation branch: `manager.create_feature_branch()`
4. Update progress: `manager.update_mission_progress()`
5. Submit PR when complete: `manager.create_pull_request()`

This creates the full autonomous development loop!
