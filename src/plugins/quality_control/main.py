"""
Quality Control Plugin - Main Implementation

Central orchestrator for code quality assurance operations including linting,
test coverage analysis, quality metrics, and integration with SIDHE systems.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

from .linting.python_linter import PythonLinter
from .linting.javascript_linter import JavaScriptLinter
from .coverage.test_runner import TestRunner
from .coverage.coverage_analyzer import CoverageAnalyzer
from .metrics.quality_scorer import QualityScorer
from .integration.dashboard_integration import DashboardIntegration

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """Comprehensive quality assessment report"""

    timestamp: str
    overall_score: float
    linting_results: Dict[str, Any]
    coverage_results: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    gate_status: Dict[str, bool]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QualityStatus:
    """Current quality control system status"""

    enabled: bool
    last_check: Optional[str]
    overall_score: Optional[float]
    components_healthy: Dict[str, bool]
    active_issues: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class QualityControlPlugin:
    """
    Quality Control Plugin - ADR-024 Implementation

    Provides comprehensive code quality assurance through:
    - Automated linting (Python: black, flake8, mypy; JS: eslint, prettier)
    - Test coverage analysis and reporting
    - Code quality metrics and scoring
    - Integration with Git hooks and SIDHE dashboard
    - Quality gates for quest completion
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize Quality Control Plugin"""
        self.plugin_name = "quality_control"
        self.version = "1.0.0"
        self.config_path = config_path or Path(__file__).parent / "config"

        # Initialize components
        self.python_linter = PythonLinter(self.config_path)
        self.js_linter = JavaScriptLinter(self.config_path)
        self.test_runner = TestRunner(self.config_path)
        self.coverage_analyzer = CoverageAnalyzer(self.config_path)
        self.quality_scorer = QualityScorer(self.config_path)
        self.dashboard = DashboardIntegration()

        # Plugin state
        self.enabled = True
        self.last_check = None
        self.current_status = None

        logger.info(f"Quality Control Plugin v{self.version} initialized")

    async def health_check(self) -> Dict[str, Any]:
        """Plugin health check for SIDHE monitoring"""
        try:
            # Check component health
            components = {
                "python_linter": await self.python_linter.health_check(),
                "js_linter": await self.js_linter.health_check(),
                "test_runner": await self.test_runner.health_check(),
                "coverage_analyzer": await self.coverage_analyzer.health_check(),
                "quality_scorer": await self.quality_scorer.health_check(),
            }

            all_healthy = all(
                comp.get("healthy", False) for comp in components.values()
            )

            return {
                "plugin": self.plugin_name,
                "version": self.version,
                "healthy": all_healthy,
                "status": "operational" if all_healthy else "degraded",
                "components": components,
                "last_check": datetime.now().isoformat(),
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

    async def run_full_quality_check(self, scope: str = "all") -> QualityReport:
        """
        Run comprehensive quality check on specified scope

        Args:
            scope: "all", "backend", "frontend", "plugins", or specific path

        Returns:
            QualityReport with complete analysis results
        """
        logger.info(f"Starting full quality check (scope: {scope})")
        start_time = datetime.now()

        try:
            # Determine files to analyze based on scope
            files_to_check = await self._get_files_for_scope(scope)

            # Run parallel quality checks
            tasks = [
                self._run_linting_checks(files_to_check),
                self._run_coverage_analysis(scope),
                self._run_quality_metrics(files_to_check),
            ]

            linting_results, coverage_results, metrics_results = await asyncio.gather(
                *tasks
            )

            # Calculate overall quality score
            overall_score = await self.quality_scorer.calculate_overall_score(
                linting_results, coverage_results, metrics_results
            )

            # Compile issues and recommendations
            issues = self._compile_issues(
                linting_results, coverage_results, metrics_results
            )
            recommendations = await self._generate_recommendations(
                issues, overall_score
            )

            # Evaluate quality gates
            gate_status = await self._evaluate_quality_gates(
                overall_score, coverage_results
            )

            # Create comprehensive report
            report = QualityReport(
                timestamp=start_time.isoformat(),
                overall_score=overall_score,
                linting_results=linting_results,
                coverage_results=coverage_results,
                quality_metrics=metrics_results,
                issues=issues,
                recommendations=recommendations,
                gate_status=gate_status,
            )

            # Update plugin status
            self.last_check = start_time.isoformat()
            self.current_status = report

            # Update dashboard
            await self.dashboard.update_quality_status(report)

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Quality check completed in {duration:.2f}s (score: {overall_score:.1f})"
            )

            return report

        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            raise

    async def run_incremental_check(self, changed_files: List[str]) -> QualityReport:
        """
        Run quality check on specific changed files for faster feedback

        Args:
            changed_files: List of file paths that have changed

        Returns:
            QualityReport for changed files only
        """
        logger.info(f"Running incremental quality check on {len(changed_files)} files")

        # Filter files by type
        python_files = [f for f in changed_files if f.endswith((".py",))]
        js_files = [
            f for f in changed_files if f.endswith((".js", ".jsx", ".ts", ".tsx"))
        ]

        # Run targeted checks
        linting_results = {}
        if python_files:
            python_result = await self.python_linter.lint_files(python_files)
            linting_results["python"] = python_result
        if js_files:
            js_result = await self.js_linter.lint_files(js_files)
            linting_results["javascript"] = js_result

        # Quick quality assessment
        quality_metrics = await self.quality_scorer.quick_assessment(changed_files)

        # Create focused report
        report = QualityReport(
            timestamp=datetime.now().isoformat(),
            overall_score=quality_metrics.get("score", 0),
            linting_results=linting_results,
            coverage_results={},  # Not calculated for incremental
            quality_metrics=quality_metrics,
            issues=self._compile_issues(linting_results, {}, quality_metrics),
            recommendations=[],
            gate_status={},
        )

        return report

    async def get_quality_status(self) -> QualityStatus:
        """Get current quality control system status"""
        components_healthy = {}

        if self.enabled:
            health_check = await self.health_check()
            components_healthy = {
                comp: details.get("healthy", False)
                for comp, details in health_check.get("components", {}).items()
            }

        return QualityStatus(
            enabled=self.enabled,
            last_check=self.last_check,
            overall_score=(
                self.current_status.overall_score if self.current_status else None
            ),
            components_healthy=components_healthy,
            active_issues=len(self.current_status.issues) if self.current_status else 0,
        )

    async def enforce_quality_gates(self, quest_id: str) -> Dict[str, Any]:
        """
        Enforce quality gates for quest completion

        Args:
            quest_id: The quest being evaluated

        Returns:
            Gate evaluation results
        """
        logger.info(f"Evaluating quality gates for quest {quest_id}")

        # Run full quality check
        quality_report = await self.run_full_quality_check()

        # Evaluate gates
        gates = {
            "overall_score": quality_report.overall_score >= 85.0,
            "linting_compliance": self._check_linting_compliance(
                quality_report.linting_results
            ),
            "coverage_threshold": self._check_coverage_threshold(
                quality_report.coverage_results
            ),
            "no_critical_issues": len(
                [i for i in quality_report.issues if i.get("severity") == "critical"]
            )
            == 0,
        }

        all_gates_passed = all(gates.values())

        result = {
            "quest_id": quest_id,
            "gates_passed": all_gates_passed,
            "gate_details": gates,
            "overall_score": quality_report.overall_score,
            "blocking_issues": [
                i
                for i in quality_report.issues
                if i.get("severity") in ["critical", "high"]
            ],
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Quality gates for {quest_id}: {'PASSED' if all_gates_passed else 'FAILED'}"
        )
        return result

    # Private helper methods

    async def _get_files_for_scope(self, scope: str) -> List[str]:
        """Get list of files to analyze based on scope"""
        if scope == "all":
            return await self._get_all_source_files()
        elif scope == "backend":
            return await self._get_backend_files()
        elif scope == "frontend":
            return await self._get_frontend_files()
        elif scope == "plugins":
            return await self._get_plugin_files()
        else:
            # Assume it's a specific path
            return [scope] if Path(scope).exists() else []

    async def _get_all_source_files(self) -> List[str]:
        """Get all source files in the project"""
        project_root = Path(__file__).parent.parent.parent.parent
        files = []

        # Python files
        for pattern in ["**/*.py"]:
            files.extend(
                [
                    str(f)
                    for f in project_root.glob(pattern)
                    if not self._should_ignore_file(f)
                ]
            )

        # JavaScript/TypeScript files
        for pattern in ["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx"]:
            files.extend(
                [
                    str(f)
                    for f in project_root.glob(pattern)
                    if not self._should_ignore_file(f)
                ]
            )

        return files

    async def _get_backend_files(self) -> List[str]:
        """Get backend source files"""
        backend_path = (
            Path(__file__).parent.parent.parent / "conversation_engine" / "backend"
        )
        return [
            str(f)
            for f in backend_path.glob("**/*.py")
            if not self._should_ignore_file(f)
        ]

    async def _get_frontend_files(self) -> List[str]:
        """Get frontend source files"""
        frontend_path = (
            Path(__file__).parent.parent.parent / "conversation_engine" / "frontend"
        )
        files = []
        for pattern in ["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx"]:
            files.extend(
                [
                    str(f)
                    for f in frontend_path.glob(pattern)
                    if not self._should_ignore_file(f)
                ]
            )
        return files

    async def _get_plugin_files(self) -> List[str]:
        """Get plugin source files"""
        plugins_path = Path(__file__).parent.parent
        return [
            str(f)
            for f in plugins_path.glob("**/*.py")
            if not self._should_ignore_file(f)
        ]

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored in quality checks"""
        ignore_patterns = [
            "node_modules",
            "__pycache__",
            ".git",
            ".pytest_cache",
            "build",
            "dist",
            "coverage",
            ".coverage",
        ]
        return any(pattern in str(file_path) for pattern in ignore_patterns)

    async def _run_linting_checks(self, files: List[str]) -> Dict[str, Any]:
        """Run linting checks on specified files"""
        results = {}

        # Separate files by type
        python_files = [f for f in files if f.endswith(".py")]
        js_files = [f for f in files if f.endswith((".js", ".jsx", ".ts", ".tsx"))]

        # Run linting in parallel
        tasks = []
        if python_files:
            tasks.append(self.python_linter.lint_files(python_files))
        if js_files:
            tasks.append(self.js_linter.lint_files(js_files))

        if tasks:
            lint_results = await asyncio.gather(*tasks)
            if python_files:
                results["python"] = lint_results[0]
            if js_files:
                results["javascript"] = (
                    lint_results[-1]
                    if js_files
                    else lint_results[1] if len(lint_results) > 1 else {}
                )

        return results

    async def _run_coverage_analysis(self, scope: str) -> Dict[str, Any]:
        """Run test coverage analysis"""
        # Run tests and analyze coverage
        test_results = await self.test_runner.run_test_suite(scope)
        coverage_results = await self.coverage_analyzer.analyze_coverage(test_results)

        return coverage_results

    async def _run_quality_metrics(self, files: List[str]) -> Dict[str, Any]:
        """Calculate quality metrics for files"""
        return await self.quality_scorer.calculate_metrics(files)

    def _compile_issues(
        self, linting_results: Dict, coverage_results: Dict, metrics_results: Dict
    ) -> List[Dict[str, Any]]:
        """Compile all issues from different quality checks"""
        issues = []

        # Add linting issues
        for lang, results in linting_results.items():
            # Handle both dict and LintResult objects
            if hasattr(results, "issues"):
                issues_list = results.issues
            elif isinstance(results, dict):
                issues_list = results.get("issues", [])
            else:
                issues_list = []

            for issue in issues_list:
                issues.append(
                    {
                        "type": "linting",
                        "language": lang,
                        "severity": issue.get("severity", "medium"),
                        "description": issue.get("description", ""),
                        "file": issue.get("file", ""),
                        "line": issue.get("line", 0),
                    }
                )

        # Add coverage issues
        coverage_issues = coverage_results.get("issues", [])
        for issue in coverage_issues:
            issues.append(
                {
                    "type": "coverage",
                    "severity": issue.get("severity", "medium"),
                    "description": issue.get("description", ""),
                    "file": issue.get("file", ""),
                    "coverage": issue.get("coverage", 0),
                }
            )

        # Add quality metric issues
        metrics_issues = metrics_results.get("issues", [])
        for issue in metrics_issues:
            issues.append(
                {
                    "type": "quality",
                    "severity": issue.get("severity", "medium"),
                    "description": issue.get("description", ""),
                    "metric": issue.get("metric", ""),
                    "value": issue.get("value", 0),
                }
            )

        return issues

    async def _generate_recommendations(
        self, issues: List[Dict], overall_score: float
    ) -> List[str]:
        """Generate actionable recommendations based on issues"""
        recommendations = []

        # Score-based recommendations
        if overall_score < 60:
            recommendations.append(
                "Critical: Overall quality score is below acceptable threshold. Immediate attention required."
            )
        elif overall_score < 80:
            recommendations.append(
                "Warning: Quality score needs improvement. Focus on high-impact issues."
            )

        # Issue-type specific recommendations
        issue_types = {}
        for issue in issues:
            issue_type = issue["type"]
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        if issue_types.get("linting", 0) > 10:
            recommendations.append(
                "High number of linting issues. Run automated formatting tools."
            )

        if issue_types.get("coverage", 0) > 0:
            recommendations.append(
                "Test coverage is below target. Add tests for uncovered code paths."
            )

        if issue_types.get("quality", 0) > 5:
            recommendations.append(
                "Code complexity issues detected. Consider refactoring complex functions."
            )

        return recommendations

    async def _evaluate_quality_gates(
        self, overall_score: float, coverage_results: Dict
    ) -> Dict[str, bool]:
        """Evaluate quality gates for pass/fail decisions"""
        return {
            "minimum_score": overall_score >= 75.0,
            "target_score": overall_score >= 85.0,
            "coverage_threshold": coverage_results.get("overall_coverage", 0) >= 80.0,
            "critical_issues": (
                len(
                    [
                        i
                        for i in self.current_status.issues
                        if i.get("severity") == "critical"
                    ]
                )
                == 0
                if self.current_status
                else True
            ),
        }

    def _check_linting_compliance(self, linting_results: Dict) -> bool:
        """Check if linting compliance meets standards"""
        for lang_results in linting_results.values():
            if lang_results.get("errors", 0) > 0:
                return False
        return True

    def _check_coverage_threshold(self, coverage_results: Dict) -> bool:
        """Check if coverage meets minimum threshold"""
        return coverage_results.get("overall_coverage", 0) >= 80.0


# Plugin interface for SIDHE system
async def create_plugin(**kwargs) -> QualityControlPlugin:
    """Factory function for creating Quality Control plugin instance"""
    return QualityControlPlugin(**kwargs)


async def get_plugin_info() -> Dict[str, Any]:
    """Get plugin information for SIDHE plugin registry"""
    return {
        "name": "quality_control",
        "version": "1.0.0",
        "description": "Comprehensive code quality assurance and standards enforcement",
        "author": "SIDHE Development Team",
        "capabilities": [
            "code_linting",
            "test_coverage",
            "quality_metrics",
            "git_integration",
            "dashboard_integration",
        ],
        "requirements": [
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pytest>=7.0.0",
            "coverage>=7.0.0",
        ],
    }
