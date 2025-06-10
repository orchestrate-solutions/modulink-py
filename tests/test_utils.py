"""Tests for utility functions and helper implementations."""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Union
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modulink.types import ChainFunction, Ctx, Link, MiddlewareFunction
from modulink.utils import (
    ErrorHandlers,
    Validators,
    _ensure_async_call,
    catch_errors,
    debounce,
    error_handlers,
    filter_context,
    logging,
    memoize,
    parallel,
    performance_tracker,
    retry,
    set_values,
    timing,
    transform,
    validate,
    validators,
    when,
)


def test_utils_imports_and_exports():
    """Test that all utility functions and classes are properly exported."""
    # Conditional and control flow
    from modulink.utils import debounce, parallel, when

    assert callable(when)
    assert callable(parallel)
    assert callable(debounce)

    # Data transformation
    from modulink.utils import filter_context, set_values, transform

    assert callable(transform)
    assert callable(set_values)
    assert callable(filter_context)

    # Middleware functions
    from modulink.utils import catch_errors, logging, memoize, retry, timing, validate

    assert callable(catch_errors)
    assert callable(timing)
    assert callable(logging)
    assert callable(validate)
    assert callable(retry)
    assert callable(memoize)

    # Performance monitoring
    from modulink.utils import performance_tracker

    assert callable(performance_tracker)

    # Error handling and validation classes
    from modulink.utils import ErrorHandlers, Validators

    assert ErrorHandlers is not None
    assert Validators is not None

    # Internal utilities
    from modulink.utils import _ensure_async_call

    assert callable(_ensure_async_call)


def test_chain_not_in_utils():
    """Test that Chain and chain are no longer in utils - they're in chain.py."""
    with pytest.raises(ImportError):
        from modulink.utils import Chain

    with pytest.raises(ImportError):
        from modulink.utils import chain


def test_compose_does_not_exist():
    """Test that compose function has been removed and no longer exists."""
    with pytest.raises(ImportError):
        from modulink.utils import compose


@pytest.mark.asyncio
async def test_catch_errors_middleware_execution():
    """Test catch_errors middleware execution."""

    def error_handler(error, ctx: Ctx) -> Ctx:
        return {**ctx, "handled_error": str(error)}

    error_middleware = catch_errors(error_handler)

    # Test middleware execution (placeholder - actual error catching would be in chain execution)
    result = await error_middleware({"input": "data"})
    assert result["input"] == "data"


@pytest.mark.asyncio
async def test_ensure_async_call_sync_function():
    """Test _ensure_async_call with synchronous functions."""

    def sync_link(ctx: Ctx) -> Ctx:
        ctx["sync_executed"] = True
        return ctx

    result = await _ensure_async_call(sync_link, {"input": "data"})

    assert result["input"] == "data"
    assert result["sync_executed"] is True


@pytest.mark.asyncio
async def test_ensure_async_call_async_function():
    """Test _ensure_async_call with asynchronous functions."""

    async def async_link(ctx: Ctx) -> Ctx:
        await asyncio.sleep(0.01)
        ctx["async_executed"] = True
        return ctx

    result = await _ensure_async_call(async_link, {"input": "data"})

    assert result["input"] == "data"
    assert result["async_executed"] is True


@pytest.mark.asyncio
async def test_ensure_async_call_error_handling():
    """Test _ensure_async_call error capture and handling."""

    def failing_link(ctx: Ctx) -> Ctx:
        raise ValueError("Test error")

    result = await _ensure_async_call(failing_link, {"input": "data"})

    assert result["input"] == "data"
    assert "error" in result
    assert isinstance(result["error"], ValueError)
    assert str(result["error"]) == "Test error"


@pytest.mark.asyncio
async def test_ensure_async_call_non_dict_return():
    """Test _ensure_async_call with non-dict return values."""

    def bad_link(ctx: Ctx) -> str:
        return "not a dict"

    result = await _ensure_async_call(bad_link, {"input": "data"})

    assert result["input"] == "data"
    assert "error" in result
    assert isinstance(result["error"], TypeError)


