"""Tests for event triggers and reactive patterns."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modulink import Ctx


def test_triggers_imports_and_exports():
    """Test that all trigger-related exports are available."""
    # Core trigger functions
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    assert callable(http_trigger)
    assert callable(cron_trigger)
    assert callable(message_trigger)
    assert callable(cli_trigger)

    # Triggers dictionary
    from modulink.triggers import triggers

    assert isinstance(triggers, dict)
    assert "http" in triggers
    assert "cron" in triggers
    assert "message" in triggers
    assert "cli" in triggers

    # All should be callable
    for trigger_name, trigger_func in triggers.items():
        assert callable(trigger_func)


def test_triggers_dictionary_completeness():
    """Test that triggers dictionary contains all expected trigger functions."""
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
        triggers,
    )

    assert triggers["http"] == http_trigger
    assert triggers["cron"] == cron_trigger
    assert triggers["message"] == message_trigger
    assert triggers["cli"] == cli_trigger


def test_trigger_type_annotations():
    """Test that trigger functions have proper type annotations."""
    import inspect

    from modulink.triggers import http_trigger

    sig = inspect.signature(http_trigger)

    # Should have path, methods, and optional app parameters
    assert "path" in sig.parameters
    assert "methods" in sig.parameters
    assert "app" in sig.parameters

    # app should have default None
    assert sig.parameters["app"].default is None


@pytest.mark.asyncio
async def test_http_trigger_basic():
    """Test basic HTTP trigger functionality."""
    from modulink.triggers import http_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        ctx["processed"] = True
        ctx["method"] = ctx.get("method", "unknown")
        return ctx

    # Create trigger without app (manual integration)
    trigger = http_trigger("/api/test", ["GET", "POST"])
    result = await trigger(test_chain, {"initial": "data"})

    assert result["success"] is True
    assert "handler" in result
    assert result["path"] == "/api/test"
    assert result["methods"] == ["GET", "POST"]
    assert callable(result["handler"])


@pytest.mark.asyncio
async def test_http_trigger_manual_handler():
    """Test HTTP trigger manual handler execution."""
    from modulink.triggers import http_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        ctx["processed"] = True
        ctx["request_method"] = ctx.get("method", "GET")
        return ctx

    trigger = http_trigger("/api/manual", ["POST"])
    result = await trigger(test_chain)

    handler = result["handler"]

    # Test handler execution
    request_data = {
        "method": "POST",
        "query": {"param": "value"},
        "body": {"data": "test"},
        "headers": {"Content-Type": "application/json"},
    }

    handler_result = await handler(request_data)

    assert handler_result["processed"] is True
    assert handler_result["request_method"] == "POST"
    assert handler_result["method"] == "POST"
    assert handler_result["query"] == {"param": "value"}


@pytest.mark.asyncio
async def test_http_trigger_with_fastapi_app():
    """Test HTTP trigger with FastAPI app integration."""
    from modulink.triggers import http_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        ctx["fastapi_processed"] = True
        return ctx

    # Mock FastAPI app
    mock_app = Mock()
    mock_app.add_api_route = Mock()

    trigger = http_trigger("/api/fastapi", ["GET"], app=mock_app)
    result = await trigger(test_chain, {"service": "test"})

    assert result["success"] is True
    assert result["path"] == "/api/fastapi"
    assert result["methods"] == ["GET"]

    # Verify route was added
    mock_app.add_api_route.assert_called_once()
    call_args = mock_app.add_api_route.call_args
    assert call_args[0][0] == "/api/fastapi"  # path
    assert callable(call_args[0][1])  # handler
    assert call_args[1]["methods"] == ["GET"]


@pytest.mark.asyncio
async def test_http_trigger_fastapi_handler_execution():
    """Test FastAPI handler execution with request processing."""
    from modulink.triggers import http_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        ctx["processed"] = True
        ctx["request_path"] = ctx.get("path", "unknown")
        return ctx

    mock_app = Mock()
    captured_handler = None

    def capture_handler(path, handler, methods):
        nonlocal captured_handler
        captured_handler = handler

    mock_app.add_api_route = capture_handler

    trigger = http_trigger("/api/test", ["POST"], app=mock_app)
    await trigger(test_chain)

    # Test the captured handler
    assert captured_handler is not None

    # Mock request object
    mock_request = Mock()
    mock_request.method = "POST"
    mock_request.url.path = "/api/test"
    mock_request.query_params = {"param": "value"}
    mock_request.headers = {"Content-Type": "application/json"}
    mock_request.json = AsyncMock(return_value={"data": "test"})

    result = await captured_handler(mock_request)

    assert result["processed"] is True
    assert result["request_path"] == "/api/test"
    assert result["method"] == "POST"


@pytest.mark.asyncio
async def test_http_trigger_fastapi_error_handling():
    """Test FastAPI handler error handling."""
    from modulink.triggers import http_trigger

    async def failing_chain(ctx: Ctx) -> Ctx:
        raise ValueError("Chain execution failed")

    mock_app = Mock()
    captured_handler = None

    def capture_handler(path, handler, methods):
        nonlocal captured_handler
        captured_handler = handler

    mock_app.add_api_route = capture_handler

    trigger = http_trigger("/api/error", ["GET"], app=mock_app)
    await trigger(failing_chain)

    # Test error handling
    mock_request = Mock()
    mock_request.method = "GET"
    mock_request.url.path = "/api/error"
    mock_request.query_params = {}
    mock_request.headers = {}

    result = await captured_handler(mock_request)

    assert "error" in result
    assert "Chain execution failed" in str(result["error"])


@pytest.mark.asyncio
async def test_http_trigger_context_creation():
    """Test HTTP trigger context creation with all fields."""
    from modulink.triggers import http_trigger

    captured_context = None

    async def context_capturing_chain(ctx: Ctx) -> Ctx:
        nonlocal captured_context
        captured_context = ctx.copy()
        return ctx

    trigger = http_trigger("/api/context", ["GET"])
    result = await trigger(context_capturing_chain, {"initial": "data"})

    handler = result["handler"]

    request_data = {
        "request": {"mock": "request"},
        "method": "GET",
        "query": {"q": "search"},
        "body": {"field": "value"},
        "headers": {"Authorization": "Bearer token"},
    }

    await handler(request_data)

    # Verify context was created with all expected fields
    assert captured_context is not None
    assert captured_context["type"] == "http"
    assert captured_context["method"] == "GET"
    assert captured_context["path"] == "/api/context"
    assert captured_context["query"] == {"q": "search"}
    assert captured_context["body"] == {"field": "value"}
    assert captured_context["headers"] == {"Authorization": "Bearer token"}
    assert captured_context["initial"] == "data"


@pytest.mark.asyncio
async def test_cron_trigger_basic():
    """Test basic cron trigger functionality."""
    from modulink.triggers import cron_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        ctx["cron_executed"] = True
        ctx["schedule"] = ctx.get("schedule", "unknown")
        return ctx

    trigger = cron_trigger("0 12 * * *")
    result = await trigger(test_chain, {"job": "daily_backup"})

    assert result["success"] is True
    assert result["schedule"] == "0 12 * * *"
    assert "execute" in result
    assert callable(result["execute"])


@pytest.mark.asyncio
async def test_cron_trigger_execution():
    """Test cron trigger job execution."""
    from modulink.triggers import cron_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        ctx["executed_at"] = ctx.get("scheduled_at", "unknown")
        ctx["job_completed"] = True
        return ctx

    trigger = cron_trigger("*/5 * * * *")
    result = await trigger(test_chain, {"task": "cleanup"})

    execute_func = result["execute"]
    execution_result = await execute_func()

    assert execution_result["job_completed"] is True
    assert execution_result["type"] == "cron"
    assert execution_result["schedule"] == "*/5 * * * *"
    assert execution_result["task"] == "cleanup"
    assert "scheduled_at" in execution_result


@pytest.mark.asyncio
async def test_cron_trigger_error_handling():
    """Test cron trigger error handling."""
    from modulink.triggers import cron_trigger

    async def failing_chain(ctx: Ctx) -> Ctx:
        raise ValueError("Cron job failed")

    trigger = cron_trigger("0 0 * * *")
    result = await trigger(failing_chain)

    execute_func = result["execute"]
    execution_result = await execute_func()

    assert "error" in execution_result
    assert "Cron job failed" in str(execution_result["error"])


@pytest.mark.asyncio
async def test_cron_trigger_context_creation():
    """Test cron trigger context creation."""
    from modulink.triggers import cron_trigger

    captured_context = None

    async def context_capturing_chain(ctx: Ctx) -> Ctx:
        nonlocal captured_context
        captured_context = ctx.copy()
        return ctx

    trigger = cron_trigger("0 6 * * MON")
    result = await trigger(context_capturing_chain, {"environment": "production"})

    execute_func = result["execute"]
    await execute_func()

    assert captured_context is not None
    assert captured_context["type"] == "cron"
    assert captured_context["schedule"] == "0 6 * * MON"
    assert captured_context["environment"] == "production"
    assert "scheduled_at" in captured_context


@pytest.mark.asyncio
async def test_message_trigger_basic():
    """Test basic message trigger functionality."""
    from modulink.triggers import message_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        ctx["message_processed"] = True
        ctx["topic"] = ctx.get("topic", "unknown")
        return ctx

    trigger = message_trigger("user.created")
    result = await trigger(test_chain, {"service": "users"})

    assert result["success"] is True
    assert result["topic"] == "user.created"
    assert "handler" in result
    assert callable(result["handler"])


@pytest.mark.asyncio
async def test_message_trigger_handler_execution():
    """Test message trigger handler execution."""
    from modulink.triggers import message_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        ctx["processed"] = True
        ctx["message_data"] = ctx.get("message", {})
        return ctx

    trigger = message_trigger("order.completed")
    result = await trigger(test_chain, {"service": "orders"})

    handler = result["handler"]
    message_data = {"order_id": "12345", "status": "completed"}

    handler_result = await handler(message_data)

    assert handler_result["processed"] is True
    assert handler_result["type"] == "message"
    assert handler_result["topic"] == "order.completed"
    assert handler_result["message"] == message_data
    assert handler_result["service"] == "orders"


@pytest.mark.asyncio
async def test_message_trigger_error_handling():
    """Test message trigger error handling."""
    from modulink.triggers import message_trigger

    async def failing_chain(ctx: Ctx) -> Ctx:
        raise ValueError("Message processing failed")

    trigger = message_trigger("error.topic")
    result = await trigger(failing_chain)

    handler = result["handler"]

    handler_result = await handler({"data": "test"})

    assert "error" in handler_result
    assert "Message processing failed" in str(handler_result["error"])


@pytest.mark.asyncio
async def test_message_trigger_context_creation():
    """Test message trigger context creation."""
    from modulink.triggers import message_trigger

    captured_context = None

    async def context_capturing_chain(ctx: Ctx) -> Ctx:
        nonlocal captured_context
        captured_context = ctx.copy()
        return ctx

    trigger = message_trigger("payment.processed")
    result = await trigger(context_capturing_chain, {"processor": "stripe"})

    handler = result["handler"]
    message = {"payment_id": "pay_123", "amount": 1000}

    await handler(message)

    assert captured_context is not None
    assert captured_context["type"] == "message"
    assert captured_context["topic"] == "payment.processed"
    assert captured_context["message"] == message
    assert captured_context["processor"] == "stripe"
    assert "received_at" in captured_context


@pytest.mark.asyncio
async def test_cli_trigger_basic():
    """Test basic CLI trigger functionality."""
    from modulink.triggers import cli_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        ctx["cli_executed"] = True
        ctx["command"] = ctx.get("command", "unknown")
        return ctx

    trigger = cli_trigger("deploy")
    result = await trigger(test_chain, {"environment": "staging"})

    assert result["success"] is True
    assert result["command"] == "deploy"
    assert "handler" in result
    assert callable(result["handler"])


@pytest.mark.asyncio
async def test_cli_trigger_handler_execution():
    """Test CLI trigger handler execution."""
    from modulink.triggers import cli_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        ctx["executed"] = True
        ctx["cli_args"] = ctx.get("args", [])
        return ctx

    trigger = cli_trigger("backup")
    result = await trigger(test_chain, {"tool": "rsync"})

    handler = result["handler"]
    args = ["--target", "/backup", "--verbose"]

    handler_result = await handler(args)

    assert handler_result["executed"] is True
    assert handler_result["type"] == "cli"
    assert handler_result["command"] == "backup"
    assert handler_result["args"] == args
    assert handler_result["tool"] == "rsync"


@pytest.mark.asyncio
async def test_cli_trigger_error_handling():
    """Test CLI trigger error handling."""
    from modulink.triggers import cli_trigger

    async def failing_chain(ctx: Ctx) -> Ctx:
        raise ValueError("CLI command failed")

    trigger = cli_trigger("failing-command")
    result = await trigger(failing_chain)

    handler = result["handler"]

    handler_result = await handler(["--force"])

    assert "error" in handler_result
    assert "CLI command failed" in str(handler_result["error"])


@pytest.mark.asyncio
async def test_cli_trigger_context_creation():
    """Test CLI trigger context creation."""
    from modulink.triggers import cli_trigger

    captured_context = None

    async def context_capturing_chain(ctx: Ctx) -> Ctx:
        nonlocal captured_context
        captured_context = ctx.copy()
        return ctx

    trigger = cli_trigger("migrate")
    result = await trigger(context_capturing_chain, {"database": "production"})

    handler = result["handler"]
    args = ["--up", "--steps", "5"]

    await handler(args)

    assert captured_context is not None
    assert captured_context["type"] == "cli"
    assert captured_context["command"] == "migrate"
    assert captured_context["args"] == args
    assert captured_context["database"] == "production"
    assert "invoked_at" in captured_context


@pytest.mark.asyncio
async def test_trigger_context_merging():
    """Test that initial context is properly merged with trigger context."""
    from modulink.triggers import http_trigger

    async def test_chain(ctx: Ctx) -> Ctx:
        # Should have both initial and trigger context
        ctx["merged"] = True
        return ctx

    initial_ctx = {"user_id": "123", "session": "abc", "custom_field": "value"}

    trigger = http_trigger("/api/merge", ["POST"])
    result = await trigger(test_chain, initial_ctx)

    handler = result["handler"]
    request_data = {"method": "POST", "body": {"action": "update"}}

    handler_result = await handler(request_data)

    # Should have both initial and trigger-specific context
    assert handler_result["user_id"] == "123"
    assert handler_result["session"] == "abc"
    assert handler_result["custom_field"] == "value"
    assert handler_result["type"] == "http"
    assert handler_result["method"] == "POST"
    assert handler_result["merged"] is True


@pytest.mark.asyncio
async def test_trigger_with_chain_function():
    """Test triggers work with different types of chain functions."""
    from modulink.triggers import message_trigger

    # Test with simple function
    async def simple_chain(ctx: Ctx) -> Ctx:
        ctx["simple"] = True
        return ctx

    # Test with chain instance (if available)
    try:
        from modulink import chain

        def link1(ctx: Ctx) -> Ctx:
            ctx["link1"] = True
            return ctx

        def link2(ctx: Ctx) -> Ctx:
            ctx["link2"] = True
            return ctx

        chain_instance = chain(link1, link2)

        trigger = message_trigger("test.chain")
        result = await trigger(chain_instance)

        handler = result["handler"]
        handler_result = await handler({"test": "data"})

        assert handler_result["link1"] is True
        assert handler_result["link2"] is True

    except ImportError:
        # Chain not available, test with simple function only
        trigger = message_trigger("test.simple")
        result = await trigger(simple_chain)

        handler = result["handler"]
        handler_result = await handler({"test": "data"})

        assert handler_result["simple"] is True


def test_trigger_function_signatures():
    """Test that all trigger functions have consistent signatures."""
    import inspect

    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    # All triggers should return a function that accepts (chain_fn, initial_ctx=None)
    for trigger_func in [http_trigger, cron_trigger, message_trigger, cli_trigger]:
        # Create a trigger instance
        if trigger_func == http_trigger:
            trigger = trigger_func("/test", ["GET"])
        elif trigger_func == cron_trigger:
            trigger = trigger_func("0 * * * *")
        elif trigger_func == message_trigger:
            trigger = trigger_func("test.topic")
        elif trigger_func == cli_trigger:
            trigger = trigger_func("test-cmd")

        # Check the returned trigger signature
        sig = inspect.signature(trigger)
        params = list(sig.parameters.keys())

        assert "target_chain" in params
        assert "initial_ctx" in params
        assert sig.parameters["initial_ctx"].default is None


@pytest.mark.asyncio
async def test_triggers_independence():
    """Test that triggers work independently without ModuLink instance."""
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    async def independent_chain(ctx: Ctx) -> Ctx:
        ctx["independent"] = True
        ctx["trigger_type"] = ctx.get("type", "unknown")
        return ctx

    # Test all triggers work independently
    triggers_to_test = [
        (http_trigger("/test", ["GET"]), "http"),
        (cron_trigger("0 * * * *"), "cron"),
        (message_trigger("test.topic"), "message"),
        (cli_trigger("test-cmd"), "cli"),
    ]

    for trigger, expected_type in triggers_to_test:
        result = await trigger(independent_chain)

        assert result["success"] is True

        if "handler" in result:
            # Test handler execution for triggers that return handlers
            if expected_type == "http":
                handler_result = await result["handler"]({"method": "GET"})
            elif expected_type == "message":
                handler_result = await result["handler"]({"data": "test"})
            elif expected_type == "cli":
                handler_result = await result["handler"](["--test"])
            else:
                continue

            assert handler_result["independent"] is True
            assert handler_result["trigger_type"] == expected_type
        elif "execute" in result:
            # Test execution for cron trigger
            execution_result = await result["execute"]()
            assert execution_result["independent"] is True
            assert execution_result["trigger_type"] == expected_type


@pytest.mark.asyncio
async def test_context_factory_functions():
    """Test that triggers use proper context factory functions."""
    from modulink.triggers import http_trigger

    captured_contexts = []

    async def context_inspecting_chain(ctx: Ctx) -> Ctx:
        captured_contexts.append(ctx.copy())
        return ctx

    # Test HTTP context creation
    trigger = http_trigger("/api/inspect", ["POST"])
    result = await trigger(context_inspecting_chain)

    handler = result["handler"]
    request_data = {
        "request": {"mock": "request"},
        "method": "POST",
        "query": {"param": "value"},
        "body": {"data": "test"},
        "headers": {"Authorization": "Bearer token"},
    }

    await handler(request_data)

    # Verify the context was created properly
    assert len(captured_contexts) == 1
    http_ctx = captured_contexts[0]

    # Should have all HTTP context fields
    assert http_ctx["type"] == "http"
    assert http_ctx["method"] == "POST"
    assert http_ctx["path"] == "/api/inspect"
    assert http_ctx["query"] == {"param": "value"}
    assert http_ctx["body"] == {"data": "test"}
    assert http_ctx["headers"] == {"Authorization": "Bearer token"}
    assert "request" in http_ctx


def test_triggers_module_structure():
    """Test the overall triggers module structure."""
    import modulink.triggers as triggers_module

    # Test that all expected functions are available
    expected_functions = [
        "http_trigger",
        "cron_trigger",
        "message_trigger",
        "cli_trigger",
    ]
    for func_name in expected_functions:
        assert hasattr(triggers_module, func_name)
        assert callable(getattr(triggers_module, func_name))

    # Test triggers dictionary
    assert hasattr(triggers_module, "triggers")
    assert isinstance(triggers_module.triggers, dict)
    assert len(triggers_module.triggers) == 4

    # Test module docstring
    assert triggers_module.__doc__ is not None
    assert "ModuLink Standalone Triggers" in triggers_module.__doc__


@pytest.mark.asyncio
async def test_trigger_response_consistency():
    """Test that all triggers return consistent response structures."""
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    async def dummy_chain(ctx: Ctx) -> Ctx:
        return ctx

    # Test all triggers return success and type-specific fields
    http_result = await http_trigger("/test", ["GET"])(dummy_chain)
    cron_result = await cron_trigger("0 * * * *")(dummy_chain)
    message_result = await message_trigger("test.topic")(dummy_chain)
    cli_result = await cli_trigger("test-cmd")(dummy_chain)

    # All should have success field
    for result in [http_result, cron_result, message_result, cli_result]:
        assert "success" in result
        assert result["success"] is True

    # Check type-specific fields
    assert "path" in http_result and "methods" in http_result
    assert "schedule" in cron_result and "execute" in cron_result
    assert "topic" in message_result and "handler" in message_result
    assert "command" in cli_result and "handler" in cli_result


@pytest.mark.asyncio
async def test_triggers_with_single_links():
    """Test that triggers properly handle single links as 1-dimensional chains."""
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    def single_auth_link(ctx: Ctx) -> Ctx:
        ctx["authenticated"] = True
        ctx["user_id"] = ctx.get("user_id", "default_user")
        return ctx

    # Test HTTP trigger with single link
    http_trigger_func = http_trigger("/api/auth", ["POST"])
    http_result = await http_trigger_func(single_auth_link, {"service": "auth"})

    assert http_result["success"] is True
    handler = http_result["handler"]

    request_data = {
        "method": "POST",
        "body": {"username": "test", "password": "secret"},
        "headers": {"Content-Type": "application/json"},
    }

    auth_result = await handler(request_data)
    assert auth_result["authenticated"] is True
    assert auth_result["service"] == "auth"
    assert auth_result["type"] == "http"
    assert auth_result["method"] == "POST"


@pytest.mark.asyncio
async def test_triggers_single_vs_multiple_links():
    """Test that single links work consistently compared to multiple links."""
    from modulink.triggers import message_trigger

    def auth_link(ctx: Ctx) -> Ctx:
        ctx["authenticated"] = True
        return ctx

    def data_link(ctx: Ctx) -> Ctx:
        ctx["data_processed"] = True
        return ctx

    # Test with chain function (multiple links)
    try:
        from modulink.chain import chain

        multi_chain = chain(auth_link, data_link)

        trigger_multi = message_trigger("user.multi")
        result_multi = await trigger_multi(multi_chain, {"source": "multi"})

        handler_multi = result_multi["handler"]
        multi_result = await handler_multi({"user_id": "123"})

        assert multi_result["authenticated"] is True
        assert multi_result["data_processed"] is True
        assert multi_result["source"] == "multi"

    except ImportError:
        # Chain not available, skip this part
        pass

    # Test with single link (1-dimensional chain)
    trigger_single = message_trigger("user.single")
    result_single = await trigger_single(auth_link, {"source": "single"})

    handler_single = result_single["handler"]
    single_result = await handler_single({"user_id": "123"})

    assert single_result["authenticated"] is True
    assert "data_processed" not in single_result  # Only auth_link executed
    assert single_result["source"] == "single"


@pytest.mark.asyncio
async def test_http_trigger_single_link_integration():
    """Test HTTP trigger with single link and comprehensive context."""
    from modulink.triggers import http_trigger

    def user_lookup_link(ctx: Ctx) -> Ctx:
        user_id = ctx.get("query", {}).get("user_id")
        if user_id:
            ctx["user"] = {"id": user_id, "name": f"User_{user_id}"}
            ctx["lookup_successful"] = True
        else:
            ctx["error"] = "user_id required"
        return ctx

    trigger = http_trigger("/api/user", ["GET"])
    result = await trigger(user_lookup_link, {"version": "v1"})

    handler = result["handler"]

    # Test successful lookup
    request_data = {
        "method": "GET",
        "query": {"user_id": "42"},
        "headers": {"Authorization": "Bearer token123"},
    }

    lookup_result = await handler(request_data)

    assert lookup_result["lookup_successful"] is True
    assert lookup_result["user"]["id"] == "42"
    assert lookup_result["user"]["name"] == "User_42"
    assert lookup_result["version"] == "v1"
    assert lookup_result["type"] == "http"
    assert lookup_result["method"] == "GET"
    assert lookup_result["path"] == "/api/user"

    # Test failed lookup
    request_data_no_id = {"method": "GET", "query": {}, "headers": {}}

    error_result = await handler(request_data_no_id)
    assert "error" in error_result
    assert error_result["error"] == "user_id required"


@pytest.mark.asyncio
async def test_cron_trigger_single_link_execution():
    """Test cron trigger with single link for scheduled operations."""
    from modulink.triggers import cron_trigger

    execution_log = []

    def backup_link(ctx: Ctx) -> Ctx:
        backup_type = ctx.get("backup_type", "incremental")
        execution_log.append(f"backup_{backup_type}")
        ctx["backup_completed"] = True
        ctx["backup_timestamp"] = ctx.get("scheduled_at", "unknown")
        return ctx

    trigger = cron_trigger("0 2 * * *")  # Daily at 2 AM
    result = await trigger(backup_link, {"backup_type": "full", "retention": "30d"})

    assert result["success"] is True
    assert result["schedule"] == "0 2 * * *"

    execute_func = result["execute"]
    backup_result = await execute_func()

    assert execution_log == ["backup_full"]
    assert backup_result["backup_completed"] is True
    assert backup_result["backup_type"] == "full"
    assert backup_result["retention"] == "30d"
    assert backup_result["type"] == "cron"
    assert "scheduled_at" in backup_result


@pytest.mark.asyncio
async def test_message_trigger_single_link_processing():
    """Test message trigger with single link for event processing."""
    from modulink.triggers import message_trigger

    processed_messages = []

    def order_processor_link(ctx: Ctx) -> Ctx:
        message = ctx.get("message", {})
        order_id = message.get("order_id")

        if order_id:
            processed_messages.append(order_id)
            ctx["order_processed"] = True
            ctx["order_id"] = order_id
            ctx["processing_status"] = "completed"
        else:
            ctx["error"] = "Invalid order message"

        return ctx

    trigger = message_trigger("orders.created")
    result = await trigger(
        order_processor_link, {"processor": "main", "region": "us-east"}
    )

    assert result["success"] is True
    assert result["topic"] == "orders.created"

    handler = result["handler"]

    # Test successful processing
    order_message = {"order_id": "ORD-123", "amount": 99.99, "customer": "user123"}
    process_result = await handler(order_message)

    assert processed_messages == ["ORD-123"]
    assert process_result["order_processed"] is True
    assert process_result["order_id"] == "ORD-123"
    assert process_result["processing_status"] == "completed"
    assert process_result["processor"] == "main"
    assert process_result["region"] == "us-east"
    assert process_result["type"] == "message"
    assert process_result["topic"] == "orders.created"
    assert process_result["message"] == order_message

    # Test error handling
    invalid_message = {"invalid": "data"}
    error_result = await handler(invalid_message)

    assert "error" in error_result
    assert error_result["error"] == "Invalid order message"


@pytest.mark.asyncio
async def test_cli_trigger_single_link_command():
    """Test CLI trigger with single link for command operations."""
    from modulink.triggers import cli_trigger

    executed_commands = []

    def deploy_link(ctx: Ctx) -> Ctx:
        command = ctx.get("command")
        args = ctx.get("args", [])
        environment = None

        # Parse arguments
        for i, arg in enumerate(args):
            if arg == "--env" and i + 1 < len(args):
                environment = args[i + 1]
                break

        if environment:
            executed_commands.append(f"deploy_to_{environment}")
            ctx["deployment_successful"] = True
            ctx["target_environment"] = environment
            ctx["deployment_id"] = f"deploy_{len(executed_commands)}"
        else:
            ctx["error"] = "Environment not specified"

        return ctx

    trigger = cli_trigger("deploy")
    result = await trigger(deploy_link, {"tool": "kubectl", "cluster": "production"})

    assert result["success"] is True
    assert result["command"] == "deploy"

    handler = result["handler"]

    # Test successful deployment
    deploy_args = ["--env", "staging", "--force", "--timeout", "300"]
    deploy_result = await handler(deploy_args)

    assert executed_commands == ["deploy_to_staging"]
    assert deploy_result["deployment_successful"] is True
    assert deploy_result["target_environment"] == "staging"
    assert deploy_result["deployment_id"] == "deploy_1"
    assert deploy_result["tool"] == "kubectl"
    assert deploy_result["cluster"] == "production"
    assert deploy_result["type"] == "cli"
    assert deploy_result["command"] == "deploy"
    assert deploy_result["args"] == deploy_args

    # Test error handling
    invalid_args = ["--force", "--timeout", "300"]  # Missing --env
    error_result = await handler(invalid_args)

    assert "error" in error_result
    assert error_result["error"] == "Environment not specified"


@pytest.mark.asyncio
async def test_trigger_context_factory_consistency():
    """Test that all triggers create consistent context structures."""
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    captured_contexts = []

    def context_capturing_link(ctx: Ctx) -> Ctx:
        captured_contexts.append(ctx.copy())
        ctx["context_captured"] = True
        return ctx

    # Test HTTP context
    http_trigger_func = http_trigger("/test", ["POST"])
    http_result = await http_trigger_func(
        context_capturing_link, {"source": "http_test"}
    )

    await http_result["handler"](
        {
            "method": "POST",
            "query": {"test": "value"},
            "body": {"data": "test"},
            "headers": {"Auth": "token"},
        }
    )

    # Test cron context
    cron_trigger_func = cron_trigger("0 0 * * *")
    cron_result = await cron_trigger_func(
        context_capturing_link, {"source": "cron_test"}
    )

    await cron_result["execute"]()

    # Test message context
    msg_trigger_func = message_trigger("test.topic")
    msg_result = await msg_trigger_func(context_capturing_link, {"source": "msg_test"})

    await msg_result["handler"]({"message": "data"})

    # Test CLI context
    cli_trigger_func = cli_trigger("test-cmd")
    cli_result = await cli_trigger_func(context_capturing_link, {"source": "cli_test"})

    await cli_result["handler"](["--flag", "value"])

    # Verify all contexts were captured
    assert len(captured_contexts) == 4

    # Verify each context has expected structure
    http_ctx, cron_ctx, msg_ctx, cli_ctx = captured_contexts

    # HTTP context
    assert http_ctx["type"] == "http"
    assert http_ctx["method"] == "POST"
    assert http_ctx["path"] == "/test"
    assert http_ctx["source"] == "http_test"
    assert "query" in http_ctx
    assert "body" in http_ctx
    assert "headers" in http_ctx

    # Cron context
    assert cron_ctx["type"] == "cron"
    assert cron_ctx["schedule"] == "0 0 * * *"
    assert cron_ctx["source"] == "cron_test"
    assert "scheduled_at" in cron_ctx

    # Message context
    assert msg_ctx["type"] == "message"
    assert msg_ctx["topic"] == "test.topic"
    assert msg_ctx["source"] == "msg_test"
    assert msg_ctx["message"] == {"message": "data"}
    assert "received_at" in msg_ctx

    # CLI context
    assert cli_ctx["type"] == "cli"
    assert cli_ctx["command"] == "test-cmd"
    assert cli_ctx["source"] == "cli_test"
    assert cli_ctx["args"] == ["--flag", "value"]
    assert "invoked_at" in cli_ctx


@pytest.mark.asyncio
async def test_trigger_error_propagation():
    """Test that errors in single links are properly propagated through triggers."""
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    def failing_link(ctx: Ctx) -> Ctx:
        error_type = ctx.get("error_type", "general")
        raise ValueError(f"Test {error_type} error")

    # Test HTTP error propagation
    http_trigger_func = http_trigger("/error", ["GET"])
    http_result = await http_trigger_func(failing_link, {"error_type": "http"})

    http_error_result = await http_result["handler"]({"method": "GET"})
    assert "error" in http_error_result
    assert "Test http error" in str(http_error_result["error"])

    # Test cron error propagation
    cron_trigger_func = cron_trigger("0 * * * *")
    cron_result = await cron_trigger_func(failing_link, {"error_type": "cron"})

    cron_error_result = await cron_result["execute"]()
    assert "error" in cron_error_result
    assert "Test cron error" in str(cron_error_result["error"])

    # Test message error propagation
    msg_trigger_func = message_trigger("error.topic")
    msg_result = await msg_trigger_func(failing_link, {"error_type": "message"})

    msg_error_result = await msg_result["handler"]({"data": "test"})
    assert "error" in msg_error_result
    assert "Test message error" in str(msg_error_result["error"])

    # Test CLI error propagation
    cli_trigger_func = cli_trigger("error-cmd")
    cli_result = await cli_trigger_func(failing_link, {"error_type": "cli"})

    cli_error_result = await cli_result["handler"](["--test"])
    assert "error" in cli_error_result
    assert "Test cli error" in str(cli_error_result["error"])


@pytest.mark.asyncio
async def test_async_single_links_in_triggers():
    """Test that async single links work properly in all triggers."""
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    async def async_processing_link(ctx: Ctx) -> Ctx:
        await asyncio.sleep(0.01)  # Simulate async work
        ctx["async_processed"] = True
        ctx["processing_delay"] = 0.01
        return ctx

    # Test with HTTP trigger
    http_trigger_func = http_trigger("/async", ["POST"])
    http_result = await http_trigger_func(async_processing_link, {"processor": "async"})

    http_handler_result = await http_result["handler"](
        {"method": "POST", "data": "test"}
    )
    assert http_handler_result["async_processed"] is True
    assert http_handler_result["processor"] == "async"

    # Test with cron trigger
    cron_trigger_func = cron_trigger("0 */2 * * *")
    cron_result = await cron_trigger_func(async_processing_link, {"processor": "async"})

    cron_execution_result = await cron_result["execute"]()
    assert cron_execution_result["async_processed"] is True
    assert cron_execution_result["processor"] == "async"

    # Test with message trigger
    msg_trigger_func = message_trigger("async.processing")
    msg_result = await msg_trigger_func(async_processing_link, {"processor": "async"})

    msg_handler_result = await msg_result["handler"]({"async": "data"})
    assert msg_handler_result["async_processed"] is True
    assert msg_handler_result["processor"] == "async"

    # Test with CLI trigger
    cli_trigger_func = cli_trigger("async-process")
    cli_result = await cli_trigger_func(async_processing_link, {"processor": "async"})

    cli_handler_result = await cli_result["handler"](["--async", "true"])
    assert cli_handler_result["async_processed"] is True
    assert cli_handler_result["processor"] == "async"


def test_trigger_single_link_principle_compliance():
    """Test that triggers comply with the 'single link as 1-dimensional chain' principle."""
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    def simple_link(ctx: Ctx) -> Ctx:
        ctx["simple_operation"] = True
        return ctx

    # All trigger functions should accept single links without requiring wrapping
    triggers_to_test = [
        http_trigger("/simple", ["GET"]),
        cron_trigger("0 0 * * *"),
        message_trigger("simple.topic"),
        cli_trigger("simple-cmd"),
    ]

    for trigger in triggers_to_test:
        # Should be able to pass a single link directly
        assert callable(trigger)

        # Trigger should accept the single link without errors
        # (This tests the signature compliance)
        import inspect

        sig = inspect.signature(trigger)
        params = list(sig.parameters.keys())

        assert "target_chain" in params
        assert "initial_ctx" in params


@pytest.mark.asyncio
async def test_trigger_response_structure_consistency():
    """Test that all triggers return consistent response structures."""
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    def dummy_link(ctx: Ctx) -> Ctx:
        ctx["processed"] = True
        return ctx

    # Test all trigger response structures
    http_result = await http_trigger("/test", ["GET"])(dummy_link)
    cron_result = await cron_trigger("0 * * * *")(dummy_link)
    message_result = await message_trigger("test.topic")(dummy_link)
    cli_result = await cli_trigger("test-cmd")(dummy_link)

    # All should have success field
    for result in [http_result, cron_result, message_result, cli_result]:
        assert "success" in result
        assert result["success"] is True

    # Verify specific fields for each trigger type
    assert "path" in http_result and "methods" in http_result
    assert "schedule" in cron_result and "execute" in cron_result
    assert "topic" in message_result and "handler" in message_result
    assert "command" in cli_result and "handler" in cli_result

    # Verify handlers/executors are callable
    assert callable(http_result["handler"])
    assert callable(cron_result["execute"])
    assert callable(message_result["handler"])
    assert callable(cli_result["handler"])


@pytest.mark.asyncio
async def test_trigger_independence_from_modulink():
    """Test that triggers work completely independently from ModuLink instance."""
    from modulink.triggers import (
        cli_trigger,
        cron_trigger,
        http_trigger,
        message_trigger,
    )

    execution_log = []

    def independent_link(ctx: Ctx) -> Ctx:
        execution_log.append(f"independent_{ctx.get('type', 'unknown')}")
        ctx["independent_execution"] = True
        ctx["no_modulink_required"] = True
        return ctx

    # Test that triggers can be created and executed without any ModuLink setup

    # HTTP independence
    http_trigger_func = http_trigger("/independent", ["POST"])
    http_result = await http_trigger_func(independent_link)
    http_execution = await http_result["handler"]({"method": "POST"})

    # Cron independence
    cron_trigger_func = cron_trigger("0 12 * * *")
    cron_result = await cron_trigger_func(independent_link)
    cron_execution = await cron_result["execute"]()

    # Message independence
    msg_trigger_func = message_trigger("independent.topic")
    msg_result = await msg_trigger_func(independent_link)
    msg_execution = await msg_result["handler"]({"independent": "message"})

    # CLI independence
    cli_trigger_func = cli_trigger("independent-cmd")
    cli_result = await cli_trigger_func(independent_link)
    cli_execution = await cli_result["handler"](["--independent"])

    # Verify all executed independently
    assert execution_log == [
        "independent_http",
        "independent_cron",
        "independent_message",
        "independent_cli",
    ]

    # Verify all results show independence
    for result in [http_execution, cron_execution, msg_execution, cli_execution]:
        assert result["independent_execution"] is True
        assert result["no_modulink_required"] is True
