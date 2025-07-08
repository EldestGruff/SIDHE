#!/usr/bin/env python3
"""
SIDHE Session Protocol System

This module ensures every conversation follows proper SIDHE development processes,
maintaining consistency across AI instances and conversations.

Usage:
    from session_protocol import RikerSession
    
    # Start of conversation
    session = FairyCircle()
    session.initialize()
    
    # During conversation
    session.update_quest_status("QUEST-003", "active")
    
    # End of conversation  
    session.complete(summary="Implemented Config Manager plugin")
"""

import os
import json
import yaml
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class QuestStatus(Enum):
    """Quest status states"""
    SUMMONED = "summoned"
    ACTIVE = "active" 
    FULFILLED = "fulfilled"
    CURSED = "cursed"
    ABANDONED = "abandoned"


@dataclass
class ProjectState:
    """Current state of the SIDHE project"""
    active_quests: List[str]
    completed_quests: List[str]
    blocked_quests: List[str]
    voice_of_wisdom_status: str
    plugin_status: Dict[str, str]
    last_update: str
    current_focus: Optional[str] = None


@dataclass
class SessionSummary:
    """Summary of a development session"""
    session_id: str
    start_time: str
    end_time: str
    participants: List[str]
    focus_area: str
    accomplishments: List[str]
    decisions_made: List[str]
    next_actions: List[str]
    missions_updated: List[Dict[str, str]]