@pytest.mark.asyncio
async def test_when_conditional_true():
    """Test when utility with true predicate."""

    def predicate(ctx: Ctx) -> bool:
        return ctx.get("should_execute", False)

    def conditional_link(ctx: Ctx) -> Ctx:
        ctx["conditional_executed"] = True
        return ctx

    when_link = when(predicate, conditional_link)
    result = await when_link({"should_execute": True})

    assert result["conditional_executed"] is True


@pytest.mark.asyncio
async def test_when_conditional_false():
    """Test when utility with false predicate."""

    def predicate(ctx: Ctx) -> bool:
        return ctx.get("should_execute", False)

    def conditional_link(ctx: Ctx) -> Ctx:
        ctx["conditional_executed"] = True
        return ctx

    when_link = when(predicate, conditional_link)
    result = await when_link({"should_execute": False})

    assert "conditional_executed" not in result


@pytest.mark.asyncio
async def test_parallel_execution():
    """Test parallel execution using proper chain functionality."""

    def link1(ctx: Ctx) -> Ctx:
        ctx["link1_executed"] = True
        return ctx

    def link2(ctx: Ctx) -> Ctx:
        ctx["link2_executed"] = True
        return ctx

    parallel_link = parallel(link1, link2)
    result = await parallel_link({"initial": "data"})

    assert result["initial"] == "data"
    assert result["link1_executed"] is True
    assert result["link2_executed"] is True


@pytest.mark.asyncio
async def test_debounce_functionality():
    """Test debounce functionality using proper chain functionality."""
    execution_count = {"count": 0}

    def counting_link(ctx: Ctx) -> Ctx:
        execution_count["count"] += 1
        ctx["execution_count"] = execution_count["count"]
        return ctx

    debounced_link = debounce(0.1, counting_link)

    # Rapid calls should be debounced
    await debounced_link({})
    result = await debounced_link({})  # This should be skipped

    assert execution_count["count"] == 1
    assert "execution_count" not in result  # Second call was skipped


@pytest.mark.asyncio
async def test_memoize_caching():
    """Test memoize caching using proper chain functionality."""
    execution_count = {"count": 0}

    def counting_link(ctx: Ctx) -> Ctx:
        execution_count["count"] += 1
        ctx["execution_count"] = execution_count["count"]
        return ctx

    memoized_link = memoize(lambda ctx: "same_key", counting_link, ttl=60.0)

    # First call
    result1 = await memoized_link({"input": "data"})
    # Second call with same key should use cache
    result2 = await memoized_link({"input": "data"})

    assert execution_count["count"] == 1  # Only executed once
    assert result1["execution_count"] == 1
    assert result2["execution_count"] == 1  # Same cached result


@pytest.mark.asyncio
async def test_timing_middleware():
    """Test timing middleware functionality."""
    timing_middleware = timing("test_operation")

    result = await timing_middleware({"input": "data"})

    assert result["input"] == "data"
    assert "timing" in result
    assert "test_operation" in result["timing"]
    assert isinstance(result["timing"]["test_operation"], (int, float))


@pytest.mark.asyncio
async def test_timing_middleware_default_label():
    """Test timing middleware with default label."""
    timing_middleware = timing()

    result = await timing_middleware({"input": "data"})

    assert result["input"] == "data"
    assert "timing" in result
    assert "execution" in result["timing"]


@pytest.mark.asyncio
async def test_logging_middleware():
    """Test logging middleware functionality."""
    with patch("builtins.print") as mock_print:
        logging_middleware = logging()

        result = await logging_middleware({"input": "data"})

        assert result["input"] == "data"
        # Should have called print for input logging
        mock_print.assert_called()


@pytest.mark.asyncio
async def test_logging_middleware_selective():
    """Test logging middleware with selective options."""
    with patch("builtins.print") as mock_print:
        logging_middleware = logging(log_input=False, log_output=True, log_timing=False)

        result = await logging_middleware({"input": "data", "timing": {"test": 123}})

        assert result["input"] == "data"


