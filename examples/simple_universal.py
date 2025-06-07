#!/usr/bin/env python3
"""
Simple Universal Type System Example for ModuLink Python

Demonstrates the simplified universal types: Ctx, Link, Chain, Trigger, and Middleware
This approach matches the TypeScript implementation structure.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Callable, Protocol, runtime_checkable

# Define the universal types directly here for the example
Ctx = Dict[str, Any]

@runtime_checkable
class Link(Protocol):
    """A link is a function that transforms a context."""
    async def __call__(self, ctx: Ctx) -> Ctx:
        ...

@runtime_checkable 
class Chain(Protocol):
    """A chain is a function that processes context through multiple links."""
    async def __call__(self, ctx: Ctx) -> Ctx:
        ...

@runtime_checkable
class Trigger(Protocol):
    """A trigger is a function that initiates chain execution."""
    async def __call__(self, chain: Chain, initial_ctx: Ctx = None) -> Ctx:
        ...

@runtime_checkable
class Middleware(Protocol):
    """Middleware is a function that transforms context."""
    async def __call__(self, ctx: Ctx) -> Ctx:
        ...

# Example context
example_ctx: Ctx = {
    "user_id": "123",
    "data": {"name": "John", "email": "john@example.com"},
    "timestamp": datetime.now().isoformat()
}

# Example Link - basic transformation function
async def validate_user(ctx: Ctx) -> Ctx:
    """Validate user from context."""
    print(f"🔍 Validating user: {ctx.get('user_id')}")
    
    if not ctx.get("user_id"):
        return {**ctx, "error": Exception("User ID is required")}
    
    return {**ctx, "validated": True}

# Example Link - data processing
async def process_user_data(ctx: Ctx) -> Ctx:
    """Process user data."""
    print(f"⚙️ Processing user data for: {ctx.get('data', {}).get('name')}")
    
    if ctx.get("error"):
        return ctx  # Skip processing if there's an error
    
    return {
        **ctx,
        "processed_data": {
            **ctx.get("data", {}),
            "processed": True,
            "processed_at": datetime.now().isoformat()
        }
    }

# Example Chain - composed transformation
async def user_processing_chain(ctx: Ctx) -> Ctx:
    """Process user through validation and data processing."""
    print("🔗 Starting user processing chain")
    
    result = await validate_user(ctx)
    if not result.get("error"):
        result = await process_user_data(result)
    
    print(f"✅ Chain completed: {'with errors' if result.get('error') else 'successfully'}")
    return result

# Example Middleware - adds logging and timing
async def logging_middleware(ctx: Ctx) -> Ctx:
    """Add logging and timing to context."""
    import time
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    print(f"🚀 [{timestamp}] Starting execution")
    
    # Just transform the context - no need for "next"
    duration = time.time() - start_time
    print(f"🏁 [{datetime.now().isoformat()}] Middleware setup completed in {duration*1000:.2f}ms")
    
    return {**ctx, "execution_time": duration, "start_time": start_time}

# Example Trigger - HTTP-like trigger
async def http_trigger(chain: Chain, initial_ctx: Ctx = None) -> Ctx:
    """HTTP trigger that executes a chain."""
    print("📡 HTTP Trigger activated")
    
    ctx: Ctx = {
        **(initial_ctx or {}),
        "trigger": "http",
        "method": "POST",
        "path": "/api/users",
        "timestamp": datetime.now().isoformat()
    }
    
    return await chain(ctx)

# Example Trigger - Cron-like trigger
async def cron_trigger(chain: Chain, initial_ctx: Ctx = None) -> Ctx:
    """Cron trigger that executes a chain."""
    print("⏰ Cron Trigger activated")
    
    ctx: Ctx = {
        **(initial_ctx or {}),
        "trigger": "cron",
        "schedule": "0 */5 * * *",
        "timestamp": datetime.now().isoformat()
    }
    
    return await chain(ctx)

# Example demonstrating middleware and chain composition
async def chain_with_middleware(ctx: Ctx) -> Ctx:
    """Apply middleware first, then the processing chain."""
    # Apply middleware first, then the processing chain
    result = await logging_middleware(ctx)
    result = await user_processing_chain(result)
    return result

async def main():
    """Main execution function."""
    print("🌟 ModuLink Universal Type System Demo\n")
    
    print("=== Example 1: HTTP Trigger ===")
    http_result = await http_trigger(chain_with_middleware, example_ctx)
    print("Result:", {k: str(v) if isinstance(v, Exception) else v for k, v in http_result.items()})
    
    print("\n=== Example 2: Cron Trigger ===")
    cron_result = await cron_trigger(chain_with_middleware, example_ctx)
    print("Result:", {k: str(v) if isinstance(v, Exception) else v for k, v in cron_result.items()})
    
    print("\n=== Example 3: Error Handling ===")
    error_ctx: Ctx = {"data": {"name": "Jane"}}  # Missing user_id
    error_result = await http_trigger(chain_with_middleware, error_ctx)
    print("Error Result:", {k: str(v) if isinstance(v, Exception) else v for k, v in error_result.items()})
    
    print("\n🎯 Universal Type System Benefits:")
    print("✅ Simple function types - no over-engineered abstractions")
    print("✅ Composable - links, chains, triggers work together")
    print("✅ Testable - each function can be tested independently")
    print("✅ Type-safe - full type hints support")
    print("✅ Flexible - triggers are just functions that accept contexts")

if __name__ == "__main__":
    asyncio.run(main())
