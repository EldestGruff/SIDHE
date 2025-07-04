#!/usr/bin/env python3
"""
Test runner for Conversation Engine
Runs comprehensive test suite with proper reporting
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type="all", coverage=False, verbose=False, markers=None):
    """Run tests with specified options"""
    
    # Get the test directory
    test_dir = Path(__file__).parent
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    if test_type == "unit":
        cmd.append(str(test_dir / "backend"))
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    else:
        cmd.append(str(test_dir))
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=../backend",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    # Add markers
    if markers:
        cmd.extend(["-m", markers])
    
    # Add async support
    cmd.extend(["--asyncio-mode=auto"])
    
    # Add output options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)
    
    # Change to test directory
    os.chdir(test_dir)
    
    # Run tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def check_dependencies():
    """Check if test dependencies are installed"""
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pytest-mock",
        "httpx",
        "fastapi",
        "redis",
        "anthropic"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("Missing required test dependencies:")
        for package in missing:
            print(f"  - {package}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run Conversation Engine tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--markers", "-m",
        help="Run only tests with specified markers"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check test dependencies and exit"
    )
    
    args = parser.parse_args()
    
    if args.check_deps:
        if check_dependencies():
            print("All test dependencies are installed!")
            return 0
        else:
            return 1
    
    # Check dependencies before running tests
    if not check_dependencies():
        return 1
    
    print("=" * 60)
    print("🚀 RIKER CONVERSATION ENGINE TEST SUITE")
    print("=" * 60)
    print(f"Test Type: {args.type}")
    print(f"Coverage: {'Enabled' if args.coverage else 'Disabled'}")
    print(f"Verbose: {'Enabled' if args.verbose else 'Disabled'}")
    if args.markers:
        print(f"Markers: {args.markers}")
    print("=" * 60)
    
    # Run tests
    exit_code = run_tests(
        test_type=args.type,
        coverage=args.coverage,
        verbose=args.verbose,
        markers=args.markers
    )
    
    print("=" * 60)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())