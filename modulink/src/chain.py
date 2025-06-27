"""
Backward compatibility module for modulink.src.chain.

DEPRECATED: Import directly from modulink instead.
    from modulink import Chain  # Preferred
    from modulink.src.chain import Chain  # Deprecated but supported
"""

from ..chain import Chain

__all__ = ["Chain"]
