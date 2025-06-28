"""
Link protocol for ModuLink Next.

Defines the Link protocol as a pure unit of work for use in chains.
Links are async or sync callables that transform a Context.
Links may also handle errors directly (hybrid error handling is supported).
See README.md section 2.1 for details.
"""

from typing import Protocol, Callable, Awaitable
from .context import Context

class Link(Protocol):
    """
    ModuLink Next Link protocol.

    - A pure unit of work: transforms input Context to output Context.
    - Can be an async or sync callable (function or class with __call__).
    - Automatic naming from function/class name.
    - Docstrings are preserved for documentation and inspection.
    - Hybrid error handling: links may handle errors directly, or let Chain handle them.
    - Used as steps in a Chain.
    """
    name: str
    __call__: Callable[[Context], Awaitable[Context]]

def is_link(obj) -> bool:
    """
    Check if an object conforms to the Link protocol.

    Args:
        obj: Any object to check.
    Returns:
        bool: True if the object is a Link (callable with a docstring), False otherwise.
    """
    return callable(obj) and hasattr(obj, "__doc__")
