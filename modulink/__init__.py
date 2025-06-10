"""
ModuLink Python Implementation

A lightweight function composition framework for Python using universal types.
ModuLink provides simple, consistent patterns that work across multiple languages,
enabling clean functional composition with rich context flow and middleware support.

Core Philosophy:
- Universal Types: Simple function signatures that work across languages
- Functional Composition: Pure functions connected through context flow
- Minimal API: Only 5 core types you need to learn
- Context Flow: Rich context dictionaries carry data through function chains

Key Features:
- Chain-based function composition with middleware support
- Async/sync function handling with automatic type coercion
- Comprehensive error handling and recovery mechanisms
- Performance monitoring and timing utilities
- Framework integration helpers for web apps, CLI tools, and more
- Type-safe context creation with specialized factory functions

Example:
    >>> from modulink import Ctx, chain, create_context
    >>>
    >>> async def validate_user(ctx: Ctx) -> Ctx:
    ...     if not ctx.get('email'):
    ...         return {**ctx, 'errors': ['Email required']}
    ...     return ctx
    >>>
    >>> async def send_welcome(ctx: Ctx) -> Ctx:
    ...     if not ctx.get('errors'):
    ...         print(f"Welcome {ctx['email']}")
    ...         return {**ctx, 'sent': True}
    ...     return ctx
    >>>
    >>> user_flow = chain(validate_user, send_welcome)
    >>> ctx = create_context(trigger="api", email="alice@example.com")
    >>> result = await user_flow(ctx)
"""

from .chain import chain
from .core import create_modulink
from .triggers import cli_trigger, cron_trigger, http_trigger, message_trigger
from .types import (
    Chain,
    ConnectionType,
    Ctx,
    Link,
    Middleware,
    Status,
    Trigger,
    create_cli_context,
    create_context,
    create_cron_context,
    create_http_context,
    create_message_context,
)
from .utils import (
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


# For backward compatibility and convenience
def ctx(**kwargs) -> Ctx:
    """Create a new context dictionary with optional initial values."""
    return dict(kwargs)


__all__ = [
    # Core types
    "Ctx",
    "Link",
    "Chain",
    "Trigger",
    "Middleware",
    "Status",
    "ctx",
    # Context creation
    "create_context",
    "create_http_context",
    "create_cron_context",
    "create_cli_context",
    "create_message_context",
    # Core functions
    "create_modulink",
    # Standalone functions
    "chain",
    # Triggers
    "http_trigger",
    "cron_trigger",
    "message_trigger",
    "cli_trigger",
    "triggers",
    # Chain and utilities
    "timing",
    "logging",
    "validate",
    "performance_tracker",
    "when",
    "parallel",
    "memoize",
    "transform",
    "set_values",
    "filter_context",
    "debounce",
    "retry",
    "catch_errors",
    # Helper classes
    "validators",
    "error_handlers",
    # Connection type
    "ConnectionType",
]
