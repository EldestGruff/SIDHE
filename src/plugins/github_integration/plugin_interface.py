from typing import List, Dict, Any, Optional
import os
from github import Github, GithubException
import re
import logging
from slugify import slugify
from .mission_parser import MissionParser, ParsedMission

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
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.repo_name = repo_name or os.getenv('GITHUB_REPO')
        
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable or pass token parameter.")
        
        if not self.repo_name:
            raise ValueError("Repository name is required. Set GITHUB_REPO environment variable or pass repo_name parameter.")
        
        try:
            self.github = Github(self.token)
            self.repo = self.github.get_repo(self.repo_name)
            self.mission_parser = MissionParser()
            
            # Verify access by getting repo info
            _ = self.repo.name
            logger.info(f"Successfully connected to GitHub repository: {self.repo_name}")
            
        except GithubException as e:
            logger.error(f"Failed to connect to GitHub: {e}")
            raise
    
    def get_away_missions(self, state: str = "open") -> List[Dict[str, Any]]:
        """
        Fetch all Away Missions (issues with 'away-mission' label)
        
        Args:
            state: Issue state - "open", "closed", or "all"
            
        Returns:
            List of mission dictionaries with parsed data
        """
        try:
            issues = self.repo.get_issues(state=state, labels=['away-mission'])
            missions = []
            
            for issue in issues:
                try:
                    parsed_mission = self.mission_parser.parse_mission(
                        issue.number, 
                        issue.title, 
                        issue.body or ""
                    )
                    
                    mission_dict = {
                        'number': issue.number,
                        'title': issue.title,
                        'state': issue.state,
                        'url': issue.html_url,
                        'created_at': issue.created_at.isoformat(),
                        'updated_at': issue.updated_at.isoformat(),
                        'mission_id': parsed_mission.mission_id,
                        'classification': parsed_mission.classification,
                        'mission_type': parsed_mission.mission_type,
                        'objectives': [{'description': obj.description, 'is_primary': obj.is_primary} 
                                     for obj in parsed_mission.objectives],
                        'acceptance_criteria': [{'description': ac.description, 'is_complete': ac.is_complete} 
                                              for ac in parsed_mission.acceptance_criteria],
                        'referenced_docs': parsed_mission.referenced_docs
                    }
                    missions.append(mission_dict)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse mission #{issue.number}: {e}")
                    # Add basic info even if parsing fails
                    missions.append({
                        'number': issue.number,
                        'title': issue.title,
                        'state': issue.state,
                        'url': issue.html_url,
                        'created_at': issue.created_at.isoformat(),
                        'updated_at': issue.updated_at.isoformat(),
                        'mission_id': 'PARSE_ERROR',
                        'classification': 'Unknown',
                        'mission_type': 'Unknown',
                        'objectives': [],
                        'acceptance_criteria': [],
                        'referenced_docs': []
                    })
            
            return missions
            
        except GithubException as e:
            logger.error(f"Failed to fetch away missions: {e}")
            raise
    
    def get_mission_details(self, mission_number: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific mission
        
        Args:
            mission_number: GitHub issue number
            
        Returns:
            Parsed mission data including objectives, specs, criteria
        """
        try:
            issue = self.repo.get_issue(mission_number)
            
            # Check if it has the away-mission label
            if not any(label.name == 'away-mission' for label in issue.labels):
                raise ValueError(f"Issue #{mission_number} is not an Away Mission")
            
            parsed_mission = self.mission_parser.parse_mission(
                issue.number, 
                issue.title, 
                issue.body or ""
            )
            
            return {
                'number': issue.number,
                'title': issue.title,
                'state': issue.state,
                'url': issue.html_url,
                'created_at': issue.created_at.isoformat(),
                'updated_at': issue.updated_at.isoformat(),
                'mission_id': parsed_mission.mission_id,
                'classification': parsed_mission.classification,
                'mission_type': parsed_mission.mission_type,
                'objectives': [{'description': obj.description, 'is_primary': obj.is_primary, 'sub_objectives': obj.sub_objectives} 
                             for obj in parsed_mission.objectives],
                'technical_specs': parsed_mission.technical_specs,
                'acceptance_criteria': [{'description': ac.description, 'is_complete': ac.is_complete} 
                                      for ac in parsed_mission.acceptance_criteria],
                'captains_notes': parsed_mission.captains_notes,
                'referenced_docs': parsed_mission.referenced_docs
            }
            
        except GithubException as e:
            logger.error(f"Failed to get mission #{mission_number}: {e}")
            raise
    
    def create_feature_branch(self, mission_number: int, mission_title: str) -> str:
        """
        Create a new branch for the mission
        
        Args:
            mission_number: GitHub issue number
            mission_title: Mission title for branch name
            
        Returns:
            Branch name created
        """
        try:
            # Generate branch name: away-mission-{number}-{slugified-title}
            slugified_title = slugify(mission_title, max_length=50)
            branch_name = f"away-mission-{mission_number}-{slugified_title}"
            
            # Get the main branch reference
            main_ref = self.repo.get_git_ref("heads/main")
            
            # Create new branch from main
            self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=main_ref.object.sha
            )
            
            logger.info(f"Created branch: {branch_name}")
            return branch_name
            
        except GithubException as e:
            if e.status == 422:
                logger.warning(f"Branch {branch_name} already exists")
                return branch_name
            logger.error(f"Failed to create branch: {e}")
            raise
    
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
        try:
            # Get mission details for title
            mission = self.get_mission_details(mission_number)
            
            pr_title = f"Away Mission #{mission_number}: {mission['title']}"
            
            pr_body = f"""## Mission Complete

**Mission ID:** {mission['mission_id']}
**Classification:** {mission['classification']}

### Changes Summary
{changes_summary}

### Mission Objectives
""" + "\n".join([f"- {obj['description']}" for obj in mission['objectives']]) + f"""

### Acceptance Criteria
""" + "\n".join([f"- {'✅' if ac['is_complete'] else '❌'} {ac['description']}" for ac in mission['acceptance_criteria']]) + f"""

---
Closes #{mission_number}

🚀 Generated by Riker GitHub Integration
"""
            
            # Create the PR
            pr = self.repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base="main"
            )
            
            # Add labels
            pr.add_to_labels('away-mission', 'ready-for-review')
            
            logger.info(f"Created PR #{pr.number} for mission #{mission_number}")
            return pr.number
            
        except GithubException as e:
            logger.error(f"Failed to create PR for mission #{mission_number}: {e}")
            raise
    
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
        try:
            issue = self.repo.get_issue(mission_number)
            
            # Format the progress comment
            status_emoji = {
                'in-progress': '🚀',
                'blocked': '🚫',
                'complete': '✅',
                'paused': '⏸️',
                'reviewing': '👀'
            }.get(status.lower(), '📝')
            
            comment_body = f"""## Mission Progress Update

**Status:** {status_emoji} {status.title()}

{details}

---
*Update from Riker GitHub Integration*
"""
            
            # Post the comment
            issue.create_comment(comment_body)
            
            # Update labels based on status
            current_labels = [label.name for label in issue.labels]
            
            # Remove old status labels
            status_labels = ['in-progress', 'blocked', 'complete', 'paused', 'reviewing']
            for label in status_labels:
                if label in current_labels:
                    issue.remove_from_labels(label)
            
            # Add new status label
            if status.lower() in status_labels:
                issue.add_to_labels(status.lower())
            
            logger.info(f"Updated mission #{mission_number} status to: {status}")
            return True
            
        except GithubException as e:
            logger.error(f"Failed to update mission #{mission_number}: {e}")
            return False
    
    def get_specification(self, spec_path: str) -> str:
        """
        Read a specification file from the repository
        
        Args:
            spec_path: Path to spec file (e.g., "crew-quarters/conversation-engine.md")
            
        Returns:
            Specification content
        """
        try:
            file_content = self.repo.get_contents(spec_path)
            return file_content.decoded_content.decode('utf-8')
            
        except GithubException as e:
            logger.error(f"Failed to get specification {spec_path}: {e}")
            raise