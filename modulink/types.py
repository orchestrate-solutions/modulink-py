"""
ModuLink Universal Types System for Python

Simple function types that replace over-engineered abstractions:
- Ctx: Context dictionary (any key-value pairs)
- Link: Function that transforms context (sync or async)
- Chain: Async function that transforms context
- Trigger: Function that executes a chain with initial context
- Middleware: Function that transforms context (simple, no "next" parameter)

This mirrors the TypeScript universal types system for consistency across languages.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, Protocol, Union

# Universal Context Type - just a dictionary that can hold anything
Ctx = Dict[str, Any]


class Link(Protocol):
    """Protocol for Link functions that transform context data.

    A Link is the fundamental building block in ModuLink chains. Links are functions
    that accept a context dictionary and return a modified context dictionary.
    Links can be either synchronous or asynchronous - the ModuLink system handles
    both transparently during chain execution.

    Key characteristics:
    - Pure functions: should not have side effects on the input context
    - Composable: can be chained together to build complex workflows
    - Flexible: can be sync or async based on the operation requirements
    - Type-safe: provides clear input/output contracts via type hints

    Examples:
        Synchronous link:
        >>> def auth_link(ctx: Ctx) -> Ctx:
        ...     ctx = ctx.copy()
        ...     ctx["user"] = authenticate_user(ctx.get("token"))
        ...     return ctx

        Asynchronous link:
        >>> async def data_link(ctx: Ctx) -> Ctx:
        ...     ctx = ctx.copy()
        ...     ctx["data"] = await fetch_data_async(ctx["user_id"])
        ...     return ctx

    Note:
        Links should copy the input context before modifying it to avoid
        unintended mutations that could affect other parts of the chain.
    """

    def __call__(self, ctx: Ctx) -> Union[Ctx, Awaitable[Ctx]]:
        """Transform context and return new context.

        Args:
            ctx (Ctx): Input context dictionary containing data to be processed.
                      Should not be mutated directly - copy before modifying.

        Returns:
            Union[Ctx, Awaitable[Ctx]]: Modified context dictionary.
                                       Can be returned directly (sync) or as an awaitable (async).
        """
        ...


class Chain(Protocol):
    """Protocol for Chain functions that execute sequences of links asynchronously.

    A Chain represents a composed sequence of Link functions that execute in order.
    Chains are always asynchronous for consistency and to support async operations
    within the execution pipeline. Chains are the primary execution unit in ModuLink
    and are created by composing one or more Link functions.

    Key characteristics:
    - Always async: provides consistent execution model regardless of link types
    - Sequential execution: links execute in the order they were composed
    - Error handling: execution stops on first error encountered
    - Middleware support: global and chain-specific middleware is applied automatically
    - Context propagation: modified context flows from one link to the next

    Examples:
        >>> # Chain created from multiple links
        >>> chain = modulink.create_chain(auth_link, validate_link, process_link)
        >>> result = await chain({"user_id": "123"})

        >>> # Named chain with specific middleware
        >>> named_chain = modulink.create_named_chain("user_workflow", auth_link, process_link)
        >>> result = await named_chain(initial_context)

    Note:
        Chains are typically created using modulink.create_chain() or
        modulink.create_named_chain() rather than implementing this protocol directly.
    """

    async def __call__(self, ctx: Ctx) -> Ctx:
        """Execute the chain asynchronously with the provided context.

        Args:
            ctx (Ctx): Input context dictionary containing initial data for the chain.
                      This context will be passed through each link in sequence.

        Returns:
            Ctx: Final context dictionary after all links have executed.
                 Contains the cumulative modifications from all links in the chain.

        Note:
            If any link or middleware sets an "error" key in the context,
            chain execution will stop early and return the error context.
        """
        ...


class Trigger(Protocol):
    """Protocol for Trigger functions that initiate chain execution from external events.

    A Trigger is responsible for connecting external events (HTTP requests, cron schedules,
    CLI commands, messages) to ModuLink chains. Triggers set up the initial context and
    execute chains in response to specific events or conditions.

    Key characteristics:
    - Event-driven: responds to external stimuli like HTTP requests or cron schedules
    - Context creation: builds appropriate initial context for the chain
    - Framework integration: connects with web frameworks, schedulers, message queues
    - Async execution: always executes chains asynchronously

    Examples:
        >>> # HTTP trigger for web endpoints
        >>> trigger = modulink.triggers.http("/api/users", ["GET", "POST"])
        >>> result = await trigger(user_chain)

        >>> # Cron trigger for scheduled tasks
        >>> trigger = modulink.triggers.cron("0 */6 * * *")  # Every 6 hours
        >>> result = await trigger(cleanup_chain)

    Note:
        Triggers are typically created using the trigger factory functions
        (http_trigger, cron_trigger, etc.) rather than implementing this protocol directly.
    """

    async def __call__(
        self, target_chain: Chain, initial_ctx: Optional[Ctx] = None
    ) -> Ctx:
        """Execute a chain with optional initial context.

        Args:
            target_chain (Chain): The chain to execute when the trigger fires.
                                 Must be an async function that accepts and returns a Ctx.
            initial_ctx (Optional[Ctx], optional): Initial context data to merge with
                                                  the trigger-specific context.
                                                  Defaults to None.

        Returns:
            Ctx: Final context dictionary after chain execution completes.
                 Contains the result of the chain execution and any modifications
                 made during the process.
        """
        ...


class Middleware(Protocol):
    """Protocol for Middleware functions that transform context in the execution pipeline.

    Middleware provides a way to intercept and modify context data as it flows through
    ModuLink chains. Unlike traditional middleware patterns, ModuLink middleware is
    simplified - it transforms context directly without complex "next" function parameters.

    Key characteristics:
    - Pure transformations: modify context and return the result
    - No "next" parameter: simpler than traditional middleware patterns
    - Sequential application: middleware is applied in registration order
    - Always async: provides consistent execution model
    - Composable: multiple middleware can be applied to the same target

    Examples:
        >>> # Logging middleware
        >>> async def logging_middleware(ctx: Ctx) -> Ctx:
        ...     print(f"Processing request: {ctx.get('path', 'unknown')}")
        ...     return ctx
        >>>
        >>> # Authentication middleware
        >>> async def auth_middleware(ctx: Ctx) -> Ctx:
        ...     ctx = ctx.copy()
        ...     if not ctx.get("token"):
        ...         ctx["error"] = Exception("Authentication required")
        ...     return ctx
        >>>
        >>> # Apply middleware
        >>> modulink.use.global_middleware(logging_middleware)
        >>> modulink.use.on_chain("api").on_input(auth_middleware)

    Note:
        Middleware functions should copy the context before modifying it to avoid
        unintended side effects on other parts of the execution pipeline.
    """

    async def __call__(self, ctx: Ctx) -> Ctx:
        """Transform context and return new context.

        Args:
            ctx (Ctx): Input context dictionary to be processed by the middleware.
                      Should not be mutated directly - copy before modifying.

        Returns:
            Ctx: Modified context dictionary after middleware processing.
                 Can include additional data, modified existing data, or error information.

        Note:
            If middleware sets an "error" key in the context, it will typically
            stop further execution in the chain.
        """
        ...


class ConnectionType(Enum):
    """Enumeration of supported connection types for ModuLink chains.

    This enum defines the available connection types that can be used
    with the modulink.connect() method. Using an enum prevents typos
    and provides better IDE support with autocomplete.

    Values:
        HTTP: Connect chains to HTTP endpoints (web frameworks)
        CRON: Connect chains to scheduled tasks (cron jobs)
        CLI: Connect chains to command-line interfaces
        MESSAGE: Connect chains to message queues and pub/sub systems

    Example:
        >>> from modulink.types import ConnectionType
        >>> modulink.connect(ConnectionType.HTTP, my_chain, app=app, method="POST", path="/api/data")
        >>> modulink.connect(ConnectionType.MESSAGE, my_chain, topic="user.created", handler=message_handler)
    """

    HTTP = "http"
    CRON = "cron"
    CLI = "cli"
    MESSAGE = "message"


class Status(Enum):
    """Enumeration for standardized status responses across ModuLink operations.

    This enum provides consistent status values for operations like cleanup,
    connections, and other ModuLink functions that need to return status information.

    Values:
        SUCCESS: Operation completed successfully
        FAILED: Operation failed with an error
        PENDING: Operation is in progress or pending
        CANCELLED: Operation was cancelled
        TIMEOUT: Operation timed out
        INVALID: Operation had invalid parameters or state
    """

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    INVALID = "invalid"


# Type aliases for convenience and backwards compatibility
LinkFunction = Callable[[Ctx], Union[Ctx, Awaitable[Ctx]]]
"""Type alias for Link functions.