class FairyCircle:
    """
    Manages SIDHE development session protocols
    
    Ensures consistent processes across conversations:
    - Project state loading and tracking
    - Archmage's log maintenance  
    - Sanctum document updates
    - Away quest lifecycle management
    - Documentation consistency
    - Architectural integrity enforcement
    """
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize session with project context"""
        self.project_root = Path(project_root or os.getcwd())
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now(timezone.utc).isoformat()
        self.participants = []
        self.accomplishments = []
        self.decisions_made = []
        self.missions_updated = []
        
        # Key project files
        self.bridge_file = self.project_root / "BRIDGE.md"
        self.captains_log_dir = self.project_root / "chronicle"
        self.crew_quarters_dir = self.project_root / "grimoire"
        self.adr_file = self.project_root / "grimoire" / "architectural-decision-record.md"
        self.away_quests_dir = self.project_root / "quests"
        self.state_file = self.project_root / ".sidhe-state.json"
        
        # Architectural governance files
        self.constraints_file = self.project_root / "grimoire" / "architectural-constraints.md"
        self.authority_matrix_file = self.project_root / "grimoire" / "decision-authority-matrix.md"
        
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize session with current project state
        
        Returns:
            Dict containing current project context for the conversation
        """
        print(f"🚀 [SIDHE Session Protocol] Initializing session {self.session_id}")
        
        # Load current project state
        project_state = self._load_project_state()
        
        # Load recent archmage's log entries
        recent_log_entries = self._load_recent_log_entries(limit=3)
        
        # Load active quests
        active_quests = self._load_active_quests()
        
        # Load current ADR decisions
        recent_decisions = self._load_recent_adr_entries(limit=5)
        
        # Create session context
        context = {
            "session_id": self.session_id,
            "project_state": asdict(project_state),
            "recent_log_entries": recent_log_entries,
            "active_quests": active_quests,
            "recent_decisions": recent_decisions,
            "bridge_status": self._load_bridge_status(),
            "initialization_time": self.start_time
        }
        
        print(f"✅ Session initialized - {len(active_quests)} active missions loaded")
        return context
    
    def update_quest_status(self, quest_id: str, new_status: QuestStatus, 
                            notes: Optional[str] = None) -> bool:
        """
        Update quest status and move files accordingly
        
        Args:
            quest_id: Quest identifier (e.g., "QUEST-003")
            new_status: New quest status
            notes: Optional notes about the status change
            
        Returns:
            True if update successful
        """
        try:
            # Track the update
            self.missions_updated.append({
                "quest_id": quest_id,
                "new_status": new_status.value,
                "notes": notes or "",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Move quest files based on status
            self._move_quest_files(quest_id, new_status)
            
            # Update project state
            self._update_project_state_for_quest(quest_id, new_status)
            
            print(f"📋 Updated {quest_id} status to {new_status.value}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating quest {quest_id}: {e}")
            return False
    
    def validate_architectural_change(self, change_description: str, 
                                   affected_components: List[str]) -> Dict[str, Any]:
        """
        Validate if a proposed change violates architectural constraints
        
        Args:
            change_description: Description of the proposed change
            affected_components: List of components that would be affected
            
        Returns:
            Dict with validation results and recommendations
        """
        try:
            constraints = self._load_architectural_constraints()
            authority_matrix = self._load_decision_authority_matrix()
            
            validation_result = {
                "is_allowed": True,
                "violations": [],
                "warnings": [],
                "escalation_required": False,
                "recommendations": []
            }
            
            # Check against core architectural constraints
            for constraint in constraints.get("core_constraints", []):
                if self._check_constraint_violation(change_description, constraint, affected_components):
                    validation_result["violations"].append({
                        "constraint": constraint["name"],
                        "description": constraint["description"],
                        "rationale": constraint["rationale"]
                    })
                    validation_result["is_allowed"] = False
            
            # Check authority boundaries
            change_category = self._categorize_change(change_description, affected_components)
            required_authority = authority_matrix.get(change_category, "strategic")
            
            if required_authority == "strategic":
                validation_result["escalation_required"] = True
                validation_result["is_allowed"] = False
                validation_result["recommendations"].append(
                    "This change requires strategic architectural review. Please consult with Archmage/Strategic AI before proceeding."
                )
            
            # Generate specific warnings and recommendations
            self._add_specific_warnings(validation_result, change_description, affected_components)
            
            print(f"🛡️ Architectural validation: {'✅ ALLOWED' if validation_result['is_allowed'] else '❌ BLOCKED'}")
            if validation_result["violations"]:
                print(f"⚠️ Violations found: {len(validation_result['violations'])}")
            if validation_result["escalation_required"]:
                print(f"🚨 Escalation required: Strategic review needed")
                
            return validation_result
            
        except Exception as e:
            print(f"⚠️ Error validating architectural change: {e}")
            # Fail safe - require escalation if validation fails
            return {
                "is_allowed": False,
                "violations": [],
                "warnings": [f"Validation system error: {e}"],
                "escalation_required": True,
                "recommendations": ["Validation failed. Please consult with Strategic AI before proceeding."]
            }
    
    def record_architectural_violation_attempt(self, change_description: str, 
                                              validation_result: Dict[str, Any]):
        """Record when implementation AI attempts architectural violations"""
        violation_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "change_description": change_description,
            "violations": validation_result["violations"],
            "escalation_required": validation_result["escalation_required"]
        }
        
        # Add to session tracking
        if not hasattr(self, 'architectural_violations'):
            self.architectural_violations = []
        self.architectural_violations.append(violation_entry)
        
        print(f"📋 Recorded architectural violation attempt for review")
    
    def _load_architectural_constraints(self) -> Dict[str, Any]:
        """Load architectural constraints from constraints file"""
        try:
            if self.constraints_file.exists():
                with open(self.constraints_file, 'r') as f:
                    content = f.read()
                
                # Parse markdown format constraints (simplified)
                constraints = {
                    "core_constraints": [],
                    "technology_constraints": [],
                    "pattern_constraints": []
                }
                
                # Extract constraint sections
                if "## Core Architectural Constraints" in content:
                    core_section = content.split("## Core Architectural Constraints")[1].split("##")[0]
                    constraints["core_constraints"] = self._parse_constraint_section(core_section)
                
                return constraints
        except Exception as e:
            print(f"⚠️ Could not load architectural constraints: {e}")
        
        # Return default critical constraints
        return {
            "core_constraints": [
                {
                    "name": "Plugin Communication via Message Bus",
                    "description": "All plugin communication must use Redis message bus, not direct imports",
                    "rationale": "Maintains loose coupling, testability, and scalability",
                    "keywords": ["direct import", "from plugins.", "import plugins.", "message bus", "redis"]
                },
                {
                    "name": "Plugin Architecture Integrity", 
                    "description": "Plugins must remain self-contained with standardized interfaces",
                    "rationale": "Enables independent development and enchantment",
                    "keywords": ["plugin", "direct", "coupling", "interface"]
                },
                {
                    "name": "Conversation Engine as Central Orchestrator",
                    "description": "Conversation Engine coordinates all other components, not a plugin itself",
                    "rationale": "Clear architectural hierarchy and single point of control",
                    "keywords": ["conversation engine", "plugin", "orchestrator", "central"]
                }
            ]
        }
    
    def _load_decision_authority_matrix(self) -> Dict[str, str]:
        """Load decision authority matrix"""
        try:
            if self.authority_matrix_file.exists():
                with open(self.authority_matrix_file, 'r') as f:
                    content = f.read()
                # Parse authority matrix from markdown (simplified)
                return self._parse_authority_matrix(content)
        except Exception as e:
            print(f"⚠️ Could not load authority matrix: {e}")
        
        # Return default authority boundaries
        return {
            "architectural_pattern_changes": "strategic",
            "technology_stack_changes": "strategic", 
            "plugin_communication_changes": "strategic",
            "core_component_changes": "strategic",
            "bug_fixes": "implementation",
            "performance_optimizations": "implementation",
            "code_refactoring_within_patterns": "implementation",
            "test_additions": "implementation",
            "documentation_updates": "implementation"
        }
    
    def _check_constraint_violation(self, change_description: str, constraint: Dict, 
                                   affected_components: List[str]) -> bool:
        """Check if a change violates a specific architectural constraint"""
        change_lower = change_description.lower()
        
        # Check for constraint-specific keywords
        for keyword in constraint.get("keywords", []):
            if keyword.lower() in change_lower:
                # Special logic for message bus constraint
                if constraint["name"] == "Plugin Communication via Message Bus":
                    if any(term in change_lower for term in ["direct import", "from plugins.", "import plugins."]):
                        if any(comp in change_lower for comp in ["plugin", "component"]):
                            return True
                return True
        
        return False
    
    def _categorize_change(self, change_description: str, affected_components: List[str]) -> str:
        """Categorize the type of change for authority checking"""
        change_lower = change_description.lower()
        
        # Strategic-level changes
        strategic_indicators = [
            "architecture", "pattern", "message bus", "direct import", "plugin communication",
            "technology stack", "framework", "database", "communication protocol"
        ]
        
        if any(indicator in change_lower for indicator in strategic_indicators):
            return "architectural_pattern_changes"
        
        # Component-level changes
        if any(comp in change_lower for comp in ["conversation engine", "core", "orchestrator"]):
            return "core_component_changes"
        
        # Implementation-level changes
        implementation_indicators = [
            "bug fix", "performance", "optimization", "refactor", "test", "documentation"
        ]
        
        if any(indicator in change_lower for indicator in implementation_indicators):
            return "bug_fixes"
        
        # Default to requiring strategic review for unclear changes
        return "architectural_pattern_changes"
    
    def _add_specific_warnings(self, validation_result: Dict, change_description: str, 
                              affected_components: List[str]):
        """Add specific warnings based on change patterns"""
        change_lower = change_description.lower()
        
        # Message bus specific warnings
        if any(term in change_lower for term in ["direct", "import", "from plugins"]):
            validation_result["warnings"].append({
                "type": "message_bus_bypass",
                "message": "Consider using message bus instead of direct imports for plugin communication",
                "reference": "ADR-004: Plugin Communication Architecture"
            })
        
        # Plugin architecture warnings
        if "plugin" in change_lower and any(term in change_lower for term in ["direct", "couple"]):
            validation_result["warnings"].append({
                "type": "plugin_coupling",
                "message": "Avoid tight coupling between plugins. Use standardized interfaces.",
                "reference": "ADR-001: Project Structure and Plugin Architecture"
            })
    
    def _parse_constraint_section(self, section_text: str) -> List[Dict]:
        """Parse constraints from markdown section (simplified implementation)"""
        # This would be enhanced with proper markdown parsing
        constraints = []
        # Basic parsing implementation would go here
        return constraints
    
    def _parse_authority_matrix(self, content: str) -> Dict[str, str]:
        """Parse authority matrix from markdown (simplified implementation)"""
        # This would be enhanced with proper markdown parsing  
        matrix = {}
        # Basic parsing implementation would go here
        return matrix
    
    def add_accomplishment(self, description: str, quest_id: Optional[str] = None):
        """Record an accomplishment for this session"""
        accomplishment = {
            "description": description,
            "quest_id": quest_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.accomplishments.append(accomplishment)
        print(f"✅ Recorded accomplishment: {description}")
    
    def add_decision(self, decision: str, context: Optional[str] = None):
        """Record an architectural decision made during session"""
        decision_entry = {
            "decision": decision,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.decisions_made.append(decision_entry)
        print(f"🎯 Recorded decision: {decision}")
    
    def complete(self, summary: str, next_focus: Optional[str] = None) -> SessionSummary:
        """
        Complete session and update all tracking documents
        
        Args:
            summary: Summary of what was accomplished
            next_focus: Suggested focus for next session
            
        Returns:
            SessionSummary object with complete session data
        """
        print(f"🏁 [SIDHE Session Protocol] Completing session {self.session_id}")
        
        # Create session summary
        session_summary = SessionSummary(
            session_id=self.session_id,
            start_time=self.start_time,
            end_time=datetime.now(timezone.utc).isoformat(),
            participants=self.participants,
            focus_area=summary,
            accomplishments=[acc["description"] for acc in self.accomplishments],
            decisions_made=[dec["decision"] for dec in self.decisions_made],
            next_actions=[next_focus] if next_focus else [],
            missions_updated=self.missions_updated
        )
        
        # Update archmage's log
        self._update_captains_log(session_summary)
        
        # Update sanctum document
        self._update_bridge_document(session_summary)
        
        # Update project state
        self._save_project_state(next_focus)
        
        # Update ADR if decisions were made
        if self.decisions_made:
            self._update_adr_with_decisions()
        
        print(f"📝 Session complete - {len(self.accomplishments)} accomplishments recorded")
        return session_summary
    
    def _load_project_state(self) -> ProjectState:
        """Load current project state from state file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                return ProjectState(**data)
        except Exception as e:
            print(f"⚠️ Could not load project state: {e}")
        
        # Return default state
        return ProjectState(
            active_quests=[],
            completed_quests=[],
            blocked_quests=[],
            voice_of_wisdom_status="foundation_complete",
            plugin_status={
                "tome_keeper": "complete",
                "quest_tracker": "complete", 
                "config_manager": "complete"
            },
            last_update=datetime.now(timezone.utc).isoformat()
        )
    
    def _load_active_quests(self) -> List[Dict[str, Any]]:
        """Load currently active quests"""
        missions = []
        
        # Check summoned missions
        summoned_dir = self.away_quests_dir / "summoned"
        if summoned_dir.exists():
            for quest_file in summoned_dir.glob("*.md"):
                missions.append({
                    "id": quest_file.stem,
                    "status": "summoned",
                    "file": str(quest_file)
                })
        
        # Check active missions  
        active_dir = self.away_quests_dir / "active"
        if active_dir.exists():
            for quest_file in active_dir.glob("*.md"):
                missions.append({
                    "id": quest_file.stem,
                    "status": "active", 
                    "file": str(quest_file)
                })
        
        return missions
    
    def _load_recent_log_entries(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Load recent archmage's log entries"""
        entries = []
        
        if not self.captains_log_dir.exists():
            return entries
            
        # Get most recent log files
        log_files = sorted(self.captains_log_dir.glob("*.md"), reverse=True)
        
        for log_file in log_files[:limit]:
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                entries.append({
                    "file": log_file.name,
                    "date": log_file.stem,
                    "preview": content[:200] + "..." if len(content) > 200 else content
                })
            except Exception as e:
                print(f"⚠️ Could not read log file {log_file}: {e}")
        
        return entries
    
    def _load_recent_adr_entries(self, limit: int = 5) -> List[str]:
        """Load recent ADR decisions"""
        decisions = []
        
        try:
            if self.adr_file.exists():
                with open(self.adr_file, 'r') as f:
                    content = f.read()
                
                # Extract recent ADR entries (simplified)
                import re
                adr_pattern = r"## (ADR-\d+:[^#]+)"
                matches = re.findall(adr_pattern, content)
                decisions = matches[-limit:] if matches else []
        except Exception as e:
            print(f"⚠️ Could not load ADR entries: {e}")
        
        return decisions
    
    def _load_bridge_status(self) -> Dict[str, Any]:
        """Load current sanctum status"""
        try:
            if self.bridge_file.exists():
                with open(self.bridge_file, 'r') as f:
                    content = f.read()
                return {
                    "exists": True,
                    "last_modified": datetime.fromtimestamp(
                        self.bridge_file.stat().st_mtime
                    ).isoformat(),
                    "preview": content[:300] + "..." if len(content) > 300 else content
                }
        except Exception as e:
            print(f"⚠️ Could not load sanctum status: {e}")
        
        return {"exists": False}
    
    def _move_quest_files(self, quest_id: str, new_status: QuestStatus):
        """Move quest files to appropriate directory based on status"""
        # Define directory mapping
        status_dirs = {
            QuestStatus.SUMMONED: "summoned",
            QuestStatus.ACTIVE: "active", 
            QuestStatus.FULFILLED: "fulfilled",
            QuestStatus.CURSED: "cursed",
            QuestStatus.ABANDONED: "abandoned"
        }
        
        target_dir = self.away_quests_dir / status_dirs[new_status]
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Find current quest file
        for status_dir in status_dirs.values():
            current_dir = self.away_quests_dir / status_dir
            quest_file = current_dir / f"{quest_id}.md"
            
            if quest_file.exists():
                target_file = target_dir / f"{quest_id}.md"
                quest_file.rename(target_file)
                print(f"📁 Moved {quest_id} to {status_dirs[new_status]}/")
                break
    
    def _update_captains_log(self, session_summary: SessionSummary):
        """Update archmage's log with session summary"""
        self.captains_log_dir.mkdir(exist_ok=True)
        
        # Get current date for log file
        log_date = datetime.now().strftime("%Y-%m-%d")
        log_file = self.captains_log_dir / f"stardate-{log_date}.md"
        
        # Create log entry
        log_entry = f"""
## Session {session_summary.session_id}
**Start Time:** {session_summary.start_time}
**End Time:** {session_summary.end_time}
**Focus:** {session_summary.focus_area}

### Accomplishments
{chr(10).join(f"- {acc}" for acc in session_summary.accomplishments)}

### Decisions Made
{chr(10).join(f"- {dec}" for dec in session_summary.decisions_made)}

### Quests Updated
{chr(10).join(f"- {quest['quest_id']}: {quest['new_status']}" for quest in session_summary.missions_updated)}

### Next Actions
{chr(10).join(f"- {action}" for action in session_summary.next_actions)}

---
"""
        
        # Append to log file
        with open(log_file, 'a') as f:
            f.write(log_entry)
        
        print(f"📝 Updated archmage's log: {log_file.name}")
    
    def _update_bridge_document(self, session_summary: SessionSummary):
        """Update sanctum document with current status"""
        bridge_content = f"""# BRIDGE - Current Status

**Last Updated:** {session_summary.end_time}
**Session:** {session_summary.session_id}

## 🎯 Current Focus
{session_summary.focus_area}

## 📊 Recent Accomplishments
{chr(10).join(f"- {acc}" for acc in session_summary.accomplishments[-5:])}

## 🚀 Active Quests
{chr(10).join(f"- {quest['quest_id']}: {quest['new_status']}" for quest in session_summary.missions_updated if quest['new_status'] == 'active')}

## 🔄 Next Actions
{chr(10).join(f"- {action}" for action in session_summary.next_actions)}

## 📈 System Status
- **Conversation Engine:** Foundation Complete ✅
- **Memory Manager Plugin:** Complete ✅  
- **GitHub Integration Plugin:** Complete ✅
- **Config Manager Plugin:** Complete ✅

---
*Updated by SIDHE Session Protocol System*
"""
        
        with open(self.bridge_file, 'w') as f:
            f.write(bridge_content)
        
        print(f"🌉 Updated sanctum document")
    
    def _save_project_state(self, next_focus: Optional[str]):
        """Save current project state"""
        state = ProjectState(
            active_quests=[m["quest_id"] for m in self.missions_updated if m["new_status"] == "active"],
            completed_quests=[m["quest_id"] for m in self.missions_updated if m["new_status"] == "complete"],
            blocked_quests=[m["quest_id"] for m in self.missions_updated if m["new_status"] == "blocked"],
            voice_of_wisdom_status="foundation_complete",
            plugin_status={
                "tome_keeper": "complete",
                "quest_tracker": "complete",
                "config_manager": "complete"
            },
            last_update=datetime.now(timezone.utc).isoformat(),
            current_focus=next_focus
        )
        
        with open(self.state_file, 'w') as f:
            json.dump(asdict(state), f, indent=2)
        
        print(f"💾 Saved project state")
    
    def _update_adr_with_decisions(self):
        """Update ADR with any architectural decisions made during session"""
        # This would append new ADR entries based on decisions_made
        # Implementation depends on ADR format and numbering scheme
        print(f"📋 ADR update needed for {len(self.decisions_made)} decisions")


def create_session_template() -> str:
    """
    Generate a template prompt for starting new conversations
    
    Returns:
        Template string for copying into new AI conversations
    """
    return """
# SIDHE Development Session - Initialization Protocol

I'm starting a new development session for Project SIDHE. Please run the session initialization protocol:

```python
from session_protocol import FairyCircle

session = FairyCircle()
context = session.initialize()

# Display current project context
print("📋 Project Context Loaded:")
print(f"- Active Missions: {len(context['active_quests'])}")
print(f"- Recent Decisions: {len(context['recent_decisions'])}")
print(f"- Sanctum Status: {context['bridge_status']['exists']}")
```

Based on the loaded context, please:
1. Summarize the current project state
2. List active quests  
3. Identify the current focus area
4. Suggest next steps

Remember to follow SIDHE development protocols:
- Update quest status as work progresses
- Record accomplishments and decisions
- Complete session with proper documentation updates
"""


if __name__ == "__main__":
    # Example usage
    session = FairyCircle()
    
    # Initialize session
    context = session.initialize()
    print("Session initialized with context keys:", list(context.keys()))
    
    # Example session workflow
    session.add_accomplishment("Updated architectural decision record with new features")
    session.add_decision("Prioritize LCARS theming after core functionality")
    session.update_quest_status("QUEST-003", QuestStatus.FULFILLED, "Config Manager plugin completed")
    
    # Complete session
    summary = session.complete(
        summary="Session Protocol System implementation",
        next_focus="Begin Quality Control Plugin cluster planning"
    )
    
    print(f"Session {summary.session_id} completed successfully")
    print(f"Template for next conversation:\n{create_session_template()}")
