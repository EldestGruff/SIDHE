import pytest
import json
import yaml
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

# Import the classes we're testing
from .plugin_interface import WorkflowGenerator, Workflow, WorkflowStep, WorkflowStatus
from .templates.library import TemplateLibrary, WorkflowTemplate, TemplateMatch
from .storage.redis_store import RedisWorkflowStore, WorkflowExecution
from .validator.schema import WorkflowValidator


class TestWorkflowGenerator:
    """Test the main WorkflowGenerator class"""
    
    def test_init_with_redis_connection(self):
        """Test initialization with successful Redis connection"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.return_value.ping.return_value = True
            
            generator = WorkflowGenerator("redis://localhost:6379")
            
            assert generator.redis is not None
            mock_redis.assert_called_once_with("redis://localhost:6379")
    
    def test_init_without_redis_connection(self):
        """Test initialization with failed Redis connection"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            generator = WorkflowGenerator("redis://localhost:6379")
            
            assert generator.redis is None
    
    def test_generate_from_text_basic(self):
        """Test basic workflow generation from text"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.return_value.ping.return_value = True
            
            generator = WorkflowGenerator()
            
            # Mock the natural language parser
            with patch.object(generator.nl_parser, 'parse') as mock_parse:
                mock_parse.return_value = {
                    "name": "test-workflow",
                    "version": "1.0",
                    "description": "Test workflow",
                    "inputs": [],
                    "steps": [
                        {
                            "id": "step1",
                            "type": "command",
                            "command": "echo 'hello'"
                        }
                    ]
                }
                
                # Mock template library
                with patch.object(generator.template_library, 'find_matches') as mock_find:
                    mock_find.return_value = []
                    
                    # Mock validator
                    with patch.object(generator.validator, 'validate') as mock_validate:
                        mock_validate.return_value = Mock(is_valid=True)
                        
                        workflow = generator.generate_from_text("Create a test workflow")
                        
                        assert workflow.name == "test-workflow"
                        assert workflow.version == "1.0"
                        assert len(workflow.steps) == 1
                        assert workflow.steps[0].command == "echo 'hello'"
    
    def test_generate_from_text_with_template(self):
        """Test workflow generation with template matching"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.return_value.ping.return_value = True
            
            generator = WorkflowGenerator()
            
            # Mock the natural language parser
            with patch.object(generator.nl_parser, 'parse') as mock_parse:
                mock_parse.return_value = {
                    "name": "python-project",
                    "version": "1.0",
                    "description": "Python project setup",
                    "inputs": [],
                    "steps": []
                }
                
                # Mock template library with match
                template = WorkflowTemplate(
                    name="python-setup",
                    description="Python project template",
                    keywords=["python", "setup"],
                    workflow_dict={
                        "name": "python-setup",
                        "version": "1.0",
                        "description": "Python setup template",
                        "inputs": [{"name": "project_name", "type": "string", "required": True}],
                        "steps": [{"id": "create_dir", "type": "command", "command": "mkdir ${project_name}"}]
                    }
                )
                
                template_match = TemplateMatch(template, 0.8, ["python", "setup"])
                
                with patch.object(generator.template_library, 'find_matches') as mock_find:
                    mock_find.return_value = [template_match]
                    
                    with patch.object(generator.template_library, 'apply_template') as mock_apply:
                        mock_apply.return_value = {
                            "name": "python-project",
                            "version": "1.0",
                            "description": "Python project setup",
                            "inputs": [{"name": "project_name", "type": "string", "required": True}],
                            "steps": [{"id": "create_dir", "type": "command", "command": "mkdir ${project_name}"}]
                        }
                        
                        # Mock validator
                        with patch.object(generator.validator, 'validate') as mock_validate:
                            mock_validate.return_value = Mock(is_valid=True)
                            
                            workflow = generator.generate_from_text("Create a Python project")
                            
                            assert workflow.name == "python-project"
                            assert len(workflow.inputs) == 1
                            assert workflow.inputs[0]["name"] == "project_name"
                            assert len(workflow.steps) == 1
    
    def test_generate_from_text_invalid_workflow(self):
        """Test workflow generation with validation failure"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.return_value.ping.return_value = True
            
            generator = WorkflowGenerator()
            
            # Mock the natural language parser
            with patch.object(generator.nl_parser, 'parse') as mock_parse:
                mock_parse.return_value = {
                    "name": "",  # Invalid empty name
                    "version": "1.0",
                    "description": "Test workflow",
                    "inputs": [],
                    "steps": []
                }
                
                # Mock template library
                with patch.object(generator.template_library, 'find_matches') as mock_find:
                    mock_find.return_value = []
                    
                    # Mock validator with failure
                    with patch.object(generator.validator, 'validate') as mock_validate:
                        mock_validate.return_value = Mock(
                            is_valid=False,
                            errors=["Name cannot be empty"]
                        )
                        
                        with pytest.raises(ValueError, match="Invalid workflow"):
                            generator.generate_from_text("Create invalid workflow")
    
    def test_save_workflow_success(self):
        """Test successful workflow saving"""
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            mock_redis_client.set.return_value = True
            
            generator = WorkflowGenerator()
            
            workflow = Workflow(
                name="test-workflow",
                version="1.0",
                description="Test workflow",
                inputs=[],
                steps=[]
            )
            
            workflow_id = generator.save_workflow(workflow)
            
            assert workflow_id == "workflow:test-workflow:1.0"
            mock_redis_client.set.assert_called_once()
    
    def test_save_workflow_no_redis(self):
        """Test workflow saving without Redis connection"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            generator = WorkflowGenerator()
            
            workflow = Workflow(
                name="test-workflow",
                version="1.0",
                description="Test workflow",
                inputs=[],
                steps=[]
            )
            
            workflow_id = generator.save_workflow(workflow)
            
            assert workflow_id is None


