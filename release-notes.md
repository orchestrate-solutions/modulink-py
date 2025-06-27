# ModuLink-Py v4.0.2

This release focuses on project cleanup and maintainability, removing experimental AI automation components that have been extracted to their own repository.

## What's Changed in v4.0.2

- **Project Cleanup**: Removed experimental AI release automation system that was successfully extracted to its own repository
- **Focus Restoration**: Project now contains only core ModuLink functionality for better maintainability  
- **Configuration Fix**: Corrected mypy python_version configuration in pyproject.toml
- **Clean Architecture**: Simplified project structure with clear separation of concerns

The AI release automation system has been moved to its own repository and is now a standalone project. This allows ModuLink-py to maintain its focus on core async function orchestration capabilities.

## Core ModuLink Features Remain

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
