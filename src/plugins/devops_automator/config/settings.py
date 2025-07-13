"""
DevOps Automator Configuration Settings

Configuration management for DevOps automation including
deployment strategies, monitoring settings, and integration parameters.
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GitHubConfig:
    """GitHub integration configuration"""
    token: Optional[str] = None
    organization: str = "EldestGruff"
    repository: str = "SIDHE"
    api_base_url: str = "https://api.github.com"
    webhook_secret: Optional[str] = None
    
    def __post_init__(self):
        # Load token from environment if not provided
        if not self.token:
            self.token = os.getenv("GITHUB_TOKEN")


@dataclass
class DockerConfig:
    """Docker configuration"""
    docker_host: str = "unix:///var/run/docker.sock"
    registry_url: str = "ghcr.io"
    registry_namespace: str = "sidhe"
    registry_username: Optional[str] = None
    registry_password: Optional[str] = None
    
    def __post_init__(self):
        # Load registry credentials from environment if not provided
        if not self.registry_username:
            self.registry_username = os.getenv("DOCKER_REGISTRY_USERNAME")
        if not self.registry_password:
            self.registry_password = os.getenv("DOCKER_REGISTRY_PASSWORD")


@dataclass
class MonitoringConfig:
    """Monitoring system configuration"""
    metrics_endpoint: str = "http://localhost:9090"
    alerting_endpoint: str = "http://localhost:9093"
    dashboard_url: str = "http://localhost:3001"
    collection_interval: int = 60
    retention_days: int = 30
    
    # Alert thresholds
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 85.0
    memory_warning_threshold: float = 80.0
    memory_critical_threshold: float = 90.0
    disk_warning_threshold: float = 80.0
    disk_critical_threshold: float = 90.0
    response_time_warning_ms: int = 1000
    response_time_critical_ms: int = 2000


@dataclass
class DeploymentConfig:
    """Deployment strategy configuration"""
    default_strategy: str = "blue_green"
    quality_gates_enabled: bool = True
    rollback_enabled: bool = True
    
    # Blue-green deployment settings
    blue_green_health_check_timeout: int = 300
    blue_green_traffic_switch_delay: int = 60
    blue_green_rollback_timeout: int = 180
    
    # Canary deployment settings
    canary_initial_traffic: int = 10
    canary_increment_percentage: int = 20
    canary_increment_interval: int = 300
    canary_success_threshold: float = 99.5
    
    # Direct deployment settings
    direct_backup_enabled: bool = True
    direct_health_check_timeout: int = 180
    direct_rollback_timeout: int = 120


@dataclass
class QualityGatesConfig:
    """Quality gates configuration"""
    enabled: bool = True
    minimum_coverage: float = 80.0
    target_coverage: float = 90.0
    linting_required: bool = True
    security_scan_required: bool = True
    performance_test_required: bool = False
    
    # Gate timeouts
    linting_timeout: int = 300
    security_scan_timeout: int = 600
    performance_test_timeout: int = 900


class DevOpsConfig:
    """
    Main configuration class for DevOps Automator Plugin
    
    Manages all configuration aspects including GitHub integration,
    Docker settings, monitoring, deployment strategies, and quality gates.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize DevOps configuration"""
        self.config_path = config_path or Path(__file__).parent
        
        # Load configuration from files and environment
        self._load_configuration()
        
        logger.info("DevOps configuration initialized")
    
    def _load_configuration(self):
        """Load configuration from files and environment variables"""
        try:
            # Load from YAML configuration file if it exists
            config_file = self.config_path / "devops_config.yaml"
            config_data = {}
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
            
            # Initialize configuration objects
            self.github_config = GitHubConfig(**config_data.get("github", {}))
            self.docker_config = DockerConfig(**config_data.get("docker", {}))
            self.monitoring_config = MonitoringConfig(**config_data.get("monitoring", {}))
            self.deployment_config = DeploymentConfig(**config_data.get("deployment", {}))
            self.quality_gates_config = QualityGatesConfig(**config_data.get("quality_gates", {}))
            
            # Load environment-specific overrides
            self._apply_environment_overrides()
            
        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            # Use default configurations if loading fails
            self.github_config = GitHubConfig()
            self.docker_config = DockerConfig()
            self.monitoring_config = MonitoringConfig()
            self.deployment_config = DeploymentConfig()
            self.quality_gates_config = QualityGatesConfig()
    
    def _apply_environment_overrides(self):
        """Apply environment variable overrides"""
        # GitHub overrides
        if os.getenv("DEVOPS_GITHUB_ORG"):
            self.github_config.organization = os.getenv("DEVOPS_GITHUB_ORG")
        if os.getenv("DEVOPS_GITHUB_REPO"):
            self.github_config.repository = os.getenv("DEVOPS_GITHUB_REPO")
        
        # Docker overrides
        if os.getenv("DEVOPS_DOCKER_REGISTRY"):
            self.docker_config.registry_url = os.getenv("DEVOPS_DOCKER_REGISTRY")
        if os.getenv("DEVOPS_DOCKER_NAMESPACE"):
            self.docker_config.registry_namespace = os.getenv("DEVOPS_DOCKER_NAMESPACE")
        
        # Monitoring overrides
        if os.getenv("DEVOPS_METRICS_ENDPOINT"):
            self.monitoring_config.metrics_endpoint = os.getenv("DEVOPS_METRICS_ENDPOINT")
        if os.getenv("DEVOPS_DASHBOARD_URL"):
            self.monitoring_config.dashboard_url = os.getenv("DEVOPS_DASHBOARD_URL")
        
        # Deployment overrides
        if os.getenv("DEVOPS_DEFAULT_STRATEGY"):
            self.deployment_config.default_strategy = os.getenv("DEVOPS_DEFAULT_STRATEGY")
        if os.getenv("DEVOPS_QUALITY_GATES_ENABLED"):
            self.deployment_config.quality_gates_enabled = os.getenv("DEVOPS_QUALITY_GATES_ENABLED").lower() == "true"
    
    def get_deployment_strategy_config(self, strategy: str) -> Dict[str, Any]:
        """
        Get configuration for specific deployment strategy
        
        Args:
            strategy: Deployment strategy name
            
        Returns:
            Strategy-specific configuration
        """
        if strategy == "blue_green":
            return {
                "health_check_timeout": self.deployment_config.blue_green_health_check_timeout,
                "traffic_switch_delay": self.deployment_config.blue_green_traffic_switch_delay,
                "rollback_timeout": self.deployment_config.blue_green_rollback_timeout,
                "quality_gates_enabled": self.deployment_config.quality_gates_enabled
            }
        elif strategy == "canary":
            return {
                "initial_traffic": self.deployment_config.canary_initial_traffic,
                "increment_percentage": self.deployment_config.canary_increment_percentage,
                "increment_interval": self.deployment_config.canary_increment_interval,
                "success_threshold": self.deployment_config.canary_success_threshold,
                "quality_gates_enabled": self.deployment_config.quality_gates_enabled
            }
        elif strategy == "direct":
            return {
                "backup_enabled": self.deployment_config.direct_backup_enabled,
                "health_check_timeout": self.deployment_config.direct_health_check_timeout,
                "rollback_timeout": self.deployment_config.direct_rollback_timeout,
                "quality_gates_enabled": self.deployment_config.quality_gates_enabled
            }
        else:
            return {}
    
    def get_quality_gates_config(self) -> Dict[str, Any]:
        """Get quality gates configuration"""
        return {
            "enabled": self.quality_gates_config.enabled,
            "minimum_coverage": self.quality_gates_config.minimum_coverage,
            "target_coverage": self.quality_gates_config.target_coverage,
            "linting_required": self.quality_gates_config.linting_required,
            "security_scan_required": self.quality_gates_config.security_scan_required,
            "performance_test_required": self.quality_gates_config.performance_test_required,
            "timeouts": {
                "linting": self.quality_gates_config.linting_timeout,
                "security_scan": self.quality_gates_config.security_scan_timeout,
                "performance_test": self.quality_gates_config.performance_test_timeout
            }
        }
    
    def get_monitoring_thresholds(self) -> Dict[str, Any]:
        """Get monitoring alert thresholds"""
        return {
            "cpu": {
                "warning": self.monitoring_config.cpu_warning_threshold,
                "critical": self.monitoring_config.cpu_critical_threshold
            },
            "memory": {
                "warning": self.monitoring_config.memory_warning_threshold,
                "critical": self.monitoring_config.memory_critical_threshold
            },
            "disk": {
                "warning": self.monitoring_config.disk_warning_threshold,
                "critical": self.monitoring_config.disk_critical_threshold
            },
            "response_time": {
                "warning": self.monitoring_config.response_time_warning_ms,
                "critical": self.monitoring_config.response_time_critical_ms
            }
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate configuration settings
        
        Returns:
            Validation results
        """
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Validate GitHub configuration
        if not self.github_config.token:
            validation_results["warnings"].append("GitHub token not configured - some features may be limited")
        
        # Validate Docker configuration
        if not self.docker_config.registry_username or not self.docker_config.registry_password:
            validation_results["warnings"].append("Docker registry credentials not configured - push operations may fail")
        
        # Validate deployment strategy
        valid_strategies = ["blue_green", "canary", "direct"]
        if self.deployment_config.default_strategy not in valid_strategies:
            validation_results["errors"].append(f"Invalid default deployment strategy: {self.deployment_config.default_strategy}")
            validation_results["valid"] = False
        
        # Validate quality gates thresholds
        if self.quality_gates_config.minimum_coverage > self.quality_gates_config.target_coverage:
            validation_results["errors"].append("Minimum coverage cannot be higher than target coverage")
            validation_results["valid"] = False
        
        # Validate monitoring thresholds
        if self.monitoring_config.cpu_warning_threshold >= self.monitoring_config.cpu_critical_threshold:
            validation_results["errors"].append("CPU warning threshold must be lower than critical threshold")
            validation_results["valid"] = False
        
        if self.monitoring_config.memory_warning_threshold >= self.monitoring_config.memory_critical_threshold:
            validation_results["errors"].append("Memory warning threshold must be lower than critical threshold")
            validation_results["valid"] = False
        
        return validation_results
    
    def save_configuration(self, config_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Save current configuration to YAML file
        
        Args:
            config_file: Optional path to save configuration
            
        Returns:
            Save operation results
        """
        try:
            save_path = config_file or (self.config_path / "devops_config.yaml")
            
            config_data = {
                "github": {
                    "organization": self.github_config.organization,
                    "repository": self.github_config.repository,
                    "api_base_url": self.github_config.api_base_url
                    # Note: Don't save sensitive data like tokens
                },
                "docker": {
                    "docker_host": self.docker_config.docker_host,
                    "registry_url": self.docker_config.registry_url,
                    "registry_namespace": self.docker_config.registry_namespace
                    # Note: Don't save sensitive credentials
                },
                "monitoring": {
                    "metrics_endpoint": self.monitoring_config.metrics_endpoint,
                    "alerting_endpoint": self.monitoring_config.alerting_endpoint,
                    "dashboard_url": self.monitoring_config.dashboard_url,
                    "collection_interval": self.monitoring_config.collection_interval,
                    "retention_days": self.monitoring_config.retention_days,
                    "cpu_warning_threshold": self.monitoring_config.cpu_warning_threshold,
                    "cpu_critical_threshold": self.monitoring_config.cpu_critical_threshold,
                    "memory_warning_threshold": self.monitoring_config.memory_warning_threshold,
                    "memory_critical_threshold": self.monitoring_config.memory_critical_threshold,
                    "disk_warning_threshold": self.monitoring_config.disk_warning_threshold,
                    "disk_critical_threshold": self.monitoring_config.disk_critical_threshold,
                    "response_time_warning_ms": self.monitoring_config.response_time_warning_ms,
                    "response_time_critical_ms": self.monitoring_config.response_time_critical_ms
                },
                "deployment": {
                    "default_strategy": self.deployment_config.default_strategy,
                    "quality_gates_enabled": self.deployment_config.quality_gates_enabled,
                    "rollback_enabled": self.deployment_config.rollback_enabled,
                    "blue_green_health_check_timeout": self.deployment_config.blue_green_health_check_timeout,
                    "blue_green_traffic_switch_delay": self.deployment_config.blue_green_traffic_switch_delay,
                    "blue_green_rollback_timeout": self.deployment_config.blue_green_rollback_timeout,
                    "canary_initial_traffic": self.deployment_config.canary_initial_traffic,
                    "canary_increment_percentage": self.deployment_config.canary_increment_percentage,
                    "canary_increment_interval": self.deployment_config.canary_increment_interval,
                    "canary_success_threshold": self.deployment_config.canary_success_threshold,
                    "direct_backup_enabled": self.deployment_config.direct_backup_enabled,
                    "direct_health_check_timeout": self.deployment_config.direct_health_check_timeout,
                    "direct_rollback_timeout": self.deployment_config.direct_rollback_timeout
                },
                "quality_gates": {
                    "enabled": self.quality_gates_config.enabled,
                    "minimum_coverage": self.quality_gates_config.minimum_coverage,
                    "target_coverage": self.quality_gates_config.target_coverage,
                    "linting_required": self.quality_gates_config.linting_required,
                    "security_scan_required": self.quality_gates_config.security_scan_required,
                    "performance_test_required": self.quality_gates_config.performance_test_required,
                    "linting_timeout": self.quality_gates_config.linting_timeout,
                    "security_scan_timeout": self.quality_gates_config.security_scan_timeout,
                    "performance_test_timeout": self.quality_gates_config.performance_test_timeout
                }
            }
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            return {
                "success": True,
                "config_file": str(save_path),
                "saved_at": logger.info(f"Configuration saved to {save_path}")
            }
            
        except Exception as e:
            logger.error(f"Configuration save failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "github": {
                "organization": self.github_config.organization,
                "repository": self.github_config.repository,
                "api_base_url": self.github_config.api_base_url,
                "token_configured": bool(self.github_config.token)
            },
            "docker": {
                "docker_host": self.docker_config.docker_host,
                "registry_url": self.docker_config.registry_url,
                "registry_namespace": self.docker_config.registry_namespace,
                "credentials_configured": bool(self.docker_config.registry_username and self.docker_config.registry_password)
            },
            "monitoring": {
                "metrics_endpoint": self.monitoring_config.metrics_endpoint,
                "alerting_endpoint": self.monitoring_config.alerting_endpoint,
                "dashboard_url": self.monitoring_config.dashboard_url,
                "collection_interval": self.monitoring_config.collection_interval,
                "thresholds": self.get_monitoring_thresholds()
            },
            "deployment": {
                "default_strategy": self.deployment_config.default_strategy,
                "quality_gates_enabled": self.deployment_config.quality_gates_enabled,
                "rollback_enabled": self.deployment_config.rollback_enabled,
                "strategies": {
                    "blue_green": self.get_deployment_strategy_config("blue_green"),
                    "canary": self.get_deployment_strategy_config("canary"),
                    "direct": self.get_deployment_strategy_config("direct")
                }
            },
            "quality_gates": self.get_quality_gates_config()
        }