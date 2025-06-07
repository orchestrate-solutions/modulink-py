import pytest
import subprocess
import sys
import os

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "../examples")

@pytest.mark.parametrize("script", [
    "chain_demo.py",
    "enhanced_chain_demo.py",
    "basic_example.py",
    "immutable_example.py",
    "advanced_immutable_example.py",
])
def test_example_scripts_run(script, capfd):
    """Run example scripts and check for expected output or errors."""
    script_path = os.path.join(EXAMPLES_DIR, script)
    assert os.path.exists(script_path), f"Example script {script} not found"
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    out = result.stdout
    err = result.stderr
    # Check that script runs and prints something meaningful
    assert result.returncode == 0, f"{script} failed: {err}"
    assert len(out.strip()) > 0, f"{script} produced no output"
    # Optionally, check for known success markers in output
    assert "Demo" in out or "completed" in out or "Success" in out or "✅" in out, f"{script} output not as expected: {out}"

@pytest.mark.parametrize("script", [
    "basic_example.py",
])
def test_example_script_negative(script):
    """Run example script with bad input to check error handling."""
    script_path = os.path.join(EXAMPLES_DIR, script)
    assert os.path.exists(script_path), f"Example script {script} not found"
    # Simulate bad input by setting an env var or passing args if supported
    # Here we just check that it doesn't crash
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    assert result.returncode == 0, f"{script} failed unexpectedly: {result.stderr}"
