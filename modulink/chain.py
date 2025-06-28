"""
Chain composition for ModuLink Next.

Defines the Chain class and its API for composing, connecting, and running links with middleware and error handling.
See README.md section 2.2 for details.
"""

from .context import Context
from .link import Link
from typing import Any, Callable, Awaitable, Dict, List, Optional, Protocol

class Chain:
    """
    ModuLink Next Chain: Compose, connect, and run async workflows.

    - Accepts any number of Link objects (async or sync functions) in order.
    - Supports explicit connections (branching, error handling) via .connect().
    - Supports middleware for observability, logging, and metrics via .use().
    - Runs the chain with .run(ctx), passing a Context through all links.
    - Provides .inspect() for structure introspection and dynamic docstring updates.
    - Designed for composable, testable, and debuggable async workflows.
    """
    def __init__(self, *links: Link):
        """
        Initialize a Chain with one or more Link objects.
        Links are auto-wired in sequence; use .connect() for custom flows.
        """
        self._links = list(links)
        self._connections = []
        self._middleware = []
        self._update_doc()

    def _update_doc(self):
        """
        Dynamically update the Chain's docstring to reflect its current structure.
        Lists all links, connections, and middleware attached to this chain.
        """
        doc = (self.__class__.__doc__ or "") + "\n\n"
        doc += "Links:\n"
        for link in self._links:
            doc += f"  - {getattr(link, '__name__', str(link))}: {getattr(link, '__doc__', '')}\n"
        doc += f"\nConnections: {self._connections}\n"
        doc += f"Middleware: {[type(m).__name__ for m in self._middleware]}"
        self.__doc__ = doc

    def add_link(self, link: Link):
        """
        Add a Link to the end of the chain.
        Links must conform to the Link protocol (async or sync callable).
        """
        self._links.append(link)
        self._update_doc()

    def use(self, middleware: Any, on_link: Link = None, position: str = None):
        """
        Attach middleware to the chain or to a specific link.
        If on_link is None, attaches as chain-level middleware.
        If on_link is provided, attaches as link-level middleware (before/after).
        position: 'before' or 'after' for link-level middleware.
        """
        if on_link is None:
            self._middleware.append(middleware)
        else:
            if not hasattr(on_link, "_before_middleware"):
                on_link._before_middleware = []
            if not hasattr(on_link, "_after_middleware"):
                on_link._after_middleware = []
            if position == 'before':
                on_link._before_middleware.append(middleware)
            elif position == 'after':
                on_link._after_middleware.append(middleware)
            else:
                raise ValueError("position must be 'before' or 'after' for link-level middleware")
        self._update_doc()

    def connect(self, source, target, condition):
        """
        Explicitly connect a source Link (or Chain) to a target Link (or Chain) with a condition.
        Enables branching, error handling, and custom flows.
        - source: the Link (or Chain) to branch from (must be a specific link in the current chain)
        - target: the Link or Chain to branch to if condition(ctx) is True
        - condition: a callable that takes ctx and returns bool
         
        Note: The source must be a link in this chain, and the target can be either a single Link or another Chain.
        """
        self._connections.append({"source": source, "target": target, "condition": condition})
        self._update_doc()

    async def run(self, ctx: Context) -> Context:
        """
        Execute the chain with the given Context.
        Passes the context through all links in order, applying middleware hooks.
        Handles errors and branching via .connect().
        Returns the final Context after all processing.
        Middleware receives position, index, and mwctx.
        Supports both chain-level and link-level middleware.
        """
        import inspect
        current_ctx = ctx
        mwctx = Context()  # Shared middleware context for this run
        for link_index, link in enumerate(self._links):
            # Chain-level before middleware
            for mw_index, m in enumerate(self._middleware):
                if hasattr(m, "before"):
                    m.link = link
                    m.position = 'chain-before'
                    m.index = mw_index
                    await m.before(link, current_ctx, mwctx)
            # Link-level before middleware
            if hasattr(link, "_before_middleware"):
                for mw_index, m in enumerate(link._before_middleware):
                    if hasattr(m, "before"):
                        m.link = link
                        m.position = 'link-before'
                        m.index = mw_index
                        await m.before(link, current_ctx, mwctx)
            try:
                if inspect.iscoroutinefunction(link):
                    result = await link(current_ctx)
                else:
                    result = link(current_ctx)
            except Exception as exc:
                current_ctx["exception"] = exc
                routed = False
                for conn in self._connections:
                    if conn["source"] == link and callable(conn["condition"]):
                        try:
                            if conn["condition"](current_ctx):
                                next_link = conn["target"]
                                if inspect.iscoroutinefunction(next_link):
                                    result = await next_link(current_ctx)
                                else:
                                    result = next_link(current_ctx)
                                routed = True
                                break
                        except Exception:
                            continue
                if not routed:
                    break
            # Link-level after middleware
            if hasattr(link, "_after_middleware"):
                for mw_index, m in enumerate(link._after_middleware):
                    if hasattr(m, "after"):
                        m.link = link
                        m.position = 'link-after'
                        m.index = mw_index
                        await m.after(link, current_ctx, result, mwctx)
            # Chain-level after middleware
            for mw_index, m in enumerate(self._middleware):
                if hasattr(m, "after"):
                    m.link = link
                    m.position = 'chain-after'
                    m.index = mw_index
                    await m.after(link, current_ctx, result, mwctx)
            current_ctx = result
        return current_ctx

    def inspect(self) -> dict:
        """
        Return a dict representation of the chain's structure.
        Includes all links, connections, and middleware for debugging and introspection.
        """
        return {
            "links": [getattr(link, "__name__", str(link)) for link in self._links],
            "connections": self._connections,
            "middleware": [type(m).__name__ for m in self._middleware]
        }
