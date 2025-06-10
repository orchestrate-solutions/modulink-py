"""Tests for connection and networking utilities."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modulink import Ctx
from modulink.types import ConnectionType


def test_connect_imports_and_exports():
    """Test that all connect-related exports are available."""
    # Core connect module
    import modulink.connect

    assert modulink.connect is not None

    # Test connection handlers registry
    from modulink.connect import CONNECTION_HANDLERS

    assert isinstance(CONNECTION_HANDLERS, dict)

    # Test connection type enum
    try:
        from modulink import ConnectionType

        assert ConnectionType is not None
        assert hasattr(ConnectionType, "HTTP")
        assert hasattr(ConnectionType, "CRON")
        assert hasattr(ConnectionType, "CLI")
        assert hasattr(ConnectionType, "MESSAGE")
    except ImportError:
        pytest.skip("ConnectionType not exported from main module yet")


def test_connection_handlers_registry():
    """Test that all connection handlers are registered."""
    from modulink.connect import CONNECTION_HANDLERS

    # Test that all expected connection types have handlers
    expected_types = [
        ConnectionType.HTTP,
        ConnectionType.CRON,
        ConnectionType.CLI,
        ConnectionType.MESSAGE,
    ]

    for conn_type in expected_types:
        assert conn_type in CONNECTION_HANDLERS
        assert callable(CONNECTION_HANDLERS[conn_type])


def test_parse_cron_expression():
    """Test cron expression parsing utility."""
    from modulink.connect import _parse_cron_expression

    # Test basic cron expression
    result = _parse_cron_expression("0 12 * * *")
    expected = {
        "minute": "0",
        "hour": "12",
        "day": "*",
        "month": "*",
        "day_of_week": "*",
    }
    assert result == expected

    # Test complex cron expression
    result = _parse_cron_expression("30 14 1 */2 MON")
    expected = {
        "minute": "30",
        "hour": "14",
        "day": "1",
        "month": "*/2",
        "day_of_week": "MON",
    }
    assert result == expected

    # Test with extra whitespace
    result = _parse_cron_expression("  0   6   *   *   *  ")
    expected = {
        "minute": "0",
        "hour": "6",
        "day": "*",
        "month": "*",
        "day_of_week": "*",
    }
    assert result == expected


@patch("modulink.connect.Request")
@patch("modulink.connect.JSONResponse")
def test_handle_http_connection_basic(mock_json_response, mock_request):
    """Test basic HTTP connection handling."""
    from modulink.connect import _handle_http_connection

    # Mock objects
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "http", "test": "context"}

    mock_chain_fn = AsyncMock(return_value={"result": "success"})

    mock_app = Mock()
    mock_app.add_api_route = Mock()

    # Test HTTP connection setup
    kwargs = {"app": mock_app, "method": "GET", "path": "/api/test"}

    _handle_http_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Verify route was added
    mock_app.add_api_route.assert_called_once()
    call_args = mock_app.add_api_route.call_args
    assert call_args[0][0] == "/api/test"  # path
    assert call_args[1]["methods"] == ["GET"]  # methods


def test_handle_http_connection_missing_params():
    """Test HTTP connection with missing required parameters."""
    from modulink.connect import _handle_http_connection

    mock_modulink = Mock()
    mock_chain_fn = Mock()

    # Test missing app
    with pytest.raises(ValueError, match="HTTP connection requires 'app' parameter"):
        _handle_http_connection(
            mock_modulink, mock_chain_fn, method="GET", path="/test"
        )

    # Test missing method
    with pytest.raises(ValueError, match="HTTP connection requires 'method' parameter"):
        _handle_http_connection(mock_modulink, mock_chain_fn, app=Mock(), path="/test")

    # Test missing path
    with pytest.raises(ValueError, match="HTTP connection requires 'path' parameter"):
        _handle_http_connection(mock_modulink, mock_chain_fn, app=Mock(), method="GET")


@patch("modulink.connect.datetime")
def test_handle_cron_connection_basic(mock_datetime):
    """Test basic cron connection handling."""
    from modulink.connect import _handle_cron_connection

    # Mock datetime
    mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"

    # Mock objects
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "cron", "test": "context"}

    mock_chain_fn = Mock(return_value={"result": "success"})
    mock_chain_fn.__name__ = "test_chain"

    mock_scheduler = Mock()
    mock_scheduler.add_job = Mock()

    # Test cron connection setup
    kwargs = {"scheduler": mock_scheduler, "cron_expression": "0 12 * * *"}

    _handle_cron_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Verify job was added
    mock_scheduler.add_job.assert_called_once()
    call_args = mock_scheduler.add_job.call_args
    assert call_args[1]["minute"] == "0"
    assert call_args[1]["hour"] == "12"
    assert call_args[1]["day"] == "*"
    assert call_args[1]["month"] == "*"
    assert call_args[1]["day_of_week"] == "*"


def test_handle_cron_connection_missing_params():
    """Test cron connection with missing required parameters."""
    from modulink.connect import _handle_cron_connection

    mock_modulink = Mock()
    mock_chain_fn = Mock()

    # Test missing scheduler
    with pytest.raises(
        ValueError, match="Cron connection requires 'scheduler' parameter"
    ):
        _handle_cron_connection(
            mock_modulink, mock_chain_fn, cron_expression="0 12 * * *"
        )

    # Test missing cron_expression
    with pytest.raises(
        ValueError, match="Cron connection requires 'cron_expression' parameter"
    ):
        _handle_cron_connection(mock_modulink, mock_chain_fn, scheduler=Mock())


@patch("modulink.connect.click")
@patch("modulink.connect.datetime")
def test_handle_cli_connection_basic(mock_datetime, mock_click):
    """Test basic CLI connection handling."""
    from modulink.connect import _handle_cli_connection

    # Mock datetime
    mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"

    # Mock objects
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "cli", "test": "context"}

    mock_chain_fn = Mock(return_value={"result": "success"})
    mock_chain_fn.__name__ = "test_command"

    mock_cli_group = Mock()
    mock_cli_group.command = Mock()

    # Test CLI connection setup
    kwargs = {"cli_group": mock_cli_group, "command_name": "test-cmd"}

    _handle_cli_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Verify command was added
    mock_cli_group.command.assert_called_once_with("test-cmd")


def test_handle_cli_connection_missing_params():
    """Test CLI connection with missing required parameters."""
    from modulink.connect import _handle_cli_connection

    mock_modulink = Mock()
    mock_chain_fn = Mock()

    # Test missing cli_group
    with pytest.raises(
        ValueError, match="CLI connection requires 'cli_group' parameter"
    ):
        _handle_cli_connection(mock_modulink, mock_chain_fn, command_name="test")

    # Test missing command_name
    with pytest.raises(
        ValueError, match="CLI connection requires 'command_name' parameter"
    ):
        _handle_cli_connection(mock_modulink, mock_chain_fn, cli_group=Mock())


@patch("modulink.connect.datetime")
def test_handle_message_connection_basic(mock_datetime):
    """Test basic message connection handling."""
    from modulink.connect import _handle_message_connection

    # Mock datetime
    mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"

    # Mock objects
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "message", "test": "context"}

    mock_chain_fn = Mock(return_value={"result": "success"})

    # Test message connection setup
    kwargs = {"topic": "test.topic"}

    result = _handle_message_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Verify handler was created
    assert "handler" in result
    assert "topic" in result
    assert result["topic"] == "test.topic"
    assert callable(result["handler"])


def test_handle_message_connection_missing_params():
    """Test message connection with missing required parameters."""
    from modulink.connect import _handle_message_connection

    mock_modulink = Mock()
    mock_chain_fn = Mock()

    # Test missing topic
    with pytest.raises(
        ValueError, match="Message connection requires 'topic' parameter"
    ):
        _handle_message_connection(mock_modulink, mock_chain_fn)


@pytest.mark.asyncio
async def test_http_handler_get_request():
    """Test HTTP handler with GET request."""
    from modulink.connect import _handle_http_connection

    # Mock objects
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "http", "method": "GET"}

    mock_chain_fn = AsyncMock(return_value={"result": "success"})

    mock_app = Mock()
    captured_handler = None

    def capture_handler(path, handler, methods):
        nonlocal captured_handler
        captured_handler = handler

    mock_app.add_api_route = capture_handler

    # Setup HTTP connection
    kwargs = {"app": mock_app, "method": "GET", "path": "/api/test"}

    _handle_http_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Test the captured handler
    assert captured_handler is not None

    # Mock request object
    mock_request = Mock()
    mock_request.method = "GET"
    mock_request.url.path = "/api/test"
    mock_request.query_params = {}
    mock_request.headers = {"content-type": "application/json"}

    with patch("modulink.connect.JSONResponse") as mock_json_response:
        await captured_handler(mock_request)
        mock_json_response.assert_called_once()


@pytest.mark.asyncio
async def test_http_handler_post_request():
    """Test HTTP handler with POST request."""
    from modulink.connect import _handle_http_connection

    # Mock objects
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "http", "method": "POST"}

    mock_chain_fn = AsyncMock(return_value={"result": "success"})

    mock_app = Mock()
    captured_handler = None

    def capture_handler(path, handler, methods):
        nonlocal captured_handler
        captured_handler = handler

    mock_app.add_api_route = capture_handler

    # Setup HTTP connection
    kwargs = {"app": mock_app, "method": "POST", "path": "/api/create"}

    _handle_http_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Test the captured handler with POST data
    mock_request = Mock()
    mock_request.method = "POST"
    mock_request.url.path = "/api/create"
    mock_request.query_params = {}
    mock_request.headers = {"content-type": "application/json"}
    mock_request.json = AsyncMock(return_value={"data": "test"})

    with patch("modulink.connect.JSONResponse") as mock_json_response:
        await captured_handler(mock_request)
        mock_json_response.assert_called_once()


@pytest.mark.asyncio
async def test_http_handler_error_handling():
    """Test HTTP handler error handling."""
    from modulink.connect import _handle_http_connection

    # Mock objects that will cause an error
    mock_modulink = Mock()
    mock_modulink.create_context.side_effect = Exception("Context creation failed")

    mock_chain_fn = AsyncMock()

    mock_app = Mock()
    captured_handler = None

    def capture_handler(path, handler, methods):
        nonlocal captured_handler
        captured_handler = handler

    mock_app.add_api_route = capture_handler

    # Setup HTTP connection
    kwargs = {"app": mock_app, "method": "GET", "path": "/api/error"}

    _handle_http_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Test error handling
    mock_request = Mock()
    mock_request.method = "GET"
    mock_request.url.path = "/api/error"
    mock_request.query_params = {}
    mock_request.headers = {}

    with patch("modulink.connect.JSONResponse") as mock_json_response:
        await captured_handler(mock_request)
        # Should be called with error response
        call_args = mock_json_response.call_args
        assert call_args[0][0]["success"] is False
        assert call_args[1]["status_code"] == 400


@patch("modulink.connect.datetime")
def test_cron_job_execution(mock_datetime):
    """Test cron job execution."""
    from modulink.connect import _handle_cron_connection

    # Mock datetime
    mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"

    # Mock objects
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "cron", "executed": True}

    mock_chain_fn = Mock(return_value={"result": "cron_success"})
    mock_chain_fn.__name__ = "cron_test"

    mock_scheduler = Mock()
    captured_job = None

    def capture_job(job_func, trigger_type, **cron_params):
        nonlocal captured_job
        captured_job = job_func

    mock_scheduler.add_job = capture_job

    # Setup cron connection
    kwargs = {"scheduler": mock_scheduler, "cron_expression": "0 0 * * *"}

    _handle_cron_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Execute the captured job function
    assert captured_job is not None
    with patch("builtins.print") as mock_print:
        captured_job()
        # Verify print statements were called
        assert mock_print.call_count >= 2


@patch("modulink.connect.datetime")
def test_cron_job_error_handling(mock_datetime):
    """Test cron job error handling."""
    from modulink.connect import _handle_cron_connection

    # Mock datetime
    mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"

    # Mock objects that will cause an error
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "cron"}

    mock_chain_fn = Mock(side_effect=Exception("Cron execution failed"))
    mock_chain_fn.__name__ = "failing_cron"

    mock_scheduler = Mock()
    captured_job = None

    def capture_job(job_func, trigger_type, **cron_params):
        nonlocal captured_job
        captured_job = job_func

    mock_scheduler.add_job = capture_job

    # Setup cron connection
    kwargs = {"scheduler": mock_scheduler, "cron_expression": "0 0 * * *"}

    _handle_cron_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Execute the captured job function
    with patch("builtins.print") as mock_print:
        captured_job()
        # Should print error message
        error_calls = [
            call for call in mock_print.call_args_list if "error" in str(call)
        ]
        assert len(error_calls) > 0


@patch("modulink.connect.click")
@patch("modulink.connect.datetime")
def test_cli_command_execution(mock_datetime, mock_click):
    """Test CLI command execution."""
    from modulink.connect import _handle_cli_connection

    # Mock datetime
    mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"

    # Set up click mock to behave like real click
    def mock_option(*args, **kwargs):
        def decorator(func):
            return func  # Just return the function unchanged

        return decorator

    mock_click.option = mock_option

    # Mock objects
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "cli", "executed": True}

    mock_chain_fn = Mock(return_value={"result": "cli_success"})

    mock_cli_group = Mock()
    captured_command = None

    def capture_command(name):
        def decorator(func):
            nonlocal captured_command
            captured_command = func
            return func

        return decorator

    mock_cli_group.command = capture_command

    # Setup CLI connection
    kwargs = {"cli_group": mock_cli_group, "command_name": "test-cmd"}

    _handle_cli_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Execute the captured command
    assert captured_command is not None
    with patch("builtins.print") as mock_print:
        captured_command("test.txt")
        # Verify print statements were called
        assert mock_print.call_count >= 2


@patch("modulink.connect.click")
@patch("modulink.connect.datetime")
def test_cli_command_error_handling(mock_datetime, mock_click):
    """Test CLI command error handling."""
    from modulink.connect import _handle_cli_connection

    # Mock datetime
    mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"

    # Set up click mock to behave like real click
    def mock_option(*args, **kwargs):
        def decorator(func):
            return func  # Just return the function unchanged

        return decorator

    mock_click.option = mock_option

    # Mock objects that will cause an error
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "cli"}

    mock_chain_fn = Mock(side_effect=Exception("CLI execution failed"))

    mock_cli_group = Mock()
    captured_command = None

    def capture_command(name):
        def decorator(func):
            nonlocal captured_command
            captured_command = func
            return func

        return decorator

    mock_cli_group.command = capture_command

    # Setup CLI connection
    kwargs = {"cli_group": mock_cli_group, "command_name": "failing-cmd"}

    _handle_cli_connection(mock_modulink, mock_chain_fn, **kwargs)

    # Execute the captured command with error handling
    with patch("builtins.print") as mock_print, patch("builtins.exit") as mock_exit:
        captured_command("test.txt")
        # Should print error and exit
        error_calls = [
            call for call in mock_print.call_args_list if "error" in str(call)
        ]
        assert len(error_calls) > 0
        mock_exit.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_message_handler_execution():
    """Test message handler execution."""
    from modulink.connect import _handle_message_connection

    # Mock objects
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {
        "type": "message",
        "topic": "test.topic",
        "message": {"data": "test"},
    }

    mock_chain_fn = Mock(return_value={"result": "message_success"})

    # Setup message connection
    kwargs = {"topic": "test.topic"}

    result = _handle_message_connection(mock_modulink, mock_chain_fn, **kwargs)
    handler = result["handler"]

    # Execute the handler
    with patch("builtins.print") as mock_print:
        message_result = await handler({"data": "test_message"})
        assert message_result["result"] == "message_success"
        # Verify print statements were called
        assert mock_print.call_count >= 2


@pytest.mark.asyncio
async def test_message_handler_error_handling():
    """Test message handler error handling."""
    from modulink.connect import _handle_message_connection

    # Mock objects that will cause an error
    mock_modulink = Mock()
    mock_modulink.create_context.return_value = {"type": "message"}

    mock_chain_fn = Mock(side_effect=Exception("Message processing failed"))

    # Setup message connection
    kwargs = {"topic": "error.topic"}

    result = _handle_message_connection(mock_modulink, mock_chain_fn, **kwargs)
    handler = result["handler"]

    # Execute the handler and expect error
    with patch("builtins.print") as mock_print:
        with pytest.raises(Exception, match="Message processing failed"):
            await handler({"data": "test_message"})
        # Should print error message
        error_calls = [
            call for call in mock_print.call_args_list if "error" in str(call)
        ]
        assert len(error_calls) > 0


def test_connection_type_integration():
    """Test integration with ConnectionType enum."""
    from modulink.connect import CONNECTION_HANDLERS

    # Test that we can use ConnectionType values to access handlers
    http_handler = CONNECTION_HANDLERS[ConnectionType.HTTP]
    cron_handler = CONNECTION_HANDLERS[ConnectionType.CRON]
    cli_handler = CONNECTION_HANDLERS[ConnectionType.CLI]
    message_handler = CONNECTION_HANDLERS[ConnectionType.MESSAGE]

    assert callable(http_handler)
    assert callable(cron_handler)
    assert callable(cli_handler)
    assert callable(message_handler)


def test_connection_handler_function_signatures():
    """Test that all connection handlers have consistent signatures."""
    from modulink.connect import CONNECTION_HANDLERS

    # All handlers should accept (modulink, chain_fn, **kwargs)
    for conn_type, handler in CONNECTION_HANDLERS.items():
        # Test that handlers are callable
        assert callable(handler)

        # Test that they have the expected parameter count
        import inspect

        sig = inspect.signature(handler)
        params = list(sig.parameters.keys())

        # Should have at least 3 parameters: modulink, chain_fn, **kwargs
        assert len(params) >= 2
        assert params[0] == "modulink"
        assert params[1] == "chain_fn"


def test_internal_function_accessibility():
    """Test that internal functions are accessible for testing."""
    # Test that we can import internal functions for testing
    from modulink.connect import (
        _handle_cli_connection,
        _handle_cron_connection,
        _handle_http_connection,
        _handle_message_connection,
        _parse_cron_expression,
    )

    assert callable(_handle_http_connection)
    assert callable(_handle_cron_connection)
    assert callable(_handle_cli_connection)
    assert callable(_handle_message_connection)
    assert callable(_parse_cron_expression)


def test_module_level_constants():
    """Test module-level constants and registries."""
    from modulink.connect import CONNECTION_HANDLERS

    # Test that CONNECTION_HANDLERS is properly structured
    assert isinstance(CONNECTION_HANDLERS, dict)
    assert len(CONNECTION_HANDLERS) == 4  # HTTP, CRON, CLI, MESSAGE

    # Test that all values are callable
    for handler in CONNECTION_HANDLERS.values():
        assert callable(handler)
