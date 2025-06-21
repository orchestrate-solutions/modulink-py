"""
ModuLink Next: Unified exports and CLI entrypoint

This __init__.py exposes all primary ModuLink Next components and CLI utilities for easy import and use.
"""

from .src.chain import Chain
from .src.context import Context
from .src.docs import get_doc
from .src.link import Link, is_link
from .src.listeners import BaseListener
from .src.middleware import Middleware

# CLI entrypoint (if using `python -m modulink_next` or similar)
def main():
    from .src import modulink_doc
    modulink_doc.main()

__all__ = [
    "Chain",
    "Context",
    "get_doc",
    "Link",
    "is_link",
    "BaseListener",
    "Middleware",
]
