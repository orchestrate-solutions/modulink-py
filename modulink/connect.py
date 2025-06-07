"""
modulink.connect - Python helpers for connecting ModuLink chains to HTTP, cron, and CLI.

- connect_http_route(app, modulink, method, path, chain_fn)
- connect_cron_job(scheduler, cron_expression, modulink, chain_fn)
- connect_cli_command(cli_group, command_name, modulink, chain_fn)
"""

from datetime import datetime

def connect_http_route(app, modulink, method, path, chain_fn):
    """
    Registers a FastAPI route and connects it to a ModuLink chain.
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse

    async def handler(request: Request):
        try:
            body = {}
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.json()
                except Exception:
                    body = {}
            ctx = modulink.create_context(
                type="http",
                method=request.method,
                path=request.url.path,
                query=dict(request.query_params),
                payload=body,
                headers=dict(request.headers),
                req=request
            )
            result_ctx = await chain_fn(ctx)
            return JSONResponse({
                "success": True,
                "data": result_ctx
            })
        except Exception as err:
            return JSONResponse({"success": False, "message": str(err)}, status_code=400)

    app.add_api_route(path, handler, methods=[method.upper()])

def connect_cron_job(scheduler, cron_expression, modulink, chain_fn):
    """
    Schedules a cron job using APScheduler or similar.
    """
    def job():
        ctx = modulink.create_context(
            type="cron",
            schedule=cron_expression,
            scheduled_at=datetime.utcnow().isoformat()
        )
        try:
            result = chain_fn(ctx)
            print(f"[CRON] ran {chain_fn.__name__} at {datetime.utcnow().isoformat()}")
            print(f"[CRON] result: {result}")
        except Exception as err:
            print(f"[CRON][{chain_fn.__name__}] error: {err}")

    scheduler.add_job(job, "cron", **_parse_cron_expression(cron_expression))

def _parse_cron_expression(expr):
    """
    Parses a cron expression string into APScheduler cron params.
    """
    # This is a placeholder; in real use, parse expr properly.
    # For "* * * * *", return dict(minute="*", hour="*", day="*", month="*", day_of_week="*")
    fields = expr.strip().split()
    keys = ["minute", "hour", "day", "month", "day_of_week"]
    return dict(zip(keys, fields))

def connect_cli_command(cli_group, command_name, modulink, chain_fn):
    """
    Registers a CLI command using Click and connects it to a ModuLink chain.
    """
    import click

    @cli_group.command(command_name)
    @click.option("--filename", "-f", help="File to import")
    def command(filename):
        ctx = modulink.create_context(
            type="cli",
            command=command_name,
            cli_args={"filename": filename},
            invoked_at=datetime.utcnow().isoformat()
        )
        try:
            result = chain_fn(ctx)
            print(f"[CLI] Command '{command_name}' completed successfully")
            print(f"[CLI] Result: {result}")
        except Exception as err:
            print(f"[CLI][{command_name}] error: {err}")
            exit(1)
