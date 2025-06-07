import pytest
from modulink import core

def test_modulink_options_defaults():
    opts = core.ModulinkOptions()
    assert opts.environment == "development"
    assert opts.enable_logging is True

def test_create_modulink_instance():
    instance = core.create_modulink()
    assert hasattr(instance, "create_chain")
    assert hasattr(instance, "register_chain")
