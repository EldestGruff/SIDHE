#!/bin/bash
# Session Protocol Deployment Script
# Deploys and tests the Riker Session Protocol System

echo "🚀 [Session Protocol] Deployment Starting..."
echo "=================================================="

# Check if we're in a Riker project directory
if [[ ! -f "PRIME_DIRECTIVE.md" ]]; then
    echo "⚠️  Warning: PRIME_DIRECTIVE.md not found. Are you in the Riker project root?"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled."
        exit 1
    fi
fi

# Create scripts directory if it doesn't exist
echo "📁 Creating scripts directory..."
mkdir -p scripts

# Check if session_protocol.py already exists
if [[ -f "scripts/session_protocol.py" ]]; then
    echo "⚠️  session_protocol.py already exists"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled."
        exit 1
    fi
fi

# Create the session protocol file
echo "📝 Creating session_protocol.py..."
cat > scripts/session_protocol.py << 'EOF'
#!/usr/bin/env python3
"""
Riker Session Protocol System

This module ensures every conversation follows proper Riker development processes,
maintaining consistency across AI instances and conversations.

Usage:
    from session_protocol import RikerSession
    
    # Start of conversation
    session = RikerSession()
    session.initialize()
    
    # During conversation
    session.update_mission_status("AWAY-003", "active")
    
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


class MissionStatus(Enum):
    """Away Mission status states"""
    PROPOSED = "proposed"
    ACTIVE = "active" 
    COMPLETE = "complete"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class ProjectState:
    """Current state of the Riker project"""
    active_missions: List[str]
    completed_missions: List[str]
    blocked_missions: List[str]
    conversation_engine_status: str
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


class RikerSession:
    """
    Manages Riker development session protocols
    
    Ensures consistent processes across conversations:
    - Project state loading and tracking
    - Captain's log maintenance  
    - Bridge document updates
    - Away mission lifecycle management
    - Documentation consistency
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
        self.captains_log_dir = self.project_root / "captains-log"
        self.crew_quarters_dir = self.project_root / "crew-quarters"
        self.adr_file = self.project_root / "crew-quarters" / "architectural-decision-record.md"
        self.away_missions_dir = self.project_root / "away-missions"
        self.state_file = self.project_root / ".riker-state.json"
        
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize session with current project state
        
        Returns:
            Dict containing current project context for the conversation
        """
        print(f"🚀 [Riker Session Protocol] Initializing session {self.session_id}")
        
        # Create required directories
        self._ensure_directory_structure()
        
        # Load current project state
        project_state = self._load_project_state()
        
        # Load recent captain's log entries
        recent_log_entries = self._load_recent_log_entries(limit=3)
        
        # Load active away missions
        active_missions = self._load_active_missions()
        
        # Load current ADR decisions
        recent_decisions = self._load_recent_adr_entries(limit=5)
        
        # Create session context
        context = {
            "session_id": self.session_id,
            "project_state": asdict(project_state),
            "recent_log_entries": recent_log_entries,
            "active_missions": active_missions,
            "recent_decisions": recent_decisions,
            "bridge_status": self._load_bridge_status(),
            "initialization_time": self.start_time
        }
        
        print(f"✅ Session initialized - {len(active_missions)} active missions loaded")
        return context
    
    def _ensure_directory_structure(self):
        """Ensure all required directories exist"""
        directories = [
            self.captains_log_dir,
            self.crew_quarters_dir,
            self.away_missions_dir / "proposed",
            self.away_missions_dir / "active",
            self.away_missions_dir / "completed",
            self.away_missions_dir / "blocked",
            self.away_missions_dir / "cancelled"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def update_mission_status(self, mission_id: str, new_status: MissionStatus, 
                            notes: Optional[str] = None) -> bool:
        """
        Update away mission status and move files accordingly
        
        Args:
            mission_id: Mission identifier (e.g., "AWAY-003")
            new_status: New mission status
            notes: Optional notes about the status change
            
        Returns:
            True if update successful
        """
        try:
            # Track the update
            self.missions_updated.append({
                "mission_id": mission_id,
                "new_status": new_status.value,
                "notes": notes or "",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Move mission files based on status
            self._move_mission_files(mission_id, new_status)
            
            # Update project state
            self._update_project_state_for_mission(mission_id, new_status)
            
            print(f"📋 Updated {mission_id} status to {new_status.value}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating mission {mission_id}: {e}")
            return False
    
    def add_accomplishment(self, description: str, mission_id: Optional[str] = None):
        """Record an accomplishment for this session"""
        accomplishment = {
            "description": description,
            "mission_id": mission_id,
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
        print(f"🏁 [Riker Session Protocol] Completing session {self.session_id}")
        
        # Create session summary
        session_summary = SessionSummary(
            session_id=self.session_id,
            start_time=self.start_time,
            end_time=datetime.now(timezone.utc).isoformat(),
            participants=self.participants or ["Captain Andy", "Chief Engineer Ivy"],
            focus_area=summary,
            accomplishments=[acc["description"] for acc in self.accomplishments],
            decisions_made=[dec["decision"] for dec in self.decisions_made],
            next_actions=[next_focus] if next_focus else [],
            missions_updated=self.missions_updated
        )
        
        # Update captain's log
        self._update_captains_log(session_summary)
        
        # Update bridge document
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
            active_missions=[],
            completed_missions=[],
            blocked_missions=[],
            conversation_engine_status="foundation_complete",
            plugin_status={
                "memory_manager": "complete",
                "github_integration": "complete", 
                "config_manager": "complete"
            },
            last_update=datetime.now(timezone.utc).isoformat()
        )
    
    def _load_active_missions(self) -> List[Dict[str, Any]]:
        """Load currently active away missions"""
        missions = []
        
        # Check all mission directories
        status_dirs = ["proposed", "active", "completed", "blocked", "cancelled"]
        for status in status_dirs:
            status_dir = self.away_missions_dir / status
            if status_dir.exists():
                for mission_file in status_dir.glob("*.md"):
                    missions.append({
                        "id": mission_file.stem,
                        "status": status,
                        "file": str(mission_file)
                    })
        
        return missions
    
    def _load_recent_log_entries(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Load recent captain's log entries"""
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
        """Load current bridge status"""
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
            print(f"⚠️ Could not load bridge status: {e}")
        
        return {"exists": False}
    
    def _move_mission_files(self, mission_id: str, new_status: MissionStatus):
        """Move mission files to appropriate directory based on status"""
        # Define directory mapping
        status_dirs = {
            MissionStatus.PROPOSED: "proposed",
            MissionStatus.ACTIVE: "active", 
            MissionStatus.COMPLETE: "completed",
            MissionStatus.BLOCKED: "blocked",
            MissionStatus.CANCELLED: "cancelled"
        }
        
        target_dir = self.away_missions_dir / status_dirs[new_status]
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Find current mission file
        for status_dir in status_dirs.values():
            current_dir = self.away_missions_dir / status_dir
            mission_file = current_dir / f"{mission_id}.md"
            
            if mission_file.exists():
                target_file = target_dir / f"{mission_id}.md"
                mission_file.rename(target_file)
                print(f"📁 Moved {mission_id} to {status_dirs[new_status]}/")
                break
    
    def _update_project_state_for_mission(self, mission_id: str, new_status: MissionStatus):
        """Update project state tracking for mission status change"""
        # This would update internal tracking - simplified for now
        pass
    
    def _update_captains_log(self, session_summary: SessionSummary):
        """Update captain's log with session summary"""
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

