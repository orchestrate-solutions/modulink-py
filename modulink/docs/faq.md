# ModuLink Next FAQ (Validated)

Frequently Asked Questions about ModuLink Next, validated against the main README and codebase.

---

## What is ModuLink Next?
A minimal, composable, and observable async function orchestration ecosystem for Python. It lets you chain, branch, and observe async (and sync) functions with middleware and listeners. See the Quick Start in the README for a full example.

---

## How is ModuLink Next different from other workflow/orchestration tools?
- Pure Python, no DSL or YAML required.
- Async-first, but supports sync functions as links.
- Dynamic docstrings and inspectability: chains and listeners update their docstrings automatically to reflect their current structure.
- Middleware and listeners are first-class, composable, and easy to test.
- Minimal, composable, and designed for rapid prototyping and production use.

---

## Can I use synchronous functions as links?
Yes! Both `def` and `async def` functions can be used as links in a Chain. The system will handle both seamlessly.

---

## How do I handle errors in a chain?
- Use try/except in links to catch expected errors and set `ctx["error"]`.
- Use `chain.connect()` with conditions to route errors or timeouts to handlers (see README section 3 and 7 for advanced branching).
- Unexpected exceptions are caught and stored in `ctx["exception"]` by the chain, and can be routed using connections with conditions.

---

## How do I add middleware?
Call `chain.use(middleware_instance)`. Middleware must implement `before` and `after` async methods. Example middleware (`Logging`, `Timing`) are provided and can be attached to any chain.

---

## How do I inspect or document my chain?
- Use `chain.inspect()` for a dict view of the structure (links, connections, middleware).
- Use `print(chain.__doc__)` for a dynamic docstring that updates automatically as the chain is mutated.

---

## Can I mutate the chain after creation?
Yes! You can add links, middleware, and connections at any time. The docstring and inspect output will update automatically to reflect the current state.

---

## How do I run multiple chains in parallel?
Use `asyncio.gather()`:

```python
import asyncio
results = await asyncio.gather(chain1.run(ctx1), chain2.run(ctx2))
```

---

## How do I secure my listeners?
- Use HTTPS for HTTP listeners in production.
- Authenticate and validate all incoming requests.
- Restrict TCP listeners to trusted networks.
- See the security.md guide for more details.

---

## Where can I find more examples?
See [examples.md](./examples.md), [recipes.md](./recipes.md), and the main README for practical patterns and advanced usage.

---

## How do I contribute?
- Fork the repo, make changes, and submit a PR.
- See [CONTRIBUTING.md](./CONTRIBUTING.md) if available.
- Open issues for bugs, questions, or feature requests.

---

## Where do I get help?
- Check the [troubleshooting guide](./troubleshooting.md).
- Open an issue on GitHub.

---

## What is the best way to document and debug my chains?
- Add docstrings to all links and chains for best IDE and AI experience.
- Use `print(chain.__doc__)` and `chain.inspect()` to verify structure and connections.
- Use middleware for logging and timing to trace execution.

---

## Can I use ModuLink Next for sync-only code?
Yes, but the system is optimized for async. Sync functions are supported and can be mixed with async links in the same chain.

---

## How do I test my chains?
- Use pytest or your favorite test framework.
- Test chains in isolation with different context inputs.
- See `test_verbose.py` and `tests.py` for real test examples.

---

For more, see the main README and the linked documentation files.
