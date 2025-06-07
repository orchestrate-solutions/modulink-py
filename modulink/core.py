"""
ModuLink Core Implementation for Python

This is the simplified implementation using the ModuLink type system.
It replaces the over-engineered class-based approach with simple function types.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .types import (
    Ctx, Link, Chain, Trigger, Middleware,
    LinkFunction, ChainFunction, MiddlewareFunction,
    create_context, create_http_context, create_cron_context,
    create_cli_context, create_message_context, get_current_timestamp
)

logger = logging.getLogger(__name__)


class ModulinkOptions:
    """Configuration options for ModuLink."""
    
    def __init__(
        self,
        environment: str = "development",
        enable_logging: bool = True
    ):
        self.environment = environment
        self.enable_logging = enable_logging


def create_modulink(app=None, options: Optional[ModulinkOptions] = None):
    """
    Factory function to create a ModuLink instance with universal types.
    
    Args:
        app: Optional web framework app (FastAPI, Flask, etc.)
        options: Configuration options
        
    Returns:
        ModuLink instance with universal types API
    """
    if options is None:
        options = ModulinkOptions()
    
    # Internal state
    global_middleware: List[MiddlewareFunction] = []
    link_middleware: Dict[str, Dict[str, List[MiddlewareFunction]]] = {}
    chain_middleware: Dict[str, Dict[str, List[MiddlewareFunction]]] = {}
    registered_chains: Dict[str, Chain] = {}
    registered_links: Dict[str, Link] = {}
    cron_tasks: List[Any] = []
    
    def log(message: str) -> None:
        """Internal logging."""
        if options.enable_logging:
            print(f"[ModuLink] {message}")
    
    async def _ensure_async_link(link: Link) -> ChainFunction:
        """Convert a link to an async function."""
        async def async_wrapper(ctx: Ctx) -> Ctx:
            if asyncio.iscoroutinefunction(link):
                return await link(ctx)
            else:
                return link(ctx)
        return async_wrapper
    
    def create_chain(*links: Link) -> Chain:
        """
        Create a chain by composing links with middleware.
        Global middleware is applied automatically.
        """
        async def chain_impl(ctx: Ctx) -> Ctx:
            result = ctx.copy()
            
            # Apply global middleware first
            for mw in global_middleware:
                result = await mw(result)
                if result.get("error"):
                    break
            
            # Execute links in sequence
            for i, link in enumerate(links):
                if result.get("error"):
                    break  # Stop on error
                
                link_name = f"link_{i}"
                wrapped_link = apply_link_middleware(link_name, link)
                result = await wrapped_link(result)
            
            return result
        
        return chain_impl
    
    def create_named_chain(name: str, *links: Link) -> Chain:
        """Create a named chain with middleware support."""
        chain = create_chain(*links)
        return apply_chain_middleware(name, chain)
    
    async def apply_link_middleware(link_name: str, link: Link) -> ChainFunction:
        """Apply middleware to a specific link."""
        link_mw = link_middleware.get(link_name)
        if not link_mw or (not link_mw.get("before") and not link_mw.get("after")):
            return await _ensure_async_link(link)
        
        async def wrapped_link(ctx: Ctx) -> Ctx:
            result = ctx.copy()
            
            # Apply before middleware
            for mw in link_mw.get("before", []):
                result = await mw(result)
            
            # Execute the actual link
            async_link = await _ensure_async_link(link)
            result = await async_link(result)
            
            # Apply after middleware
            for mw in link_mw.get("after", []):
                result = await mw(result)
            
            return result
        
        return wrapped_link
    
    async def apply_chain_middleware(chain_name: str, chain: Chain) -> Chain:
        """Apply middleware to a chain."""
        chain_mw = chain_middleware.get(chain_name)
        
        async def wrapped_chain(ctx: Ctx) -> Ctx:
            result = ctx.copy()
            
            # Apply chain-specific before middleware
            # Note: Global middleware is already applied in create_chain
            if chain_mw:
                for mw in chain_mw.get("before", []):
                    result = await mw(result)
            
            # Execute the actual chain
            result = await chain(result)
            
            # Apply chain-specific after middleware
            if chain_mw:
                for mw in chain_mw.get("after", []):
                    result = await mw(result)
            
            return result
        
        return wrapped_chain
    
    # HTTP Trigger factory
    def http_trigger(path: str, methods: List[str]) -> Trigger:
        async def trigger_impl(chain: Chain, initial_ctx: Optional[Ctx] = None) -> Ctx:
            if app is None:
                log("No web app provided. HTTP triggers will not work.")
                return {"error": Exception("No web app available")}
            
            # Apply global middleware to the chain
            wrapped_chain = await apply_chain_middleware("http", chain)
            
            # For FastAPI
            if hasattr(app, 'add_api_route'):
                async def fastapi_handler(request):
                    try:
                        # Get request body if it exists
                        body = {}
                        if hasattr(request, 'json'):
                            try:
                                body = await request.json()
                            except:
                                body = {}
                        
                        ctx = create_http_context(
                            request=request,
                            method=request.method,
                            path=request.url.path,
                            query=dict(request.query_params),
                            body=body,
                            headers=dict(request.headers),
                            **(initial_ctx or {})
                        )
                        
                        result = await wrapped_chain(ctx)
                        
                        if result.get("error"):
                            return {"error": str(result["error"])}
                        else:
                            # Remove internal properties before sending response
                            response_data = {k: v for k, v in result.items() 
                                           if k not in ["req", "res"]}
                            return response_data
                    
                    except Exception as error:
                        return {"error": str(error)}
                
                for method in methods:
                    app.add_api_route(path, fastapi_handler, methods=[method])
            
            log(f"HTTP trigger registered: {', '.join(methods)} {path}")
            return {"success": True}
        
        return trigger_impl
    
    # Cron Trigger factory
    def cron_trigger(schedule: str) -> Trigger:
        async def trigger_impl(chain: Chain, initial_ctx: Optional[Ctx] = None) -> Ctx:
            wrapped_chain = await apply_chain_middleware("cron", chain)
            
            # Simplified cron implementation
            # In production, you'd use a proper cron library like APScheduler
            async def execute_job():
                try:
                    ctx = create_cron_context(
                        schedule=schedule,
                        **(initial_ctx or {})
                    )
                    await wrapped_chain(ctx)
                except Exception as error:
                    log(f"Cron job error: {error}")
            
            task = {"schedule": schedule, "execute": execute_job}
            cron_tasks.append(task)
            
            log(f"Cron trigger registered: {schedule}")
            return {"success": True, "execute": execute_job}
        
        return trigger_impl
    
    # Message Trigger factory
    def message_trigger(topic: str) -> Trigger:
        async def trigger_impl(chain: Chain, initial_ctx: Optional[Ctx] = None) -> Ctx:
            wrapped_chain = await apply_chain_middleware("message", chain)
            
            # Simulate message consumer setup
            async def message_handler(message: Any):
                try:
                    ctx = create_message_context(
                        topic=topic,
                        message=message,
                        **(initial_ctx or {})
                    )
                    await wrapped_chain(ctx)
                except Exception as error:
                    log(f"Message handler error: {error}")
            
            log(f"Message trigger registered: {topic}")
            return {"success": True, "handler": message_handler}
        
        return trigger_impl
    
    # CLI Trigger factory
    def cli_trigger(command: str) -> Trigger:
        async def trigger_impl(chain: Chain, initial_ctx: Optional[Ctx] = None) -> Ctx:
            wrapped_chain = await apply_chain_middleware("cli", chain)
            
            async def command_handler(args: List[str]):
                try:
                    ctx = create_cli_context(
                        command=command,
                        args=args,
                        **(initial_ctx or {})
                    )
                    return await wrapped_chain(ctx)
                except Exception as error:
                    log(f"CLI command error: {error}")
                    raise error
            
            log(f"CLI trigger registered: {command}")
            return {"success": True, "handler": command_handler}
        
        return trigger_impl
    
    # Middleware interface
    class MiddlewareInterface:
        def global_middleware(self, mw: MiddlewareFunction) -> None:
            """Register global middleware (applied to all chains)."""
            global_middleware.append(mw)
            log("Global middleware registered")
        
        def on_link(self, link_name: str):
            """Get link-specific middleware interface."""
            if link_name not in link_middleware:
                link_middleware[link_name] = {"before": [], "after": []}
            
            class LinkMiddlewareInterface:
                def on_input(self, mw: MiddlewareFunction) -> None:
                    link_middleware[link_name]["before"].append(mw)
                    log(f"Input middleware registered for link: {link_name}")
                
                def on_output(self, mw: MiddlewareFunction) -> None:
                    link_middleware[link_name]["after"].append(mw)
                    log(f"Output middleware registered for link: {link_name}")
            
            return LinkMiddlewareInterface()
        
        def on_chain(self, chain_name: str):
            """Get chain-specific middleware interface."""
            if chain_name not in chain_middleware:
                chain_middleware[chain_name] = {"before": [], "after": []}
            
            class ChainMiddlewareInterface:
                def on_input(self, mw: MiddlewareFunction) -> None:
                    chain_middleware[chain_name]["before"].append(mw)
                    log(f"Input middleware registered for chain: {chain_name}")
                
                def on_output(self, mw: MiddlewareFunction) -> None:
                    chain_middleware[chain_name]["after"].append(mw)
                    log(f"Output middleware registered for chain: {chain_name}")
            
            return ChainMiddlewareInterface()
    
    # Convenience methods
    class ConvenienceMethods:
        async def http(self, path: str, methods: List[str], *links: Link) -> Ctx:
            """Convenience method for HTTP endpoints."""
            chain = await create_chain(*links)
            trigger = http_trigger(path, methods)
            return await trigger(chain)
        
        async def cron(self, schedule: str, *links: Link) -> Ctx:
            """Convenience method for cron jobs."""
            chain = await create_chain(*links)
            trigger = cron_trigger(schedule)
            return await trigger(chain)
        
        async def message(self, topic: str, *links: Link) -> Ctx:
            """Convenience method for message handlers."""
            chain = await create_chain(*links)
            trigger = message_trigger(topic)
            return await trigger(chain)
        
        async def cli(self, command: str, *links: Link) -> Ctx:
            """Convenience method for CLI commands."""
            chain = await create_chain(*links)
            trigger = cli_trigger(command)
            return await trigger(chain)
    
    # Public API
    use = MiddlewareInterface()
    when = ConvenienceMethods()
    
    triggers = {
        "http": http_trigger,
        "cron": cron_trigger,
        "message": message_trigger,
        "cli": cli_trigger
    }
    
    def register_chain(name: str, chain: Chain) -> None:
        """Register a named chain."""
        registered_chains[name] = chain
        log(f"Chain registered: {name}")
    
    def register_link(name: str, link: Link) -> Link:
        """Register a named link for middleware targeting."""
        registered_links[name] = link
        log(f"Link registered: {name}")
        return link
    
    def get_chain(name: str) -> Optional[Chain]:
        """Get a registered chain by name."""
        return registered_chains.get(name)
    
    def cleanup() -> None:
        """Cleanup resources."""
        cron_tasks.clear()
        log("Cleanup completed")
    
    # Create the ModuLink instance
    class ModuLinkInstance:
        def __init__(self):
            self.create_chain = create_chain
            self.create_named_chain = create_named_chain
            self.apply_link_middleware = apply_link_middleware
            self.apply_chain_middleware = apply_chain_middleware
            self.use = use
            self.when = when
            self.triggers = triggers
            self.register_chain = register_chain
            self.register_link = register_link
            self.get_chain = get_chain
            self.cleanup = cleanup
            self.environment = options.environment
            self.enable_logging = options.enable_logging
    
    return ModuLinkInstance()


# Type for the ModuLink instance created by the factory
Modulink = Any  # Would be the return type of create_modulink