### Away Missions Updated
{chr(10).join(f"- {mission['mission_id']}: {mission['new_status']}" for mission in session_summary.missions_updated)}

### Next Actions
{chr(10).join(f"- {action}" for action in session_summary.next_actions)}

---
"""
        
        # Append to log file
        with open(log_file, 'a') as f:
            f.write(log_entry)
        
        print(f"📝 Updated captain's log: {log_file.name}")
    
    def _update_bridge_document(self, session_summary: SessionSummary):
        """Update bridge document with current status"""
        bridge_content = f"""# BRIDGE - Current Status

**Last Updated:** {session_summary.end_time}
**Session:** {session_summary.session_id}

## 🎯 Current Focus
{session_summary.focus_area}

## 📊 Recent Accomplishments
{chr(10).join(f"- {acc}" for acc in session_summary.accomplishments[-5:])}

## 🚀 Active Away Missions
{chr(10).join(f"- {mission['mission_id']}: {mission['new_status']}" for mission in session_summary.missions_updated if mission['new_status'] == 'active')}

## 🔄 Next Actions
{chr(10).join(f"- {action}" for action in session_summary.next_actions)}

## 📈 System Status
- **Conversation Engine:** Foundation Complete ✅
- **Memory Manager Plugin:** Complete ✅  
- **GitHub Integration Plugin:** Complete ✅
- **Config Manager Plugin:** Complete ✅