Represents a callable that accepts a Ctx and returns either a Ctx directly (synchronous)
or an Awaitable[Ctx] (asynchronous). This is the functional type underlying the Link protocol.

Example:
    >>> def my_link(ctx: Ctx) -> Ctx:  # Synchronous LinkFunction
    ...     return {**ctx, "processed": True}
    >>>
    >>> async def async_link(ctx: Ctx) -> Ctx:  # Asynchronous LinkFunction
    ...     await asyncio.sleep(0.1)
    ...     return {**ctx, "async_processed": True}
"""

ChainFunction = Callable[[Ctx], Awaitable[Ctx]]
"""Type alias for Chain functions.

Represents an async callable that accepts a Ctx and returns an Awaitable[Ctx].
This is the functional type underlying the Chain protocol. Chains are always async
to provide consistent execution semantics.

Example:
    >>> async def my_chain(ctx: Ctx) -> Ctx:  # ChainFunction
    ...     result = await some_async_operation(ctx)
    ...     return {**ctx, "result": result}
"""

TriggerFunction = Callable[[Chain, Optional[Ctx]], Awaitable[Ctx]]
"""Type alias for Trigger functions.

Represents an async callable that accepts a Chain and optional initial Ctx,
then returns an Awaitable[Ctx]. Triggers initiate chain execution in response
to external events.

