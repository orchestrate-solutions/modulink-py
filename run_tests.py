"""
Test runner script for ModuLink Python

This script provides convenient ways to run tests with different configurations.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n🔄 {description}")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    """Main test runner"""
    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🧪 ModuLink Python Test Runner")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        print("❌ pytest not found. Installing...")
        if not run_command("pip install pytest pytest-cov", "Installing pytest"):
            sys.exit(1)
    
    # Run basic tests
    if not run_command("python -m pytest tests/ -v", "Running basic tests"):
        print("❌ Basic tests failed")
        sys.exit(1)
    
    # Run tests with coverage
    if not run_command(
        "python -m pytest tests/ --cov=modulink --cov-report=term-missing", 
        "Running tests with coverage"
    ):
        print("⚠️  Coverage tests failed, but continuing...")
    
    # Run specific test files
    test_files = [
        "tests/test_context.py",
        "tests/test_modulink.py", 
        "tests/test_triggers.py"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            run_command(
                f"python -m pytest {test_file} -v",
                f"Running {test_file}"
            )
    
    print("\n✅ All tests completed!")
    print("\n📊 To run tests manually:")
    print("  python -m pytest tests/                    # Run all tests")
    print("  python -m pytest tests/test_context.py     # Run context tests")
    print("  python -m pytest tests/ --cov=modulink     # Run with coverage")
    print("  python -m pytest tests/ -k 'test_name'     # Run specific test")

if __name__ == "__main__":
    main()
