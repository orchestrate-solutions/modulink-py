"""
Backward compatibility module for modulink.src.listeners.

DEPRECATED: Import directly from modulink instead.
    from modulink import BaseListener  # Preferred
    from modulink.src.listeners import BaseListener  # Deprecated but supported
"""

from ..listeners import BaseListener

__all__ = ["BaseListener"]