Example:
    >>> async def my_trigger(chain: Chain, initial_ctx: Optional[Ctx] = None) -> Ctx:
    ...     ctx = initial_ctx or create_context(trigger="custom")
    ...     return await chain(ctx)
"""

MiddlewareFunction = Callable[[Ctx], Awaitable[Ctx]]
"""Type alias for Middleware functions.

Represents an async callable that accepts a Ctx and returns an Awaitable[Ctx].
This is the functional type underlying the Middleware protocol. Middleware transforms
context data as it flows through the execution pipeline.

Example:
    >>> async def my_middleware(ctx: Ctx) -> Ctx:  # MiddlewareFunction
    ...     # Log the incoming context
    ...     logger.info(f"Processing context: {ctx.get('id', 'unknown')}")
    ...     return {**ctx, "logged": True}
"""


def get_current_timestamp() -> str:
    """Get current timestamp in ISO 8601 format.

    This utility function provides a standardized way to generate timestamps
    for ModuLink contexts. The timestamp includes millisecond precision and
    follows the ISO 8601 standard format.

    Returns:
        str: Current timestamp in ISO 8601 format (e.g., "2024-01-15T14:30:45.123456").
             Includes microsecond precision for high-resolution timing.

    Example:
        >>> timestamp = get_current_timestamp()
        >>> print(timestamp)  # "2024-01-15T14:30:45.123456"

        >>> # Using in context creation
        >>> ctx = create_context(
        ...     trigger="manual",
        ...     timestamp=get_current_timestamp(),
        ...     user_id="123"
        ... )

    """
    return datetime.now(timezone.utc).isoformat()


def create_context(
    *, trigger: str = "unknown", timestamp: Optional[str] = None, **kwargs: Any
) -> Ctx:
    """Create a new ModuLink context with common fields and metadata.

    This is the primary factory function for creating ModuLink contexts. It establishes
    the foundational structure that all ModuLink chains expect, providing consistent
    metadata about execution triggers and timing.

    The created context serves as the data container that flows through ModuLink chains,
    carrying both user data and system metadata. All ModuLink links receive and return
    contexts created through this function or its specialized variants.

    Args:
        trigger (str, optional): Type of event or system that initiated this context.
                               Common values include:
                               - "http": Web request triggers
                               - "cron": Scheduled task triggers
                               - "cli": Command-line invocation
                               - "message": Message queue/pub-sub triggers
                               - "manual": Direct programmatic invocation
                               - "test": Unit test execution
                               Defaults to "unknown".
        timestamp (str, optional): ISO 8601 formatted timestamp indicating when
                                 this context was created. If not provided,
                                 automatically generated using get_current_timestamp().
                                 Should include timezone information for production use.
        **kwargs (Any): Additional arbitrary data to include in the context.
                       These become top-level fields in the returned dictionary
                       and can contain any JSON-serializable data including
                       nested objects, arrays, and primitive types.

    Returns:
        Ctx: A new context dictionary containing the specified trigger, timestamp,
             and any additional fields provided via kwargs. The dictionary can be
             safely modified by links in the chain.

    Example:
        >>> # Basic context creation
        >>> ctx = create_context(trigger="manual")
        >>> print(ctx["trigger"])  # "manual"
        >>> print(ctx["timestamp"])  # Auto-generated timestamp

        >>> # Context with custom data
        >>> ctx = create_context(
        ...     trigger="api",
        ...     user_id="123",
        ...     operation="user_signup",
        ...     metadata={"source": "mobile_app", "version": "2.1.0"}
        ... )

        >>> # Using in a chain
        >>> initial_ctx = create_context(
        ...     trigger="cron",
        ...     job_type="cleanup",
        ...     batch_size=100
        ... )
        >>> result = await cleanup_chain(initial_ctx)

    Note:
        This function uses keyword-only arguments (note the *) to prevent
        positional argument confusion and ensure explicit, readable context creation.
    """
    ctx: Ctx = {
        "trigger": trigger,
        "type": trigger,  # Add type field as alias for trigger for backward compatibility
        "timestamp": timestamp or get_current_timestamp(),
        **kwargs,
    }
    return ctx


def create_http_context(
    request=None,
    method: str = "GET",
    path: str = "/",
    query: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Ctx:
    """Create an HTTP-specific ModuLink context for web request processing.

    This specialized context factory creates contexts optimized for HTTP request
    processing. It includes all the standard web request metadata that ModuLink
    chains typically need when handling API endpoints, webhooks, or web application
    requests.

    The resulting context is structured to work seamlessly with web frameworks
    like FastAPI, Flask, Django, and others, providing a consistent interface
    regardless of the underlying web framework.

    Args:
        request (Any, optional): The original HTTP request object from your web framework.
                               Can be a FastAPI Request, Flask request, Django HttpRequest,
                               or any other framework's request object. Used for accessing
                               framework-specific features when needed. Defaults to None.
        method (str, optional): HTTP method for the request.
                              Common values: "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS".
                              Should be uppercase for consistency. Defaults to "GET".
        path (str, optional): The request path/route without query parameters.
                            Should start with "/" and represent the resource being accessed.
                            Examples: "/api/users", "/health", "/webhook/github".
                            Defaults to "/".
        query (Dict[str, Any], optional): Query parameters from the URL as key-value pairs.
                                        Values can be strings, lists (for multiple values),
                                        or None. Example: {"page": "1", "limit": "10"}.
                                        Defaults to empty dict.
        body (Dict[str, Any], optional): Parsed request body data for POST/PUT/PATCH requests.
                                       Should contain the deserialized JSON/form data.
                                       For file uploads, consider storing file metadata here.
                                       Defaults to empty dict.
        headers (Dict[str, Any], optional): HTTP headers as key-value pairs.
                                          Keys should be lowercase for consistency.
                                          Common headers: {"content-type": "application/json",
                                          "authorization": "Bearer token123"}.
                                          Defaults to empty dict.
        **kwargs (Any): Additional request-specific data such as:
                       - user_id: Authenticated user identifier
                       - session_id: Session tracking information
                       - ip_address: Client IP address
                       - user_agent: Browser/client information
                       - correlation_id: Request tracing identifier

    Returns:
        Ctx: HTTP context dictionary containing:
             - trigger: Set to "http"
             - timestamp: Auto-generated ISO timestamp
             - req: Original request object (if provided)
             - method: HTTP method
             - path: Request path
             - query: Query parameters
             - body: Request body data
             - headers: HTTP headers
             - Plus any additional fields from kwargs

    Example:
        >>> # Basic HTTP context
        >>> ctx = create_http_context(
        ...     method="POST",
        ...     path="/api/users",
        ...     body={"name": "Alice", "email": "alice@example.com"}
        ... )

        >>> # Full HTTP context with authentication
        >>> ctx = create_http_context(
        ...     request=fastapi_request,
        ...     method="GET",
        ...     path="/api/users/123",
        ...     query={"include": "profile"},
        ...     headers={"authorization": "Bearer abc123"},
        ...     user_id="user_123",
        ...     correlation_id="req_456"
        ... )

        >>> # Using with a web framework
        >>> @app.post("/api/users")
        >>> async def create_user(request: Request):
        ...     ctx = create_http_context(
        ...         request=request,
        ...         method="POST",
        ...         path="/api/users",
        ...         body=await request.json()
        ...     )
        ...     return await user_creation_chain(ctx)

    Note:
        This function automatically sets the trigger to "http" and provides
        sensible defaults for all HTTP-related fields to ensure consistent
        context structure across different web frameworks.
    """
    return create_context(
        trigger="http",
        req=request,
        request=request,  # Add 'request' field for backward compatibility
        method=method,
        path=path,
        query=query or {},
        body=body or {},
        headers=headers or {},
        **kwargs,
    )


def create_cron_context(schedule: str, **kwargs: Any) -> Ctx:
    """Create a cron-specific ModuLink context for scheduled task processing.

    This specialized context factory creates contexts optimized for scheduled tasks
    and background jobs. It includes scheduling metadata that helps with job tracking,
    monitoring, and debugging cron-based workflows.

    Args:
        schedule (str): Cron schedule expression that triggered this execution.
                       Should follow standard cron format (5 or 6 fields).
                       Examples:
                       - "0 0 * * *" (daily at midnight)
                       - "*/15 * * * *" (every 15 minutes)
                       - "0 9 * * 1-5" (weekdays at 9 AM)
                       - "0 0 1 * *" (first day of every month)
        **kwargs (Any): Additional scheduling context such as:
                       - job_id: Unique identifier for this job instance
                       - job_name: Human-readable name for the scheduled task
                       - expected_duration: Estimated execution time in seconds
                       - max_retries: Number of retry attempts allowed
                       - environment: Deployment environment (prod, staging, dev)
                       - last_run: Timestamp of the previous execution
                       - next_run: Timestamp of the next scheduled execution

    Returns:
        Ctx: Cron context dictionary containing:
             - trigger: Set to "cron"
             - timestamp: Auto-generated ISO timestamp of execution start
             - schedule: The cron expression that triggered this execution
             - Plus any additional fields from kwargs

    Example:
        >>> # Basic daily cleanup job
        >>> ctx = create_cron_context(
        ...     schedule="0 2 * * *",  # 2 AM daily
        ...     job_name="cleanup_temp_files",
        ...     job_id="cleanup_001"
        ... )

        >>> # Complex scheduled report generation
        >>> ctx = create_cron_context(
        ...     schedule="0 6 * * 1",  # Monday 6 AM
        ...     job_name="weekly_analytics_report",
        ...     job_id="analytics_weekly_001",
        ...     expected_duration=300,  # 5 minutes
        ...     max_retries=3,
        ...     report_type="user_engagement",
        ...     recipients=["admin@company.com", "analytics@company.com"]
        ... )

        >>> # Using with a scheduler
        >>> @scheduler.scheduled_job("cron", hour=0, minute=0)
        >>> async def midnight_cleanup():
        ...     ctx = create_cron_context(
        ...         schedule="0 0 * * *",
        ...         job_name="midnight_cleanup",
        ...         cleanup_type="full"
        ...     )
        ...     await cleanup_chain(ctx)

    Note:
        The schedule parameter should be the exact cron expression that triggered
        this execution. This helps with debugging scheduling issues and provides
        audit trails for scheduled operations.
    """
    return create_context(
        trigger="cron",
        schedule=schedule,
        scheduled_at=kwargs.get("scheduled_at", get_current_timestamp()),
        **kwargs,
    )


def create_cli_context(command: str, args: Optional[list] = None, **kwargs: Any) -> Ctx:
    """Create a CLI-specific ModuLink context for command-line application processing.

    This specialized context factory creates contexts optimized for command-line
    applications and scripts. It captures command invocation details that help
    with argument processing, help generation, and CLI workflow management.

    Args:
        command (str): The primary command or script name that was invoked.
                      Should be the base command without arguments.
                      Examples: "migrate", "deploy", "backup", "process-files"
        args (list, optional): Command-line arguments passed to the command.
                              Should be a list of strings representing the parsed arguments.
                              Can include flags, options, and positional arguments.
                              Example: ["--verbose", "--env=production", "user_data.csv"]
                              Defaults to empty list.
        **kwargs (Any): Additional CLI context such as:
                       - working_directory: Current working directory when command was run
                       - environment_vars: Relevant environment variables
                       - user: System user running the command
                       - terminal_type: Type of terminal/shell being used
                       - script_path: Full path to the script being executed
                       - pid: Process ID of the command execution
                       - exit_code: Expected exit code for successful execution
                       - help_requested: Boolean indicating if help was requested

    Returns:
        Ctx: CLI context dictionary containing:
             - trigger: Set to "cli"
             - timestamp: Auto-generated ISO timestamp of command execution
             - command: The command name that was invoked
             - args: List of command-line arguments
             - Plus any additional fields from kwargs

    Example:
        >>> # Basic CLI command
        >>> ctx = create_cli_context(
        ...     command="backup",
        ...     args=["--database", "production", "--compress"]
        ... )

        >>> # Complex CLI with environment context
        >>> ctx = create_cli_context(
        ...     command="deploy",
        ...     args=["--env", "staging", "--version", "1.2.3", "--force"],
        ...     working_directory="/projects/myapp",
        ...     user="deploy_user",
        ...     deployment_target="staging-cluster",
        ...     git_commit="abc123def456"
        ... )

        >>> # Using with Click framework
        >>> @click.command()
        >>> @click.option('--verbose', is_flag=True)
        >>> @click.argument('filename')
        >>> def process_file(verbose, filename):
        ...     ctx = create_cli_context(
        ...         command="process_file",
        ...         args=[f"--verbose={verbose}", filename],
        ...         input_file=filename,
        ...         verbose=verbose
        ...     )
        ...     await file_processing_chain(ctx)

        >>> # Using with argparse
        >>> def main():
        ...     parser = argparse.ArgumentParser()
        ...     parser.add_argument('--config', required=True)
        ...     parsed_args = parser.parse_args()
        ...
        ...     ctx = create_cli_context(
        ...         command="main",
        ...         args=sys.argv[1:],
        ...         config_file=parsed_args.config
        ...     )
        ...     await main_processing_chain(ctx)

    Note:
        The args list should contain the actual arguments passed to the command,
        not the parsed/processed versions. This preserves the original command
        invocation for debugging and audit purposes.
    """
    return create_context(
        trigger="cli",
        command=command,
        args=args or [],
        invoked_at=kwargs.get("invoked_at", get_current_timestamp()),
        **kwargs,
    )


def create_message_context(topic: str, message: Any, **kwargs: Any) -> Ctx:
    """Create a message-specific ModuLink context for event-driven and messaging processing.

    This specialized context factory creates contexts optimized for message queue,
    pub/sub, and event-driven architectures. It captures message metadata that helps
    with processing, routing, acknowledgment, and error handling in distributed systems.

    Args:
        topic (str): The message topic, queue name, or event type that triggered this processing.
                    Should represent the logical channel or category of the message.
                    Examples:
                    - "user.created" (domain events)
                    - "order.payment.processed" (business events)
                    - "notifications.email" (system queues)
                    - "analytics.pageview" (tracking events)
        message (Any): The actual message payload or event data.
                      Can be any serializable data structure including:
                      - Dictionaries for structured data
                      - Strings for text messages
                      - Lists for batch operations
                      - Custom objects (will be stored as-is)
        **kwargs (Any): Additional messaging context such as:
                       - message_id: Unique identifier for this specific message
                       - correlation_id: Identifier linking related messages
                       - producer: Service/system that sent the message
                       - consumer_group: Group of consumers processing this message type
                       - partition: Message partition for ordered processing
                       - offset: Message offset within the partition
                       - retry_count: Number of processing attempts made
                       - max_retries: Maximum retry attempts allowed
                       - dead_letter_queue: Queue for failed messages
                       - priority: Message processing priority (1-10)
                       - expires_at: Message expiration timestamp

    Returns:
        Ctx: Message context dictionary containing:
             - trigger: Set to "message"
             - timestamp: Auto-generated ISO timestamp when context was created
             - topic: The message topic/queue/event type
             - message: The actual message payload
             - Plus any additional fields from kwargs

    Example:
        >>> # Basic event processing
        >>> ctx = create_message_context(
        ...     topic="user.signup.completed",
        ...     message={"user_id": "123", "email": "alice@example.com"},
        ...     message_id="msg_456",
        ...     correlation_id="signup_789"
        ... )

        >>> # Complex message with retry logic
        >>> ctx = create_message_context(
        ...     topic="order.payment.failed",
        ...     message={
        ...         "order_id": "order_123",
        ...         "payment_method": "credit_card",
        ...         "amount": 99.99,
        ...         "error_code": "insufficient_funds"
        ...     },
        ...     message_id="payment_failure_456",
        ...     correlation_id="order_123",
        ...     retry_count=1,
        ...     max_retries=3,
        ...     producer="payment_service",
        ...     priority=8
        ... )

        >>> # Using with message queue frameworks
        >>> # Kafka example
        >>> def kafka_message_handler(kafka_message):
        ...     ctx = create_message_context(
        ...         topic=kafka_message.topic,
        ...         message=json.loads(kafka_message.value),
        ...         partition=kafka_message.partition,
        ...         offset=kafka_message.offset,
        ...         producer=kafka_message.headers.get('producer'),
        ...         message_id=kafka_message.headers.get('message_id')
        ...     )
        ...     await process_message_chain(ctx)
        >>>
        >>> # RabbitMQ example
        >>> def rabbitmq_callback(channel, method, properties, body):
        ...     ctx = create_message_context(
        ...         topic=method.routing_key,
        ...         message=json.loads(body),
        ...         message_id=properties.message_id,
        ...         correlation_id=properties.correlation_id,
        ...         retry_count=properties.headers.get('retry_count', 0)
        ...     )
        ...     await process_message_chain(ctx)

    Note:
        The message payload is stored as-is in the context. For large messages,
        consider storing a reference (like S3 key) instead of the full payload
        to avoid memory issues in high-throughput scenarios.
    """
    return create_context(
        trigger="message",
        topic=topic,
        message=message,
        received_at=kwargs.get("received_at", get_current_timestamp()),
        **kwargs,
    )


# For backward compatibility and convenience
def ctx(**kwargs) -> Ctx:
    """Create a new context dictionary with optional initial values.

    This is a convenience function for creating simple ModuLink contexts when you
    don't need the specialized context factories (HTTP, cron, CLI, message). It provides
    a quick way to create contexts for testing, manual invocation, or simple use cases.

    This function bypasses the standard ModuLink context structure and creates a
    plain dictionary, making it useful for:
    - Unit testing ModuLink chains
    - Prototyping and development
    - Simple scripts that don't need trigger metadata
    - Converting existing dictionaries to ModuLink contexts

    Args:
        **kwargs (Any): Arbitrary key-value pairs to include in the context.
                       Can be any JSON-serializable data including nested
                       objects, arrays, and primitive types.

    Returns:
        Ctx: A simple context dictionary containing only the provided kwargs.
             No automatic timestamp, trigger, or other metadata is added.

    Example:
        >>> # Simple context creation
        >>> ctx = ctx(user_id="123", action="login")
        >>> print(ctx)  # {"user_id": "123", "action": "login"}

        >>> # Complex nested data
        >>> ctx = ctx(
        ...     user={"id": "123", "name": "Alice"},
        ...     preferences={"theme": "dark", "language": "en"},
        ...     session={"id": "sess_456", "expires": "2024-01-15T10:00:00"}
        ... )

        >>> # Converting existing data
        >>> existing_data = {"temperature": 23.5, "humidity": 65}
        >>> ctx = ctx(**existing_data, location="office", sensor_id="temp_001")

        >>> # Using in tests
        >>> def test_user_processing():
        ...     test_ctx = ctx(
        ...         user_id="test_user_123",
        ...         email="test@example.com",
        ...         test_mode=True
        ...     )
        ...     result = await user_processing_chain(test_ctx)
        ...     assert result["processed"] is True

    Note:
        Unlike create_context() and its specialized variants, this function does NOT
        automatically add timestamp, trigger, or other standard ModuLink metadata.
        For production use, prefer the specialized context creation functions.
    """
    return dict(kwargs)
