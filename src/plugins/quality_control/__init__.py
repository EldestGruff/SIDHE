"""
Quality Control Plugin Cluster

Provides comprehensive code quality assurance, testing coverage analysis,
linting, and standards enforcement for the SIDHE ecosystem.

This plugin cluster implements ADR-024 and provides:
- Automated code linting for Python and JavaScript
- Test coverage analysis and reporting
- Code quality metrics and scoring
- Integration with Git hooks and SIDHE dashboard
- Quality gates for quest completion
"""

from .main import QualityControlPlugin

__version__ = "1.0.0"
__author__ = "SIDHE Development Team"
__description__ = "Quality Control Plugin Cluster for automated code quality assurance"

# Plugin exports
__all__ = [
    "QualityControlPlugin",
]