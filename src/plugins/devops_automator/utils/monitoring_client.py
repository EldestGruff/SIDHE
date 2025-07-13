"""
Monitoring Client Utility

Infrastructure monitoring client providing metrics collection,
alerting, and integration with monitoring systems.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MonitoringClient:
    """
    Infrastructure monitoring client for metrics and alerting
    
    Provides capabilities for metrics collection, alerting,
    dashboard integration, and monitoring system coordination.
    """
    
    def __init__(self, monitoring_config):
        """Initialize monitoring client"""
        self.config = monitoring_config
        # Handle both dict and MonitoringConfig object
        if hasattr(monitoring_config, 'metrics_endpoint'):
            self.metrics_endpoint = monitoring_config.metrics_endpoint
            self.alerting_endpoint = monitoring_config.alerting_endpoint
            self.dashboard_url = monitoring_config.dashboard_url
            self.collection_interval = monitoring_config.collection_interval
        else:
            self.metrics_endpoint = monitoring_config.get("metrics_endpoint")
            self.alerting_endpoint = monitoring_config.get("alerting_endpoint") 
            self.dashboard_url = monitoring_config.get("dashboard_url")
            self.collection_interval = monitoring_config.get("collection_interval", 60)
        
        logger.info("Monitoring client initialized")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check monitoring systems health"""
        try:
            # Simulate monitoring systems health check
            await asyncio.sleep(0.1)
            
            return {
                "healthy": True,
                "metrics_system": True,
                "alerting_system": True,
                "dashboard_accessible": True,
                "collection_interval_seconds": self.collection_interval,
                "last_metrics_collection": datetime.now().isoformat(),
                "active_alerts": 2,
                "total_metrics": 847
            }
        except Exception as e:
            logger.error(f"Monitoring health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def collect_application_metrics(self, applications: List[str]) -> Dict[str, Any]:
        """
        Collect application-specific metrics
        
        Args:
            applications: List of applications to monitor
            
        Returns:
            Application metrics data
        """
        logger.info(f"Collecting metrics for {len(applications)} applications")
        
        try:
            # Simulate metrics collection
            await asyncio.sleep(0.3)
            
            metrics_data = {}
            
            for app in applications:
                metrics_data[app] = await self._collect_app_metrics(app)
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "applications": applications,
                "metrics": metrics_data,
                "collection_time_seconds": 0.3
            }
            
        except Exception as e:
            logger.error(f"Application metrics collection failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "applications": applications
            }
    
    async def send_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send alert to monitoring system
        
        Args:
            alert: Alert data to send
            
        Returns:
            Alert sending results
        """
        logger.info(f"Sending alert: {alert.get('type', 'unknown')} - {alert.get('severity', 'unknown')}")
        
        try:
            # Simulate alert sending
            await asyncio.sleep(0.2)
            
            alert_id = f"alert-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            return {
                "success": True,
                "alert_id": alert_id,
                "alert_type": alert.get("type", "unknown"),
                "severity": alert.get("severity", "unknown"),
                "message": alert.get("message", ""),
                "sent_at": datetime.now().isoformat(),
                "delivery_channels": ["email", "slack", "webhook"],
                "acknowledged": False
            }
            
        except Exception as e:
            logger.error(f"Alert sending failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "alert_data": alert
            }
    
    async def query_metrics(self, query: str, time_range: str = "1h") -> Dict[str, Any]:
        """
        Query metrics from monitoring system
        
        Args:
            query: Metrics query (PromQL-like syntax)
            time_range: Time range for query
            
        Returns:
            Query results
        """
        logger.info(f"Querying metrics: {query} (range: {time_range})")
        
        try:
            # Simulate metrics query
            await asyncio.sleep(0.2)
            
            # Generate mock time series data
            data_points = await self._generate_mock_timeseries(query, time_range)
            
            return {
                "success": True,
                "query": query,
                "time_range": time_range,
                "data_points": len(data_points),
                "data": data_points,
                "queried_at": datetime.now().isoformat(),
                "execution_time_ms": 200
            }
            
        except Exception as e:
            logger.error(f"Metrics query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def create_dashboard(self, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create monitoring dashboard
        
        Args:
            dashboard_config: Dashboard configuration
            
        Returns:
            Dashboard creation results
        """
        logger.info(f"Creating dashboard: {dashboard_config.get('name', 'unnamed')}")
        
        try:
            # Simulate dashboard creation
            await asyncio.sleep(0.4)
            
            dashboard_id = f"dashboard-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            return {
                "success": True,
                "dashboard_id": dashboard_id,
                "name": dashboard_config.get("name", "SIDHE Dashboard"),
                "panels": len(dashboard_config.get("panels", [])),
                "refresh_interval": dashboard_config.get("refresh_interval", "30s"),
                "created_at": datetime.now().isoformat(),
                "dashboard_url": f"{self.dashboard_url}/d/{dashboard_id}",
                "public": dashboard_config.get("public", False)
            }
            
        except Exception as e:
            logger.error(f"Dashboard creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "dashboard_config": dashboard_config
            }
    
    async def get_alert_rules(self) -> Dict[str, Any]:
        """
        Get configured alert rules
        
        Returns:
            List of alert rules
        """
        logger.info("Getting alert rules")
        
        try:
            # Simulate alert rules retrieval
            await asyncio.sleep(0.1)
            
            alert_rules = [
                {
                    "rule_id": "cpu-high",
                    "name": "High CPU Usage",
                    "query": "cpu_usage_percent > 80",
                    "severity": "warning",
                    "threshold": 80,
                    "duration": "5m",
                    "enabled": True,
                    "last_triggered": "2025-07-12T09:15:00Z"
                },
                {
                    "rule_id": "memory-critical",
                    "name": "Critical Memory Usage",
                    "query": "memory_usage_percent > 90",
                    "severity": "critical",
                    "threshold": 90,
                    "duration": "2m",
                    "enabled": True,
                    "last_triggered": None
                },
                {
                    "rule_id": "disk-space-low",
                    "name": "Low Disk Space",
                    "query": "disk_usage_percent > 85",
                    "severity": "warning",
                    "threshold": 85,
                    "duration": "10m",
                    "enabled": True,
                    "last_triggered": None
                },
                {
                    "rule_id": "service-down",
                    "name": "Service Unavailable",
                    "query": "service_up == 0",
                    "severity": "critical",
                    "threshold": 0,
                    "duration": "1m",
                    "enabled": True,
                    "last_triggered": None
                }
            ]
            
            return {
                "success": True,
                "total_rules": len(alert_rules),
                "enabled_rules": len([r for r in alert_rules if r["enabled"]]),
                "rules": alert_rules,
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Alert rules retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_alert_rule(self, rule_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update alert rule configuration
        
        Args:
            rule_id: ID of rule to update
            updates: Updates to apply
            
        Returns:
            Update results
        """
        logger.info(f"Updating alert rule: {rule_id}")
        
        try:
            # Simulate rule update
            await asyncio.sleep(0.1)
            
            return {
                "success": True,
                "rule_id": rule_id,
                "updates_applied": updates,
                "updated_at": datetime.now().isoformat(),
                "version": "v2",
                "enabled": updates.get("enabled", True)
            }
            
        except Exception as e:
            logger.error(f"Alert rule update failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "rule_id": rule_id
            }
    
    async def get_active_alerts(self) -> Dict[str, Any]:
        """
        Get currently active alerts
        
        Returns:
            List of active alerts
        """
        logger.info("Getting active alerts")
        
        try:
            # Simulate active alerts retrieval
            await asyncio.sleep(0.1)
            
            active_alerts = [
                {
                    "alert_id": "alert-001",
                    "rule_id": "cpu-high",
                    "severity": "warning",
                    "message": "CPU usage is high on sidhe-backend: 82%",
                    "started_at": "2025-07-12T10:15:00Z",
                    "duration_minutes": 25,
                    "affected_services": ["sidhe-backend"],
                    "acknowledged": False,
                    "silenced": False
                },
                {
                    "alert_id": "alert-002", 
                    "rule_id": "response-time-high",
                    "severity": "warning",
                    "message": "Response time increased on /api/plugins endpoint: 1.2s",
                    "started_at": "2025-07-12T10:30:00Z",
                    "duration_minutes": 10,
                    "affected_services": ["sidhe-backend"],
                    "acknowledged": True,
                    "silenced": False
                }
            ]
            
            return {
                "success": True,
                "total_active_alerts": len(active_alerts),
                "critical_alerts": len([a for a in active_alerts if a["severity"] == "critical"]),
                "warning_alerts": len([a for a in active_alerts if a["severity"] == "warning"]),
                "alerts": active_alerts,
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Active alerts retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def acknowledge_alert(self, alert_id: str, acknowledgment_note: str = "") -> Dict[str, Any]:
        """
        Acknowledge an active alert
        
        Args:
            alert_id: ID of alert to acknowledge
            acknowledgment_note: Optional note about acknowledgment
            
        Returns:
            Acknowledgment results
        """
        logger.info(f"Acknowledging alert: {alert_id}")
        
        try:
            # Simulate alert acknowledgment
            await asyncio.sleep(0.1)
            
            return {
                "success": True,
                "alert_id": alert_id,
                "acknowledged": True,
                "acknowledged_at": datetime.now().isoformat(),
                "acknowledged_by": "DevOps Automator Plugin",
                "acknowledgment_note": acknowledgment_note,
                "auto_resolve": False
            }
            
        except Exception as e:
            logger.error(f"Alert acknowledgment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "alert_id": alert_id
            }
    
    # Private helper methods
    
    async def _collect_app_metrics(self, app_name: str) -> Dict[str, Any]:
        """Collect metrics for a specific application"""
        # Simulate app-specific metrics collection
        await asyncio.sleep(0.1)
        
        import random
        base_cpu = random.uniform(5, 25)
        base_memory = random.uniform(100, 400)
        base_requests = random.randint(10, 100)
        
        return {
            "cpu_usage_percent": round(base_cpu, 2),
            "memory_usage_mb": round(base_memory, 2),
            "requests_per_minute": base_requests,
            "response_time_ms": round(random.uniform(50, 200), 2),
            "error_rate_percent": round(random.uniform(0.1, 2.0), 2),
            "uptime_seconds": random.randint(3600, 86400),
            "active_connections": random.randint(5, 50),
            "disk_io_mb": round(random.uniform(1, 10), 2),
            "network_io_mb": round(random.uniform(0.5, 5), 2),
            "last_updated": datetime.now().isoformat()
        }
    
    async def _generate_mock_timeseries(self, query: str, time_range: str) -> List[Dict[str, Any]]:
        """Generate mock time series data for queries"""
        # Parse time range
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
        elif time_range.endswith('d'):
            hours = int(time_range[:-1]) * 24
        else:
            hours = 1
        
        # Generate data points (one per minute)
        data_points = []
        now = datetime.now()
        
        import random
        base_value = 50 if "cpu" in query else 200 if "memory" in query else 80
        
        for i in range(hours * 60):
            timestamp = now - timedelta(minutes=i)
            value = base_value + random.uniform(-10, 10) + (random.random() - 0.5) * 20
            
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "value": round(max(0, value), 2),
                "metric": query.split()[0] if " " in query else query
            })
        
        return list(reversed(data_points))  # Reverse to get chronological order