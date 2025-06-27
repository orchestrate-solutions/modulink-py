"""
Backward compatibility module for modulink.src.context.

DEPRECATED: Import directly from modulink instead.
    from modulink import Context  # Preferred
    from modulink.src.context import Context  # Deprecated but supported
"""

import warnings
warnings.warn(
    "DEPRECATED: Import 'Context' from 'modulink', not 'modulink.src.context'. This bridge will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2
)

from ..context import Context

__all__ = ["Context"]
