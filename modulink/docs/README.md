**ModuLink MVP Documentation Draft**

A minimal, composable, and observable async function orchestration ecosystem. Concepts build progressively from simple examples to advanced patterns.

---

## 1. Quick Start Example

```python
from modulink import Chain, Context
from modulink.middleware import Logging, Timing

async def validate_email(ctx: Context) -> Context:
    if "email" not in ctx:
        ctx["error"] = "Missing email"
    return ctx

async def send_welcome(ctx: Context) -> Context:
    print(f"Welcome sent to {ctx['email']}")
    return ctx

# Build a Chain with two Links (auto-named and wired)
signup = Chain(validate_email, send_welcome)

# Attach middleware for observability
signup.use(Logging())
signup.use(Timing())

# Execute with context
result = await signup.run({"email": "alice@example.com"})

# Inspect structure
print(signup.inspect())
# {
#   "nodes": ["validate_email", "send_welcome"],
#   "edges": [
#     {"source":"validate_email","target":"send_welcome","condition":true}
#   ]
# }
```

*Start simple: define pure async functions, chain them, add middleware, and run.*

---

## 2. Core Concepts

**Recent Implementation Updates:**

- `Chain.run` now executes links sequentially, supports middleware hooks, and handles exceptions by storing them in the context.
- Hybrid error handling: when a link raises an exception, the chain checks for connected error/timeout handlers and routes execution accordingly.
- Example middleware (`Logging`, `Timing`) are implemented and can be attached to a chain.
- Dynamic docstrings for `Chain` and `Listener` instances reflect current configuration and update on mutation.
- VSCode extension roadmap and TODOs added for future developer tooling.

---

### 2.1. Link

A **Link** is a pure unit of work:

```python
from typing import Protocol, Callable, Awaitable
from modulink import Context

class Link(Protocol):
    name: str    # inferred from function or class name
    __call__: Callable[[Context], Awaitable[Context]]
```

- **Automatic Naming** from `func.__name__` or class name.
- **Docstrings** preserved in `link.__doc__`.
- **Single Responsibility:** transforms input `Context` to output `Context`.
- **Pure:** no side-effects, no branching, no error handling.

### 2.2. Chain

A **Chain** is a named graph of Links:

```python
from modulink import Chain, Context

# Auto-named by assignment: 'signup'
signup: Chain = Chain(validate_email, send_welcome)
```

- **Auto-wiring:** adjacent Links connected with `condition=True`.
- **API:**
  - `add_link(link)`
  - `connect(source, target, condition)`
  - `use(middleware)`
  - `run(ctx) -> Context`
  - `inspect() -> dict`

### 2.3. Condition & Connection

Define edges explicitly for branching:

```python
from typing import Union, Callable
from modulink import Context

ConditionExpr = Union[bool, Callable[[Context], bool]]
```

- `True` ⇒ always take edge
- `False` ⇒ never
- `lambda ctx: bool` ⇒ custom

```python
signup.connect(
  source    = validate_email,
  target    = handle_error,
  condition = lambda ctx: "error" in ctx
)
```

### 2.4. Middleware

```python
class Middleware(Protocol):
    async def before(self, link: Link, ctx: Context) -> None: ...
    async def after(self,  link: Link, ctx: Context, result: Context) -> None: ...
```

- **Read-only:** inspect `Context`, log/metrics, no mutation
- Attach via `.use()`

---

## 3. Hybrid Error Handling

| Layer       | Handles Errors? | Mechanism                              |
| ----------- | --------------- | -------------------------------------- |
| **Link**    | Optional        | `try/except` → `ctx['error']`          |
| **Chain**   | Always          | wraps Link calls → `ctx['exception']`  |
| **Connect** | Routing         | `condition=lambda ctx: 'error' in ctx` |

*Expected errors in Links, unexpected caught by Chain, all routed via ****\`\`**** predicates.*

---

## 4. Integration with External Services

Turn external calls into Links:

- **HTTP** via `httpx`
- **gRPC** via `grpc.aio`
- **Message Queues** via `aiokafka`, `aio-pika`
- **Databases** via `asyncpg`
- **WebSockets** via `websockets`

*Each integration is just an async function Link in your Chain.*

---

## 5. Listeners (Triggers)

First-class server bindings that implement `async __call__(self, ctx: Context) -> Context`:

### 5.1. HTTP Listener (FastAPI)

```python
from modulink import Chain
from modulink.listeners.http import HttpListener

