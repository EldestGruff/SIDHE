"""
DevOps Automator Component Tests

Focused tests for individual components including utilities,
configuration management, and component interactions.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import shutil
import yaml
from datetime import datetime

# Import utilities and configuration
from ..utils.github_client import GitHubClient
from ..utils.docker_client import DockerClient
from ..utils.monitoring_client import MonitoringClient
from ..config.settings import DevOpsConfig, GitHubConfig, DockerConfig, MonitoringConfig


class TestGitHubClient:
    """Test suite for GitHub client utility"""
    
    @pytest.fixture
    def github_config(self):
        """Create GitHub configuration for testing"""
        return {
            "token": "test-token-123",
            "organization": "TestOrg",
            "repository": "TestRepo",
            "api_base_url": "https://api.github.com"
        }
    
    @pytest.fixture
    def github_client(self, github_config):
        """Create GitHub client instance for testing"""
        return GitHubClient(github_config)
    
    @pytest.mark.asyncio
    async def test_health_check(self, github_client):
        """Test GitHub client health check"""
        health = await github_client.health_check()
        
        assert isinstance(health, dict)
        assert "healthy" in health
        assert "api_accessible" in health
        assert "authenticated" in health
        assert "organization" in health
        assert "repository" in health
        assert health["organization"] == "TestOrg"
        assert health["repository"] == "TestRepo"
    
    @pytest.mark.asyncio
    async def test_create_workflow_file(self, github_client):
        """Test workflow file creation"""
        workflow_content = """
