"""Tests for core functionality."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modulink import Ctx
from modulink.types import ConnectionType, Status


def test_core_imports_and_exports():
    """Test that all core-related exports are available."""
    # Core factory function
    from modulink.core import create_modulink

    assert callable(create_modulink)

    # ModulinkOptions class
    from modulink.core import ModulinkOptions

    assert ModulinkOptions is not None

    # Test that we can create an instance
    modulink = create_modulink()
    assert modulink is not None


def test_modulink_options_defaults():
    """Test ModulinkOptions default values."""
    from modulink.core import ModulinkOptions

    options = ModulinkOptions()

    assert options.environment == "development"
    assert options.enable_logging is True


def test_modulink_options_custom_values():
    """Test ModulinkOptions with custom values."""
    from modulink.core import ModulinkOptions

    options = ModulinkOptions(environment="production", enable_logging=False)

    assert options.environment == "production"
    assert options.enable_logging is False


def test_create_modulink_basic():
    """Test basic ModuLink instance creation."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    # Test basic instance attributes
    assert hasattr(modulink, "use")
    assert hasattr(modulink, "when")
    assert hasattr(modulink, "cleanup")
    assert hasattr(modulink, "connect")
    assert hasattr(modulink, "environment")
    assert hasattr(modulink, "enable_logging")
    assert hasattr(modulink, "app")


def test_create_modulink_with_app():
    """Test ModuLink instance creation with app."""
    from modulink.core import create_modulink

    mock_app = Mock()
    modulink = create_modulink(app=mock_app)

    assert modulink.app is mock_app


def test_create_modulink_with_options():
    """Test ModuLink instance creation with custom options."""
    from modulink.core import ModulinkOptions, create_modulink

    options = ModulinkOptions(environment="testing", enable_logging=False)

    modulink = create_modulink(options=options)

    assert modulink.environment == "testing"
    assert modulink.enable_logging is False


def test_middleware_interface_structure():
    """Test MiddlewareInterface structure and methods."""
    from modulink.core import create_modulink

    modulink = create_modulink()
    middleware_interface = modulink.use

    # Test that it has the expected methods
    assert hasattr(middleware_interface, "global_middleware")
    assert callable(middleware_interface.global_middleware)


@pytest.mark.asyncio
async def test_global_middleware_registration():
    """Test global middleware registration."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    # Mock middleware function
    async def test_middleware(ctx: Ctx) -> Ctx:
        ctx["middleware_executed"] = True
        return ctx

    # Should not raise any errors
    modulink.use.global_middleware(test_middleware)


def test_convenience_methods_structure():
    """Test ConvenienceMethods structure and methods."""
    from modulink.core import create_modulink

    modulink = create_modulink()
    convenience = modulink.when

    # Test that it has the expected methods
    assert hasattr(convenience, "http")
    assert hasattr(convenience, "cron")
    assert hasattr(convenience, "message")
    assert hasattr(convenience, "cli")

    # All should be callable
    assert callable(convenience.http)
    assert callable(convenience.cron)
    assert callable(convenience.message)
    assert callable(convenience.cli)


@pytest.mark.asyncio
async def test_convenience_http_method():
    """Test convenience HTTP method."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def test_link(ctx: Ctx) -> Ctx:
        ctx["link_executed"] = True
        return ctx

    handler = modulink.when.http(test_link)

    # Should return an async function
    assert callable(handler)
    assert asyncio.iscoroutinefunction(handler)

    # Test execution
    result = await handler({"test": "data"})
    assert result["link_executed"] is True
    assert result["test"] == "data"


@pytest.mark.asyncio
async def test_convenience_cron_method():
    """Test convenience cron method."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def test_link(ctx: Ctx) -> Ctx:
        ctx["cron_executed"] = True
        return ctx

    handler = modulink.when.cron(test_link)

    # Should return an async function
    assert callable(handler)
    assert asyncio.iscoroutinefunction(handler)

    # Test execution
    result = await handler({"scheduled": True})
    assert result["cron_executed"] is True
    assert result["scheduled"] is True


@pytest.mark.asyncio
async def test_convenience_message_method():
    """Test convenience message method."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def test_link(ctx: Ctx) -> Ctx:
        ctx["message_processed"] = True
        return ctx

    handler = modulink.when.message(test_link)

    # Should return an async function
    assert callable(handler)
    assert asyncio.iscoroutinefunction(handler)

    # Test execution
    result = await handler({"message": "test"})
    assert result["message_processed"] is True
    assert result["message"] == "test"


