#!/usr/bin/env python3
"""
Chain Demo - Showcasing ModuLink's middleware system and utilities.
"""

import asyncio
import time
from modulink import (
    ctx,
    chain, timing, logging, validate, performance_tracker,
    when, parallel, memoize, transform, set_values,
    validators, error_handlers
)

# Example business logic links
async def process_user_data(context):
    """Process user data with some artificial delay."""
    await asyncio.sleep(0.1)  # Simulate processing time
    
    user_id = context.get("user_id")
    if not user_id:
        raise ValueError("Missing user_id")
    
    return {**context, "processed": True, "timestamp": time.time()}

async def enrich_data(context):
    """Enrich the data with additional information."""
    return {
        **context,
        "enriched": True,
        "user_name": f"User_{context.get('user_id', 'unknown')}"
    }

async def save_to_database(context):
    """Simulate saving to database."""
    await asyncio.sleep(0.05)  # Simulate DB write
    return {**context, "saved": True, "db_id": f"db_{context.get('user_id')}"}

async def demo_chain():
    """Demonstrate the chain with middleware."""
    print("🚀 Chain Demo - ModuLink Python")
    print("=" * 60)
    
    # Create a chain with middleware
    user_processing = chain(
        process_user_data,
        enrich_data,
        save_to_database
    )
    
    # Middleware setup
    test_chain = chain(
        # Input validation
        validate(validators.required(["user_id"])),
        # Logging
        logging(log_output=True, log_timing=True),
        # Timing
        timing("total_execution"),
        # Execute main chain
        user_processing
    )
    
    # Test with valid input
    print("\n📝 Test 1: Valid input")
    result = await test_chain(ctx(user_id="12345", action="create"))
    print(f"✅ Success: {result.get('saved', False)}")
    print(f"📊 Timing: {result.get('timing', {})}")
    
    # Test with invalid input (missing user_id)
    print("\n📝 Test 2: Invalid input (missing user_id)")
    result = await test_chain(ctx(action="create"))
    if result.get("error"):
        print(f"❌ Error caught: {result['error']}")
    
    # Test conditional execution
    print("\n📝 Test 3: Conditional execution with when()")
    conditional_chain = chain(
        when(lambda ctx: ctx.get("premium", False), enrich_data),
        save_to_database
    )
    
    result = await conditional_chain(ctx(user_id="67890", premium=True))
    print(f"✅ Premium user enriched: {result.get('enriched', False)}")
    
    result = await conditional_chain(ctx(user_id="67890", premium=False))
    print(f"ℹ️ Regular user not enriched: {result.get('enriched', False)}")

async def demo_utility_library():
    """Demonstrate the utility library."""
    print("\n🛠️ Utility Library Demo")
    print("=" * 40)
    
    # Parallel execution
    print("\n📝 Parallel execution:")
    parallel_chain = parallel(
        set_values({"source": "api"}),
        set_values({"timestamp": time.time()}),
        transform("user_id", lambda x, ctx: f"processed_{x}")
    )
    
    result = await parallel_chain(ctx(user_id="test123"))
    print(f"✅ Parallel result: {result}")
    
    # Memoization
    print("\n📝 Memoization demo:")
    expensive_operation = memoize(
        key_fn=lambda ctx: f"user_{ctx.get('user_id')}",
        link=process_user_data,
        ttl=5.0
    )
    
    start = time.time()
    result1 = await expensive_operation(ctx(user_id="memo123"))
    time1 = time.time() - start
    
    start = time.time()
    result2 = await expensive_operation(ctx(user_id="memo123"))
    time2 = time.time() - start
    
    print(f"✅ First call: {time1:.3f}s")
    print(f"✅ Cached call: {time2:.3f}s (from cache: {result2.get('from_cache', False)})")

async def demo_error_handling():
    """Demonstrate error handling patterns."""
    print("\n🔧 Error Handling Demo")
    print("=" * 40)
    
    async def failing_link(context):
        if context.get("should_fail"):
            raise RuntimeError("Intentional failure for demo")
        return {**context, "success": True}
    
    # Create chain with error handler
    error_chain = chain(
        failing_link,
        transform(
            "error",
            lambda err, ctx: {"message": str(err), "user_friendly": True} if err else None
        )
    )
    
    # Test error propagation
    print("\n📝 Error propagation:")
    result = await error_chain(ctx(should_fail=True))
    if result.get("error", {}).get("user_friendly"):
        print(f"✅ User-friendly error: {result['error']['message']}")

async def main():
    """Run all demos."""
    print("🎯 ModuLink Python Demo")
    print("=" * 80)
    
    await demo_chain()
    await demo_utility_library()
    await demo_error_handling()
    
    print("\n🎉 Demo completed! ModuLink Python features demonstrated:")
    print("   ✅ Chain with middleware")
    print("   ✅ Validation & error handling")
    print("   ✅ Utility functions")
    print("   ✅ Performance tracking")

if __name__ == "__main__":
    asyncio.run(main())
