"""
DevOps Automator Plugin Cluster

Provides comprehensive DevOps automation, CI/CD orchestration, Docker management,
infrastructure monitoring, and deployment strategies for the SIDHE ecosystem.

This plugin cluster implements ADR-025 and provides:
- CI/CD pipeline orchestration with GitHub Actions integration
- Docker image management with security scanning and lifecycle automation
- Infrastructure monitoring with real-time health dashboards
- Deployment orchestration supporting blue-green and canary strategies
- Quality gate integration with the Quality Control Plugin
- Real-time DevOps event streaming through Redis message bus
"""

from .main import DevOpsAutomatorPlugin

__version__ = "1.0.0"
__author__ = "SIDHE Development Team"
__description__ = "DevOps Automator Plugin Cluster for enterprise-grade automation"

# Plugin exports
__all__ = [
    "DevOpsAutomatorPlugin",
]