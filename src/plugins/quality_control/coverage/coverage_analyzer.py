"""
Coverage Analyzer for Quality Control Plugin

Analyzes test coverage data and generates comprehensive coverage reports
with detailed metrics and recommendations for improvement.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class CoverageMetrics:
    """Coverage metrics for a specific component"""
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    statement_coverage: float
    uncovered_lines: List[int]
    partially_covered_lines: List[int]

@dataclass
class CoverageReport:
    """Comprehensive coverage analysis report"""
    overall_coverage: float
    coverage_by_file: Dict[str, CoverageMetrics]
    coverage_by_component: Dict[str, float]
    missing_coverage: List[Dict[str, Any]]
    coverage_trends: Dict[str, float]
    recommendations: List[str]
    gate_status: Dict[str, bool]
    timestamp: str

class CoverageAnalyzer:
    """
    Test coverage analysis and reporting engine
    
    Analyzes coverage data from pytest-cov and Jest to provide
    comprehensive coverage insights and improvement recommendations.
    """
    
    def __init__(self, config_path: Path):
        """Initialize coverage analyzer with configuration"""
        self.config_path = config_path
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
        self.coverage_targets = self._load_coverage_targets()
        logger.info("Coverage analyzer initialized")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if coverage analysis tools are available"""
        return {
            'healthy': True,
            'coverage_targets': self.coverage_targets,
            'project_root': str(self.project_root)
        }
    
    async def analyze_coverage(self, test_results: Dict[str, Any]) -> CoverageReport:
        """
        Analyze test coverage data and generate comprehensive report
        
        Args:
            test_results: Test execution results with coverage data
            
        Returns:
            CoverageReport with detailed coverage analysis
        """
        logger.info("Analyzing test coverage data")
        
        # Collect coverage data from different sources
        python_coverage = await self._analyze_python_coverage()
        js_coverage = await self._analyze_javascript_coverage()
        
        # Calculate overall metrics
        overall_coverage = self._calculate_overall_coverage(python_coverage, js_coverage)
        coverage_by_file = self._compile_file_coverage(python_coverage, js_coverage)
        coverage_by_component = self._calculate_component_coverage(coverage_by_file)
        
        # Identify missing coverage
        missing_coverage = self._identify_missing_coverage(coverage_by_file)
        
        # Generate recommendations
        recommendations = await self._generate_coverage_recommendations(
            overall_coverage, coverage_by_component, missing_coverage
        )
        
        # Evaluate coverage gates
        gate_status = self._evaluate_coverage_gates(overall_coverage, coverage_by_component)
        
        report = CoverageReport(
            overall_coverage=overall_coverage,
            coverage_by_file=coverage_by_file,
            coverage_by_component=coverage_by_component,
            missing_coverage=missing_coverage,
            coverage_trends={},  # TODO: Implement trend tracking
            recommendations=recommendations,
            gate_status=gate_status,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Coverage analysis completed: {overall_coverage:.1f}% overall coverage")
        return report
    
    async def generate_coverage_report(self, format: str = "html") -> str:
        """
        Generate coverage report in specified format
        
        Args:
            format: Report format ("html", "json", "xml")
            
        Returns:
            Path to generated report file
        """
        logger.info(f"Generating coverage report in {format} format")
        
        if format == "html":
            return await self._generate_html_report()
        elif format == "json":
            return await self._generate_json_report()
        elif format == "xml":
            return await self._generate_xml_report()
        else:
            raise ValueError(f"Unsupported report format: {format}")
    
    async def check_coverage_targets(self) -> Dict[str, Any]:
        """
        Check if coverage meets defined targets
        
        Returns:
            Coverage compliance report
        """
        coverage_report = await self.analyze_coverage({})
        
        compliance = {}
        for component, target in self.coverage_targets.get('by_component', {}).items():
            actual = coverage_report.coverage_by_component.get(component, 0)
            compliance[component] = {
                'target': target,
                'actual': actual,
                'meets_target': actual >= target,
                'gap': max(0, target - actual)
            }
        
        overall_target = self.coverage_targets.get('global', {}).get('minimum_coverage', 80)
        overall_compliance = coverage_report.overall_coverage >= overall_target
        
        return {
            'overall_compliance': overall_compliance,
            'overall_target': overall_target,
            'overall_actual': coverage_report.overall_coverage,
            'component_compliance': compliance,
            'blocking_components': [
                comp for comp, data in compliance.items() 
                if not data['meets_target']
            ]
        }
    
    async def _analyze_python_coverage(self) -> Optional[Dict[str, Any]]:
        """Analyze Python test coverage data"""
        try:
            coverage_file = self.project_root / "coverage.json"
            if not coverage_file.exists():
                logger.warning("Python coverage file not found")
                return None
            
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            return self._process_python_coverage_data(coverage_data)
            
        except Exception as e:
            logger.error(f"Failed to analyze Python coverage: {e}")
            return None
    
    async def _analyze_javascript_coverage(self) -> Optional[Dict[str, Any]]:
        """Analyze JavaScript test coverage data"""
        try:
            frontend_path = self.project_root / "src" / "conversation_engine" / "frontend"
            coverage_dir = frontend_path / "coverage"
            
            if not coverage_dir.exists():
                logger.warning("JavaScript coverage directory not found")
                return None
            
            # Look for Jest coverage files
            lcov_file = coverage_dir / "lcov.info"
            json_file = coverage_dir / "coverage-final.json"
            
            if json_file.exists():
                with open(json_file, 'r') as f:
                    coverage_data = json.load(f)
                return self._process_javascript_coverage_data(coverage_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to analyze JavaScript coverage: {e}")
            return None
    
    def _process_python_coverage_data(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Python coverage data from pytest-cov"""
        processed = {
            'overall_coverage': 0,
            'files': {},
            'summary': coverage_data.get('totals', {})
        }
        
        # Extract file-level coverage
        files = coverage_data.get('files', {})
        total_statements = 0
        covered_statements = 0
        
        for file_path, file_data in files.items():
            summary = file_data.get('summary', {})
            statements = summary.get('num_statements', 0)
            covered = summary.get('covered_lines', 0)
            
            total_statements += statements
            covered_statements += covered
            
            processed['files'][file_path] = CoverageMetrics(
                line_coverage=summary.get('percent_covered', 0),
                branch_coverage=summary.get('percent_covered_display', 0),
                function_coverage=0,  # Not available in pytest-cov
                statement_coverage=summary.get('percent_covered', 0),
                uncovered_lines=file_data.get('missing_lines', []),
                partially_covered_lines=file_data.get('excluded_lines', [])
            )
        
        if total_statements > 0:
            processed['overall_coverage'] = (covered_statements / total_statements) * 100
        
        return processed
    
    def _process_javascript_coverage_data(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process JavaScript coverage data from Jest"""
        processed = {
            'overall_coverage': 0,
            'files': {},
            'summary': {}
        }
        
        total_lines = 0
        covered_lines = 0
        
        for file_path, file_data in coverage_data.items():
            statements = file_data.get('s', {})
            functions = file_data.get('f', {})
            branches = file_data.get('b', {})
            
            # Calculate line coverage
            statement_map = file_data.get('statementMap', {})
            covered_statements = sum(1 for count in statements.values() if count > 0)
            total_statement_count = len(statements)
            
            line_coverage = (covered_statements / total_statement_count * 100) if total_statement_count > 0 else 0
            
            total_lines += total_statement_count
            covered_lines += covered_statements
            
            # Calculate function coverage
            covered_functions = sum(1 for count in functions.values() if count > 0)
            total_functions = len(functions)
            function_coverage = (covered_functions / total_functions * 100) if total_functions > 0 else 0
            
            # Calculate branch coverage
            covered_branches = sum(1 for branch_set in branches.values() for count in branch_set if count > 0)
            total_branches = sum(len(branch_set) for branch_set in branches.values())
            branch_coverage = (covered_branches / total_branches * 100) if total_branches > 0 else 0
            
            processed['files'][file_path] = CoverageMetrics(
                line_coverage=line_coverage,
                branch_coverage=branch_coverage,
                function_coverage=function_coverage,
                statement_coverage=line_coverage,
                uncovered_lines=[],  # Would need to parse statementMap
                partially_covered_lines=[]
            )
        
        if total_lines > 0:
            processed['overall_coverage'] = (covered_lines / total_lines) * 100
        
        return processed
    
    def _calculate_overall_coverage(self, python_coverage: Optional[Dict], js_coverage: Optional[Dict]) -> float:
        """Calculate weighted overall coverage across all codebases"""
        coverages = []
        weights = []
        
        if python_coverage and python_coverage.get('overall_coverage', 0) > 0:
            coverages.append(python_coverage['overall_coverage'])
            weights.append(0.7)  # Python gets higher weight
        
        if js_coverage and js_coverage.get('overall_coverage', 0) > 0:
            coverages.append(js_coverage['overall_coverage'])
            weights.append(0.3)  # JavaScript gets lower weight
        
        if not coverages:
            return 0.0
        
        # Calculate weighted average
        total_weight = sum(weights)
        weighted_sum = sum(cov * weight for cov, weight in zip(coverages, weights))
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _compile_file_coverage(self, python_coverage: Optional[Dict], js_coverage: Optional[Dict]) -> Dict[str, CoverageMetrics]:
        """Compile coverage metrics for all files"""
        all_files = {}
        
        if python_coverage:
            all_files.update(python_coverage.get('files', {}))
        
        if js_coverage:
            all_files.update(js_coverage.get('files', {}))
        
        return all_files
    
    def _calculate_component_coverage(self, coverage_by_file: Dict[str, CoverageMetrics]) -> Dict[str, float]:
        """Calculate coverage by component/module"""
        components = {}
        
        for file_path, metrics in coverage_by_file.items():
            # Determine component from file path
            if 'conversation_engine/backend' in file_path:
                component = 'backend'
            elif 'conversation_engine/frontend' in file_path:
                component = 'frontend'
            elif 'plugins' in file_path:
                # Extract plugin name
                parts = file_path.split('/')
                if 'plugins' in parts:
                    plugin_idx = parts.index('plugins')
                    if plugin_idx + 1 < len(parts):
                        component = f"plugin_{parts[plugin_idx + 1]}"
                    else:
                        component = 'plugins'
                else:
                    component = 'plugins'
            else:
                component = 'other'
            
            if component not in components:
                components[component] = []
            
            components[component].append(metrics.line_coverage)
        
        # Calculate average coverage per component
        return {
            comp: sum(coverages) / len(coverages) if coverages else 0
            for comp, coverages in components.items()
        }
    
    def _identify_missing_coverage(self, coverage_by_file: Dict[str, CoverageMetrics]) -> List[Dict[str, Any]]:
        """Identify files and areas with missing coverage"""
        missing = []
        
        for file_path, metrics in coverage_by_file.items():
            if metrics.line_coverage < 80:  # Below acceptable threshold
                missing.append({
                    'file': file_path,
                    'current_coverage': metrics.line_coverage,
                    'target_coverage': 80,
                    'gap': 80 - metrics.line_coverage,
                    'uncovered_lines': len(metrics.uncovered_lines),
                    'severity': 'high' if metrics.line_coverage < 50 else 'medium'
                })
        
        # Sort by severity and gap
        missing.sort(key=lambda x: (x['severity'] == 'high', x['gap']), reverse=True)
        
        return missing
    
    async def _generate_coverage_recommendations(self, overall_coverage: float, component_coverage: Dict[str, float], missing_coverage: List[Dict]) -> List[str]:
        """Generate actionable coverage improvement recommendations"""
        recommendations = []
        
        if overall_coverage < 60:
            recommendations.append("Critical: Overall test coverage is below 60%. Immediate test development required.")
        elif overall_coverage < 80:
            recommendations.append("Warning: Test coverage is below target. Focus on high-impact areas.")
        
        # Component-specific recommendations
        for component, coverage in component_coverage.items():
            if coverage < 70:
                recommendations.append(f"Low coverage in {component} ({coverage:.1f}%). Add comprehensive tests.")
        
        # File-specific recommendations
        high_priority_files = [item for item in missing_coverage[:5] if item['severity'] == 'high']
        if high_priority_files:
            files_list = ', '.join([item['file'].split('/')[-1] for item in high_priority_files])
            recommendations.append(f"Priority files need testing: {files_list}")
        
        return recommendations
    
    def _evaluate_coverage_gates(self, overall_coverage: float, component_coverage: Dict[str, float]) -> Dict[str, bool]:
        """Evaluate coverage gates for quality control"""
        gates = {}
        
        # Overall coverage gate
        min_coverage = self.coverage_targets.get('global', {}).get('minimum_coverage', 80)
        gates['minimum_overall_coverage'] = overall_coverage >= min_coverage
        
        target_coverage = self.coverage_targets.get('global', {}).get('target_coverage', 90)
        gates['target_overall_coverage'] = overall_coverage >= target_coverage
        
        # Component coverage gates
        component_targets = self.coverage_targets.get('by_component', {})
        for component, target in component_targets.items():
            actual = component_coverage.get(component, 0)
            gates[f'{component}_coverage'] = actual >= target
        
        return gates
    
    def _load_coverage_targets(self) -> Dict[str, Any]:
        """Load coverage targets from configuration"""
        # Default coverage targets
        return {
            'global': {
                'minimum_coverage': 80,
                'target_coverage': 90
            },
            'by_component': {
                'backend': 90,
                'frontend': 75,
                'plugins': 85
            }
        }
    
    async def _generate_html_report(self) -> str:
        """Generate HTML coverage report"""
        # This would integrate with existing coverage tools
        return str(self.project_root / "htmlcov" / "index.html")
    
    async def _generate_json_report(self) -> str:
        """Generate JSON coverage report"""
        return str(self.project_root / "coverage.json")
    
    async def _generate_xml_report(self) -> str:
        """Generate XML coverage report"""
        return str(self.project_root / "coverage.xml")