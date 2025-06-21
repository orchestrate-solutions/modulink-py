# ModuLink Next Recipes Cookbook (Verbose)

A collection of practical patterns and recipes for common tasks with ModuLink Next, with detailed comments explaining each step and concept.

---

## 1. Basic Chain

```python
from modulink.src.chain import Chain

# Define two async steps that mutate the context
# a sync or async function can be used as a link
async def step1(ctx):
    ctx["a"] = 1  # Set a value in the context
    return ctx

async def step2(ctx):
    ctx["b"] = ctx["a"] + 1  # Use previous value to compute a new one
    return ctx

# Compose the chain with the steps in order
chain = Chain(step1, step2)

# Run the chain with an empty context; result will have both 'a' and 'b'
result = await chain.run({})
```

---

## 2. Branching with Conditions

```python
# Define an error handler link
async def error_handler(ctx):
    ctx["handled"] = True  # Mark that error was handled
    return ctx

# Create a chain and add a conditional branch
chain = Chain(step1, step2)
# If 'error' is present in the context after step2, route to error_handler
chain.connect(step2, error_handler, lambda ctx: "error" in ctx)
```

---

## 3. Adding Middleware

```python
from modulink.src.middleware import Logging, Timing

# Attach built-in middleware for logging and timing
chain.use(Logging())  # Logs before/after each link
chain.use(Timing())   # Measures execution time for each link
```

---

## 4. Custom Middleware

```python
# Define your own middleware by implementing async before/after methods
class CustomMW:
    async def before(self, link, ctx):
        print("Before", link)  # Called before each link
    async def after(self, link, ctx, result):
        print("After", link)   # Called after each link

chain.use(CustomMW())
```

---

## 5. Integration: HTTP Request

```python
import httpx

# Use any async function as a link, including those that call external APIs
async def fetch(ctx):
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.example.com")
        ctx["data"] = resp.json()  # Store API response in context
    return ctx

chain = Chain(fetch)
```

---

## 6. Listener Setup

```python
from modulink.src.listeners import HttpListener

# Expose a chain as an HTTP endpoint using a listener
listener = HttpListener(chain, "/endpoint", ["POST"])
listener.serve(port=8080)  # Starts the HTTP server (stub in MVP)
```

---

## 7. Error Handling in Links

```python
# Handle expected errors inside links and set 'error' in context
async def safe_link(ctx):
    try:
        # risky operation
        pass
    except Exception as e:
        ctx["error"] = str(e)  # Store error message in context
    return ctx
```

---

## 8. Chain Inspection

```python
# Inspect the structure and docstring of your chain at any time
print(chain.inspect())    # Dict with links, connections, middleware
print(chain.__doc__)     # Human-readable summary, auto-updated
```

---

## 9. Dynamic Chain Mutation

```python
# Add new steps to a chain after creation; docstring and inspect update automatically
def new_step(ctx):
    ctx["x"] = 42
    return ctx
chain.add_link(new_step)
```

---

## 10. Parallel Chains (Pattern)

```python
# Run multiple chains concurrently using asyncio.gather
import asyncio

results = await asyncio.gather(chain1.run(ctx1), chain2.run(ctx2))
# Each result corresponds to the output of a chain
```

---

# For more, see [examples.md](./examples.md) and the main README.
