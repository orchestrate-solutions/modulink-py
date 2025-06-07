#!/usr/bin/env python3
"""
ModuLink Python FastAPI Example - ModuLink Types System

Demonstrates FastAPI integration with the ModuLink types system.
Shows how to create HTTP endpoints using functional composition.

To run this example:
1. Install FastAPI: pip install fastapi uvicorn
2. Run: python examples/basic_fastapi.py
3. Test: curl -X POST http://localhost:8000/api/users -H "Content-Type: application/json" -d '{"userId": "123"}'
"""

try:
    from fastapi import FastAPI, Request, HTTPException
    import uvicorn
except ImportError:
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    exit(1)

import asyncio
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Add the modulink package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import ModuLink types
from modulink import Ctx, Link, Middleware, compose, when, catch_errors, timing

# Create FastAPI app
app = FastAPI(title="ModuLink Types FastAPI Example")

# Middleware definitions
async def request_middleware(ctx: Ctx) -> Ctx:
    """Add request metadata to context."""
    return {
        **ctx,
        "timestamp": datetime.now().isoformat(),
        "request_id": f"req_{id(ctx)}"
    }

async def logging_middleware(ctx: Ctx) -> Ctx:
    """Log request details."""
    print(f"[{ctx.get('timestamp')}] {ctx.get('method')} {ctx.get('path')} - ID: {ctx.get('request_id')}")
    return ctx

# Business logic functions
async def validate_user(ctx: Ctx) -> Ctx:
    """Validate user from request body."""
    body = ctx.get("body", {})
    
    if not body.get("userId"):
        raise ValueError("User ID is required")
    
    return {**ctx, "userValidated": True, "userId": body["userId"]}

async def fetch_user_data(ctx: Ctx) -> Ctx:
    """Fetch user data (simulated)."""
    user_id = ctx.get("userId")
    print(f"Fetching data for user: {user_id}")
    
    # Simulate API call delay
    await asyncio.sleep(0.1)
    
    user_data = {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "role": "user",
        "created_at": datetime.now().isoformat()
    }
    
    return {**ctx, "userData": user_data}

async def format_response(ctx: Ctx) -> Ctx:
    """Format the final response."""
    return {
        **ctx,
        "response": {
            "success": True,
            "data": ctx.get("userData"),
            "metadata": {
                "request_id": ctx.get("request_id"),
                "timestamp": ctx.get("timestamp"),
                "processing_time": ctx.get("duration")
            }
        }
    }

async def health_check(ctx: Ctx) -> Ctx:
    """Health check endpoint logic."""
    return {
        **ctx,
        "response": {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
    }

# Create processing chains using ModuLink types
user_processing_chain = compose(
    request_middleware,
    logging_middleware,
    timing(validate_user),
    catch_errors(fetch_user_data),
    format_response
)

health_chain = compose(
    request_middleware,
    timing(health_check)
)

# FastAPI endpoint handlers
async def create_context_from_request(request: Request) -> Ctx:
    """Convert FastAPI request to ModuLink context."""
    ctx: Ctx = {
        "method": request.method,
        "path": request.url.path,
        "headers": dict(request.headers),
        "query": dict(request.query_params)
    }
    
    # Add body for POST/PUT requests
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            ctx["body"] = await request.json()
        except:
            ctx["body"] = {}
    
    return ctx

async def handle_chain_response(ctx: Ctx) -> Dict[str, Any]:
    """Handle the response from a ModuLink chain."""
    if ctx.get("error"):
        error_msg = str(ctx["error"])
        print(f"Error in chain: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    return ctx.get("response", {"success": True, "data": ctx})

@app.post("/api/users")
async def create_user(request: Request):
    """Create user endpoint using ModuLink chain."""
    ctx = await create_context_from_request(request)
    result_ctx = await user_processing_chain(ctx)
    return await handle_chain_response(result_ctx)

@app.get("/api/users/{user_id}")
async def get_user(user_id: str, request: Request):
    """Get user endpoint using ModuLink chain."""
    ctx = await create_context_from_request(request)
    ctx["body"] = {"userId": user_id}  # Add user_id to body for processing
    
    # Create a simpler chain for GET requests
    get_user_chain = compose(
        request_middleware,
        timing(fetch_user_data),
        format_response
    )
    
    result_ctx = await get_user_chain(ctx)
    return await handle_chain_response(result_ctx)

@app.get("/health")
async def health(request: Request):
    """Health check endpoint."""
    ctx = await create_context_from_request(request)
    result_ctx = await health_chain(ctx)
    return await handle_chain_response(result_ctx)

# Conditional execution example
@app.post("/api/users/conditional")
async def conditional_user_processing(request: Request):
    """Demonstrate conditional processing with when()."""
    ctx = await create_context_from_request(request)
    
    # Chain with conditional processing
    conditional_chain = compose(
        request_middleware,
        when(
            lambda ctx: ctx.get("body", {}).get("validate", True),
            validate_user
        ),
        fetch_user_data,
        format_response
    )
    
    result_ctx = await conditional_chain(ctx)
    return await handle_chain_response(result_ctx)

if __name__ == "__main__":
    print("🚀 Starting ModuLink Types FastAPI Demo")
    print("📡 Available endpoints:")
    print("  POST /api/users                  - Create user (requires userId in body)")
    print("  GET  /api/users/{user_id}        - Get user by ID")
    print("  POST /api/users/conditional      - Conditional processing example")
    print("  GET  /health                     - Health check")
    print()
    print("📝 Example requests:")
    print("  curl -X POST http://localhost:8000/api/users \\")
    print("    -H \"Content-Type: application/json\" \\")
    print("    -d '{\"userId\": \"123\"}'")
    print()
    print("  curl http://localhost:8000/api/users/456")
    print()
    print("  curl http://localhost:8000/health")
    print()
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")