signup = Chain(validate_email, send_welcome)
signup_listener = HttpListener(
  chain   = signup,
  path    = "/signup",
  methods = ["POST"]
)
signup_listener.serve(port=8000)
```

### 5.2. TCP Listener

```python
from modulink.listeners.tcp import TcpListener

echo_listener = TcpListener(
  chain = echo_chain,
  port  = 9000
)
```

*Unit-testable by direct call; extensible by subclassing ****\`\`****.*

---

## 6. Best Practices

### 6.1. File Organization

```text
project/
├── app.py         # Links, Chains, Listeners (business logic)
├── server.py      # Bootstraps FastAPI/TCP server, mounts listeners
├── listeners.py   # Custom listeners (BaseListener subclasses)
├── links.py       # Pure Link definitions
└── chains.py      # Chain compositions (optional)
```

### 6.2. Chain Docstring Injection

The `Chain` class automatically keeps its docstring up to date with the current structure (links, connections, middleware) using its internal `_update_doc()` method. This method is called whenever the chain is mutated (adding links, connections, or middleware), so IDE hovers and documentation always reflect the latest state.

Example:

```python
from modulink import Chain

def a(ctx): "A link"; return ctx
def b(ctx): "B link"; return ctx

chain = Chain(a, b)
print(chain.__doc__)
# Shows links, connections, and middleware

chain.add_link(lambda ctx: ctx)
print(chain.__doc__)
# Docstring updates automatically
```

*No monkeypatching is needed; docstrings are always current thanks to `_update_doc()`.*

---

## 7. Advanced Connection Examples

Showcasing verbose, multi-branch connection setups for complex flows.

```python
from modulink import Chain, Context

async def validate_email(ctx: Context) -> Context:
    """Ensure 'email' exists; simulate timeout or validation error."""
    # simulate conditions
    if ctx.get("simulate_timeout"):
        ctx["timeout"] = True
        return ctx
    if "email" not in ctx:
        ctx["error"] = "Missing email"
    return ctx

async def send_welcome(ctx: Context) -> Context:
    """Send welcome email if validation passed."""
    print(f"Welcome sent to {ctx['email']}")
    return ctx

async def handle_error(ctx: Context) -> Context:
    """Handle validation errors."""
    print("Validation error:", ctx.get("error"))
    return ctx

async def handle_timeout(ctx: Context) -> Context:
    """Handle timeouts separately."""
    print("Operation timed out for user", ctx.get("user_id"))
    return ctx

# Compose chain with primary and fallback branches
signup = Chain(validate_email, send_welcome)

# Register additional Links
signup.add_link(handle_error)
signup.add_link(handle_timeout)

# Explicit branching with predicates
signup.connect(
    source    = validate_email,
    target    = handle_timeout,
    condition = lambda ctx: ctx.get("timeout", False)
)
signup.connect(
    source    = validate_email,
    target    = handle_error,
    condition = lambda ctx: "error" in ctx
)
# Default path when no error/timeout
signup.connect(
    source    = validate_email,
    target    = send_welcome,
    condition = lambda ctx: not ("error" in ctx or ctx.get("timeout", False))
)

# Now, run with different contexts:
await signup.run({"user_id": 123, "simulate_timeout": True})
# routes to handle_timeout

await signup.run({})
# routes to handle_error

await signup.run({"email": "alice@example.com"})
# routes to send_welcome
```

---

## 8. Example: Running an Exported (Static) Chain

# After exporting a chain to a static module (e.g., `exported_chain.py`), you can use it as a normal Python module.
# The chain is immutable and safe for production use.

# static_run_example.py
import asyncio
from exported_chain import chain  # 'chain' is the exported, static Chain object

async def main():
    ctx = {}
    result = await chain.run(ctx)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())

# This script will execute the static chain just like the original, but with all mutation methods disabled.
# The exported file is pure Python and can be versioned, audited, and deployed as a static artifact.
```
