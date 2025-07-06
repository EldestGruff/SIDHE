from typing import Dict, List, Optional, Any
import yaml
import json
from dataclasses import dataclass
from enum import Enum
import redis
import logging
from datetime import datetime

# Import submodules
from .parser.natural_language import NaturalLanguageParser
from .validator.schema import WorkflowValidator
from .executor.engine import WorkflowExecutor
from .templates.library import TemplateLibrary

logger = logging.getLogger(__name__)

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "command": self.command,
            "plugin": self.plugin,
            "action": self.action,
            "params": self.params,
            "working_dir": self.working_dir,
            "on_failure": self.on_failure,
            "timeout": self.timeout,
            "requires": self.requires
        }

@dataclass
class Workflow:
    name: str
    version: str
    description: str
    inputs: List[Dict[str, Any]]
    steps: List[WorkflowStep]
    outputs: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "inputs": self.inputs,
            "steps": [step.to_dict() for step in self.steps],
            "outputs": self.outputs,
            "metadata": self.metadata
        }

class WorkflowGenerator:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            self.redis = redis.from_url(redis_url)
            # Test connection
            self.redis.ping()
            logger.info("Redis connection established for WorkflowGenerator")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis connection failed: {e}. Workflow storage will be disabled.")
            self.redis = None
        
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
        logger.info(f"Generating workflow from description: {description[:100]}...")
        
        # Parse natural language to workflow structure
        workflow_dict = self.nl_parser.parse(description, context)
        
        # Check for matching templates
        template_matches = self.template_library.find_matches(description)
        if template_matches:
            logger.info(f"Found {len(template_matches)} matching templates")
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
            error_msg = f"Invalid workflow: {validation_result.errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Successfully generated workflow: {workflow.name}")
        return workflow
    
    def execute_workflow(self, workflow: Workflow, inputs: Dict[str, Any], 
                        dry_run: bool = False) -> Dict[str, Any]:
        """Execute a workflow with given inputs"""
        logger.info(f"Executing workflow: {workflow.name} (dry_run={dry_run})")
        return self.executor.execute(workflow, inputs, dry_run)
    
    def save_workflow(self, workflow: Workflow) -> str:
        """Save workflow to storage and return ID"""
        if not self.redis:
            logger.warning("Redis not available, workflow not saved")
            return None
            
        workflow_id = f"workflow:{workflow.name}:{workflow.version}"
        try:
            workflow_data = {
                "workflow": workflow.to_dict(),
                "created_at": datetime.utcnow().isoformat(),
                "status": WorkflowStatus.DRAFT.value
            }
            self.redis.set(workflow_id, json.dumps(workflow_data))
            logger.info(f"Workflow saved with ID: {workflow_id}")
            return workflow_id
        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            return None
    
    def load_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Load workflow from storage"""
        if not self.redis:
            logger.warning("Redis not available, cannot load workflow")
            return None
            
        try:
            workflow_data = self.redis.get(workflow_id)
            if not workflow_data:
                logger.warning(f"Workflow not found: {workflow_id}")
                return None
                
            data = json.loads(workflow_data)
            workflow_dict = data["workflow"]
            return self._dict_to_workflow(workflow_dict)
        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            return None
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all saved workflows"""
        if not self.redis:
            logger.warning("Redis not available, cannot list workflows")
            return []
            
        try:
            workflow_keys = self.redis.keys("workflow:*")
            workflows = []
            
            for key in workflow_keys:
                data = json.loads(self.redis.get(key))
                workflows.append({
                    "id": key.decode() if isinstance(key, bytes) else key,
                    "name": data["workflow"]["name"],
                    "version": data["workflow"]["version"],
                    "description": data["workflow"]["description"],
                    "created_at": data["created_at"],
                    "status": data["status"]
                })
            
            return sorted(workflows, key=lambda x: x["created_at"], reverse=True)
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []
    
    def _dict_to_workflow(self, workflow_dict: Dict[str, Any]) -> Workflow:
        """Convert dictionary to Workflow object"""
        steps = []
        for step_dict in workflow_dict.get("steps", []):
            step = WorkflowStep(
                id=step_dict["id"],
                type=step_dict["type"],
                description=step_dict.get("description"),
                command=step_dict.get("command"),
                plugin=step_dict.get("plugin"),
                action=step_dict.get("action"),
                params=step_dict.get("params"),
                working_dir=step_dict.get("working_dir"),
                on_failure=step_dict.get("on_failure", "abort"),
                timeout=step_dict.get("timeout", 300),
                requires=step_dict.get("requires")
            )
            steps.append(step)
        
        return Workflow(
            name=workflow_dict["name"],
            version=workflow_dict["version"],
            description=workflow_dict["description"],
            inputs=workflow_dict.get("inputs", []),
            steps=steps,
            outputs=workflow_dict.get("outputs"),
            metadata=workflow_dict.get("metadata")
        )