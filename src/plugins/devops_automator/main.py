"""
DevOps Automator Plugin - Main Implementation

Enterprise-grade DevOps automation orchestrator providing CI/CD pipeline management,
Docker image operations, infrastructure monitoring, and deployment strategies.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

from .components.pipeline_orchestrator import PipelineOrchestrator
from .components.docker_manager import DockerManager
from .components.infrastructure_monitor import InfrastructureMonitor
from .components.deployment_orchestrator import DeploymentOrchestrator
from .utils.github_client import GitHubClient
from .utils.docker_client import DockerClient
from .utils.monitoring_client import MonitoringClient
from .config.settings import DevOpsConfig

logger = logging.getLogger(__name__)


@dataclass
class DeploymentConfig:
    """Configuration for deployment operations"""
    environment: str
    strategy: str  # "direct", "blue_green", "canary"
    quality_gates: List[str]
    rollback_criteria: Dict[str, Any]
    security_requirements: Dict[str, Any]
    timeout_seconds: int = 300

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeploymentResult:
    """Results from deployment operations"""
    deployment_id: str
    status: str
    environment: str
    strategy: str
    start_time: str
    end_time: Optional[str]
    logs: List[str]
    metrics: Dict[str, Any]
    rollback_available: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InfrastructureStatus:
    """Current infrastructure health and status"""
    services: Dict[str, Dict[str, Any]]
    containers: Dict[str, Dict[str, Any]]
    metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    resource_usage: Dict[str, Any]
    last_updated: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineResult:
    """Results from CI/CD pipeline operations"""
    pipeline_id: str
    status: str
    stages: List[Dict[str, Any]]
    quality_gates: List[Dict[str, Any]]
    deployment_url: Optional[str]
    rollback_url: Optional[str]
    duration_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DevOpsAutomatorPlugin:
    """
    DevOps Automator Plugin - ADR-025 Implementation
    
    Provides enterprise-grade DevOps automation through:
    - CI/CD pipeline orchestration with GitHub Actions integration
    - Docker image management with security scanning and lifecycle automation
    - Infrastructure monitoring with real-time health dashboards
    - Deployment orchestration supporting multiple strategies
    - Quality gate integration with Quality Control Plugin
    - Real-time DevOps event streaming
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize DevOps Automator Plugin"""
        self.plugin_name = "devops_automator"
        self.version = "1.0.0"
        self.config_path = config_path or Path(__file__).parent / "config"
        
        # Load configuration
        self.config = DevOpsConfig(self.config_path)
        
        # Initialize components
        self.pipeline_orchestrator = PipelineOrchestrator(self.config_path)
        self.docker_manager = DockerManager(self.config_path)
        self.infrastructure_monitor = InfrastructureMonitor(self.config_path)
        self.deployment_orchestrator = DeploymentOrchestrator(self.config_path)
        
        # Initialize utilities
        self.github_client = GitHubClient(self.config.github_config)
        self.docker_client = DockerClient(self.config.docker_config)
        self.monitoring_client = MonitoringClient(self.config.monitoring_config)
        
        # Plugin state
        self.enabled = True
        self.active_deployments = {}
        self.last_health_check = None
        
        logger.info(f"DevOps Automator Plugin v{self.version} initialized")

    async def health_check(self) -> Dict[str, Any]:
        """Plugin health check for SIDHE monitoring"""
        try:
            # Check component health
            components = {
                "pipeline_orchestrator": await self.pipeline_orchestrator.health_check(),
                "docker_manager": await self.docker_manager.health_check(),
                "infrastructure_monitor": await self.infrastructure_monitor.health_check(),
                "deployment_orchestrator": await self.deployment_orchestrator.health_check(),
            }
            
            # Check external dependencies
            external_deps = {
                "github_api": await self.github_client.health_check(),
                "docker_daemon": await self.docker_client.health_check(),
                "monitoring_systems": await self.monitoring_client.health_check(),
            }
            
            all_healthy = (
                all(comp.get("healthy", False) for comp in components.values()) and
                all(dep.get("healthy", False) for dep in external_deps.values())
            )
            
            self.last_health_check = datetime.now().isoformat()
            
            return {
                "plugin": self.plugin_name,
                "version": self.version,
                "healthy": all_healthy,
                "status": "operational" if all_healthy else "degraded",
                "components": components,
                "external_dependencies": external_deps,
                "active_deployments": len(self.active_deployments),
                "last_check": self.last_health_check,
                "enabled": self.enabled,
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "plugin": self.plugin_name,
                "healthy": False,
                "status": "error",
                "error": str(e),
            }

    async def deploy_environment(self, environment: str, config: DeploymentConfig) -> DeploymentResult:
        """
        Deploy to specified environment using configured strategy
        
        Args:
            environment: Target environment (dev, staging, production)
            config: Deployment configuration and parameters
            
        Returns:
            DeploymentResult with deployment status and details
        """
        logger.info(f"Starting deployment to {environment} using {config.strategy} strategy")
        
        deployment_id = f"deploy-{environment}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        start_time = datetime.now()
        
        try:
            # Validate quality gates if specified
            if config.quality_gates:
                gate_results = await self._validate_quality_gates(config.quality_gates)
                if not gate_results["passed"]:
                    return DeploymentResult(
                        deployment_id=deployment_id,
                        status="failed",
                        environment=environment,
                        strategy=config.strategy,
                        start_time=start_time.isoformat(),
                        end_time=datetime.now().isoformat(),
                        logs=[f"Quality gates failed: {gate_results['failures']}"],
                        metrics={},
                        rollback_available=False
                    )
            
            # Execute deployment based on strategy
            if config.strategy == "blue_green":
                result = await self.deployment_orchestrator.execute_blue_green_deployment(
                    environment, config
                )
            elif config.strategy == "canary":
                result = await self.deployment_orchestrator.execute_canary_deployment(
                    environment, config
                )
            else:  # direct deployment
                result = await self.deployment_orchestrator.execute_direct_deployment(
                    environment, config
                )
            
            # Track active deployment
            self.active_deployments[deployment_id] = {
                "environment": environment,
                "strategy": config.strategy,
                "start_time": start_time.isoformat(),
                "status": result["status"]
            }
            
            # Monitor deployment health
            await self._monitor_deployment_health(deployment_id, environment)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Deployment {deployment_id} completed in {duration:.2f}s")
            
            return DeploymentResult(
                deployment_id=deployment_id,
                status=result["status"],
                environment=environment,
                strategy=config.strategy,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                logs=result.get("logs", []),
                metrics=result.get("metrics", {}),
                rollback_available=result.get("rollback_available", True)
            )
            
        except Exception as e:
            logger.error(f"Deployment {deployment_id} failed: {e}")
            return DeploymentResult(
                deployment_id=deployment_id,
                status="failed",
                environment=environment,
                strategy=config.strategy,
                start_time=start_time.isoformat(),
                end_time=datetime.now().isoformat(),
                logs=[f"Deployment failed: {str(e)}"],
                metrics={},
                rollback_available=False
            )

    async def manage_docker_images(self, action: str, image_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage Docker images through their lifecycle
        
        Args:
            action: Action to perform (build, scan, push, pull, cleanup)
            image_config: Image configuration and parameters
            
        Returns:
            Results of the image management operation
        """
        logger.info(f"Managing Docker image: {action} for {image_config.get('name', 'unknown')}")
        
        try:
            if action == "build":
                return await self.docker_manager.build_image(image_config)
            elif action == "scan":
                return await self.docker_manager.scan_image_security(image_config["name"])
            elif action == "push":
                return await self.docker_manager.push_image(image_config["name"])
            elif action == "pull":
                return await self.docker_manager.pull_image(image_config["name"])
            elif action == "cleanup":
                return await self.docker_manager.cleanup_images(image_config.get("policy", {}))
            else:
                raise ValueError(f"Unknown Docker action: {action}")
                
        except Exception as e:
            logger.error(f"Docker image management failed for {action}: {e}")
            return {
                "status": "error",
                "action": action,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def monitor_infrastructure(self, scope: str = "all") -> InfrastructureStatus:
        """
        Monitor infrastructure health and collect metrics
        
        Args:
            scope: Monitoring scope (all, services, containers, resources)
            
        Returns:
            InfrastructureStatus with current system state
        """
        logger.info(f"Monitoring infrastructure (scope: {scope})")
        
        try:
            # Collect system metrics
            metrics = await self.infrastructure_monitor.collect_system_metrics(scope)
            
            # Monitor service health
            services = await self.infrastructure_monitor.monitor_service_health()
            
            # Monitor container status
            containers = await self.infrastructure_monitor.monitor_container_status()
            
            # Check for alerts
            alerts = await self.infrastructure_monitor.check_alerts()
            
            # Calculate resource usage
            resource_usage = await self.infrastructure_monitor.calculate_resource_usage()
            
            return InfrastructureStatus(
                services=services,
                containers=containers,
                metrics=metrics,
                alerts=alerts,
                resource_usage=resource_usage,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Infrastructure monitoring failed: {e}")
            raise

    async def orchestrate_pipeline(self, pipeline_config: Dict[str, Any]) -> PipelineResult:
        """
        Orchestrate CI/CD pipeline execution
        
        Args:
            pipeline_config: Pipeline configuration and parameters
            
        Returns:
            PipelineResult with execution status and details
        """
        logger.info(f"Orchestrating pipeline: {pipeline_config.get('name', 'unnamed')}")
        
        pipeline_id = f"pipeline-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        start_time = datetime.now()
        
        try:
            # Create or update GitHub Actions workflow
            workflow_result = await self.pipeline_orchestrator.create_workflow(pipeline_config)
            
            # Trigger pipeline execution
            execution_result = await self.pipeline_orchestrator.trigger_pipeline(
                pipeline_config["repository"],
                pipeline_config.get("branch", "main")
            )
            
            # Monitor pipeline progress
            monitoring_result = await self.pipeline_orchestrator.monitor_pipeline_progress(
                execution_result["run_id"]
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return PipelineResult(
                pipeline_id=pipeline_id,
                status=monitoring_result["status"],
                stages=monitoring_result.get("stages", []),
                quality_gates=monitoring_result.get("quality_gates", []),
                deployment_url=monitoring_result.get("deployment_url"),
                rollback_url=monitoring_result.get("rollback_url"),
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Pipeline orchestration failed: {e}")
            return PipelineResult(
                pipeline_id=pipeline_id,
                status="failed",
                stages=[],
                quality_gates=[],
                deployment_url=None,
                rollback_url=None,
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )

    async def manage_rollbacks(self, deployment_id: str, strategy: str = "automatic") -> Dict[str, Any]:
        """
        Manage deployment rollbacks with various strategies
        
        Args:
            deployment_id: ID of deployment to rollback
            strategy: Rollback strategy (automatic, manual, immediate)
            
        Returns:
            Rollback operation results
        """
        logger.info(f"Managing rollback for deployment {deployment_id} (strategy: {strategy})")
        
        try:
            if deployment_id not in self.active_deployments:
                return {
                    "status": "error",
                    "message": f"Deployment {deployment_id} not found",
                    "timestamp": datetime.now().isoformat()
                }
            
            deployment_info = self.active_deployments[deployment_id]
            
            return await self.deployment_orchestrator.execute_rollback(
                deployment_id,
                deployment_info["environment"],
                strategy
            )
            
        except Exception as e:
            logger.error(f"Rollback management failed: {e}")
            return {
                "status": "error",
                "deployment_id": deployment_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def analyze_deployment_metrics(self, timeframe: str = "24h") -> Dict[str, Any]:
        """
        Analyze deployment metrics and performance
        
        Args:
            timeframe: Analysis timeframe (1h, 24h, 7d, 30d)
            
        Returns:
            Deployment metrics analysis
        """
        logger.info(f"Analyzing deployment metrics for timeframe: {timeframe}")
        
        try:
            # Collect deployment metrics
            metrics = await self.infrastructure_monitor.collect_deployment_metrics(timeframe)
            
            # Analyze performance trends
            trends = await self._analyze_performance_trends(metrics, timeframe)
            
            # Calculate success rates
            success_rates = await self._calculate_success_rates(metrics)
            
            # Generate insights and recommendations
            insights = await self._generate_deployment_insights(metrics, trends, success_rates)
            
            return {
                "timeframe": timeframe,
                "metrics": metrics,
                "trends": trends,
                "success_rates": success_rates,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Deployment metrics analysis failed: {e}")
            return {
                "status": "error",
                "timeframe": timeframe,
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }

    # Private helper methods

    async def _validate_quality_gates(self, quality_gates: List[str]) -> Dict[str, Any]:
        """Validate quality gates before deployment"""
        try:
            # Import Quality Control Plugin if available
            from ..quality_control.main import QualityControlPlugin
            
            quality_plugin = QualityControlPlugin()
            results = {"passed": True, "failures": []}
            
            for gate in quality_gates:
                if gate == "linting_check":
                    lint_result = await quality_plugin.run_incremental_check([])
                    if lint_result.errors > 0:
                        results["passed"] = False
                        results["failures"].append(f"Linting errors: {lint_result.errors}")
                        
                elif gate == "coverage_check":
                    quality_report = await quality_plugin.run_full_quality_check()
                    coverage = quality_report.coverage_results.get("overall_coverage", 0)
                    if coverage < 80:
                        results["passed"] = False
                        results["failures"].append(f"Coverage below threshold: {coverage}%")
                        
                # Add more quality gate validations as needed
            
            return results
            
        except ImportError:
            logger.warning("Quality Control Plugin not available for gate validation")
            return {"passed": True, "failures": []}
        except Exception as e:
            logger.error(f"Quality gate validation failed: {e}")
            return {"passed": False, "failures": [str(e)]}

    async def _monitor_deployment_health(self, deployment_id: str, environment: str):
        """Monitor deployment health in background"""
        try:
            # Start background monitoring task
            asyncio.create_task(
                self._deployment_health_monitor_task(deployment_id, environment)
            )
        except Exception as e:
            logger.error(f"Failed to start deployment health monitoring: {e}")

    async def _deployment_health_monitor_task(self, deployment_id: str, environment: str):
        """Background task to monitor deployment health"""
        try:
            for _ in range(10):  # Monitor for 10 cycles
                await asyncio.sleep(30)  # Check every 30 seconds
                
                health_status = await self.infrastructure_monitor.check_deployment_health(
                    deployment_id, environment
                )
                
                if not health_status.get("healthy", True):
                    logger.warning(f"Deployment {deployment_id} health degraded")
                    # Could trigger automatic rollback here based on configuration
                    
        except Exception as e:
            logger.error(f"Deployment health monitoring task failed: {e}")

    async def _analyze_performance_trends(self, metrics: Dict, timeframe: str) -> Dict[str, Any]:
        """Analyze performance trends from metrics"""
        # Placeholder for trend analysis logic
        return {
            "deployment_frequency": "stable",
            "success_rate_trend": "improving",
            "performance_trend": "stable",
            "resource_usage_trend": "optimizing"
        }

    async def _calculate_success_rates(self, metrics: Dict) -> Dict[str, float]:
        """Calculate deployment success rates"""
        total_deployments = metrics.get("total_deployments", 0)
        successful_deployments = metrics.get("successful_deployments", 0)
        
        if total_deployments == 0:
            return {"overall": 0.0, "by_environment": {}}
        
        overall_rate = (successful_deployments / total_deployments) * 100
        
        return {
            "overall": round(overall_rate, 2),
            "by_environment": metrics.get("environment_success_rates", {}),
            "by_strategy": metrics.get("strategy_success_rates", {})
        }

    async def _generate_deployment_insights(self, metrics: Dict, trends: Dict, success_rates: Dict) -> List[str]:
        """Generate deployment insights and recommendations"""
        insights = []
        
        # Success rate insights
        if success_rates["overall"] < 90:
            insights.append("Deployment success rate is below optimal threshold. Review failed deployments.")
        
        # Performance insights
        if trends.get("performance_trend") == "degrading":
            insights.append("Deployment performance is degrading. Consider infrastructure optimization.")
        
        # Frequency insights
        if trends.get("deployment_frequency") == "low":
            insights.append("Low deployment frequency detected. Consider increasing automation.")
        
        return insights


# Plugin interface for SIDHE system
async def create_plugin(**kwargs) -> DevOpsAutomatorPlugin:
    """Factory function for creating DevOps Automator plugin instance"""
    return DevOpsAutomatorPlugin(**kwargs)


async def get_plugin_info() -> Dict[str, Any]:
    """Get plugin information for SIDHE plugin registry"""
    return {
        "name": "devops_automator",
        "version": "1.0.0",
        "description": "Enterprise-grade DevOps automation and orchestration",
        "author": "SIDHE Development Team",
        "capabilities": [
            "ci_cd_orchestration",
            "docker_management",
            "infrastructure_monitoring",
            "deployment_automation",
            "quality_gate_integration",
            "rollback_management"
        ],
        "requirements": [
            "docker>=6.0.0",
            "GitPython>=3.1.0",
            "PyGithub>=1.58.0",
            "redis>=4.5.0",
            "psutil>=5.9.0",
            "aiohttp>=3.8.0"
        ],
    }