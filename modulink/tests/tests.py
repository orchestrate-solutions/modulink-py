"""Test skeleton for ModuLink Next.

This file contains tests for dynamic docstrings, CLI documentation, and protocol conformance.
See README.md section 6 for best practices.
"""

import pytest
from modulink.src.chain import Chain
from modulink.src.context import Context
from modulink.src.link import Link, is_link
from modulink.src.middleware import Middleware, is_middleware
from modulink.src.listeners import BaseListener, HttpListener, TcpListener

def sample_link(ctx: Context) -> Context:
    """Sample link docstring."""
    return ctx

def another_link(ctx: Context) -> Context:
    """Another link docstring."""
    return ctx

def test_chain_dynamic_docstring():
    chain = Chain(sample_link, another_link)
    doc = chain.__doc__
    assert "sample_link" in doc
    assert "Sample link docstring." in doc
    assert "another_link" in doc
    assert "Another link docstring." in doc
    # Add a link and check update
    def third_link(ctx: Context) -> Context:
        """Third link docstring."""
        return ctx
    chain.add_link(third_link)
    assert "third_link" in chain.__doc__
    assert "Third link docstring." in chain.__doc__

def test_chain_docstring_updates_on_connect_and_middleware():
    chain = Chain(sample_link)
    chain.connect(sample_link, sample_link, True)
    assert "Connections" in chain.__doc__
    class DummyMiddleware:
        pass
    chain.use(DummyMiddleware())
    assert "DummyMiddleware" in chain.__doc__

def test_listener_dynamic_docstring():
    chain = Chain(sample_link)
    http_listener = HttpListener(chain, "/signup", ["POST"])
    tcp_listener = TcpListener(chain, 9000)
    assert "/signup" in http_listener.__doc__
    assert "9000" in tcp_listener.__doc__

def test_chain_run_smoke():
    """Should fail: Chain.run is not implemented."""
    chain = Chain()
    ctx = {}
    with pytest.raises(AssertionError):
        assert chain.run(ctx) == {"expected": "result"}

def test_link_protocol():
    """Test Link protocol conformance."""
    async def link_impl(ctx: Context) -> Context:
        return ctx
    assert is_link(link_impl), "Link should be callable and have a docstring"

def test_middleware_protocol():
    """Test Middleware protocol conformance."""
    class MW:
        async def before(self, link, ctx): pass
        async def after(self, link, ctx, result): pass
    mw = MW()
    assert is_middleware(mw), "Middleware should have before and after methods"

def test_listener_stub():
    """Test Listener stub functionality."""
    listener = BaseListener()
    ctx = {}
    import asyncio
    result = asyncio.run(listener(ctx))
    assert result.get("listener_called") is True

def test_get_doc_api():
    """Test the get_doc API for various topics."""
    from modulink import docs
    chain_doc = docs.get_doc("chain")
    assert "named graph of Links" in chain_doc
    assert "Logs link execution" in docs.get_doc("middleware.Logging")
    assert "Measures and logs execution time" in docs.get_doc("middleware.Timing")
    assert "ModuLink MVP Documentation Draft" in docs.get_doc("readme")

def test_modulink_doc_cli():
    """Test the modulink-doc CLI script for all major documentation topics."""
    import subprocess
    import sys
    import os
    cli = os.path.abspath("modulink/modulink-doc")

    # Test Chain documentation
    result = subprocess.run([sys.executable, cli, "chain"], capture_output=True, text=True)
    assert "named graph of Links" in result.stdout

    # Test Middleware documentation
    result = subprocess.run([sys.executable, cli, "middleware.Logging"], capture_output=True, text=True)
    assert "Logs link execution" in result.stdout
    result = subprocess.run([sys.executable, cli, "middleware.Timing"], capture_output=True, text=True)
    assert "Measures and logs execution time" in result.stdout

    # Test README documentation
    result = subprocess.run([sys.executable, cli, "readme"], capture_output=True, text=True)
    assert "ModuLink MVP Documentation Draft" in result.stdout

    # Test Examples documentation
    result = subprocess.run([sys.executable, cli, "examples"], capture_output=True, text=True)
    assert "Usage Examples & Best Practices" in result.stdout
    assert "Quick Start" in result.stdout
    assert "Advanced Branching" in result.stdout
    assert "Integration Example" in result.stdout
    assert "Best Practices" in result.stdout

    # Test TODO documentation
    result = subprocess.run([sys.executable, cli, "todo"], capture_output=True, text=True)
    assert "Completion Checklist" in result.stdout

    # Test unknown topic
    result = subprocess.run([sys.executable, cli, "unknown_topic"], capture_output=True, text=True)
    assert "No documentation found for topic" in result.stdout