@pytest.mark.asyncio
async def test_validate_middleware():
    """Test validate middleware functionality."""

    def schema(ctx: Ctx) -> bool:
        return "required_field" in ctx

    validation_middleware = validate(schema)

    # Test valid context
    result = await validation_middleware({"required_field": "value"})
    assert result["required_field"] == "value"
    assert "error" not in result

    # Test invalid context
    result = await validation_middleware({"other_field": "value"})
    assert "error" in result
    assert isinstance(result["error"], Exception)


@pytest.mark.asyncio
async def test_validate_middleware_custom_message():
    """Test validate middleware with custom error message."""

    def schema(ctx: Ctx) -> str:
        if "required_field" not in ctx:
            return "Custom error: required_field is missing"
        return True

    validation_middleware = validate(schema)

    result = await validation_middleware({"other_field": "value"})
    assert "error" in result
    assert "Custom error: required_field is missing" in str(result["error"])


@pytest.mark.asyncio
async def test_retry_middleware():
    """Test retry middleware functionality."""
    retry_middleware = retry(max_attempts=3, delay=0.1)

    # Test with no error
    result = await retry_middleware({"input": "data"})
    assert result["input"] == "data"
    assert result["attempt"] == 1


@pytest.mark.asyncio
async def test_transform_single_link():
    """Test transform utility functionality."""
    uppercase_transform = transform(
        "name", lambda value, ctx: value.upper() if value else ""
    )

    result = await uppercase_transform({"name": "john", "age": 30})

    assert result["name"] == "JOHN"
    assert result["age"] == 30


@pytest.mark.asyncio
async def test_transform_missing_field():
    """Test transform with missing field."""
    default_transform = transform(
        "missing", lambda value, ctx: "default" if value is None else value
    )

    result = await default_transform({"other": "value"})

    assert result["missing"] == "default"
    assert result["other"] == "value"


@pytest.mark.asyncio
async def test_transform_complex_computation():
    """Test transform with complex computation using context."""
    full_name_transform = transform(
        "full_name",
        lambda _, ctx: f"{ctx.get('first_name', '')} {ctx.get('last_name', '')}".strip(),
    )

    result = await full_name_transform({"first_name": "John", "last_name": "Doe"})

    assert result["full_name"] == "John Doe"


@pytest.mark.asyncio
async def test_set_values_single_link():
    """Test set_values utility functionality."""
    set_defaults = set_values({"status": "active", "type": "user"})

    result = await set_defaults({"name": "John"})

    assert result["name"] == "John"
    assert result["status"] == "active"
    assert result["type"] == "user"


@pytest.mark.asyncio
async def test_set_values_override():
    """Test set_values with override behavior."""
    set_values_link = set_values({"status": "new_status"})

    result = await set_values_link({"status": "old_status", "name": "John"})

    assert result["status"] == "new_status"  # Should override
    assert result["name"] == "John"


@pytest.mark.asyncio
async def test_filter_context_single_link():
    """Test filter_context utility functionality."""
    remove_internal = filter_context(lambda key, value: not key.startswith("_"))

    result = await remove_internal(
        {"name": "John", "_internal": "secret", "age": 30, "_debug": "info"}
    )

    assert result["name"] == "John"
    assert result["age"] == 30
    assert "_internal" not in result
    assert "_debug" not in result


@pytest.mark.asyncio
async def test_filter_context_by_type():
    """Test filter_context by value type."""
    strings_only = filter_context(lambda key, value: isinstance(value, str))

    result = await strings_only(
        {"name": "John", "age": 30, "email": "john@example.com", "score": 95.5}
    )

    assert result["name"] == "John"
    assert result["email"] == "john@example.com"
    assert "age" not in result
    assert "score" not in result


@pytest.mark.asyncio
async def test_parallel_error_handling():
    """Test parallel execution with error handling."""

    def good_link(ctx: Ctx) -> Ctx:
        ctx["good"] = True
        return ctx

    def bad_link(ctx: Ctx) -> Ctx:
        raise ValueError("Test error")

    parallel_link = parallel(good_link, bad_link)
    result = await parallel_link({"initial": "data"})

    assert result["initial"] == "data"
    assert result["good"] is True
    assert "error" in result


