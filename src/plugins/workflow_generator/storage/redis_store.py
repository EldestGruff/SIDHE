from typing import Dict, List, Optional, Any
import redis
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from ..plugin_interface import Workflow, WorkflowStatus

logger = logging.getLogger(__name__)

@dataclass
class WorkflowExecution:
    """Represents a workflow execution record"""
    execution_id: str
    workflow_name: str
    workflow_version: str
    status: WorkflowStatus
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    step_results: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "execution_id": self.execution_id,
            "workflow_name": self.workflow_name,
            "workflow_version": self.workflow_version,
            "status": self.status.value if isinstance(self.status, WorkflowStatus) else self.status,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "step_results": self.step_results,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }

class RedisWorkflowStore:
    """
    Redis-based storage for workflows and execution history
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis connection
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection with error handling"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self.redis_client = None
    
    def is_connected(self) -> bool:
        """Check if Redis connection is available"""
        return self.redis_client is not None
    
    def _ensure_connection(self) -> bool:
        """Ensure Redis connection is available, attempt reconnect if needed"""
        if not self.redis_client:
            self._connect()
        return self.redis_client is not None
    
    # Workflow Storage Methods
    
    def save_workflow(self, workflow: Workflow) -> bool:
        """
        Save a workflow definition to Redis
        
        Args:
            workflow: Workflow to save
            
        Returns:
            True if saved successfully
        """
        if not self._ensure_connection():
            logger.error("Redis connection not available")
            return False
        
        try:
            workflow_key = f"riker:workflow:{workflow.name}:{workflow.version}"
            workflow_data = {
                "workflow": workflow.to_dict(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "status": WorkflowStatus.DRAFT.value
            }
            
            # Save workflow
            self.redis_client.set(workflow_key, json.dumps(workflow_data))
            
            # Add to workflow index
            self.redis_client.sadd("riker:workflows:index", workflow_key)
            
            # Set expiration (30 days for workflow definitions)
            self.redis_client.expire(workflow_key, timedelta(days=30))
            
            logger.info(f"Saved workflow: {workflow.name} v{workflow.version}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save workflow: {e}")
            return False
    
    def load_workflow(self, workflow_name: str, version: str = None) -> Optional[Workflow]:
        """
        Load a workflow definition from Redis
        
        Args:
            workflow_name: Name of the workflow
            version: Specific version (latest if None)
            
        Returns:
            Workflow object or None if not found
        """
        if not self._ensure_connection():
            logger.error("Redis connection not available")
            return None
        
        try:
            if version:
                workflow_key = f"riker:workflow:{workflow_name}:{version}"
            else:
                # Find latest version
                workflow_key = self._find_latest_workflow_version(workflow_name)
                if not workflow_key:
                    logger.warning(f"No workflow found: {workflow_name}")
                    return None
            
            workflow_data = self.redis_client.get(workflow_key)
            if not workflow_data:
                logger.warning(f"Workflow not found: {workflow_key}")
                return None
            
            data = json.loads(workflow_data)
            workflow_dict = data["workflow"]
            
            # Convert back to Workflow object
            workflow = self._dict_to_workflow(workflow_dict)
            
            logger.info(f"Loaded workflow: {workflow.name} v{workflow.version}")
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to load workflow: {e}")
            return None
    
    def _find_latest_workflow_version(self, workflow_name: str) -> Optional[str]:
        """Find the latest version of a workflow"""
        try:
            pattern = f"riker:workflow:{workflow_name}:*"
            keys = self.redis_client.keys(pattern)
            
            if not keys:
                return None
            
            # Sort by version number (assuming semantic versioning)
            def version_key(key: str) -> tuple:
                version_str = key.split(":")[-1]
                try:
                    return tuple(map(int, version_str.split(".")))
                except ValueError:
                    return (0, 0)
            
            sorted_keys = sorted(keys, key=version_key, reverse=True)
            return sorted_keys[0]
            
        except Exception as e:
            logger.error(f"Error finding latest workflow version: {e}")
            return None
    
    def list_workflows(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all available workflows
        
        Args:
            limit: Maximum number of workflows to return
            
        Returns:
            List of workflow metadata
        """
        if not self._ensure_connection():
            logger.error("Redis connection not available")
            return []
        
        try:
            workflow_keys = self.redis_client.smembers("riker:workflows:index")
            workflows = []
            
            for key in list(workflow_keys)[:limit]:
                workflow_data = self.redis_client.get(key)
                if workflow_data:
                    data = json.loads(workflow_data)
                    workflow_info = data["workflow"]
                    workflows.append({
                        "name": workflow_info["name"],
                        "version": workflow_info["version"],
                        "description": workflow_info["description"],
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "status": data["status"],
                        "key": key
                    })
            
            # Sort by updated_at (newest first)
            workflows.sort(key=lambda x: x["updated_at"], reverse=True)
            
            logger.info(f"Listed {len(workflows)} workflows")
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            return []
    
    def delete_workflow(self, workflow_name: str, version: str) -> bool:
        """
        Delete a workflow definition
        
        Args:
            workflow_name: Name of the workflow
            version: Version to delete
            
        Returns:
            True if deleted successfully
        """
        if not self._ensure_connection():
            logger.error("Redis connection not available")
            return False
        
        try:
            workflow_key = f"riker:workflow:{workflow_name}:{version}"
            
            # Delete from Redis
            deleted = self.redis_client.delete(workflow_key)
            
            # Remove from index
            self.redis_client.srem("riker:workflows:index", workflow_key)
            
            if deleted:
                logger.info(f"Deleted workflow: {workflow_name} v{version}")
                return True
            else:
                logger.warning(f"Workflow not found for deletion: {workflow_name} v{version}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to delete workflow: {e}")
            return False
    
    # Execution Storage Methods
    
    def save_execution(self, execution: WorkflowExecution) -> bool:
        """
        Save workflow execution record
        
        Args:
            execution: Execution record to save
            
        Returns:
            True if saved successfully
        """
        if not self._ensure_connection():
            logger.error("Redis connection not available")
            return False
        
        try:
            execution_key = f"riker:execution:{execution.execution_id}"
            execution_data = execution.to_dict()
            
            # Save execution
            self.redis_client.set(execution_key, json.dumps(execution_data))
            
            # Add to execution index
            self.redis_client.sadd("riker:executions:index", execution_key)
            
            # Add to workflow-specific execution list
            workflow_executions_key = f"riker:executions:{execution.workflow_name}"
            self.redis_client.sadd(workflow_executions_key, execution_key)
            
            # Set expiration (7 days for execution records)
            self.redis_client.expire(execution_key, timedelta(days=7))
            
            logger.info(f"Saved execution: {execution.execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save execution: {e}")
            return False
    
    def load_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """
        Load workflow execution record
        
        Args:
            execution_id: Execution ID to load
            
        Returns:
            WorkflowExecution object or None if not found
        """
        if not self._ensure_connection():
            logger.error("Redis connection not available")
            return None
        
        try:
            execution_key = f"riker:execution:{execution_id}"
            execution_data = self.redis_client.get(execution_key)
            
            if not execution_data:
                logger.warning(f"Execution not found: {execution_id}")
                return None
            
            data = json.loads(execution_data)
            
            # Convert back to WorkflowExecution object
            execution = WorkflowExecution(
                execution_id=data["execution_id"],
                workflow_name=data["workflow_name"],
                workflow_version=data["workflow_version"],
                status=WorkflowStatus(data["status"]),
                inputs=data["inputs"],
                outputs=data["outputs"],
                step_results=data["step_results"],
                started_at=datetime.fromisoformat(data["started_at"]) if data["started_at"] else None,
                completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
                error=data.get("error")
            )
            
            logger.info(f"Loaded execution: {execution_id}")
            return execution
            
        except Exception as e:
            logger.error(f"Failed to load execution: {e}")
            return None
    
    def list_executions(self, workflow_name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List workflow executions
        
        Args:
            workflow_name: Filter by workflow name (None for all)
            limit: Maximum number of executions to return
            
        Returns:
            List of execution metadata
        """
        if not self._ensure_connection():
            logger.error("Redis connection not available")
            return []
        
        try:
            if workflow_name:
                execution_keys = self.redis_client.smembers(f"riker:executions:{workflow_name}")
            else:
                execution_keys = self.redis_client.smembers("riker:executions:index")
            
            executions = []
            
            for key in list(execution_keys)[:limit]:
                execution_data = self.redis_client.get(key)
                if execution_data:
                    data = json.loads(execution_data)
                    executions.append({
                        "execution_id": data["execution_id"],
                        "workflow_name": data["workflow_name"],
                        "workflow_version": data["workflow_version"],
                        "status": data["status"],
                        "started_at": data["started_at"],
                        "completed_at": data["completed_at"],
                        "error": data.get("error")
                    })
            
            # Sort by started_at (newest first)
            executions.sort(key=lambda x: x["started_at"], reverse=True)
            
            logger.info(f"Listed {len(executions)} executions")
            return executions
            
        except Exception as e:
            logger.error(f"Failed to list executions: {e}")
            return []
    
    def update_execution_status(self, execution_id: str, status: WorkflowStatus, 
                              outputs: Dict[str, Any] = None, error: str = None) -> bool:
        """
        Update execution status
        
        Args:
            execution_id: Execution ID to update
            status: New status
            outputs: Optional outputs to update
            error: Optional error message
            
        Returns:
            True if updated successfully
        """
        if not self._ensure_connection():
            logger.error("Redis connection not available")
            return False
        
        try:
            execution_key = f"riker:execution:{execution_id}"
            execution_data = self.redis_client.get(execution_key)
            
            if not execution_data:
                logger.warning(f"Execution not found for update: {execution_id}")
                return False
            
            data = json.loads(execution_data)
            
            # Update fields
            data["status"] = status.value if isinstance(status, WorkflowStatus) else status
            if outputs is not None:
                data["outputs"] = outputs
            if error is not None:
                data["error"] = error
            
            # Set completion time if finished
            if status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.ROLLED_BACK]:
                data["completed_at"] = datetime.utcnow().isoformat()
            
            # Save updated data
            self.redis_client.set(execution_key, json.dumps(data))
            
            logger.info(f"Updated execution status: {execution_id} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update execution status: {e}")
            return False
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """
        Clean up expired workflow and execution data
        
        Returns:
            Dictionary with cleanup statistics
        """
        if not self._ensure_connection():
            logger.error("Redis connection not available")
            return {"workflows": 0, "executions": 0}
        
        try:
            cleaned_workflows = 0
            cleaned_executions = 0
            
            # Clean up workflow index
            workflow_keys = self.redis_client.smembers("riker:workflows:index")
            for key in workflow_keys:
                if not self.redis_client.exists(key):
                    self.redis_client.srem("riker:workflows:index", key)
                    cleaned_workflows += 1
            
            # Clean up execution index
            execution_keys = self.redis_client.smembers("riker:executions:index")
            for key in execution_keys:
                if not self.redis_client.exists(key):
                    self.redis_client.srem("riker:executions:index", key)
                    cleaned_executions += 1
            
            logger.info(f"Cleaned up {cleaned_workflows} workflows, {cleaned_executions} executions")
            return {"workflows": cleaned_workflows, "executions": cleaned_executions}
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            return {"workflows": 0, "executions": 0}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        if not self._ensure_connection():
            logger.error("Redis connection not available")
            return {}
        
        try:
            stats = {
                "total_workflows": self.redis_client.scard("riker:workflows:index"),
                "total_executions": self.redis_client.scard("riker:executions:index"),
                "redis_memory_usage": self.redis_client.info("memory").get("used_memory_human", "N/A"),
                "redis_connected_clients": self.redis_client.info("clients").get("connected_clients", 0)
            }
            
            # Count workflows by status
            workflow_keys = self.redis_client.smembers("riker:workflows:index")
            status_counts = {}
            
            for key in workflow_keys:
                workflow_data = self.redis_client.get(key)
                if workflow_data:
                    data = json.loads(workflow_data)
                    status = data.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
            
            stats["workflow_status_counts"] = status_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
    
    def _dict_to_workflow(self, workflow_dict: Dict[str, Any]) -> Workflow:
        """Convert dictionary to Workflow object"""
        from ..plugin_interface import WorkflowStep
        
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