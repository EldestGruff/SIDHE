import asyncio
import json
import logging
import subprocess
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

# Import only what we need to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..plugin_interface import WorkflowStatus, Workflow, WorkflowStep
else:
    # Use module-level imports to avoid circular dependency
    import sys
    WorkflowStatus = type('WorkflowStatus', (), {})
    Workflow = type('Workflow', (), {})
    WorkflowStep = type('WorkflowStep', (), {})
from .step_runner import StepRunner
from .rollback import RollbackManager

logger = logging.getLogger(__name__)

@dataclass
class ExecutionContext:
    workflow: Any  # Workflow type
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    step_results: Dict[str, Any]
    status: Any  # WorkflowStatus type
    dry_run: bool
    start_time: datetime
    variables: Dict[str, Any]  # Runtime variables
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "workflow": self.workflow.to_dict() if hasattr(self.workflow, 'to_dict') else str(self.workflow),
            "inputs": self.inputs,
            "outputs": self.outputs,
            "step_results": self.step_results,
            "status": self.status.value if hasattr(self.status, 'value') else str(self.status),
            "dry_run": self.dry_run,
            "start_time": self.start_time.isoformat(),
            "variables": self.variables
        }

class WorkflowExecutor:
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.step_runner = StepRunner()
        self.rollback_manager = RollbackManager()
        self.active_executions = {}  # Track running executions
        
        logger.info("WorkflowExecutor initialized")
    
    async def execute(self, workflow: Any, inputs: Dict[str, Any], 
                      dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute workflow asynchronously
        
        Args:
            workflow: Workflow to execute
            inputs: Input parameters
            dry_run: If True, simulate execution without making changes
            
        Returns:
            Execution results
        """
        execution_id = f"execution:{workflow.name}:{int(time.time())}"
        logger.info(f"Starting workflow execution: {execution_id} (dry_run={dry_run})")
        
        # Import WorkflowStatus here to avoid circular imports
        from ..plugin_interface import WorkflowStatus
        
        # Initialize execution context
        context = ExecutionContext(
            workflow=workflow,
            inputs=inputs,
            outputs={},
            step_results={},
            status=WorkflowStatus.RUNNING,
            dry_run=dry_run,
            start_time=datetime.utcnow(),
            variables={}
        )
        
        # Validate inputs
        validation_errors = self._validate_inputs(workflow, inputs)
        if validation_errors:
            logger.error(f"Input validation failed: {validation_errors}")
            return {
                "execution_id": execution_id,
                "status": "FAILED",
                "error": f"Input validation failed: {', '.join(validation_errors)}",
                "outputs": {},
                "step_results": {},
                "duration": 0
            }
        
        # Store initial state
        self.active_executions[execution_id] = context
        self._save_execution_state(execution_id, context)
        
        try:
            # Execute steps in dependency order
            execution_order = self._calculate_execution_order(workflow.steps)
            logger.info(f"Execution order: {execution_order}")
            
            for step_id in execution_order:
                step = next(s for s in workflow.steps if s.id == step_id)
                logger.info(f"Executing step: {step_id}")
                
                # Check dependencies
                if not self._dependencies_met(step, context):
                    error_msg = f"Dependencies not met for step {step_id}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                
                # Execute step
                if dry_run:
                    result = await self._dry_run_step(step, context)
                else:
                    result = await self.step_runner.run(step, context)
                
                context.step_results[step_id] = result
                
                # Update variables from step output
                if result.get("variables"):
                    context.variables.update(result["variables"])
                
                # Handle failure
                if not result.get("success", False):
                    await self._handle_step_failure(step, result, context)
                    if context.status in [WorkflowStatus.FAILED, WorkflowStatus.ROLLED_BACK]:
                        break
                
                # Update execution state
                self._save_execution_state(execution_id, context)
                
                # Check for cancellation
                if execution_id not in self.active_executions:
                    logger.info(f"Execution cancelled: {execution_id}")
                    context.status = WorkflowStatus.FAILED
                    break
            
            # Workflow completed successfully
            if context.status == WorkflowStatus.RUNNING:
                context.status = WorkflowStatus.COMPLETED
                
                # Extract outputs
                context.outputs = self._extract_outputs(workflow, context)
                
                logger.info(f"Workflow execution completed: {execution_id}")
                
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            context.status = WorkflowStatus.FAILED
            
            # Attempt rollback if configured
            if workflow.metadata and workflow.metadata.get("auto_rollback", False):
                logger.info("Attempting automatic rollback")
                try:
                    await self.rollback_manager.rollback(context)
                    context.status = WorkflowStatus.ROLLED_BACK
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")
        
        finally:
            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            # Save final state
            self._save_execution_state(execution_id, context)
        
        # Calculate duration
        duration = (datetime.utcnow() - context.start_time).total_seconds()
        
        return {
            "execution_id": execution_id,
            "status": context.status.value,
            "outputs": context.outputs,
            "step_results": context.step_results,
            "duration": duration,
            "error": context.step_results.get("error") if context.status == WorkflowStatus.FAILED else None
        }
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel running execution"""
        if execution_id in self.active_executions:
            logger.info(f"Cancelling execution: {execution_id}")
            del self.active_executions[execution_id]
            return True
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current execution status"""
        if execution_id in self.active_executions:
            context = self.active_executions[execution_id]
            return {
                "execution_id": execution_id,
                "status": context.status.value,
                "current_step": self._get_current_step(context),
                "progress": self._calculate_progress(context),
                "duration": (datetime.utcnow() - context.start_time).total_seconds()
            }
        
        # Try to load from storage
        if self.redis:
            try:
                stored_data = self.redis.get(f"execution:{execution_id}")
                if stored_data:
                    return json.loads(stored_data)
            except Exception as e:
                logger.error(f"Failed to load execution status: {e}")
        
        return None
    
    def _validate_inputs(self, workflow: Any, inputs: Dict[str, Any]) -> List[str]:
        """Validate workflow inputs"""
        errors = []
        
        # Check required inputs
        for input_def in workflow.inputs:
            name = input_def.get("name")
            required = input_def.get("required", False)
            input_type = input_def.get("type", "string")
            
            if required and name not in inputs:
                errors.append(f"Required input missing: {name}")
            elif name in inputs:
                # Type validation
                value = inputs[name]
                if not self._validate_input_type(value, input_type):
                    errors.append(f"Invalid type for input '{name}': expected {input_type}")
        
        return errors
    
    def _validate_input_type(self, value: Any, expected_type: str) -> bool:
        """Validate input type"""
        type_map = {
            "string": str,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        if expected_type not in type_map:
            return True  # Unknown type, skip validation
        
        expected_python_type = type_map[expected_type]
        return isinstance(value, expected_python_type)
    
    def _calculate_execution_order(self, steps: List[Any]) -> List[str]:
        """Calculate step execution order respecting dependencies"""
        # Build dependency graph
        dependencies = {}
        for step in steps:
            dependencies[step.id] = step.requires or []
        
        # Topological sort
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(node):
            if node in temp_visited:
                raise ValueError(f"Circular dependency detected involving step: {node}")
            if node in visited:
                return
            
            temp_visited.add(node)
            for dep in dependencies.get(node, []):
                visit(dep)
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)
        
        # Visit all nodes
        for step_id in dependencies:
            if step_id not in visited:
                visit(step_id)
        
        return result
    
    def _dependencies_met(self, step: Any, context: ExecutionContext) -> bool:
        """Check if step dependencies are met"""
        if not step.requires:
            return True
        
        for dep in step.requires:
            if dep not in context.step_results:
                return False
            
            # Check if dependency step succeeded
            dep_result = context.step_results[dep]
            if not dep_result.get("success", False):
                return False
        
        return True
    
    async def _dry_run_step(self, step: Any, context: ExecutionContext) -> Dict[str, Any]:
        """Simulate step execution without making changes"""
        logger.info(f"Dry run step: {step.id}")
        
        # Simulate execution time
        await asyncio.sleep(0.1)
        
        result = {
            "success": True,
            "dry_run": True,
            "step_id": step.id,
            "message": f"Dry run: {step.description or step.id}",
            "duration": 0.1
        }
        
        # Generate mock output based on step type
        if step.type == "command":
            result["output"] = f"Mock output for command: {step.command}"
        elif step.type == "plugin_action":
            result["output"] = f"Mock output for plugin action: {step.plugin}.{step.action}"
        
        return result
    
    async def _handle_step_failure(self, step: Any, result: Dict[str, Any], 
                                   context: ExecutionContext) -> None:
        """Handle step failure based on failure mode"""
        failure_mode = step.on_failure
        
        logger.warning(f"Step {step.id} failed with mode: {failure_mode}")
        
        if failure_mode == "abort":
            context.status = WorkflowStatus.FAILED
            logger.error(f"Workflow aborted due to step failure: {step.id}")
        
        elif failure_mode == "continue":
            logger.info(f"Continuing after step failure: {step.id}")
            # Continue execution
        
        elif failure_mode == "rollback":
            logger.info(f"Rolling back due to step failure: {step.id}")
            try:
                await self.rollback_manager.rollback(context)
                context.status = WorkflowStatus.ROLLED_BACK
            except Exception as e:
                logger.error(f"Rollback failed: {e}")
                context.status = WorkflowStatus.FAILED
    
    def _extract_outputs(self, workflow: Any, context: ExecutionContext) -> Dict[str, Any]:
        """Extract workflow outputs from step results"""
        outputs = {}
        
        if not workflow.outputs:
            return outputs
        
        for output_def in workflow.outputs:
            output_name = output_def.get("name")
            from_step = output_def.get("from_step")
            path = output_def.get("path", "output")
            
            if from_step in context.step_results:
                step_result = context.step_results[from_step]
                
                # Extract value using path
                try:
                    value = self._extract_value_by_path(step_result, path)
                    outputs[output_name] = value
                except Exception as e:
                    logger.warning(f"Failed to extract output '{output_name}': {e}")
                    outputs[output_name] = None
        
        return outputs
    
    def _extract_value_by_path(self, data: Dict[str, Any], path: str) -> Any:
        """Extract value from nested dictionary using dot notation"""
        if not path:
            return data
        
        parts = path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                raise ValueError(f"Cannot access path '{path}' - not a dictionary")
        
        return current
    
    def _get_current_step(self, context: ExecutionContext) -> Optional[str]:
        """Get currently executing step"""
        completed_steps = set(context.step_results.keys())
        
        for step in context.workflow.steps:
            if step.id not in completed_steps:
                # Check if dependencies are met
                if self._dependencies_met(step, context):
                    return step.id
        
        return None
    
    def _calculate_progress(self, context: ExecutionContext) -> float:
        """Calculate execution progress (0.0 to 1.0)"""
        total_steps = len(context.workflow.steps)
        completed_steps = len(context.step_results)
        
        if total_steps == 0:
            return 1.0
        
        return completed_steps / total_steps
    
    def _save_execution_state(self, execution_id: str, context: ExecutionContext) -> None:
        """Save execution state to storage"""
        if not self.redis:
            return
        
        try:
            state_data = {
                "execution_id": execution_id,
                "status": context.status.value,
                "outputs": context.outputs,
                "step_results": context.step_results,
                "start_time": context.start_time.isoformat(),
                "last_update": datetime.utcnow().isoformat(),
                "progress": self._calculate_progress(context)
            }
            
            # Store with TTL (24 hours)
            self.redis.setex(f"execution:{execution_id}", 86400, json.dumps(state_data))
        except Exception as e:
            logger.error(f"Failed to save execution state: {e}")
    
    def list_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent executions"""
        if not self.redis:
            return []
        
        try:
            execution_keys = self.redis.keys("execution:*")
            executions = []
            
            for key in execution_keys[:limit]:
                data = json.loads(self.redis.get(key))
                executions.append(data)
            
            # Sort by start time
            executions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
            return executions
        except Exception as e:
            logger.error(f"Failed to list executions: {e}")
            return []