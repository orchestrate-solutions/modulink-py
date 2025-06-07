"""
Tests for ModuLink utility functions and chain middleware system.
"""

import pytest
import asyncio
import time
from typing import Dict, Any
from modulink.types import Ctx
from modulink.utils import (
    chain, timing, logging, validate, performance_tracker,
    when, parallel, memoize, transform, set_values,
    validators, error_handlers
)

# Helper functions for testing
async def increment_value(ctx: Ctx) -> Ctx:
    """Test link that increments a value in the context."""
    return {**ctx, "value": ctx.get("value", 0) + 1}

async def double_value(ctx: Ctx) -> Ctx:
    """Test link that doubles a value in the context."""
    return {**ctx, "value": ctx.get("value", 0) * 2}

async def failing_link(ctx: Ctx) -> Ctx:
    """Test link that always fails."""
    raise ValueError("Test error")

class TestChainFunctionality:
    """Test core chain functionality including middleware support."""

    @pytest.mark.asyncio
    async def test_basic_chain_execution(self):
        """Test that a simple chain executes links in order."""
        test_chain = chain(increment_value, double_value)
        result = await test_chain({"value": 1})
        assert result["value"] == 4, f"Expected 4, got {result['value']}"

    @pytest.mark.asyncio
    async def test_middleware_execution_order(self):
        """Test that middleware runs in the correct order."""
        execution_order = []
        
        def order_tracking_middleware(label: str):
            def middleware(ctx: Ctx) -> Ctx:
                execution_order.append(label)
                return ctx
            return middleware
        
        test_chain = chain(increment_value)
        test_chain.on_input(order_tracking_middleware("input"))
        test_chain.on_output(order_tracking_middleware("output"))
        test_chain.use(order_tracking_middleware("global"))
        
        await test_chain({"value": 1})
        # Expected order: [on_input] : link : [global] : [on_output]
        assert execution_order == ["input", "global", "output"], f"Order was {execution_order}"

    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test that errors are properly caught and propagated."""
        test_chain = chain(increment_value, failing_link, double_value)
        result = await test_chain({"value": 1})
        
        assert "error" in result, "Error should be present in result"
        assert isinstance(result["error"], ValueError), f"Error type: {type(result['error'])}"
        # The chain continues processing after error, so double_value still executes
        # This gives us: 1 -> increment(2) -> fail(error, but value remains 2) -> double(4)
        assert result["value"] == 4, f"Chain should continue processing after error, got {result['value']}"

    @pytest.mark.asyncio
    async def test_performance_tracking(self):
        """Test performance tracking middleware."""
        test_chain = chain(
            increment_value,
            double_value
        )
        test_chain.on_input(performance_tracker())
        
        result = await test_chain({"value": 1})
        
        # The performance tracker puts data directly in "performance", not "_metadata"
        assert "performance" in result, "Should have performance in result"
        assert "start_time" in result["performance"], "Should have start_time in performance"

    @pytest.mark.asyncio
    async def test_logging_middleware_positive(self, capfd):
        """Test that logging middleware outputs expected logs on success."""
        test_chain = chain(increment_value)
        test_chain.use(logging(log_input=True, log_output=True, log_timing=True))
        await test_chain({"value": 1})
        out, err = capfd.readouterr()
        assert "[ModuLink] Input:" in out
        assert "[ModuLink] Output:" in out
        assert "[ModuLink] Execution time:" in out

    @pytest.mark.asyncio
    async def test_logging_middleware_negative(self, capfd):
        """Test that logging middleware outputs logs on error."""
        test_chain = chain(failing_link)
        test_chain.use(logging(log_input=True, log_output=True, log_timing=True))
        await test_chain({"value": 1})
        out, err = capfd.readouterr()
        assert "[ModuLink] Input:" in out
        assert "[ModuLink] Output:" in out
        assert "[ModuLink] Execution time:" in out

class TestUtilityFunctions:
    """Test utility functions from ModuLink."""

    @pytest.mark.asyncio
    async def test_when_conditional(self):
        """Test conditional execution with when()."""
        should_run = lambda ctx: ctx.get("run", False)
        conditional_chain = chain(
            when(should_run, increment_value)
        )
        
        # Test when condition is true
        result1 = await conditional_chain({"run": True, "value": 1})
        assert result1["value"] == 2, "when() should run increment_value if run=True"
        
        # Test when condition is false
        result2 = await conditional_chain({"run": False, "value": 1})
        assert result2["value"] == 1, "when() should not run increment_value if run=False"

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel execution utility."""
        parallel_chain = parallel(
            set_values({"a": 1}),
            set_values({"b": 2}),
            transform("value", lambda x, _: x * 2 if x else 0)
        )
        
        result = await parallel_chain({"value": 5})
        assert result["a"] == 1, "Parallel set_values a failed"
        assert result["b"] == 2, "Parallel set_values b failed"
        assert result["value"] == 10, "Parallel transform failed"

    @pytest.mark.asyncio
    async def test_memoization(self):
        """Test memoization with TTL."""
        call_count = 0
        
        async def expensive_operation(ctx: Ctx) -> Ctx:
            nonlocal call_count
            call_count += 1
            return {**ctx, "result": "computed"}
        
        memoized = memoize(
            key_fn=lambda ctx: str(ctx.get("key")),
            link=expensive_operation,
            ttl=0.1  # Short TTL for testing
        )
        
        # First call
        result1 = await memoized({"key": "test"})
        assert result1["result"] == "computed"
        assert call_count == 1, "First call should compute"
        
        # Second call (should use cache)
        result2 = await memoized({"key": "test"})
        assert result2.get("from_cache") is True, "Second call should use cache"
        assert call_count == 1, "Cache should prevent recompute"
        
        # Wait for TTL to expire
        await asyncio.sleep(0.2)
        
        # Third call (should recompute)
        result3 = await memoized({"key": "test"})
        assert result3.get("from_cache") is not True, "Cache should expire"
        assert call_count == 2, "Should recompute after TTL"

class TestErrorHandling:
    """Test error handling patterns."""

    def test_error_handlers_log_and_continue(self):
        """Test log and continue error handler."""
        error = ValueError("Test error")
        context = {"test": "data"}
        
        result = error_handlers.log_and_continue(error, context)
        assert result["error"] == error, "Error should be present in context"
        assert result["test"] == "data"

    def test_error_handlers_user_friendly(self):
        """Test user-friendly error handler."""
        error = ValueError("Technical error message")
        context = {"test": "data"}
        
        result = error_handlers.user_friendly(error, context)
        assert result["error"]["user_friendly"] is True, "Should mark error as user-friendly"
        assert "message" in result["error"]

class TestValidation:
    """Test validation patterns."""

    def test_required_fields_validation(self):
        """Test required fields validator."""
        validator = validators.required(["field1", "field2"])
        
        # Test with all required fields
        result1 = validator({"field1": "value1", "field2": "value2"})
        assert result1 is True, "All required fields present should return True"
        
        # Test with missing fields
        result2 = validator({"field1": "value1"})
        assert isinstance(result2, str), "Missing fields should return error string"
        assert "field2" in result2

    def test_type_validation(self):
        """Test type validation."""
        validator = validators.types({"name": "str", "age": "int"})
        
        # Test with correct types
        result1 = validator({"name": "John", "age": 30})
        assert result1 is True, "Correct types should return True"
        
        # Test with incorrect types
        result2 = validator({"name": "John", "age": "30"})
        assert isinstance(result2, str), "Incorrect types should return error string"
        assert "age" in result2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
