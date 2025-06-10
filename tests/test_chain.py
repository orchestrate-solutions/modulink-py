"""Tests for chain functionality."""

import asyncio

import pytest

from modulink import Ctx, chain


def test_chain_imports_and_exports():
    """Test that all chain-related exports are available."""
    # Core chain function
    from modulink import chain

    assert callable(chain)

    # Try to import chain-related types if available
    try:
        from modulink import ChainFunction, MiddlewareFunction

        assert ChainFunction is not None
        assert MiddlewareFunction is not None
    except ImportError:
        # Types might not be exported yet
        pass

    # Try to import Status enum if available
    try:
        from modulink import Status

        assert Status is not None
        assert hasattr(Status, "SUCCESS")
        assert hasattr(Status, "FAILED")
    except ImportError:
        pass


def test_chain_creation():
    """Test basic chain creation."""

    def link1(ctx: Ctx) -> Ctx:
        ctx["step1"] = True
        return ctx

    def link2(ctx: Ctx) -> Ctx:
        ctx["step2"] = True
        return ctx

    test_chain = chain(link1, link2)
    assert test_chain is not None
    assert hasattr(test_chain, "use")
    assert hasattr(test_chain.use, "before")
    assert hasattr(test_chain.use, "after")


def test_chain_instance_properties():
    """Test ChainInstance properties and methods."""

    def sample_link(ctx: Ctx) -> Ctx:
        return ctx

    test_chain = chain(sample_link)

    # Test that we have the expected attributes
    assert hasattr(test_chain, "links")
    assert hasattr(test_chain, "use")
    assert hasattr(test_chain, "cleanup")
    assert callable(test_chain)

    # Test links are stored
    assert len(test_chain.links) == 1
    assert test_chain.links[0] == sample_link


def test_chain_middleware_properties():
    """Test ChainMiddleware properties."""
    test_chain = chain()
    middleware_instance = test_chain.use

    # Test middleware properties
    assert hasattr(middleware_instance, "before_each_link")
    assert hasattr(middleware_instance, "after_each_link")
    assert isinstance(middleware_instance.before_each_link, list)
    assert isinstance(middleware_instance.after_each_link, list)

    # Initially empty
    assert len(middleware_instance.before_each_link) == 0
    assert len(middleware_instance.after_each_link) == 0


@pytest.mark.asyncio
async def test_chain_execution():
    """Test basic chain execution."""

    def link1(ctx: Ctx) -> Ctx:
        ctx["value"] = 1
        return ctx

    def link2(ctx: Ctx) -> Ctx:
        ctx["value"] *= 2
        return ctx

    test_chain = chain(link1, link2)
    result = await test_chain({})

    assert result["value"] == 2


@pytest.mark.asyncio
async def test_empty_chain():
    """Test empty chain execution."""
    test_chain = chain()
    result = await test_chain({"initial": True})

    assert result["initial"] is True


@pytest.mark.asyncio
async def test_chain_middleware_before():
    """Test before middleware functionality."""
    execution_order = []

    def middleware(ctx: Ctx) -> Ctx:
        execution_order.append("middleware")
        return ctx

    def link(ctx: Ctx) -> Ctx:
        execution_order.append("link")
        return ctx

    test_chain = chain(link)
    middleware_result = test_chain.use.before(middleware)

    # Test fluent interface
    assert middleware_result == test_chain.use

    await test_chain({})

    assert execution_order == ["middleware", "link"]


@pytest.mark.asyncio
async def test_chain_middleware_after():
    """Test after middleware functionality."""
    execution_order = []

    def middleware(ctx: Ctx) -> Ctx:
        execution_order.append("middleware")
        return ctx

    def link(ctx: Ctx) -> Ctx:
        execution_order.append("link")
        return ctx

    test_chain = chain(link)
    middleware_result = test_chain.use.after(middleware)

    # Test fluent interface
    assert middleware_result == test_chain.use

    await test_chain({})

    assert execution_order == ["link", "middleware"]


