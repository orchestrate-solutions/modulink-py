# ModuLink-Py v4.0.1

This release of ModuLink-Py introduces a minimal, composable, and observable async function orchestration ecosystem.

## Quick Start

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
```

## Core Concepts

*   **Link**: A pure, single-responsibility async function.
*   **Chain**: A named graph of Links, automatically wired.
*   **Middleware**: Attach logging, timing, and other cross-cutting concerns.
*   **Listeners**: First-class server bindings for HTTP, TCP, and more.

See the [CHANGELOG.md](https://github.com/orchestrate-solutions/modulink-py/blob/main/CHANGELOG.md) for detailed changes.
