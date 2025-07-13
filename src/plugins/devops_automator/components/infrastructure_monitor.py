"""
Infrastructure Monitor Component

Provides comprehensive infrastructure monitoring, health checking,
metrics collection, and alerting for the SIDHE ecosystem.
"""

import asyncio
import logging
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class InfrastructureMonitor:
    """
    System health monitoring and metrics collection
    
    Provides capabilities for monitoring services, containers, resources,
    generating alerts, and creating real-time dashboards.
    """
    
    def __init__(self, config_path: Path):
        """Initialize Infrastructure Monitor"""
        self.config_path = config_path
        self.monitored_services = {}
        self.alert_history = []
        self.metrics_cache = {}
        self.alert_thresholds = self._load_alert_thresholds()
        
        logger.info("Infrastructure Monitor initialized")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check infrastructure monitor health"""
        try:
            # Check monitoring capabilities
            system_accessible = await self._check_system_access()
            metrics_collection = await self._check_metrics_collection()
            alerting_functional = await self._check_alerting_system()
            
            healthy = system_accessible and metrics_collection and alerting_functional
            
            return {
                "healthy": healthy,
                "system_access": system_accessible,
                "metrics_collection": metrics_collection,
                "alerting_system": alerting_functional,
                "monitored_services": len(self.monitored_services),
                "active_alerts": len([a for a in self.alert_history if a.get("resolved", False) == False])
            }
        except Exception as e:
            logger.error(f"Infrastructure monitor health check failed: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def collect_system_metrics(self, scope: str = "all") -> Dict[str, Any]:
        """
        Collect comprehensive system metrics
        
        Args:
            scope: Metrics scope (all, cpu, memory, disk, network)
            
        Returns:
            System metrics data
        """
        logger.info(f"Collecting system metrics (scope: {scope})")
        
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "scope": scope
            }
            
            if scope in ["all", "cpu"]:
                metrics["cpu"] = await self._collect_cpu_metrics()
            
            if scope in ["all", "memory"]:
                metrics["memory"] = await self._collect_memory_metrics()
            
            if scope in ["all", "disk"]:
                metrics["disk"] = await self._collect_disk_metrics()
            
            if scope in ["all", "network"]:
                metrics["network"] = await self._collect_network_metrics()
            
            if scope in ["all", "processes"]:
                metrics["processes"] = await self._collect_process_metrics()
            
            # Cache metrics for dashboard
            self.metrics_cache[scope] = {
                "data": metrics,
                "collected_at": datetime.now(),
                "ttl_seconds": 60
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "scope": scope,
                "error": str(e)
            }
    
    async def monitor_service_health(self, services: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Monitor health of specified services
        
        Args:
            services: List of service names to monitor (None for all)
            
        Returns:
            Service health status for each service
        """
        logger.info(f"Monitoring service health for {len(services) if services else 'all'} services")
        
        try:
            # Default SIDHE services to monitor
            if services is None:
                services = [
                    "sidhe-conversation-engine",
                    "sidhe-frontend",
                    "redis",
                    "sidhe-plugins"
                ]
            
            service_health = {}
            
            for service_name in services:
                health_data = await self._check_service_health(service_name)
                service_health[service_name] = health_data
                
                # Update monitored services registry
                self.monitored_services[service_name] = {
                    "last_checked": datetime.now().isoformat(),
                    "status": health_data.get("status", "unknown"),
                    "health_score": health_data.get("health_score", 0)
                }
            
            return service_health
            
        except Exception as e:
            logger.error(f"Service health monitoring failed: {e}")
            return {}
    
    async def monitor_container_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Monitor Docker container status and health
        
        Returns:
            Container status for all running containers
        """
        logger.info("Monitoring container status")
        
        try:
            container_status = {}
            
            # Simulate container monitoring
            # In a real implementation, this would use Docker API
            mock_containers = [
                "sidhe-backend",
                "sidhe-frontend", 
                "redis",
                "nginx-proxy"
            ]
            
            for container_name in mock_containers:
                status_data = await self._check_container_status(container_name)
                container_status[container_name] = status_data
            
            return container_status
            
        except Exception as e:
            logger.error(f"Container status monitoring failed: {e}")
            return {}
    
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for system alerts based on thresholds
        
        Returns:
            List of active alerts
        """
        logger.info("Checking for system alerts")
        
        try:
            current_alerts = []
            
            # Collect current metrics for alert evaluation
            current_metrics = await self.collect_system_metrics("all")
            
            # Check CPU alerts
            cpu_alerts = await self._check_cpu_alerts(current_metrics.get("cpu", {}))
            current_alerts.extend(cpu_alerts)
            
            # Check memory alerts
            memory_alerts = await self._check_memory_alerts(current_metrics.get("memory", {}))
            current_alerts.extend(memory_alerts)
            
            # Check disk alerts
            disk_alerts = await self._check_disk_alerts(current_metrics.get("disk", {}))
            current_alerts.extend(disk_alerts)
            
            # Check service alerts
            service_alerts = await self._check_service_alerts()
            current_alerts.extend(service_alerts)
            
            # Add to alert history
            for alert in current_alerts:
                alert["created_at"] = datetime.now().isoformat()
                alert["resolved"] = False
                self.alert_history.append(alert)
            
            # Clean up old resolved alerts
            await self._cleanup_old_alerts()
            
            return current_alerts
            
        except Exception as e:
            logger.error(f"Alert checking failed: {e}")
            return []
    
    async def calculate_resource_usage(self) -> Dict[str, Any]:
        """
        Calculate overall resource usage and capacity
        
        Returns:
            Resource usage summary and projections
        """
        logger.info("Calculating resource usage")
        
        try:
            # Get current system metrics
            cpu_info = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            # Calculate usage percentages
            cpu_usage = cpu_info
            memory_usage = memory_info.percent
            disk_usage = (disk_info.used / disk_info.total) * 100
            
            # Determine capacity status
            cpu_status = self._get_usage_status(cpu_usage, "cpu")
            memory_status = self._get_usage_status(memory_usage, "memory") 
            disk_status = self._get_usage_status(disk_usage, "disk")
            
            # Calculate overall health score
            health_score = (
                (100 - cpu_usage) * 0.3 +
                (100 - memory_usage) * 0.4 +
                (100 - disk_usage) * 0.3
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": round(cpu_usage, 2),
                    "status": cpu_status,
                    "cores": psutil.cpu_count()
                },
                "memory": {
                    "usage_percent": round(memory_usage, 2),
                    "used_gb": round(memory_info.used / (1024**3), 2),
                    "total_gb": round(memory_info.total / (1024**3), 2),
                    "status": memory_status
                },
                "disk": {
                    "usage_percent": round(disk_usage, 2),
                    "used_gb": round(disk_info.used / (1024**3), 2),
                    "total_gb": round(disk_info.total / (1024**3), 2),
                    "status": disk_status
                },
                "overall_health_score": round(health_score, 2),
                "capacity_recommendations": await self._generate_capacity_recommendations(
                    cpu_usage, memory_usage, disk_usage
                )
            }
            
        except Exception as e:
            logger.error(f"Resource usage calculation failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def collect_deployment_metrics(self, timeframe: str = "24h") -> Dict[str, Any]:
        """
        Collect deployment-related metrics
        
        Args:
            timeframe: Time period for metrics (1h, 24h, 7d, 30d)
            
        Returns:
            Deployment metrics data
        """
        logger.info(f"Collecting deployment metrics for timeframe: {timeframe}")
        
        try:
            # Parse timeframe
            hours = self._parse_timeframe_to_hours(timeframe)
            
            # Simulate deployment metrics
            # In a real implementation, this would query deployment history
            metrics = {
                "timeframe": timeframe,
                "total_deployments": 15,
                "successful_deployments": 14,
                "failed_deployments": 1,
                "average_deployment_time_minutes": 8.5,
                "rollback_count": 0,
                "environment_breakdown": {
                    "development": {"deployments": 8, "success_rate": 100},
                    "staging": {"deployments": 4, "success_rate": 100},
                    "production": {"deployments": 3, "success_rate": 67}
                },
                "strategy_breakdown": {
                    "direct": {"deployments": 10, "success_rate": 90},
                    "blue_green": {"deployments": 3, "success_rate": 100},
                    "canary": {"deployments": 2, "success_rate": 100}
                },
                "performance_metrics": {
                    "fastest_deployment_minutes": 3.2,
                    "slowest_deployment_minutes": 15.8,
                    "p95_deployment_time_minutes": 12.1
                },
                "quality_gate_metrics": {
                    "total_quality_checks": 15,
                    "passed_quality_gates": 14,
                    "failed_quality_gates": 1,
                    "average_quality_score": 87.3
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Deployment metrics collection failed: {e}")
            return {
                "timeframe": timeframe,
                "error": str(e)
            }
    
    async def check_deployment_health(self, deployment_id: str, environment: str) -> Dict[str, Any]:
        """
        Check health of a specific deployment
        
        Args:
            deployment_id: ID of deployment to check
            environment: Environment where deployment is running
            
        Returns:
            Deployment health status
        """
        logger.info(f"Checking deployment health: {deployment_id} in {environment}")
        
        try:
            # Simulate deployment health check
            # In a real implementation, this would check actual deployment health
            health_checks = [
                {"name": "application_startup", "status": "healthy", "response_time_ms": 150},
                {"name": "database_connectivity", "status": "healthy", "response_time_ms": 45},
                {"name": "external_api_access", "status": "healthy", "response_time_ms": 230},
                {"name": "health_endpoint", "status": "healthy", "response_time_ms": 25},
                {"name": "load_balancer", "status": "healthy", "response_time_ms": 10}
            ]
            
            all_healthy = all(check["status"] == "healthy" for check in health_checks)
            avg_response_time = sum(check["response_time_ms"] for check in health_checks) / len(health_checks)
            
            return {
                "deployment_id": deployment_id,
                "environment": environment,
                "healthy": all_healthy,
                "overall_status": "healthy" if all_healthy else "degraded",
                "health_checks": health_checks,
                "average_response_time_ms": round(avg_response_time, 2),
                "checked_at": datetime.now().isoformat(),
                "uptime_seconds": 3600,  # Simulate 1 hour uptime
                "request_success_rate": 99.7
            }
            
        except Exception as e:
            logger.error(f"Deployment health check failed: {e}")
            return {
                "deployment_id": deployment_id,
                "environment": environment,
                "healthy": False,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }
    
    # Private helper methods
    
    def _load_alert_thresholds(self) -> Dict[str, Any]:
        """Load alert thresholds from configuration"""
        return {
            "cpu": {"warning": 70, "critical": 85},
            "memory": {"warning": 80, "critical": 90},
            "disk": {"warning": 80, "critical": 90},
            "response_time": {"warning": 1000, "critical": 2000}
        }
    
    async def _check_system_access(self) -> bool:
        """Check if system metrics are accessible"""
        try:
            psutil.cpu_percent()
            psutil.virtual_memory()
            return True
        except Exception:
            return False
    
    async def _check_metrics_collection(self) -> bool:
        """Check if metrics collection is functional"""
        try:
            await self._collect_cpu_metrics()
            return True
        except Exception:
            return False
    
    async def _check_alerting_system(self) -> bool:
        """Check if alerting system is functional"""
        return True  # Alerting is always functional in this implementation
    
    async def _collect_cpu_metrics(self) -> Dict[str, Any]:
        """Collect CPU metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        return {
            "usage_percent": cpu_percent,
            "cores": cpu_count,
            "frequency_mhz": cpu_freq.current if cpu_freq else 0,
            "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0.0, 0.0, 0.0]
        }
    
    async def _collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory metrics"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "usage_percent": memory.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_gb": round(swap.used / (1024**3), 2),
            "swap_percent": swap.percent
        }
    
    async def _collect_disk_metrics(self) -> Dict[str, Any]:
        """Collect disk metrics"""
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        return {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "usage_percent": round((disk.used / disk.total) * 100, 2),
            "read_mb": round(disk_io.read_bytes / (1024**2), 2) if disk_io else 0,
            "write_mb": round(disk_io.write_bytes / (1024**2), 2) if disk_io else 0
        }
    
    async def _collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network metrics"""
        net_io = psutil.net_io_counters()
        
        return {
            "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errors_in": net_io.errin,
            "errors_out": net_io.errout,
            "drops_in": net_io.dropin,
            "drops_out": net_io.dropout
        }
    
    async def _collect_process_metrics(self) -> Dict[str, Any]:
        """Collect process metrics"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage and get top 10
        top_processes = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
        
        return {
            "total_processes": len(processes),
            "top_cpu_processes": top_processes,
            "zombie_processes": len([p for p in processes if p.get('status') == 'zombie'])
        }
    
    async def _check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service"""
        # Simulate service health check
        await asyncio.sleep(0.1)
        
        # Mock different service statuses
        import hashlib
        service_hash = int(hashlib.md5(service_name.encode()).hexdigest()[:8], 16) % 4
        
        if service_hash == 0:
            return {
                "status": "healthy",
                "health_score": 95,
                "response_time_ms": 50,
                "uptime_hours": 72,
                "last_restart": "2025-07-10T10:30:00Z",
                "memory_usage_mb": 150,
                "cpu_usage_percent": 5.2
            }
        elif service_hash == 1:
            return {
                "status": "warning",
                "health_score": 75,
                "response_time_ms": 850,
                "uptime_hours": 24,
                "last_restart": "2025-07-11T14:15:00Z",
                "memory_usage_mb": 280,
                "cpu_usage_percent": 12.8,
                "warnings": ["High response time", "Memory usage increasing"]
            }
        elif service_hash == 2:
            return {
                "status": "critical",
                "health_score": 30,
                "response_time_ms": 2500,
                "uptime_hours": 2,
                "last_restart": "2025-07-12T08:00:00Z",
                "memory_usage_mb": 450,
                "cpu_usage_percent": 25.1,
                "errors": ["Service restarting frequently", "High error rate"]
            }
        else:
            return {
                "status": "unknown",
                "health_score": 0,
                "error": "Unable to connect to service"
            }
    
    async def _check_container_status(self, container_name: str) -> Dict[str, Any]:
        """Check status of a specific container"""
        # Simulate container status check
        await asyncio.sleep(0.1)
        
        return {
            "status": "running",
            "health": "healthy",
            "uptime": "2d 14h 32m",
            "restart_count": 0,
            "memory_usage_mb": 180,
            "cpu_usage_percent": 3.5,
            "image": f"sidhe/{container_name}:latest",
            "ports": ["8000:8000"] if "backend" in container_name else ["3000:3000"],
            "volumes": ["/data:/app/data"],
            "last_health_check": datetime.now().isoformat()
        }
    
    async def _check_cpu_alerts(self, cpu_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for CPU-related alerts"""
        alerts = []
        cpu_usage = cpu_metrics.get("usage_percent", 0)
        
        if cpu_usage >= self.alert_thresholds["cpu"]["critical"]:
            alerts.append({
                "type": "cpu",
                "severity": "critical",
                "message": f"CPU usage is critically high: {cpu_usage:.1f}%",
                "value": cpu_usage,
                "threshold": self.alert_thresholds["cpu"]["critical"]
            })
        elif cpu_usage >= self.alert_thresholds["cpu"]["warning"]:
            alerts.append({
                "type": "cpu",
                "severity": "warning",
                "message": f"CPU usage is high: {cpu_usage:.1f}%",
                "value": cpu_usage,
                "threshold": self.alert_thresholds["cpu"]["warning"]
            })
        
        return alerts
    
    async def _check_memory_alerts(self, memory_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for memory-related alerts"""
        alerts = []
        memory_usage = memory_metrics.get("usage_percent", 0)
        
        if memory_usage >= self.alert_thresholds["memory"]["critical"]:
            alerts.append({
                "type": "memory",
                "severity": "critical",
                "message": f"Memory usage is critically high: {memory_usage:.1f}%",
                "value": memory_usage,
                "threshold": self.alert_thresholds["memory"]["critical"]
            })
        elif memory_usage >= self.alert_thresholds["memory"]["warning"]:
            alerts.append({
                "type": "memory",
                "severity": "warning",
                "message": f"Memory usage is high: {memory_usage:.1f}%",
                "value": memory_usage,
                "threshold": self.alert_thresholds["memory"]["warning"]
            })
        
        return alerts
    
    async def _check_disk_alerts(self, disk_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for disk-related alerts"""
        alerts = []
        disk_usage = disk_metrics.get("usage_percent", 0)
        
        if disk_usage >= self.alert_thresholds["disk"]["critical"]:
            alerts.append({
                "type": "disk",
                "severity": "critical",
                "message": f"Disk usage is critically high: {disk_usage:.1f}%",
                "value": disk_usage,
                "threshold": self.alert_thresholds["disk"]["critical"]
            })
        elif disk_usage >= self.alert_thresholds["disk"]["warning"]:
            alerts.append({
                "type": "disk",
                "severity": "warning",
                "message": f"Disk usage is high: {disk_usage:.1f}%",
                "value": disk_usage,
                "threshold": self.alert_thresholds["disk"]["warning"]
            })
        
        return alerts
    
    async def _check_service_alerts(self) -> List[Dict[str, Any]]:
        """Check for service-related alerts"""
        alerts = []
        
        for service_name, service_info in self.monitored_services.items():
            if service_info.get("status") == "critical":
                alerts.append({
                    "type": "service",
                    "severity": "critical",
                    "message": f"Service {service_name} is in critical state",
                    "service": service_name,
                    "health_score": service_info.get("health_score", 0)
                })
            elif service_info.get("status") == "warning":
                alerts.append({
                    "type": "service",
                    "severity": "warning",
                    "message": f"Service {service_name} is showing warnings",
                    "service": service_name,
                    "health_score": service_info.get("health_score", 0)
                })
        
        return alerts
    
    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        self.alert_history = [
            alert for alert in self.alert_history
            if not alert.get("resolved", False) or 
            datetime.fromisoformat(alert.get("created_at", "")) > cutoff_time
        ]
    
    def _get_usage_status(self, usage_percent: float, resource_type: str) -> str:
        """Get usage status based on thresholds"""
        thresholds = self.alert_thresholds.get(resource_type, {"warning": 70, "critical": 90})
        
        if usage_percent >= thresholds["critical"]:
            return "critical"
        elif usage_percent >= thresholds["warning"]:
            return "warning"
        else:
            return "healthy"
    
    async def _generate_capacity_recommendations(self, cpu_usage: float, memory_usage: float, disk_usage: float) -> List[str]:
        """Generate capacity planning recommendations"""
        recommendations = []
        
        if cpu_usage > 70:
            recommendations.append("Consider scaling CPU resources or optimizing CPU-intensive processes")
        
        if memory_usage > 75:
            recommendations.append("Monitor memory usage trends and consider increasing available memory")
        
        if disk_usage > 80:
            recommendations.append("Disk space is getting low - consider cleanup or expansion")
        
        if not recommendations:
            recommendations.append("Resource usage is within normal parameters")
        
        return recommendations
    
    def _parse_timeframe_to_hours(self, timeframe: str) -> int:
        """Parse timeframe string to hours"""
        if timeframe.endswith('h'):
            return int(timeframe[:-1])
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 24
        else:
            return 24  # Default to 24 hours