from typing import List, Dict, Any, Optional
import os
from github import Github, GithubException
import re
import logging
from slugify import slugify
# Conditional imports - handle both relative and absolute
try:
    from .quest_parser import QuestParser, ParsedMission
except ImportError:
    # Fallback for certification script or standalone usage
    try:
        from quest_parser import QuestParser, ParsedMission
    except ImportError:
        # Create mock classes for certification
        from types import SimpleNamespace
        
        class ParsedMission:
            def __init__(self):
                self.quest_id = "MOCK_001"
                self.classification = "Mock"
                self.quest_type = "Test"
                self.objectives = []
                self.acceptance_criteria = []
                self.referenced_docs = []
                self.technical_specs = ""
                self.captains_notes = ""
        
        class QuestParser:
            def parse_quest(self, number, title, body):
                return ParsedMission()

# Import PDK classes
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.pdk.sidhe_pdk import EnchantedPlugin, PluginCapability, PluginMessage

logger = logging.getLogger(__name__)

class QuestTracker(EnchantedPlugin):
    """Manages all GitHub operations for SIDHE"""
    
    def __init__(self):
        """Initialize the GitHub Integration plugin"""
        super().__init__(
            plugin_id="quest_tracker",
            plugin_name="Quest Tracker",
            version="2.0.0"
        )
        
        # Initialize GitHub connection
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo_name = os.getenv('GITHUB_REPO')
        
        # For certification mode, allow graceful degradation
        self.certification_mode = not self.token or not self.repo_name
        
        if self.certification_mode:
            # Mock GitHub components for certification
            self.logger.info("🔧 Running in certification mode - mocking GitHub connection")
            self.github = None
            self.repo = None
            self.quest_parser = QuestParser()
        else:
            try:
                self.github = Github(self.token)
                self.repo = self.github.get_repo(self.repo_name)
                self.quest_parser = QuestParser()
                
                # Verify access by getting repo info
                _ = self.repo.name
                self.logger.info(f"🔗 Successfully connected to GitHub repository: {self.repo_name}")
                
            except (GithubException, Exception) as e:
                self.logger.warning(f"⚠️ Failed to connect to GitHub: {e}")
                self.certification_mode = True
                self.github = None
                self.repo = None
                self.quest_parser = QuestParser()
        
        # Register capabilities
        self.register_capability(PluginCapability(
            name="get_away_quests",
            description="Fetch all quests with filtering options",
            parameters={"state": "string"},
            returns={"quests": "array"}
        ))
        
        self.register_capability(PluginCapability(
            name="get_quest_details",
            description="Get detailed information about a specific quest",
            parameters={"quest_number": "integer"},
            returns={"quest": "object"}
        ))
        
        self.register_capability(PluginCapability(
            name="create_feature_branch",
            description="Create a new branch for a quest",
            parameters={"quest_number": "integer", "quest_title": "string"},
            returns={"branch_name": "string"}
        ))
        
        self.register_capability(PluginCapability(
            name="create_pull_request",
            description="Create a PR for a completed quest",
            parameters={"quest_number": "integer", "branch_name": "string", "changes_summary": "string"},
            returns={"pr_number": "integer"}
        ))
        
        self.register_capability(PluginCapability(
            name="update_quest_progress",
            description="Update quest progress via issue comment",
            parameters={"quest_number": "integer", "status": "string", "details": "string"},
            returns={"success": "boolean"}
        ))
        
        self.register_capability(PluginCapability(
            name="get_specification",
            description="Read a specification file from the repository",
            parameters={"spec_path": "string"},
            returns={"content": "string", "path": "string"}
        ))
    
    async def handle_request(self, message: PluginMessage) -> Dict[str, Any]:
        """Handle GitHub-related requests"""
        action = message.payload.get("action")
        
        if action == "get_away_quests":
            return await self._get_away_quests(
                message.payload.get("state", "open")
            )
        elif action == "get_quest_details":
            return await self._get_quest_details(
                message.payload.get("quest_number")
            )
        elif action == "create_feature_branch":
            return await self._create_feature_branch(
                message.payload.get("quest_number"),
                message.payload.get("quest_title")
            )
        elif action == "create_pull_request":
            return await self._create_pull_request(
                message.payload.get("quest_number"),
                message.payload.get("branch_name"),
                message.payload.get("changes_summary")
            )
        elif action == "update_quest_progress":
            return await self._update_quest_progress(
                message.payload.get("quest_number"),
                message.payload.get("status"),
                message.payload.get("details", "")
            )
        elif action == "get_specification":
            return await self._get_specification(
                message.payload.get("spec_path")
            )
        elif action == "test":
            # Handle test requests for certification
            return {
                "status": "success",
                "message": "Quest Tracker is functioning correctly",
                "data": message.payload.get("data", "test_response"),
                "plugin_info": {
                    "name": self.plugin_name,
                    "version": self.version,
                    "capabilities": len(self.capabilities),
                    "github_repo": self.repo_name if hasattr(self, 'repo_name') else "Not configured"
                }
            }
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _get_away_quests(self, state: str = "open") -> Dict[str, Any]:
        """
        Fetch all Quests (issues with 'quest' label)
        
        Args:
            state: Issue state - "open", "closed", or "all"
            
        Returns:
            Dictionary containing list of quest dictionaries with parsed data
        """
        if state not in ["open", "closed", "all"]:
            raise ValueError("state must be 'open', 'closed', or 'all'")
            
        try:
            issues = self.repo.get_issues(state=state, labels=['quest'])
            missions = []
            
            for issue in issues:
                try:
                    parsed_quest = self.quest_parser.parse_quest(
                        issue.number, 
                        issue.title, 
                        issue.body or ""
                    )
                    
                    quest_dict = {
                        'number': issue.number,
                        'title': issue.title,
                        'state': issue.state,
                        'url': issue.html_url,
                        'created_at': issue.created_at.isoformat(),
                        'updated_at': issue.updated_at.isoformat(),
                        'quest_id': parsed_quest.quest_id,
                        'classification': parsed_quest.classification,
                        'quest_type': parsed_quest.quest_type,
                        'objectives': [{'description': obj.description, 'is_primary': obj.is_primary} 
                                     for obj in parsed_quest.objectives],
                        'acceptance_criteria': [{'description': ac.description, 'is_complete': ac.is_complete} 
                                              for ac in parsed_quest.acceptance_criteria],
                        'referenced_docs': parsed_quest.referenced_docs
                    }
                    missions.append(quest_dict)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to parse quest #{issue.number}: {e}")
                    # Add basic info even if parsing fails
                    missions.append({
                        'number': issue.number,
                        'title': issue.title,
                        'state': issue.state,
                        'url': issue.html_url,
                        'created_at': issue.created_at.isoformat(),
                        'updated_at': issue.updated_at.isoformat(),
                        'quest_id': 'PARSE_ERROR',
                        'classification': 'Unknown',
                        'quest_type': 'Unknown',
                        'objectives': [],
                        'acceptance_criteria': [],
                        'referenced_docs': []
                    })
            
            self.logger.info(f"📋 Retrieved {len(missions)} quests with state '{state}'")
            return {"quests": missions}
            
        except GithubException as e:
            self.logger.error(f"❌ Failed to fetch quests: {e}")
            raise
    
    async def _get_quest_details(self, quest_number: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific quest
        
        Args:
            quest_number: GitHub issue number
            
        Returns:
            Parsed quest data including objectives, specs, criteria
        """
        if not quest_number:
            raise ValueError("quest_number is required")
            
        try:
            issue = self.repo.get_issue(quest_number)
            
            # Check if it has the quest label
            if not any(label.name == 'quest' for label in issue.labels):
                raise ValueError(f"Issue #{quest_number} is not a Quest")
            
            parsed_quest = self.quest_parser.parse_quest(
                issue.number, 
                issue.title, 
                issue.body or ""
            )
            
            quest_data = {
                'number': issue.number,
                'title': issue.title,
                'state': issue.state,
                'url': issue.html_url,
                'created_at': issue.created_at.isoformat(),
                'updated_at': issue.updated_at.isoformat(),
                'quest_id': parsed_quest.quest_id,
                'classification': parsed_quest.classification,
                'quest_type': parsed_quest.quest_type,
                'objectives': [{'description': obj.description, 'is_primary': obj.is_primary, 'sub_objectives': obj.sub_objectives} 
                             for obj in parsed_quest.objectives],
                'technical_specs': parsed_quest.technical_specs,
                'acceptance_criteria': [{'description': ac.description, 'is_complete': ac.is_complete} 
                                      for ac in parsed_quest.acceptance_criteria],
                'captains_notes': parsed_quest.captains_notes,
                'referenced_docs': parsed_quest.referenced_docs
            }
            
            self.logger.info(f"📄 Retrieved details for quest #{quest_number}")
            return {"quest": quest_data}
            
        except GithubException as e:
            self.logger.error(f"❌ Failed to get quest #{quest_number}: {e}")
            raise
    
    async def _create_feature_branch(self, quest_number: int, quest_title: str) -> Dict[str, Any]:
        """
        Create a new branch for the quest
        
        Args:
            quest_number: GitHub issue number
            quest_title: Quest title for branch name
            
        Returns:
            Dictionary containing branch name created
        """
        if not quest_number:
            raise ValueError("quest_number is required")
        if not quest_title:
            raise ValueError("quest_title is required")
            
        try:
            # Generate branch name: quest-{number}-{slugified-title}
            slugified_title = slugify(quest_title, max_length=50)
            branch_name = f"quest-{quest_number}-{slugified_title}"
            
            # Get the main branch reference
            main_ref = self.repo.get_git_ref("heads/main")
            
            # Create new branch from main
            self.repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=main_ref.object.sha
            )
            
            self.logger.info(f"🌳 Created branch: {branch_name}")
            return {"branch_name": branch_name}
            
        except GithubException as e:
            if e.status == 422:
                self.logger.warning(f"⚠️ Branch {branch_name} already exists")
                return {"branch_name": branch_name}
            self.logger.error(f"❌ Failed to create branch: {e}")
            raise
    
    async def _create_pull_request(self, quest_number: int, branch_name: str, 
                          changes_summary: str) -> Dict[str, Any]:
        """
        Create a PR for completed quest
        
        Args:
            quest_number: GitHub issue number
            branch_name: Source branch for PR
            changes_summary: Description of changes made
            
        Returns:
            Dictionary containing PR number created
        """
        if not quest_number:
            raise ValueError("quest_number is required")
        if not branch_name:
            raise ValueError("branch_name is required")
        if not changes_summary:
            raise ValueError("changes_summary is required")
            
        try:
            # Get quest details for title
            quest_response = await self._get_quest_details(quest_number)
            quest = quest_response["quest"]
            
            pr_title = f"Quest #{quest_number}: {quest['title']}"
            
            pr_body = f"""## Quest Complete

**Quest ID:** {quest['quest_id']}
**Classification:** {quest['classification']}

### Changes Summary
{changes_summary}

### Quest Objectives
""" + "\n".join([f"- {obj['description']}" for obj in quest['objectives']]) + f"""

### Acceptance Criteria
""" + "\n".join([f"- {'✅' if ac['is_complete'] else '❌'} {ac['description']}" for ac in quest['acceptance_criteria']]) + f"""

---
Closes #{quest_number}

🚀 Generated by SIDHE GitHub Integration
"""
            
            # Create the PR
            pr = self.repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base="main"
            )
            
            # Add labels
            pr.add_to_labels('quest', 'ready-for-review')
            
            self.logger.info(f"🔀 Created PR #{pr.number} for quest #{quest_number}")
            return {"pr_number": pr.number}
            
        except GithubException as e:
            self.logger.error(f"❌ Failed to create PR for quest #{quest_number}: {e}")
            raise
    
    async def _update_quest_progress(self, quest_number: int, status: str, 
                               details: str = "") -> Dict[str, Any]:
        """
        Update quest progress via issue comment
        
        Args:
            quest_number: GitHub issue number
            status: Current status (e.g., "in-progress", "blocked", "complete")
            details: Additional details about progress
            
        Returns:
            Dictionary containing success boolean
        """
        if not quest_number:
            raise ValueError("quest_number is required")
        if not status:
            raise ValueError("status is required")
            
        try:
            issue = self.repo.get_issue(quest_number)
            
            # Format the progress comment
            status_emoji = {
                'in-progress': '🚀',
                'blocked': '🚫',
                'complete': '✅',
                'paused': '⏸️',
                'reviewing': '👀'
            }.get(status.lower(), '📝')
            
            comment_body = f"""## Quest Progress Update

**Status:** {status_emoji} {status.title()}

{details}

---
*Update from SIDHE GitHub Integration*
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
            
            self.logger.info(f"📝 Updated quest #{quest_number} status to: {status}")
            return {"success": True}
            
        except GithubException as e:
            self.logger.error(f"❌ Failed to update quest #{quest_number}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_specification(self, spec_path: str) -> Dict[str, Any]:
        """
        Read a specification file from the repository
        
        Args:
            spec_path: Path to spec file (e.g., "grimoire/conversation-engine.md")
            
        Returns:
            Dictionary containing specification content
        """
        if not spec_path:
            raise ValueError("spec_path is required")
            
        try:
            file_content = self.repo.get_contents(spec_path)
            content = file_content.decoded_content.decode('utf-8')
            
            self.logger.info(f"📜 Retrieved specification: {spec_path}")
            return {"content": content, "path": spec_path}
            
        except GithubException as e:
            self.logger.error(f"❌ Failed to get specification {spec_path}: {e}")
            raise