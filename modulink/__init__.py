"""
ModuLink Next: Unified exports and CLI entrypoint

This __init__.py exposes all primary ModuLink Next components and CLI utilities for easy import and use.
"""

from .chain import Chain
from .context import Context
from .docs import get_doc
from .link import Link, is_link
from .listeners import BaseListener, HttpListener, TcpListener
from .middleware import Middleware, Logging, Timing, is_middleware

# CLI entrypoint (if using `python -m modulink_next` or similar)
def main():
    from . import modulink_doc
    modulink_doc.main()

__all__ = [
    "Chain",
    "Context", 
    "get_doc",
    "Link",
    "is_link",
    "BaseListener",
    "HttpListener",
    "TcpListener",
    "Middleware",
    "Logging",
    "Timing", 
    "is_middleware",
]
