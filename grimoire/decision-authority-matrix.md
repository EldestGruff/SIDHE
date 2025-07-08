# SIDHE Decision Authority Matrix

**Purpose:** Define clear boundaries between Strategic and Implementation decision-making authority  
**Enforcement:** Automated by Session Protocol System  
**Created:** 2025-07-05  
**Status:** ACTIVE

## 🎯 Authority Levels

### 🏛️ Strategic Authority (Archmage + Strategic AI)
**Scope:** Architecture, patterns, technology choices, cross-cutting decisions  
**Participants:** Andy (Archmage), Claude Web (Strategic AI)  
**Process:** ADR creation, architectural analysis, long-term planning

### 🔧 Implementation Authority (Implementation AI)  
**Scope:** Code implementation, bug fixes, optimizations within established patterns  
**Participants:** Claude Code, other implementation tools  
**Process:** Execute within constraints, escalate when boundaries are unclear

## 📋 Decision Classification Matrix

| Decision Category | Authority Level | Examples | Escalation Required |
|-------------------|----------------|----------|-------------------|
| **Architectural Patterns** | Strategic | Message bus vs direct imports, plugin architecture changes, orchestration patterns | ✅ Always |
| **Technology Stack** | Strategic | FastAPI → Django, React → Vue, Redis → RabbitMQ | ✅ Always |
| **Core Component Structure** | Strategic | Conversation Engine location, plugin boundaries, service interfaces | ✅ Always |
| **Communication Protocols** | Strategic | WebSocket → polling, message formats, API design affecting multiple components | ✅ Always |
| **Database/Persistence Strategy** | Strategic | Adding SQL databases, changing Redis usage patterns, data architecture | ✅ Always |
| **External Dependencies** | Strategic | New frameworks, libraries, services | ✅ Always |
| **Security Architecture** | Strategic | Authentication patterns, encryption choices, security boundaries | ✅ Always |
| **Plugin Interface Changes** | Strategic | Modifying plugin contracts, changing plugin communication patterns | ✅ Always |
| **Performance Architecture** | Strategic | Caching strategies, scaling patterns, load balancing approaches | ✅ Always |
| **Testing Strategy** | Strategic | Testing frameworks, test architecture, integration patterns | ✅ Always |
| **Bug Fixes** | Implementation | Fixing errors within established patterns | ❌ No |
| **Performance Optimizations** | Implementation | Code-level optimizations within architectural constraints | ❌ No |
| **Code Refactoring** | Implementation | Improving code quality while maintaining patterns | ❌ No |
| **Test Implementation** | Implementation | Adding tests following established patterns | ❌ No |
| **Documentation Updates** | Implementation | Code comments, API docs, user guides | ❌ No |
| **Configuration Adjustments** | Implementation | Environment variables, enchantment settings | ❌ No |
| **Error Handling** | Implementation | Adding try/catch, improving error messages | ❌ No |
| **Logging Improvements** | Implementation | Adding debug info, improving log formats | ❌ No |
| **Development Tooling** | Implementation | Build scripts, development utilities | ❌ No |
| **Minor UI/UX Improvements** | Implementation | Styling, component layout within design system | ❌ No |

## 🚨 High-Risk Indicators

Implementation AIs should **immediately escalate** when encountering these patterns:

### 🔴 Immediate Escalation Triggers
- **Direct Plugin Communication**: `from plugins.` imports, bypassing message bus
- **Architecture Changes**: "Let's refactor the architecture to..."
- **Technology Replacement**: "We should use X instead of Y"
- **Pattern Violations**: Breaking established communication/design patterns
- **Core Component Movement**: Moving Conversation Engine, changing plugin boundaries
- **New External Dependencies**: Adding frameworks, databases, services

### 🟡 Warning Indicators (Validate First)
- **Performance Shortcuts**: "This would be faster if we..."
- **Simplification Attempts**: "We can simplify this by..."
- **Pattern Bypassing**: "Instead of using the established pattern..."
- **Cross-Component Changes**: Modifications affecting multiple components
- **Interface Modifications**: Changing APIs, message formats, or contracts

