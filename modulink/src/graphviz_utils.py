"""
Backward compatibility module for modulink.src.graphviz_utils.

DEPRECATED: Import directly from modulink instead.
    from modulink.graphviz_utils import to_graphviz  # Preferred
    from modulink.src.graphviz_utils import to_graphviz  # Deprecated but supported
"""

from ..graphviz_utils import *

__all__ = ["to_graphviz"]
