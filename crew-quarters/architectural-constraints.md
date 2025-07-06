# Riker Architectural Constraints

**Purpose:** Define inviolable architectural decisions that implementation AIs must respect  
**Authority:** Strategic (Captain + Strategic AI) - Implementation AIs CANNOT modify these constraints  
**Created:** 2025-07-05  
**Status:** ACTIVE - Enforced by Session Protocol System

## 🛡️ Core Architectural Constraints

### Constraint 1: Plugin Communication via Message Bus
**Decision Reference:** ADR-004  
**Constraint:** All plugin communication MUST use Redis message bus, NOT direct imports  
**Rationale:** Maintains loose coupling, testability, and scalability  
**Violation Indicators:**
- `from plugins.` imports between plugins
- `import plugins.` statements in core code
- Direct plugin class instantiation across boundaries
- Bypassing message bus for plugin communication

**Implementation AI Guidance:**
- ❌ **NEVER**: `from plugins.memory_manager import MemoryManager`
- ✅ **ALWAYS**: Use message bus for plugin communication
- 🚨 **ESCALATE**: If direct communication seems necessary

### Constraint 2: Plugin Architecture Integrity  
**Decision Reference:** ADR-001  
**Constraint:** Plugins MUST remain self-contained with standardized interfaces  
**Rationale:** Enables independent development, testing, and deployment  
**Violation Indicators:**
- Tight coupling between plugins
- Shared state outside message bus
- Plugin-specific code in core components
- Breaking plugin interface contracts

**Implementation AI Guidance:**
- ❌ **NEVER**: Create dependencies between plugins
- ✅ **ALWAYS**: Use standardized plugin interfaces
- 🚨 **ESCALATE**: If plugin boundaries need modification

### Constraint 3: Conversation Engine as Central Orchestrator
**Decision Reference:** ADR-002  
**Constraint:** Conversation Engine coordinates all components, is NOT a plugin itself  
**Rationale:** Clear architectural hierarchy and single point of control  
**Violation Indicators:**
- Moving Conversation Engine to `src/plugins/`
- Making core orchestration logic pluggable
- Creating multiple orchestrators
- Bypassing central coordination

**Implementation AI Guidance:**
- ❌ **NEVER**: Make Conversation Engine a plugin
- ✅ **ALWAYS**: Route coordination through Conversation Engine
- 🚨 **ESCALATE**: If orchestration patterns need changes

### Constraint 4: Technology Stack Consistency
**Decision Reference:** ADR-003  
**Constraint:** Core technology choices (FastAPI, React, Redis, WebSockets) are fixed  
**Rationale:** Architectural consistency and team expertise  
**Violation Indicators:**
- Replacing FastAPI with Flask/Django
- Replacing React with Vue/Angular  
- Replacing Redis with other message buses
- Adding conflicting technologies

**Implementation AI Guidance:**
- ❌ **NEVER**: Replace core technology choices
- ✅ **ALWAYS**: Use established stack
- 🚨 **ESCALATE**: If technology limitations are encountered

### Constraint 5: WebSocket Communication Pattern
**Decision Reference:** ADR-006  
**Constraint:** Real-time communication MUST use WebSockets, not polling/REST  
**Rationale:** Performance and user experience requirements  
**Violation Indicators:**
- Replacing WebSockets with polling
- Adding REST endpoints for real-time features
- Breaking WebSocket message protocols

**Implementation AI Guidance:**
- ❌ **NEVER**: Replace WebSockets with polling for real-time features
- ✅ **ALWAYS**: Use established WebSocket patterns
- 🚨 **ESCALATE**: If WebSocket limitations are encountered

## 🔒 Technology Constraints

### Database/Persistence
- **Redis**: Primary for message bus and session state
- **File System**: Secondary for documentation and configuration
- **NO**: Introduction of SQL databases without strategic approval

### Communication Protocols  
- **WebSockets**: Real-time browser communication
- **Redis Pub/Sub**: Inter-component messaging
- **HTTP**: API endpoints for non-real-time operations
- **NO**: Custom protocols or alternative message buses

### Development Tools
- **Docker**: Containerization and deployment
- **GitHub**: Version control and project management
- **Python 3.11+**: Backend development
- **Node.js 18+**: Frontend build tools

## ⚠️ Warning Patterns

Implementation AIs should escalate immediately when encountering:

### High-Risk Patterns
- "Let's simplify this by using direct imports instead..."
- "We can bypass the message bus for performance..."
- "This would be easier with a different framework..."
- "Let's make this a plugin to be more modular..."

### Architecture-Changing Language
- "Refactor the architecture to..."
- "Change the communication pattern to..."
- "Replace [core technology] with..."
- "Modify the plugin structure to..."

## 🚨 Escalation Protocol

When implementation AI encounters potential constraint violations:

1. **STOP** - Do not proceed with the change
2. **VALIDATE** - Run `session.validate_architectural_change()`
3. **ESCALATE** - If validation fails, create escalation brief
4. **DOCUMENT** - Record the attempted change for strategic review
5. **WAIT** - Do not implement until strategic approval received

### Escalation Brief Template
```
🚨 ARCHITECTURAL ESCALATION REQUIRED

**Proposed Change:** [Description]
**Affected Components:** [List]
**Constraint Violations:** [From validation]
**Tactical Rationale:** [Why this seems necessary]
**Strategic Review Needed:** [Specific questions for Strategic AI]
```

## 📋 Implementation AI Boundaries

### ✅ ALLOWED (Implementation Authority)
- Bug fixes within established patterns
- Performance optimizations within constraints
- Code refactoring that maintains architectural patterns
- Test additions and improvements
- Documentation updates
- Configuration adjustments
- Error handling improvements

### 🚨 REQUIRES ESCALATION (Strategic Authority)
- Architecture pattern modifications
- Technology stack changes
- Plugin communication pattern changes
- Core component structure changes
- New external dependencies
- Database/persistence strategy changes
- API design changes that affect multiple components

## 🔄 Constraint Evolution

**These constraints can only be modified by:**
- Captain (Andy) with explicit approval
- Strategic AI with Captain consultation
- Formal ADR process with documented rationale

**Implementation AIs CANNOT:**
- Modify these constraints
- Create exceptions without escalation
- Override constraints for convenience
- Make "temporary" constraint violations

---

**Enforcement:** Automated by Session Protocol System  
**Review Cycle:** Monthly or when architectural decisions change  
**Next Review:** Upon completion of Quality Control Plugin implementation
