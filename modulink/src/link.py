"""
Backward compatibility module for modulink.src.link.

DEPRECATED: Import directly from modulink instead.
    from modulink import Link, is_link  # Preferred
    from modulink.src.link import Link, is_link  # Deprecated but supported
"""

from ..link import Link, is_link

__all__ = ["Link", "is_link"]
