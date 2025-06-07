#!/usr/bin/env python3
"""
ModuLink Python Advanced FastAPI Example - Universal Types System

Demonstrates advanced FastAPI integration with the universal types system.
Shows validation, normalization, error handling, and complex workflows.

To run this example:
1. Install dependencies: pip install fastapi uvicorn pydantic[email]
2. Run: python examples/fastapi_example.py
3. Test: curl -X POST http://localhost:8000/api/users -H "Content-Type: application/json" -d '{"name": "John Doe", "email": "john@example.com", "age": 25}'
"""

try:
    from fastapi import FastAPI, Request, HTTPException
    from pydantic import BaseModel, EmailStr, ValidationError
    import uvicorn
except ImportError:
    print("Dependencies not installed. Install with: pip install fastapi uvicorn pydantic[email]")
    exit(1)

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os
import random

# Add the modulink package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import universal types
from modulink import Ctx, Link, compose, when, catch_errors, timing

# Create FastAPI app
app = FastAPI(
    title="ModuLink Advanced FastAPI Example",
    description="Advanced integration with universal types system",
    version="2.0.0"
)

# Pydantic models for request/response validation
class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    age: int

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: int
    status: str
    welcome_message: str
    created_at: str

# Middleware and utility functions
async def request_logger(ctx: Ctx) -> Ctx:
    """Log incoming requests."""
    method = ctx.get("method")
    path = ctx.get("path")
    timestamp = datetime.now().isoformat()
    request_id = f"req_{id(ctx)}"
    
    print(f"[{timestamp}] {method} {path} - Request ID: {request_id}")
    
    return {
        **ctx,
        "timestamp": timestamp,
        "request_id": request_id,
        "start_time": datetime.now().timestamp()
    }

async def validate_user_data(ctx: Ctx) -> Ctx:
    """Validate user data using Pydantic."""
    body = ctx.get("body", {})
    
    try:
        # Validate using Pydantic model
        user_request = UserCreateRequest(**body)
        validated_data = user_request.dict()
        
        # Additional business validation
        if validated_data["age"] < 18:
            raise ValueError("User must be at least 18 years old")
        
        if validated_data["age"] > 120:
            raise ValueError("Invalid age provided")
        
        if len(validated_data["name"].strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        
        return {**ctx, "validated_data": validated_data, "validation_passed": True}
        
    except ValidationError as e:
        raise ValueError(f"Validation error: {e}")
    except Exception as e:
        raise ValueError(f"Validation failed: {str(e)}")

async def normalize_user_data(ctx: Ctx) -> Ctx:
    """Normalize user data."""
    if not ctx.get("validation_passed"):
        return ctx
    
    data = ctx.get("validated_data", {})
    
    # Normalize name
    data["name"] = data["name"].strip().title()
    
    # Normalize email (already validated by Pydantic)
    data["email"] = data["email"].lower()
    
    return {**ctx, "normalized_data": data}

async def save_user(ctx: Ctx) -> Ctx:
    """Save user to database (simulated)."""
    data = ctx.get("normalized_data", {})
    
    # Simulate database save
    await asyncio.sleep(0.05)  # Simulate DB latency
    
    user_id = random.randint(1000, 9999)
    created_at = datetime.now().isoformat()
    
    user_data = {
        **data,
        "id": user_id,
        "status": "active",
        "created_at": created_at
    }
    
    print(f"💾 Saved user {data['name']} with ID {user_id}")
    
    return {**ctx, "user_data": user_data}

async def generate_welcome_message(ctx: Ctx) -> Ctx:
    """Generate personalized welcome message."""
    user_data = ctx.get("user_data", {})
    
    name = user_data.get("name", "User")
    age = user_data.get("age", 0)
    
    # Generate age-appropriate welcome message
    if age < 25:
        message = f"Welcome to our platform, {name}! Excited to have you on board! 🎉"
    elif age < 40:
        message = f"Hello {name}! Great to have you join our community! 👋"
    else:
        message = f"Welcome {name}! We're honored to have you with us! 🌟"
    
    return {
        **ctx,
        "user_data": {**user_data, "welcome_message": message}
    }

async def format_user_response(ctx: Ctx) -> Ctx:
    """Format the final user response."""
    user_data = ctx.get("user_data", {})
    request_id = ctx.get("request_id")
    
    return {
        **ctx,
        "response": {
            "success": True,
            "data": user_data,
            "metadata": {
                "request_id": request_id,
                "timestamp": ctx.get("timestamp"),
                "processing_time": ctx.get("duration")
            }
        }
    }

async def audit_log(ctx: Ctx) -> Ctx:
    """Log user creation for audit purposes."""
    user_data = ctx.get("user_data", {})
    request_id = ctx.get("request_id")
    
    print(f"📋 AUDIT: User created - ID: {user_data.get('id')}, "
          f"Email: {user_data.get('email')}, Request: {request_id}")
    
    return ctx

# Error handling functions
async def handle_validation_errors(ctx: Ctx) -> Ctx:
    """Handle validation errors gracefully."""
    if ctx.get("error") and "validation" in str(ctx["error"]).lower():
        return {
            **ctx,
            "response": {
                "success": False,
                "error": "Validation failed",
                "details": str(ctx["error"]),
                "timestamp": datetime.now().isoformat()
            }
        }
    return ctx

# Create processing chains
user_creation_chain = compose(
    request_logger,
    timing(validate_user_data),
    catch_errors(normalize_user_data),
    catch_errors(save_user),
    generate_welcome_message,
    audit_log,
    format_user_response,
    handle_validation_errors
)

# Health check chain
async def health_check(ctx: Ctx) -> Ctx:
    """Comprehensive health check."""
    return {
        **ctx,
        "response": {
            "status": "healthy",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "database": "connected",  # Simulated
                "cache": "available",     # Simulated
                "external_apis": "online" # Simulated
            }
        }
    }

