"""
Backward compatibility module for modulink.src.docs.

DEPRECATED: Import directly from modulink instead.
    from modulink import get_doc  # Preferred
    from modulink.src.docs import get_doc  # Deprecated but supported
"""

from ..docs import get_doc

__all__ = ["get_doc"]
