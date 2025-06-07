#!/usr/bin/env python3
"""
Enhanced Middleware System Example for ModuLink Universal Types

Demonstrates the simplified middleware system where middleware just transforms context.
No complex "next" parameter needed - middleware applies in sequence.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any
import json

# Add the modulink package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modulink import Ctx, Link, Chain, Trigger, Middleware

# Example Links
async def validate_user(ctx: Ctx) -> Ctx:
    """Validate user from context."""
    print(f"🔍 Validating user: {ctx.get('user_id')}")
    
    if not ctx.get("user_id"):
        return {**ctx, "error": Exception("User ID is required")}
    
    return {**ctx, "user_validated": True}

async def process_user_data(ctx: Ctx) -> Ctx:
    """Process user data."""
    if ctx.get("error"):
        return ctx  # Skip if there's an error
    
    print(f"⚙️ Processing data for user: {ctx.get('user_id')}")
    
    return {
        **ctx,
        "processed_data": {
            "user_id": ctx.get("user_id"),
            "processed_at": datetime.now().isoformat(),
            "status": "processed"
        }
    }

async def format_response(ctx: Ctx) -> Ctx:
    """Format the response."""
    if ctx.get("error"):
        return ctx  # Skip if there's an error
    
    print("📋 Formatting response")
    
    return {
        **ctx,
        "response": {
            "success": True,
            "data": ctx.get("processed_data"),
            "message": "User data processed successfully"
        }
    }

# Example Middleware Functions (simple transformations)

# Global timing middleware - adds timing info
async def timing_middleware(ctx: Ctx) -> Ctx:
    """Add timing information to context."""
    import time
    timestamp = datetime.now().isoformat()
    print(f"⏱️  [TIMING] Execution started at {timestamp}")
    return {**ctx, "start_time": time.time(), "timestamp": timestamp}

# Input validation middleware
async def input_validation_middleware(ctx: Ctx) -> Ctx:
    """Validate input requirements."""
    print("🔒 [VALIDATION] Checking input requirements")
    
    if not ctx.get("req") and not ctx.get("user_id"):
        return {**ctx, "error": Exception("Missing required input")}
    
    return {**ctx, "input_validated": True}

# Output sanitization middleware
async def output_sanitization_middleware(ctx: Ctx) -> Ctx:
    """Clean output data."""
    print("🧹 [SANITIZATION] Cleaning output data")
    
    response = ctx.get("response")
    if response and isinstance(response, dict):
        # Remove sensitive fields
        sanitized = {k: v for k, v in response.items() 
                    if k not in ["internal_id", "debug"]}
        return {**ctx, "response": sanitized}
    
    return ctx

# Audit middleware - logs operations
async def audit_middleware(ctx: Ctx) -> Ctx:
    """Log operations for audit trail."""
    operation = ctx.get("operation", "unknown")
    user_id = ctx.get("user_id", "anonymous")
    print(f"📝 [AUDIT] Operation: {operation}, User: {user_id}")
    
    return {
        **ctx,
        "audit_log": {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "user_id": user_id
        }
    }

# Rate limiting middleware
async def rate_limiting_middleware(ctx: Ctx) -> Ctx:
    """Simple rate limiting check."""
    print("🚦 [RATE LIMIT] Checking request rate")
    
    # Simulate rate limit check
    user_id = ctx.get("user_id")
    if user_id == "blocked_user":
        return {**ctx, "error": Exception("Rate limit exceeded")}
    
    return {**ctx, "rate_limit_checked": True}

# Error handling middleware
async def error_handling_middleware(ctx: Ctx) -> Ctx:
    """Handle and format errors."""
    error = ctx.get("error")
    if error:
        print(f"❌ [ERROR HANDLER] Processing error: {error}")
        return {
            **ctx,
            "response": {
                "success": False,
                "error": str(error),
                "timestamp": ctx.get("timestamp")
            }
        }
    return ctx

# Create middleware stacks for different scenarios

# Basic processing chain with timing
async def basic_processing_chain(ctx: Ctx) -> Ctx:
    """Basic chain with timing middleware."""
    print("🔗 Starting basic processing chain")
    
    # Apply timing middleware
    result = await timing_middleware(ctx)
    
    # Execute processing links
    result = await validate_user(result)
    if not result.get("error"):
        result = await process_user_data(result)
        result = await format_response(result)
    
    return result

# Enhanced processing chain with full middleware stack
async def enhanced_processing_chain(ctx: Ctx) -> Ctx:
    """Enhanced chain with full middleware stack."""
    print("🔗 Starting enhanced processing chain")
    
    # Input middleware stack
    result = await timing_middleware(ctx)
    result = await input_validation_middleware(result)
    result = await audit_middleware(result)
    result = await rate_limiting_middleware(result)
    
    # Core processing (only if no errors)
    if not result.get("error"):
        result = await validate_user(result)
        if not result.get("error"):
            result = await process_user_data(result)
            result = await format_response(result)
    
    # Output middleware stack
    result = await output_sanitization_middleware(result)
    result = await error_handling_middleware(result)
    
    return result

# Specialized middleware for specific use cases

async def admin_processing_chain(ctx: Ctx) -> Ctx:
    """Processing chain for admin operations."""
    print("🔗 Starting admin processing chain")
    
    # Add admin-specific middleware
    async def admin_auth_middleware(ctx: Ctx) -> Ctx:
        print("👑 [ADMIN AUTH] Checking admin privileges")
        if not ctx.get("is_admin"):
            return {**ctx, "error": Exception("Admin privileges required")}
        return {**ctx, "admin_verified": True}
    
    # Apply middleware stack
    result = await timing_middleware(ctx)
    result = await admin_auth_middleware(result)
    result = await audit_middleware(result)
    
    # Core processing
    if not result.get("error"):
        result = await validate_user(result)
        if not result.get("error"):
            result = await process_user_data(result)
            result = await format_response(result)
    
    result = await error_handling_middleware(result)
    
    return result

# Create trigger factories

async def http_trigger(chain: Chain, path: str = "/api/users", method: str = "POST") -> Trigger:
    """HTTP trigger with request context."""
    async def trigger_impl(initial_ctx: Ctx = None) -> Ctx:
        print(f"📡 HTTP Trigger activated: {method} {path}")
        
        ctx: Ctx = {
            **(initial_ctx or {}),
            "trigger": "http",
            "method": method,
            "path": path,
            "operation": "http_request",
            "timestamp": datetime.now().isoformat()
        }
        
        return await chain(ctx)
    
    return trigger_impl

async def background_job_trigger(chain: Chain, job_name: str = "user_processing") -> Trigger:
    """Background job trigger."""
    async def trigger_impl(initial_ctx: Ctx = None) -> Ctx:
        print(f"⚙️ Background Job Trigger activated: {job_name}")
        
        ctx: Ctx = {
            **(initial_ctx or {}),
            "trigger": "background_job",
            "job_name": job_name,
            "operation": "background_processing",
            "timestamp": datetime.now().isoformat()
        }
        
        return await chain(ctx)
    
    return trigger_impl

async def demonstrate_middleware():
    """Manual middleware demonstration."""
    print("\n🎯 Manual Middleware Demonstration\n")
    
    # Test context
    test_context: Ctx = {
        "user_id": "user123",
        "operation": "processUser",
        "timestamp": datetime.now().isoformat()
    }
    
    print("=== Example 1: Basic Processing ===")
    result1 = await basic_processing_chain(test_context)
    print("Result:", {k: str(v) if isinstance(v, Exception) else v 
                     for k, v in result1.items() if k != "start_time"})
    
    print("\n=== Example 2: Enhanced Processing ===")
    result2 = await enhanced_processing_chain(test_context)
    print("Result:", {k: str(v) if isinstance(v, Exception) else v 
                     for k, v in result2.items() if k != "start_time"})
    
    print("\n=== Example 3: Error Handling ===")
    error_context: Ctx = {
        "operation": "processUser",
        "timestamp": datetime.now().isoformat()
        # Missing user_id to trigger validation error
    }
    result3 = await enhanced_processing_chain(error_context)
    print("Error Result:", {k: str(v) if isinstance(v, Exception) else v 
                          for k, v in result3.items() if k != "start_time"})
    
    print("\n=== Example 4: Admin Processing ===")
    admin_context: Ctx = {
        "user_id": "admin123",
        "is_admin": True,
        "operation": "adminOperation",
        "timestamp": datetime.now().isoformat()
    }
    result4 = await admin_processing_chain(admin_context)
    print("Admin Result:", {k: str(v) if isinstance(v, Exception) else v 
                          for k, v in result4.items() if k != "start_time"})
    
    print("\n=== Example 5: Rate Limiting ===")
    blocked_context: Ctx = {
        "user_id": "blocked_user",
        "operation": "processUser",
        "timestamp": datetime.now().isoformat()
    }
    result5 = await enhanced_processing_chain(blocked_context)
    print("Blocked Result:", {k: str(v) if isinstance(v, Exception) else v 
                            for k, v in result5.items() if k != "start_time"})
    
    print("\n=== Example 6: HTTP Trigger ===")
    http_user_trigger = await http_trigger(enhanced_processing_chain, "/api/users/process", "POST")
    result6 = await http_user_trigger(test_context)
    print("HTTP Result:", {k: str(v) if isinstance(v, Exception) else v 
                         for k, v in result6.items() if k != "start_time"})
    
    print("\n=== Example 7: Background Job Trigger ===")
    bg_job_trigger = await background_job_trigger(basic_processing_chain, "daily_user_processing")
    result7 = await bg_job_trigger(test_context)
    print("Background Job Result:", {k: str(v) if isinstance(v, Exception) else v 
                                   for k, v in result7.items() if k != "start_time"})
    
    print("\n✨ Enhanced Middleware Benefits:")
    print("✅ Simple transformations - no complex 'next' parameter")
    print("✅ Granular control - target specific processing stages")
    print("✅ Composable - stack multiple middleware easily")
    print("✅ Debuggable - each middleware is a pure transformation")
    print("✅ Flexible - apply before or after core processing")
    print("✅ Specialized chains - different middleware for different use cases")
    print("✅ Error handling - centralized error processing")
    print("✅ Audit trail - comprehensive logging and monitoring")

async def main():
    """Main execution function."""
    print("🌟 ModuLink Enhanced Middleware System Demo\n")
    
    await demonstrate_middleware()

if __name__ == "__main__":
    asyncio.run(main())
