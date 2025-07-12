"""
Quality Scorer for Quality Control Plugin

Calculates comprehensive quality metrics and overall quality scores
based on linting results, test coverage, code complexity, and standards compliance.
"""

import ast
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Quality metrics for code analysis"""
    complexity_score: float
    maintainability_score: float
    documentation_score: float
    standards_compliance: float
    security_score: float
    overall_score: float

@dataclass
class FileQualityMetrics:
    """Quality metrics for individual files"""
    file_path: str
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    function_count: int
    class_count: int
    docstring_coverage: float
    comment_ratio: float
    duplicate_lines: int
    quality_score: float

class QualityScorer:
    """
    Code quality analysis and scoring engine
    
    Analyzes code complexity, maintainability, documentation coverage,
    and standards compliance to provide comprehensive quality scoring.
    """
    
    def __init__(self, config_path: Path):
        """Initialize quality scorer with configuration"""
        self.config_path = config_path
        self.quality_standards = self._load_quality_standards()
        logger.info("Quality scorer initialized")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if quality scoring is operational"""
        return {
            'healthy': True,
            'quality_standards': self.quality_standards,
            'supported_languages': ['python', 'javascript']
        }
    
    async def calculate_overall_score(self, linting_results: Dict, coverage_results: Dict, metrics_results: Dict) -> float:
        """
        Calculate overall quality score based on all quality factors
        
        Args:
            linting_results: Results from linting analysis
            coverage_results: Results from coverage analysis
            metrics_results: Results from metrics analysis
            
        Returns:
            Overall quality score (0-100)
        """
        logger.info("Calculating overall quality score")
        
        # Weight factors for overall score
        weights = {
            'linting': 0.3,      # 30% weight for linting compliance
            'coverage': 0.25,    # 25% weight for test coverage
            'complexity': 0.2,   # 20% weight for code complexity
            'documentation': 0.15, # 15% weight for documentation
            'standards': 0.1     # 10% weight for standards compliance
        }
        
        scores = {}
        
        # Calculate linting score
        scores['linting'] = self._calculate_linting_score(linting_results)
        
        # Calculate coverage score
        scores['coverage'] = self._calculate_coverage_score(coverage_results)
        
        # Calculate complexity score
        scores['complexity'] = self._calculate_complexity_score(metrics_results)
        
        # Calculate documentation score
        scores['documentation'] = self._calculate_documentation_score(metrics_results)
        
        # Calculate standards compliance score
        scores['standards'] = self._calculate_standards_score(linting_results, metrics_results)
        
        # Calculate weighted overall score
        overall_score = sum(scores[factor] * weights[factor] for factor in weights.keys())
        
        logger.info(f"Overall quality score calculated: {overall_score:.1f}")
        return min(100.0, max(0.0, overall_score))
    
    async def calculate_metrics(self, files: List[str]) -> Dict[str, Any]:
        """
        Calculate detailed quality metrics for specified files
        
        Args:
            files: List of file paths to analyze
            
        Returns:
            Comprehensive quality metrics
        """
        logger.info(f"Calculating quality metrics for {len(files)} files")
        
        file_metrics = []
        overall_metrics = {
            'total_files': len(files),
            'total_lines': 0,
            'total_functions': 0,
            'total_classes': 0,
            'average_complexity': 0,
            'documentation_coverage': 0,
            'issues': []
        }
        
        python_files = [f for f in files if f.endswith('.py')]
        js_files = [f for f in files if f.endswith(('.js', '.jsx', '.ts', '.tsx'))]
        
        # Analyze Python files
        for file_path in python_files:
            metrics = await self._analyze_python_file(file_path)
            if metrics:
                file_metrics.append(metrics)
                overall_metrics['total_lines'] += metrics.lines_of_code
                overall_metrics['total_functions'] += metrics.function_count
                overall_metrics['total_classes'] += metrics.class_count
        
        # Analyze JavaScript files
        for file_path in js_files:
            metrics = await self._analyze_javascript_file(file_path)
            if metrics:
                file_metrics.append(metrics)
                overall_metrics['total_lines'] += metrics.lines_of_code
                overall_metrics['total_functions'] += metrics.function_count
                overall_metrics['total_classes'] += metrics.class_count
        
        # Calculate aggregate metrics
        if file_metrics:
            overall_metrics['average_complexity'] = sum(m.cyclomatic_complexity for m in file_metrics) / len(file_metrics)
            overall_metrics['documentation_coverage'] = sum(m.docstring_coverage for m in file_metrics) / len(file_metrics)
        
        # Identify quality issues
        overall_metrics['issues'] = self._identify_quality_issues(file_metrics)
        
        return {
            'file_metrics': [m.__dict__ for m in file_metrics],
            'overall_metrics': overall_metrics,
            'quality_score': self._calculate_aggregate_quality_score(file_metrics)
        }
    
    async def quick_assessment(self, files: List[str]) -> Dict[str, Any]:
        """
        Perform quick quality assessment for incremental checks
        
        Args:
            files: List of changed files to assess
            
        Returns:
            Quick quality assessment
        """
        logger.info(f"Performing quick assessment on {len(files)} files")
        
        python_files = [f for f in files if f.endswith('.py')]
        js_files = [f for f in files if f.endswith(('.js', '.jsx', '.ts', '.tsx'))]
        
        issues = []
        total_score = 0
        file_count = 0
        
        # Quick analysis of Python files
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic complexity check
                tree = ast.parse(content)
                complexity = self._calculate_cyclomatic_complexity(tree)
                
                if complexity > 10:
                    issues.append({
                        'type': 'complexity',
                        'file': file_path,
                        'severity': 'high' if complexity > 15 else 'medium',
                        'description': f'High cyclomatic complexity: {complexity}'
                    })
                
                # Basic scoring
                file_score = max(0, 100 - (complexity * 2))
                total_score += file_score
                file_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Quick analysis of JavaScript files
        for file_path in js_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic metrics
                lines = len(content.split('\n'))
                functions = content.count('function ') + content.count('=> ')
                
                if lines > 500:
                    issues.append({
                        'type': 'size',
                        'file': file_path,
                        'severity': 'medium',
                        'description': f'Large file: {lines} lines'
                    })
                
                # Basic scoring
                file_score = max(0, 100 - (lines * 0.1))
                total_score += file_score
                file_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        average_score = total_score / file_count if file_count > 0 else 0
        
        return {
            'score': average_score,
            'files_analyzed': file_count,
            'issues': issues,
            'assessment_type': 'quick'
        }
    
    async def _analyze_python_file(self, file_path: str) -> Optional[FileQualityMetrics]:
        """Analyze quality metrics for a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # Basic metrics
            lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            function_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            class_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
            
            # Complexity metrics
            cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)
            cognitive_complexity = self._calculate_cognitive_complexity(tree)
            
            # Documentation metrics
            docstring_coverage = self._calculate_docstring_coverage(tree)
            comment_ratio = self._calculate_comment_ratio(content)
            
            # Quality score
            quality_score = self._calculate_file_quality_score(
                cyclomatic_complexity, cognitive_complexity, docstring_coverage, comment_ratio
            )
            
            return FileQualityMetrics(
                file_path=file_path,
                lines_of_code=lines_of_code,
                cyclomatic_complexity=cyclomatic_complexity,
                cognitive_complexity=cognitive_complexity,
                function_count=function_count,
                class_count=class_count,
                docstring_coverage=docstring_coverage,
                comment_ratio=comment_ratio,
                duplicate_lines=0,  # TODO: Implement duplicate detection
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze Python file {file_path}: {e}")
            return None
    
    async def _analyze_javascript_file(self, file_path: str) -> Optional[FileQualityMetrics]:
        """Analyze quality metrics for a JavaScript/TypeScript file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Basic metrics
            lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
            function_count = content.count('function ') + content.count('=> ') + content.count('function(')
            class_count = content.count('class ')
            
            # Simple complexity estimation
            cyclomatic_complexity = self._estimate_js_complexity(content)
            cognitive_complexity = cyclomatic_complexity  # Simplified
            
            # Documentation metrics
            docstring_coverage = self._calculate_js_documentation_coverage(content)
            comment_ratio = self._calculate_js_comment_ratio(content)
            
            # Quality score
            quality_score = self._calculate_file_quality_score(
                cyclomatic_complexity, cognitive_complexity, docstring_coverage, comment_ratio
            )
            
            return FileQualityMetrics(
                file_path=file_path,
                lines_of_code=lines_of_code,
                cyclomatic_complexity=cyclomatic_complexity,
                cognitive_complexity=cognitive_complexity,
                function_count=function_count,
                class_count=class_count,
                docstring_coverage=docstring_coverage,
                comment_ratio=comment_ratio,
                duplicate_lines=0,
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze JavaScript file {file_path}: {e}")
            return None
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity for Python AST"""
        complexity = 1  # Start with 1 for the initial path
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """Calculate cognitive complexity for Python AST"""
        # Simplified cognitive complexity calculation
        complexity = 0
        nesting_level = 0
        
        class CognitiveComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 0
                self.nesting = 0
            
            def visit_If(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1
            
            def visit_While(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1
            
            def visit_For(self, node):
                self.complexity += 1 + self.nesting
                self.nesting += 1
                self.generic_visit(node)
                self.nesting -= 1
        
        visitor = CognitiveComplexityVisitor()
        visitor.visit(tree)
        return visitor.complexity
    
    def _calculate_docstring_coverage(self, tree: ast.AST) -> float:
        """Calculate docstring coverage for Python AST"""
        functions_and_classes = []
        documented = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                functions_and_classes.append(node)
                
                # Check if first statement is a string (docstring)
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    documented += 1
        
        return (documented / len(functions_and_classes) * 100) if functions_and_classes else 0
    
    def _calculate_comment_ratio(self, content: str) -> float:
        """Calculate comment ratio for Python code"""
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        
        return (comment_lines / total_lines * 100) if total_lines > 0 else 0
    
    def _estimate_js_complexity(self, content: str) -> int:
        """Estimate complexity for JavaScript/TypeScript code"""
        complexity = 1
        
        # Count decision points
        complexity += content.count('if ')
        complexity += content.count('while ')
        complexity += content.count('for ')
        complexity += content.count('switch ')
        complexity += content.count('catch ')
        complexity += content.count('&&')
        complexity += content.count('||')
        complexity += content.count('?')  # Ternary operator
        
        return complexity
    
    def _calculate_js_documentation_coverage(self, content: str) -> float:
        """Calculate documentation coverage for JavaScript/TypeScript"""
        # Simple heuristic: look for JSDoc comments
        functions = content.count('function ') + content.count('=> ')
        jsdoc_comments = content.count('/**')
        
        return (jsdoc_comments / functions * 100) if functions > 0 else 0
    
    def _calculate_js_comment_ratio(self, content: str) -> float:
        """Calculate comment ratio for JavaScript/TypeScript"""
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith('//') or line.strip().startswith('*')])
        
        return (comment_lines / total_lines * 100) if total_lines > 0 else 0
    
    def _calculate_file_quality_score(self, cyclomatic_complexity: int, cognitive_complexity: int, 
                                    docstring_coverage: float, comment_ratio: float) -> float:
        """Calculate overall quality score for a file"""
        score = 100
        
        # Penalize high complexity
        if cyclomatic_complexity > 10:
            score -= (cyclomatic_complexity - 10) * 5
        
        if cognitive_complexity > 15:
            score -= (cognitive_complexity - 15) * 3
        
        # Reward good documentation
        if docstring_coverage < 80:
            score -= (80 - docstring_coverage) * 0.5
        
        if comment_ratio < 10:
            score -= (10 - comment_ratio) * 2
        
        return max(0, min(100, score))
    
    def _calculate_linting_score(self, linting_results: Dict) -> float:
        """Calculate score based on linting results"""
        if not linting_results:
            return 50  # Neutral score if no linting data
        
        total_issues = 0
        error_weight = 5
        warning_weight = 2
        
        for lang_results in linting_results.values():
            if isinstance(lang_results, dict):
                total_issues += lang_results.get('errors', 0) * error_weight
                total_issues += lang_results.get('warnings', 0) * warning_weight
        
        # Score decreases with more issues
        score = max(0, 100 - total_issues)
        return score
    
    def _calculate_coverage_score(self, coverage_results: Dict) -> float:
        """Calculate score based on test coverage"""
        overall_coverage = coverage_results.get('overall_coverage', 0)
        return overall_coverage  # Coverage percentage directly maps to score
    
    def _calculate_complexity_score(self, metrics_results: Dict) -> float:
        """Calculate score based on code complexity"""
        if not metrics_results or 'overall_metrics' not in metrics_results:
            return 70  # Neutral score
        
        avg_complexity = metrics_results['overall_metrics'].get('average_complexity', 0)
        
        # Good complexity (1-5): 100-90
        # Acceptable complexity (6-10): 89-70
        # High complexity (11-20): 69-40
        # Very high complexity (>20): <40
        
        if avg_complexity <= 5:
            return 100 - (avg_complexity * 2)
        elif avg_complexity <= 10:
            return 90 - ((avg_complexity - 5) * 4)
        elif avg_complexity <= 20:
            return 70 - ((avg_complexity - 10) * 3)
        else:
            return max(0, 40 - ((avg_complexity - 20) * 2))
    
    def _calculate_documentation_score(self, metrics_results: Dict) -> float:
        """Calculate score based on documentation coverage"""
        if not metrics_results or 'overall_metrics' not in metrics_results:
            return 50  # Neutral score
        
        doc_coverage = metrics_results['overall_metrics'].get('documentation_coverage', 0)
        return doc_coverage  # Documentation percentage directly maps to score
    
    def _calculate_standards_score(self, linting_results: Dict, metrics_results: Dict) -> float:
        """Calculate score based on coding standards compliance"""
        # Combine linting compliance and code quality metrics
        linting_score = self._calculate_linting_score(linting_results)
        complexity_score = self._calculate_complexity_score(metrics_results)
        
        # Weighted average
        return (linting_score * 0.7) + (complexity_score * 0.3)
    
    def _identify_quality_issues(self, file_metrics: List[FileQualityMetrics]) -> List[Dict[str, Any]]:
        """Identify quality issues from file metrics"""
        issues = []
        
        for metrics in file_metrics:
            if metrics.cyclomatic_complexity > 10:
                issues.append({
                    'type': 'complexity',
                    'severity': 'high' if metrics.cyclomatic_complexity > 15 else 'medium',
                    'file': metrics.file_path,
                    'description': f'High cyclomatic complexity: {metrics.cyclomatic_complexity}',
                    'metric': 'cyclomatic_complexity',
                    'value': metrics.cyclomatic_complexity
                })
            
            if metrics.cognitive_complexity > 15:
                issues.append({
                    'type': 'complexity',
                    'severity': 'high' if metrics.cognitive_complexity > 25 else 'medium',
                    'file': metrics.file_path,
                    'description': f'High cognitive complexity: {metrics.cognitive_complexity}',
                    'metric': 'cognitive_complexity',
                    'value': metrics.cognitive_complexity
                })
            
            if metrics.docstring_coverage < 50:
                issues.append({
                    'type': 'documentation',
                    'severity': 'medium',
                    'file': metrics.file_path,
                    'description': f'Low documentation coverage: {metrics.docstring_coverage:.1f}%',
                    'metric': 'docstring_coverage',
                    'value': metrics.docstring_coverage
                })
            
            if metrics.lines_of_code > 500:
                issues.append({
                    'type': 'size',
                    'severity': 'medium',
                    'file': metrics.file_path,
                    'description': f'Large file: {metrics.lines_of_code} lines',
                    'metric': 'lines_of_code',
                    'value': metrics.lines_of_code
                })
        
        return issues
    
    def _calculate_aggregate_quality_score(self, file_metrics: List[FileQualityMetrics]) -> float:
        """Calculate aggregate quality score from file metrics"""
        if not file_metrics:
            return 0
        
        total_score = sum(metrics.quality_score for metrics in file_metrics)
        return total_score / len(file_metrics)
    
    def _load_quality_standards(self) -> Dict[str, Any]:
        """Load quality standards configuration"""
        return {
            'complexity': {
                'cyclomatic_threshold': 10,
                'cognitive_threshold': 15
            },
            'documentation': {
                'minimum_coverage': 80,
                'public_api_coverage': 95
            },
            'maintainability': {
                'max_file_size': 500,
                'max_function_length': 50
            }
        }