## 🔧 Implementation AI Guidelines

### ✅ Proceed Freely (Implementation Authority)
```python
# Bug fixes
if error_condition:
    handle_error_properly()

# Performance within patterns
def optimized_function():
    # Faster implementation of same logic
    pass

# Code quality improvements
class WellNamedClass:  # Better than GenericClass
    def descriptive_method_name(self):  # Better than do_stuff()
        pass

# Test additions
def test_existing_functionality():
    assert existing_function() == expected_result
```

### 🚨 Escalate Immediately (Strategic Authority)
```python
# WRONG - Direct plugin imports
from plugins.tome_keeper import MemoryManager  # ESCALATE

# WRONG - Architecture changes
def bypass_message_bus():  # ESCALATE
    pass

# WRONG - Technology replacement
import flask  # If replacing FastAPI - ESCALATE
```

### 🟡 Validate Before Proceeding
```python
# Check if this requires strategic review
session.validate_architectural_change(
    change_description="Add caching layer to plugin communication",
    affected_components=["message_bus", "plugin_communication"]
)
```

## 📝 Escalation Process

### Step 1: Recognize Need for Escalation
```python
# Implementation AI encounters potential violation
change_description = "Replace Redis pub/sub with direct function calls for performance"
affected_components = ["message_bus", "plugin_communication", "performance"]

# Run validation
result = session.validate_architectural_change(change_description, affected_components)

if not result["is_allowed"] or result["escalation_required"]:
    # Proceed to escalation
```

### Step 2: Create Escalation Brief
```markdown
🚨 ARCHITECTURAL ESCALATION REQUIRED

**Session ID:** {session_id}
**Timestamp:** {timestamp}

**Proposed Change:** Replace Redis pub/sub with direct function calls for performance

**Affected Components:** 
- message_bus
- plugin_communication  
- performance

**Constraint Violations:**
- Plugin Communication via Message Bus (ADR-004)
- Plugin Architecture Integrity (ADR-001)

**Tactical Rationale:** 
Performance tests show 50ms latency in plugin communication. Direct calls would reduce to 5ms.

**Strategic Review Questions:**
1. Is this performance impact acceptable vs architectural benefits?
2. Are there alternative optimizations within message bus pattern?
3. Should we modify the constraint or find alternative solutions?

**Implementation Blocked Until:** Strategic approval received
```

### Step 3: Document and Wait
```python
# Record the violation attempt
session.record_architectural_violation_attempt(change_description, result)

# Do NOT implement the change
# Wait for strategic guidance
# Continue with other tasks that don't violate constraints
```

## 🔄 Authority Escalation Examples

### Example 1: Performance Optimization
**Scenario:** Plugin communication is slow  
**Implementation Impulse:** Use direct imports instead of message bus  
**Correct Process:** Escalate for strategic review of performance vs architecture tradeoffs

### Example 2: Bug Fix Difficulty  
**Scenario:** Bug is hard to fix within current pattern  
**Implementation Impulse:** Refactor the pattern to make fix easier  
**Correct Process:** Fix bug within pattern, escalate pattern concerns separately

### Example 3: Feature Complexity
**Scenario:** New feature doesn't fit well in plugin architecture  
**Implementation Impulse:** Modify plugin boundaries or create exceptions  
**Correct Process:** Escalate architectural questions, implement within constraints

## 📊 Authority Review Process

### Monthly Authority Review
- Analyze escalation patterns
- Identify areas where constraints may need refinement
- Update authority matrix based on project evolution
- Train implementation AIs on updated boundaries

### Constraint Evolution
- Only Strategic Authority can modify constraints
- All changes require ADR process
- Implementation feedback considered but doesn't override strategic decisions
- Emergency override only with Archmage approval

---

**Enforcement:** Session Protocol System automatically validates changes  
**Training:** New implementation AIs receive authority matrix briefing  
**Appeals:** Strategic Authority can grant exceptions with documentation  
**Updates:** Matrix evolves with project maturity and lessons learned