@pytest.mark.asyncio
async def test_convenience_cli_method():
    """Test convenience CLI method."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def test_link(ctx: Ctx) -> Ctx:
        ctx["cli_executed"] = True
        return ctx

    handler = modulink.when.cli(test_link)

    # Should return an async function
    assert callable(handler)
    assert asyncio.iscoroutinefunction(handler)

    # Test execution
    result = await handler({"command": "test"})
    assert result["cli_executed"] is True
    assert result["command"] == "test"


@pytest.mark.asyncio
async def test_convenience_methods_with_multiple_links():
    """Test convenience methods with multiple links."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def link1(ctx: Ctx) -> Ctx:
        ctx["step1"] = True
        return ctx

    def link2(ctx: Ctx) -> Ctx:
        ctx["step2"] = True
        return ctx

    handler = modulink.when.http(link1, link2)
    result = await handler({})

    assert result["step1"] is True
    assert result["step2"] is True


@pytest.mark.asyncio
async def test_convenience_methods_with_global_middleware():
    """Test that convenience methods apply global middleware."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    # Register global middleware
    async def global_mw(ctx: Ctx) -> Ctx:
        ctx["global_middleware_applied"] = True
        return ctx

    modulink.use.global_middleware(global_mw)

    def test_link(ctx: Ctx) -> Ctx:
        ctx["link_executed"] = True
        return ctx

    handler = modulink.when.http(test_link)
    result = await handler({})

    assert result["global_middleware_applied"] is True
    assert result["link_executed"] is True


@pytest.mark.asyncio
async def test_convenience_methods_error_handling():
    """Test error handling in convenience methods."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def failing_link(ctx: Ctx) -> Ctx:
        raise ValueError("Test error")

    def recovery_link(ctx: Ctx) -> Ctx:
        ctx["recovery_attempted"] = True
        return ctx

    handler = modulink.when.http(failing_link, recovery_link)
    result = await handler({})

    # Error should stop execution
    assert "error" in result
    assert "recovery_attempted" not in result


@pytest.mark.asyncio
async def test_convenience_methods_with_async_links():
    """Test convenience methods with async links."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    async def async_link(ctx: Ctx) -> Ctx:
        await asyncio.sleep(0.01)
        ctx["async_executed"] = True
        return ctx

    def sync_link(ctx: Ctx) -> Ctx:
        ctx["sync_executed"] = True
        return ctx

    handler = modulink.when.http(async_link, sync_link)
    result = await handler({})

    assert result["async_executed"] is True
    assert result["sync_executed"] is True


def test_cleanup_basic():
    """Test basic cleanup functionality."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    # Add some global middleware
    async def test_middleware(ctx: Ctx) -> Ctx:
        return ctx

    modulink.use.global_middleware(test_middleware)

    # Test cleanup
    result = modulink.cleanup()

    assert isinstance(result, dict)
    assert "status" in result
    assert "message" in result
    assert result["status"] == Status.SUCCESS


def test_cleanup_error_handling():
    """Test cleanup error handling."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    # This should succeed without errors
    result = modulink.cleanup()

    assert result["status"] == Status.SUCCESS
    assert "error" not in result


@patch("modulink.core.print")
def test_logging_enabled(mock_print):
    """Test logging when enabled."""
    from modulink.core import ModulinkOptions, create_modulink

    options = ModulinkOptions(enable_logging=True)
    modulink = create_modulink(options=options)

    # Add middleware to trigger logging
    async def test_middleware(ctx: Ctx) -> Ctx:
        return ctx

    modulink.use.global_middleware(test_middleware)

    # Should have printed log message
    mock_print.assert_called_with("[ModuLink] Global middleware registered")


@patch("modulink.core.print")
def test_logging_disabled(mock_print):
    """Test logging when disabled."""
    from modulink.core import ModulinkOptions, create_modulink

    options = ModulinkOptions(enable_logging=False)
    modulink = create_modulink(options=options)

    # Add middleware to trigger logging
    async def test_middleware(ctx: Ctx) -> Ctx:
        return ctx

    modulink.use.global_middleware(test_middleware)

    # Should not have printed anything
    mock_print.assert_not_called()


def test_ensure_async_link_sync_function():
    """Test _ensure_async_link with sync function."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def sync_link(ctx: Ctx) -> Ctx:
        ctx["sync_called"] = True
        return ctx

    # Access the internal function through convenience method
    handler = modulink.when.http(sync_link)

    # Should be async
    assert asyncio.iscoroutinefunction(handler)


