#!/usr/bin/env python3
"""
Enhanced Chain Demo - Showcasing the new 3-level middleware system

This example demonstrates the enhanced chain functionality that brings
ModuLink Python up to parity with ModuLink JavaScript.
"""

import asyncio
import time
from modulink.types import ctx
from modulink.utils import (
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

async def demo_enhanced_chain():
    """Demonstrate the enhanced chain with 3-level middleware."""
    print("🚀 Enhanced Chain Demo - ModuLink Python Parity")
    print("=" * 60)
    
    # Create a chain with the enhanced middleware system
    user_processing_chain = chain(
        process_user_data,
        enrich_data,
        save_to_database
    )
    
    # Add onInput middleware (runs before any links)
    user_processing_chain.on_input(performance_tracker())
    user_processing_chain.on_input(validate(validators.required(["user_id"])))
    user_processing_chain.on_input(logging(log_output=False, log_timing=False))
    
    # Add onOutput middleware (runs after each link)
    user_processing_chain.on_output(timing("link_execution"))
    
    # Add global middleware (runs around the entire chain)
    user_processing_chain.use(logging(log_input=False, log_output=True))
    
    # Test with valid input
    print("\n📝 Test 1: Valid input")
    result = await user_processing_chain(ctx(user_id="12345", action="create"))
    print(f"✅ Success: {result.get('saved', False)}")
    print(f"📊 Performance: {result.get('_metadata', {})}")
    
    # Test with invalid input (missing user_id)
    print("\n📝 Test 2: Invalid input (missing user_id)")
    result = await user_processing_chain(ctx(action="create"))
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
    """Demonstrate the rich utility library."""
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
    
    error_chain = chain(failing_link)
    
    # Test error propagation
    print("\n📝 Error propagation:")
    result = await error_chain(ctx(should_fail=True))
    if result.get("error"):
        print(f"❌ Error properly caught: {type(result['error']).__name__}")
    
    # Test with error handler middleware
    error_chain.use(lambda ctx: error_handlers.user_friendly(ctx.get("error"), ctx) if ctx.get("error") else ctx)
    
    result = await error_chain(ctx(should_fail=True))
    if result.get("error", {}).get("user_friendly"):
        print(f"✅ User-friendly error: {result['error']['message']}")

async def main():
    """Run all demos."""
    print("🎯 ModuLink Python - JavaScript Parity Demo")
    print("=" * 80)
    
    await demo_enhanced_chain()
    await demo_utility_library()
    await demo_error_handling()
    
    print("\n🎉 Demo completed! ModuLink Python now has JavaScript parity for:")
    print("   ✅ 3-Level Middleware (onInput, onOutput, use)")
    print("   ✅ Error Propagation")
    print("   ✅ Performance Tracking")
    print("   ✅ Rich Utility Library")
    print("   ✅ Validation & Error Handling Patterns")

if __name__ == "__main__":
    asyncio.run(main())
