"""
Python Linting Engine

Provides comprehensive Python code linting using black, flake8, and mypy.
Implements automated formatting, style checking, and type validation.
"""

import asyncio
import subprocess
import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LintResult:
    """Results from Python linting operations"""
    files_checked: int
    errors: int
    warnings: int
    issues: List[Dict[str, Any]]
    formatted_files: List[str]
    execution_time: float
    tools_used: List[str]

class PythonLinter:
    """
    Python code linting and formatting engine
    
    Integrates black (formatting), flake8 (style), and mypy (types)
    to provide comprehensive Python code quality assurance.
    """
    
    def __init__(self, config_path: Path):
        """Initialize Python linter with configuration"""
        self.config_path = config_path
        self.tools = {
            'black': self._get_black_config(),
            'flake8': self._get_flake8_config(),
            'mypy': self._get_mypy_config()
        }
        logger.info("Python linter initialized")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Python linting tools are available"""
        tools_status = {}
        
        for tool in ['black', 'flake8', 'mypy']:
            try:
                result = await asyncio.create_subprocess_exec(
                    tool, '--version',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                tools_status[tool] = {
                    'available': result.returncode == 0,
                    'version': 'unknown'
                }
            except FileNotFoundError:
                tools_status[tool] = {
                    'available': False,
                    'error': 'Tool not found'
                }
        
        all_available = all(status['available'] for status in tools_status.values())
        
        return {
            'healthy': all_available,
            'tools': tools_status,
            'config_path': str(self.config_path)
        }
    
    async def lint_files(self, files: List[str]) -> LintResult:
        """
        Run complete Python linting on specified files
        
        Args:
            files: List of Python file paths to lint
            
        Returns:
            LintResult with comprehensive linting analysis
        """
        start_time = asyncio.get_event_loop().time()
        python_files = [f for f in files if f.endswith('.py') and Path(f).exists()]
        
        if not python_files:
            return LintResult(
                files_checked=0,
                errors=0,
                warnings=0,
                issues=[],
                formatted_files=[],
                execution_time=0,
                tools_used=[]
            )
        
        logger.info(f"Linting {len(python_files)} Python files")
        
        # Run linting tools in parallel
        tasks = [
            self._run_black(python_files),
            self._run_flake8(python_files),
            self._run_mypy(python_files)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        black_result, flake8_result, mypy_result = results
        
        # Compile results
        all_issues = []
        formatted_files = []
        tools_used = []
        
        # Process black results
        if isinstance(black_result, dict):
            formatted_files.extend(black_result.get('formatted_files', []))
            all_issues.extend(black_result.get('issues', []))
            if black_result.get('executed'):
                tools_used.append('black')
        
        # Process flake8 results
        if isinstance(flake8_result, dict):
            all_issues.extend(flake8_result.get('issues', []))
            if flake8_result.get('executed'):
                tools_used.append('flake8')
        
        # Process mypy results
        if isinstance(mypy_result, dict):
            all_issues.extend(mypy_result.get('issues', []))
            if mypy_result.get('executed'):
                tools_used.append('mypy')
        
        # Calculate error/warning counts
        errors = len([issue for issue in all_issues if issue.get('severity') == 'error'])
        warnings = len([issue for issue in all_issues if issue.get('severity') == 'warning'])
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        result = LintResult(
            files_checked=len(python_files),
            errors=errors,
            warnings=warnings,
            issues=all_issues,
            formatted_files=formatted_files,
            execution_time=execution_time,
            tools_used=tools_used
        )
        
        logger.info(f"Python linting completed: {errors} errors, {warnings} warnings")
        return result
    
    async def format_files(self, files: List[str]) -> Dict[str, Any]:
        """Format Python files using black"""
        python_files = [f for f in files if f.endswith('.py') and Path(f).exists()]
        
        if not python_files:
            return {'formatted_files': [], 'errors': []}
        
        return await self._run_black(python_files, check_only=False)
    
    async def _run_black(self, files: List[str], check_only: bool = True) -> Dict[str, Any]:
        """Run black formatter on Python files"""
        try:
            cmd = ['black']
            if check_only:
                cmd.append('--check')
            cmd.append('--diff')
            cmd.extend(files)
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            stdout_text = stdout.decode() if stdout else ""
            stderr_text = stderr.decode() if stderr else ""
            
            issues = []
            formatted_files = []
            
            if process.returncode != 0:
                # Parse black output for formatting issues
                if "would reformat" in stdout_text:
                    lines = stdout_text.split('\n')
                    for line in lines:
                        if "would reformat" in line:
                            file_path = line.split("would reformat ")[1] if "would reformat " in line else ""
                            if file_path:
                                issues.append({
                                    'file': file_path,
                                    'line': 0,
                                    'severity': 'warning',
                                    'description': 'File requires formatting',
                                    'tool': 'black'
                                })
                                if not check_only:
                                    formatted_files.append(file_path)
            
            return {
                'executed': True,
                'issues': issues,
                'formatted_files': formatted_files,
                'stdout': stdout_text,
                'stderr': stderr_text
            }
            
        except Exception as e:
            logger.error(f"Black execution failed: {e}")
            return {
                'executed': False,
                'error': str(e),
                'issues': [],
                'formatted_files': []
            }
    
    async def _run_flake8(self, files: List[str]) -> Dict[str, Any]:
        """Run flake8 linter on Python files"""
        try:
            cmd = ['flake8', '--format=json'] + files
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            stdout_text = stdout.decode() if stdout else ""
            stderr_text = stderr.decode() if stderr else ""
            
            issues = []
            
            # Parse flake8 output
            if stdout_text:
                try:
                    # Try to parse as JSON first
                    flake8_results = json.loads(stdout_text)
                    for result in flake8_results:
                        issues.append({
                            'file': result.get('filename', ''),
                            'line': result.get('line_number', 0),
                            'column': result.get('column_number', 0),
                            'severity': 'error' if result.get('code', '').startswith('E') else 'warning',
                            'description': f"{result.get('code', '')}: {result.get('text', '')}",
                            'tool': 'flake8'
                        })
                except json.JSONDecodeError:
                    # Fallback to parsing standard flake8 output
                    lines = stdout_text.split('\n')
                    for line in lines:
                        if ':' in line and line.strip():
                            parts = line.split(':')
                            if len(parts) >= 4:
                                issues.append({
                                    'file': parts[0],
                                    'line': int(parts[1]) if parts[1].isdigit() else 0,
                                    'column': int(parts[2]) if parts[2].isdigit() else 0,
                                    'severity': 'error',
                                    'description': ':'.join(parts[3:]).strip(),
                                    'tool': 'flake8'
                                })
            
            return {
                'executed': True,
                'issues': issues,
                'stdout': stdout_text,
                'stderr': stderr_text
            }
            
        except Exception as e:
            logger.error(f"Flake8 execution failed: {e}")
            return {
                'executed': False,
                'error': str(e),
                'issues': []
            }
    
    async def _run_mypy(self, files: List[str]) -> Dict[str, Any]:
        """Run mypy type checker on Python files"""
        try:
            cmd = ['mypy', '--show-error-codes', '--no-error-summary'] + files
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            stdout_text = stdout.decode() if stdout else ""
            stderr_text = stderr.decode() if stderr else ""
            
            issues = []
            
            # Parse mypy output
            if stdout_text:
                lines = stdout_text.split('\n')
                for line in lines:
                    if ':' in line and line.strip():
                        parts = line.split(':')
                        if len(parts) >= 3:
                            issues.append({
                                'file': parts[0],
                                'line': int(parts[1]) if parts[1].isdigit() else 0,
                                'severity': 'error' if 'error:' in line else 'warning',
                                'description': ':'.join(parts[2:]).strip(),
                                'tool': 'mypy'
                            })
            
            return {
                'executed': True,
                'issues': issues,
                'stdout': stdout_text,
                'stderr': stderr_text
            }
            
        except Exception as e:
            logger.error(f"Mypy execution failed: {e}")
            return {
                'executed': False,
                'error': str(e),
                'issues': []
            }
    
    def _get_black_config(self) -> Dict[str, Any]:
        """Get black formatting configuration"""
        return {
            'line_length': 88,
            'target_version': ['py311'],
            'include': r'\.pyi?$',
            'extend_exclude': r'/(migrations|node_modules|\.git)/'
        }
    
    def _get_flake8_config(self) -> Dict[str, Any]:
        """Get flake8 linting configuration"""
        return {
            'max_line_length': 88,
            'extend_ignore': ['E203', 'W503'],
            'max_complexity': 10,
            'exclude': ['.git', '__pycache__', 'migrations', 'node_modules']
        }
    
    def _get_mypy_config(self) -> Dict[str, Any]:
        """Get mypy type checking configuration"""
        return {
            'python_version': '3.11',
            'warn_return_any': True,
            'warn_unused_configs': True,
            'disallow_untyped_defs': True,
            'ignore_missing_imports': True
        }