name: Test Workflow
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""
        
        result = await github_client.create_workflow_file("test-workflow", workflow_content)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "workflow_name" in result
        assert "workflow_path" in result
        assert result["workflow_name"] == "test-workflow"
    
    @pytest.mark.asyncio
    async def test_trigger_workflow(self, github_client):
        """Test workflow triggering"""
        result = await github_client.trigger_workflow("test-workflow", "main", {"param1": "value1"})
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "run_id" in result
        assert "workflow_name" in result
        assert "branch" in result
        assert result["workflow_name"] == "test-workflow"
        assert result["branch"] == "main"
    
    @pytest.mark.asyncio
    async def test_get_workflow_run_status(self, github_client):
        """Test workflow run status retrieval"""
        # First trigger a workflow
        trigger_result = await github_client.trigger_workflow("test-workflow", "main")
        run_id = trigger_result["run_id"]
        
        # Then check its status
        status = await github_client.get_workflow_run_status(run_id)
        
        assert isinstance(status, dict)
        assert "run_id" in status
        assert "status" in status
        assert "jobs" in status
        assert status["run_id"] == run_id
        assert status["status"] in ["queued", "in_progress", "completed"]
    
    @pytest.mark.asyncio
    async def test_create_deployment(self, github_client):
        """Test GitHub deployment creation"""
        result = await github_client.create_deployment("staging", "main", "Test deployment")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "deployment_id" in result
        assert "environment" in result
        assert "ref" in result
        assert result["environment"] == "staging"
        assert result["ref"] == "main"
    
    @pytest.mark.asyncio
    async def test_update_deployment_status(self, github_client):
        """Test deployment status update"""
        # First create a deployment
        deployment_result = await github_client.create_deployment("staging", "main", "Test")
        deployment_id = deployment_result["deployment_id"]
        
        # Then update its status
        update_result = await github_client.update_deployment_status(
            deployment_id, "success", "https://staging.example.com"
        )
        
        assert isinstance(update_result, dict)
        assert "success" in update_result
        assert "deployment_id" in update_result
        assert "status" in update_result
        assert update_result["deployment_id"] == deployment_id
        assert update_result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_create_release(self, github_client):
        """Test GitHub release creation"""
        result = await github_client.create_release(
            "v1.2.3", "Release v1.2.3", "Bug fixes and improvements", False
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "release_id" in result
        assert "tag_name" in result
        assert "name" in result
        assert result["tag_name"] == "v1.2.3"
        assert result["name"] == "Release v1.2.3"
    
    @pytest.mark.asyncio
    async def test_get_repository_info(self, github_client):
        """Test repository information retrieval"""
        info = await github_client.get_repository_info()
        
        assert isinstance(info, dict)
        assert "success" in info
        assert "organization" in info
        assert "repository" in info
        assert "default_branch" in info
        assert "languages" in info
        assert "workflows" in info
    
    @pytest.mark.asyncio
    async def test_list_workflow_runs(self, github_client):
        """Test workflow runs listing"""
        runs = await github_client.list_workflow_runs("test-workflow", 5)
        
        assert isinstance(runs, dict)
        assert "success" in runs
        assert "workflow_name" in runs
        assert "runs" in runs
        assert len(runs["runs"]) <= 5
        assert runs["workflow_name"] == "test-workflow"


class TestDockerClient:
    """Test suite for Docker client utility"""
    
    @pytest.fixture
    def docker_config(self):
        """Create Docker configuration for testing"""
        return {
            "docker_host": "unix:///var/run/docker.sock",
            "registry_url": "ghcr.io",
            "registry_namespace": "test-org",
            "registry_username": "test-user",
            "registry_password": "test-pass"
        }
    
    @pytest.fixture
    def docker_client(self, docker_config):
        """Create Docker client instance for testing"""
        return DockerClient(docker_config)
    
    @pytest.mark.asyncio
    async def test_health_check(self, docker_client):
        """Test Docker client health check"""
        health = await docker_client.health_check()
        
        assert isinstance(health, dict)
        assert "healthy" in health
        assert "daemon_accessible" in health
        assert "registry_accessible" in health
        assert "docker_version" in health
        assert "running_containers" in health
    
    @pytest.mark.asyncio
    async def test_build_image(self, docker_client):
        """Test Docker image building"""
        result = await docker_client.build_image(
            "/app", "Dockerfile", "test-image:v1.0.0", {"ENV": "production"}
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "build_id" in result
        assert "image_tag" in result
        assert "build_logs" in result
        assert result["image_tag"] == "test-image:v1.0.0"
    
    @pytest.mark.asyncio
    async def test_push_image(self, docker_client):
        """Test Docker image push"""
        # First build an image
        build_result = await docker_client.build_image("/app", "Dockerfile", "test-image:v1.0.0")
        
        # Then push it
        push_result = await docker_client.push_image("test-image:v1.0.0")
        
        assert isinstance(push_result, dict)
        assert "success" in push_result
        assert "image_tag" in push_result
        assert "registry_tag" in push_result
        assert "digest" in push_result
        assert push_result["image_tag"] == "test-image:v1.0.0"
    
    @pytest.mark.asyncio
    async def test_pull_image(self, docker_client):
        """Test Docker image pull"""
        result = await docker_client.pull_image("nginx:latest")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "image_tag" in result
        assert "image_id" in result
        assert "pull_logs" in result
        assert result["image_tag"] == "nginx:latest"
    
    @pytest.mark.asyncio
    async def test_run_container(self, docker_client):
        """Test Docker container running"""
        result = await docker_client.run_container(
            "nginx:latest",
            "test-nginx",
            {"80": "8080"},
            {"ENV": "test"},
            {"/data": "/app/data"}
        )
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "container_id" in result
        assert "container_name" in result
        assert "status" in result
        assert result["container_name"] == "test-nginx"
        assert result["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_stop_container(self, docker_client):
        """Test Docker container stopping"""
        # First run a container
        run_result = await docker_client.run_container("nginx:latest", "test-nginx")
        container_id = run_result["container_id"]
        
        # Then stop it
        stop_result = await docker_client.stop_container(container_id, 10)
        
        assert isinstance(stop_result, dict)
        assert "success" in stop_result
        assert "container_id" in stop_result
        assert "status" in stop_result
        assert stop_result["container_id"] == container_id
        assert stop_result["status"] == "stopped"
    
    @pytest.mark.asyncio
    async def test_list_containers(self, docker_client):
        """Test Docker container listing"""
        # Test running containers only
        running_containers = await docker_client.list_containers(False)
        
        assert isinstance(running_containers, dict)
        assert "success" in running_containers
        assert "total_containers" in running_containers
        assert "running_containers" in running_containers
        assert "containers" in running_containers
        
        # Test all containers
        all_containers = await docker_client.list_containers(True)
        
        assert isinstance(all_containers, dict)
        assert "success" in all_containers
        assert "containers" in all_containers
        assert len(all_containers["containers"]) >= len(running_containers["containers"])
    
    @pytest.mark.asyncio
    async def test_list_images(self, docker_client):
        """Test Docker image listing"""
        result = await docker_client.list_images()
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "total_images" in result
        assert "total_size_mb" in result
        assert "images" in result
        assert isinstance(result["images"], list)
    
    @pytest.mark.asyncio
    async def test_remove_image(self, docker_client):
        """Test Docker image removal"""
        result = await docker_client.remove_image("test-image:v1.0.0", False)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "image_tag" in result
        assert "freed_space_mb" in result
        assert result["image_tag"] == "test-image:v1.0.0"
    
    @pytest.mark.asyncio
    async def test_get_container_logs(self, docker_client):
        """Test container logs retrieval"""
        # First run a container
        run_result = await docker_client.run_container("nginx:latest", "test-nginx")
        container_id = run_result["container_id"]
        
        # Then get its logs
        logs_result = await docker_client.get_container_logs(container_id, 50)
        
        assert isinstance(logs_result, dict)
        assert "success" in logs_result
        assert "container_id" in logs_result
        assert "logs" in logs_result
        assert "lines_returned" in logs_result
        assert logs_result["container_id"] == container_id
        assert len(logs_result["logs"]) <= 50
    
    @pytest.mark.asyncio
    async def test_inspect_container(self, docker_client):
        """Test container inspection"""
        # First run a container
        run_result = await docker_client.run_container("nginx:latest", "test-nginx")
        container_id = run_result["container_id"]
        
        # Then inspect it
        inspect_result = await docker_client.inspect_container(container_id)
        
        assert isinstance(inspect_result, dict)
        assert "success" in inspect_result
        assert "container_id" in inspect_result
        assert "name" in inspect_result
        assert "image" in inspect_result
        assert "status" in inspect_result
        assert "network" in inspect_result
        assert "resource_usage" in inspect_result
        assert inspect_result["container_id"] == container_id


class TestMonitoringClient:
    """Test suite for Monitoring client utility"""
    
    @pytest.fixture
    def monitoring_config(self):
        """Create monitoring configuration for testing"""
        return {
            "metrics_endpoint": "http://localhost:9090",
            "alerting_endpoint": "http://localhost:9093",
            "dashboard_url": "http://localhost:3001",
            "collection_interval": 60
        }
    
    @pytest.fixture
    def monitoring_client(self, monitoring_config):
        """Create monitoring client instance for testing"""
        return MonitoringClient(monitoring_config)
    
    @pytest.mark.asyncio
    async def test_health_check(self, monitoring_client):
        """Test monitoring client health check"""
        health = await monitoring_client.health_check()
        
        assert isinstance(health, dict)
        assert "healthy" in health
        assert "metrics_system" in health
        assert "alerting_system" in health
        assert "dashboard_accessible" in health
        assert "collection_interval_seconds" in health
    
    @pytest.mark.asyncio
    async def test_collect_application_metrics(self, monitoring_client):
        """Test application metrics collection"""
        apps = ["sidhe-backend", "sidhe-frontend", "redis"]
        result = await monitoring_client.collect_application_metrics(apps)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "applications" in result
        assert "metrics" in result
        assert len(result["metrics"]) == len(apps)
        
        for app in apps:
            assert app in result["metrics"]
            app_metrics = result["metrics"][app]
            assert "cpu_usage_percent" in app_metrics
            assert "memory_usage_mb" in app_metrics
            assert "requests_per_minute" in app_metrics
    
    @pytest.mark.asyncio
    async def test_send_alert(self, monitoring_client):
        """Test alert sending"""
        alert = {
            "type": "cpu",
            "severity": "warning",
            "message": "CPU usage is high: 85%",
            "value": 85,
            "threshold": 80
        }
        
        result = await monitoring_client.send_alert(alert)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "alert_id" in result
        assert "alert_type" in result
        assert "severity" in result
        assert result["alert_type"] == "cpu"
        assert result["severity"] == "warning"
    
    @pytest.mark.asyncio
    async def test_query_metrics(self, monitoring_client):
        """Test metrics querying"""
        result = await monitoring_client.query_metrics("cpu_usage_percent", "1h")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "query" in result
        assert "time_range" in result
        assert "data" in result
        assert result["query"] == "cpu_usage_percent"
        assert result["time_range"] == "1h"
        assert isinstance(result["data"], list)
    
    @pytest.mark.asyncio
    async def test_create_dashboard(self, monitoring_client):
        """Test dashboard creation"""
        dashboard_config = {
            "name": "SIDHE DevOps Dashboard",
            "panels": [
                {"title": "CPU Usage", "query": "cpu_usage_percent"},
                {"title": "Memory Usage", "query": "memory_usage_percent"},
                {"title": "Deployment Status", "query": "deployment_success_rate"}
            ],
            "refresh_interval": "30s",
            "public": False
        }
        
        result = await monitoring_client.create_dashboard(dashboard_config)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "dashboard_id" in result
        assert "name" in result
        assert "dashboard_url" in result
        assert result["name"] == "SIDHE DevOps Dashboard"
        assert result["panels"] == 3
    
    @pytest.mark.asyncio
    async def test_get_alert_rules(self, monitoring_client):
        """Test alert rules retrieval"""
        result = await monitoring_client.get_alert_rules()
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "total_rules" in result
        assert "enabled_rules" in result
        assert "rules" in result
        assert isinstance(result["rules"], list)
        
        for rule in result["rules"]:
            assert "rule_id" in rule
            assert "name" in rule
            assert "query" in rule
            assert "severity" in rule
            assert "enabled" in rule
    
    @pytest.mark.asyncio
    async def test_update_alert_rule(self, monitoring_client):
        """Test alert rule update"""
        updates = {
            "enabled": False,
            "threshold": 90,
            "duration": "10m"
        }
        
        result = await monitoring_client.update_alert_rule("cpu-high", updates)
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "rule_id" in result
        assert "updates_applied" in result
        assert result["rule_id"] == "cpu-high"
        assert result["updates_applied"] == updates
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, monitoring_client):
        """Test active alerts retrieval"""
        result = await monitoring_client.get_active_alerts()
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "total_active_alerts" in result
        assert "critical_alerts" in result
        assert "warning_alerts" in result
        assert "alerts" in result
        assert isinstance(result["alerts"], list)
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, monitoring_client):
        """Test alert acknowledgment"""
        result = await monitoring_client.acknowledge_alert("alert-001", "Investigating the issue")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "alert_id" in result
        assert "acknowledged" in result
        assert "acknowledgment_note" in result
        assert result["alert_id"] == "alert-001"
        assert result["acknowledged"] is True


class TestDevOpsConfiguration:
    """Test suite for DevOps configuration management"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for tests"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_config_file(self, temp_config_dir):
        """Create sample configuration file for testing"""
        config_data = {
            "github": {
                "organization": "TestOrg",
                "repository": "TestRepo"
            },
            "docker": {
                "registry_url": "registry.test.com",
                "registry_namespace": "test-ns"
            },
            "monitoring": {
                "metrics_endpoint": "http://test-metrics:9090",
                "cpu_warning_threshold": 75.0,
                "memory_critical_threshold": 95.0
            },
            "deployment": {
                "default_strategy": "canary",
                "quality_gates_enabled": True,
                "canary_initial_traffic": 5
            },
            "quality_gates": {
                "enabled": True,
                "minimum_coverage": 85.0,
                "linting_required": True
            }
        }
        
        config_file = temp_config_dir / "devops_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        return config_file
    
    def test_config_loading_from_file(self, temp_config_dir, sample_config_file):
        """Test configuration loading from YAML file"""
        config = DevOpsConfig(temp_config_dir)
        
        # Test GitHub config
        assert config.github_config.organization == "TestOrg"
        assert config.github_config.repository == "TestRepo"
        
        # Test Docker config
        assert config.docker_config.registry_url == "registry.test.com"
        assert config.docker_config.registry_namespace == "test-ns"
        
        # Test monitoring config
        assert config.monitoring_config.metrics_endpoint == "http://test-metrics:9090"
        assert config.monitoring_config.cpu_warning_threshold == 75.0
        assert config.monitoring_config.memory_critical_threshold == 95.0
        
        # Test deployment config
        assert config.deployment_config.default_strategy == "canary"
        assert config.deployment_config.quality_gates_enabled is True
        assert config.deployment_config.canary_initial_traffic == 5
        
        # Test quality gates config
        assert config.quality_gates_config.enabled is True
        assert config.quality_gates_config.minimum_coverage == 85.0
        assert config.quality_gates_config.linting_required is True
    
    def test_config_default_values(self, temp_config_dir):
        """Test configuration with default values"""
        config = DevOpsConfig(temp_config_dir)
        
        # Test that defaults are applied when no config file exists
        assert config.github_config.organization == "EldestGruff"
        assert config.github_config.repository == "SIDHE"
        assert config.docker_config.registry_url == "ghcr.io"
        assert config.monitoring_config.cpu_warning_threshold == 70.0
        assert config.deployment_config.default_strategy == "blue_green"
    
    @patch.dict('os.environ', {
        'DEVOPS_GITHUB_ORG': 'EnvOrg',
        'DEVOPS_DOCKER_REGISTRY': 'env-registry.com',
        'DEVOPS_DEFAULT_STRATEGY': 'direct'
    })
    def test_environment_overrides(self, temp_config_dir):
        """Test environment variable overrides"""
        config = DevOpsConfig(temp_config_dir)
        
        assert config.github_config.organization == "EnvOrg"
        assert config.docker_config.registry_url == "env-registry.com"
        assert config.deployment_config.default_strategy == "direct"
    
    def test_get_deployment_strategy_config(self, temp_config_dir):
        """Test deployment strategy configuration retrieval"""
        config = DevOpsConfig(temp_config_dir)
        
        # Test blue-green strategy config
        bg_config = config.get_deployment_strategy_config("blue_green")
        assert "health_check_timeout" in bg_config
        assert "traffic_switch_delay" in bg_config
        assert "rollback_timeout" in bg_config
        assert bg_config["quality_gates_enabled"] is True
        
        # Test canary strategy config
        canary_config = config.get_deployment_strategy_config("canary")
        assert "initial_traffic" in canary_config
        assert "increment_percentage" in canary_config
        assert "increment_interval" in canary_config
        assert "success_threshold" in canary_config
        
        # Test direct strategy config
        direct_config = config.get_deployment_strategy_config("direct")
        assert "backup_enabled" in direct_config
        assert "health_check_timeout" in direct_config
        assert "rollback_timeout" in direct_config
        
        # Test invalid strategy
        invalid_config = config.get_deployment_strategy_config("invalid")
        assert invalid_config == {}
    
    def test_get_quality_gates_config(self, temp_config_dir):
        """Test quality gates configuration retrieval"""
        config = DevOpsConfig(temp_config_dir)
        gates_config = config.get_quality_gates_config()
        
        assert "enabled" in gates_config
        assert "minimum_coverage" in gates_config
        assert "target_coverage" in gates_config
        assert "linting_required" in gates_config
        assert "security_scan_required" in gates_config
        assert "timeouts" in gates_config
        
        timeouts = gates_config["timeouts"]
        assert "linting" in timeouts
        assert "security_scan" in timeouts
        assert "performance_test" in timeouts
    
    def test_get_monitoring_thresholds(self, temp_config_dir):
        """Test monitoring thresholds retrieval"""
        config = DevOpsConfig(temp_config_dir)
        thresholds = config.get_monitoring_thresholds()
        
        assert "cpu" in thresholds
        assert "memory" in thresholds
        assert "disk" in thresholds
        assert "response_time" in thresholds
        
        # Validate structure
        for resource in ["cpu", "memory", "disk"]:
            assert "warning" in thresholds[resource]
            assert "critical" in thresholds[resource]
            assert thresholds[resource]["warning"] < thresholds[resource]["critical"]
        
        assert "warning" in thresholds["response_time"]
        assert "critical" in thresholds["response_time"]
    
    def test_validate_configuration(self, temp_config_dir):
        """Test configuration validation"""
        config = DevOpsConfig(temp_config_dir)
        
        # Test valid configuration
        validation = config.validate_configuration()
        assert "valid" in validation
        assert "warnings" in validation
        assert "errors" in validation
        assert isinstance(validation["warnings"], list)
        assert isinstance(validation["errors"], list)
        
        # Test invalid configuration
        config.deployment_config.default_strategy = "invalid_strategy"
        config.quality_gates_config.minimum_coverage = 95.0
        config.quality_gates_config.target_coverage = 80.0  # Lower than minimum
        
        validation = config.validate_configuration()
        assert validation["valid"] is False
        assert len(validation["errors"]) >= 2
    
    def test_save_configuration(self, temp_config_dir):
        """Test configuration saving"""
        config = DevOpsConfig(temp_config_dir)
        
        # Modify some settings
        config.github_config.organization = "SavedOrg"
        config.docker_config.registry_namespace = "saved-ns"
        config.monitoring_config.cpu_warning_threshold = 65.0
        
        # Save configuration
        save_result = config.save_configuration()
        
        assert "success" in save_result
        if save_result["success"]:
            assert "config_file" in save_result
            
            # Verify saved file exists and contains correct data
            saved_file = Path(save_result["config_file"])
            assert saved_file.exists()
            
            with open(saved_file, 'r') as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data["github"]["organization"] == "SavedOrg"
            assert saved_data["docker"]["registry_namespace"] == "saved-ns"
            assert saved_data["monitoring"]["cpu_warning_threshold"] == 65.0
    
    def test_to_dict(self, temp_config_dir):
        """Test configuration dictionary conversion"""
        config = DevOpsConfig(temp_config_dir)
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "github" in config_dict
        assert "docker" in config_dict
        assert "monitoring" in config_dict
        assert "deployment" in config_dict
        assert "quality_gates" in config_dict
        
        # Validate GitHub section
        github_section = config_dict["github"]
        assert "organization" in github_section
        assert "repository" in github_section
        assert "token_configured" in github_section
        
        # Validate Docker section
        docker_section = config_dict["docker"]
        assert "registry_url" in docker_section
        assert "credentials_configured" in docker_section
        
        # Validate monitoring section
        monitoring_section = config_dict["monitoring"]
        assert "thresholds" in monitoring_section
        
        # Validate deployment section
        deployment_section = config_dict["deployment"]
        assert "strategies" in deployment_section
        strategies = deployment_section["strategies"]
        assert "blue_green" in strategies
        assert "canary" in strategies
        assert "direct" in strategies


if __name__ == "__main__":
    pytest.main([__file__, "-v"])