@pytest.mark.asyncio
async def test_chain_multiple_before_middleware():
    """Test multiple before middleware functions."""
    execution_order = []

    def middleware1(ctx: Ctx) -> Ctx:
        execution_order.append("middleware1")
        return ctx

    def middleware2(ctx: Ctx) -> Ctx:
        execution_order.append("middleware2")
        return ctx

    def link(ctx: Ctx) -> Ctx:
        execution_order.append("link")
        return ctx

    test_chain = chain(link)
    test_chain.use.before(middleware1)
    test_chain.use.before(middleware2)
    await test_chain({})

    assert execution_order == ["middleware1", "middleware2", "link"]


@pytest.mark.asyncio
async def test_chain_multiple_after_middleware():
    """Test multiple after middleware functions."""
    execution_order = []

    def middleware1(ctx: Ctx) -> Ctx:
        execution_order.append("middleware1")
        return ctx

    def middleware2(ctx: Ctx) -> Ctx:
        execution_order.append("middleware2")
        return ctx

    def link(ctx: Ctx) -> Ctx:
        execution_order.append("link")
        return ctx

    test_chain = chain(link)
    test_chain.use.after(middleware1)
    test_chain.use.after(middleware2)
    await test_chain({})

    assert execution_order == ["link", "middleware1", "middleware2"]


@pytest.mark.asyncio
async def test_chain_middleware_list():
    """Test adding middleware as a list."""
    execution_order = []

    def middleware1(ctx: Ctx) -> Ctx:
        execution_order.append("middleware1")
        return ctx

    def middleware2(ctx: Ctx) -> Ctx:
        execution_order.append("middleware2")
        return ctx

    def link(ctx: Ctx) -> Ctx:
        execution_order.append("link")
        return ctx

    test_chain = chain(link)
    test_chain.use.before([middleware1, middleware2])
    await test_chain({})

    assert execution_order == ["middleware1", "middleware2", "link"]


@pytest.mark.asyncio
async def test_chain_middleware_list_after():
    """Test adding after middleware as a list."""
    execution_order = []

    def middleware1(ctx: Ctx) -> Ctx:
        execution_order.append("middleware1")
        return ctx

    def middleware2(ctx: Ctx) -> Ctx:
        execution_order.append("middleware2")
        return ctx

    def link(ctx: Ctx) -> Ctx:
        execution_order.append("link")
        return ctx

    test_chain = chain(link)
    test_chain.use.after([middleware1, middleware2])
    await test_chain({})

    assert execution_order == ["link", "middleware1", "middleware2"]


@pytest.mark.asyncio
async def test_chain_error_handling():
    """Test error handling in chains - errors are captured in context."""

    def failing_link(ctx: Ctx) -> Ctx:
        raise ValueError("Test error")

    def recovery_link(ctx: Ctx) -> Ctx:
        ctx["recovery_attempted"] = True
        return ctx

    test_chain = chain(failing_link, recovery_link)
    result = await test_chain({})

    # Chain should capture error in context, not raise
    assert "error" in result
    assert isinstance(result["error"], ValueError)
    assert str(result["error"]) == "Test error"
    # Recovery link should not execute due to error
    assert "recovery_attempted" not in result


@pytest.mark.asyncio
async def test_chain_error_stops_execution():
    """Test that error stops further link execution."""
    execution_order = []

    def link1(ctx: Ctx) -> Ctx:
        execution_order.append("link1")
        return ctx

    def failing_link(ctx: Ctx) -> Ctx:
        execution_order.append("failing_link")
        raise ValueError("Test error")

    def link3(ctx: Ctx) -> Ctx:
        execution_order.append("link3")
        return ctx

    test_chain = chain(link1, failing_link, link3)
    result = await test_chain({})

    assert execution_order == ["link1", "failing_link"]
    assert "error" in result


@pytest.mark.asyncio
async def test_chain_middleware_error_handling():
    """Test error handling in middleware."""

    def failing_middleware(ctx: Ctx) -> Ctx:
        raise ValueError("Middleware error")

    def link(ctx: Ctx) -> Ctx:
        ctx["link_executed"] = True
        return ctx

    test_chain = chain(link)
    test_chain.use.before(failing_middleware)
    result = await test_chain({})

    assert "error" in result
    assert isinstance(result["error"], ValueError)
    assert "link_executed" not in result


