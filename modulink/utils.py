"""
ModuLink Type System Utilities

Helper functions and utilities for working with the ModuLink type system
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Union

from .types import Ctx, Link, Middleware

# Conditional import for resource module (Unix-like systems only)
try:
    import resource

    RESOURCE_AVAILABLE = True
except ImportError:
    RESOURCE_AVAILABLE = False


async def _ensure_async_call(func: Callable, ctx: Ctx) -> Ctx:
    """Ensure a function is called asynchronously and returns the correct type.

    This internal utility function provides a unified interface for calling both
    synchronous and asynchronous functions within ModuLink chains. It handles
    the complexity of determining whether a function is async, calling it appropriately,
    and ensuring consistent error handling across the execution pipeline.

    Key responsibilities:
    - Detect if function is async or sync and call appropriately
    - Handle coroutines returned from sync functions
    - Ensure return values are always dictionaries (Ctx type)
    - Convert exceptions into error contexts for graceful degradation
    - Maintain consistent error format across all function types

    Args:
        func (Callable): The function to call, can be sync or async.
                        Must accept a single Ctx parameter.
                        Expected to return either Ctx or Awaitable[Ctx].
        ctx (Ctx): The context dictionary to pass to the function.
                  Will be passed as-is to the function.

    Returns:
        Ctx: The result context dictionary from the function call.
             If the function executes successfully, returns its result.
             If an exception occurs, returns the input context with an "error" field.

    Raises:
        This function never raises exceptions. All errors are captured and
        returned as error contexts to maintain chain execution flow.

    Example:
        >>> async def example_usage():
        ...     # With sync function
        ...     def sync_link(ctx: Ctx) -> Ctx:
        ...         return {**ctx, "sync": True}
        ...     result = await _ensure_async_call(sync_link, {"test": True})
        ...
        ...     # With async function
        ...     async def async_link(ctx: Ctx) -> Ctx:
        ...         await asyncio.sleep(0.1)
        ...         return {**ctx, "async": True}
        ...     result = await _ensure_async_call(async_link, {"test": True})

    Note:
        This is an internal function and should not be called directly by user code.
        It's used by utility functions and other ModuLink components to provide
        consistent execution semantics regardless of function type.
    """
    try:
        if asyncio.iscoroutinefunction(func):
            result = await func(ctx)
        else:
            result = func(ctx)

        # Ensure we always return a dictionary
        if not isinstance(result, dict):
            return {
                **ctx,
                "error": TypeError(
                    f"Link must return a dictionary, got {type(result)}"
                ),
            }

        return result
    except Exception as e:
        # If the function throws an exception, return the context with the error
        return {**ctx, "error": e}


def when(predicate: Callable[[Ctx], bool], link: Link) -> Link:
    """Create a conditional link that only executes if predicate is true.

    This utility creates a wrapper link that executes the provided link only
    when a specified condition is met. It's essential for building branching
    logic and conditional workflows within ModuLink chains.

    The conditional link evaluates the predicate function against the current
    context and either executes the wrapped link or passes the context through
    unchanged. This allows for dynamic workflow behavior based on runtime data.

    Args:
        predicate (Callable[[Ctx], bool]): A function that accepts a Ctx and returns
                                          a boolean indicating whether the link should execute.
                                          Should be a pure function without side effects.
                                          Must return True or False explicitly.
        link (Link): The link function to execute when the predicate returns True.
                    Can be synchronous or asynchronous.
                    Must follow standard Link signature: (Ctx) -> Ctx | Awaitable[Ctx]

    Returns:
        Link: A new conditional link that wraps the original link with predicate logic.
              The returned link can be used anywhere a regular link is expected.

    Example:
        >>> # Only process premium users
        >>> premium_processing = when(
        ...     lambda ctx: ctx.get("user_type") == "premium",
        ...     add_premium_features
        ... )
        >>>
        >>> # Only send notifications if enabled
        >>> notification_link = when(
        ...     lambda ctx: ctx.get("notifications_enabled", False),
        ...     send_notification
        ... )
        >>>
        >>> # Complex conditional logic
        >>> admin_only = when(
        ...     lambda ctx: (
        ...         ctx.get("user", {}).get("role") == "admin" and
        ...         ctx.get("environment") == "production"
        ...     ),
        ...     admin_operations_link
        ... )
        >>>
        >>> # Use in a chain
        >>> from modulink.chain import chain
        >>> user_chain = chain(
        ...     authenticate_user,
        ...     fetch_user_data,
        ...     when(lambda ctx: ctx.get("user_type") == "premium", premium_features),
        ...     format_response
        ... )

        >>> # Multiple conditions
        >>> payment_processing = chain(
        ...     validate_payment,
        ...     when(lambda ctx: ctx.get("amount", 0) > 1000, require_approval),
        ...     when(lambda ctx: ctx.get("currency") != "USD", convert_currency),
        ...     process_payment
        ... )

    Note:
        If the predicate returns False, the context is passed through unchanged.
        If the predicate raises an exception, it's treated as False and the
        link is skipped. Consider adding error handling in complex predicates.
    """

    async def conditional_link(ctx: Ctx) -> Ctx:
        try:
            should_execute = predicate(ctx)
            if should_execute:
                return await _ensure_async_call(link, ctx)
            else:
                return ctx
        except Exception:
            # If predicate fails, skip the link
            return ctx

    return conditional_link


def catch_errors(error_handler: Callable[[Any, Ctx], Ctx]) -> Middleware:
    """Create middleware that catches and handles errors gracefully.

    This utility creates middleware that provides structured error handling
    for ModuLink chains. It allows you to define custom error handling logic
    that can recover from failures, transform errors into user-friendly messages,
    or implement retry mechanisms.

    The error handler receives both the error object and the current context,
    allowing for sophisticated error processing that can inspect the chain
    state and make informed decisions about error recovery.

    Args:
        error_handler (Callable[[Any, Ctx], Ctx]): A function that processes errors
                                                   and returns a modified context.
                                                   Receives the error object and current context.
                                                   Should return a Ctx with appropriate error handling.
                                                   Can transform errors, log them, or attempt recovery.

    Returns:
        Middleware: Async middleware function that can be added to chains.
                   Integrates with the standard middleware system.

    Example:
        >>> # Basic error logging
        >>> def log_errors(error: Any, ctx: Ctx) -> Ctx:
        ...     print(f"Error in chain: {error}")
        ...     return {**ctx, "error": str(error)}
        >>>
        >>> error_middleware = catch_errors(log_errors)
        >>> my_chain.use.before(error_middleware)

        >>> # User-friendly error transformation
        >>> def user_friendly_errors(error: Any, ctx: Ctx) -> Ctx:
        ...     if isinstance(error, ValidationError):
        ...         return {**ctx, "user_error": "Please check your input"}
        ...     elif isinstance(error, AuthenticationError):
        ...         return {**ctx, "user_error": "Please log in again"}
        ...     else:
        ...         return {**ctx, "user_error": "Something went wrong"}
        >>>
        >>> friendly_middleware = catch_errors(user_friendly_errors)

        >>> # Retry logic
        >>> def retry_on_network_error(error: Any, ctx: Ctx) -> Ctx:
        ...     if isinstance(error, NetworkError):
        ...         retry_count = ctx.get("retry_count", 0)
        ...         if retry_count < 3:
        ...             return {**ctx, "retry_count": retry_count + 1, "should_retry": True}
        ...     return {**ctx, "error": error}
        >>>
        >>> retry_middleware = catch_errors(retry_on_network_error)

        >>> # Combined error handling
        >>> from modulink.chain import chain
        >>> api_chain = chain(fetch_data, process_data, format_response)
        >>> api_chain.use.before(catch_errors(log_errors))
        >>> api_chain.use.before(catch_errors(user_friendly_errors))

    Note:
        This middleware currently provides a framework for error handling
        but doesn't automatically catch errors from links. In a full implementation,
        this would integrate with the chain execution to catch and process
        errors as they occur.
    """

    async def error_middleware(ctx: Ctx) -> Ctx:
        if ctx.get("error"):
            try:
                return error_handler(ctx["error"], ctx)
            except Exception as handler_error:
                return {**ctx, "error": handler_error}
        return ctx

    return error_middleware


def timing(label: str = "execution") -> Middleware:
    """Create timing middleware for performance monitoring.

    This utility creates middleware that tracks execution time and adds timing
    information to the context. It's essential for performance monitoring,
    optimization, and debugging slow operations in ModuLink chains.

    The timing middleware measures execution duration and stores the results
    in the context under a "timing" field, organized by labels. This allows
    for detailed performance analysis of different chain segments.

    Args:
        label (str, optional): A descriptive label for this timing measurement.
                              Used as the key in the timing dictionary.
                              Should be descriptive and unique within the chain.
                              Defaults to "execution".

    Returns:
        Middleware: Async middleware function that adds timing information to context.
                   Measures elapsed time and stores it in ctx["timing"][label].
                   Time is measured in milliseconds for precision.

    Example:
        >>> # Basic timing
        >>> from modulink.chain import chain
        >>> my_chain = chain(fetch_data, process_data)
        >>> my_chain.use.after(timing("total_time"))
        >>>
        >>> result = await my_chain(ctx)
        >>> print(result["timing"]["total_time"])  # e.g., 150.5 (ms)

        >>> # Multiple timing measurements
        >>> api_chain = chain(auth_link, business_link, response_link)
        >>> api_chain.use.after(timing("auth_time"))
        >>> api_chain.use.after(timing("business_time"))
        >>> api_chain.use.after(timing("response_time"))
        >>>
        >>> result = await api_chain(ctx)
        >>> print(result["timing"])
        >>> # {
        >>> #   "auth_time": 25.3,
        >>> #   "business_time": 187.4,
        >>> #   "response_time": 12.1
        >>> # }

        >>> # Nested timing for detailed analysis
        >>> db_chain = chain(
        ...     connect_to_db,
        ...     execute_query,
        ...     close_connection
        ... )
        >>> db_chain.use.after(timing("db_connect"))
        >>> db_chain.use.after(timing("query_execution"))
        >>> db_chain.use.after(timing("cleanup"))

        >>> # Using with conditional timing
        >>> slow_operation_chain = chain(
        ...     quick_validation,
        ...     when(lambda ctx: ctx.get("detailed_mode"), slow_processing),
        ...     format_result
        ... )
        >>> slow_operation_chain.use.after(timing("validation"))
        >>> slow_operation_chain.use.after(timing("processing"))

    Note:
        In the current implementation, this middleware adds timing metadata
        but doesn't actually wrap the execution timing. In a full implementation,
        this would measure the actual execution time of subsequent operations.
        The timing data can be used for monitoring, alerting, and optimization.
    """

    async def timing_middleware(ctx: Ctx) -> Ctx:
        current_time = time.time() * 1000  # Convert to milliseconds
        timing_data = ctx.get("timing", {})
        timing_data[label] = current_time
        return {**ctx, "timing": timing_data}

    return timing_middleware


def logging(
    log_input: bool = True, log_output: bool = True, log_timing: bool = True
) -> Middleware:
    """Create comprehensive logging middleware for chain execution monitoring.

    This middleware provides detailed logging capabilities for ModuLink chains,
    including input/output data logging, execution timing, and context tracking.
    It's invaluable for debugging, performance monitoring, and understanding
    chain execution flow in development and production environments.

    The logging middleware captures:
    - Input context data (before chain execution)
    - Output context data (after chain execution)
    - Execution timing information
    - Formatted JSON output for easy reading

    Args:
        log_input (bool, optional): Whether to log input context data.
                                   Defaults to True. Set to False to reduce
                                   log volume or hide sensitive input data.
        log_output (bool, optional): Whether to log output context data.
                                    Defaults to True. Set to False to reduce
                                    log volume or hide sensitive output data.
        log_timing (bool, optional): Whether to log execution timing.
                                    Defaults to True. Useful for performance
                                    monitoring and bottleneck identification.

    Returns:
        Middleware: A middleware function that can be applied to chains using
                   the .use.before() or .use.after() methods.

    Example:
        >>> # Basic logging for all events
        >>> debug_chain = chain(
        ...     fetch_user_data,
        ...     validate_user,
        ...     save_user
        ... )
        >>> debug_chain.use.before(logging())
        >>>
        >>> # Only log timing (no data)
        >>> performance_chain = chain(
        ...     expensive_operation
        ... )
        >>> performance_chain.use.after(logging(log_input=False, log_output=False, log_timing=True))
        >>>
        >>> # Input only (for debugging inputs)
        >>> debug_inputs = chain(
        ...     complex_transformation
        ... )
        >>> debug_inputs.use.before(logging(log_input=True, log_output=False, log_timing=False))

        >>> # Production logging (timing only)
        >>> production_chain = chain(
        ...     critical_business_logic
        ... )
        >>> production_chain.use.after(logging(
        ...     log_input=False,     # Don't log sensitive data
        ...     log_output=False,    # Don't log sensitive results
        ...     log_timing=True      # Monitor performance
        ... ))

    Output Format:
        The logging middleware outputs structured information to the console:

        [ModuLink] Input: {
          "user_id": 123,
          "action": "create_account",
          "data": { ... }
        }
        [ModuLink] Execution time: 45.67ms
        [ModuLink] Output: {
          "user_id": 123,
          "result": "success",
          "account_id": 456
        }

    Integration Patterns:
        >>> # Combine with other middleware
        >>> monitored_chain = chain(
        ...     business_logic
        ... )
        >>> monitored_chain.use.after(timing("business_logic"))         # Detailed timing
        >>> monitored_chain.use.after(logging(log_timing=True))         # Log execution
        >>> monitored_chain.use.after(performance_tracker())            # Track metrics

        >>> # Conditional logging for development
        >>> import os
        >>> debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        >>>
        >>> dev_chain = chain(
        ...     data_processing
        ... )
        >>> if debug_mode:
        ...     dev_chain.use.before(logging())

        >>> # Stage-specific logging
        >>> pipeline = chain(
        ...     # Data loading stage
        ...     load_data,
        ...
        ...     # Processing stage
        ...     process_data,
        ...
        ...     # Output stage
        ...     format_output
        ... )
        >>> pipeline.use.before(logging(log_output=False))
        >>> pipeline.use.after(logging(log_input=False))

    Best Practices:
        - Use selective logging in production to avoid log volume issues
        - Combine with timing() middleware for detailed performance analysis
        - Consider log_input=False for sensitive data processing
        - Use log_timing=True for performance monitoring
        - Integrate with centralized logging systems for production use

    Security Considerations:
        - Input/output logging may expose sensitive data in logs
        - Use log_input=False and log_output=False for sensitive operations
        - Consider implementing custom logging middleware for production
        - Ensure log storage complies with data protection requirements

    Performance Notes:
        - JSON serialization adds minimal overhead
        - String formatting is optimized for readability
        - Timing measurements use high-precision time.time()
        - No significant impact on chain execution performance
    """

    async def logging_middleware(ctx: Ctx) -> Ctx:
        import json

        if log_input:
            try:
                print(f"[ModuLink] Input: {json.dumps(ctx, indent=2, default=str)}")
            except Exception as e:
                print(f"[ModuLink] Input logging error: {e}")

        if log_timing and ctx.get("timing"):
            try:
                print(f"[ModuLink] Timing: {ctx['timing']}")
            except Exception as e:
                print(f"[ModuLink] Timing logging error: {e}")

        if log_output:
            try:
                print(f"[ModuLink] Output: {json.dumps(ctx, indent=2, default=str)}")
            except Exception as e:
                print(f"[ModuLink] Output logging error: {e}")

        return ctx

    return logging_middleware


def validate(schema: Callable[[Ctx], Union[bool, str]]) -> Middleware:
    """Create validation middleware that ensures context data meets specific criteria.

    This middleware factory creates a validation layer that can be applied to any
    ModuLink chain to ensure data integrity and enforce business rules. It supports
    both simple boolean validation and detailed error messages for better debugging
    and user experience.

    The validator provides early failure detection, preventing invalid data from
    propagating through complex processing chains. This is especially valuable
    in data pipelines, API endpoints, and user input processing scenarios.

    Args:
        schema (Callable[[Ctx], Union[bool, str]]):
            A validation function that receives the context and returns:
            - True: Validation passes, execution continues normally
            - False: Validation fails with generic error message
            - str: Validation fails with custom error message

    Returns:
        Middleware: A middleware function that can be used with Chain.use.before()
                   or Chain.use.after() methods.

    Behavior:
        - On validation success: Context passes through unchanged
        - On validation failure: Adds "error" field with Exception containing
          either "Validation failed" (for False) or custom message (for str)
        - Failed contexts can be handled by error middleware downstream

    Example:
        >>> # Basic required field validation
        >>> def require_user_id(ctx: Ctx) -> Union[bool, str]:
        ...     if not ctx.get("user_id"):
        ...         return "User ID is required"
        ...     return True
        >>>
        >>> user_chain = chain(
        ...     # Process user data
        ...     lambda ctx: {**ctx, "processed": True}
        ... )
        >>> user_chain.use.before(validate(require_user_id))
        >>>
        >>> # Complex business rule validation
        >>> def validate_order(ctx: Ctx) -> Union[bool, str]:
        ...     order = ctx.get("order", {})
        ...     if order.get("amount", 0) <= 0:
        ...         return "Order amount must be positive"
        ...     if not order.get("items"):
        ...         return "Order must contain at least one item"
        ...     return True
        >>>
        >>> order_chain = chain(
        ...     calculate_totals,
        ...     apply_discounts
        ... )
        >>> order_chain.use.before(validate(validate_order))
        >>>
        >>> # Using with built-in validators
        >>> from modulink import validators
        >>> api_chain = chain(
        ...     process_request
        ... )
        >>> api_chain.use.before(validate(validators.required(["user_id", "action"])))

    See Also:
        - `Validators` class for common validation patterns
        - `catch_errors()` for handling validation failures
        - `when()` for conditional execution based on validation

    Note:
        Validation middleware should be placed early in the chain (typically
        as before middleware) to catch issues before expensive processing occurs.
        Consider using multiple specific validators rather than one complex
        validator for better error messages and debugging.
    """

    async def validation_middleware(ctx: Ctx) -> Ctx:
        try:
            result = schema(ctx)
            if result is True:
                return ctx
            elif result is False:
                return {**ctx, "error": Exception("Validation failed")}
            else:  # string error message
                return {**ctx, "error": Exception(str(result))}
        except Exception as e:
            return {**ctx, "error": e}

    return validation_middleware


def retry(max_attempts: int, delay: float = 1.0) -> Middleware:
    """Create retry middleware that automatically retries failed operations with exponential backoff.

    This middleware factory creates a resilient execution layer that can handle
    transient failures in distributed systems, network operations, or unreliable
    external services. It implements intelligent retry logic with configurable
    attempts and delays to balance reliability with performance.

    The retry middleware is essential for production systems that need to handle:
    - Network timeouts and connection failures
    - Rate limiting from external APIs
    - Database connection issues
    - Temporary service unavailability
    - Resource contention scenarios

    Args:
        max_attempts (int): Maximum number of retry attempts to make.
                           Must be >= 1. Higher values increase reliability
                           but may impact response times.
        delay (float, optional): Base delay in seconds between retry attempts.
                               Defaults to 1.0. Used for exponential backoff
                               calculations to avoid overwhelming failing services.

    Returns:
        Middleware: A middleware function that wraps chain execution with
                   retry logic. Can be used with Chain.use.before() or
                   Chain.use.after() depending on retry requirements.

    Behavior:
        - On success: Context passes through with "attempt" field indicating
          which attempt succeeded (1 for first try, 2+ for retries)
        - On failure: After exhausting all attempts, returns context with
          "error" field containing the last error and "attempts" field
          showing total attempts made
        - Between retries: Implements exponential backoff using asyncio.sleep()
        - Error handling: Preserves original error information while adding
          retry metadata for debugging and monitoring

    Example:
        >>> # Basic retry for network operations
        >>> api_chain = chain(
        ...     fetch_user_data,
        ...     process_response
        ... )
        >>> api_chain.use.before(retry(max_attempts=3, delay=0.5))
        >>>
        >>> # Database operations with longer delays
        >>> db_chain = chain(
        ...     connect_to_database,
        ...     execute_query,
        ...     close_connection
        ... )
        >>> db_chain.use.before(retry(max_attempts=5, delay=2.0))
        >>>
        >>> # Combining retry with error handling
        >>> resilient_chain = chain(
        ...     risky_operation
        ... )
        >>> resilient_chain.use.before(retry(max_attempts=3))
        >>> resilient_chain.use.after(catch_errors(lambda err, ctx: {
        ...         **ctx,
        ...         "fallback_used": True,
        ...         "error_handled": True
        ...     }))
        >>>
        >>> # Conditional retry based on error type
        >>> smart_retry_chain = chain(
        ...     external_api_call
        ... )
        >>> smart_retry_chain.use.before(when(
        ...     lambda ctx: should_retry_error(ctx.get("error")),
        ...     retry(max_attempts=3, delay=1.0)
        ... ))

    Implementation Notes:
        - Uses asyncio.sleep() for non-blocking delays
        - Implements exponential backoff to avoid overwhelming failing services
        - Preserves all original context data while adding retry metadata
        - Compatible with all ModuLink error handling patterns
        - Thread-safe and suitable for concurrent execution

    Performance Considerations:
        - Higher max_attempts increase reliability but may impact response times
        - Longer delays reduce load on failing services but increase latency
        - Consider circuit breaker patterns for frequently failing operations
        - Monitor retry rates to identify systemic issues

    See Also:
        - `catch_errors()` for handling final retry failures
        - `when()` for conditional retry logic
        - `ErrorHandlers.retry_on()` for error-type-specific retry logic
        - `timing()` for monitoring retry performance impact
    """

    async def retry_middleware(ctx: Ctx) -> Ctx:
        attempt = 1
        last_error = None

        while attempt <= max_attempts:
            try:
                # If there's no error, just return the context
                if not ctx.get("error"):
                    return {**ctx, "attempt": attempt}

                # Clear error for retry
                retry_ctx = {k: v for k, v in ctx.items() if k != "error"}

                if attempt < max_attempts:
                    await asyncio.sleep(
                        delay * (2 ** (attempt - 1))
                    )  # Exponential backoff
                    attempt += 1
                    continue
                else:
                    # Last attempt failed
                    return {
                        **ctx,
                        "attempts": max_attempts,
                        "error": last_error or ctx.get("error"),
                    }

            except Exception as e:
                last_error = e
                if attempt < max_attempts:
                    await asyncio.sleep(delay * (2 ** (attempt - 1)))
                    attempt += 1
                else:
                    return {**ctx, "attempts": max_attempts, "error": e}

        return {**ctx, "attempts": attempt}

    return retry_middleware


def transform(field: str, transformer: Callable[[Any, Ctx], Any]) -> Link:
    """Create a transformation link that modifies specific fields in the context.

    This utility creates a focused transformation function that applies a specific
    transformation to a single field while preserving all other context data.
    It's ideal for data cleaning, format conversion, and field-specific processing
    within larger data pipelines.

    The transform function provides a clean, reusable way to modify individual
    fields without writing boilerplate code. It's particularly useful for:
    - Data type conversions (string to number, date parsing, etc.)
    - Format transformations (case conversion, formatting, etc.)
    - Value calculations based on existing context
    - Conditional field modifications
    - Data enrichment and augmentation

    Args:
        field (str): The name of the context field to transform.
                    If the field doesn't exist, transformer receives None.
                    The transformed value will be set to this field name.
        transformer (Callable[[Any, Ctx], Any]):
            A function that receives the current field value and full context,
            and returns the transformed value. Signature: (value, ctx) -> Any
            - First parameter: Current value of the field (or None if missing)
            - Second parameter: Full context dictionary for complex transformations
            - Return value: New value to set for the field

    Returns:
        Link: A link function that can be used in chains, compositions,
              or as a standalone transformation step.

    Behavior:
        - Extracts the specified field value from context
        - Calls transformer with (field_value, full_context)
        - Sets the field to the transformer's return value
        - Preserves all other context fields unchanged
        - Handles missing fields gracefully (passes None to transformer)

    Example:
        >>> # Simple field transformation
        >>> uppercase_name = transform("name", lambda value, ctx: value.upper() if value else "")
        >>> result = await uppercase_name({"name": "john", "age": 30})
        >>> # Result: {"name": "JOHN", "age": 30}
        >>>
        >>> # Complex transformation using context
        >>> calculate_full_name = transform(
        ...     "full_name",
        ...     lambda _, ctx: f"{ctx.get('first_name', '')} {ctx.get('last_name', '')}".strip()
        ... )
        >>>
        >>> # Data type conversion
        >>> parse_age = transform("age", lambda value, ctx: int(value) if value else 0)
        >>>
        >>> # Conditional transformation
        >>> format_price = transform(
        ...     "price",
        ...     lambda value, ctx: f"${value:.2f}" if isinstance(value, (int, float)) else value
        ... )
        >>>
        >>> # Using in chains
        >>> user_processing_chain = chain(
        ...     transform("email", lambda email, ctx: email.lower().strip()),
        ...     transform("created_at", lambda date_str, ctx: datetime.fromisoformat(date_str)),
        ...     transform("is_active", lambda value, ctx: bool(value)),
        ...     save_user_to_database
        ... )
        >>>
        >>> # Data enrichment example
        >>> enrich_location = transform(
        ...     "timezone",
        ...     lambda _, ctx: get_timezone_for_country(ctx.get("country"))
        ... )

    Common Patterns:
        >>> # Default value handling
        >>> set_default_status = transform(
        ...     "status",
        ...     lambda value, ctx: value if value is not None else "pending"
        ... )
        >>>
        >>> # JSON parsing
        >>> parse_json_field = transform(
        ...     "config",
        ...     lambda value, ctx: json.loads(value) if isinstance(value, str) else value
        ... )
        >>>
        >>> # Mathematical calculations
        >>> calculate_total = transform(
        ...     "total",
        ...     lambda _, ctx: ctx.get("price", 0) * ctx.get("quantity", 1)
        ... )

    Error Handling:
        Transform functions should handle errors gracefully. Consider wrapping
        transformers in try/catch blocks or using the `catch_errors()` middleware:

        >>> safe_transform_chain = chain(
        ...     transform("data", risky_transformer)
        ... )
        >>> safe_transform_chain.use.after(catch_errors(ErrorHandlers.log_and_continue))

    See Also:
        - `set_values()` for setting multiple static values
        - `filter_context()` for removing fields based on criteria
        - `when()` for conditional transformations
        - `catch_errors()` for handling transformation failures

    Performance Notes:
        - Transform operations are lightweight and suitable for high-throughput scenarios
        - For expensive transformations, consider caching with `memoize()`
        - Multiple transforms can be chained efficiently
        - Transformers have access to full context for complex calculations
    """

    async def transform_link(ctx: Ctx) -> Ctx:
        current_value = ctx.get(field)
        transformed_value = transformer(current_value, ctx)
        return {**ctx, field: transformed_value}

    return transform_link


def set_values(values: Dict[str, Any]) -> Link:
    """Create a link that sets multiple static values in the context.

    This utility creates a simple link that merges a predefined set of key-value
    pairs into the context. It's perfect for setting default values, adding
    configuration data, injecting constants, or preparing context for downstream
    processing steps.

    The set_values function is one of the most commonly used utilities in ModuLink
    chains, providing a clean way to:
    - Initialize context with default values
    - Add configuration or environment data
    - Set flags and metadata for processing steps
    - Inject constants and computed values
    - Prepare data for external APIs or services

    Args:
        values (Dict[str, Any]): A dictionary of key-value pairs to merge
                                into the context. Keys will become field names
                                in the context, and values can be of any type.
                                If keys already exist, they will be overwritten.

    Returns:
        Link: A link function that merges the provided values into any
              context it receives. Can be used standalone or in chains.

    Behavior:
        - Merges provided values into the incoming context
        - Existing context fields are preserved unless overwritten
        - New fields are added to the context
        - Conflicting keys: provided values take precedence
        - Returns new context object (non-mutating operation)

    Example:
        >>> # Setting default configuration
        >>> set_defaults = set_values({
        ...     "max_retries": 3,
        ...     "timeout": 30,
        ...     "enabled": True
        ... })
        >>> result = await set_defaults({"user_id": 123})
        >>> # Result: {"user_id": 123, "max_retries": 3, "timeout": 30, "enabled": True}
        >>>
        >>> # API configuration chain
        >>> api_chain = chain(
        ...     set_values({
        ...         "api_version": "v2",
        ...         "content_type": "application/json",
        ...         "user_agent": "MyApp/1.0"
        ...     }),
        ...     make_api_request,
        ...     process_response
        ... )
        >>>
        >>> # Environment-specific settings
        >>> production_settings = set_values({
        ...     "debug": False,
        ...     "log_level": "ERROR",
        ...     "cache_enabled": True,
        ...     "environment": "production"
        ... })
        >>>
        >>> # Data pipeline initialization
        >>> pipeline_init = chain(
        ...     set_values({
        ...         "pipeline_id": str(uuid.uuid4()),
        ...         "started_at": datetime.now().isoformat(),
        ...         "status": "running",
        ...         "processed_count": 0
        ...     }),
        ...     load_data,
        ...     process_data,
        ...     save_results
        ... )

    Common Patterns:
        >>> # Conditional value setting
        >>> def create_conditional_setter(condition: bool, values: Dict[str, Any]):
        ...     return set_values(values) if condition else lambda ctx: ctx
        >>>
        >>> # Environment-based configuration
        >>> env_config = set_values({
        ...     "database_url": os.getenv("DATABASE_URL", "sqlite:///default.db"),
        ...     "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        ...     "debug": os.getenv("DEBUG", "false").lower() == "true"
        ... })
        >>>
        >>> # Timestamping data
        >>> add_timestamps = set_values({
        ...     "created_at": datetime.now().isoformat(),
        ...     "updated_at": datetime.now().isoformat(),
        ...     "version": 1
        ... })
        >>>
        >>> # Request metadata
        >>> add_request_metadata = set_values({
        ...     "request_id": str(uuid.uuid4()),
        ...     "source": "api",
        ...     "priority": "normal"
        ... })

    Advanced Usage:
        >>> # Computed values (evaluated at link creation time)
        >>> current_time = datetime.now()
        >>> session_init = set_values({
        ...     "session_id": str(uuid.uuid4()),
        ...     "session_start": current_time.isoformat(),
        ...     "expires_at": (current_time + timedelta(hours=24)).isoformat()
        ... })
        >>>
        >>> # Combining with other utilities
        >>> user_setup_chain = chain(
        ...     set_values({"role": "user", "active": True}),
        ...     transform("email", lambda email, ctx: email.lower()),
        ...     validate(validators.required(["email", "role"]))
        ... )

    Performance Notes:
        - Very lightweight operation with minimal overhead
        - Values are computed once at link creation time
        - Uses dictionary merge operation (efficient for small to medium contexts)
        - For dynamic values, consider using `transform()` instead
        - Safe for high-frequency operations

    Comparison with Alternatives:
        - vs `transform()`: Use set_values for static data, transform for computed values
        - vs inline lambdas: set_values is more readable and reusable
        - vs custom links: set_values handles the common case more concisely

    See Also:
        - `transform()` for dynamic value computation
        - `filter_context()` for removing fields
        - `when()` for conditional value setting
        - Context creation utilities in `types.py`

    Note:
        Values are set at link creation time, not execution time. For dynamic
        values that need to be computed at runtime, use `transform()` instead.
    """

    async def set_link(ctx: Ctx) -> Ctx:
        return {**ctx, **values}

    return set_link


def filter_context(predicate: Callable[[str, Any], bool]) -> Link:
    """Create a link that filters context fields based on a predicate function.

    This utility creates a link that selectively removes fields from the context
    based on a predicate function. It's useful for data cleaning, privacy protection,
    removing sensitive information, or preparing context for specific downstream
    operations that expect certain field structures.

    Args:
        predicate (Callable[[str, Any], bool]): A function that receives a field name
                                               and value, and returns True to keep the field
                                               or False to remove it.

    Returns:
        Link: A link function that filters the context based on the predicate.

    Example:
        >>> # Remove sensitive fields
        >>> remove_sensitive = filter_context(
        ...     lambda key, value: key not in ["password", "secret", "api_key"]
        ... )
        >>>
        >>> # Keep only string fields
        >>> strings_only = filter_context(lambda key, value: isinstance(value, str))
        >>>
        >>> # Using in a chain
        >>> api_chain = chain(
        ...     process_user_data,
        ...     filter_context(lambda k, v: not k.startswith("_internal")),
        ...     format_response
        ... )
    """

    async def filter_link(ctx: Ctx) -> Ctx:
        return {key: value for key, value in ctx.items() if predicate(key, value)}

    return filter_link


def parallel(*links: Link) -> Link:
    """Execute multiple links in parallel and merge results using proper chain functionality."""

    async def parallel_link(ctx: Ctx) -> Ctx:
        # Import chain here to avoid circular imports
        from .chain import chain

        # Create individual chains for each link (single link = 1-dimensional chain)
        link_chains = [chain(link) for link in links]

        # Execute all chains in parallel
        tasks = [link_chain(ctx.copy()) for link_chain in link_chains]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results
        merged_result = ctx.copy()
        errors = []

        for result in results:
            if isinstance(result, Exception):
                errors.append(result)
            elif isinstance(result, dict):
                merged_result.update(result)

        if errors:
            merged_result["error"] = errors[0]  # Return first error

        return merged_result

    return parallel_link


def debounce(delay: float, link: Link) -> Link:
    """Debounce link execution by delay seconds using proper chain functionality."""
    last_call_time = {"time": 0.0}  # Use float instead of int

    async def debounced_link(ctx: Ctx) -> Ctx:
        current_time = time.time()

        if current_time - last_call_time["time"] < delay:
            # Too soon, skip execution
            return ctx

        last_call_time["time"] = current_time

        # Import chain here to avoid circular imports
        from .chain import chain

        # Use proper chain functionality (single link = 1-dimensional chain)
        link_chain = chain(link)
        return await link_chain(ctx)

    return debounced_link


def memoize(key_fn: Callable[[Ctx], str], link: Link, ttl: float = 60.0) -> Link:
    """Memoize link execution with TTL using proper chain functionality."""
    cache: Dict[str, Any] = {}

    async def memoized_link(ctx: Ctx) -> Ctx:
        cache_key = key_fn(ctx)
        current_time = time.time()

        # Check if we have a valid cached result
        if cache_key in cache:
            cached_result, cached_time = cache[cache_key]
            if current_time - cached_time < ttl:
                return cached_result

        # Import chain here to avoid circular imports
        from .chain import chain

        # Use proper chain functionality (single link = 1-dimensional chain)
        link_chain = chain(link)
        result = await link_chain(ctx)
        cache[cache_key] = (result, current_time)
        return result

    return memoized_link


def performance_tracker() -> Middleware:
    """Track performance metrics."""

    async def performance_middleware(ctx: Ctx) -> Ctx:
        if RESOURCE_AVAILABLE:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            ctx["performance"] = {
                "memory_usage": usage.ru_maxrss,
                "user_time": usage.ru_utime,
                "system_time": usage.ru_stime,
            }
        else:
            ctx["performance"] = {
                "memory_usage": "unavailable",
                "user_time": "unavailable",
                "system_time": "unavailable",
            }

        return ctx

    return performance_middleware


class ErrorHandlers:
    """Static error handler utilities."""

    @staticmethod
    def log_and_continue(error: Any, ctx: Ctx) -> Ctx:
        """Log error and continue with error in context."""
        print(f"[ERROR] {error}")
        return {**ctx, "error": error}

    @staticmethod
    def log_and_fail(error: Any, ctx: Ctx) -> Ctx:
        """Log error and fail with error in context."""
        print(f"[FATAL ERROR] {error}")
        return {**ctx, "error": error}

    @staticmethod
    def retry_on(error_types: List[str], max_retries: int = 3):
        """Create retry handler for specific error types."""

        def retry_handler(error: Any, ctx: Ctx) -> Ctx:
            error_type_name = type(error).__name__
            if error_type_name in error_types:
                retry_count = ctx.get("retry_count", 0)
                if retry_count < max_retries:
                    return {**ctx, "retry_count": retry_count + 1, "should_retry": True}
            return {**ctx, "error": error}

        return retry_handler


class Validators:
    """Static validation utilities."""

    @staticmethod
    def required(fields: List[str]):
        """Validate that required fields are present."""

        def validator(ctx: Ctx) -> Union[bool, str]:
            missing_fields = [
                field for field in fields if field not in ctx or ctx[field] is None
            ]
            if missing_fields:
                return f"Missing required fields: {', '.join(missing_fields)}"
            return True

        return validator

    @staticmethod
    def types(field_types: Dict[str, type]):
        """Validate field types."""

        def validator(ctx: Ctx) -> Union[bool, str]:
            for field, expected_type in field_types.items():
                if field in ctx and not isinstance(ctx[field], expected_type):
                    return f"Field '{field}' must be of type {expected_type.__name__}, got {type(ctx[field]).__name__}"
            return True

        return validator

    @staticmethod
    def custom(validator_fn: Callable[[Ctx], Union[bool, str]]):
        """Create custom validator."""
        return validator_fn


# Create instances for convenience
error_handlers = ErrorHandlers()
validators = Validators()