@pytest.mark.asyncio
async def test_memoize_ttl_expiration():
    """Test memoize TTL expiration."""
    execution_count = {"count": 0}

    def counting_link(ctx: Ctx) -> Ctx:
        execution_count["count"] += 1
        ctx["execution_count"] = execution_count["count"]
        return ctx

    # Very short TTL
    memoized_link = memoize(lambda ctx: "key", counting_link, ttl=0.01)

    # First call
    await memoized_link({"input": "data"})

    # Wait for TTL to expire
    await asyncio.sleep(0.02)

    # Second call should execute again
    await memoized_link({"input": "data"})

    assert execution_count["count"] == 2  # Should have executed twice


@pytest.mark.asyncio
async def test_performance_tracker_middleware():
    """Test performance tracker middleware."""
    perf_middleware = performance_tracker()

    result = await perf_middleware({"input": "data"})

    assert result["input"] == "data"
    assert "performance" in result
    assert isinstance(result["performance"], dict)


def test_catch_errors_middleware():
    """Test catch_errors middleware creation and behavior."""

    def error_handler(error, ctx: Ctx) -> Ctx:
        return {**ctx, "handled_error": str(error)}

    error_middleware = catch_errors(error_handler)

    # Test that it creates middleware
    assert callable(error_middleware)
    assert asyncio.iscoroutinefunction(error_middleware)


def test_error_handlers_class():
    """Test ErrorHandlers class and methods."""
    # Test that ErrorHandlers has expected methods
    assert hasattr(ErrorHandlers, "log_and_continue")
    assert hasattr(ErrorHandlers, "log_and_fail")
    assert hasattr(ErrorHandlers, "retry_on")

    # Test that methods are static
    assert callable(ErrorHandlers.log_and_continue)
    assert callable(ErrorHandlers.log_and_fail)
    assert callable(ErrorHandlers.retry_on)


def test_error_handlers_log_and_continue():
    """Test ErrorHandlers.log_and_continue method."""
    error = ValueError("Test error")
    ctx = {"input": "data"}

    result = ErrorHandlers.log_and_continue(error, ctx)

    assert result["input"] == "data"
    assert "error" in result
    assert result["error"] == error


def test_error_handlers_log_and_fail():
    """Test ErrorHandlers.log_and_fail method."""
    error = ValueError("Test error")
    ctx = {"input": "data"}

    result = ErrorHandlers.log_and_fail(error, ctx)

    assert result["input"] == "data"
    assert "error" in result
    assert result["error"] == error


def test_error_handlers_retry_on():
    """Test ErrorHandlers.retry_on method."""
    retry_handler = ErrorHandlers.retry_on(
        ["ValueError", "ConnectionError"], max_retries=3
    )

    assert callable(retry_handler)

    # Test with retryable error
    retryable_error = ValueError("Connection failed")
    ctx = {"input": "data"}
    result = retry_handler(retryable_error, ctx)

    assert "input" in result


def test_validators_class():
    """Test Validators class and methods."""
    # Test that Validators has expected methods
    assert hasattr(Validators, "required")
    assert hasattr(Validators, "types")
    assert hasattr(Validators, "custom")

    # Test that methods are static
    assert callable(Validators.required)
    assert callable(Validators.types)
    assert callable(Validators.custom)


def test_validators_required():
    """Test Validators.required method."""
    required_validator = Validators.required(["name", "email"])

    assert callable(required_validator)

    # Test with all required fields
    valid_ctx = {"name": "John", "email": "john@example.com", "age": 30}
    result = required_validator(valid_ctx)
    assert result is True

    # Test with missing required field
    invalid_ctx = {"name": "John", "age": 30}
    result = required_validator(invalid_ctx)
    assert isinstance(result, str)
    assert "email" in result


def test_validators_types():
    """Test Validators.types method."""
    type_validator = Validators.types({"age": int, "name": str, "score": float})

    assert callable(type_validator)

    # Test with correct types
    valid_ctx = {"age": 30, "name": "John", "score": 95.5}
    result = type_validator(valid_ctx)
    assert result is True

    # Test with incorrect type
    invalid_ctx = {"age": "thirty", "name": "John", "score": 95.5}
    result = type_validator(invalid_ctx)
    assert isinstance(result, str)
    assert "age" in result


