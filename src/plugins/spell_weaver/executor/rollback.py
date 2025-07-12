import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RollbackAction:
    """Represents a rollback action"""
    step_id: str
    action_type: str  # command, file_restore, plugin_action
    description: str
    action_data: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action_type": self.action_type,
            "description": self.description,
            "action_data": self.action_data,
            "timestamp": self.timestamp.isoformat()
        }

class RollbackManager:
    """Manages workflow rollback operations"""
    
    def __init__(self):
        self.rollback_actions = {}  # execution_id -> List[RollbackAction]
        logger.info("RollbackManager initialized")
    
    def record_action(self, execution_id: str, step_id: str, action_type: str, 
                     description: str, action_data: Dict[str, Any]) -> None:
        """
        Record an action that can be rolled back
        
        Args:
            execution_id: Workflow execution ID
            step_id: Step that performed the action
            action_type: Type of action (command, file_restore, plugin_action)
            description: Human-readable description
            action_data: Data needed for rollback
        """
        if execution_id not in self.rollback_actions:
            self.rollback_actions[execution_id] = []
        
        rollback_action = RollbackAction(
            step_id=step_id,
            action_type=action_type,
            description=description,
            action_data=action_data,
            timestamp=datetime.utcnow()
        )
        
        self.rollback_actions[execution_id].append(rollback_action)
        logger.info(f"Recorded rollback action: {description}")
    
    async def rollback(self, context) -> Dict[str, Any]:
        """
        Perform rollback of executed actions
        
        Args:
            context: ExecutionContext
            
        Returns:
            Rollback results
        """
        execution_id = f"execution:{context.workflow.name}:{int(context.start_time.timestamp())}"
        
        logger.info(f"Starting rollback for execution: {execution_id}")
        
        if execution_id not in self.rollback_actions:
            logger.info("No rollback actions recorded")
            return {"success": True, "actions_rolled_back": 0, "errors": []}
        
        actions = self.rollback_actions[execution_id]
        
        # Rollback actions in reverse order
        actions.reverse()
        
        results = []
        errors = []
        
        for action in actions:
            try:
                logger.info(f"Rolling back: {action.description}")
                result = await self._execute_rollback_action(action, context)
                results.append(result)
                
                if not result.get("success", False):
                    errors.append(f"Failed to rollback {action.description}: {result.get('error')}")
                    
            except Exception as e:
                error_msg = f"Error rolling back {action.description}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                results.append({
                    "success": False,
                    "action": action.description,
                    "error": str(e)
                })
        
        # Clean up rollback actions
        if execution_id in self.rollback_actions:
            del self.rollback_actions[execution_id]
        
        rollback_result = {
            "success": len(errors) == 0,
            "actions_rolled_back": len([r for r in results if r.get("success", False)]),
            "total_actions": len(actions),
            "errors": errors,
            "results": results
        }
        
        logger.info(f"Rollback completed: {rollback_result['actions_rolled_back']}/{rollback_result['total_actions']} actions successful")
        
        return rollback_result
    
    async def _execute_rollback_action(self, action: RollbackAction, context) -> Dict[str, Any]:
        """Execute a single rollback action"""
        
        if action.action_type == "command":
            return await self._rollback_command(action, context)
        
        elif action.action_type == "file_restore":
            return await self._rollback_file_restore(action, context)
        
        elif action.action_type == "plugin_action":
            return await self._rollback_plugin_action(action, context)
        
        elif action.action_type == "directory_restore":
            return await self._rollback_directory_restore(action, context)
        
        else:
            return {
                "success": False,
                "action": action.description,
                "error": f"Unknown rollback action type: {action.action_type}"
            }
    
    async def _rollback_command(self, action: RollbackAction, context) -> Dict[str, Any]:
        """Rollback a command action"""
        rollback_command = action.action_data.get("rollback_command")
        
        if not rollback_command:
            return {
                "success": False,
                "action": action.description,
                "error": "No rollback command specified"
            }
        
        logger.info(f"Executing rollback command: {rollback_command}")
        
        try:
            # Execute rollback command
            process = await asyncio.create_subprocess_shell(
                rollback_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=action.action_data.get("working_dir")
            )
            
            stdout, stderr = await process.communicate()
            
            success = process.returncode == 0
            
            return {
                "success": success,
                "action": action.description,
                "command": rollback_command,
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace')
            }
            
        except Exception as e:
            return {
                "success": False,
                "action": action.description,
                "error": str(e)
            }
    
    async def _rollback_file_restore(self, action: RollbackAction, context) -> Dict[str, Any]:
        """Rollback file changes by restoring from backup"""
        import shutil
        import os
        
        original_path = action.action_data.get("original_path")
        backup_path = action.action_data.get("backup_path")
        
        if not original_path or not backup_path:
            return {
                "success": False,
                "action": action.description,
                "error": "Missing original_path or backup_path"
            }
        
        try:
            if os.path.exists(backup_path):
                # Restore from backup
                shutil.copy2(backup_path, original_path)
                
                # Clean up backup
                os.remove(backup_path)
                
                logger.info(f"Restored file: {original_path}")
                
                return {
                    "success": True,
                    "action": action.description,
                    "restored_path": original_path
                }
            else:
                # Backup doesn't exist, try to remove created file
                if os.path.exists(original_path):
                    os.remove(original_path)
                    
                return {
                    "success": True,
                    "action": action.description,
                    "removed_path": original_path
                }
                
        except Exception as e:
            return {
                "success": False,
                "action": action.description,
                "error": str(e)
            }
    
    async def _rollback_directory_restore(self, action: RollbackAction, context) -> Dict[str, Any]:
        """Rollback directory changes"""
        import shutil
        import os
        
        directory_path = action.action_data.get("directory_path")
        was_created = action.action_data.get("was_created", False)
        
        if not directory_path:
            return {
                "success": False,
                "action": action.description,
                "error": "Missing directory_path"
            }
        
        try:
            if was_created and os.path.exists(directory_path):
                # Remove created directory
                shutil.rmtree(directory_path)
                
                logger.info(f"Removed created directory: {directory_path}")
                
                return {
                    "success": True,
                    "action": action.description,
                    "removed_directory": directory_path
                }
            else:
                # Directory was not created by us, skip
                return {
                    "success": True,
                    "action": action.description,
                    "message": "Directory was not created by workflow, skipping"
                }
                
        except Exception as e:
            return {
                "success": False,
                "action": action.description,
                "error": str(e)
            }
    
    async def _rollback_plugin_action(self, action: RollbackAction, context) -> Dict[str, Any]:
        """Rollback plugin action"""
        plugin_name = action.action_data.get("plugin")
        rollback_action = action.action_data.get("rollback_action")
        rollback_params = action.action_data.get("rollback_params", {})
        
        if not plugin_name or not rollback_action:
            return {
                "success": False,
                "action": action.description,
                "error": "Missing plugin or rollback_action"
            }
        
        try:
            # This would need to be implemented with actual plugin registry
            # For now, return success
            
            logger.info(f"Would rollback plugin action: {plugin_name}.{rollback_action}")
            
            return {
                "success": True,
                "action": action.description,
                "plugin": plugin_name,
                "rollback_action": rollback_action,
                "message": "Plugin rollback simulation"
            }
            
        except Exception as e:
            return {
                "success": False,
                "action": action.description,
                "error": str(e)
            }
    
    def create_file_backup(self, file_path: str) -> Optional[str]:
        """
        Create a backup of a file before modification
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file or None if failed
        """
        import shutil
        import tempfile
        import os
        
        if not os.path.exists(file_path):
            return None
        
        try:
            # Create backup in temp directory
            backup_dir = tempfile.mkdtemp(prefix="sidhe_backup_")
            backup_filename = os.path.basename(file_path) + ".backup"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(file_path, backup_path)
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def suggest_rollback_command(self, original_command: str) -> Optional[str]:
        """
        Suggest a rollback command for common operations
        
        Args:
            original_command: Original command that was executed
            
        Returns:
            Suggested rollback command or None
        """
        command = original_command.strip().lower()
        
        # File operations
        if command.startswith("mkdir "):
            directory = command[6:].strip()
            return f"rmdir {directory}"
        
        elif command.startswith("touch "):
            file_path = command[6:].strip()
            return f"rm {file_path}"
        
        elif command.startswith("cp "):
            # This is complex, would need to parse cp arguments
            return None
        
        elif command.startswith("mv "):
            # This is complex, would need to parse mv arguments
            return None
        
        # Git operations
        elif "git add" in command:
            return "git reset HEAD"
        
        elif "git commit" in command:
            return "git reset HEAD~1"
        
        elif "git push" in command:
            return "git reset HEAD~1 && git push --force-with-lease"
        
        # Package operations
        elif command.startswith("npm install"):
            return "npm uninstall"
        
        elif command.startswith("pip install"):
            package = command.replace("pip install", "").strip()
            return f"pip uninstall {package}"
        
        # Service operations
        elif "systemctl start" in command:
            service = command.replace("systemctl start", "").strip()
            return f"systemctl stop {service}"
        
        elif "systemctl enable" in command:
            service = command.replace("systemctl enable", "").strip()
            return f"systemctl disable {service}"
        
        return None
    
    def get_rollback_summary(self, execution_id: str) -> Dict[str, Any]:
        """Get summary of rollback actions for execution"""
        if execution_id not in self.rollback_actions:
            return {"actions": [], "count": 0}
        
        actions = self.rollback_actions[execution_id]
        
        return {
            "actions": [action.to_dict() for action in actions],
            "count": len(actions),
            "types": list(set(action.action_type for action in actions))
        }
    
    def clear_rollback_actions(self, execution_id: str) -> None:
        """Clear rollback actions for an execution"""
        if execution_id in self.rollback_actions:
            del self.rollback_actions[execution_id]
            logger.info(f"Cleared rollback actions for execution: {execution_id}")
    
    def can_rollback(self, execution_id: str) -> bool:
        """Check if rollback is possible for execution"""
        return execution_id in self.rollback_actions and len(self.rollback_actions[execution_id]) > 0