def test_ensure_async_link_async_function():
    """Test _ensure_async_link with async function."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    async def async_link(ctx: Ctx) -> Ctx:
        ctx["async_called"] = True
        return ctx

    # Access the internal function through convenience method
    handler = modulink.when.http(async_link)

    # Should be async
    assert asyncio.iscoroutinefunction(handler)


def test_connect_method_exists():
    """Test that connect method exists and is callable."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    assert hasattr(modulink, "connect")
    assert callable(modulink.connect)


def test_connect_with_http_connection_type():
    """Test connect method with HTTP connection type."""
    from modulink.core import create_modulink

    mock_app = Mock()
    modulink = create_modulink(app=mock_app)

    def test_chain(ctx: Ctx) -> Ctx:
        return ctx

    # Test with enum
    with patch("modulink.core.CONNECTION_HANDLERS") as mock_handlers:
        mock_handler = Mock()
        mock_handlers.__getitem__.return_value = mock_handler
        mock_handlers.__contains__.return_value = True  # Fix the 'in' operator

        modulink.connect(
            ConnectionType.HTTP, test_chain, app=mock_app, method="GET", path="/test"
        )

        # Should have called the handler
        mock_handler.assert_called_once()


def test_connect_with_string_connection_type():
    """Test connect method with string connection type (backward compatibility)."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def test_chain(ctx: Ctx) -> Ctx:
        return ctx

    # Test with string that maps to enum
    with patch("modulink.core.CONNECTION_HANDLERS") as mock_handlers:
        mock_handler = Mock()
        mock_handlers.__getitem__.return_value = mock_handler
        mock_handlers.__contains__.return_value = True  # Fix the 'in' operator

        modulink.connect("http", test_chain, app=Mock(), method="GET", path="/test")

        # Should have called the handler
        mock_handler.assert_called_once()


def test_connect_invalid_connection_type():
    """Test connect method with invalid connection type."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def test_chain(ctx: Ctx) -> Ctx:
        return ctx

    # Test with invalid string
    with pytest.raises(ValueError, match="Unsupported connection type"):
        modulink.connect("invalid_type", test_chain)

    # Test with invalid type
    with pytest.raises(
        TypeError, match="connection_type must be a ConnectionType enum"
    ):
        modulink.connect(123, test_chain)


def test_connect_unsupported_connection_type():
    """Test connect method with unsupported connection type enum."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def test_chain(ctx: Ctx) -> Ctx:
        return ctx

    # Mock a ConnectionType that's not in handlers
    with patch("modulink.core.CONNECTION_HANDLERS", {}):
        with pytest.raises(ValueError, match="Unsupported connection type"):
            modulink.connect(ConnectionType.HTTP, test_chain)


def test_modulink_instance_attributes():
    """Test ModuLinkInstance has all expected attributes."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    # Test all expected attributes exist
    assert hasattr(modulink, "use")
    assert hasattr(modulink, "when")
    assert hasattr(modulink, "cleanup")
    assert hasattr(modulink, "connect")
    assert hasattr(modulink, "environment")
    assert hasattr(modulink, "enable_logging")
    assert hasattr(modulink, "app")


def test_modulink_instance_environment_config():
    """Test ModuLinkInstance environment configuration."""
    from modulink.core import ModulinkOptions, create_modulink

    options = ModulinkOptions(environment="staging", enable_logging=False)

    modulink = create_modulink(options=options)

    assert modulink.environment == "staging"
    assert modulink.enable_logging is False


