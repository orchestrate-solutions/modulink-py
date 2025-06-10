"""
ModuLink Core Implementation for Python

This is the simplified implementation using the ModuLink type system.
It replaces the over-engineered class-based approach with simple function types.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .types import ChainFunction, ConnectionType, Ctx, Link, MiddlewareFunction, Status

logger = logging.getLogger(__name__)

# Import CONNECTION_HANDLERS for testing accessibility
try:
    from .connect import CONNECTION_HANDLERS
except ImportError:
    CONNECTION_HANDLERS = None  # type: ignore


class ModulinkOptions:
    """Configuration options for ModuLink.

    This class provides configuration settings for ModuLink instances,
    allowing users to customize behavior for different deployment environments
    and logging preferences.

    Attributes:
        environment (str): The deployment environment (e.g., 'development', 'production', 'testing').
                          Defaults to 'development'.
        enable_logging (bool): Whether to enable internal ModuLink logging.
                              When True, ModuLink will output operational messages.
                              Defaults to True.

    Example:
        >>> options = ModulinkOptions(environment="production", enable_logging=False)
        >>> modulink = create_modulink(options=options)
    """

    def __init__(self, environment: str = "development", enable_logging: bool = True):
        """Initialize ModulinkOptions with environment and logging settings.

        Args:
            environment (str, optional): The deployment environment name.
                                       Common values include 'development', 'production', 'testing'.
                                       Defaults to 'development'.
            enable_logging (bool, optional): Whether to enable ModuLink's internal logging.
                                           When True, operational messages are printed to console.
                                           Defaults to True.
        """
        self.environment = environment
        self.enable_logging = enable_logging


def create_modulink(app=None, options: Optional[ModulinkOptions] = None):
    """Factory function to create a ModuLink instance with universal types.

    This is the main entry point for creating a ModuLink instance. It sets up
    the complete ModuLink ecosystem including middleware management, chain composition,
    trigger handling, and provides a clean API for building modular applications.

    The returned instance provides:
    - Chain creation and composition via create_chain()
    - Middleware management via the 'use' interface
    - Trigger factories via the 'triggers' dictionary
    - Convenience methods via the 'when' interface
    - Registration and retrieval of named chains and links

    Args:
        app (Any, optional): Optional web framework application instance.
                           Supports FastAPI, Flask, and other WSGI/ASGI frameworks.
                           Required for HTTP triggers to function properly.
                           Defaults to None.
        options (ModulinkOptions, optional): Configuration options for the ModuLink instance.
                                           If not provided, defaults to ModulinkOptions()
                                           with development environment and logging enabled.

    Returns:
        ModuLinkInstance: A configured ModuLink instance with the following attributes:
            - create_chain: Function to create chains from links
            - create_named_chain: Function to create named chains with middleware
            - use: Middleware management interface
            - when: Convenience methods for common patterns
            - triggers: Dictionary of trigger factory functions
            - register_chain/register_link: Functions for named registration
            - get_chain: Function to retrieve registered chains
            - cleanup: Function to clean up resources
            - environment: Current environment setting
            - enable_logging: Current logging setting

    Example:
        >>> from modulink import create_modulink, ModulinkOptions
        >>>
        >>> # Basic usage
        >>> modulink = create_modulink()
        >>>
        >>> # With FastAPI app
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> modulink = create_modulink(app=app)
        >>>
        >>> # With custom options
        >>> options = ModulinkOptions(environment="production", enable_logging=False)
        >>> modulink = create_modulink(app=app, options=options)
    """
    if options is None:
        options = ModulinkOptions()

    # Internal state
    global_middleware: List[MiddlewareFunction] = []
    link_middleware: Dict[str, Dict[str, List[MiddlewareFunction]]] = {}
    chain_middleware: Dict[str, Dict[str, List[MiddlewareFunction]]] = {}
    cron_tasks: List[Any] = []

    # Store the app for use by triggers and connection handlers
    framework_app = app

    def log(message: str) -> None:
        """Internal logging function for ModuLink operations.

        Conditionally logs messages based on the enable_logging configuration.
        All log messages are prefixed with "[ModuLink]" for easy identification.

        Args:
            message (str): The message to log. Should be a descriptive string
                         about the operation being performed or completed.

        Returns:
            None

        Note:
            Logging output goes to stdout via print(). In production environments,
            consider redirecting this to a proper logging system.
        """
        if options.enable_logging:
            print(f"[ModuLink] {message}")

    async def _ensure_async_link(link: Link) -> ChainFunction:
        """Convert a link function to an async function for uniform execution.

        This internal helper ensures that all links can be executed uniformly
        within the async chain execution context, regardless of whether the
        original link was defined as sync or async.

        Args:
            link (Link): A link function that may be either synchronous or asynchronous.
                       Must accept a Ctx parameter and return a Ctx.

        Returns:
            ChainFunction: An async function that accepts a Ctx and returns a Ctx.
                         This function will properly await the link if it's async,
                         or execute it synchronously if needed.

        Note:
            This function uses asyncio.iscoroutinefunction() to detect async functions.
            Sync functions are executed directly within the async wrapper.
        """

        async def async_wrapper(ctx: Ctx) -> Ctx:
            if asyncio.iscoroutinefunction(link):
                return await link(ctx)
            else:
                # For sync functions, call them directly and return the result
                # Since this is an async function, mypy knows the return is Awaitable[Ctx]
                return link(ctx)  # type: ignore

        return async_wrapper

    class MiddlewareInterface:
        """Interface for registering middleware at different scopes within ModuLink.

        This class provides methods to register middleware functions that can be applied
        globally. Middleware functions are executed in the order they are registered
        and can modify the context, perform side effects, or halt execution by setting
        an error.

        Methods:
            global_middleware: Register middleware that applies to all chains
        """

        def global_middleware(self, mw: MiddlewareFunction) -> None:
            """Register global middleware that applies to all chains.

            Global middleware is automatically applied to every chain created
            through create_chain(). This is useful for cross-cutting concerns
            like logging, authentication, or error handling that should apply
            universally.

            Args:
                mw (MiddlewareFunction): An async function that accepts a Ctx and returns a Ctx.
                                       The middleware can modify the context, perform side effects,
                                       or halt execution by setting ctx["error"].

            Returns:
                None

            Example:
                >>> async def logging_middleware(ctx):
                ...     print(f"Processing request: {ctx.get('request_id', 'unknown')}")
                ...     return ctx
                >>>
                >>> modulink.use.global_middleware(logging_middleware)
            """
            global_middleware.append(mw)
            log("Global middleware registered")

    class ConvenienceMethods:
        """Convenience methods for common ModuLink patterns.

        This class provides simplified methods that create basic async functions
        for common use cases. These methods accept either single links or multiple
        links, treating a single link as a 1-dimensional chain.

        Methods:
            http: Create HTTP handler
            cron: Create scheduled handler
            message: Create message handler
            cli: Create CLI command handler
        """

        def _create_chain_handler(self, *links: Link) -> ChainFunction:
            """Create a chain handler that applies global middleware and executes links.

            This internal method creates a unified handler for all convenience methods,
            ensuring consistent behavior whether passed a single link or multiple links.
            A single link is treated as a 1-dimensional chain.

            Args:
                *links (Link): Variable number of link functions to compose.
                               If one link is provided, it's treated as a 1-dimensional chain.
                               If multiple links are provided, they're executed in sequence.

            Returns:
                ChainFunction: An async function that executes the links with global middleware.
            """

            async def handler(ctx: Ctx) -> Ctx:
                result = ctx.copy()

                try:
                    # Apply global middleware first
                    for mw in global_middleware:
                        result = await mw(result)
                        if result.get("error"):
                            break

                    # Execute links in sequence (single link = 1-dimensional chain)
                    for link in links:
                        if result.get("error"):
                            break

                        async_link = await _ensure_async_link(link)
                        result = await async_link(result)

                except Exception as e:
                    result["error"] = (
                        e  # Store the actual exception object, not just the string
                    )

                return result

            return handler

        def http(self, *links: Link) -> ChainFunction:
            """Create an async function for HTTP handling.

            This convenience method creates an async function for HTTP handling.
            Accepts either a single link (treated as 1-dimensional chain) or multiple links.

            Args:
                *links (Link): Variable number of link functions to compose.
                               A single link is treated as a 1-dimensional chain.
                               Multiple links are executed in sequence.

            Returns:
                ChainFunction: An async function that executes the links in sequence.

            Example:
                >>> # Single link (1-dimensional chain)
                >>> handler = modulink.when.http(auth_link)
                >>>
                >>> # Multiple links (multi-dimensional chain)
                >>> handler = modulink.when.http(auth_link, get_users_link)
            """
            return self._create_chain_handler(*links)

        def cron(self, *links: Link) -> ChainFunction:
            """Create an async function for scheduled tasks.

            This convenience method creates an async function for scheduled tasks.
            Accepts either a single link (treated as 1-dimensional chain) or multiple links.

            Args:
                *links (Link): Variable number of link functions to compose.
                               A single link is treated as a 1-dimensional chain.
                               Multiple links are executed in sequence.

            Returns:
                ChainFunction: An async function that executes the links in sequence.

            Example:
                >>> # Single link (1-dimensional chain)
                >>> handler = modulink.when.cron(backup_link)
                >>>
                >>> # Multiple links (multi-dimensional chain)
                >>> handler = modulink.when.cron(backup_link, cleanup_link)
            """
            return self._create_chain_handler(*links)

        def message(self, *links: Link) -> ChainFunction:
            """Create an async function for message handling.

            This convenience method creates an async function for message handling.
            Accepts either a single link (treated as 1-dimensional chain) or multiple links.

            Args:
                *links (Link): Variable number of link functions to compose.
                               A single link is treated as a 1-dimensional chain.
                               Multiple links are executed in sequence.

            Returns:
                ChainFunction: An async function that executes the links in sequence.

            Example:
                >>> # Single link (1-dimensional chain)
                >>> handler = modulink.when.message(validate_link)
                >>>
                >>> # Multiple links (multi-dimensional chain)
                >>> handler = modulink.when.message(validate_link, process_user_link)
            """
            return self._create_chain_handler(*links)

        def cli(self, *links: Link) -> ChainFunction:
            """Create an async function for CLI commands.

            This convenience method creates an async function for CLI commands.
            Accepts either a single link (treated as 1-dimensional chain) or multiple links.

            Args:
                *links (Link): Variable number of link functions to compose.
                               A single link is treated as a 1-dimensional chain.
                               Multiple links are executed in sequence.

            Returns:
                ChainFunction: An async function that executes the links in sequence.

            Example:
                >>> # Single link (1-dimensional chain)
                >>> handler = modulink.when.cli(validate_args_link)
                >>>
                >>> # Multiple links (multi-dimensional chain)
                >>> handler = modulink.when.cli(validate_args_link, deploy_link)
            """
            return self._create_chain_handler(*links)

    # Public API
    use = MiddlewareInterface()
    when = ConvenienceMethods()

    def cleanup() -> Dict[str, Any]:
        """Clean up resources and reset internal state.

        This function cleans up all internal resources and resets the ModuLink
        instance to a clean state. This is useful for testing, shutdown procedures,
        or when you need to reset the ModuLink instance.

        The cleanup process:
        1. Clears all global middleware
        2. Clears all link middleware configurations
        3. Clears all chain middleware configurations
        4. Clears all scheduled cron tasks
        5. Logs the completion of cleanup

        Returns:
            Dict[str, Any]: Status dictionary with success/failure information.
                          Keys: 'status' (Status), 'message' (str), 'error' (str, optional)

        Example:
            >>> # During application shutdown
            >>> result = modulink.cleanup()
            >>> if result['status'] == Status.SUCCESS:
            ...     print("Cleanup successful")
            >>> else:
            ...     print(f"Cleanup failed: {result['error']}")
            >>>
            >>> # In tests for clean state
            >>> def test_setup():
            ...     result = modulink.cleanup()  # Start with clean state
            ...     assert result['status'] == Status.SUCCESS, f"Cleanup failed: {result.get('error')}"
            ...     # ... test code

        Note:
            This completely resets the ModuLink instance state, including
            all registered middleware and scheduled tasks. Returns status
            to indicate success or failure of the cleanup operation.
        """
        try:
            global_middleware.clear()
            link_middleware.clear()
            chain_middleware.clear()
            cron_tasks.clear()

            log("Cleanup completed - all state cleared")
            return {
                "status": Status.SUCCESS,
                "message": "Cleanup completed successfully - all state cleared",
            }
        except Exception as error:
            error_msg = f"Cleanup failed: {str(error)}"
            log(error_msg)
            return {
                "status": Status.FAILED,
                "message": "Cleanup failed",
                "error": str(error),
            }

    def connect(connection_type, chain_fn, **kwargs):
        """Connect a ModuLink chain to external systems (HTTP, cron, CLI, message).

        This is the unified interface for connecting ModuLink chains to different
        systems. It provides a consistent API for integrating chains with web
        frameworks, schedulers, command-line interfaces, and message systems.

        This function works with both ModuLink instance chains, standalone chains,
        and single links (treated as 1-dimensional chains).

        Args:
            connection_type (ConnectionType): Type of connection using the ConnectionType enum.
                                            Available options: ConnectionType.HTTP, ConnectionType.CRON,
                                            ConnectionType.CLI, ConnectionType.MESSAGE
            chain_fn: ModuLink chain function, standalone chain function, or single link function.
                     Single links are treated as 1-dimensional chains.
            **kwargs: Connection-specific parameters:
                For HTTP: app, method, path
                For cron: scheduler, cron_expression
                For CLI: cli_group, command_name
                For MESSAGE: topic (required), plus optional message system config

        Returns:
            Result from the connection handler

        Raises:
            ValueError: If connection_type is not supported or required params missing
            TypeError: If connection_type is not a ConnectionType enum value

        Example:
            >>> from modulink.types import ConnectionType
            >>> from modulink.chain import chain
            >>>
            >>> # With standalone chain
            >>> my_chain = chain(auth_link, data_link)
            >>> modulink.connect(ConnectionType.HTTP, my_chain,
            ...                  app=fastapi_app, method="POST", path="/api/data")
            >>>
            >>> # With single link (treated as 1-dimensional chain)
            >>> modulink.connect(ConnectionType.HTTP, auth_link,
            ...                  app=fastapi_app, method="GET", path="/api/auth")
        """
        # Validate connection_type is a ConnectionType enum
        if not isinstance(connection_type, ConnectionType):
            if isinstance(connection_type, str):
                # Try to convert string to enum for backward compatibility
                try:
                    connection_type = ConnectionType(connection_type.lower())
                except ValueError:
                    supported_types = [ct.value for ct in ConnectionType]
                    raise ValueError(
                        f"Unsupported connection type '{connection_type}'. Supported types: {supported_types}"
                    )
            else:
                raise TypeError(
                    f"connection_type must be a ConnectionType enum, got {type(connection_type)}"
                )

        # Check if CONNECTION_HANDLERS is available (for testing)
        if CONNECTION_HANDLERS is None:
            raise ImportError("CONNECTION_HANDLERS not available")

        if connection_type not in CONNECTION_HANDLERS:
            supported_types = [ct.value for ct in ConnectionType]
            raise ValueError(
                f"Unsupported connection type '{connection_type.value}'. Supported types: {supported_types}"
            )

        # If chain_fn is a single link function, wrap it to make it chain-compatible
        # This treats a single link as a 1-dimensional chain
        if callable(chain_fn) and not hasattr(chain_fn, "links"):
            # This is likely a single link function, wrap it to be chain-compatible
            original_link = chain_fn

            async def chain_wrapper(ctx: Ctx) -> Ctx:
                """Wrapper to make a single link behave like a 1-dimensional chain."""
                async_link = await _ensure_async_link(original_link)
                return await async_link(ctx)

            chain_fn = chain_wrapper

        # Create a context creation function for the handlers
        def create_context(**context_kwargs):
            from .types import create_context

            return create_context(**context_kwargs)

        # Create a minimal modulink interface for handlers
        handler_modulink = type(
            "HandlerModulink",
            (),
            {
                "create_context": create_context,
                "app": framework_app,  # Make app available to connection handlers
            },
        )()

        # Get the handler and execute it
        handler = CONNECTION_HANDLERS[connection_type]
        return handler(handler_modulink, chain_fn, **kwargs)

    class ModuLinkInstance:
        """The main ModuLink instance providing access to all ModuLink functionality.

        This class serves as the primary interface for ModuLink operations,
        providing access to middleware management and convenience methods.
        It is returned by the create_modulink() factory function and configured
        with the provided options.

        The instance provides:
        - Middleware registration interface
        - Convenience methods for common patterns
        - Configuration and cleanup methods

        Attributes:
            use: Middleware registration interface
            when: Convenience methods interface
            cleanup: Function to clean up resources
            environment: Current environment setting
            enable_logging: Current logging configuration
        """

        def __init__(self):
            self.use = use
            self.when = when
            self.cleanup = cleanup
            self.environment = options.environment
            self.enable_logging = options.enable_logging
            self.connect = connect
            self.app = framework_app  # Expose app through the instance

    return ModuLinkInstance()


# Type alias for the ModuLink instance created by the factory function
Modulink = Any  # Runtime type would be ModuLinkInstance, but using Any for flexibility
