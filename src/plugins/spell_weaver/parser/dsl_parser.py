import yaml
import json
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class DSLParser:
    """Parser for workflow DSL files (YAML/JSON)"""
    
    def __init__(self):
        self.supported_formats = ['.yaml', '.yml', '.json']
        logger.info("DSLParser initialized")
    
    def parse_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse workflow DSL file
        
        Args:
            file_path: Path to workflow file
            
        Returns:
            Dictionary representing workflow structure
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")
        
        if file_path.suffix not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        logger.info(f"Parsing workflow file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.json':
                    workflow_dict = json.load(f)
                else:
                    workflow_dict = yaml.safe_load(f)
            
            # Validate structure
            self._validate_structure(workflow_dict)
            
            logger.info(f"Successfully parsed workflow: {workflow_dict.get('name', 'unnamed')}")
            return workflow_dict
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            raise ValueError(f"Invalid YAML in workflow file: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise ValueError(f"Invalid JSON in workflow file: {e}")
        except Exception as e:
            logger.error(f"Error parsing workflow file: {e}")
            raise ValueError(f"Failed to parse workflow file: {e}")
    
    def parse_string(self, content: str, format_hint: str = 'yaml') -> Dict[str, Any]:
        """
        Parse workflow DSL from string
        
        Args:
            content: Workflow content as string
            format_hint: Format hint ('yaml' or 'json')
            
        Returns:
            Dictionary representing workflow structure
        """
        logger.info(f"Parsing workflow string (format: {format_hint})")
        
        try:
            if format_hint.lower() == 'json':
                workflow_dict = json.loads(content)
            else:
                workflow_dict = yaml.safe_load(content)
            
            # Validate structure
            self._validate_structure(workflow_dict)
            
            logger.info(f"Successfully parsed workflow: {workflow_dict.get('name', 'unnamed')}")
            return workflow_dict
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            raise ValueError(f"Invalid YAML content: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise ValueError(f"Invalid JSON content: {e}")
        except Exception as e:
            logger.error(f"Error parsing workflow content: {e}")
            raise ValueError(f"Failed to parse workflow content: {e}")
    
    def validate_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate workflow file and return validation results
        
        Args:
            file_path: Path to workflow file
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "workflow": None
        }
        
        try:
            workflow_dict = self.parse_file(file_path)
            validation_result["workflow"] = workflow_dict
            
            # Perform detailed validation
            errors, warnings = self._detailed_validation(workflow_dict)
            validation_result["errors"] = errors
            validation_result["warnings"] = warnings
            validation_result["valid"] = len(errors) == 0
            
        except Exception as e:
            validation_result["errors"] = [str(e)]
        
        return validation_result
    
    def convert_to_yaml(self, workflow_dict: Dict[str, Any]) -> str:
        """Convert workflow dictionary to YAML string"""
        try:
            return yaml.dump(workflow_dict, default_flow_style=False, indent=2)
        except Exception as e:
            logger.error(f"Error converting to YAML: {e}")
            raise ValueError(f"Failed to convert workflow to YAML: {e}")
    
    def convert_to_json(self, workflow_dict: Dict[str, Any]) -> str:
        """Convert workflow dictionary to JSON string"""
        try:
            return json.dumps(workflow_dict, indent=2)
        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            raise ValueError(f"Failed to convert workflow to JSON: {e}")
    
    def _validate_structure(self, workflow_dict: Dict[str, Any]) -> None:
        """Validate basic workflow structure"""
        if not isinstance(workflow_dict, dict):
            raise ValueError("Workflow must be a dictionary")
        
        # Check required fields
        required_fields = ["name", "version", "description", "steps"]
        for field in required_fields:
            if field not in workflow_dict:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate steps
        if not isinstance(workflow_dict["steps"], list):
            raise ValueError("Steps must be a list")
        
        if len(workflow_dict["steps"]) == 0:
            raise ValueError("Workflow must have at least one step")
        
        # Validate each step
        for i, step in enumerate(workflow_dict["steps"]):
            if not isinstance(step, dict):
                raise ValueError(f"Step {i} must be a dictionary")
            
            if "id" not in step:
                raise ValueError(f"Step {i} missing required field: id")
            
            if "type" not in step:
                raise ValueError(f"Step {i} missing required field: type")
    
    def _detailed_validation(self, workflow_dict: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """
        Perform detailed validation of workflow structure
        
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Validate workflow metadata
        if not workflow_dict.get("name"):
            errors.append("Workflow name cannot be empty")
        
        if not workflow_dict.get("version"):
            errors.append("Workflow version cannot be empty")
        elif not self._is_valid_version(workflow_dict["version"]):
            warnings.append("Version should follow semantic versioning (e.g., '1.0')")
        
        # Validate inputs
        if "inputs" in workflow_dict:
            if not isinstance(workflow_dict["inputs"], list):
                errors.append("Inputs must be a list")
            else:
                for i, input_def in enumerate(workflow_dict["inputs"]):
                    input_errors = self._validate_input(input_def, i)
                    errors.extend(input_errors)
        
        # Validate steps
        step_ids = set()
        for i, step in enumerate(workflow_dict["steps"]):
            step_errors, step_warnings = self._validate_step(step, i, step_ids)
            errors.extend(step_errors)
            warnings.extend(step_warnings)
            
            # Track step IDs for dependency validation
            if "id" in step:
                step_ids.add(step["id"])
        
        # Validate step dependencies
        for step in workflow_dict["steps"]:
            if "requires" in step and step["requires"]:
                for dep in step["requires"]:
                    if dep not in step_ids:
                        errors.append(f"Step '{step['id']}' depends on non-existent step '{dep}'")
        
        return errors, warnings
    
    def _validate_input(self, input_def: Dict[str, Any], index: int) -> List[str]:
        """Validate input definition"""
        errors = []
        
        if not isinstance(input_def, dict):
            errors.append(f"Input {index} must be a dictionary")
            return errors
        
        if "name" not in input_def:
            errors.append(f"Input {index} missing required field: name")
        
        if "type" not in input_def:
            errors.append(f"Input {index} missing required field: type")
        else:
            valid_types = ["string", "number", "boolean", "array", "object", "enum"]
            if input_def["type"] not in valid_types:
                errors.append(f"Input {index} has invalid type: {input_def['type']}")
        
        return errors
    
    def _validate_step(self, step: Dict[str, Any], index: int, existing_ids: set) -> tuple[List[str], List[str]]:
        """Validate step definition"""
        errors = []
        warnings = []
        
        if not isinstance(step, dict):
            errors.append(f"Step {index} must be a dictionary")
            return errors, warnings
        
        # Check required fields
        if "id" not in step:
            errors.append(f"Step {index} missing required field: id")
        elif step["id"] in existing_ids:
            errors.append(f"Step {index} has duplicate ID: {step['id']}")
        
        if "type" not in step:
            errors.append(f"Step {index} missing required field: type")
        else:
            valid_types = ["command", "plugin_action", "template", "conditional"]
            if step["type"] not in valid_types:
                errors.append(f"Step {index} has invalid type: {step['type']}")
        
        # Type-specific validation
        if step.get("type") == "command":
            if "command" not in step:
                errors.append(f"Step {index} of type 'command' must have 'command' field")
        
        elif step.get("type") == "plugin_action":
            if "plugin" not in step:
                errors.append(f"Step {index} of type 'plugin_action' must have 'plugin' field")
            if "action" not in step:
                errors.append(f"Step {index} of type 'plugin_action' must have 'action' field")
        
        elif step.get("type") == "template":
            if "template" not in step:
                errors.append(f"Step {index} of type 'template' must have 'template' field")
        
        elif step.get("type") == "conditional":
            if "condition" not in step:
                errors.append(f"Step {index} of type 'conditional' must have 'condition' field")
        
        # Validate optional fields
        if "timeout" in step:
            if not isinstance(step["timeout"], int) or step["timeout"] < 1:
                errors.append(f"Step {index} timeout must be a positive integer")
            elif step["timeout"] > 3600:
                warnings.append(f"Step {index} has very long timeout ({step['timeout']}s)")
        
        if "on_failure" in step:
            valid_failure_modes = ["abort", "continue", "rollback"]
            if step["on_failure"] not in valid_failure_modes:
                errors.append(f"Step {index} has invalid on_failure mode: {step['on_failure']}")
        
        # Check for missing description
        if not step.get("description"):
            warnings.append(f"Step {index} ('{step.get('id', 'unnamed')}') missing description")
        
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