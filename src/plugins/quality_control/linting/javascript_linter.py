"""
JavaScript/TypeScript Linting Engine

Provides comprehensive JavaScript and TypeScript code linting using eslint and prettier.
Implements automated formatting, style checking, and best practices enforcement.
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
    """Results from JavaScript/TypeScript linting operations"""
    files_checked: int
    errors: int
    warnings: int
    issues: List[Dict[str, Any]]
    formatted_files: List[str]
    execution_time: float
    tools_used: List[str]

class JavaScriptLinter:
    """
    JavaScript/TypeScript code linting and formatting engine
    
    Integrates eslint (linting) and prettier (formatting)
    to provide comprehensive JavaScript/TypeScript code quality assurance.
    """
    
    def __init__(self, config_path: Path):
        """Initialize JavaScript linter with configuration"""
        self.config_path = config_path
        self.tools = {
            'eslint': self._get_eslint_config(),
            'prettier': self._get_prettier_config()
        }
        logger.info("JavaScript linter initialized")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if JavaScript linting tools are available"""
        tools_status = {}
        
        for tool in ['eslint', 'prettier']:
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
        Run complete JavaScript/TypeScript linting on specified files
        
        Args:
            files: List of JS/TS file paths to lint
            
        Returns:
            LintResult with comprehensive linting analysis
        """
        start_time = asyncio.get_event_loop().time()
        js_files = [f for f in files if f.endswith(('.js', '.jsx', '.ts', '.tsx')) and Path(f).exists()]
        
        if not js_files:
            return LintResult(
                files_checked=0,
                errors=0,
                warnings=0,
                issues=[],
                formatted_files=[],
                execution_time=0,
                tools_used=[]
            )
        
        logger.info(f"Linting {len(js_files)} JavaScript/TypeScript files")
        
        # Run linting tools in parallel
        tasks = [
            self._run_eslint(js_files),
            self._run_prettier(js_files)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        eslint_result, prettier_result = results
        
        # Compile results
        all_issues = []
        formatted_files = []
        tools_used = []
        
        # Process eslint results
        if isinstance(eslint_result, dict):
            all_issues.extend(eslint_result.get('issues', []))
            if eslint_result.get('executed'):
                tools_used.append('eslint')
        
        # Process prettier results
        if isinstance(prettier_result, dict):
            formatted_files.extend(prettier_result.get('formatted_files', []))
            all_issues.extend(prettier_result.get('issues', []))
            if prettier_result.get('executed'):
                tools_used.append('prettier')
        
        # Calculate error/warning counts
        errors = len([issue for issue in all_issues if issue.get('severity') == 'error'])
        warnings = len([issue for issue in all_issues if issue.get('severity') == 'warning'])
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        result = LintResult(
            files_checked=len(js_files),
            errors=errors,
            warnings=warnings,
            issues=all_issues,
            formatted_files=formatted_files,
            execution_time=execution_time,
            tools_used=tools_used
        )
        
        logger.info(f"JavaScript linting completed: {errors} errors, {warnings} warnings")
        return result
    
    async def format_files(self, files: List[str]) -> Dict[str, Any]:
        """Format JavaScript/TypeScript files using prettier"""
        js_files = [f for f in files if f.endswith(('.js', '.jsx', '.ts', '.tsx')) and Path(f).exists()]
        
        if not js_files:
            return {'formatted_files': [], 'errors': []}
        
        return await self._run_prettier(js_files, check_only=False)
    
    async def _run_eslint(self, files: List[str]) -> Dict[str, Any]:
        """Run eslint linter on JavaScript/TypeScript files"""
        try:
            cmd = ['eslint', '--format=json'] + files
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            stdout_text = stdout.decode() if stdout else ""
            stderr_text = stderr.decode() if stderr else ""
            
            issues = []
            
            # Parse eslint JSON output
            if stdout_text:
                try:
                    eslint_results = json.loads(stdout_text)
                    for file_result in eslint_results:
                        for message in file_result.get('messages', []):
                            issues.append({
                                'file': file_result.get('filePath', ''),
                                'line': message.get('line', 0),
                                'column': message.get('column', 0),
                                'severity': 'error' if message.get('severity') == 2 else 'warning',
                                'description': f"{message.get('ruleId', '')}: {message.get('message', '')}",
                                'tool': 'eslint'
                            })
                except json.JSONDecodeError:
                    logger.warning("Failed to parse eslint JSON output")
            
            return {
                'executed': True,
                'issues': issues,
                'stdout': stdout_text,
                'stderr': stderr_text
            }
            
        except Exception as e:
            logger.error(f"ESLint execution failed: {e}")
            return {
                'executed': False,
                'error': str(e),
                'issues': []
            }
    
    async def _run_prettier(self, files: List[str], check_only: bool = True) -> Dict[str, Any]:
        """Run prettier formatter on JavaScript/TypeScript files"""
        try:
            cmd = ['prettier']
            if check_only:
                cmd.append('--check')
            else:
                cmd.append('--write')
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
            
            if process.returncode != 0 and check_only:
                # Parse prettier output for formatting issues
                lines = stderr_text.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('['):
                        issues.append({
                            'file': line.strip(),
                            'line': 0,
                            'severity': 'warning',
                            'description': 'File requires formatting',
                            'tool': 'prettier'
                        })
            elif not check_only and process.returncode == 0:
                # Files were formatted successfully
                formatted_files = files
            
            return {
                'executed': True,
                'issues': issues,
                'formatted_files': formatted_files,
                'stdout': stdout_text,
                'stderr': stderr_text
            }
            
        except Exception as e:
            logger.error(f"Prettier execution failed: {e}")
            return {
                'executed': False,
                'error': str(e),
                'issues': [],
                'formatted_files': []
            }
    
    def _get_eslint_config(self) -> Dict[str, Any]:
        """Get eslint linting configuration"""
        return {
            'extends': ['@typescript-eslint/recommended'],
            'rules': {
                'no-unused-vars': 'error',
                'prefer-const': 'error',
                'no-console': 'warn',
                '@typescript-eslint/no-explicit-any': 'warn'
            },
            'parser': '@typescript-eslint/parser',
            'plugins': ['@typescript-eslint']
        }
    
    def _get_prettier_config(self) -> Dict[str, Any]:
        """Get prettier formatting configuration"""
        return {
            'tabWidth': 2,
            'semi': True,
            'singleQuote': True,
            'trailingComma': 'es5',
            'bracketSpacing': True,
            'arrowParens': 'avoid'
        }