---
*Updated by Riker Session Protocol System*
"""
        
        with open(self.bridge_file, 'w') as f:
            f.write(bridge_content)
        
        print(f"🌉 Updated bridge document")
    
    def _save_project_state(self, next_focus: Optional[str]):
        """Save current project state"""
        state = ProjectState(
            active_missions=[m["mission_id"] for m in self.missions_updated if m["new_status"] == "active"],
            completed_missions=[m["mission_id"] for m in self.missions_updated if m["new_status"] == "complete"],
            blocked_missions=[m["mission_id"] for m in self.missions_updated if m["new_status"] == "blocked"],
            conversation_engine_status="foundation_complete",
            plugin_status={
                "memory_manager": "complete",
                "github_integration": "complete",
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
# Riker Development Session - Initialization Protocol

I'm starting a new development session for Project Riker. Please run the session initialization protocol:

```python
import sys
sys.path.append('scripts')
from session_protocol import RikerSession

session = RikerSession()
context = session.initialize()

# Display current project context
print("📋 Project Context Loaded:")
print(f"- Active Missions: {len(context['active_missions'])}")
print(f"- Recent Decisions: {len(context['recent_decisions'])}")
print(f"- Bridge Status: {context['bridge_status']['exists']}")
```

Based on the loaded context, please:
1. Summarize the current project state
2. List active away missions  
3. Identify the current focus area
4. Suggest next steps

Remember to follow Riker development protocols:
- Update mission status as work progresses
- Record accomplishments and decisions
- Complete session with proper documentation updates
"""


if __name__ == "__main__":
    # Example usage
    session = RikerSession()
    
    # Initialize session
    context = session.initialize()
    print("Session initialized with context keys:", list(context.keys()))
    
    # Example session workflow
    session.add_accomplishment("Updated architectural decision record with new features")
    session.add_decision("Prioritize LCARS theming after core functionality")
    session.update_mission_status("AWAY-008", MissionStatus.ACTIVE, "Session Protocol System implementation")
    
    # Complete session
    summary = session.complete(
        summary="Session Protocol System implementation and testing",
        next_focus="Begin Quality Control Plugin cluster planning"
    )
    
    print(f"Session {summary.session_id} completed successfully")
    print(f"\nTemplate for next conversation:\n{create_session_template()}")
EOF

echo "✅ session_protocol.py created successfully"

# Make it executable
chmod +x scripts/session_protocol.py

echo "🔧 Made script executable"

# Test the deployment by running a basic initialization
echo "🧪 Testing deployment..."
echo "Running basic initialization test..."

cd "$(dirname "$0")" 2>/dev/null || true

python3 -c "
import sys
sys.path.append('scripts')
try:
    from session_protocol import RikerSession
    print('✅ Import successful')
    
    # Test initialization
    session = RikerSession()
    print('✅ Session object created')
    
    context = session.initialize()
    print('✅ Initialization successful')
    print(f'Session ID: {session.session_id}')
    print(f'Context keys: {list(context.keys())}')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "🎉 [Session Protocol] Deployment Complete!"
echo "=================================================="
echo ""
echo "📝 Next Steps:"
echo "1. Test full session lifecycle with: python3 scripts/session_protocol.py"
echo "2. Use the session template for new conversations"
echo "3. Import in conversations with: from session_protocol import RikerSession"
echo ""
echo "📋 Usage:"
echo "  session = RikerSession()"
echo "  context = session.initialize()"
echo "  session.add_accomplishment('Deployed Session Protocol')"
echo "  session.complete('Session Protocol deployment test')"
EOF

# Make the deployment script executable
chmod +x session_protocol_deploy.sh

echo "📦 Session Protocol deployment script created!"
echo ""
echo "🚀 To deploy, run:"
echo "  ./session_protocol_deploy.sh"
echo ""
echo "This will:"
echo "  1. Create the scripts directory"
echo "  2. Deploy session_protocol.py"
echo "  3. Test the deployment"
echo "  4. Provide usage instructions"