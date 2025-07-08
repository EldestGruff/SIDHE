# MAGICAL_TOME.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SIDHE** is an AI-powered development assistant designed as a "Apprentice" - a trusted second-in-command that transforms ideas into implemented reality. The project follows Fairy Tale-inspired design principles and uses a quest-driven development approach where all work is organized as "quests" (GitHub issues).

## Core Operating Principles

Follow the **THE_OLD_LAWS.md** when working in this codebase:
- **Archmage-First Protocol**: User is the visionary/decision-maker, you are the executor
- **Conversational Development**: Development happens through natural dialogue
- **Quest Principle**: Complex problems broken into discrete GitHub issues labeled `quest`
- **Transparent Operations**: All actions must be logged and explainable
- Use Fairy Tale terminology naturally: "Archmage" for user, "Quest complete" for task completion, "Acknowledged" for understanding

## Architecture

### Plugin-Based System
The codebase follows a modular plugin architecture in `/src/plugins/`:

```
src/plugins/
├── quest_tracker/     # ✅ Complete - GitHub API operations
├── tome_keeper/         # ✅ Complete - Redis-based conversation memory  
├── voice_of_wisdom/    # 📋 Planned - Core AI conversation interface
├── spell_weaver/     # 📋 Planned - AI-powered automation creation
└── task_dispatcher/        # 📋 Planned - Multi-model AI orchestration
```

### Current Implementation Status

**GitHub Integration Plugin** (Fully Implemented):
- `QuestTracker`: Handles quests (issues), branch creation, PR management
- `QuestParser`: Parses structured quest format from issue bodies
- CLI commands for quest lifecycle management
- Branch naming: `quest-{number}-{slugified-title}`

**Memory Manager Plugin** (Fully Implemented):
- Redis-based conversation memory with 24-hour TTL
- Key pattern: `sidhe:memory:{conversation_id}`
- Handles Redis connection failures gracefully

## Development Commands

### Environment Setup
```bash
# GitHub Integration Plugin
python3 -m venv quest_tracker_env
source quest_tracker_env/bin/activate
pip install -r requirements_quest_tracker.txt

# Required environment variables
export GITHUB_TOKEN='your_personal_access_token'
export GITHUB_REPO='EldestGruff/sidhe'  # or your repo
```

### Testing
```bash
# Run specific plugin tests
python3 -m pytest src/plugins/quest_tracker/test_quest_tracker.py -v
python3 -m pytest src/plugins/tome_keeper/test_tome_keeper.py -v

# Run all tests
python3 -m pytest src/plugins/ -v
```

### GitHub Integration Commands
```bash
# List quests
python -m src.plugins.quest_tracker.cli list-missions

# Show quest details
python -m src.plugins.quest_tracker.cli show-quest {issue_number}

# Start working on quest (creates branch, updates status)
python -m src.plugins.quest_tracker.cli start-quest {issue_number}

# Complete quest (creates PR)
python -m src.plugins.quest_tracker.cli complete-quest {issue_number}

# Test GitHub connection
python -m src.plugins.quest_tracker.cli test-connection
```

### Demonstration
```bash
# Run GitHub integration demo (uses mock data)
python3 demo_quest_tracker.py
```

## Quest Format

Away missions follow this structured format in GitHub issue bodies:

```markdown
# Quest Brief: {Title}

**Quest ID:** QUEST-{number}
**Classification:** 🔴 Priority One | 🟠 Priority Two | 🟡 Priority Three
**Type:** Feature Implementation | Bug Fix | Refactoring | Documentation

## 🎯 Quest Objectives
### Primary Objective
{Main goal description}

### Secondary Objectives
- [ ] {Secondary task 1}
- [ ] {Secondary task 2}

## 🔧 Technical Specifications
- **Framework:** {Technology stack}
- **Dependencies:** {Required libraries}

## 📋 Acceptance Criteria
- [ ] {Criterion 1}
- [ ] {Criterion 2}

## 👨‍✈️ Archmage's Notes
{Additional context or requirements}

## Referenced Documents
- [Spec Name](grimoire/spec-file.md)
```

## Key Conventions

### Directory Structure
- `grimoire/`: Component specifications (read before implementing)
- `quests/`: Quest tracking and templates
- `spellcraft/`: Technical architecture and decisions
- `chronicle/`: Project logs and progress tracking
- `src/plugins/`: Core plugin implementations

### Code Patterns
- Each plugin has: `plugin_interface.py` (main class), CLI, tests
- Use type hints throughout Python code
- Follow the established error handling patterns (Red/Giant's Warning system)
- All major actions should be logged with appropriate level
- Configuration via environment variables

### Dependency Management
- Keep dependencies minimal and focused per plugin
- Use virtual environments for testing/development
- Pin specific versions in requirements files

## Working with Quests

1. **Quest Creation**: Create GitHub issues with `quest` label using the quest format
2. **Quest Execution**: Use the GitHub integration CLI to manage quest lifecycle
3. **Specification-First**: Check `grimoire/` for detailed specs before implementing
4. **Feature Branches**: Always work in quest-specific branches created by the CLI
5. **Progress Updates**: Use CLI to update quest status and maintain transparency

## Integration Points

- **GitHub**: All missions tracked as labeled issues, PRs auto-link to issues
- **Redis**: Memory manager requires Redis instance (falls back gracefully if unavailable)
- **Environment Variables**: Configuration primarily through env vars (GITHUB_TOKEN, GITHUB_REPO)

## Important Notes

- The project is still in early development - many planned components are not yet implemented
- Follow the Fairy Tale theming consistently but don't force it
- Always consult specifications in `grimoire/` before implementing new features
- The system is designed to be self-improving - meta-development is encouraged
- When implementing new plugins, follow the established patterns from existing plugins