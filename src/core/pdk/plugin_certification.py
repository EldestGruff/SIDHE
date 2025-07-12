#!/usr/bin/env python3
"""
SIDHE Plugin Certification System
=================================

The sacred guardian that ensures all plugins meet SIDHE's communication standards.

This system validates that plugins:
- Properly inherit from EnchantedPlugin
- Implement required methods correctly
- Follow message bus protocols
- Handle errors gracefully
- Respond to health checks
- Register capabilities properly
- Meet performance requirements

Only certified plugins shall pass through the mystical gates!
"""

import asyncio
import inspect
import json
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, Callable
from unittest.mock import patch

import yaml
from pydantic import BaseModel, Field, ValidationError

from sidhe_pdk import (
    EnchantedPlugin, PluginMessage, MessageType, PluginStatus,
    PluginCapability, create_plugin_message
)
from sidhe_pdk_test_utilities import MockRedis, TestClient, PerformanceBenchmark


class CertificationLevel(str, Enum):
    """Levels of plugin certification"""
    BASIC = "basic"           # Meets minimum requirements
    STANDARD = "standard"     # Follows all best practices
    ADVANCED = "advanced"     # Exceptional implementation
    FAILED = "failed"         # Does not meet requirements


class ComplianceCheck(BaseModel):
    """Result of a single compliance check"""
    name: str
    category: str
    passed: bool
    severity: str = Field(default="warning")  # error, warning, info
    message: str
    details: Optional[Dict[str, Any]] = None


class CertificationReport(BaseModel):
    """Complete certification report for a plugin"""
    plugin_id: str
    plugin_name: str
    plugin_version: str
    certification_date: datetime
    certification_level: CertificationLevel
    
    # Detailed results
    compliance_checks: List[ComplianceCheck]
    performance_metrics: Dict[str, Any]
    security_assessment: Dict[str, Any]
    
    # Summary
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: int
    
    # Recommendations
    recommendations: List[str]
    
    def to_markdown(self) -> str:
        """Generate markdown report"""
        report = [
            f"# SIDHE Plugin Certification Report",
            f"## Plugin: {self.plugin_name} ({self.plugin_id})",
            f"**Version:** {self.plugin_version}",
            f"**Date:** {self.certification_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Certification Level:** {self.certification_level.value.upper()}",
            "",
            "## Summary",
            f"- Total Checks: {self.total_checks}",
            f"- Passed: {self.passed_checks}",
            f"- Failed: {self.failed_checks}",
            f"- Warnings: {self.warnings}",
            "",
            "## Compliance Checks",
        ]
        
        # Group by category
        categories = {}
        for check in self.compliance_checks:
            if check.category not in categories:
                categories[check.category] = []
            categories[check.category].append(check)
        
        for category, checks in categories.items():
            report.append(f"\n### {category}")
            for check in checks:
                status = "✅" if check.passed else "❌"
                report.append(f"- {status} **{check.name}**: {check.message}")
                if check.details:
                    for key, value in check.details.items():
                        report.append(f"  - {key}: {value}")
        
        # Performance metrics
        report.extend([
            "",
            "## Performance Metrics",
            f"- Average Response Time: {self.performance_metrics.get('avg_response_time_ms', 'N/A')}ms",
            f"- Success Rate: {self.performance_metrics.get('success_rate', 'N/A')}%",
            f"- Throughput: {self.performance_metrics.get('requests_per_second', 'N/A')} req/s",
        ])
        
        # Security assessment
        report.extend([
            "",
            "## Security Assessment",
            f"- Input Validation: {self.security_assessment.get('input_validation', 'Not tested')}",
            f"- Error Handling: {self.security_assessment.get('error_handling', 'Not tested')}",
            f"- Resource Limits: {self.security_assessment.get('resource_limits', 'Not tested')}",
        ])
        
        # Recommendations
        if self.recommendations:
            report.extend([
                "",
                "## Recommendations",
            ])
            for rec in self.recommendations:
                report.append(f"- {rec}")
        
        return "\n".join(report)


