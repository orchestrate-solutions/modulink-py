#!/usr/bin/env python3
"""
ModuLink Python FastAPI Example - Universal Types System

Demonstrates FastAPI integration with the universal types system.
Shows how to create HTTP endpoints using functional composition.
"""

from fastapi import FastAPI, Request
import uvicorn
import asyncio
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Add the modulink package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import universal types
from modulink import Ctx, Link, Middleware, compose, when, catch_errors, timing

# Create FastAPI app
app = FastAPI()

# Simple createModulink implementation
def create_modulink(app, options):
    """Factory function to create a ModuLink instance."""
    
    class ModulinkInstance:
        def __init__(self):
            self.app = app
            self.environment = options.get('environment', 'development')
            self.enable_logging = options.get('enableLogging', True)
            self.global_middleware = []
        
        class UseInterface:
            def __init__(self, parent):
                self.parent = parent
            
            async def global_middleware(self, middleware: Middleware):
                """Register global middleware."""
                self.parent.global_middleware.append(middleware)
                if self.parent.enable_logging:
                    print("Global middleware registered")
        
        class WhenInterface:
            def __init__(self, parent):
                self.parent = parent
            
            async def http(self, path: str, methods: list, *links: Link):
                """Register HTTP endpoint with chain of links."""
                async def endpoint_handler(request: Request):
                    # Create context from request
                    ctx: Ctx = {
                        "method": request.method,
                        "path": request.url.path,
                        "headers": dict(request.headers),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Add body if it exists
                    try:
                        if request.method in ["POST", "PUT", "PATCH"]:
                            ctx["body"] = await request.json()
                    except:
                        ctx["body"] = {}
                    
                    # Apply global middleware first
                    for middleware in self.parent.global_middleware:
                        ctx = await middleware(ctx)
                    
                    # Execute links in sequence
                    for link in links:
                        if ctx.get("error"):
                            break
                        ctx = await link(ctx)
                    
                    # Return response
                    if ctx.get("error"):
                        return {"error": str(ctx["error"])}
                    elif ctx.get("response"):
                        return ctx["response"]
                    else:
                        return {"success": True, "data": ctx}
                
                # Register with FastAPI
                for method in methods:
                    if method.upper() == "GET":
                        app.get(path)(endpoint_handler)
                    elif method.upper() == "POST":
                        app.post(path)(endpoint_handler)
                    elif method.upper() == "PUT":
                        app.put(path)(endpoint_handler)
                    elif method.upper() == "DELETE":
                        app.delete(path)(endpoint_handler)
                
                if self.parent.enable_logging:
                    print(f"Registered HTTP endpoint: {' '.join(methods)} {path}")
        
        class TriggersInterface:
            def __init__(self, parent):
                self.parent = parent
            
            def http(self, path: str, methods: list):
                """Create HTTP trigger."""
                async def trigger_func(chain_func):
                    await self.parent.when.http(path, methods, chain_func)
                return trigger_func
        
        def __init__(self):
            self.app = app
            self.environment = options.get('environment', 'development')
            self.enable_logging = options.get('enableLogging', True)
            self.global_middleware = []
            self.use = self.UseInterface(self)
            self.when = self.WhenInterface(self)
            self.triggers = self.TriggersInterface(self)
        
        def create_named_chain(self, name: str, *links: Link):
            """Create a named chain of links."""
            async def chain_func(ctx: Ctx) -> Ctx:
                result = ctx
                for link in links:
                    if result.get("error"):
                        break
                    result = await link(result)
                return result
            
            if self.enable_logging:
                print(f"Created named chain: {name}")
            return chain_func
        
        def cleanup(self):
            """Cleanup resources."""
            if self.enable_logging:
                print("Cleanup completed")
    
    return ModulinkInstance()

# Initialize ModuLink with universal types
modu = create_modulink(app, {
    'environment': 'development',
    'enableLogging': True
})

# Define reusable links
async def validate_user(ctx: Ctx) -> Ctx:
    """Validate user from request body."""
    print("Validating user...")
    body = ctx.get("body", {})
    
    if not body.get("userId"):
        return {**ctx, "error": Exception("User ID is required")}
    
    return {**ctx, "userValidated": True}

async def fetch_user_data(ctx: Ctx) -> Ctx:
    """Fetch user data (simulated)."""
    if ctx.get("error"):
        return ctx  # Skip if there's an error
    
    user_id = ctx.get("body", {}).get("userId")
    print(f"Fetching data for user: {user_id}")
    
    # Simulate API call
    user_data = {
        "id": user_id,
        "name": "John Doe",
        "email": "john@example.com",
        "role": "user"
    }
    
    return {**ctx, "userData": user_data}

async def format_response(ctx: Ctx) -> Ctx:
    """Format the final response."""
    print("Formatting response...")
    if ctx.get("error"):
        return ctx  # Skip if there's an error
    
    return {
        **ctx,
        "response": {
            "success": True,
            "data": ctx.get("userData"),
            "timestamp": datetime.now().isoformat()
        }
    }

# Register global middleware
async def global_middleware(ctx: Ctx) -> Ctx:
    print(f"[{datetime.now().isoformat()}] Request started")
    return {**ctx, "startTime": datetime.now().timestamp() * 1000}

# Add completion middleware to chain
async def completion_middleware(ctx: Ctx) -> Ctx:
    """Add completion timing to requests."""
    if ctx.get("startTime"):
        duration = (datetime.now().timestamp() * 1000) - ctx["startTime"]
        print(f"[{datetime.now().isoformat()}] Request completed in {duration:.0f}ms")
        return {**ctx, "duration": duration}
    return ctx

# Example error handling chain
async def error_handler(ctx: Ctx) -> Ctx:
    """Handle errors in the chain."""
    if ctx.get("error"):
        print(f"Error occurred: {ctx['error']}")
        return {
            **ctx,
            "response": {
                "success": False,
                "error": str(ctx["error"]),
                "timestamp": datetime.now().isoformat()
            }
        }
    return ctx

async def setup_endpoints():
    """Setup all endpoints asynchronously."""
    # Register global middleware
    await modu.use.global_middleware(global_middleware)
    
    # Create HTTP endpoint using the convenience method
    await modu.when.http('/api/users', ['POST'], validate_user, fetch_user_data, format_response)
    
    # Alternative: Create a named chain and use it with a trigger
    user_processing_chain = modu.create_named_chain('userProcessing', validate_user, fetch_user_data, format_response)
    http_trigger = modu.triggers.http('/api/users/process', ['POST'])
    await http_trigger(user_processing_chain)
    
    # Register error handling endpoint
    await modu.when.http('/api/users/with-error-handling', ['POST'], 
        validate_user, 
        fetch_user_data, 
        format_response, 
        error_handler
    )

if __name__ == "__main__":
    # Setup endpoints first
    asyncio.run(setup_endpoints())
    
    print("🚀 Starting ModuLink Universal Types Demo Server")
    print("📡 Available endpoints:")
    print("  POST /api/users")
    print("  POST /api/users/process") 
    print("  POST /api/users/with-error-handling")
    print("\n📝 Example request:")
    print("  curl -X POST http://localhost:8000/api/users \\")
    print("    -H \"Content-Type: application/json\" \\")
    print("    -d '{\"userId\": \"123\"}'")
    print()
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\n🔄 Cleaning up...")
        modu.cleanup()
        print("👋 Goodbye!")