class TestTemplateLibrary:
    """Test the TemplateLibrary class"""
    
    def test_init_loads_default_templates(self):
        """Test that initialization loads default templates"""
        library = TemplateLibrary()
        
        # Should have built-in templates
        assert len(library.templates) > 0
        assert "python-project-setup" in library.templates
        assert "react-app-enchant" in library.templates
        assert "git-workflow" in library.templates
        assert "docker-build-enchant" in library.templates
    
    def test_find_matches_exact_keywords(self):
        """Test finding templates with exact keyword matches"""
        library = TemplateLibrary()
        
        matches = library.find_matches("Create a Python project with setup")
        
        assert len(matches) > 0
        # Should find python-project-setup template
        python_matches = [m for m in matches if m.template.name == "python-project-setup"]
        assert len(python_matches) > 0
        assert python_matches[0].confidence > 0.1
    
    def test_find_matches_partial_keywords(self):
        """Test finding templates with partial keyword matches"""
        library = TemplateLibrary()
        
        matches = library.find_matches("Deploy my React application")
        
        assert len(matches) > 0
        # Should find react-app-enchant template
        react_matches = [m for m in matches if m.template.name == "react-app-enchant"]
        assert len(react_matches) > 0
    
    def test_find_matches_no_match(self):
        """Test finding templates with no matches"""
        library = TemplateLibrary()
        
        matches = library.find_matches("Something completely unrelated")
        
        # Should return empty list or very low confidence matches
        assert len(matches) == 0 or all(m.confidence < 0.1 for m in matches)
    
    def test_apply_template_basic(self):
        """Test basic template application"""
        library = TemplateLibrary()
        
        # Get a template
        template = library.get_template("python-project-setup")
        template_match = TemplateMatch(template, 0.8, ["python", "setup"])
        
        # Create a basic workflow dict
        workflow_dict = {
            "name": "my-project",
            "version": "1.0",
            "description": "My Python project",
            "inputs": [],
            "steps": []
        }
        
        # Apply template
        merged = library.apply_template(template_match, workflow_dict)
        
        assert merged["name"] == "my-project"  # Should keep original name
        assert len(merged["inputs"]) > 0  # Should have template inputs
        assert len(merged["steps"]) > 0  # Should have template steps
    
    def test_add_template(self):
        """Test adding a new template"""
        library = TemplateLibrary()
        
        new_template = WorkflowTemplate(
            name="test-template",
            description="Test template",
            keywords=["test"],
            workflow_dict={
                "name": "test-workflow",
                "version": "1.0",
                "description": "Test workflow",
                "inputs": [],
                "steps": []
            }
        )
        
        success = library.add_template(new_template)
        
        assert success is True
        assert "test-template" in library.templates
        assert library.get_template("test-template") == new_template
    
    def test_remove_template(self):
        """Test removing a template"""
        library = TemplateLibrary()
        
        # Add a template first
        new_template = WorkflowTemplate(
            name="temp-template",
            description="Temporary template",
            keywords=["temp"],
            workflow_dict={}
        )
        library.add_template(new_template)
        
        # Remove it
        success = library.remove_template("temp-template")
        
        assert success is True
        assert "temp-template" not in library.templates
    
    def test_update_template_rating(self):
        """Test updating template rating"""
        library = TemplateLibrary()
        
        # Update rating for existing template
        success = library.update_template_rating("python-project-setup", 4.5)
        
        assert success is True
        template = library.get_template("python-project-setup")
        assert template.rating == 4.5
    
    def test_update_template_rating_nonexistent(self):
        """Test updating rating for nonexistent template"""
        library = TemplateLibrary()
        
        success = library.update_template_rating("nonexistent-template", 4.5)
        
        assert success is False


