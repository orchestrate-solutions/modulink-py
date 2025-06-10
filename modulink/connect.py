"""
modulink.connect - Python helpers for connecting ModuLink chains to HTTP, cron, and CLI.

These are internal helper functions used by the ModuLink instance's connect method.
Connection functionality is accessed through modulink.connect() rather than standalone functions.
"""

from datetime import datetime, timezone

from .types import ConnectionType

# Import these at module level for testability
try:
    from fastapi import Request
    from fastapi.responses import JSONResponse
except ImportError:
    JSONResponse = None  # type: ignore
    Request = None  # type: ignore

try:
    import click
except ImportError:
    click = None  # type: ignore


def _handle_http_connection(modulink, chain_fn, **kwargs):
    """Internal handler for HTTP connections."""
    required_params = ["app", "method", "path"]
    for param in required_params:
        if param not in kwargs:
            raise ValueError(f"HTTP connection requires '{param}' parameter")

    if JSONResponse is None or Request is None:
        raise ImportError(
            "FastAPI is required for HTTP connections. Install with: pip install fastapi"
        )

    async def handler(request):
        try:
            body = {}
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.json()
                except Exception:
                    body = {}
            ctx = modulink.create_context(
                trigger="http",
                method=request.method,
                path=request.url.path,
                query=dict(request.query_params),
                payload=body,
                headers=dict(request.headers),
                req=request,
            )
            result_ctx = await chain_fn(ctx)
            return JSONResponse({"success": True, "data": result_ctx})
        except Exception as err:
            return JSONResponse(
                {"success": False, "message": str(err)}, status_code=400
            )

    kwargs["app"].add_api_route(
        kwargs["path"], handler, methods=[kwargs["method"].upper()]
    )


def _handle_cron_connection(modulink, chain_fn, **kwargs):
    """Internal handler for cron connections."""
    required_params = ["scheduler", "cron_expression"]
    for param in required_params:
        if param not in kwargs:
            raise ValueError(f"Cron connection requires '{param}' parameter")

    def job():
        ctx = modulink.create_context(
            trigger="cron",
            schedule=kwargs["cron_expression"],
            scheduled_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            result = chain_fn(ctx)
            print(
                f"[CRON] ran {chain_fn.__name__} at {datetime.now(timezone.utc).isoformat()}"
            )
            print(f"[CRON] result: {result}")
        except Exception as err:
            print(f"[CRON][{chain_fn.__name__}] error: {err}")

    kwargs["scheduler"].add_job(
        job, "cron", **_parse_cron_expression(kwargs["cron_expression"])
    )


def _handle_cli_connection(modulink, chain_fn, **kwargs):
    """Internal handler for CLI connections."""
    required_params = ["cli_group", "command_name"]
    for param in required_params:
        if param not in kwargs:
            raise ValueError(f"CLI connection requires '{param}' parameter")

    if click is None:
        raise ImportError(
            "Click is required for CLI connections. Install with: pip install click"
        )

    @kwargs["cli_group"].command(kwargs["command_name"])
    @click.option("--filename", "-f", help="File to import")
    def command(filename):
        print(f"[CLI] Executing command '{kwargs['command_name']}'")
        ctx = modulink.create_context(
            trigger="cli",
            command=kwargs["command_name"],
            cli_args={"filename": filename},
            invoked_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            # Handle both sync and async chain functions
            import asyncio

            if asyncio.iscoroutinefunction(chain_fn):
                result = asyncio.run(chain_fn(ctx))
            else:
                result = chain_fn(ctx)
            print(f"[CLI] Command '{kwargs['command_name']}' completed successfully")
            print(f"[CLI] Result: {result}")
        except Exception as err:
            print(f"[CLI][{kwargs['command_name']}] error: {err}")
            exit(1)


def _handle_message_connection(modulink, chain_fn, **kwargs):
    """Internal handler for message connections."""
    required_params = ["topic"]
    for param in required_params:
        if param not in kwargs:
            raise ValueError(f"Message connection requires '{param}' parameter")

    async def message_handler(message):
        ctx = modulink.create_context(
            trigger="message",
            topic=kwargs["topic"],
            message=message,
            received_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            result = chain_fn(ctx)
            print(f"[MESSAGE] processed message on topic '{kwargs['topic']}'")
            print(f"[MESSAGE] result: {result}")
            return result
        except Exception as err:
            print(f"[MESSAGE][{kwargs['topic']}] error: {err}")
            raise err

    # Return the handler for integration with message systems
    return {"handler": message_handler, "topic": kwargs["topic"]}


def _parse_cron_expression(expr):
    """Parse a cron expression string into APScheduler cron parameters."""
    fields = expr.strip().split()
    keys = ["minute", "hour", "day", "month", "day_of_week"]
    return dict(zip(keys, fields))


# Connection handler registry
CONNECTION_HANDLERS = {
    ConnectionType.HTTP: _handle_http_connection,
    ConnectionType.CRON: _handle_cron_connection,
    ConnectionType.CLI: _handle_cli_connection,
    ConnectionType.MESSAGE: _handle_message_connection,
}