@pytest.mark.asyncio
async def test_chain_middleware_error_stops_after_middleware():
    """Test that error in before middleware stops after middleware."""
    execution_order = []

    def failing_before_middleware(ctx: Ctx) -> Ctx:
        execution_order.append("failing_before")
        raise ValueError("Before middleware error")

    def after_middleware(ctx: Ctx) -> Ctx:
        execution_order.append("after_middleware")
        return ctx

    def link(ctx: Ctx) -> Ctx:
        execution_order.append("link")
        return ctx

    test_chain = chain(link)
    test_chain.use.before(failing_before_middleware)
    test_chain.use.after(after_middleware)
    result = await test_chain({})

    assert execution_order == ["failing_before"]
    assert "error" in result


def test_chain_cleanup():
    """Test chain cleanup functionality."""

    def middleware(ctx: Ctx) -> Ctx:
        return ctx

    def link(ctx: Ctx) -> Ctx:
        return ctx

    test_chain = chain(link)
    test_chain.use.before(middleware)
    test_chain.use.after(middleware)

    # Verify middleware is registered
    assert len(test_chain.use.before_each_link) == 1
    assert len(test_chain.use.after_each_link) == 1

    # Test cleanup
    result = test_chain.cleanup()

    # Test cleanup response structure
    assert isinstance(result, dict)
    assert "status" in result
    assert "message" in result

    # Test middleware was cleared
    assert len(test_chain.use.before_each_link) == 0
    assert len(test_chain.use.after_each_link) == 0


def test_chain_cleanup_error_handling():
    """Test cleanup error handling."""

    def link(ctx: Ctx) -> Ctx:
        return ctx

    test_chain = chain(link)

    # This should succeed normally
    result = test_chain.cleanup()
    assert "status" in result
    assert "message" in result


@pytest.mark.asyncio
async def test_async_link_support():
    """Test async link support in chains."""

    async def async_link(ctx: Ctx) -> Ctx:
        await asyncio.sleep(0.01)
        ctx["async_executed"] = True
        return ctx

    def sync_link(ctx: Ctx) -> Ctx:
        ctx["sync_executed"] = True
        return ctx

    test_chain = chain(async_link, sync_link)
    result = await test_chain({})

    assert result["async_executed"] is True
    assert result["sync_executed"] is True


@pytest.mark.asyncio
async def test_async_middleware_support():
    """Test async middleware support."""

    async def async_middleware(ctx: Ctx) -> Ctx:
        await asyncio.sleep(0.01)
        ctx["async_middleware_executed"] = True
        return ctx

    def sync_link(ctx: Ctx) -> Ctx:
        ctx["link_executed"] = True
        return ctx

    test_chain = chain(sync_link)
    test_chain.use.before(async_middleware)
    result = await test_chain({})

    assert result["async_middleware_executed"] is True
    assert result["link_executed"] is True


@pytest.mark.asyncio
async def test_mixed_async_sync_middleware():
    """Test mixing async and sync middleware."""
    execution_order = []

    async def async_before(ctx: Ctx) -> Ctx:
        await asyncio.sleep(0.01)
        execution_order.append("async_before")
        return ctx

    def sync_before(ctx: Ctx) -> Ctx:
        execution_order.append("sync_before")
        return ctx

    async def async_after(ctx: Ctx) -> Ctx:
        await asyncio.sleep(0.01)
        execution_order.append("async_after")
        return ctx

    def sync_after(ctx: Ctx) -> Ctx:
        execution_order.append("sync_after")
        return ctx

    def link(ctx: Ctx) -> Ctx:
        execution_order.append("link")
        return ctx

    test_chain = chain(link)
    test_chain.use.before([async_before, sync_before])
    test_chain.use.after([async_after, sync_after])
    result = await test_chain({})

    expected_order = [
        "async_before",
        "sync_before",
        "link",
        "async_after",
        "sync_after",
    ]
    assert execution_order == expected_order