class TestRedisWorkflowStore:
    """Test the RedisWorkflowStore class"""
    
    def test_init_with_connection(self):
        """Test initialization with successful Redis connection"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.return_value.ping.return_value = True
            
            store = RedisWorkflowStore()
            
            assert store.is_connected() is True
            mock_redis.assert_called_once()
    
    def test_init_without_connection(self):
        """Test initialization with failed Redis connection"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            store = RedisWorkflowStore()
            
            assert store.is_connected() is False
    
    def test_save_workflow_success(self):
        """Test successful workflow saving"""
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            mock_redis_client.set.return_value = True
            
            store = RedisWorkflowStore()
            
            workflow = Workflow(
                name="test-workflow",
                version="1.0",
                description="Test workflow",
                inputs=[],
                steps=[]
            )
            
            success = store.save_workflow(workflow)
            
            assert success is True
            mock_redis_client.set.assert_called_once()
            mock_redis_client.sadd.assert_called_once()
            mock_redis_client.expire.assert_called_once()
    
    def test_save_workflow_no_connection(self):
        """Test workflow saving without Redis connection"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            store = RedisWorkflowStore()
            
            workflow = Workflow(
                name="test-workflow",
                version="1.0",
                description="Test workflow",
                inputs=[],
                steps=[]
            )
            
            success = store.save_workflow(workflow)
            
            assert success is False
    
    def test_load_workflow_success(self):
        """Test successful workflow loading"""
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            
            # Mock workflow data
            workflow_data = {
                "workflow": {
                    "name": "test-workflow",
                    "version": "1.0",
                    "description": "Test workflow",
                    "inputs": [],
                    "steps": []
                },
                "created_at": "2023-01-01T00:00:00",
                "status": "draft"
            }
            
            mock_redis_client.get.return_value = json.dumps(workflow_data)
            
            store = RedisWorkflowStore()
            workflow = store.load_workflow("test-workflow", "1.0")
            
            assert workflow is not None
            assert workflow.name == "test-workflow"
            assert workflow.version == "1.0"
    
    def test_load_workflow_not_found(self):
        """Test loading nonexistent workflow"""
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            mock_redis_client.get.return_value = None
            
            store = RedisWorkflowStore()
            workflow = store.load_workflow("nonexistent-workflow", "1.0")
            
            assert workflow is None
    
    def test_list_workflows(self):
        """Test listing workflows"""
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            
            # Mock workflow keys
            workflow_keys = ["sidhe:workflow:test1:1.0", "sidhe:workflow:test2:1.0"]
            mock_redis_client.smembers.return_value = workflow_keys
            
            # Mock workflow data
            workflow_data = {
                "workflow": {
                    "name": "test1",
                    "version": "1.0",
                    "description": "Test workflow 1"
                },
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "status": "draft"
            }
            
            mock_redis_client.get.return_value = json.dumps(workflow_data)
            
            store = RedisWorkflowStore()
            workflows = store.list_workflows()
            
            assert len(workflows) == 2
            assert workflows[0]["name"] == "test1"
    
    def test_save_execution_success(self):
        """Test successful execution saving"""
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            
            store = RedisWorkflowStore()
            
            execution = WorkflowExecution(
                execution_id="exec-123",
                workflow_name="test-workflow",
                workflow_version="1.0",
                status=WorkflowStatus.RUNNING,
                inputs={"param1": "value1"},
                outputs={},
                step_results={},
                started_at=datetime.utcnow()
            )
            
            success = store.save_execution(execution)
            
            assert success is True
            mock_redis_client.set.assert_called_once()
            mock_redis_client.sadd.assert_called()
            mock_redis_client.expire.assert_called_once()
    
    def test_load_execution_success(self):
        """Test successful execution loading"""
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            
            # Mock execution data
            execution_data = {
                "execution_id": "exec-123",
                "workflow_name": "test-workflow",
                "workflow_version": "1.0",
                "status": "running",
                "inputs": {"param1": "value1"},
                "outputs": {},
                "step_results": {},
                "started_at": "2023-01-01T00:00:00.000000",
                "completed_at": None,
                "error": None
            }
            
            mock_redis_client.get.return_value = json.dumps(execution_data)
            
            store = RedisWorkflowStore()
            execution = store.load_execution("exec-123")
            
            assert execution is not None
            assert execution.execution_id == "exec-123"
            assert execution.workflow_name == "test-workflow"
            assert execution.status == WorkflowStatus.RUNNING
    
    def test_update_execution_status(self):
        """Test updating execution status"""
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            
            # Mock existing execution data
            execution_data = {
                "execution_id": "exec-123",
                "workflow_name": "test-workflow",
                "workflow_version": "1.0",
                "status": "running",
                "inputs": {},
                "outputs": {},
                "step_results": {},
                "started_at": "2023-01-01T00:00:00.000000",
                "completed_at": None,
                "error": None
            }
            
            mock_redis_client.get.return_value = json.dumps(execution_data)
            
            store = RedisWorkflowStore()
            success = store.update_execution_status(
                "exec-123",
                WorkflowStatus.COMPLETED,
                {"result": "success"}
            )
            
            assert success is True
            mock_redis_client.set.assert_called()
    
    def test_get_storage_stats(self):
        """Test getting storage statistics"""
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            
            # Mock Redis info
            mock_redis_client.info.side_effect = lambda section: {
                "memory": {"used_memory_human": "1.2M"},
                "clients": {"connected_clients": 5}
            }.get(section, {})
            
            mock_redis_client.scard.return_value = 10
            mock_redis_client.smembers.return_value = ["key1", "key2"]
            mock_redis_client.get.return_value = json.dumps({
                "workflow": {"name": "test"},
                "status": "draft"
            })
            
            store = RedisWorkflowStore()
            stats = store.get_storage_stats()
            
            assert "total_workflows" in stats
            assert "total_executions" in stats
            assert "redis_memory_usage" in stats
            assert "redis_connected_clients" in stats
    
    def test_cleanup_expired_data(self):
        """Test cleaning up expired data"""
        with patch('redis.from_url') as mock_redis:
            mock_redis_client = Mock()
            mock_redis.return_value = mock_redis_client
            mock_redis_client.ping.return_value = True
            
            # Mock workflow and execution keys
            mock_redis_client.smembers.side_effect = [
                ["sidhe:workflow:test1:1.0", "sidhe:workflow:test2:1.0"],  # workflows
                ["sidhe:execution:exec1", "sidhe:execution:exec2"]  # executions
            ]
            
            # Mock exists - one key exists, one doesn't
            mock_redis_client.exists.side_effect = [True, False, True, False]
            
            store = RedisWorkflowStore()
            stats = store.cleanup_expired_data()
            
            assert stats["workflows"] == 1
            assert stats["executions"] == 1
            assert mock_redis_client.srem.call_count == 2


class TestWorkflowValidator:
    """Test the WorkflowValidator class"""
    
    def test_validate_valid_workflow(self):
        """Test validating a valid workflow"""
        from .validator.schema import WorkflowValidator
        
        validator = WorkflowValidator()
        
        workflow = Workflow(
            name="test-workflow",
            version="1.0",
            description="Test workflow",
            inputs=[],
            steps=[
                WorkflowStep(
                    id="step1",
                    type="command",
                    command="echo 'hello'"
                )
            ]
        )
        
        # Mock the safety checker
        with patch.object(validator.safety_checker, 'check') as mock_check:
            mock_check.return_value = Mock(
                is_safe=True,
                violations=[],
                warnings=[]
            )
            
            result = validator.validate(workflow)
            
            assert result.is_valid is True
            assert len(result.errors) == 0
    
    def test_validate_invalid_workflow_empty_name(self):
        """Test validating workflow with empty name"""
        from .validator.schema import WorkflowValidator
        
        validator = WorkflowValidator()
        
        workflow = Workflow(
            name="",  # Empty name
            version="1.0",
            description="Test workflow",
            inputs=[],
            steps=[]
        )
        
        # Mock the safety checker
        with patch.object(validator.safety_checker, 'check') as mock_check:
            mock_check.return_value = Mock(
                is_safe=True,
                violations=[],
                warnings=[]
            )
            
            result = validator.validate(workflow)
            
            assert result.is_valid is False
            assert len(result.errors) > 0
    
    def test_validate_unsafe_workflow(self):
        """Test validating workflow with safety violations"""
        from .validator.schema import WorkflowValidator
        
        validator = WorkflowValidator()
        
        workflow = Workflow(
            name="test-workflow",
            version="1.0",
            description="Test workflow",
            inputs=[],
            steps=[
                WorkflowStep(
                    id="step1",
                    type="command",
                    command="rm -rf /"  # Dangerous command
                )
            ]
        )
        
        # Mock the safety checker to report violation
        with patch.object(validator.safety_checker, 'check') as mock_check:
            mock_check.return_value = Mock(
                is_safe=False,
                violations=["Dangerous command detected: rm -rf /"],
                warnings=[]
            )
            
            result = validator.validate(workflow)
            
            assert result.is_valid is False
            assert len(result.errors) > 0
            assert "Dangerous command detected" in result.errors[0]


class TestWorkflowStep:
    """Test the WorkflowStep dataclass"""
    
    def test_to_dict(self):
        """Test converting WorkflowStep to dictionary"""
        step = WorkflowStep(
            id="test-step",
            type="command",
            description="Test step",
            command="echo 'test'",
            timeout=60
        )
        
        step_dict = step.to_dict()
        
        assert step_dict["id"] == "test-step"
        assert step_dict["type"] == "command"
        assert step_dict["description"] == "Test step"
        assert step_dict["command"] == "echo 'test'"
        assert step_dict["timeout"] == 60


class TestWorkflow:
    """Test the Workflow dataclass"""
    
    def test_to_dict(self):
        """Test converting Workflow to dictionary"""
        workflow = Workflow(
            name="test-workflow",
            version="1.0",
            description="Test workflow",
            inputs=[{"name": "param1", "type": "string"}],
            steps=[
                WorkflowStep(
                    id="step1",
                    type="command",
                    command="echo 'test'"
                )
            ]
        )
        
        workflow_dict = workflow.to_dict()
        
        assert workflow_dict["name"] == "test-workflow"
        assert workflow_dict["version"] == "1.0"
        assert workflow_dict["description"] == "Test workflow"
        assert len(workflow_dict["inputs"]) == 1
        assert len(workflow_dict["steps"]) == 1
        assert workflow_dict["steps"][0]["id"] == "step1"


class TestWorkflowExecution:
    """Test the WorkflowExecution dataclass"""
    
    def test_to_dict(self):
        """Test converting WorkflowExecution to dictionary"""
        execution = WorkflowExecution(
            execution_id="exec-123",
            workflow_name="test-workflow",
            workflow_version="1.0",
            status=WorkflowStatus.COMPLETED,
            inputs={"param1": "value1"},
            outputs={"result": "success"},
            step_results={"step1": {"success": True}},
            started_at=datetime(2023, 1, 1, 10, 0, 0),
            completed_at=datetime(2023, 1, 1, 10, 5, 0)
        )
        
        execution_dict = execution.to_dict()
        
        assert execution_dict["execution_id"] == "exec-123"
        assert execution_dict["workflow_name"] == "test-workflow"
        assert execution_dict["workflow_version"] == "1.0"
        assert execution_dict["status"] == "completed"
        assert execution_dict["inputs"]["param1"] == "value1"
        assert execution_dict["outputs"]["result"] == "success"
        assert execution_dict["step_results"]["step1"]["success"] is True
        assert execution_dict["started_at"] == "2023-01-01T10:00:00"
        assert execution_dict["completed_at"] == "2023-01-01T10:05:00"


# Integration Tests
class TestIntegration:
    """Integration tests for the workflow generator system"""
    
    def test_end_to_end_workflow_generation(self):
        """Test complete workflow generation pipeline"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.return_value.ping.return_value = True
            mock_redis.return_value.set.return_value = True
            
            generator = WorkflowGenerator()
            
            # Mock natural language parser
            with patch.object(generator.nl_parser, 'parse') as mock_parse:
                mock_parse.return_value = {
                    "name": "python-project",
                    "version": "1.0",
                    "description": "Create a Python project",
                    "inputs": [
                        {"name": "project_name", "type": "string", "required": True}
                    ],
                    "steps": [
                        {
                            "id": "create_structure",
                            "type": "command",
                            "command": "mkdir -p ${project_name}/{src,tests}"
                        },
                        {
                            "id": "create_venv",
                            "type": "command",
                            "command": "python -m venv ${project_name}/venv"
                        }
                    ]
                }
                
                # Mock validator
                with patch.object(generator.validator, 'validate') as mock_validate:
                    mock_validate.return_value = Mock(is_valid=True)
                    
                    # Generate workflow
                    workflow = generator.generate_from_text("Create a Python project with virtual environment")
                    
                    # Verify workflow structure
                    assert workflow.name == "python-project"
                    assert len(workflow.steps) == 2
                    assert workflow.steps[0].id == "create_structure"
                    assert workflow.steps[1].id == "create_venv"
                    
                    # Save workflow
                    workflow_id = generator.save_workflow(workflow)
                    assert workflow_id is not None
    
    def test_workflow_execution_flow(self):
        """Test workflow execution flow"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.return_value.ping.return_value = True
            
            generator = WorkflowGenerator()
            
            # Create a simple workflow
            workflow = Workflow(
                name="test-execution",
                version="1.0",
                description="Test execution workflow",
                inputs=[],
                steps=[
                    WorkflowStep(
                        id="echo_step",
                        type="command",
                        command="echo 'Hello, World!'"
                    )
                ]
            )
            
            # Mock the executor
            with patch.object(generator.executor, 'execute') as mock_execute:
                mock_execute.return_value = {
                    "execution_id": "exec-123",
                    "status": WorkflowStatus.COMPLETED,
                    "outputs": {"message": "Hello, World!"},
                    "step_results": {
                        "echo_step": {"success": True, "output": "Hello, World!"}
                    }
                }
                
                # Execute workflow
                result = generator.execute_workflow(workflow, {}, dry_run=False)
                
                assert result["status"] == WorkflowStatus.COMPLETED
                assert result["outputs"]["message"] == "Hello, World!"
                assert result["step_results"]["echo_step"]["success"] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])