health_chain = compose(
    request_logger,
    timing(health_check)
)

# FastAPI utility functions
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
    if ctx.get("error") and not ctx.get("response"):
        error_msg = str(ctx["error"])
        print(f"❌ Unhandled error in chain: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    return ctx.get("response", {"success": True, "data": ctx})

# FastAPI endpoints
@app.post("/api/users", response_model=None)
async def create_user(request: Request):
    """
    Create a new user with validation, normalization, and audit logging.
    
    Demonstrates:
    - Pydantic validation
    - Data normalization
    - Error handling
    - Audit logging
    - Personalized responses
    """
    ctx = await create_context_from_request(request)
    result_ctx = await user_creation_chain(ctx)
    return await handle_chain_response(result_ctx)

@app.get("/api/users/{user_id}")
async def get_user(user_id: str, request: Request):
    """Get user by ID (simulated)."""
    async def fetch_user(ctx: Ctx) -> Ctx:
        # Simulate user lookup
        await asyncio.sleep(0.02)
        
        user_data = {
            "id": int(user_id),
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "age": random.randint(18, 65),
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        return {**ctx, "user_data": user_data}
    
    get_user_chain = compose(
        request_logger,
        timing(fetch_user),
        generate_welcome_message,
        format_user_response
    )
    
    ctx = await create_context_from_request(request)
    result_ctx = await get_user_chain(ctx)
    return await handle_chain_response(result_ctx)

@app.get("/health")
async def health_endpoint(request: Request):
    """Comprehensive health check endpoint."""
    ctx = await create_context_from_request(request)
    result_ctx = await health_chain(ctx)
    return await handle_chain_response(result_ctx)

# Conditional processing example
@app.post("/api/users/bulk")
async def bulk_create_users(request: Request):
    """Create multiple users with conditional processing."""
    async def process_bulk_users(ctx: Ctx) -> Ctx:
        users = ctx.get("body", {}).get("users", [])
        
        if not users:
            raise ValueError("No users provided")
        
        if len(users) > 10:
            raise ValueError("Maximum 10 users allowed per request")
        
        processed_users = []
        
        for user_data in users:
            # Create individual context for each user
            user_ctx = {"body": user_data}
            
            # Process each user through the chain
            result = await compose(
                validate_user_data,
                normalize_user_data,
                save_user,
                generate_welcome_message
            )(user_ctx)
            
            if not result.get("error"):
                processed_users.append(result.get("user_data"))
        
        return {**ctx, "processed_users": processed_users}
    
    bulk_chain = compose(
        request_logger,
        timing(process_bulk_users),
        lambda ctx: {
            **ctx,
            "response": {
                "success": True,
                "data": ctx.get("processed_users", []),
                "count": len(ctx.get("processed_users", [])),
                "timestamp": datetime.now().isoformat()
            }
        }
    )
    
    ctx = await create_context_from_request(request)
    result_ctx = await bulk_chain(ctx)
    return await handle_chain_response(result_ctx)

if __name__ == "__main__":
    print("🚀 Starting ModuLink Advanced FastAPI Demo")
    print("📡 Available endpoints:")
    print("  POST /api/users           - Create user with full validation")
    print("  GET  /api/users/{id}      - Get user by ID")
    print("  POST /api/users/bulk      - Create multiple users")
    print("  GET  /health              - Health check")
    print()
    print("📝 Example requests:")
    print('  curl -X POST http://localhost:8000/api/users \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"name": "John Doe", "email": "john@example.com", "age": 25}\'')
    print()
    print('  curl -X POST http://localhost:8000/api/users/bulk \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"users": [{"name": "Alice", "email": "alice@example.com", "age": 30}]}\'')
    print()
    print("  curl http://localhost:8000/health")
    print()
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    except KeyboardInterrupt:
        print("\n👋 Server stopped!")
