import asyncio
import subprocess
import json
import logging
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime
import tempfile
from pathlib import Path

# Import WorkflowStep at runtime to avoid circular imports

logger = logging.getLogger(__name__)

class StepRunner:
    """Executes individual workflow steps"""
    
    def __init__(self):
        self.plugin_registry = {}
        self.template_cache = {}
        
        # Register built-in plugins
        self._register_built_in_plugins()
        
        logger.info("StepRunner initialized")
    
    async def run(self, step: Any, context) -> Dict[str, Any]:
        """
        Execute a workflow step
        
        Args:
            step: WorkflowStep to execute
            context: ExecutionContext
            
        Returns:
            Step execution result
        """
        logger.info(f"Running step: {step.id} (type: {step.type})")
        
        start_time = time.time()
        
        try:
            # Apply timeout
            if step.timeout:
                result = await asyncio.wait_for(
                    self._execute_step(step, context),
                    timeout=step.timeout
                )
            else:
                result = await self._execute_step(step, context)
            
            duration = time.time() - start_time
            result["duration"] = duration
            
            logger.info(f"Step {step.id} completed in {duration:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.error(f"Step {step.id} timed out after {duration:.2f}s")
            return {
                "success": False,
                "error": f"Step timed out after {step.timeout}s",
                "step_id": step.id,
                "duration": duration
            }
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Step {step.id} failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "step_id": step.id,
                "duration": duration
            }
    
    async def _execute_step(self, step: Any, context) -> Dict[str, Any]:
        """Execute step based on type"""
        if step.type == "command":
            return await self._execute_command(step, context)
        
        elif step.type == "plugin_action":
            return await self._execute_plugin_action(step, context)
        
        elif step.type == "template":
            return await self._execute_template(step, context)
        
        elif step.type == "conditional":
            return await self._execute_conditional(step, context)
        
        else:
            raise ValueError(f"Unknown step type: {step.type}")
    
    async def _execute_command(self, step: Any, context) -> Dict[str, Any]:
        """Execute shell command"""
        command = step.command
        if not command:
            raise ValueError("Command step must have a command")
        
        # Substitute variables
        command = self._substitute_variables(command, context)
        
        logger.info(f"Executing command: {command}")
        
        # Set up environment
        env = os.environ.copy()
        if step.params and step.params.get("environment"):
            env.update(step.params["environment"])
        
        # Set working directory
        cwd = step.working_dir
        if cwd:
            cwd = self._substitute_variables(cwd, context)
            cwd = os.path.expanduser(cwd)
        
        # Execute command
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            success = process.returncode == 0
            
            result = {
                "success": success,
                "step_id": step.id,
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "output": stdout_text if success else stderr_text
            }
            
            # Extract variables from output if specified
            if step.params and step.params.get("extract_variables"):
                result["variables"] = self._extract_variables_from_output(
                    stdout_text, step.params["extract_variables"]
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "step_id": step.id,
                "error": str(e),
                "output": ""
            }
    
    async def _execute_plugin_action(self, step: Any, context) -> Dict[str, Any]:
        """Execute plugin action"""
        plugin_name = step.plugin
        action_name = step.action
        
        if not plugin_name or not action_name:
            raise ValueError("Plugin action step must specify plugin and action")
        
        logger.info(f"Executing plugin action: {plugin_name}.{action_name}")
        
        # Get plugin instance
        plugin = self.plugin_registry.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin not found: {plugin_name}")
        
        # Get action method
        action_method = getattr(plugin, action_name, None)
        if not action_method:
            raise ValueError(f"Action not found: {plugin_name}.{action_name}")
        
        # Prepare parameters
        params = step.params or {}
        params = self._substitute_variables_in_dict(params, context)
        
        # Execute action
        try:
            if asyncio.iscoroutinefunction(action_method):
                result = await action_method(**params)
            else:
                result = action_method(**params)
            
            return {
                "success": True,
                "step_id": step.id,
                "output": result,
                "plugin": plugin_name,
                "action": action_name
            }
            
        except Exception as e:
            logger.error(f"Plugin action failed: {e}")
            return {
                "success": False,
                "step_id": step.id,
                "error": str(e),
                "plugin": plugin_name,
                "action": action_name
            }
    
    async def _execute_template(self, step: Any, context) -> Dict[str, Any]:
        """Execute template step"""
        template_name = step.params.get("template") if step.params else None
        if not template_name:
            raise ValueError("Template step must specify template name")
        
        logger.info(f"Executing template: {template_name}")
        
        # Load template
        template = self._load_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        # Substitute variables in template
        variables = step.params.get("variables", {})
        variables = self._substitute_variables_in_dict(variables, context)
        
        # Execute template steps
        results = []
        for template_step in template.get("steps", []):
            # Import WorkflowStep here to avoid circular imports
            from ..plugin_interface import WorkflowStep
            
            # Create step object
            temp_step = WorkflowStep(
                id=f"{step.id}_{template_step['id']}",
                type=template_step["type"],
                description=template_step.get("description"),
                command=template_step.get("command"),
                plugin=template_step.get("plugin"),
                action=template_step.get("action"),
                params=template_step.get("params"),
                working_dir=template_step.get("working_dir"),
                timeout=template_step.get("timeout", 300),
                on_failure=template_step.get("on_failure", "abort")
            )
            
            # Substitute template variables
            if temp_step.command:
                temp_step.command = self._substitute_template_variables(temp_step.command, variables)
            
            # Execute step
            step_result = await self.run(temp_step, context)
            results.append(step_result)
            
            # Check for failure
            if not step_result.get("success", False):
                return {
                    "success": False,
                    "step_id": step.id,
                    "error": f"Template step failed: {step_result.get('error')}",
                    "template": template_name,
                    "results": results
                }
        
        return {
            "success": True,
            "step_id": step.id,
            "template": template_name,
            "results": results,
            "output": "Template executed successfully"
        }
    
    async def _execute_conditional(self, step: Any, context) -> Dict[str, Any]:
        """Execute conditional step"""
        condition = step.params.get("condition") if step.params else None
        if not condition:
            raise ValueError("Conditional step must specify condition")
        
        logger.info(f"Evaluating condition: {condition}")
        
        # Evaluate condition
        condition_result = self._evaluate_condition(condition, context)
        
        # Choose steps to execute
        if condition_result:
            steps_to_execute = step.params.get("then_steps", [])
        else:
            steps_to_execute = step.params.get("else_steps", [])
        
        # Execute chosen steps
        results = []
        for conditional_step in steps_to_execute:
            # Import WorkflowStep here to avoid circular imports
            from ..plugin_interface import WorkflowStep
            
            # Create step object
            temp_step = WorkflowStep(
                id=f"{step.id}_{conditional_step['id']}",
                type=conditional_step["type"],
                description=conditional_step.get("description"),
                command=conditional_step.get("command"),
                plugin=conditional_step.get("plugin"),
                action=conditional_step.get("action"),
                params=conditional_step.get("params"),
                working_dir=conditional_step.get("working_dir"),
                timeout=conditional_step.get("timeout", 300),
                on_failure=conditional_step.get("on_failure", "abort")
            )
            
            # Execute step
            step_result = await self.run(temp_step, context)
            results.append(step_result)
            
            # Check for failure
            if not step_result.get("success", False):
                return {
                    "success": False,
                    "step_id": step.id,
                    "error": f"Conditional step failed: {step_result.get('error')}",
                    "condition": condition,
                    "condition_result": condition_result,
                    "results": results
                }
        
        return {
            "success": True,
            "step_id": step.id,
            "condition": condition,
            "condition_result": condition_result,
            "results": results,
            "output": f"Conditional executed ({'then' if condition_result else 'else'} branch)"
        }
    
    def _substitute_variables(self, text: str, context) -> str:
        """Substitute variables in text"""
        if not text:
            return text
        
        # Context variables
        variables = {
            **context.inputs,
            **context.variables,
            **{f"step.{k}.output": v.get("output", "") for k, v in context.step_results.items()}
        }
        
        # Simple variable substitution
        result = text
        for var_name, var_value in variables.items():
            placeholder = f"${{{var_name}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(var_value))
        
        return result
    
    def _substitute_variables_in_dict(self, data: Dict[str, Any], context) -> Dict[str, Any]:
        """Substitute variables in dictionary recursively"""
        if isinstance(data, dict):
            return {k: self._substitute_variables_in_dict(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_variables_in_dict(item, context) for item in data]
        elif isinstance(data, str):
            return self._substitute_variables(data, context)
        else:
            return data
    
    def _substitute_template_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute template variables"""
        if not text:
            return text
        
        result = text
        for var_name, var_value in variables.items():
            placeholder = f"${{{var_name}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(var_value))
        
        return result
    
    def _extract_variables_from_output(self, output: str, extraction_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract variables from command output"""
        variables = {}
        
        # JSON extraction
        if extraction_config.get("json"):
            try:
                data = json.loads(output)
                for var_name, json_path in extraction_config["json"].items():
                    value = self._extract_json_value(data, json_path)
                    variables[var_name] = value
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from output")
        
        # Regex extraction
        if extraction_config.get("regex"):
            import re
            for var_name, pattern in extraction_config["regex"].items():
                match = re.search(pattern, output)
                if match:
                    variables[var_name] = match.group(1) if match.groups() else match.group(0)
        
        return variables
    
    def _extract_json_value(self, data: Any, path: str) -> Any:
        """Extract value from JSON using dot notation"""
        if not path:
            return data
        
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                current = current[index] if 0 <= index < len(current) else None
            else:
                return None
        
        return current
    
    def _evaluate_condition(self, condition: str, context) -> bool:
        """Evaluate conditional expression"""
        # Simple condition evaluation
        # In a production system, use a proper expression evaluator
        
        # Substitute variables
        condition = self._substitute_variables(condition, context)
        
        # Basic comparisons
        if " == " in condition:
            left, right = condition.split(" == ", 1)
            return left.strip() == right.strip()
        elif " != " in condition:
            left, right = condition.split(" != ", 1)
            return left.strip() != right.strip()
        elif " > " in condition:
            left, right = condition.split(" > ", 1)
            try:
                return float(left.strip()) > float(right.strip())
            except ValueError:
                return False
        elif " < " in condition:
            left, right = condition.split(" < ", 1)
            try:
                return float(left.strip()) < float(right.strip())
            except ValueError:
                return False
        
        # Boolean evaluation
        if condition.lower() in ["true", "1", "yes"]:
            return True
        elif condition.lower() in ["false", "0", "no"]:
            return False
        
        # Variable existence
        return bool(condition)
    
    def _load_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Load workflow template"""
        # Check cache first
        if template_name in self.template_cache:
            return self.template_cache[template_name]
        
        # Try to load from templates directory
        template_path = Path(__file__).parent.parent / "templates" / "patterns" / f"{template_name}.json"
        
        if template_path.exists():
            try:
                with open(template_path, 'r') as f:
                    template = json.load(f)
                    self.template_cache[template_name] = template
                    return template
            except Exception as e:
                logger.error(f"Failed to load template {template_name}: {e}")
        
        return None
    
    def _register_built_in_plugins(self):
        """Register built-in plugins"""
        try:
            # Import and register plugins
            from ...quest_tracker.plugin_interface import QuestTracker
            self.plugin_registry["github"] = QuestTracker()
            
            from ...tome_keeper.plugin_interface import MemoryManager
            self.plugin_registry["memory"] = MemoryManager()
            
            logger.info("Built-in plugins registered")
        except ImportError as e:
            logger.warning(f"Failed to register some plugins: {e}")
    
    def register_plugin(self, name: str, plugin_instance):
        """Register external plugin"""
        self.plugin_registry[name] = plugin_instance
        logger.info(f"Plugin registered: {name}")
    
    def list_plugins(self) -> list:
        """List available plugins"""
        return list(self.plugin_registry.keys())