def test_internal_state_isolation():
    """Test that different ModuLink instances have isolated state."""
    from modulink.core import create_modulink

    modulink1 = create_modulink()
    modulink2 = create_modulink()

    # Add middleware to first instance
    async def middleware1(ctx: Ctx) -> Ctx:
        ctx["instance1"] = True
        return ctx

    async def middleware2(ctx: Ctx) -> Ctx:
        ctx["instance2"] = True
        return ctx

    modulink1.use.global_middleware(middleware1)
    modulink2.use.global_middleware(middleware2)

    # They should be isolated
    assert modulink1 is not modulink2
    assert modulink1.use is not modulink2.use
    assert modulink1.when is not modulink2.when


@pytest.mark.asyncio
async def test_global_middleware_error_propagation():
    """Test that errors in global middleware are properly propagated."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    async def failing_middleware(ctx: Ctx) -> Ctx:
        ctx["error"] = ValueError("Middleware failed")
        return ctx

    async def normal_middleware(ctx: Ctx) -> Ctx:
        ctx["normal_middleware"] = True
        return ctx

    modulink.use.global_middleware(failing_middleware)
    modulink.use.global_middleware(normal_middleware)

    def test_link(ctx: Ctx) -> Ctx:
        ctx["link_executed"] = True
        return ctx

    handler = modulink.when.http(test_link)
    result = await handler({})

    # Error should stop further middleware and link execution
    assert "error" in result
    assert "normal_middleware" not in result
    assert "link_executed" not in result


@pytest.mark.asyncio
async def test_multiple_global_middleware_execution_order():
    """Test execution order of multiple global middleware."""
    from modulink.core import create_modulink

    modulink = create_modulink()
    execution_order = []

    async def middleware1(ctx: Ctx) -> Ctx:
        execution_order.append("middleware1")
        return ctx

    async def middleware2(ctx: Ctx) -> Ctx:
        execution_order.append("middleware2")
        return ctx

    async def middleware3(ctx: Ctx) -> Ctx:
        execution_order.append("middleware3")
        return ctx

    modulink.use.global_middleware(middleware1)
    modulink.use.global_middleware(middleware2)
    modulink.use.global_middleware(middleware3)

    def test_link(ctx: Ctx) -> Ctx:
        execution_order.append("link")
        return ctx

    handler = modulink.when.http(test_link)
    await handler({})

    assert execution_order == ["middleware1", "middleware2", "middleware3", "link"]


def test_modulink_instance_class_structure():
    """Test ModuLinkInstance class structure and methods."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    # Test instance type
    assert modulink.__class__.__name__ == "ModuLinkInstance"

    # Test that methods are bound properly
    assert modulink.use.__class__.__name__ == "MiddlewareInterface"
    assert modulink.when.__class__.__name__ == "ConvenienceMethods"
    assert callable(modulink.cleanup)
    assert callable(modulink.connect)


@pytest.mark.asyncio
async def test_context_copying_in_convenience_methods():
    """Test that convenience methods properly copy context."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def modifying_link(ctx: Ctx) -> Ctx:
        ctx["modified"] = True
        return ctx

    handler = modulink.when.http(modifying_link)

    original_ctx = {"original": "data"}
    result = await handler(original_ctx)

    # Original should be unchanged
    assert "modified" not in original_ctx
    assert result["modified"] is True
    assert result["original"] == "data"


def test_factory_function_signature():
    """Test create_modulink factory function signature and defaults."""
    import inspect

    from modulink.core import ModulinkOptions, create_modulink

    sig = inspect.signature(create_modulink)
    params = list(sig.parameters.keys())

    # Should have app and options parameters
    assert "app" in params
    assert "options" in params

    # Both should have defaults
    assert sig.parameters["app"].default is None
    assert sig.parameters["options"].default is None


def test_modulink_instance_docstring_accuracy():
    """Test that ModuLinkInstance has proper docstring."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    # Class should have docstring
    assert modulink.__class__.__doc__ is not None
    assert "ModuLink instance" in modulink.__class__.__doc__
    assert "middleware" in modulink.__class__.__doc__