def test_validators_custom():
    """Test Validators.custom method."""

    def business_rule_validator(ctx: Ctx) -> Union[bool, str]:
        age = ctx.get("age", 0)
        if age < 18:
            return "Age must be 18 or older"
        return True

    custom_validator = Validators.custom(business_rule_validator)

    assert callable(custom_validator)

    # Test with valid business rule
    valid_ctx = {"age": 25}
    result = custom_validator(valid_ctx)
    assert result is True

    # Test with invalid business rule
    invalid_ctx = {"age": 16}
    result = custom_validator(invalid_ctx)
    assert isinstance(result, str)


def test_error_handlers_instance():
    """Test error_handlers global instance."""
    from modulink.utils import error_handlers

    assert error_handlers is not None
    assert isinstance(error_handlers, ErrorHandlers)


def test_validators_instance():
    """Test validators global instance."""
    from modulink.utils import validators

    assert validators is not None
    assert isinstance(validators, Validators)


def test_utils_module_structure():
    """Test that the utils module has expected structure."""
    import modulink.utils as utils

    # Test that key functions exist
    assert hasattr(utils, "when")
    assert hasattr(utils, "catch_errors")
    assert hasattr(utils, "timing")
    assert hasattr(utils, "logging")
    assert hasattr(utils, "validate")
    assert hasattr(utils, "retry")
    assert hasattr(utils, "transform")
    assert hasattr(utils, "set_values")
    assert hasattr(utils, "filter_context")
    assert hasattr(utils, "parallel")
    assert hasattr(utils, "debounce")
    assert hasattr(utils, "memoize")
    assert hasattr(utils, "performance_tracker")

    # Test that classes exist
    assert hasattr(utils, "ErrorHandlers")
    assert hasattr(utils, "Validators")
    assert hasattr(utils, "error_handlers")
    assert hasattr(utils, "validators")


@pytest.mark.asyncio
async def test_chain_integration_with_utilities():
    """Test integration between chain functionality and utilities."""
    # Import chain here to test integration
    from modulink.chain import chain

    # Create a processing chain using utilities
    processing_chain = chain(
        transform("name", lambda name, ctx: name.upper() if name else ""),
        set_values({"processed": True}),
        when(
            lambda ctx: ctx.get("name") == "ALICE", set_values({"special_user": True})
        ),
    )

    result = await processing_chain({"name": "alice"})

    assert result["name"] == "ALICE"
    assert result["processed"] is True
    assert result["special_user"] is True


@pytest.mark.asyncio
async def test_single_link_as_chain_principle_comprehensive():
    """Test comprehensive single link as chain principle."""
    from modulink.chain import chain

    # Single link should work identically to 1-dimensional chain
    def auth_link(ctx: Ctx) -> Ctx:
        ctx["authenticated"] = True
        return ctx

    # Single link chain
    auth_chain = chain(auth_link)

    # Both should produce identical results
    single_result = await auth_chain({"user_id": "123"})

    assert single_result["user_id"] == "123"
    assert single_result["authenticated"] is True


@pytest.mark.asyncio
async def test_utility_error_handling_patterns():
    """Test error handling patterns in utilities."""
    from modulink.chain import chain

    def failing_link(ctx: Ctx) -> Ctx:
        raise ValueError("Processing failed")

    # Test error handling with recovery
    recovery_chain = chain(
        failing_link,
        catch_errors(lambda error, ctx: {**ctx, "recovered": True, "error": None}),
    )

    result = await recovery_chain({"data": "test"})

    assert result["data"] == "test"
    assert "error" in result  # Chain captures the error


@pytest.mark.asyncio
async def test_performance_and_timing_integration():
    """Test performance and timing integration."""
    from modulink.chain import chain

    slow_operation_chain = chain(set_values({"start": True}))
    slow_operation_chain.use.before(timing("operation"))
    slow_operation_chain.use.after(performance_tracker())

    result = await slow_operation_chain({"initial": "data"})

    assert result["initial"] == "data"
    assert result["start"] is True
    assert "timing" in result
    assert "performance" in result


