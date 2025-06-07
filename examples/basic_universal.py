#!/usr/bin/env python3
"""
ModuLink Python Basic Example - Universal Types System

Demonstrates the simplified universal types API that mirrors the TypeScript version.
This example shows basic link composition and trigger usage without complex framework integration.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the modulink package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modulink import Ctx, Link, Chain, Trigger, Middleware

# Example context
example_ctx: Ctx = {
    "user_id": "123",
    "data": {"name": "John", "email": "john@example.com"},
    "timestamp": datetime.now().isoformat()
}

# Define reusable links
async def validate_user(ctx: Ctx) -> Ctx:
    """Validate user from context."""
    print(f"🔍 Validating user: {ctx.get('user_id')}")
    
    body = ctx.get("body", ctx.get("data", {}))
    user_id = ctx.get("user_id") or body.get("user_id")
    
    if not user_id:
        return {**ctx, "error": Exception("User ID is required")}
    
    return {**ctx, "user_validated": True, "user_id": user_id}

async def fetch_user_data(ctx: Ctx) -> Ctx:
    """Fetch user data (simulated)."""
    if ctx.get("error"):
        return ctx  # Skip if there's an error
    
    user_id = ctx.get("user_id")
    print(f"📊 Fetching data for user: {user_id}")
    
    # Simulate API call
    user_data = {
        "id": user_id,
        "name": "John Doe",
        "email": "john@example.com",
        "role": "user"
    }
    
    return {**ctx, "user_data": user_data}

async def format_response(ctx: Ctx) -> Ctx:
    """Format the final response."""
    if ctx.get("error"):
        return {
            **ctx,
            "response": {
                "success": False,
                "error": str(ctx["error"]),
                "timestamp": ctx.get("timestamp")
            }
        }
    
    print("✨ Formatting response...")
    
    return {
        **ctx,
        "response": {
            "success": True,
            "data": ctx.get("user_data"),
            "timestamp": ctx.get("timestamp")
        }
    }

# Register global middleware - simple context transformation
async def timing_middleware(ctx: Ctx) -> Ctx:
    """Add timing information to context."""
    import time
    start_time = time.time()
    timestamp = datetime.now().isoformat()
    
    print(f"🚀 [{timestamp}] Request started")
    return {**ctx, "start_time": start_time, "timestamp": timestamp}

async def logging_middleware(ctx: Ctx) -> Ctx:
    """Add request logging."""
    print(f"📝 Processing request with trigger: {ctx.get('trigger', 'unknown')}")
    return ctx

# Create chains by composing links
async def user_processing_chain(ctx: Ctx) -> Ctx:
    """Process user through validation, data fetching, and response formatting."""
    print("🔗 Starting user processing chain")
    
    # Apply middleware
    result = await timing_middleware(ctx)
    result = await logging_middleware(result)
    
    # Execute links in sequence
    result = await validate_user(result)
    if not result.get("error"):
        result = await fetch_user_data(result)
    result = await format_response(result)
    
    print(f"✅ Chain completed: {'with errors' if result.get('error') else 'successfully'}")
    return result

# Define triggers
async def http_trigger(chain: Chain, path: str = "/api/users", method: str = "POST") -> Trigger:
    """HTTP trigger that simulates web request processing."""
    async def trigger_impl(initial_ctx: Ctx = None) -> Ctx:
        print(f"📡 HTTP Trigger activated: {method} {path}")
        
        ctx: Ctx = {
            **(initial_ctx or {}),
            "trigger": "http",
            "method": method,
            "path": path,
            "timestamp": datetime.now().isoformat()
        }
        
        return await chain(ctx)
    
    return trigger_impl

async def cron_trigger(chain: Chain, schedule: str = "0 */5 * * *") -> Trigger:
    """Cron trigger that simulates scheduled job execution."""
    async def trigger_impl(initial_ctx: Ctx = None) -> Ctx:
        print(f"⏰ Cron Trigger activated: {schedule}")
        
        ctx: Ctx = {
            **(initial_ctx or {}),
            "trigger": "cron",
            "schedule": schedule,
            "timestamp": datetime.now().isoformat()
        }
        
        return await chain(ctx)
    
    return trigger_impl

async def message_trigger(chain: Chain, topic: str = "user_events") -> Trigger:
    """Message trigger that simulates message queue processing."""
    async def trigger_impl(initial_ctx: Ctx = None) -> Ctx:
        print(f"💬 Message Trigger activated: {topic}")
        
        ctx: Ctx = {
            **(initial_ctx or {}),
            "trigger": "message",
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        }
        
        return await chain(ctx)
    
    return trigger_impl

# Example error handling link
async def error_handler(ctx: Ctx) -> Ctx:
    """Handle errors in the chain."""
    error = ctx.get("error")
    if error:
        print(f"❌ Error occurred: {error}")
        return {
            **ctx,
            "response": {
                "success": False,
                "error": str(error),
                "timestamp": ctx.get("timestamp")
            }
        }
    return ctx

# Create a chain with error handling
async def user_processing_with_error_handling(ctx: Ctx) -> Ctx:
    """User processing chain with error handling."""
    result = await user_processing_chain(ctx)
    result = await error_handler(result)
    return result

# Example health check
async def health_check_chain(ctx: Ctx) -> Ctx:
    """Simple health check chain."""
    return {
        **ctx,
        "response": {
            "status": "healthy",
            "timestamp": ctx.get("timestamp"),
            "environment": "development"
        }
    }

async def main():
    """Main execution function demonstrating the universal types system."""
    print("🌟 ModuLink Universal Types Demo\n")
    
    # Example 1: HTTP trigger with user processing
    print("=== Example 1: HTTP User Processing ===")
    http_user_trigger = await http_trigger(user_processing_chain)
    result1 = await http_user_trigger(example_ctx)
    print("Result:", {k: str(v) if isinstance(v, Exception) else v for k, v in result1.items() if k != "start_time"})
    
    # Example 2: Cron trigger 
    print("\n=== Example 2: Cron Trigger ===")
    cron_user_trigger = await cron_trigger(user_processing_chain)
    result2 = await cron_user_trigger(example_ctx)
    print("Result:", {k: str(v) if isinstance(v, Exception) else v for k, v in result2.items() if k != "start_time"})
    
    # Example 3: Error handling
    print("\n=== Example 3: Error Handling ===")
    error_ctx: Ctx = {"data": {"name": "Jane"}}  # Missing user_id
    http_error_trigger = await http_trigger(user_processing_with_error_handling)
    result3 = await http_error_trigger(error_ctx)
    print("Error Result:", {k: str(v) if isinstance(v, Exception) else v for k, v in result3.items() if k != "start_time"})
    
    # Example 4: Message trigger
    print("\n=== Example 4: Message Trigger ===")
    message_user_trigger = await message_trigger(user_processing_chain, "user_updates")
    result4 = await message_user_trigger(example_ctx)
    print("Result:", {k: str(v) if isinstance(v, Exception) else v for k, v in result4.items() if k != "start_time"})
    
    # Example 5: Health check
    print("\n=== Example 5: Health Check ===")
    health_trigger = await http_trigger(health_check_chain, "/health", "GET")
    result5 = await health_trigger({"timestamp": datetime.now().isoformat()})
    print("Health Result:", result5.get("response"))
    
    print("\n🎯 Universal Type System Benefits:")
    print("✅ Simple function types - no over-engineered abstractions")
    print("✅ Composable - links, chains, triggers work together")
    print("✅ Testable - each function can be tested independently")
    print("✅ Type-safe - full type hints support")
    print("✅ Flexible - triggers are just functions that accept contexts")
    print("✅ Framework agnostic - works with any Python web framework")

if __name__ == "__main__":
    asyncio.run(main())