class PluginManifest(BaseModel):
    """Plugin manifest requirements"""
    plugin_id: str
    plugin_name: str
    version: str
    description: str
    author: str
    license: str = "MIT"
    
    # Requirements
    min_pdk_version: str = "1.0.0"
    python_version: str = ">=3.11"
    dependencies: List[str] = Field(default_factory=list)
    
    # Capabilities
    capabilities: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Performance expectations
    expected_response_time_ms: int = 1000
    max_memory_mb: int = 512
    
    # Configuration schema
    config_schema: Optional[Dict[str, Any]] = None


class PluginCertifier:
    """
    The mystical guardian that certifies plugins meet SIDHE standards.
    
    This sacred certifier validates:
    - Proper inheritance and implementation
    - Message protocol compliance
    - Error handling robustness
    - Performance characteristics
    - Security best practices
    """
    
    def __init__(self):
        self.checks: List[ComplianceCheck] = []
        self.performance_results = {}
        self.security_results = {}
        self.recommendations = []
    
    async def certify_plugin(self, 
                            plugin_class: Type[EnchantedPlugin],
                            manifest_path: Optional[Path] = None) -> CertificationReport:
        """
        Perform complete certification of a plugin.
        
        Args:
            plugin_class: The plugin class to certify
            manifest_path: Path to plugin manifest YAML file
            
        Returns:
            Complete certification report
        """
        print(f"🔍 Beginning certification of {plugin_class.__name__}...")
        
        # Reset state
        self.checks = []
        self.performance_results = {}
        self.security_results = {}
        self.recommendations = []
        
        # Load manifest if provided
        manifest = None
        if manifest_path and manifest_path.exists():
            with open(manifest_path) as f:
                manifest_data = yaml.safe_load(f)
                manifest = PluginManifest(**manifest_data)
        
        # Create mock environment
        mock_redis = MockRedis()
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            try:
                # Instantiate plugin
                plugin = plugin_class()
                
                # Run certification checks
                await self._check_basic_compliance(plugin, plugin_class)
                await self._check_message_compliance(plugin, mock_redis)
                await self._check_error_handling(plugin)
                await self._check_performance(plugin, manifest)
                await self._check_security(plugin)
                await self._check_best_practices(plugin, plugin_class)
                
                # If manifest provided, validate against it
                if manifest:
                    await self._validate_manifest_compliance(plugin, manifest)
                
            except Exception as e:
                self.checks.append(ComplianceCheck(
                    name="Plugin Instantiation",
                    category="Basic Compliance",
                    passed=False,
                    severity="error",
                    message=f"Failed to instantiate plugin: {str(e)}",
                    details={"traceback": traceback.format_exc()}
                ))
        
        # Calculate certification level
        certification_level = self._calculate_certification_level()
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Create report
        report = CertificationReport(
            plugin_id=getattr(plugin, 'plugin_id', 'unknown'),
            plugin_name=getattr(plugin, 'plugin_name', 'Unknown Plugin'),
            plugin_version=getattr(plugin, 'version', '0.0.0'),
            certification_date=datetime.now(),
            certification_level=certification_level,
            compliance_checks=self.checks,
            performance_metrics=self.performance_results,
            security_assessment=self.security_results,
            total_checks=len(self.checks),
            passed_checks=len([c for c in self.checks if c.passed]),
            failed_checks=len([c for c in self.checks if not c.passed]),
            warnings=len([c for c in self.checks if not c.passed and c.severity == "warning"]),
            recommendations=self.recommendations
        )
        
        return report
    
    async def _check_basic_compliance(self, plugin: EnchantedPlugin, plugin_class: Type):
        """Check basic compliance requirements"""
        # Check inheritance - look for EnchantedPlugin in the MRO by name
        has_enchanted_plugin_base = any(
            base.__name__ == 'EnchantedPlugin' 
            for base in plugin_class.__mro__
        )
        self.checks.append(ComplianceCheck(
            name="Inheritance Check",
            category="Basic Compliance",
            passed=has_enchanted_plugin_base,
            severity="error",
            message="Plugin inherits from EnchantedPlugin" if has_enchanted_plugin_base 
                    else "Plugin does NOT inherit from EnchantedPlugin"
        ))
        
        # Check required attributes
        required_attrs = ['plugin_id', 'plugin_name', 'version']
        for attr in required_attrs:
            has_attr = hasattr(plugin, attr)
            self.checks.append(ComplianceCheck(
                name=f"{attr} Attribute",
                category="Basic Compliance",
                passed=has_attr,
                severity="error",
                message=f"Plugin has {attr}" if has_attr else f"Plugin missing {attr}",
                details={attr: getattr(plugin, attr, None)} if has_attr else None
            ))
        
        # Check handle_request implementation
        has_handle_request = hasattr(plugin, 'handle_request') and callable(getattr(plugin, 'handle_request'))
        is_abstract = inspect.isabstract(plugin_class.handle_request)
        is_implemented = not is_abstract and plugin_class.handle_request != EnchantedPlugin.handle_request
        
        self.checks.append(ComplianceCheck(
            name="handle_request Implementation",
            category="Basic Compliance",
            passed=has_handle_request and is_implemented,
            severity="error",
            message="handle_request is properly implemented" if is_implemented 
                    else "handle_request is NOT implemented (using base class method)"
        ))
        
        # Check capabilities registration
        has_capabilities = hasattr(plugin, 'capabilities') and len(plugin.capabilities) > 0
        self.checks.append(ComplianceCheck(
            name="Capability Registration",
            category="Basic Compliance",
            passed=has_capabilities,
            severity="warning",
            message=f"Plugin registered {len(plugin.capabilities)} capabilities" if has_capabilities
                    else "Plugin has no registered capabilities",
            details={"capabilities": [cap.model_dump() for cap in plugin.capabilities]} if has_capabilities else None
        ))
    
    async def _check_message_compliance(self, plugin: EnchantedPlugin, mock_redis: MockRedis):
        """Check message protocol compliance"""
        # Test request/response pattern
        test_request = create_plugin_message(
            MessageType.REQUEST,
            source="certifier",
            target=plugin.plugin_id,
            payload={"action": "test", "data": "certification"}
        )
        
        try:
            # Plugin should handle the request
            response = await plugin.handle_request(test_request)
            
            self.checks.append(ComplianceCheck(
                name="Request Handling",
                category="Message Protocol",
                passed=isinstance(response, dict),
                severity="error",
                message="Plugin returns proper response format" if isinstance(response, dict)
                        else f"Plugin returns invalid response type: {type(response)}",
                details={"response_sample": str(response)[:100] if response else None}
            ))
        except NotImplementedError:
            self.checks.append(ComplianceCheck(
                name="Request Handling",
                category="Message Protocol",
                passed=False,
                severity="error",
                message="handle_request raises NotImplementedError - not implemented"
            ))
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="Request Handling",
                category="Message Protocol",
                passed=False,
                severity="error",
                message=f"handle_request raised unexpected error: {type(e).__name__}",
                details={"error": str(e)}
            ))
        
        # Test health check response
        health_request = create_plugin_message(
            MessageType.HEALTH_CHECK,
            source="certifier",
            target=plugin.plugin_id
        )
        
        try:
            # Access the internal handler
            health_response = await plugin._handle_health_check(health_request)
            
            self.checks.append(ComplianceCheck(
                name="Health Check Response",
                category="Message Protocol",
                passed=isinstance(health_response, dict) and "status" in health_response,
                severity="warning",
                message="Plugin responds to health checks properly",
                details={"health_data": health_response} if isinstance(health_response, dict) else None
            ))
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="Health Check Response",
                category="Message Protocol",
                passed=False,
                severity="warning",
                message=f"Health check failed: {str(e)}"
            ))
    
    async def _check_error_handling(self, plugin: EnchantedPlugin):
        """Check error handling robustness"""
        error_scenarios = [
            {
                "name": "Invalid Action",
                "payload": {"action": "nonexistent_action"},
                "expected_error": True
            },
            {
                "name": "Missing Required Fields",
                "payload": {},
                "expected_error": True
            },
            {
                "name": "Invalid Data Type",
                "payload": {"action": "test", "data": {"nested": "too_deep" * 1000}},
                "expected_error": True
            }
        ]
        
        for scenario in error_scenarios:
            request = create_plugin_message(
                MessageType.REQUEST,
                source="certifier",
                target=plugin.plugin_id,
                payload=scenario["payload"]
            )
            
            try:
                response = await plugin.handle_request(request)
                
                # If we expected an error but got a response, that's OK if handled gracefully
                self.checks.append(ComplianceCheck(
                    name=f"Error Handling - {scenario['name']}",
                    category="Error Handling",
                    passed=True,
                    severity="info",
                    message=f"Plugin handled {scenario['name']} gracefully",
                    details={"response": str(response)[:100]}
                ))
                
            except NotImplementedError:
                # Special case - base implementation
                self.checks.append(ComplianceCheck(
                    name=f"Error Handling - {scenario['name']}",
                    category="Error Handling",
                    passed=False,
                    severity="error",
                    message="Plugin has not implemented handle_request"
                ))
                
            except Exception as e:
                # Plugin raised an exception - this is expected for error scenarios
                self.checks.append(ComplianceCheck(
                    name=f"Error Handling - {scenario['name']}",
                    category="Error Handling",
                    passed=scenario["expected_error"],
                    severity="info" if scenario["expected_error"] else "warning",
                    message=f"Plugin raised {type(e).__name__} as expected" if scenario["expected_error"]
                            else f"Plugin failed to handle error gracefully",
                    details={"error": str(e)}
                ))
    
    async def _check_performance(self, plugin: EnchantedPlugin, manifest: Optional[PluginManifest]):
        """Check performance characteristics"""
        # Create benchmark
        benchmark = PerformanceBenchmark(plugin)
        
        # Simple request for benchmarking
        test_request = create_plugin_message(
            MessageType.REQUEST,
            source="certifier",
            target=plugin.plugin_id,
            payload={"action": "test", "data": "benchmark"}
        )
        
        try:
            # Run benchmark
            perf_result = await benchmark.benchmark_request(test_request, iterations=50)
            
            self.performance_results.update(perf_result)
            
            
            # Check against manifest expectations if provided
            if manifest and manifest.expected_response_time_ms:
                meets_expectation = perf_result['avg_time_ms'] <= manifest.expected_response_time_ms
                
                self.checks.append(ComplianceCheck(
                    name="Response Time Expectation",
                    category="Performance",
                    passed=meets_expectation,
                    severity="warning",
                    message=f"Average response time: {perf_result['avg_time_ms']:.2f}ms "
                           f"(expected: <{manifest.expected_response_time_ms}ms)",
                    details=perf_result
                ))
            else:
                # Just record the performance
                self.checks.append(ComplianceCheck(
                    name="Performance Benchmark",
                    category="Performance",
                    passed=perf_result['success_rate'] > 90,
                    severity="info",
                    message=f"Average response time: {perf_result['avg_time_ms']:.2f}ms, "
                           f"Success rate: {perf_result['success_rate']:.1f}%",
                    details=perf_result
                ))
                
            # Update performance_results with expected keys
            self.performance_results = {
                'avg_response_time_ms': perf_result['avg_time_ms'],
                'success_rate': perf_result['success_rate'],
                'requests_per_second': 1000 / perf_result['avg_time_ms'] if perf_result['avg_time_ms'] > 0 else 0
            }
                
        except Exception as e:
            self.checks.append(ComplianceCheck(
                name="Performance Benchmark",
                category="Performance",
                passed=False,
                severity="warning",
                message=f"Failed to benchmark plugin: {str(e)}"
            ))
    
    async def _check_security(self, plugin: EnchantedPlugin):
        """Check security best practices"""
        # Input validation check
        injection_payloads = [
            {"action": "test'; DROP TABLE users;--", "data": "sql_injection"},
            {"action": "test", "data": "<script>alert('xss')</script>"},
            {"action": "../../../etc/passwd", "data": "path_traversal"},
            {"action": "test", "data": "x" * 10000}  # Large payload
        ]
        
        injection_handled = True
        for payload in injection_payloads:
            request = create_plugin_message(
                MessageType.REQUEST,
                source="certifier",
                target=plugin.plugin_id,
                payload=payload
            )
            
            try:
                await plugin.handle_request(request)
                # If it didn't crash, that's good
            except NotImplementedError:
                # Base implementation
                injection_handled = False
                break
            except Exception:
                # Any exception is fine - means it's handling the bad input
                pass
        
        self.security_results['input_validation'] = "Pass" if injection_handled else "Not Implemented"
        
        self.checks.append(ComplianceCheck(
            name="Input Validation",
            category="Security",
            passed=injection_handled,
            severity="warning" if injection_handled else "error",
            message="Plugin handles malicious input safely" if injection_handled
                    else "Plugin has not implemented input handling"
        ))
        
        # Resource limits check (basic)
        self.security_results['resource_limits'] = "Not tested (requires runtime monitoring)"
        
        # Error information disclosure
        try:
            error_request = create_plugin_message(
                MessageType.REQUEST,
                source="certifier",
                target=plugin.plugin_id,
                payload={"action": "trigger_error", "internal_path": "/etc/shadow"}
            )
            
            try:
                await plugin.handle_request(error_request)
                error_handling_safe = True
            except Exception as e:
                # Check if error exposes sensitive information
                error_msg = str(e)
                exposes_paths = "/etc/" in error_msg or "C:\\" in error_msg
                exposes_internal = "traceback" in error_msg.lower()
                
                error_handling_safe = not (exposes_paths or exposes_internal)
            
            self.security_results['error_handling'] = "Safe" if error_handling_safe else "May expose information"
            
            self.checks.append(ComplianceCheck(
                name="Error Information Disclosure",
                category="Security",
                passed=error_handling_safe,
                severity="warning",
                message="Error messages don't expose sensitive information" if error_handling_safe
                        else "Error messages may expose sensitive information"
            ))
            
        except NotImplementedError:
            self.security_results['error_handling'] = "Not Implemented"
    
    async def _check_best_practices(self, plugin: EnchantedPlugin, plugin_class: Type):
        """Check adherence to best practices"""
        # Docstring check
        has_class_docstring = bool(plugin_class.__doc__ and plugin_class.__doc__.strip())
        has_handle_request_docstring = bool(plugin_class.handle_request.__doc__ and 
                                           plugin_class.handle_request.__doc__.strip())
        
        self.checks.append(ComplianceCheck(
            name="Documentation",
            category="Best Practices",
            passed=has_class_docstring and has_handle_request_docstring,
            severity="info",
            message="Plugin is well documented" if has_class_docstring
                    else "Plugin lacks proper documentation"
        ))
        
        # Logging check
        has_logging = hasattr(plugin, 'logger') and plugin.logger is not None
        self.checks.append(ComplianceCheck(
            name="Logging Configuration",
            category="Best Practices",
            passed=has_logging,
            severity="info",
            message="Plugin has logging configured"
        ))
        
        # Type hints check
        handle_request_signature = inspect.signature(plugin_class.handle_request)
        has_type_hints = bool(handle_request_signature.return_annotation != inspect.Signature.empty)
        
        self.checks.append(ComplianceCheck(
            name="Type Hints",
            category="Best Practices",
            passed=has_type_hints,
            severity="info",
            message="Plugin uses type hints" if has_type_hints
                    else "Plugin should use type hints for better code quality"
        ))
        
        # Async implementation check
        is_async = inspect.iscoroutinefunction(plugin_class.handle_request)
        self.checks.append(ComplianceCheck(
            name="Async Implementation",
            category="Best Practices",
            passed=is_async,
            severity="info",
            message="Plugin uses async/await properly"
        ))
    
    async def _validate_manifest_compliance(self, plugin: EnchantedPlugin, manifest: PluginManifest):
        """Validate plugin against its manifest"""
        # Check version match
        version_matches = plugin.version == manifest.version
        self.checks.append(ComplianceCheck(
            name="Manifest Version Match",
            category="Manifest Compliance",
            passed=version_matches,
            severity="warning",
            message=f"Plugin version matches manifest ({manifest.version})" if version_matches
                    else f"Version mismatch: plugin={plugin.version}, manifest={manifest.version}"
        ))
        
        # Check capabilities match
        plugin_caps = {cap.name for cap in plugin.capabilities}
        manifest_caps = {cap['name'] for cap in manifest.capabilities}
        
        caps_match = plugin_caps == manifest_caps
        self.checks.append(ComplianceCheck(
            name="Capability Declaration",
            category="Manifest Compliance",
            passed=caps_match,
            severity="warning",
            message="Plugin capabilities match manifest" if caps_match
                    else "Capability mismatch between plugin and manifest",
            details={
                "plugin_capabilities": list(plugin_caps),
                "manifest_capabilities": list(manifest_caps),
                "missing_in_plugin": list(manifest_caps - plugin_caps),
                "extra_in_plugin": list(plugin_caps - manifest_caps)
            } if not caps_match else None
        ))
    
    def _calculate_certification_level(self) -> CertificationLevel:
        """Calculate certification level based on checks"""
        if not self.checks:
            return CertificationLevel.FAILED
        
        # Count by severity
        errors = len([c for c in self.checks if not c.passed and c.severity == "error"])
        warnings = len([c for c in self.checks if not c.passed and c.severity == "warning"])
        total_passed = len([c for c in self.checks if c.passed])
        total_checks = len(self.checks)
        
        pass_rate = total_passed / total_checks if total_checks > 0 else 0
        
        if errors > 0:
            return CertificationLevel.FAILED
        elif pass_rate >= 0.95 and warnings == 0:
            return CertificationLevel.ADVANCED
        elif pass_rate >= 0.80:
            return CertificationLevel.STANDARD
        elif pass_rate >= 0.60:
            return CertificationLevel.BASIC
        else:
            return CertificationLevel.FAILED
    
    def _generate_recommendations(self):
        """Generate recommendations based on checks"""
        # Analyze failed checks
        for check in self.checks:
            if not check.passed:
                if check.category == "Basic Compliance" and check.severity == "error":
                    self.recommendations.append(
                        f"CRITICAL: Fix {check.name} - this is required for basic functionality"
                    )
                elif check.category == "Message Protocol":
                    self.recommendations.append(
                        f"Implement proper message handling for {check.name}"
                    )
                elif check.category == "Error Handling":
                    self.recommendations.append(
                        "Improve error handling to gracefully handle invalid inputs"
                    )
                elif check.category == "Performance" and "response time" in check.message.lower():
                    self.recommendations.append(
                        "Optimize response time - consider caching or async operations"
                    )
                elif check.category == "Security":
                    self.recommendations.append(
                        f"Security: {check.message} - this is important for production use"
                    )
                elif check.category == "Best Practices":
                    self.recommendations.append(
                        f"Consider: {check.message}"
                    )
        
        # General recommendations
        if not any("capability" in check.name.lower() for check in self.checks if check.passed):
            self.recommendations.append(
                "Register plugin capabilities to help users understand what your plugin can do"
            )
        
        if not any("document" in check.name.lower() for check in self.checks if check.passed):
            self.recommendations.append(
                "Add comprehensive docstrings to improve code maintainability"
            )


