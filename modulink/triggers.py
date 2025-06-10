"""
ModuLink Standalone Triggers

Standalone trigger functions that can be used independently of the ModuLink core instance.
These triggers can be used with any chain function, including the standalon    async def trigger_impl(
        target_chai    async def trigger_impl(
        target_chain: Chain, initial_ctx: Optional[Ctx] = None
    ) -> Ctx:
        async def command_handler(args: List[str]):
            try:
                ctx = create_cli_context(
                    command=command, args=args, **(initial_ctx or {})
                )
                return await _ensure_async_call(target_chain, ctx) initial_ctx: Optional[Ctx] = None
    ) -> Ctx:
        async def message_handler(message: Any):
            try:
                ctx = create_message_context(
                    topic=topic, message=message, **(initial_ctx or {})
                )
                return await _ensure_async_call(target_chain, ctx)unction.
"""

import asyncio
from typing import Any, List, Optional

from .types import (
    Chain,
    ChainFunction,
    Ctx,
    Trigger,
    create_cli_context,
    create_cron_context,
    create_http_context,
    create_message_context,
)


async def _ensure_async_call(fn, *args, **kwargs):
    """Ensure a function call is async, handling both sync and async functions."""
    if asyncio.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)
    else:
        # For sync functions, check if they return a coroutine (like chain functions do)
        result = fn(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result


def http_trigger(path: str, methods: List[str], app=None) -> Trigger:
    """Create a standalone HTTP trigger for web application endpoints.

    This function creates a trigger that can integrate with web frameworks
    independently of the ModuLink core instance. It can be used with any
    chain function, including the standalone chain function.

    Args:
        path (str): The URL path for the HTTP endpoint.
        methods (List[str]): List of HTTP methods to accept.
        app (Any, optional): Web application instance (FastAPI, Flask, etc.).
                            If not provided, returns a handler that can be
                            integrated manually.

    Returns:
        Trigger: A function that accepts a ChainFunction and sets up HTTP handling.

    Example:
        >>> from modulink.triggers import http_trigger
        >>> from modulink.chain import chain
        >>>
        >>> my_chain = chain(auth_link, data_link)
        >>> trigger = http_trigger("/api/users", ["GET"], app=fastapi_app)
        >>> await trigger(my_chain, {"service": "users"})
    """

    async def trigger_impl(
        target_chain: Chain, initial_ctx: Optional[Ctx] = None
    ) -> Ctx:
        if app is None:
            # Return handler function for manual integration
            async def manual_handler(request_data):
                try:
                    ctx = create_http_context(
                        request=request_data.get("request"),
                        method=request_data.get("method", "GET"),
                        path=path,
                        query=request_data.get("query", {}),
                        body=request_data.get("body", {}),
                        headers=request_data.get("headers", {}),
                        **(initial_ctx or {}),
                    )
                    return await _ensure_async_call(target_chain, ctx)
                except Exception as error:
                    ctx = create_http_context(
                        request=request_data.get("request"),
                        method=request_data.get("method", "GET"),
                        path=path,
                        query=request_data.get("query", {}),
                        body=request_data.get("body", {}),
                        headers=request_data.get("headers", {}),
                        **(initial_ctx or {}),
                    )
                    ctx["error"] = str(error)
                    return ctx

            return {
                "success": True,
                "handler": manual_handler,
                "path": path,
                "methods": methods,
            }

        # For FastAPI integration
        if hasattr(app, "add_api_route"):

            async def fastapi_handler(request):
                try:
                    body = {}
                    if hasattr(request, "json"):
                        try:
                            body = await request.json()
                        except Exception:
                            body = {}

                    ctx = create_http_context(
                        request=request,
                        method=request.method,
                        path=request.url.path,
                        query=dict(request.query_params),
                        body=body,
                        headers=dict(request.headers),
                        **(initial_ctx or {}),
                    )

                    result = await _ensure_async_call(target_chain, ctx)

                    if result.get("error"):
                        return {"error": str(result["error"])}
                    else:
                        # Remove internal properties before sending response
                        response_data = {
                            k: v for k, v in result.items() if k not in ["req", "res"]
                        }
                        return response_data

                except Exception as error:
                    return {"error": str(error)}

            for method in methods:
                app.add_api_route(path, fastapi_handler, methods=[method])

        return {"success": True, "path": path, "methods": methods}

    return trigger_impl


def cron_trigger(schedule: str) -> Trigger:
    """Create a standalone cron trigger for scheduled task execution.

    This function creates a trigger for scheduled execution that can be used
    independently of the ModuLink core instance.

    Args:
        schedule (str): Cron expression defining when to execute the chain.

    Returns:
        Trigger: A function that accepts a ChainFunction and sets up scheduling.

    Example:
        >>> from modulink.triggers import cron_trigger
        >>> from modulink.chain import chain
        >>>
        >>> backup_chain = chain(backup_link, cleanup_link)
        >>> trigger = cron_trigger("0 2 * * *")  # 2 AM daily
        >>> result = await trigger(backup_chain, {"backup_type": "full"})
        >>> # Manual execution: await result["execute"]()
    """

    async def trigger_impl(
        target_chain: Chain, initial_ctx: Optional[Ctx] = None
    ) -> Ctx:
        async def execute_job():
            try:
                ctx = create_cron_context(schedule=schedule, **(initial_ctx or {}))
                return await _ensure_async_call(target_chain, ctx)
            except Exception as error:
                return {"error": str(error)}

        return {"success": True, "schedule": schedule, "execute": execute_job}

    return trigger_impl


def message_trigger(topic: str) -> Trigger:
    """Create a standalone message trigger for event-driven processing.

    This function creates a trigger for message/event handling that can be used
    independently of the ModuLink core instance.

    Args:
        topic (str): The topic, queue name, or channel to listen for messages.

    Returns:
        Trigger: A function that accepts a ChainFunction and sets up message handling.

    Example:
        >>> from modulink.triggers import message_trigger
        >>> from modulink.chain import chain
        >>>
        >>> user_chain = chain(validate_link, process_user_link)
        >>> trigger = message_trigger("user.created")
        >>> result = await trigger(user_chain, {"service": "users"})
        >>> # Use handler: await result["handler"](message_data)
    """

    async def trigger_impl(
        target_chain: Chain, initial_ctx: Optional[Ctx] = None
    ) -> Ctx:
        async def message_handler(message: Any):
            try:
                ctx = create_message_context(
                    topic=topic, message=message, **(initial_ctx or {})
                )
                return await _ensure_async_call(target_chain, ctx)
            except Exception as error:
                return {"error": str(error)}

        return {"success": True, "topic": topic, "handler": message_handler}

    return trigger_impl


def cli_trigger(command: str) -> Trigger:
    """Create a standalone CLI trigger for command-line application integration.

    This function creates a trigger for CLI command handling that can be used
    independently of the ModuLink core instance.

    Args:
        command (str): The command name or identifier for the CLI operation.

    Returns:
        Trigger: A function that accepts a ChainFunction and sets up CLI handling.

    Example:
        >>> from modulink.triggers import cli_trigger
        >>> from modulink.chain import chain
        >>>
        >>> deploy_chain = chain(validate_args_link, deploy_link)
        >>> trigger = cli_trigger("deploy")
        >>> result = await trigger(deploy_chain, {"environment": "production"})
        >>> # Use handler: await result["handler"](["--target", "production"])
    """

    async def trigger_impl(
        target_chain: Chain, initial_ctx: Optional[Ctx] = None
    ) -> Ctx:
        async def command_handler(args: List[str]):
            try:
                ctx = create_cli_context(
                    command=command, args=args, **(initial_ctx or {})
                )
                return await _ensure_async_call(target_chain, ctx)
            except Exception as error:
                return {"error": str(error)}

        return {"success": True, "command": command, "handler": command_handler}

    return trigger_impl


# Export dictionary for easy access
triggers = {
    "http": http_trigger,
    "cron": cron_trigger,
    "message": message_trigger,
    "cli": cli_trigger,
}

# Export functions individually for direct access
__all__ = ["http_trigger", "cron_trigger", "message_trigger", "cli_trigger", "triggers"]
