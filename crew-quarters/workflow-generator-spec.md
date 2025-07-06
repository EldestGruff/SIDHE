# Workflow Generator Plugin Specification

**Component**: Workflow Generator  
**Version**: 1.0  
**Status**: Ready for Implementation  
**ADR Reference**: ADR-011  

## Overview

The Workflow Generator transforms natural language descriptions into executable automation workflows. It serves as Riker's "hands" - converting understanding into action through a structured, safe, and extensible workflow system.

## Architecture

### Directory Structure
```
src/plugins/workflow_generator/
├── __init__.py
├── plugin_interface.py      # Main WorkflowGenerator class
├── parser/
│   ├── __init__.py
│   ├── natural_language.py  # NL to workflow conversion
│   └── dsl_parser.py        # YAML DSL parser
├── validator/
│   ├── __init__.py
│   ├── schema.py            # JSON schema definitions
│   └── safety_checker.py    # Security validation
├── executor/
│   ├── __init__.py
│   ├── engine.py            # Workflow execution engine
│   ├── step_runner.py       # Individual step execution
│   └── rollback.py          # Error recovery
├── templates/
│   ├── __init__.py
│   ├── library.py           # Template management
│   └── patterns/            # Pre-built workflow patterns
├── storage/
│   ├── __init__.py
│   └── redis_store.py       # Workflow persistence
├── cli.py                   # Command-line interface
└── test_workflow_generator.py
```

## Core Components

### 1. Plugin Interface (`plugin_interface.py`)

```python
from typing import Dict, List, Optional, Any
import yaml
import json
from dataclasses import dataclass
from enum import Enum
import redis

class WorkflowStatus(Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class WorkflowStep:
    id: str
    type: str  # command, plugin_action, template, conditional
    description: Optional[str] = None
    command: Optional[str] = None
    plugin: Optional[str] = None
    action: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    working_dir: Optional[str] = None
    on_failure: str = "abort"  # abort, continue, rollback
    timeout: int = 300  # seconds
    requires: Optional[List[str]] = None  # step dependencies

@dataclass
class Workflow:
    name: str
    version: str
    description: str
    inputs: List[Dict[str, Any]]
    steps: List[WorkflowStep]
    outputs: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class WorkflowGenerator:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.nl_parser = NaturalLanguageParser()
        self.validator = WorkflowValidator()
        self.executor = WorkflowExecutor(self.redis)
        self.template_library = TemplateLibrary()
        
    def generate_from_text(self, description: str, context: Optional[Dict] = None) -> Workflow:
        """
        Generate a workflow from natural language description
        
        Args:
            description: Natural language workflow description
            context: Optional context from conversation
            
        Returns:
            Generated Workflow object
        """
        # Parse natural language to workflow structure
        workflow_dict = self.nl_parser.parse(description, context)
        
        # Check for matching templates
        template_matches = self.template_library.find_matches(description)
        if template_matches:
            # Merge with best matching template
            workflow_dict = self.template_library.apply_template(
                template_matches[0], 
                workflow_dict
            )
        
        # Create workflow object
        workflow = self._dict_to_workflow(workflow_dict)
        
        # Validate workflow
        validation_result = self.validator.validate(workflow)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid workflow: {validation_result.errors}")
        
        return workflow
    
    def execute_workflow(self, workflow: Workflow, inputs: Dict[str, Any], 
                        dry_run: bool = False) -> Dict[str, Any]:
        """Execute a workflow with given inputs"""
        return self.executor.execute(workflow, inputs, dry_run)
    
    def save_workflow(self, workflow: Workflow) -> str:
        """Save workflow to storage and return ID"""
        workflow_id = f"workflow:{workflow.name}:{workflow.version}"
        self.redis.set(workflow_id, yaml.dump(workflow.__dict__))
        return workflow_id
```

### 2. Natural Language Parser (`parser/natural_language.py`)

