import anthropic
import yaml
import json
import logging
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)

class NaturalLanguageParser:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize parser with Anthropic API key"""
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        logger.info("NaturalLanguageParser initialized with Anthropic API")
        
    def parse(self, description: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Convert natural language to workflow structure using LLM
        
        Args:
            description: Natural language workflow description
            context: Optional context from conversation
            
        Returns:
            Dictionary representing workflow structure
        """
        logger.info(f"Parsing natural language description: {description[:100]}...")
        
        system_prompt = """You are a workflow generator that converts natural language 
        descriptions into structured workflow definitions. Output valid YAML that follows 
        this exact schema:

        ```yaml
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
        ```
        
        Rules:
        1. Generate a meaningful name based on the description
        2. Always use version "1.0" for new workflows
        3. Include proper error handling with on_failure settings
        4. Use reasonable timeouts (60s for quick commands, 300s for longer operations)
        5. Include all necessary inputs with appropriate types
        6. Make steps atomic and well-described
        7. Use descriptive step IDs (e.g., "install_dependencies", "run_tests")
        8. For file operations, use absolute paths or specify working_dir
        9. Return ONLY valid YAML, no additional text or formatting
        
        Example workflow types:
        - command: Shell commands (npm install, git clone, etc.)
        - plugin_action: Call other SIDHE plugins
        - template: Use pre-built workflow templates
        - conditional: Execute steps based on conditions"""
        
        user_content = f"Convert this to a workflow: {description}"
        if context:
            user_content += f"\n\nContext: {json.dumps(context)}"
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
                max_tokens=4000
            )
            
            # Extract YAML content from response
            yaml_content = response.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if yaml_content.startswith("```yaml"):
                yaml_content = yaml_content[7:]
            elif yaml_content.startswith("```"):
                yaml_content = yaml_content[3:]
            if yaml_content.endswith("```"):
                yaml_content = yaml_content[:-3]
            
            yaml_content = yaml_content.strip()
            
            # Parse YAML response
            workflow_dict = yaml.safe_load(yaml_content)
            
            # Validate basic structure
            if not isinstance(workflow_dict, dict):
                raise ValueError("Invalid workflow structure returned by LLM")
            
            required_fields = ["name", "version", "description", "steps"]
            missing_fields = [field for field in required_fields if field not in workflow_dict]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Ensure inputs exist (can be empty)
            if "inputs" not in workflow_dict:
                workflow_dict["inputs"] = []
            
            logger.info(f"Successfully parsed workflow: {workflow_dict['name']}")
            return workflow_dict
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise ValueError(f"Failed to parse natural language: {e}")
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            raise ValueError(f"Invalid YAML generated by LLM: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during parsing: {e}")
            raise ValueError(f"Failed to parse natural language: {e}")
    
    def validate_workflow_structure(self, workflow_dict: Dict[str, Any]) -> List[str]:
        """
        Validate basic workflow structure
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required top-level fields
        required_fields = ["name", "version", "description", "steps"]
        for field in required_fields:
            if field not in workflow_dict:
                errors.append(f"Missing required field: {field}")
        
        # Validate steps
        if "steps" in workflow_dict:
            if not isinstance(workflow_dict["steps"], list):
                errors.append("Steps must be a list")
            else:
                for i, step in enumerate(workflow_dict["steps"]):
                    if not isinstance(step, dict):
                        errors.append(f"Step {i} must be a dictionary")
                        continue
                    
                    # Check required step fields
                    if "id" not in step:
                        errors.append(f"Step {i} missing required field: id")
                    if "type" not in step:
                        errors.append(f"Step {i} missing required field: type")
                    
                    # Validate step type
                    valid_types = ["command", "plugin_action", "template", "conditional"]
                    if step.get("type") not in valid_types:
                        errors.append(f"Step {i} has invalid type: {step.get('type')}")
        
        # Validate inputs
        if "inputs" in workflow_dict:
            if not isinstance(workflow_dict["inputs"], list):
                errors.append("Inputs must be a list")
            else:
                for i, input_def in enumerate(workflow_dict["inputs"]):
                    if not isinstance(input_def, dict):
                        errors.append(f"Input {i} must be a dictionary")
                        continue
                    
                    if "name" not in input_def:
                        errors.append(f"Input {i} missing required field: name")
                    if "type" not in input_def:
                        errors.append(f"Input {i} missing required field: type")
        
        return errors
    
    def suggest_improvements(self, workflow_dict: Dict[str, Any]) -> List[str]:
        """
        Suggest improvements for generated workflow
        
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Check for missing descriptions
        if not workflow_dict.get("description"):
            suggestions.append("Add a more detailed workflow description")
        
        # Check steps for improvements
        for step in workflow_dict.get("steps", []):
            # Suggest descriptions for steps
            if not step.get("description"):
                suggestions.append(f"Add description for step '{step.get('id')}'")
            
            # Check for reasonable timeouts
            if step.get("timeout", 300) > 600:
                suggestions.append(f"Consider shorter timeout for step '{step.get('id')}'")
            
            # Suggest error handling
            if step.get("on_failure") == "abort":
                suggestions.append(f"Consider rollback strategy for step '{step.get('id')}'")
        
        # Check for input validation
        for input_def in workflow_dict.get("inputs", []):
            if not input_def.get("description"):
                suggestions.append(f"Add description for input '{input_def.get('name')}'")
        
        return suggestions