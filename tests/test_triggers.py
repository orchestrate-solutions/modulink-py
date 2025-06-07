import pytest
from modulink import core

def test_http_trigger_factory_exists():
    assert hasattr(core, "create_modulink")
    instance = core.create_modulink()
    assert hasattr(instance, "triggers")
    assert "http" in instance.triggers

# Placeholder for FastAPI integration test
@pytest.mark.skip(reason="FastAPI integration test placeholder")
def test_fastapi_trigger():
    pass

# Placeholder for CLI, cron, and message trigger tests
@pytest.mark.skip(reason="CLI trigger test placeholder")
def test_cli_trigger():
    pass

@pytest.mark.skip(reason="Cron trigger test placeholder")
def test_cron_trigger():
    pass

@pytest.mark.skip(reason="Message trigger test placeholder")
def test_message_trigger():
    pass