```python
import anthropic
from typing import Dict, Any, List, Optional

class NaturalLanguageParser:
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        
    def parse(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Convert natural language to workflow structure using LLM
        """
        system_prompt = """You are a workflow generator that converts natural language 
        descriptions into structured workflow definitions. Output valid YAML that follows 
        this schema:

        workflow:
          name: string
          version: string
          description: string
          inputs:
            - name: string
              type: string
              required: boolean
              default: any (optional)
          steps:
            - id: string
              type: command|plugin_action|template|conditional
              description: string (optional)
              command: string (if type is command)
              plugin: string (if type is plugin_action)
              action: string (if type is plugin_action)
              params: object (optional)
              on_failure: abort|continue|rollback
              timeout: integer (seconds)
              requires: [step_ids] (optional)
        
        Be specific and include error handling. Infer reasonable defaults."""
        
        messages = [
            {
                "role": "user",
                "content": f"Convert this to a workflow: {description}\n\nContext: {json.dumps(context or {})}"
            }
        ]
        
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            system=system_prompt,
            messages=messages,
            max_tokens=4000
        )
        
        # Parse YAML response
        yaml_content = response.content[0].text
        workflow_dict = yaml.safe_load(yaml_content)
        
        return workflow_dict['workflow']
```

### 3. Workflow Validator (`validator/schema.py`)

```python
from jsonschema import validate, ValidationError
from typing import List, Tuple

class WorkflowValidator:
    def __init__(self):
        self.schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "version": {"type": "string", "pattern": r"^\d+\.\d+$"},
                "description": {"type": "string"},
                "inputs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "required": {"type": "boolean"},
                            "default": {}
                        },
                        "required": ["name", "type"]
                    }
                },
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "type": {"enum": ["command", "plugin_action", "template", "conditional"]},
                            "command": {"type": "string"},
                            "plugin": {"type": "string"},
                            "action": {"type": "string"},
                            "params": {"type": "object"},
                            "on_failure": {"enum": ["abort", "continue", "rollback"]},
                            "timeout": {"type": "integer", "minimum": 1}
                        },
                        "required": ["id", "type"]
                    }
                }
            },
            "required": ["name", "version", "description", "steps"]
        }
        
        self.safety_checker = SafetyChecker()
    
    def validate(self, workflow: Workflow) -> ValidationResult:
        """Validate workflow structure and safety"""
        errors = []
        warnings = []
        
        # Schema validation
        try:
            validate(workflow.__dict__, self.schema)
        except ValidationError as e:
            errors.append(f"Schema validation failed: {e.message}")
        
        # Safety validation
        safety_result = self.safety_checker.check(workflow)
        if not safety_result.is_safe:
            errors.extend(safety_result.violations)
        warnings.extend(safety_result.warnings)
        
        # Dependency validation
        dep_errors = self._validate_dependencies(workflow)
        errors.extend(dep_errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

### 4. Workflow Executor (`executor/engine.py`)

```python
import asyncio
from typing import Dict, Any, List
import subprocess
from datetime import datetime

class WorkflowExecutor:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.step_runner = StepRunner()
        self.rollback_manager = RollbackManager()
        
    async def execute(self, workflow: Workflow, inputs: Dict[str, Any], 
                      dry_run: bool = False) -> Dict[str, Any]:
        """Execute workflow asynchronously"""
        execution_id = f"execution:{workflow.name}:{datetime.utcnow().isoformat()}"
        
        # Initialize execution context
        context = {
            "workflow": workflow,
            "inputs": inputs,
            "outputs": {},
            "step_results": {},
            "status": WorkflowStatus.RUNNING,
            "dry_run": dry_run
        }
        
        # Save initial state
        self._save_execution_state(execution_id, context)
        
        try:
            # Execute steps in dependency order
            execution_order = self._calculate_execution_order(workflow.steps)
            
            for step_id in execution_order:
                step = next(s for s in workflow.steps if s.id == step_id)
                
                # Check dependencies
                if not self._dependencies_met(step, context):
                    raise RuntimeError(f"Dependencies not met for step {step_id}")
                
                # Execute step
                if dry_run:
                    result = await self._dry_run_step(step, context)
                else:
                    result = await self.step_runner.run(step, context)
                
                context["step_results"][step_id] = result
                
                # Handle failure
                if not result["success"]:
                    if step.on_failure == "abort":
                        raise RuntimeError(f"Step {step_id} failed: {result['error']}")
                    elif step.on_failure == "rollback":
                        await self.rollback_manager.rollback(context)
                        context["status"] = WorkflowStatus.ROLLED_BACK
                        break
                    # continue: just proceed to next step
                
                # Update state
                self._save_execution_state(execution_id, context)
            
            # Workflow completed successfully
            if context["status"] == WorkflowStatus.RUNNING:
                context["status"] = WorkflowStatus.COMPLETED
                
        except Exception as e:
            context["status"] = WorkflowStatus.FAILED
            context["error"] = str(e)
            
            # Attempt rollback if configured
            if workflow.metadata.get("auto_rollback", False):
                await self.rollback_manager.rollback(context)
        
        finally:
            self._save_execution_state(execution_id, context)
        
        return {
            "execution_id": execution_id,
            "status": context["status"],
            "outputs": context["outputs"],
            "step_results": context["step_results"],
            "error": context.get("error")
        }
