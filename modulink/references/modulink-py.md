# ModuLink Next Cheatsheet & Core Patterns

A concise reference for ModuLink Next's core patterns, with one clear example for each. For more, use the ModuLink CLI or see the full docs.

---

## 1. Context: Mutable & Immutable

```python
from modulink import Context
ctx = Context({"user": "alice", "count": 0})  # Mutable by default
ctx["count"] = 1  # Works
ctx_imm = ctx.asImmutable()  # Make immutable
# ctx_imm["count"] = 2  # Raises TypeError
print(ctx_imm.isImmutable())  # True
print(ctx.isMutable())        # True
ctx2 = ctx_imm.asMutable()    # Back to mutable
```

---

## 2. Link: Pure Async Step (returns new context)

```python
async def increment(ctx):
    ctx = ctx.asMutable()
    ctx["count"] += 1
    return ctx.asImmutable()
```

---

## 3. Chain: Compose & Run

```python
from modulink import Chain
chain = Chain(increment)
result = await chain.run(Context({"count": 0}))
```

---

## 4. Branching & Error Handling

```python
async def error_handler(ctx):
    ctx = ctx.asMutable()
    ctx["error_handled"] = True
    return ctx.asImmutable()
chain.connect(increment, error_handler, lambda ctx: ctx["count"] > 10)
```

---

## 5. Middleware: Observability

```python
from modulink.src.middleware import Logging
chain.use(Logging())
```

---

## 6. Custom Middleware

```python
class Audit:
    async def before(self, link, ctx): print("Before", link)
    async def after(self, link, ctx, result): print("After", link)
chain.use(Audit())
```

---

## 7. Listener: HTTP Example

```python
from modulink.src.listeners import HttpListener
listener = HttpListener(chain, "/api", ["POST"])
listener.serve(port=8080)
```

---

## 8. Chain Inspection

```python
print(chain.inspect())
print(chain.__doc__)
```

---

## 9. Parallel Chains

```python
import asyncio
results = await asyncio.gather(chain.run(Context({"count": 1})), chain.run(Context({"count": 2})))
```

---

## 10. CLI Usage

- Search docs: `modulink <topic>` (e.g., `modulink chain`, `modulink middleware.Logging`)
- Export cheatsheet: `modulink --cheatsheet`

---

**Best Practices:**
- Use `.asImmutable()` for safety in async/concurrent code.
- Use `.asMutable()` for batch updates, then freeze.
- Validate/sanitize all input at entry points.
- Never use `eval`/`exec` on untrusted data.
- Use trusted middleware and review logging.
- Use `chain.inspect()` and `chain.__doc__` for debugging.
- Test chains in isolation with different contexts.

For more, see the full docs or use the CLI.
