"""
Listener stubs for ModuLink Next.

Defines base classes for HTTP and TCP listeners.
Listeners are entry points for external events (HTTP, TCP, etc.) to trigger chains.
See README.md section 5 for details.
"""

from typing import Any
from .context import Context
from .link import Link

class BaseListener:
    """
    BaseListener for ModuLink Next.

    - Abstract base class for all listeners (triggers).
    - Implements async __call__(self, ctx: Context) -> Context for event handling.
    - Provides dynamic docstring updates with configuration details.
    - Extend this class to implement custom listeners.
    """
    def __init__(self):
        """
        Initialize the listener and update its docstring with configuration.
        """
        self._update_doc()

    def _update_doc(self):
        """
        Dynamically update the listener's docstring to include configuration details.
        """
        doc = (self.__class__.__doc__ or "") + "\n\n"
        doc += f"Config: {getattr(self, '_config', {})}"
        self.__doc__ = doc

    async def __call__(self, ctx: Context) -> Context:
        """
        Handle an incoming event by processing the context.
        Default implementation echoes the context and marks it as handled.
        Override in subclasses for custom behavior.
        """
        ctx["listener_called"] = True
        return ctx

class HttpListener(BaseListener):
    """
    HTTP Listener for FastAPI integration.

    - Binds a chain to an HTTP endpoint and methods.
    - Use .serve(port=...) to start the HTTP server (stub implementation).
    - Designed for easy integration with web frameworks.
    """
    def __init__(self, chain: Any, path: str, methods: list):
        """
        Initialize an HTTP listener with a chain, endpoint path, and allowed methods.
        """
        self._config = {"chain": chain, "path": path, "methods": methods}
        super()._update_doc()

    def serve(self, port: int = 8000):
        """
        Start the HTTP server (stub implementation).
        Prints server details for demonstration purposes.
        """
        print(f"Serving HTTP on port {port} at path {self._config['path']} with methods {self._config['methods']}")

class TcpListener(BaseListener):
    """
    TCP Listener for raw socket integration.

    - Binds a chain to a TCP port for low-level event handling.
    - Use .serve() to start the TCP server (stub implementation).
    - Designed for custom network integrations.
    """
    def __init__(self, chain: Any, port: int):
        """
        Initialize a TCP listener with a chain and port number.
        """
        self._config = {"chain": chain, "port": port}
        super()._update_doc()

    def serve(self):
        """
        Start the TCP server (stub implementation).
        Prints server details for demonstration purposes.
        """
        print(f"Serving TCP on port {self._config['port']}")