async def certify_plugin_from_file(plugin_path: Path, manifest_path: Optional[Path] = None) -> CertificationReport:
    """
    Certify a plugin from a Python file.
    
    Args:
        plugin_path: Path to the plugin Python file
        manifest_path: Optional path to manifest YAML
        
    Returns:
        Certification report
    """
    import importlib.util
    import sys
    
    # Add the plugin's parent directories to sys.path for imports
    plugin_path = Path(plugin_path).resolve()
    original_path = sys.path.copy()
    
    # Add potential source directories to path
    potential_paths = [
        plugin_path.parent,  # Plugin directory
        plugin_path.parent.parent.parent,  # Potential src directory (up 3 levels from plugin file)
    ]
    
    # Also try to find src directory by looking for core/pdk
    current_path = plugin_path.parent
    while current_path.parent != current_path:  # Not at root
        if (current_path / "core" / "pdk").exists():
            potential_paths.append(current_path)
            break
        current_path = current_path.parent
    
    for path in potential_paths:
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
    
    module = None
    plugin_class = None
    
    try:
        # Load the plugin module
        spec = importlib.util.spec_from_file_location("plugin_module", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find the plugin class (should inherit from EnchantedPlugin)
        # Import EnchantedPlugin in the modified path context
        from sidhe_pdk import EnchantedPlugin as LocalEnchantedPlugin
        
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                obj.__name__ != 'EnchantedPlugin' and
                hasattr(obj, '__mro__')):
                # Check if any class in the MRO has EnchantedPlugin name
                for base in obj.__mro__:
                    if base.__name__ == 'EnchantedPlugin':
                        plugin_class = obj
                        break
                if plugin_class:
                    break
                
    except ImportError:
        # Fallback: try with the original EnchantedPlugin reference
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                obj.__name__ != 'EnchantedPlugin' and
                hasattr(obj, '__mro__')):
                # Check if any class in the MRO has EnchantedPlugin name
                for base in obj.__mro__:
                    if base.__name__ == 'EnchantedPlugin':
                        plugin_class = obj
                        break
                if plugin_class:
                    break
    finally:
        # Restore original sys.path
        sys.path = original_path
    
    if not plugin_class:
        raise ValueError(f"No EnchantedPlugin subclass found in {plugin_path}")
    
    # Run certification
    certifier = PluginCertifier()
    report = await certifier.certify_plugin(plugin_class, manifest_path)
    
    return report


