"""Documentation API for ModuLink Next.

Provides programmatic access to documentation for LMMs and users.
Supports topic-based lookup for code, guides, and recipes.
See README.md for more details.
"""

import importlib
import sys
import difflib
from pathlib import Path

DOC_TOPICS = {
    "chain": "src/chain.py",
    "middleware.Logging": "src/middleware.py",
    "middleware.Timing": "src/middleware.py",
    "example usage": "docs/README.md",
    "readme": "docs/README.md",
    "examples": "docs/examples.md",
    "todo": "docs/TODO.md",
}

def get_doc(topic: str) -> str:
    """
    Return documentation for the given topic, with fuzzy matching support.

    Args:
        topic (str): The documentation topic to query (e.g., 'chain', 'middleware.Logging', 'readme').
    Returns:
        str: The documentation text for the topic, or a not-found message.
    Notes:
        - Looks up code or markdown files for most topics.
        - For middleware and chain, returns class docstrings if available.
        - Used by the CLI and for programmatic doc queries.
    """
    topic = topic.lower()
    # Fuzzy match against DOC_TOPICS keys
    best_match = difflib.get_close_matches(topic, [k.lower() for k in DOC_TOPICS.keys()], n=1, cutoff=0.6)
    if best_match:
        topic = best_match[0]
    if topic in ("readme", "example usage"):
        path = Path(__file__).parent.parent / "docs" / "README.md"
        if path.exists():
            return path.read_text()
        return "README.md not found."
    elif topic == "examples":
        path = Path(__file__).parent.parent / "docs" / "examples.md"
        if path.exists():
            return path.read_text()
        return "examples.md not found."
    elif topic == "todo":
        path = Path(__file__).parent.parent / "docs" / "TODO.md"
        if path.exists():
            return path.read_text()
        return "TODO.md not found."
    elif topic.startswith("middleware."):
        # Extract class docstring
        from . import middleware
        cls_name = topic.split(".", 1)[1].capitalize()
        cls = getattr(middleware, cls_name, None)
        if cls and cls.__doc__:
            return cls.__doc__
        return f"Middleware '{cls_name}' not found."
    elif topic == "chain":
        from . import chain
        if hasattr(chain, "Chain"):
            return chain.Chain.__doc__ or "No docstring for Chain."
        return "Chain class not found."
    else:
        # Suggest closest topic if not found
        suggestion = difflib.get_close_matches(topic, [k.lower() for k in DOC_TOPICS.keys()], n=1)
        if suggestion:
            return f"No documentation found for topic '{topic}'. Did you mean '{suggestion[0]}'?"
        return f"No documentation found for topic '{topic}'."

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Query ModuLink documentation.")
    parser.add_argument("topic", nargs="?", default="readme", help="Documentation topic (e.g., chain, middleware.Logging, examples, todo, readme)")
    args = parser.parse_args()
    print(get_doc(args.topic))
