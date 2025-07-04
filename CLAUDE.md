# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Riker** is an AI-powered development assistant designed as a "Number One" - a trusted second-in-command that transforms ideas into implemented reality. The project follows Star Trek-inspired design principles and uses a mission-driven development approach where all work is organized as "away missions" (GitHub issues).

## Core Operating Principles

Follow the **PRIME_DIRECTIVE.md** when working in this codebase:
- **Captain-First Protocol**: User is the visionary/decision-maker, you are the executor
- **Conversational Development**: Development happens through natural dialogue
- **Away Mission Principle**: Complex problems broken into discrete GitHub issues labeled `away-mission`
- **Transparent Operations**: All actions must be logged and explainable
- Use Star Trek terminology naturally: "Captain" for user, "Mission complete" for task completion, "Acknowledged" for understanding

## Architecture

### Plugin-Based System
The codebase follows a modular plugin architecture in `/src/plugins/`:

```
src/plugins/
├── github_integration/     # ✅ Complete - GitHub API operations
├── memory_manager/         # ✅ Complete - Redis-based conversation memory  
├── conversation_engine/    # 📋 Planned - Core AI conversation interface
├── workflow_generator/     # 📋 Planned - AI-powered automation creation
└── task_dispatcher/        # 📋 Planned - Multi-model AI orchestration
```

### Current Implementation Status

**GitHub Integration Plugin** (Fully Implemented):
- `GitHubManager`: Handles away missions (issues), branch creation, PR management
- `MissionParser`: Parses structured mission format from issue bodies
- CLI commands for mission lifecycle management
- Branch naming: `away-mission-{number}-{slugified-title}`

**Memory Manager Plugin** (Fully Implemented):
- Redis-based conversation memory with 24-hour TTL
- Key pattern: `riker:memory:{conversation_id}`
- Handles Redis connection failures gracefully

## Development Commands

### Environment Setup
```bash
# GitHub Integration Plugin
python3 -m venv github_integration_env
source github_integration_env/bin/activate
pip install -r requirements_github_integration.txt

# Required environment variables
export GITHUB_TOKEN='your_personal_access_token'
export GITHUB_REPO='EldestGruff/riker'  # or your repo
```

### Testing
```bash
# Run specific plugin tests
python3 -m pytest src/plugins/github_integration/test_github_integration.py -v
python3 -m pytest src/plugins/memory_manager/test_memory_manager.py -v

# Run all tests
python3 -m pytest src/plugins/ -v
```

### GitHub Integration Commands
```bash
# List away missions
python -m src.plugins.github_integration.cli list-missions

# Show mission details
python -m src.plugins.github_integration.cli show-mission {issue_number}

# Start working on mission (creates branch, updates status)
python -m src.plugins.github_integration.cli start-mission {issue_number}

# Complete mission (creates PR)
python -m src.plugins.github_integration.cli complete-mission {issue_number}

# Test GitHub connection
python -m src.plugins.github_integration.cli test-connection
```

### Demonstration
```bash
# Run GitHub integration demo (uses mock data)
python3 demo_github_integration.py
```

## Mission Format

Away missions follow this structured format in GitHub issue bodies:

```markdown
# Away Mission Brief: {Title}

**Mission ID:** AWAY-{number}
**Classification:** 🔴 Priority One | 🟠 Priority Two | 🟡 Priority Three
**Type:** Feature Implementation | Bug Fix | Refactoring | Documentation

## 🎯 Mission Objectives
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

## 👨‍✈️ Captain's Notes
{Additional context or requirements}

## Referenced Documents
- [Spec Name](crew-quarters/spec-file.md)
```

## Key Conventions

### Directory Structure
- `crew-quarters/`: Component specifications (read before implementing)
- `away-missions/`: Mission tracking and templates
- `engineering/`: Technical architecture and decisions
- `captains-log/`: Project logs and progress tracking
- `src/plugins/`: Core plugin implementations

### Code Patterns
- Each plugin has: `plugin_interface.py` (main class), CLI, tests
- Use type hints throughout Python code
- Follow the established error handling patterns (Red/Yellow Alert system)
- All major actions should be logged with appropriate level
- Configuration via environment variables

### Dependency Management
- Keep dependencies minimal and focused per plugin
- Use virtual environments for testing/development
- Pin specific versions in requirements files

## Working with Away Missions

1. **Mission Creation**: Create GitHub issues with `away-mission` label using the mission format
2. **Mission Execution**: Use the GitHub integration CLI to manage mission lifecycle
3. **Specification-First**: Check `crew-quarters/` for detailed specs before implementing
4. **Feature Branches**: Always work in mission-specific branches created by the CLI
5. **Progress Updates**: Use CLI to update mission status and maintain transparency

## Integration Points

- **GitHub**: All missions tracked as labeled issues, PRs auto-link to issues
- **Redis**: Memory manager requires Redis instance (falls back gracefully if unavailable)
- **Environment Variables**: Configuration primarily through env vars (GITHUB_TOKEN, GITHUB_REPO)

## Important Notes

- The project is still in early development - many planned components are not yet implemented
- Follow the Star Trek theming consistently but don't force it
- Always consult specifications in `crew-quarters/` before implementing new features
- The system is designed to be self-improving - meta-development is encouraged
- When implementing new plugins, follow the established patterns from existing plugins