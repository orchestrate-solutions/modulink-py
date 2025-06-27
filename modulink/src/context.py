"""
Backward compatibility module for modulink.src.context.

DEPRECATED: Import directly from modulink instead.
    from modulink import Context  # Preferred
    from modulink.src.context import Context  # Deprecated but supported
"""

from ..context import Context

__all__ = ["Context"]