```

## Workflow DSL Specification

### Complete YAML Schema

```yaml
workflow:
  name: string                # Unique workflow name
  version: string             # Semantic version (e.g., "1.0")
  description: string         # Human-readable description
  
  # Input parameters
  inputs:
    - name: string            # Parameter name
      type: string            # string, number, boolean, enum, array, object
      required: boolean       # Whether input is required
      default: any            # Default value if not provided
      description: string     # Parameter description
      validation:             # Optional validation rules
        pattern: string       # Regex for strings
        min: number          # Min value for numbers
        max: number          # Max value for numbers
        values: [...]        # Allowed values for enum
  
  # Workflow steps
  steps:
    - id: string              # Unique step identifier
      type: string            # command, plugin_action, template, conditional
      description: string     # Step description
      
      # For command type
      command: string         # Shell command to execute
      working_dir: string     # Working directory
      environment:            # Environment variables
        KEY: value
      
      # For plugin_action type
      plugin: string          # Plugin name
      action: string          # Action to invoke
      params: object          # Action parameters
      
      # For template type
      template: string        # Template name
      variables: object       # Template variables
      
      # For conditional type
      condition: string       # Condition expression
      then_steps: [...]       # Steps if true
      else_steps: [...]       # Steps if false
      
      # Common options
      timeout: number         # Timeout in seconds (default: 300)
      retry:                  # Retry configuration
        attempts: number      # Max retry attempts
        delay: number         # Delay between retries (seconds)
      on_failure: string      # abort (default), continue, rollback
      requires: [string]      # Step dependencies (step IDs)
      
  # Output definitions
  outputs:
    - name: string            # Output name
      from_step: string       # Step ID providing output
      path: string            # JSONPath to extract value
```

## Pre-built Templates

### 1. Python Project Setup
```yaml
workflow:
  name: "python-project-setup"
  version: "1.0"
  description: "Initialize a Python project with best practices"
  
  inputs:
    - name: project_name
      type: string
      required: true
    - name: python_version
      type: string
      default: "3.11"
    - name: include_tests
      type: boolean
      default: true
      
  steps:
    - id: create_structure
      type: command
      command: |
        mkdir -p ${project_name}/{src,tests,docs}
        touch ${project_name}/README.md
        touch ${project_name}/.gitignore
        
    - id: setup_venv
      type: command
      command: "python${python_version} -m venv venv"
      working_dir: "${project_name}"
      
    - id: create_requirements
      type: template
      template: "requirements.txt"
      variables:
        include_dev: "${include_tests}"
```

### 2. React App Deployment
```yaml
workflow:
  name: "react-app-deploy"
  version: "1.0"
  description: "Build and deploy React application"
  
  inputs:
    - name: app_path
      type: string
      required: true
    - name: environment
      type: enum
      values: [development, staging, production]
      required: true
      
  steps:
    - id: install_deps
      type: command
      command: "npm ci"
      working_dir: "${app_path}"
      
    - id: run_tests
      type: command
      command: "npm test -- --watchAll=false"
      working_dir: "${app_path}"
      on_failure: abort
      
    - id: build
      type: command
      command: "npm run build"
      working_dir: "${app_path}"
      environment:
        REACT_APP_ENV: "${environment}"
