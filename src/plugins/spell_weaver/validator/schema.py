from jsonschema import validate, ValidationError
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

from .safety_checker import SafetyChecker

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __bool__(self):
        return self.is_valid

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
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "type": {"enum": ["command", "plugin_action", "template", "conditional"]},
                            "description": {"type": "string"},
                            "command": {"type": "string"},
                            "plugin": {"type": "string"},
                            "action": {"type": "string"},
                            "params": {"type": "object"},
                            "working_dir": {"type": "string"},
                            "environment": {"type": "object"},
                            "timeout": {"type": "integer", "minimum": 1},
                            "on_failure": {"enum": ["abort", "continue", "rollback"]},
                            "requires": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "retry": {
                                "type": "object",
                                "properties": {
                                    "attempts": {"type": "integer", "minimum": 1},
                                    "delay": {"type": "number", "minimum": 0}
                                }
                            }
                        },
                        "required": ["id", "type"]
                    }
                },
                "outputs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "from_step": {"type": "string"},
                            "path": {"type": "string"}
                        },
                        "required": ["name", "from_step"]
                    }
                },
                "metadata": {"type": "object"}
            },
            "required": ["name", "version", "description", "steps"]
        }
        
        self.safety_checker = SafetyChecker()
        logger.info("WorkflowValidator initialized")
    
    def validate(self, workflow) -> ValidationResult:
        """
        Validate workflow structure and safety
        
        Args:
            workflow: Workflow object to validate
            
        Returns:
            ValidationResult with validation status and messages
        """
        logger.info(f"Validating workflow: {workflow.name}")
        
        errors = []
        warnings = []
        
        # Convert workflow to dictionary for validation
        workflow_dict = workflow.to_dict()
        
        # Schema validation
        try:
            validate(workflow_dict, self.schema)
            logger.debug("Schema validation passed")
        except ValidationError as e:
            error_msg = f"Schema validation failed: {e.message}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Custom validation rules
        custom_errors, custom_warnings = self._custom_validation(workflow_dict)
        errors.extend(custom_errors)
        warnings.extend(custom_warnings)
        
        # Safety validation
        try:
            safety_result = self.safety_checker.check(workflow)
            if not safety_result.is_safe:
                errors.extend(safety_result.violations)
            warnings.extend(safety_result.warnings)
            logger.debug(f"Safety check completed: {len(safety_result.violations)} violations")
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            errors.append(f"Safety validation failed: {e}")
        
        # Dependency validation
        dep_errors = self._validate_dependencies(workflow_dict)
        errors.extend(dep_errors)
        
        # Business logic validation
        business_errors, business_warnings = self._validate_business_logic(workflow_dict)
        errors.extend(business_errors)
        warnings.extend(business_warnings)
        
        result = ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
        logger.info(f"Validation completed: {'PASS' if result.is_valid else 'FAIL'}")
        return result
    
    def _custom_validation(self, workflow_dict: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Custom validation rules beyond JSON schema"""
        errors = []
        warnings = []
        
        # Validate workflow name
        name = workflow_dict.get("name", "")
        if not name:
            errors.append("Workflow name cannot be empty")
        elif len(name) > 100:
            warnings.append("Workflow name is very long (>100 characters)")
        
        # Validate version format
        version = workflow_dict.get("version", "")
        if not self._is_valid_version(version):
            warnings.append("Version should follow semantic versioning (e.g., '1.0', '2.1.3')")
        
        # Validate inputs
        inputs = workflow_dict.get("inputs", [])
        input_names = set()
        for i, input_def in enumerate(inputs):
            if input_def.get("name") in input_names:
                errors.append(f"Duplicate input name: {input_def.get('name')}")
            input_names.add(input_def.get("name"))
            
            # Validate input types
            input_type = input_def.get("type", "")
            valid_types = ["string", "number", "boolean", "array", "object", "enum"]
            if input_type not in valid_types:
                errors.append(f"Invalid input type '{input_type}' for input '{input_def.get('name')}'")
        
        # Validate steps
        steps = workflow_dict.get("steps", [])
        step_ids = set()
        for i, step in enumerate(steps):
            step_id = step.get("id", "")
            if step_id in step_ids:
                errors.append(f"Duplicate step ID: {step_id}")
            step_ids.add(step_id)
            
            # Type-specific validation
            step_type = step.get("type", "")
            if step_type == "command":
                if not step.get("command"):
                    errors.append(f"Step '{step_id}' of type 'command' must have a command")
                elif len(step["command"]) > 1000:
                    warnings.append(f"Step '{step_id}' has very long command")
            
            elif step_type == "plugin_action":
                if not step.get("plugin"):
                    errors.append(f"Step '{step_id}' of type 'plugin_action' must specify a plugin")
                if not step.get("action"):
                    errors.append(f"Step '{step_id}' of type 'plugin_action' must specify an action")
            
            elif step_type == "template":
                if not step.get("template"):
                    errors.append(f"Step '{step_id}' of type 'template' must specify a template")
            
            elif step_type == "conditional":
                if not step.get("condition"):
                    errors.append(f"Step '{step_id}' of type 'conditional' must have a condition")
            
            # Validate timeout
            timeout = step.get("timeout", 300)
            if timeout > 3600:
                warnings.append(f"Step '{step_id}' has very long timeout ({timeout}s)")
            
            # Check for missing descriptions
            if not step.get("description"):
                warnings.append(f"Step '{step_id}' missing description")
        
        return errors, warnings
    
    def _validate_dependencies(self, workflow_dict: Dict[str, Any]) -> List[str]:
        """Validate step dependencies"""
        errors = []
        steps = workflow_dict.get("steps", [])
        
        # Build step ID set
        step_ids = {step.get("id") for step in steps if step.get("id")}
        
        # Check dependencies
        for step in steps:
            step_id = step.get("id", "")
            requires = step.get("requires", [])
            
            if not isinstance(requires, list):
                errors.append(f"Step '{step_id}' requires must be a list")
                continue
            
            for dep in requires:
                if dep not in step_ids:
                    errors.append(f"Step '{step_id}' depends on non-existent step '{dep}'")
                elif dep == step_id:
                    errors.append(f"Step '{step_id}' cannot depend on itself")
        
        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies(steps)
        if circular_deps:
            errors.append(f"Circular dependency detected: {' -> '.join(circular_deps)}")
        
        return errors
    
    def _detect_circular_dependencies(self, steps: List[Dict[str, Any]]) -> List[str]:
        """Detect circular dependencies in workflow steps"""
        # Build dependency graph
        dependencies = {}
        for step in steps:
            step_id = step.get("id", "")
            dependencies[step_id] = step.get("requires", [])
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            if node in rec_stack:
                # Found cycle - return path from cycle start
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            
            if node in visited:
                return []
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dependencies.get(node, []):
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
            
            rec_stack.remove(node)
            path.pop()
            return []
        
        # Check each node
        for step_id in dependencies:
            if step_id not in visited:
                cycle = dfs(step_id)
                if cycle:
                    return cycle
        
        return []
    
    def _validate_business_logic(self, workflow_dict: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Validate business logic and best practices"""
        errors = []
        warnings = []
        
        steps = workflow_dict.get("steps", [])
        
        # Check for workflows with no error handling
        has_error_handling = any(
            step.get("on_failure", "abort") != "abort" for step in steps
        )
        if not has_error_handling:
            warnings.append("Workflow has no error handling - consider adding rollback or continue strategies")
        
        # Check for very long workflows
        if len(steps) > 20:
            warnings.append("Workflow has many steps - consider breaking into smaller workflows")
        
        # Check for steps with no timeout
        steps_without_timeout = [
            step.get("id", f"step_{i}") 
            for i, step in enumerate(steps) 
            if "timeout" not in step
        ]
        if steps_without_timeout:
            warnings.append(f"Steps without explicit timeout: {', '.join(steps_without_timeout)}")
        
        # Check for potential resource conflicts
        working_dirs = []
        for step in steps:
            if step.get("working_dir"):
                working_dirs.append(step["working_dir"])
        
        if len(working_dirs) != len(set(working_dirs)):
            warnings.append("Multiple steps using same working directory - check for conflicts")
        
        # Check for missing outputs
        if not workflow_dict.get("outputs") and len(steps) > 1:
            warnings.append("Multi-step workflow with no defined outputs")
        
        return errors, warnings
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning"""
        if not isinstance(version, str):
            return False
        
        parts = version.split('.')
        if len(parts) < 2:
            return False
        
        try:
            for part in parts:
                int(part)
            return True
        except ValueError:
            return False
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """Get human-readable validation summary"""
        summary = []
        
        if result.is_valid:
            summary.append("✅ Workflow validation PASSED")
        else:
            summary.append("❌ Workflow validation FAILED")
        
        if result.errors:
            summary.append(f"\nErrors ({len(result.errors)}):")
            for error in result.errors:
                summary.append(f"  • {error}")
        
        if result.warnings:
            summary.append(f"\nWarnings ({len(result.warnings)}):")
            for warning in result.warnings:
                summary.append(f"  • {warning}")
        
        return "\n".join(summary)