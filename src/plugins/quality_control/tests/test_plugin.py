"""
Test suite for Quality Control Plugin

Tests the main plugin functionality, health checks, and integration points.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

from ..main import QualityControlPlugin

@pytest.fixture
def plugin():
    """Create a Quality Control Plugin instance for testing"""
    config_path = Path(__file__).parent.parent / "config"
    return QualityControlPlugin(config_path)

@pytest.mark.asyncio
async def test_plugin_initialization(plugin):
    """Test plugin initializes correctly"""
    assert plugin.plugin_name == "quality_control"
    assert plugin.version == "1.0.0"
    assert plugin.enabled is True

@pytest.mark.asyncio
async def test_health_check(plugin):
    """Test plugin health check"""
    health = await plugin.health_check()
    
    assert "plugin" in health
    assert "healthy" in health
    assert "components" in health
    assert health["plugin"] == "quality_control"

@pytest.mark.asyncio
async def test_quality_status(plugin):
    """Test getting quality status"""
    status = await plugin.get_quality_status()
    
    assert hasattr(status, 'enabled')
    assert hasattr(status, 'last_check')
    assert hasattr(status, 'components_healthy')

@pytest.mark.asyncio
async def test_incremental_check_empty_files(plugin):
    """Test incremental check with empty file list"""
    result = await plugin.run_incremental_check([])
    
    assert hasattr(result, 'overall_score')
    assert hasattr(result, 'issues')
    assert len(result.issues) == 0

@pytest.mark.asyncio
async def test_incremental_check_python_files(plugin):
    """Test incremental check with Python files"""
    # Create a temporary Python file for testing
    test_file = Path(__file__).parent / "test_sample.py"
    test_file.write_text("def hello():\n    print('hello')\n")
    
    try:
        result = await plugin.run_incremental_check([str(test_file)])
        
        assert hasattr(result, 'overall_score')
        assert hasattr(result, 'linting_results')
        assert 'python' in result.linting_results
        
    finally:
        if test_file.exists():
            test_file.unlink()

@pytest.mark.asyncio
async def test_enforce_quality_gates(plugin):
    """Test quality gate enforcement"""
    with patch.object(plugin, 'run_full_quality_check') as mock_check:
        # Mock a quality report
        mock_report = Mock()
        mock_report.overall_score = 85.0
        mock_report.linting_results = {}
        mock_report.coverage_results = {'overall_coverage': 85.0}
        mock_report.issues = []
        mock_check.return_value = mock_report
        
        result = await plugin.enforce_quality_gates("test_quest")
        
        assert "quest_id" in result
        assert "gates_passed" in result
        assert result["quest_id"] == "test_quest"

def test_file_ignore_patterns(plugin):
    """Test file ignore patterns work correctly"""
    test_files = [
        Path("node_modules/test.js"),
        Path("__pycache__/test.pyc"),
        Path(".git/config"),
        Path("src/test.py"),
        Path("build/output.js")
    ]
    
    filtered = [f for f in test_files if not plugin._should_ignore_file(f)]
    
    # Only src/test.py should remain
    assert len(filtered) == 1
    assert "src/test.py" in str(filtered[0])

@pytest.mark.asyncio
async def test_component_health_checks(plugin):
    """Test individual component health checks"""
    # Test Python linter health
    python_health = await plugin.python_linter.health_check()
    assert "healthy" in python_health
    assert "tools" in python_health
    
    # Test JavaScript linter health
    js_health = await plugin.js_linter.health_check()
    assert "healthy" in js_health
    assert "tools" in js_health
    
    # Test test runner health
    runner_health = await plugin.test_runner.health_check()
    assert "healthy" in runner_health
    assert "tools" in runner_health