"""
ModuLink Python Implementation
"""

from .types import (
    Ctx, Link, Chain, Trigger, Middleware,
    create_context, create_http_context, create_cron_context,
    create_cli_context, create_message_context
)
from .utils import (
    chain, timing, logging, validate, performance_tracker,
    when, parallel, memoize, transform, set_values,
    filter_context, debounce, retry,
    validators, error_handlers, catch_errors
)
from .core import create_modulink

# For backward compatibility and convenience
def ctx(**kwargs) -> Ctx:
    """Create a new context dictionary with optional initial values."""
    return dict(kwargs)

__all__ = [
    # Core types
    'Ctx', 'Link', 'Chain', 'Trigger', 'Middleware', 'ctx',
    
    # Context creation
    'create_context', 'create_http_context', 'create_cron_context',
    'create_cli_context', 'create_message_context',
    
    # Core functions
    'create_modulink',
    
    # Chain and utilities
    'chain', 'timing', 'logging', 'validate', 'performance_tracker',
    'when', 'parallel', 'memoize', 'transform', 'set_values',
    'filter_context', 'debounce', 'retry', 'catch_errors',
    
    # Helper classes
    'validators', 'error_handlers'
]
