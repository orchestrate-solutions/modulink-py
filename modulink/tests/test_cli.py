import os
import subprocess
import sys
import pytest


CLI = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "modulink-doc"))


def run_cli(args, **kwargs):
    env = os.environ.copy()
    # Set PYTHONPATH to the project root so modulink is importable
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env["PYTHONPATH"] = project_root
    return subprocess.run([sys.executable, CLI] + args, capture_output=True, text=True, env=env, **kwargs)


def test_help():
    result = run_cli(["--help"])
    assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()