```

## Integration Points

### 1. Conversation Engine Integration

```python
# Message handler for Conversation Engine
async def handle_workflow_request(message: Dict[str, Any]):
    """Handle workflow generation requests from Conversation Engine"""
    
    if message["intent"]["type"] == "workflow_generation":
        description = message["content"]
        context = message.get("context", {})
        
        # Generate workflow
        workflow = generator.generate_from_text(description, context)
        
        # Return preview for approval
        return {
            "type": "workflow_preview",
            "workflow": workflow.to_dict(),
            "requires_approval": True
        }
```

### 2. Memory Manager Integration

```python
# Store workflow execution history
def store_execution_result(execution_id: str, result: Dict[str, Any]):
    """Store execution results in memory for learning"""
    memory_message = {
        "type": "workflow_execution",
        "execution_id": execution_id,
        "workflow_name": result["workflow_name"],
        "status": result["status"],
        "duration": result["duration"],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    redis_client.publish("memory_manager", json.dumps(memory_message))
```

## Security Considerations

### 1. Command Execution Safety
- Sanitize all command inputs
- Use subprocess with shell=False
- Implement command allowlists
- Sandbox execution environment

### 2. Resource Limits
- CPU and memory limits per step
- Maximum workflow execution time
- Rate limiting for workflow creation
- Storage quotas for workflow definitions

### 3. Access Control
- Workflow approval requirements
- Environment-specific permissions
- Audit logging for all executions
- Sensitive data handling

## Testing Requirements

### Unit Tests
```python
def test_natural_language_parsing():
    """Test NL to workflow conversion"""
    parser = NaturalLanguageParser()
    
    description = "Create a Python project named test_app with pytest"
    workflow_dict = parser.parse(description)
    
    assert workflow_dict["name"] == "python-project-setup"
    assert any(s["command"].contains("pytest") for s in workflow_dict["steps"])

def test_workflow_validation():
    """Test workflow validation"""
    validator = WorkflowValidator()
    
    # Valid workflow
    valid_workflow = Workflow(
        name="test",
        version="1.0",
        description="Test workflow",
        inputs=[],
        steps=[WorkflowStep(id="step1", type="command", command="echo test")]
    )
    
    result = validator.validate(valid_workflow)
    assert result.is_valid
    
    # Invalid workflow (missing required fields)
    invalid_workflow = Workflow(
        name="",  # Empty name
        version="1.0",
        description="Test",
        inputs=[],
        steps=[]
    )
    
    result = validator.validate(invalid_workflow)
    assert not result.is_valid
    assert "name" in str(result.errors)
```

### Integration Tests
- End-to-end workflow execution
- Plugin action invocation
- Rollback scenarios
- Error handling paths

## CLI Usage

```bash
# Generate workflow from description
python -m src.plugins.workflow_generator.cli generate "Set up a Django project with PostgreSQL"

# Execute workflow
python -m src.plugins.workflow_generator.cli execute workflow.yaml --inputs project_name=myapp

# Dry run workflow
python -m src.plugins.workflow_generator.cli execute workflow.yaml --dry-run

# List available templates
python -m src.plugins.workflow_generator.cli list-templates

# Validate workflow file
python -m src.plugins.workflow_generator.cli validate workflow.yaml
```

## Success Criteria

- [ ] Natural language parsing accuracy > 85%
- [ ] Workflow execution reliability > 99%
- [ ] Complete rollback capability
- [ ] 20+ pre-built templates
- [ ] Sub-second validation
- [ ] Integration with all core plugins
- [ ] Comprehensive test coverage (90%+)
- [ ] Security hardening complete
- [ ] Performance benchmarks met

## Future Enhancements

1. **Visual Workflow Editor**: Web-based drag-and-drop interface
2. **Workflow Marketplace**: Share and discover community workflows
3. **Advanced Logic**: Loops, conditionals, parallel execution
4. **Workflow Versioning**: Git-like version control for workflows
5. **Execution Analytics**: Performance metrics and optimization suggestions