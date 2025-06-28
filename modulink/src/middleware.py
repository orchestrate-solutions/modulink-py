"""
Backward compatibility module for modulink.src.middleware.

DEPRECATED: Import directly from modulink instead.
    from modulink import Middleware, Logging, Timing, is_middleware  # Preferred
    from modulink.src.middleware import Middleware, Logging, Timing, is_middleware  # Deprecated but supported
"""

from ..middleware import Middleware, Logging, Timing, is_middleware

__all__ = ["Middleware", "Logging", "Timing", "is_middleware"]
