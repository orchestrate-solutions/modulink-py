"""Verbose and edge-case tests for modulink."""

import pytest
import asyncio
from modulink.src.chain import Chain
from modulink.src.context import Context
from modulink.src.link import is_link
from modulink.src.middleware import is_middleware, Logging, Timing
from modulink.src.listeners import BaseListener, HttpListener, TcpListener

# 1. Edge Case Testing
def test_empty_chain_executes_and_returns_input():
    chain = Chain()
    ctx = {"foo": "bar"}
    result = asyncio.run(chain.run(ctx))
    assert result == ctx

def test_chain_with_invalid_middleware_does_not_crash():
    class BadMiddleware:
        pass
    chain = Chain(lambda ctx: ctx)
    chain.use(BadMiddleware())
    ctx = {}
    result = asyncio.run(chain.run(ctx))
    assert isinstance(result, dict)

def test_link_raises_exception_and_is_caught():
    async def bad_link(ctx):
        raise ValueError("fail")
    chain = Chain(bad_link)
    ctx = {}
    result = asyncio.run(chain.run(ctx))
    assert "exception" in result

# 2. Parameterization
@pytest.mark.parametrize("input_ctx", [
    {},
    {"email": "test@example.com"},
    {"simulate_timeout": True},
    {"error": "fail"},
])
def test_chain_various_contexts(input_ctx):
    async def echo(ctx): return ctx
    chain = Chain(echo)
    result = asyncio.run(chain.run(input_ctx.copy()))
    assert isinstance(result, dict)

# 3. Async/Sync Mix
def test_chain_with_sync_and_async_links():
    def sync_link(ctx): return ctx
    async def async_link(ctx): return ctx
    chain = Chain(sync_link, async_link)
    ctx = {}
    result = asyncio.run(chain.run(ctx))
    assert isinstance(result, dict)

# 4. Error Propagation
def test_chain_error_routing():
    async def fail(ctx): raise RuntimeError("fail")
    async def handle(ctx): ctx["handled"] = True; return ctx
    chain = Chain(fail)
    chain.add_link(handle)
    chain.connect(fail, handle, lambda ctx: "exception" in ctx)
    ctx = {}
    result = asyncio.run(chain.run(ctx))
    assert "handled" in result

# 5. Middleware Order
def test_middleware_order(monkeypatch):
    calls = []
    class MW:
        async def before(self, link, ctx, mwctx): calls.append("before")
        async def after(self, link, ctx, result, mwctx): calls.append("after")
    chain = Chain(lambda ctx: ctx)
    chain.use(MW())
    asyncio.run(chain.run({}))
    assert calls == ["before", "after"]

# 6. Listener Integration
def test_base_listener_echoes_context():
    listener = BaseListener()
    ctx = {"foo": "bar"}
    result = asyncio.run(listener(ctx))
    assert result.get("listener_called") is True

def test_http_listener_serve_prints(capsys):
    chain = Chain(lambda ctx: ctx)
    listener = HttpListener(chain, "/test", ["GET"])
    listener.serve(port=1234)
    out = capsys.readouterr().out
    assert "Serving HTTP on port 1234" in out

def test_tcp_listener_serve_prints(capsys):
    chain = Chain(lambda ctx: ctx)
    listener = TcpListener(chain, 5678)
    listener.serve()
    out = capsys.readouterr().out
    assert "Serving TCP on port 5678" in out

# 7. Docstring/Inspect Consistency
def test_chain_docstring_after_mutation():
    def l1(ctx): "L1"; return ctx
    def l2(ctx): "L2"; return ctx
    chain = Chain(l1)
    chain.add_link(l2)
    doc = chain.__doc__
    assert "l2" in doc

# 8. CLI Robustness
def test_cli_unknown_topic(monkeypatch):
    import subprocess, sys, os
    cli = os.path.abspath("modulink/modulink-doc")
    result = subprocess.run([sys.executable, cli, "not_a_topic"], capture_output=True, text=True)
    assert "No documentation found for topic" in result.stdout

# 9. Performance/Stress (basic)
def test_chain_large_number_of_links():
    async def link(ctx): return ctx
    chain = Chain(*[link for _ in range(100)])
    ctx = {}
    result = asyncio.run(chain.run(ctx))
    assert isinstance(result, dict)

# 10. Mutation/State
def test_chain_context_isolation():
    async def add_one(ctx): ctx["n"] = ctx.get("n", 0) + 1; return ctx
    chain = Chain(add_one)
    ctx1 = {"n": 0}
    ctx2 = {"n": 10}
    r1 = asyncio.run(chain.run(ctx1.copy()))
    r2 = asyncio.run(chain.run(ctx2.copy()))
    assert r1["n"] == 1
    assert r2["n"] == 11
