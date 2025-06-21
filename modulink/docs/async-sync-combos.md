# ModuLink Next: Async, Await, and Sync Combinations

> **Quick Reference:**
>
> | Pattern                | Description                                                      |
> |------------------------|------------------------------------------------------------------|
> | Awaited Async          | Python's default: async def, always awaited by the chain         |
> | Sync                   | Regular def, runs synchronously                                  |
> | Mixed                  | Any order: ModuLink Next handles each link appropriately         |
> | **Fire-and-Forget**    | Launches background task, chain does NOT await                   |
>
> - **Awaited async**: The chain waits for the async link to finish (Python's default async/await).
> - **Fire-and-forget**: The chain launches a background task and continues immediately, like JS's Promise.then().

This guide explores how ModuLink Next chains handle combinations of awaited async, fire-and-forget async, and normal sync functions as links. It demonstrates patterns, caveats, and best practices for mixing these paradigms in your workflows.

---

## 1. Awaited Async Links (Python Default)

A true async link in Python is defined with `async def` and is always awaited by ModuLink Next. This means the chain will wait for the link to finish before moving to the next step.

```python
async def async_link(ctx):
    ctx["async"] = True
    return ctx

chain = Chain(async_link)
result = await chain.run({})
print(result)  # {'async': True}
```

---

## 2. Fire-and-Forget (Detached Async)

If you want a link to behave like JavaScript's "true async" (fire-and-forget, not awaited), you can launch a background task with `asyncio.create_task`. The chain will not wait for this task to finish.

```python
import asyncio

async def background_job(ctx):
    await asyncio.sleep(1)
    print("Background job done!", ctx)

async def fire_and_forget_link(ctx):
    asyncio.create_task(background_job(ctx.copy()))
    ctx["launched"] = True
    return ctx

chain = Chain(fire_and_forget_link)
result = await chain.run({"user": "alice"})
print(result)  # {'user': 'alice', 'launched': True}
# The background_job will print after ~1s, even though the chain is done.
```

---

## 3. Sync and Mixed Links

You can freely mix async and sync (`def`) links in the same chain. ModuLink Next will handle each appropriately.

```python
def sync_link(ctx):
    ctx["sync"] = True
    return ctx

async def async_step(ctx):
    ctx["async"] = True
    return ctx

chain = Chain(sync_link, async_step, sync_link)
result = await chain.run({})
print(result)  # {'sync': True, 'async': True}
```

---

## Best Practices

- Prefer `async def` for links that do IO or await other async code.
- Use sync links for pure computation or simple context mutation.
- Use fire-and-forget only when you do not need the result in the chain.
- You can mix sync and async links in any order.

---

For more, see the main README and recipes.
