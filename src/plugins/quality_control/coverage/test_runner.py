"""
Test Runner for Quality Control Plugin

Executes test suites for Python (pytest) and JavaScript (Jest) projects
and provides detailed test results and execution metrics.
"""

import asyncio
import subprocess
import logging
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Results from test execution"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    test_files: List[str]
    failures: List[Dict[str, Any]]
    coverage_data: Optional[Dict[str, Any]]
    exit_code: int

class TestRunner:
    """
    Test execution engine for Python and JavaScript projects
    
    Supports pytest for Python and Jest for JavaScript/TypeScript
    with comprehensive test result analysis and coverage integration.
    """
    
    def __init__(self, config_path: Path):
        """Initialize test runner with configuration"""
        self.config_path = config_path
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
        logger.info("Test runner initialized")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if test runners are available"""
        tools_status = {}
        
        # Check pytest
        try:
            result = await asyncio.create_subprocess_exec(
                'pytest', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            tools_status['pytest'] = {
                'available': result.returncode == 0,
                'version': 'unknown'
            }
        except FileNotFoundError:
            tools_status['pytest'] = {
                'available': False,
                'error': 'Tool not found'
            }
        
        # Check jest (through npm)
        try:
            result = await asyncio.create_subprocess_exec(
                'npm', 'list', 'jest', '--depth=0',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            await result.communicate()
            tools_status['jest'] = {
                'available': result.returncode == 0,
                'version': 'unknown'
            }
        except FileNotFoundError:
            tools_status['jest'] = {
                'available': False,
                'error': 'npm or jest not found'
            }
        
        all_available = any(status['available'] for status in tools_status.values())
        
        return {
            'healthy': all_available,
            'tools': tools_status,
            'project_root': str(self.project_root)
        }
    
    async def run_test_suite(self, scope: str = "all") -> Dict[str, TestResult]:
        """
        Run test suite for specified scope
        
        Args:
            scope: "all", "backend", "frontend", "plugins", or specific path
            
        Returns:
            Dictionary of test results by test type
        """
        logger.info(f"Running test suite for scope: {scope}")
        
        results = {}
        
        # Determine what tests to run based on scope
        if scope in ["all", "backend", "plugins"]:
            # Run Python tests
            python_result = await self._run_python_tests(scope)
            if python_result:
                results['python'] = python_result
        
        if scope in ["all", "frontend"]:
            # Run JavaScript tests
            js_result = await self._run_javascript_tests()
            if js_result:
                results['javascript'] = js_result
        
        return results
    
    async def run_coverage_analysis(self, scope: str = "all") -> Dict[str, Any]:
        """
        Run tests with coverage analysis
        
        Args:
            scope: Test scope to analyze
            
        Returns:
            Coverage analysis results
        """
        logger.info(f"Running coverage analysis for scope: {scope}")
        
        coverage_results = {}
        
        if scope in ["all", "backend", "plugins"]:
            python_coverage = await self._run_python_coverage(scope)
            if python_coverage:
                coverage_results['python'] = python_coverage
        
        if scope in ["all", "frontend"]:
            js_coverage = await self._run_javascript_coverage()
            if js_coverage:
                coverage_results['javascript'] = js_coverage
        
        return coverage_results
    
    async def _run_python_tests(self, scope: str) -> Optional[TestResult]:
        """Run pytest for Python code"""
        try:
            # Determine test path based on scope
            if scope == "backend":
                test_path = "src/conversation_engine/backend/tests"
            elif scope == "plugins":
                test_path = "src/plugins/*/tests"
            else:
                test_path = "src"
            
            cmd = [
                'pytest',
                test_path,
                '--verbose',
                '--tb=short',
                '--junit-xml=test-results.xml'
            ]
            
            start_time = asyncio.get_event_loop().time()
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            stdout, stderr = await process.communicate()
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Parse test results
            result = self._parse_pytest_results(
                stdout.decode() if stdout else "",
                stderr.decode() if stderr else "",
                execution_time,
                process.returncode
            )
            
            logger.info(f"Python tests completed: {result.passed_tests}/{result.total_tests} passed")
            return result
            
        except Exception as e:
            logger.error(f"Python test execution failed: {e}")
            return None
    
    async def _run_javascript_tests(self) -> Optional[TestResult]:
        """Run Jest for JavaScript/TypeScript code"""
        try:
            frontend_path = self.project_root / "src" / "conversation_engine" / "frontend"
            
            if not frontend_path.exists():
                logger.info("No frontend directory found, skipping JavaScript tests")
                return None
            
            cmd = ['npm', 'test', '--', '--watchAll=false', '--verbose']
            
            start_time = asyncio.get_event_loop().time()
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=frontend_path
            )
            
            stdout, stderr = await process.communicate()
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Parse test results
            result = self._parse_jest_results(
                stdout.decode() if stdout else "",
                stderr.decode() if stderr else "",
                execution_time,
                process.returncode
            )
            
            logger.info(f"JavaScript tests completed: {result.passed_tests}/{result.total_tests} passed")
            return result
            
        except Exception as e:
            logger.error(f"JavaScript test execution failed: {e}")
            return None
    
    async def _run_python_coverage(self, scope: str) -> Optional[Dict[str, Any]]:
        """Run pytest with coverage analysis"""
        try:
            test_path = "src" if scope == "all" else f"src/{scope}"
            
            cmd = [
                'pytest',
                test_path,
                '--cov=src',
                '--cov-report=json',
                '--cov-report=html',
                '--quiet'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            stdout, stderr = await process.communicate()
            
            # Read coverage report
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                return coverage_data
            
            return None
            
        except Exception as e:
            logger.error(f"Python coverage analysis failed: {e}")
            return None
    
    async def _run_javascript_coverage(self) -> Optional[Dict[str, Any]]:
        """Run Jest with coverage analysis"""
        try:
            frontend_path = self.project_root / "src" / "conversation_engine" / "frontend"
            
            if not frontend_path.exists():
                return None
            
            cmd = ['npm', 'test', '--', '--coverage', '--watchAll=false']
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=frontend_path
            )
            
            stdout, stderr = await process.communicate()
            
            # Parse coverage from output (Jest outputs coverage to stdout)
            coverage_data = self._parse_jest_coverage(stdout.decode() if stdout else "")
            return coverage_data
            
        except Exception as e:
            logger.error(f"JavaScript coverage analysis failed: {e}")
            return None
    
    def _parse_pytest_results(self, stdout: str, stderr: str, execution_time: float, exit_code: int) -> TestResult:
        """Parse pytest output to extract test results"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        failures = []
        test_files = []
        
        lines = stdout.split('\n')
        for line in lines:
            if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
                total_tests += 1
                file_name = line.split('::')[0]
                if file_name not in test_files:
                    test_files.append(file_name)
                
                if 'PASSED' in line:
                    passed_tests += 1
                elif 'FAILED' in line:
                    failed_tests += 1
                    failures.append({
                        'test': line.split('::')[1] if '::' in line else line,
                        'file': file_name,
                        'message': 'Test failed'
                    })
                elif 'SKIPPED' in line:
                    skipped_tests += 1
        
        return TestResult(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            execution_time=execution_time,
            test_files=test_files,
            failures=failures,
            coverage_data=None,
            exit_code=exit_code
        )
    
    def _parse_jest_results(self, stdout: str, stderr: str, execution_time: float, exit_code: int) -> TestResult:
        """Parse Jest output to extract test results"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        failures = []
        test_files = []
        
        lines = stdout.split('\n')
        for line in lines:
            if 'Tests:' in line:
                # Parse Jest summary line
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if 'passed' in part:
                        passed_tests = int(part.split()[0])
                    elif 'failed' in part:
                        failed_tests = int(part.split()[0])
                    elif 'skipped' in part:
                        skipped_tests = int(part.split()[0])
                    elif 'total' in part:
                        total_tests = int(part.split()[0])
            elif '.test.' in line and ('✓' in line or '✗' in line):
                file_name = line.split()[0] if line.split() else ''
                if file_name and file_name not in test_files:
                    test_files.append(file_name)
        
        return TestResult(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            execution_time=execution_time,
            test_files=test_files,
            failures=failures,
            coverage_data=None,
            exit_code=exit_code
        )
    
    def _parse_jest_coverage(self, output: str) -> Dict[str, Any]:
        """Parse Jest coverage output"""
        coverage_data = {
            'overall_coverage': 0,
            'line_coverage': 0,
            'function_coverage': 0,
            'branch_coverage': 0,
            'files': {}
        }
        
        lines = output.split('\n')
        for line in lines:
            if 'All files' in line and '%' in line:
                # Parse overall coverage line
                parts = line.split('|')
                if len(parts) >= 4:
                    try:
                        coverage_data['line_coverage'] = float(parts[1].strip().replace('%', ''))
                        coverage_data['branch_coverage'] = float(parts[2].strip().replace('%', ''))
                        coverage_data['function_coverage'] = float(parts[3].strip().replace('%', ''))
                        coverage_data['overall_coverage'] = coverage_data['line_coverage']
                    except (ValueError, IndexError):
                        pass
        
        return coverage_data