@pytest.mark.asyncio
async def test_convenience_methods_single_link_as_chain():
    """Test that convenience methods treat single links as 1-dimensional chains."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def single_link(ctx: Ctx) -> Ctx:
        ctx["single_link_executed"] = True
        return ctx

    # Test all convenience methods with single link
    http_handler = modulink.when.http(single_link)
    cron_handler = modulink.when.cron(single_link)
    message_handler = modulink.when.message(single_link)
    cli_handler = modulink.when.cli(single_link)

    # All should be async functions
    assert asyncio.iscoroutinefunction(http_handler)
    assert asyncio.iscoroutinefunction(cron_handler)
    assert asyncio.iscoroutinefunction(message_handler)
    assert asyncio.iscoroutinefunction(cli_handler)

    # All should execute the single link
    for handler in [http_handler, cron_handler, message_handler, cli_handler]:
        result = await handler({"initial": "data"})
        assert result["single_link_executed"] is True
        assert result["initial"] == "data"


@pytest.mark.asyncio
async def test_convenience_methods_single_vs_multiple_links():
    """Test that single link and multiple links behave consistently."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def link1(ctx: Ctx) -> Ctx:
        ctx["link1_executed"] = True
        return ctx

    def link2(ctx: Ctx) -> Ctx:
        ctx["link2_executed"] = True
        return ctx

    # Single link (1-dimensional chain)
    single_handler = modulink.when.http(link1)

    # Multiple links (multi-dimensional chain)
    multi_handler = modulink.when.http(link1, link2)

    # Test single link execution
    single_result = await single_handler({})
    assert single_result["link1_executed"] is True
    assert "link2_executed" not in single_result

    # Test multiple links execution
    multi_result = await multi_handler({})
    assert multi_result["link1_executed"] is True
    assert multi_result["link2_executed"] is True


@pytest.mark.asyncio
async def test_convenience_methods_global_middleware_with_single_link():
    """Test that global middleware applies to single links treated as chains."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    # Register global middleware
    async def global_middleware(ctx: Ctx) -> Ctx:
        ctx["global_applied"] = True
        return ctx

    modulink.use.global_middleware(global_middleware)

    def single_link(ctx: Ctx) -> Ctx:
        ctx["link_executed"] = True
        return ctx

    # Single link should get global middleware
    handler = modulink.when.http(single_link)
    result = await handler({})

    assert result["global_applied"] is True
    assert result["link_executed"] is True


@pytest.mark.asyncio
async def test_convenience_methods_error_handling_single_link():
    """Test error handling with single links treated as chains."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def failing_link(ctx: Ctx) -> Ctx:
        raise ValueError("Single link error")

    handler = modulink.when.http(failing_link)
    result = await handler({})

    # Error should be captured in context
    assert "error" in result
    assert isinstance(result["error"], ValueError)
    assert str(result["error"]) == "Single link error"


def test_connect_with_single_link():
    """Test connect method with single link treated as 1-dimensional chain."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def single_link(ctx: Ctx) -> Ctx:
        ctx["single_link_connected"] = True
        return ctx

    # Test with single link
    with patch("modulink.core.CONNECTION_HANDLERS") as mock_handlers:
        mock_handler = Mock()
        mock_handlers.__getitem__.return_value = mock_handler
        mock_handlers.__contains__.return_value = True  # Fix the 'in' operator

        modulink.connect(
            ConnectionType.HTTP, single_link, app=Mock(), method="GET", path="/test"
        )

        # Should have called the handler with wrapped single link
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args

        # The chain_fn argument should be a wrapped version of the single link
        wrapped_chain = call_args[0][1]
        assert callable(wrapped_chain)
        assert asyncio.iscoroutinefunction(wrapped_chain)


@pytest.mark.asyncio
async def test_connect_single_link_execution():
    """Test that connected single links execute properly."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    execution_log = []

    def single_link(ctx: Ctx) -> Ctx:
        execution_log.append("single_link_executed")
        ctx["result"] = "success"
        return ctx

    # Mock the connection handler to capture the wrapped chain
    captured_chain = None

    def mock_handler(handler_modulink, chain_fn, **kwargs):
        nonlocal captured_chain
        captured_chain = chain_fn
        return {"success": True}

    with patch(
        "modulink.core.CONNECTION_HANDLERS", {ConnectionType.HTTP: mock_handler}
    ):
        modulink.connect(
            ConnectionType.HTTP, single_link, app=Mock(), method="GET", path="/test"
        )

    # Execute the captured chain to verify it works
    assert captured_chain is not None
    result = await captured_chain({"input": "data"})

    assert execution_log == ["single_link_executed"]
    assert result["result"] == "success"
    assert result["input"] == "data"


