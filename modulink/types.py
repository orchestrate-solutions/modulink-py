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

from typing import Dict, Any, Union, Callable, Awaitable, Optional, Protocol
from datetime import datetime


# Universal Context Type - just a dictionary that can hold anything
Ctx = Dict[str, Any]


class Link(Protocol):
    """
    A Link is a function that transforms context.
    Can be sync or async - the system handles both transparently.
    """
    def __call__(self, ctx: Ctx) -> Union[Ctx, Awaitable[Ctx]]:
        """Transform context and return new context."""
        ...


class Chain(Protocol):
    """
    A Chain is an async function that transforms context.
    Chains are always async for consistency.
    """
    async def __call__(self, ctx: Ctx) -> Ctx:
        """Transform context asynchronously and return new context."""
        ...


class Trigger(Protocol):
    """
    A Trigger executes a chain with optional initial context.
    Returns the final context after chain execution.
    """
    async def __call__(self, target_chain: Chain, initial_ctx: Optional[Ctx] = None) -> Ctx:
        """Execute chain with initial context and return final context."""
        ...


class Middleware(Protocol):
    """
    Middleware transforms context without complex "next" parameter.
    Simple, pure transformations applied in sequence.
    """
    async def __call__(self, ctx: Ctx) -> Ctx:
        """Transform context and return new context."""
        ...


# Type aliases for convenience
LinkFunction = Callable[[Ctx], Union[Ctx, Awaitable[Ctx]]]
ChainFunction = Callable[[Ctx], Awaitable[Ctx]]
TriggerFunction = Callable[[Chain, Optional[Ctx]], Awaitable[Ctx]]
MiddlewareFunction = Callable[[Ctx], Awaitable[Ctx]]


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def create_context(
    *,
    trigger: str = "unknown",
    timestamp: Optional[str] = None,
    **kwargs: Any
) -> Ctx:
    """
    Create a new context with common fields.
    
    Args:
        trigger: Type of trigger ('http', 'cron', 'cli', 'message')
        timestamp: ISO timestamp (auto-generated if not provided)
        **kwargs: Additional context fields
        
    Returns:
        New context dictionary
    """
    ctx: Ctx = {
        "trigger": trigger,
        "timestamp": timestamp or get_current_timestamp(),
        **kwargs
    }
    return ctx


def create_http_context(
    request=None,
    method: str = "GET",
    path: str = "/",
    query: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Ctx:
    """
    Create HTTP-specific context.
    
    Args:
        request: HTTP request object
        method: HTTP method
        path: Request path
        query: Query parameters
        body: Request body
        headers: Request headers
        **kwargs: Additional context fields
        
    Returns:
        HTTP context dictionary
    """
    return create_context(
        trigger="http",
        req=request,
        method=method,
        path=path,
        query=query or {},
        body=body or {},
        headers=headers or {},
        **kwargs
    )


def create_cron_context(
    schedule: str,
    **kwargs: Any
) -> Ctx:
    """
    Create cron-specific context.
    
    Args:
        schedule: Cron schedule expression
        **kwargs: Additional context fields
        
    Returns:
        Cron context dictionary
    """
    return create_context(
        trigger="cron",
        schedule=schedule,
        **kwargs
    )


def create_cli_context(
    command: str,
    args: Optional[list] = None,
    **kwargs: Any
) -> Ctx:
    """
    Create CLI-specific context.
    
    Args:
        command: CLI command name
        args: Command arguments
        **kwargs: Additional context fields
        
    Returns:
        CLI context dictionary
    """
    return create_context(
        trigger="cli",
        command=command,
        args=args or [],
        **kwargs
    )


def create_message_context(
    topic: str,
    message: Any,
    **kwargs: Any
) -> Ctx:
    """
    Create message-specific context.
    
    Args:
        topic: Message topic
        message: Message payload
        **kwargs: Additional context fields
        
    Returns:
        Message context dictionary
    """
    return create_context(
        trigger="message",
        topic=topic,
        message=message,
        **kwargs
    )


# For backward compatibility and convenience
def ctx(**kwargs) -> Ctx:
    """Create a new context dictionary with optional initial values."""
    return dict(kwargs)
