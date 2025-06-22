"""
ModuLink Next: Unified exports and CLI entrypoint

This __init__.py exposes all primary ModuLink Next components and CLI utilities for easy import and use.
"""

from .chain import *
from .context import *
from .docs import *
from .link import *
from .listeners import *
from .middleware import *

# CLI entrypoint (if using `python -m modulink_next` or similar)
def main():
    from . import modulink_doc
    modulink_doc.main()

__all__ = []
for mod in (chain, context, docs, link, listeners, middleware):
    if hasattr(mod, "__all__"):
        __all__.extend(mod.__all__)
