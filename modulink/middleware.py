"""Middleware protocol and examples for ModuLink Next.

Defines the Middleware protocol and example middleware for observability and logging.
Middleware can be attached to chains or links and is link-aware (readonly).

Middleware is not allowed to modify the main ctx (context) passed through the chain and links.
Instead, middleware can write to a separate mwctx, which is a Context shared among all middleware in the same chain run.
Use mwctx for cross-cutting concerns (timing, tracing, etc.), but avoid using it for business logic or critical workflow decisions.
See README.md section 2.4 for details.
"""

from typing import Protocol, Optional
from .link import Link
from .context import Context

class Middleware(Protocol):
    """
    ModuLink Next Middleware protocol.

    - Used for observability, logging, or inspection during chain execution.
    - Must implement async before(link, ctx, mwctx) and after(link, ctx, result, mwctx) methods.
    - Middleware is link-aware: receives the link it is running before/after (readonly).
    - Middleware can be attached globally (chain) or to a specific link (before/after).
    - Should not mutate the main context (ctx); may write to mwctx (shared among all middleware in the chain run).
    - Middleware is aware of its queue position and index (readonly attributes: position, index).
    - Can be used for debugging, tracing, or performance measurement.
    - Middleware should not raise exceptions or alter control flow; it only observes and records.
    """
    link: Optional[Link] = None  # Set by the chain/link when attached (readonly)
    position: Optional[str] = None  # 'chain-before', 'link-before', 'link-after', 'chain-after'
    index: Optional[int] = None  # Order in the middleware queue

    async def before(self, link: Link, ctx: Context, mwctx: Context) -> None:
        """
        Called before a Link is executed.

        Args:
            link: The Link about to be executed (readonly reference).
            ctx: The current Context (read-only).
            mwctx: The middleware context (shared, writable by all middleware in this chain run).
        """
        ...

    async def after(self, link: Link, ctx: Context, result: Context, mwctx: Context) -> None:
        """
        Called after a Link is executed.

        Args:
            link: The Link that was executed (readonly reference).
            ctx: The Context before execution (read-only).
            result: The Context after execution (read-only).
            mwctx: The middleware context (shared, writable by all middleware in this chain run).
        """
        ...

def is_middleware(obj) -> bool:
    """
    Check if an object conforms to the Middleware protocol.

    Args:
        obj: Any object to check.
    Returns:
        bool: True if the object has before and after methods, False otherwise.
    """
    return hasattr(obj, "before") and hasattr(obj, "after")

class Logging:
    """
    Logging middleware for ModuLink Next.

    - Logs link execution to the console before and after each link.
    - Useful for debugging and tracing chain execution.
    - Is link-aware: knows which link it is running before/after.
    - Knows its position and index in the middleware queue.
    - Writes to mwctx for cross-cutting logging if needed.
    - Should not raise exceptions or alter control flow.
    """
    link: Optional[Link] = None
    position: Optional[str] = None
    index: Optional[int] = None

    async def before(self, link: Link, ctx: Context, mwctx: Context) -> None:
        """
        Log before a link is executed.
        """
        print(f"[Logging] Before: {getattr(link, '__name__', str(link))} ctx={ctx} position={self.position} index={self.index}")

    async def after(self, link: Link, ctx: Context, result: Context, mwctx: Context) -> None:
        """
        Log after a link is executed.
        """
        print(f"[Logging] After: {getattr(link, '__name__', str(link))} result={result} position={self.position} index={self.index}")

class Timing:
    """
    Timing middleware for ModuLink Next.

    - Measures and logs execution time for each link.
    - Useful for performance profiling and optimization.
    - Is link-aware: knows which link it is running before/after.
    - Knows its position and index in the middleware queue.
    - Writes to mwctx for cross-cutting timing if needed.
    - Should not raise exceptions or alter control flow.
    """
    import time
    link: Optional[Link] = None
    position: Optional[str] = None
    index: Optional[int] = None

    async def before(self, link: Link, ctx: Context, mwctx: Context) -> None:
        """
        Record the start time before a link is executed.
        """
        start = self.time.perf_counter()
        mwctx["_timing_start"] = start

    async def after(self, link: Link, ctx: Context, result: Context, mwctx: Context) -> None:
        """
        Log the elapsed time after a link is executed.
        """
        start = mwctx.pop("_timing_start", None)
        end = self.time.perf_counter()
        if start is not None:
            elapsed = end - start
            print(f"[Timing] {getattr(link, '__name__', str(link))} took {elapsed:.6f}s position={self.position} index={self.index}")