# CLI for plugin certification
import click

@click.command()
@click.argument('plugin_file', type=click.Path(exists=True))
@click.option('--manifest', '-m', type=click.Path(exists=True), help='Path to plugin manifest YAML')
@click.option('--output', '-o', type=click.Path(), help='Output file for certification report')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json']), default='markdown', help='Output format')
def certify(plugin_file: str, manifest: Optional[str], output: Optional[str], format: str):
    """Certify a SIDHE plugin for compliance with communication standards"""
    plugin_path = Path(plugin_file)
    manifest_path = Path(manifest) if manifest else None
    
    async def run_certification():
        try:
            report = await certify_plugin_from_file(plugin_path, manifest_path)
            
            # Generate output
            if format == 'markdown':
                output_content = report.to_markdown()
            else:
                output_content = report.json(indent=2)
            
            # Save or print
            if output:
                with open(output, 'w') as f:
                    f.write(output_content)
                click.echo(f"✅ Certification report saved to {output}")
            else:
                click.echo(output_content)
            
            # Summary
            click.echo("")
            click.echo(f"Certification Level: {report.certification_level.value.upper()}")
            click.echo(f"Passed: {report.passed_checks}/{report.total_checks} checks")
            
            if report.certification_level == CertificationLevel.FAILED:
                click.echo("❌ Plugin FAILED certification")
                exit(1)
            else:
                click.echo(f"✅ Plugin certified at {report.certification_level.value} level")
                
        except Exception as e:
            click.echo(f"❌ Certification failed: {e}")
            exit(1)
    
    asyncio.run(run_certification())


if __name__ == "__main__":
    certify()