@pytest.mark.asyncio
async def test_chain_context_preservation():
    """Test that context is properly preserved through chain."""

    def link1(ctx: Ctx) -> Ctx:
        ctx["from_link1"] = "value1"
        return ctx

    def link2(ctx: Ctx) -> Ctx:
        ctx["from_link2"] = "value2"
        return ctx

    test_chain = chain(link1, link2)
    result = await test_chain({"initial": "data"})

    assert result["initial"] == "data"
    assert result["from_link1"] == "value1"
    assert result["from_link2"] == "value2"


@pytest.mark.asyncio
async def test_chain_context_copy():
    """Test that chain creates a copy of the input context."""
    original_ctx = {"data": "original"}

    def modifying_link(ctx: Ctx) -> Ctx:
        ctx["data"] = "modified"
        return ctx

    test_chain = chain(modifying_link)
    result = await test_chain(original_ctx)

    # Original context should be unchanged
    assert original_ctx["data"] == "original"
    assert result["data"] == "modified"


@pytest.mark.asyncio
async def test_middleware_chaining():
    """Test complex middleware chaining with before and after."""
    execution_order = []

    def before1(ctx: Ctx) -> Ctx:
        execution_order.append("before1")
        return ctx

    def before2(ctx: Ctx) -> Ctx:
        execution_order.append("before2")
        return ctx

    def after1(ctx: Ctx) -> Ctx:
        execution_order.append("after1")
        return ctx

    def after2(ctx: Ctx) -> Ctx:
        execution_order.append("after2")
        return ctx

    def link1(ctx: Ctx) -> Ctx:
        execution_order.append("link1")
        return ctx

    def link2(ctx: Ctx) -> Ctx:
        execution_order.append("link2")
        return ctx

    test_chain = chain(link1, link2)
    test_chain.use.before([before1, before2])
    test_chain.use.after([after1, after2])
    await test_chain({})

    # Should execute: before1, before2, link1, after1, after2, before1, before2, link2, after1, after2
    expected = [
        "before1",
        "before2",
        "link1",
        "after1",
        "after2",
        "before1",
        "before2",
        "link2",
        "after1",
        "after2",
    ]
    assert execution_order == expected


@pytest.mark.asyncio
async def test_ensure_async_link_functionality():
    """Test the _ensure_async_link internal functionality."""

    def sync_link(ctx: Ctx) -> Ctx:
        ctx["sync_called"] = True
        return ctx

    async def async_link(ctx: Ctx) -> Ctx:
        ctx["async_called"] = True
        return ctx

    test_chain = chain(sync_link, async_link)
    result = await test_chain({})

    assert result["sync_called"] is True
    assert result["async_called"] is True


def test_chain_instance_type_checking():
    """Test that ChainInstance is properly typed and callable."""

    def sample_link(ctx: Ctx) -> Ctx:
        return ctx

    test_chain = chain(sample_link)

    # Test that it's callable
    assert callable(test_chain)

    # Test that it has the expected type structure
    assert hasattr(test_chain, "__call__")
    assert asyncio.iscoroutinefunction(test_chain.__call__)


@pytest.mark.asyncio
async def test_empty_middleware_lists():
    """Test behavior with empty middleware lists."""

    def link(ctx: Ctx) -> Ctx:
        ctx["executed"] = True
        return ctx

    test_chain = chain(link)
    test_chain.use.before([])
    test_chain.use.after([])

    result = await test_chain({})
    assert result["executed"] is True


@pytest.mark.asyncio
async def test_context_error_field_preservation():
    """Test that existing error field is preserved/handled correctly."""

    def link_with_error_check(ctx: Ctx) -> Ctx:
        if ctx.get("error"):
            ctx["error_was_present"] = True
        return ctx

    test_chain = chain(link_with_error_check)
    result = await test_chain({"error": "pre-existing error"})

    # The link should not execute if there's already an error
    assert "error_was_present" not in result
    assert result["error"] == "pre-existing error"
