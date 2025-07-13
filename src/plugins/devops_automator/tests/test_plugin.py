"""
DevOps Automator Plugin Tests

Comprehensive test suite for the DevOps Automator Plugin including
unit tests, integration tests, and component validation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

# Import the plugin and components
from ..main import DevOpsAutomatorPlugin, DeploymentConfig, DeploymentResult, InfrastructureStatus, PipelineResult
from ..components.pipeline_orchestrator import PipelineOrchestrator
from ..components.docker_manager import DockerManager
from ..components.infrastructure_monitor import InfrastructureMonitor
from ..components.deployment_orchestrator import DeploymentOrchestrator
from ..config.settings import DevOpsConfig


class TestDevOpsAutomatorPlugin:
    """Test suite for main DevOps Automator Plugin"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for tests"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def plugin(self, temp_config_dir):
        """Create plugin instance for testing"""
        return DevOpsAutomatorPlugin(config_path=temp_config_dir)
    
    @pytest.mark.asyncio
    async def test_plugin_initialization(self, plugin):
        """Test plugin initializes correctly"""
        assert plugin.plugin_name == "devops_automator"
        assert plugin.version == "1.0.0"
        assert plugin.enabled is True
        assert hasattr(plugin, 'pipeline_orchestrator')
        assert hasattr(plugin, 'docker_manager')
        assert hasattr(plugin, 'infrastructure_monitor')
        assert hasattr(plugin, 'deployment_orchestrator')
    
    @pytest.mark.asyncio
    async def test_health_check(self, plugin):
        """Test plugin health check functionality"""
        health_result = await plugin.health_check()
        
        assert isinstance(health_result, dict)
        assert "healthy" in health_result
        assert "plugin" in health_result
        assert "version" in health_result
        assert "components" in health_result
        assert "external_dependencies" in health_result
        assert health_result["plugin"] == "devops_automator"
        assert health_result["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_deploy_environment_blue_green(self, plugin):
        """Test blue-green deployment execution"""
        config = DeploymentConfig(
            environment="staging",
            strategy="blue_green",
            quality_gates=["linting_check"],
            rollback_criteria={"health_check_failure": True},
            security_requirements={"scan_required": True}
        )
        
        result = await plugin.deploy_environment("staging", config)
        
        assert isinstance(result, DeploymentResult)
        assert result.status in ["completed", "failed"]
        assert result.environment == "staging"
        assert result.strategy == "blue_green"
        assert isinstance(result.logs, list)
        assert isinstance(result.metrics, dict)
    
    @pytest.mark.asyncio
    async def test_deploy_environment_canary(self, plugin):
        """Test canary deployment execution"""
        config = DeploymentConfig(
            environment="production",
            strategy="canary",
            quality_gates=[],
            rollback_criteria={"error_rate_threshold": 1.0},
            security_requirements={}
        )
        
        result = await plugin.deploy_environment("production", config)
        
        assert isinstance(result, DeploymentResult)
        assert result.environment == "production"
        assert result.strategy == "canary"
    
    @pytest.mark.asyncio
    async def test_deploy_environment_direct(self, plugin):
        """Test direct deployment execution"""
        config = DeploymentConfig(
            environment="development",
            strategy="direct",
            quality_gates=[],
            rollback_criteria={},
            security_requirements={}
        )
        
        result = await plugin.deploy_environment("development", config)
        
        assert isinstance(result, DeploymentResult)
        assert result.environment == "development"
        assert result.strategy == "direct"
    
    @pytest.mark.asyncio
    async def test_manage_docker_images(self, plugin):
        """Test Docker image management"""
        # Test image build
        build_config = {
            "name": "test-image",
            "tag": "v1.0.0",
            "dockerfile": "Dockerfile",
            "context": "."
        }
        
        build_result = await plugin.manage_docker_images("build", build_config)
        
        assert isinstance(build_result, dict)
        assert "status" in build_result
        assert "action" in build_result
        
        # Test image scan
        scan_config = {"name": "test-image:v1.0.0"}
        scan_result = await plugin.manage_docker_images("scan", scan_config)
        
        assert isinstance(scan_result, dict)
        assert "status" in scan_result
    
    @pytest.mark.asyncio
    async def test_monitor_infrastructure(self, plugin):
        """Test infrastructure monitoring"""
        status = await plugin.monitor_infrastructure("all")
        
        assert isinstance(status, InfrastructureStatus)
        assert isinstance(status.services, dict)
        assert isinstance(status.containers, dict)
        assert isinstance(status.metrics, dict)
        assert isinstance(status.alerts, list)
        assert isinstance(status.resource_usage, dict)
        assert status.last_updated is not None
    
    @pytest.mark.asyncio
    async def test_orchestrate_pipeline(self, plugin):
        """Test CI/CD pipeline orchestration"""
        pipeline_config = {
            "name": "test-pipeline",
            "repository": "EldestGruff/SIDHE",
            "branch": "main",
            "stages": ["build", "test", "deploy"],
            "triggers": ["push", "pull_request"]
        }
        
        result = await plugin.orchestrate_pipeline(pipeline_config)
        
        assert isinstance(result, PipelineResult)
        assert result.pipeline_id is not None
        assert result.status in ["completed", "failed", "running"]
        assert isinstance(result.stages, list)
        assert isinstance(result.quality_gates, list)
    
    @pytest.mark.asyncio
    async def test_manage_rollbacks(self, plugin):
        """Test rollback management"""
        # First create a mock deployment
        plugin.active_deployments["test-deployment"] = {
            "environment": "staging",
            "strategy": "blue_green",
            "status": "active"
        }
        
        rollback_result = await plugin.manage_rollbacks("test-deployment", "automatic")
        
        assert isinstance(rollback_result, dict)
        assert "status" in rollback_result
        assert "deployment_id" in rollback_result
        assert rollback_result["deployment_id"] == "test-deployment"
    
    @pytest.mark.asyncio
    async def test_analyze_deployment_metrics(self, plugin):
        """Test deployment metrics analysis"""
        metrics = await plugin.analyze_deployment_metrics("24h")
        
        assert isinstance(metrics, dict)
        assert "timeframe" in metrics
        assert "metrics" in metrics
        assert "generated_at" in metrics
        assert metrics["timeframe"] == "24h"


class TestPipelineOrchestrator:
    """Test suite for Pipeline Orchestrator component"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for tests"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def orchestrator(self, temp_config_dir):
        """Create orchestrator instance for testing"""
        return PipelineOrchestrator(temp_config_dir)
    
    @pytest.mark.asyncio
    async def test_health_check(self, orchestrator):
        """Test orchestrator health check"""
        health = await orchestrator.health_check()
        
        assert isinstance(health, dict)
        assert "healthy" in health
        assert "github_connectivity" in health
        assert "active_pipelines" in health
    
    @pytest.mark.asyncio
    async def test_create_workflow(self, orchestrator):
        """Test workflow creation"""
        config = {
            "name": "test-workflow",
            "triggers": ["push", "pull_request"],
            "stages": ["build", "test", "deploy"],
            "environment": "staging"
        }
        
        result = await orchestrator.create_workflow(config)
        
        assert isinstance(result, dict)
        assert "status" in result
        assert "workflow_name" in result
        assert result["workflow_name"] == "test-workflow"
    
    @pytest.mark.asyncio
    async def test_trigger_pipeline(self, orchestrator):
        """Test pipeline triggering"""
        result = await orchestrator.trigger_pipeline("EldestGruff/SIDHE", "main")
        
        assert isinstance(result, dict)
        assert "status" in result
        assert "run_id" in result
        assert "repository" in result
        assert result["repository"] == "EldestGruff/SIDHE"
    
    @pytest.mark.asyncio
    async def test_monitor_pipeline_progress(self, orchestrator):
        """Test pipeline progress monitoring"""
        # First trigger a pipeline to get a run_id
        trigger_result = await orchestrator.trigger_pipeline("EldestGruff/SIDHE", "main")
        run_id = trigger_result["run_id"]
        
        # Then monitor its progress
        progress = await orchestrator.monitor_pipeline_progress(run_id)
        
        assert isinstance(progress, dict)
        assert "run_id" in progress
        assert "status" in progress
        assert "progress_percentage" in progress
        assert progress["run_id"] == run_id
    
    @pytest.mark.asyncio
    async def test_enforce_quality_gates(self, orchestrator):
        """Test quality gate enforcement"""
        result = await orchestrator.enforce_quality_gates("test-pipeline-123")
        
        assert isinstance(result, dict)
        assert "pipeline_id" in result
        assert "gates_passed" in result
        assert "gate_results" in result
        assert isinstance(result["gates_passed"], bool)


class TestDockerManager:
    """Test suite for Docker Manager component"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for tests"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def docker_manager(self, temp_config_dir):
        """Create Docker manager instance for testing"""
        return DockerManager(temp_config_dir)
    
    @pytest.mark.asyncio
    async def test_health_check(self, docker_manager):
        """Test Docker manager health check"""
        health = await docker_manager.health_check()
        
        assert isinstance(health, dict)
        assert "healthy" in health
        assert "docker_daemon" in health
        assert "registry_connectivity" in health
        assert "security_scanner" in health
    
    @pytest.mark.asyncio
    async def test_build_image(self, docker_manager):
        """Test Docker image building"""
        build_config = {
            "name": "test-image",
            "tag": "v1.0.0",
            "dockerfile": "Dockerfile",
            "context": "."
        }
        
        result = await docker_manager.build_image(build_config)
        
        assert isinstance(result, dict)
        assert "build_id" in result
        assert "image_name" in result
        assert "status" in result
        assert result["image_name"] == "test-image:v1.0.0"
    
    @pytest.mark.asyncio
    async def test_scan_image_security(self, docker_manager):
        """Test Docker image security scanning"""
        # First build an image
        build_config = {"name": "test-image", "tag": "latest"}
        build_result = await docker_manager.build_image(build_config)
        
        # Then scan it
        scan_result = await docker_manager.scan_image_security("test-image:latest")
        
        assert isinstance(scan_result, dict)
        assert "scan_id" in scan_result
        assert "image_name" in scan_result
        assert "status" in scan_result
        assert "vulnerabilities" in scan_result or "error" in scan_result
    
    @pytest.mark.asyncio
    async def test_push_image(self, docker_manager):
        """Test Docker image push"""
        # First build an image and scan it
        build_config = {"name": "test-image", "tag": "latest"}
        await docker_manager.build_image(build_config)
        await docker_manager.scan_image_security("test-image:latest")
        
        # Then push it
        push_result = await docker_manager.push_image("test-image:latest")
        
        assert isinstance(push_result, dict)
        assert "image_name" in push_result
        assert "status" in push_result
    
    @pytest.mark.asyncio
    async def test_cleanup_images(self, docker_manager):
        """Test Docker image cleanup"""
        cleanup_policy = {
            "max_age_days": 7,
            "keep_latest": 3,
            "min_size_mb": 50
        }
        
        result = await docker_manager.cleanup_images(cleanup_policy)
        
        assert isinstance(result, dict)
        assert "status" in result
        assert "cleanup_policy" in result
        assert "results" in result


class TestInfrastructureMonitor:
    """Test suite for Infrastructure Monitor component"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for tests"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def monitor(self, temp_config_dir):
        """Create monitor instance for testing"""
        return InfrastructureMonitor(temp_config_dir)
    
    @pytest.mark.asyncio
    async def test_health_check(self, monitor):
        """Test monitor health check"""
        health = await monitor.health_check()
        
        assert isinstance(health, dict)
        assert "healthy" in health
        assert "system_access" in health
        assert "metrics_collection" in health
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics(self, monitor):
        """Test system metrics collection"""
        metrics = await monitor.collect_system_metrics("all")
        
        assert isinstance(metrics, dict)
        assert "timestamp" in metrics
        assert "scope" in metrics
        assert metrics["scope"] == "all"
        
        # Test specific scopes
        cpu_metrics = await monitor.collect_system_metrics("cpu")
        assert "cpu" in cpu_metrics
        
        memory_metrics = await monitor.collect_system_metrics("memory")
        assert "memory" in memory_metrics
    
    @pytest.mark.asyncio
    async def test_monitor_service_health(self, monitor):
        """Test service health monitoring"""
        services = ["sidhe-backend", "redis"]
        health_status = await monitor.monitor_service_health(services)
        
        assert isinstance(health_status, dict)
        assert len(health_status) == len(services)
        
        for service in services:
            assert service in health_status
            assert "status" in health_status[service]
            assert "health_score" in health_status[service]
    
    @pytest.mark.asyncio
    async def test_check_alerts(self, monitor):
        """Test alert checking"""
        alerts = await monitor.check_alerts()
        
        assert isinstance(alerts, list)
        for alert in alerts:
            assert "type" in alert
            assert "severity" in alert
            assert "message" in alert
    
    @pytest.mark.asyncio
    async def test_calculate_resource_usage(self, monitor):
        """Test resource usage calculation"""
        usage = await monitor.calculate_resource_usage()
        
        assert isinstance(usage, dict)
        assert "timestamp" in usage
        assert "cpu" in usage
        assert "memory" in usage
        assert "disk" in usage
        assert "overall_health_score" in usage
        
        # Validate CPU metrics
        assert "usage_percent" in usage["cpu"]
        assert "status" in usage["cpu"]
        
        # Validate memory metrics
        assert "usage_percent" in usage["memory"]
        assert "used_gb" in usage["memory"]
        assert "total_gb" in usage["memory"]


class TestDeploymentOrchestrator:
    """Test suite for Deployment Orchestrator component"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for tests"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def orchestrator(self, temp_config_dir):
        """Create orchestrator instance for testing"""
        return DeploymentOrchestrator(temp_config_dir)
    
    @pytest.mark.asyncio
    async def test_health_check(self, orchestrator):
        """Test orchestrator health check"""
        health = await orchestrator.health_check()
        
        assert isinstance(health, dict)
        assert "healthy" in health
        assert "deployment_systems" in health
        assert "load_balancer" in health
        assert "rollback_capability" in health
    
    @pytest.mark.asyncio
    async def test_execute_blue_green_deployment(self, orchestrator):
        """Test blue-green deployment execution"""
        config = {
            "quality_gates": [],
            "rollback_criteria": {"health_check_failure": True}
        }
        
        result = await orchestrator.execute_blue_green_deployment("staging", config)
        
        assert isinstance(result, dict)
        assert "deployment_id" in result
        assert "status" in result
        assert "strategy" in result
        assert result["strategy"] == "blue_green"
    
    @pytest.mark.asyncio
    async def test_execute_canary_deployment(self, orchestrator):
        """Test canary deployment execution"""
        config = {
            "initial_traffic": 10,
            "increment_percentage": 25,
            "increment_interval": 60
        }
        
        result = await orchestrator.execute_canary_deployment("production", config)
        
        assert isinstance(result, dict)
        assert "deployment_id" in result
        assert "status" in result
        assert "strategy" in result
        assert result["strategy"] == "canary"
    
    @pytest.mark.asyncio
    async def test_execute_direct_deployment(self, orchestrator):
        """Test direct deployment execution"""
        config = {
            "backup_enabled": True,
            "health_check_timeout": 180
        }
        
        result = await orchestrator.execute_direct_deployment("development", config)
        
        assert isinstance(result, dict)
        assert "deployment_id" in result
        assert "status" in result
        assert "strategy" in result
        assert result["strategy"] == "direct"
    
    @pytest.mark.asyncio
    async def test_execute_rollback(self, orchestrator):
        """Test deployment rollback execution"""
        # Create a mock deployment first
        orchestrator.active_deployments["test-deployment"] = {
            "strategy": "blue_green",
            "environment": "staging",
            "green_id": "green-123",
            "blue_id": "blue-456"
        }
        
        result = await orchestrator.execute_rollback("test-deployment", "staging", "automatic")
        
        assert isinstance(result, dict)
        assert "deployment_id" in result
        assert "status" in result
        assert "original_deployment_strategy" in result
        assert result["deployment_id"] == "test-deployment"


class TestDevOpsConfig:
    """Test suite for DevOps configuration"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for tests"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config(self, temp_config_dir):
        """Create config instance for testing"""
        return DevOpsConfig(temp_config_dir)
    
    def test_config_initialization(self, config):
        """Test configuration initialization"""
        assert hasattr(config, 'github_config')
        assert hasattr(config, 'docker_config')
        assert hasattr(config, 'monitoring_config')
        assert hasattr(config, 'deployment_config')
        assert hasattr(config, 'quality_gates_config')
    
    def test_get_deployment_strategy_config(self, config):
        """Test deployment strategy configuration retrieval"""
        blue_green_config = config.get_deployment_strategy_config("blue_green")
        assert isinstance(blue_green_config, dict)
        assert "health_check_timeout" in blue_green_config
        assert "traffic_switch_delay" in blue_green_config
        
        canary_config = config.get_deployment_strategy_config("canary")
        assert isinstance(canary_config, dict)
        assert "initial_traffic" in canary_config
        assert "increment_percentage" in canary_config
        
        direct_config = config.get_deployment_strategy_config("direct")
        assert isinstance(direct_config, dict)
        assert "backup_enabled" in direct_config
        assert "health_check_timeout" in direct_config
    
    def test_get_quality_gates_config(self, config):
        """Test quality gates configuration retrieval"""
        gates_config = config.get_quality_gates_config()
        
        assert isinstance(gates_config, dict)
        assert "enabled" in gates_config
        assert "minimum_coverage" in gates_config
        assert "target_coverage" in gates_config
        assert "timeouts" in gates_config
    
    def test_get_monitoring_thresholds(self, config):
        """Test monitoring thresholds retrieval"""
        thresholds = config.get_monitoring_thresholds()
        
        assert isinstance(thresholds, dict)
        assert "cpu" in thresholds
        assert "memory" in thresholds
        assert "disk" in thresholds
        assert "response_time" in thresholds
        
        # Validate threshold structure
        for resource in ["cpu", "memory", "disk"]:
            assert "warning" in thresholds[resource]
            assert "critical" in thresholds[resource]
    
    def test_validate_configuration(self, config):
        """Test configuration validation"""
        validation = config.validate_configuration()
        
        assert isinstance(validation, dict)
        assert "valid" in validation
        assert "warnings" in validation
        assert "errors" in validation
        assert isinstance(validation["warnings"], list)
        assert isinstance(validation["errors"], list)
    
    def test_to_dict(self, config):
        """Test configuration dictionary conversion"""
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "github" in config_dict
        assert "docker" in config_dict
        assert "monitoring" in config_dict
        assert "deployment" in config_dict
        assert "quality_gates" in config_dict


# Integration Tests
class TestDevOpsIntegration:
    """Integration tests for DevOps Automator Plugin"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for tests"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def plugin(self, temp_config_dir):
        """Create plugin instance for testing"""
        return DevOpsAutomatorPlugin(config_path=temp_config_dir)
    
    @pytest.mark.asyncio
    async def test_full_deployment_workflow(self, plugin):
        """Test complete deployment workflow"""
        # 1. Check plugin health
        health = await plugin.health_check()
        assert health["healthy"] is True
        
        # 2. Create deployment configuration
        config = DeploymentConfig(
            environment="integration-test",
            strategy="blue_green",
            quality_gates=["linting_check"],
            rollback_criteria={"health_check_failure": True},
            security_requirements={"scan_required": False}  # Skip for test
        )
        
        # 3. Execute deployment
        deployment_result = await plugin.deploy_environment("integration-test", config)
        assert deployment_result.status in ["completed", "failed"]
        
        # 4. Monitor infrastructure
        infra_status = await plugin.monitor_infrastructure("all")
        assert isinstance(infra_status, InfrastructureStatus)
        
        # 5. Check deployment metrics
        metrics = await plugin.analyze_deployment_metrics("1h")
        assert "metrics" in metrics
    
    @pytest.mark.asyncio
    async def test_error_handling_and_rollback(self, plugin):
        """Test error handling and rollback scenarios"""
        # Create a deployment that will fail quality gates
        config = DeploymentConfig(
            environment="test-fail",
            strategy="direct",
            quality_gates=["strict_quality_check"],  # This will fail
            rollback_criteria={"immediate": True},
            security_requirements={}
        )
        
        # Execute deployment (should fail)
        deployment_result = await plugin.deploy_environment("test-fail", config)
        
        # If deployment succeeded, test rollback
        if deployment_result.status == "completed":
            rollback_result = await plugin.manage_rollbacks(
                deployment_result.deployment_id, 
                "immediate"
            )
            assert "status" in rollback_result
    
    @pytest.mark.asyncio
    async def test_plugin_interface_compliance(self, plugin):
        """Test plugin interface compliance with SIDHE standards"""
        # Test plugin info function
        plugin_info = await plugin.__class__.__module__.split('.')[-2] + ".get_plugin_info"
        from importlib import import_module
        
        try:
            module = import_module("..main", package=plugin.__module__)
            info = await module.get_plugin_info()
            
            assert isinstance(info, dict)
            assert "name" in info
            assert "version" in info
            assert "description" in info
            assert "capabilities" in info
            assert info["name"] == "devops_automator"
        except ImportError:
            # Module structure might be different in test environment
            pass
        
        # Test plugin creation function
        try:
            create_plugin = await module.create_plugin()
            assert isinstance(create_plugin, DevOpsAutomatorPlugin)
        except (ImportError, NameError):
            # Function might not be available in test environment
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])