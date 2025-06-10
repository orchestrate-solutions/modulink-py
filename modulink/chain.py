"""
ModuLink Chain Function

The core driving force of ModuLink - chain composition with full middleware support.
This is where the real power of ModuLink comes alive through simple, composable patterns.
"""

import asyncio
from typing import Any, Dict, List, Union

from .types import ChainFunction, Ctx, Link, MiddlewareFunction, Status


class ChainMiddleware:
    """Simple middleware system - just before/after every link!"""

    def __init__(self):
        self.before_each_link: List[MiddlewareFunction] = []
        self.after_each_link: List[MiddlewareFunction] = []

    def before(
        self, mw: Union[MiddlewareFunction, List[MiddlewareFunction]]
    ) -> "ChainMiddleware":
        """Add middleware to run before each link."""
        if isinstance(mw, list):
            self.before_each_link.extend(mw)
        else:
            self.before_each_link.append(mw)
        return self

    def after(
        self, mw: Union[MiddlewareFunction, List[MiddlewareFunction]]
    ) -> "ChainMiddleware":
        """Add middleware to run after each link."""
        if isinstance(mw, list):
            self.after_each_link.extend(mw)
        else:
            self.after_each_link.append(mw)
        return self


class ChainInstance:
    """A chain instance with simple middleware support - the heart of ModuLink!"""

    def __init__(self, *links: Link):
        self.links: List[Link] = list(links)
        self.use = ChainMiddleware()

    async def _ensure_async_link(self, link: Link) -> ChainFunction:
        """Convert a link to async function for uniform execution."""

        async def async_wrapper(ctx: Ctx) -> Ctx:
            if asyncio.iscoroutinefunction(link):
                return await link(ctx)
            else:
                # For sync functions, call them directly and return the result
                return link(ctx)  # type: ignore

        return async_wrapper

    async def __call__(self, ctx: Ctx) -> Ctx:
        """Execute the chain with middleware support."""
        result = ctx.copy()

        # Execute each link with its middleware
        for link in self.links:
            # Stop execution if there's an error
            if result.get("error"):
                break

            # Apply before middleware
            for middleware in self.use.before_each_link:
                if result.get("error"):
                    break
                try:
                    if asyncio.iscoroutinefunction(middleware):
                        result = await middleware(result)
                    else:
                        result = middleware(result)  # type: ignore
                except Exception as e:
                    result = {**result, "error": e}
                    break

            # Execute the link if no errors from middleware
            if not result.get("error"):
                try:
                    async_link = await self._ensure_async_link(link)
                    result = await async_link(result)
                except Exception as e:
                    result = {**result, "error": e}

            # Apply after middleware (only if no errors)
            if not result.get("error"):
                for middleware in self.use.after_each_link:
                    try:
                        if asyncio.iscoroutinefunction(middleware):
                            result = await middleware(result)
                        else:
                            result = middleware(result)  # type: ignore
                    except Exception as e:
                        result = {**result, "error": e}
                        break

        return result

    def cleanup(self) -> Dict[str, Any]:
        """Clean up middleware registrations."""
        try:
            self.use.before_each_link.clear()
            self.use.after_each_link.clear()
            return {
                "status": Status.SUCCESS,
                "message": "Chain cleanup completed successfully",
            }
        except Exception as error:
            return {
                "status": Status.FAILED,
                "message": "Chain cleanup failed",
                "error": str(error),
            }


def chain(*links: Link) -> ChainInstance:
    """Create a chain instance from links. Single link = 1-dimensional chain."""
    return ChainInstance(*links)
