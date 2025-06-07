import pytest
from modulink import connect

def test_connect_http_route_registers(monkeypatch):
    class App:
        def __init__(self):
            self.routes = []
        def add_api_route(self, path, handler, methods):
            self.routes.append((path, handler, methods))
    class Modulink:
        def create_context(self, **kwargs):
            return kwargs
    app = App()
    modulink = Modulink()
    async def chain_fn(ctx):
        return {"result": "ok", **ctx}
    connect.connect_http_route(app, modulink, "POST", "/test", chain_fn)
    assert app.routes, "Route should be registered"
    path, handler, methods = app.routes[0]
    assert path == "/test"
    assert "POST" in methods

def test_connect_cron_job_registers(monkeypatch):
    class Scheduler:
        def __init__(self):
            self.jobs = []
        def add_job(self, job, trigger, **kwargs):
            self.jobs.append((job, trigger, kwargs))
    class Modulink:
        def create_context(self, **kwargs):
            return kwargs
    scheduler = Scheduler()
    modulink = Modulink()
    def chain_fn(ctx):
        return {"ran": True}
    connect.connect_cron_job(scheduler, "* * * * *", modulink, chain_fn)
    assert scheduler.jobs, "Cron job should be registered"
    job, trigger, kwargs = scheduler.jobs[0]
    assert trigger == "cron"
    assert "minute" in kwargs

def test_connect_cli_command_registers(monkeypatch):
    commands = {}
    class CliGroup:
        def command(self, name):
            def decorator(fn):
                commands[name] = fn
                return fn
            return decorator
    class Modulink:
        def create_context(self, **kwargs):
            return kwargs
    cli_group = CliGroup()
    modulink = Modulink()
    def chain_fn(ctx):
        return {"cli": True}
    # Patch click.option to a no-op
    import sys
    sys.modules["click"] = type("click", (), {"option": lambda *a, **k: lambda f: f})()
    connect.connect_cli_command(cli_group, "import-data", modulink, chain_fn)
    assert "import-data" in commands

def test_connect_http_route_error(monkeypatch):
    class App:
        def add_api_route(self, path, handler, methods):
            self.handler = handler
    class Modulink:
        def create_context(self, **kwargs):
            return kwargs
    app = App()
    modulink = Modulink()
    async def chain_fn(ctx):
        raise ValueError("fail")
    connect.connect_http_route(app, modulink, "POST", "/fail", chain_fn)
    # Simulate FastAPI request
    class Request:
        method = "POST"
        url = type("url", (), {"path": "/fail"})
        async def json(self):
            return {}
        query_params = {}
        headers = {}
    import asyncio
    resp = asyncio.run(app.handler(Request()))
    assert resp.status_code == 400
    assert not resp.body is None
