"""
Backward compatibility module for modulink.src.listeners.

DEPRECATED: Import directly from modulink instead.
    from modulink.listeners import BaseListener, HttpListener, TcpListener  # Preferred
    from modulink.src.listeners import BaseListener, HttpListener, TcpListener  # Deprecated but supported
"""

from ..listeners import BaseListener, HttpListener, TcpListener

__all__ = ["BaseListener", "HttpListener", "TcpListener"]