@pytest.mark.asyncio
async def test_memoization_and_caching_patterns():
    """Test memoization and caching patterns."""
    execution_count = {"count": 0}

    def expensive_operation(ctx: Ctx) -> Ctx:
        execution_count["count"] += 1
        ctx["result"] = f"computed_{execution_count['count']}"
        return ctx

    # Create memoized version
    memoized_operation = memoize(
        lambda ctx: ctx.get("cache_key", "default"), expensive_operation, ttl=1.0
    )

    # First call
    result1 = await memoized_operation({"cache_key": "test"})
    # Second call with same key should use cache
    result2 = await memoized_operation({"cache_key": "test"})

    assert execution_count["count"] == 1  # Only executed once
    assert result1["result"] == "computed_1"
    assert result2["result"] == "computed_1"  # Same cached result


@pytest.mark.asyncio
async def test_complex_utility_composition():
    """Test complex utility composition patterns."""
    from modulink.chain import chain

    # Complex data processing pipeline
    data_pipeline = chain(
        # Input validation
        validate(lambda ctx: "data" in ctx),
        # Data transformation
        transform("data", lambda data, ctx: data.strip().lower()),
        # Conditional processing
        when(lambda ctx: len(ctx.get("data", "")) > 0, set_values({"processed": True})),
        # Output formatting
        transform(
            "output",
            lambda _, ctx: {"result": ctx.get("data"), "timestamp": time.time()},
        ),
    )

    result = await data_pipeline({"data": "  TEST DATA  "})

    assert result["data"] == "test data"
    assert result["processed"] is True
    assert "output" in result
    assert result["output"]["result"] == "test data"


@pytest.mark.asyncio
async def test_resource_availability_handling():
    """Test resource availability handling in performance tracker."""
    perf_middleware = performance_tracker()
    result = await perf_middleware({"test": "data"})

    assert "performance" in result
    perf = result["performance"]

    # Check basic performance fields exist
    assert "memory_usage" in perf
    assert "user_time" in perf
    assert "system_time" in perf

    # Fields should either be numeric or "unavailable"
    for field in ["memory_usage", "user_time", "system_time"]:
        value = perf[field]
        assert isinstance(value, (int, float)) or value == "unavailable"


def test_type_safety_and_validation():
    """Test type safety and validation patterns."""
    # Test required fields validator
    required_validator = Validators.required(["user_id", "email"])

    # Valid context
    valid_ctx = {"user_id": "123", "email": "test@example.com", "optional": "data"}
    assert required_validator(valid_ctx) is True

    # Invalid context - missing required field
    invalid_ctx = {"user_id": "123", "optional": "data"}
    result = required_validator(invalid_ctx)
    assert isinstance(result, str)
    assert "email" in result


def test_memory_and_performance_considerations():
    """Test memory and performance considerations."""
    # Test that context copying doesn't cause issues
    large_data = {"data": "x" * 10000}  # 10KB of data

    # Transform should handle large contexts efficiently
    transform_link = transform("processed", lambda _, ctx: True)

    # This should not raise memory errors
    result = asyncio.run(transform_link(large_data))
    assert result["data"] == "x" * 10000
    assert result["processed"] is True


@pytest.mark.asyncio
async def test_real_world_usage_patterns():
    """Test real-world usage patterns and scenarios."""
    from modulink.chain import chain

    # Simulate a real API processing chain
    api_chain = chain(
        # Authentication
        when(lambda ctx: ctx.get("auth_token"), set_values({"authenticated": True})),
        # Input validation
        validate(lambda ctx: ctx.get("authenticated", False)),
        # Data processing
        transform(
            "user_data",
            lambda data, ctx: {"processed_at": time.time(), "original": data},
        ),
        # Output formatting
        filter_context(lambda k, v: k != "auth_token"),  # Remove sensitive data
    )

    # Test successful flow
    result = await api_chain(
        {
            "auth_token": "valid_token",
            "user_data": {"name": "Alice"},
            "request_id": "req_123",
        }
    )

    assert result["authenticated"] is True
    assert "user_data" in result
    assert result["user_data"]["original"]["name"] == "Alice"
    assert "auth_token" not in result  # Filtered out
    assert result["request_id"] == "req_123"
