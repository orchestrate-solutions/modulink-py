"""
Backward compatibility package for modulink.src.

DEPRECATED: This package is maintained for backward compatibility only.
Please migrate to importing directly from the main modulink package:

    # Preferred (new):
    from modulink import Chain, Context, Link, Middleware, Logging, Timing

    # Deprecated (old, but still supported):
    from modulink.src.chain import Chain
    from modulink.src.context import Context
    from modulink.src.link import Link
    from modulink.src.middleware import Middleware, Logging, Timing

All modules in this package are re-exports from the main modulink package.
"""

# Re-export all major components for backward compatibility
from ..chain import Chain
from ..context import Context
from ..link import Link, is_link
from ..middleware import Middleware, Logging, Timing, is_middleware
from ..listeners import BaseListener
from ..docs import get_doc

__all__ = [
    "Chain",
    "Context", 
    "Link",
    "is_link",
    "Middleware",
    "Logging",
    "Timing",
    "is_middleware",
    "BaseListener",
    "get_doc",
]