def test_single_link_chain_compatibility_principle():
    """Test the fundamental principle: single link should work anywhere a chain works."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def single_link(ctx: Ctx) -> Ctx:
        ctx["processed"] = True
        return ctx

    def multi_link1(ctx: Ctx) -> Ctx:
        ctx["step1"] = True
        return ctx

    def multi_link2(ctx: Ctx) -> Ctx:
        ctx["step2"] = True
        return ctx

    # All convenience methods should accept single links
    single_handlers = [
        modulink.when.http(single_link),
        modulink.when.cron(single_link),
        modulink.when.message(single_link),
        modulink.when.cli(single_link),
    ]

    # All convenience methods should accept multiple links
    multi_handlers = [
        modulink.when.http(multi_link1, multi_link2),
        modulink.when.cron(multi_link1, multi_link2),
        modulink.when.message(multi_link1, multi_link2),
        modulink.when.cli(multi_link1, multi_link2),
    ]

    # All handlers should be async functions
    for handler in single_handlers + multi_handlers:
        assert callable(handler)
        assert asyncio.iscoroutinefunction(handler)

    # Connect should accept single links for all connection types
    with patch("modulink.core.CONNECTION_HANDLERS") as mock_handlers:
        mock_handler = Mock(return_value={"success": True})
        mock_handlers.__getitem__.return_value = mock_handler
        mock_handlers.__contains__.return_value = True  # Fix the 'in' operator

        # Test all connection types with single link
        for conn_type in [
            ConnectionType.HTTP,
            ConnectionType.CRON,
            ConnectionType.CLI,
            ConnectionType.MESSAGE,
        ]:
            modulink.connect(
                conn_type,
                single_link,
                topic="test" if conn_type == ConnectionType.MESSAGE else None,
            )
            assert mock_handler.called


def test_create_chain_handler_internal_method():
    """Test the internal _create_chain_handler method that unifies link handling."""
    from modulink.core import create_modulink

    modulink = create_modulink()
    convenience = modulink.when

    # Test that _create_chain_handler exists and is callable
    assert hasattr(convenience, "_create_chain_handler")
    assert callable(convenience._create_chain_handler)

    def test_link(ctx: Ctx) -> Ctx:
        ctx["test"] = True
        return ctx

    # Should create an async handler
    handler = convenience._create_chain_handler(test_link)
    assert callable(handler)
    assert asyncio.iscoroutinefunction(handler)


@pytest.mark.asyncio
async def test_async_single_link_support():
    """Test that async single links work properly as 1-dimensional chains."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    async def async_single_link(ctx: Ctx) -> Ctx:
        await asyncio.sleep(0.01)
        ctx["async_single"] = True
        return ctx

    handler = modulink.when.http(async_single_link)
    result = await handler({})

    assert result["async_single"] is True


@pytest.mark.asyncio
async def test_mixed_single_and_multiple_link_patterns():
    """Test mixing single links and multiple links in the same application."""
    from modulink.core import create_modulink

    modulink = create_modulink()

    def auth_link(ctx: Ctx) -> Ctx:
        ctx["authenticated"] = True
        return ctx

    def data_link(ctx: Ctx) -> Ctx:
        ctx["data_fetched"] = True
        return ctx

    def simple_link(ctx: Ctx) -> Ctx:
        ctx["simple_operation"] = True
        return ctx

    # Create handlers with different patterns
    auth_only = modulink.when.http(auth_link)  # Single link
    auth_and_data = modulink.when.http(auth_link, data_link)  # Multiple links
    simple_operation = modulink.when.message(simple_link)  # Single link, different type

    # All should work consistently
    auth_result = await auth_only({})
    complex_result = await auth_and_data({})
    simple_result = await simple_operation({})

    assert auth_result["authenticated"] is True
    assert "data_fetched" not in auth_result

    assert complex_result["authenticated"] is True
    assert complex_result["data_fetched"] is True

    assert simple_result["simple_operation"] is True
