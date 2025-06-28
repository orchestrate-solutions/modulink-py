# ModuLink-Py Import Migration Guide

## What Changed

ModuLink-py now supports clean, intuitive import paths while maintaining backward compatibility with existing code.

## New (Preferred) Import Pattern

```python
# Clean, direct imports (recommended)
from modulink import Chain, Context, Logging, Timing

async def validate_email(ctx: Context) -> Context:
    if "email" not in ctx:
        ctx["error"] = "Missing email"
    return ctx

async def send_welcome(ctx: Context) -> Context:
    print(f"Welcome sent to {ctx['email']}")
    return ctx

# Build and run chain
signup = Chain(validate_email, send_welcome)
signup.use(Logging())
signup.use(Timing())

result = await signup.run({"email": "alice@example.com"})
```

## Old (Deprecated) Import Pattern

```python
# Still works but deprecated
from modulink.src.chain import Chain
from modulink.src.context import Context
from modulink.src.middleware import Logging, Timing

# Same functionality, but imports are more verbose
```

## Migration Benefits

✅ **Cleaner imports**: `from modulink import Chain` instead of `from modulink.src.chain import Chain`  
✅ **Better IDE support**: Improved autocomplete and documentation  
✅ **Standard Python practices**: Follows conventional package structure  
✅ **No breaking changes**: Existing code continues to work  

## Migration Timeline

- **Now**: Both patterns work identically
- **Recommended**: Update new code to use clean imports
- **Existing code**: No immediate changes required
- **Future versions**: Deprecated imports will include warnings (but continue working)

## Examples

### Before (still works)
```python
from modulink.src.chain import Chain
from modulink.src.middleware import Logging
```

### After (recommended)
```python
from modulink import Chain, Logging
```

Both patterns provide identical functionality - choose what works best for your project's timeline.
