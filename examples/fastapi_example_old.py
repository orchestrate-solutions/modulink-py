"""
FastAPI Integration Example

This example shows how to integrate ModuLink with FastAPI for HTTP triggers.
It demonstrates:
- HTTP endpoint registration with ModuLink
- Request/response handling through Context
- Async function support
- Error handling and validation
- JSON serialization
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from modulink import ModuLink, Context
from typing import Dict, Any
import uvicorn

# Create FastAPI app and ModuLink instance
fastapi_app = FastAPI(title="ModuLink FastAPI Example")
modulink_app = ModuLink()

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

# ModuLink functions
def validate_user_data(ctx: Context) -> Context:
    """Validate user data"""
    ctx.start_step('validation')
    
    data = ctx.data
    
    # Age validation
    if data.get('age', 0) < 18:
        ctx.add_error('User must be at least 18 years old', 'AGE_ERROR')
    
    if data.get('age', 0) > 120:
        ctx.add_error('Invalid age provided', 'AGE_ERROR')
    
    # Name validation
    if len(data.get('name', '').strip()) < 2:
        ctx.add_error('Name must be at least 2 characters', 'NAME_ERROR')
    
    ctx.end_step('validation')
    return ctx

def normalize_user_data(ctx: Context) -> Context:
    """Normalize user data"""
    if ctx.has_errors():
        return ctx
    
    ctx.start_step('normalization')
    
    # Normalize name
    ctx.data['name'] = ctx.data['name'].strip().title()
    
    # Normalize email (already validated by Pydantic)
    ctx.data['email'] = ctx.data['email'].lower()
    
    ctx.end_step('normalization')
    return ctx

def save_user(ctx: Context) -> Context:
    """Save user to database (simulated)"""
    if ctx.has_errors():
        return ctx
    
    ctx.start_step('database_save')
    
    # Simulate database save
    import random
    user_id = random.randint(1000, 9999)
    
    ctx.data['id'] = user_id
    ctx.data['status'] = 'active'
    
    print(f"💾 Saved user {ctx.data['name']} with ID {user_id}")
    
    ctx.end_step('database_save')
    return ctx

def generate_welcome_message(ctx: Context) -> Context:
    """Generate personalized welcome message"""
    if ctx.has_errors():
        return ctx
    
    ctx.start_step('welcome_generation')
    
    name = ctx.data['name']
    age = ctx.data['age']
    
    if age < 25:
        ctx.data['welcome_message'] = f"Welcome to our platform, {name}! 🎉"
    elif age < 50:
        ctx.data['welcome_message'] = f"Great to have you here, {name}! 👋"
    else:
        ctx.data['welcome_message'] = f"Welcome aboard, {name}! We're honored to have you. 🌟"
    
    ctx.end_step('welcome_generation')
    return ctx

def send_welcome_email(ctx: Context) -> Context:
    """Send welcome email (simulated)"""
    if ctx.has_errors():
        return ctx
    
    ctx.start_step('email_sending')
    
    email = ctx.data['email']
    message = ctx.data['welcome_message']
    
    # Simulate email sending
    print(f"📧 Sending welcome email to {email}: {message}")
    
    ctx.data['email_sent'] = True
    
    ctx.end_step('email_sending')
    return ctx

# Register functions with ModuLink
modulink_app.register('validate_user_data', validate_user_data)
modulink_app.register('normalize_user_data', normalize_user_data)
modulink_app.register('save_user', save_user)
modulink_app.register('generate_welcome_message', generate_welcome_message)
modulink_app.register('send_welcome_email', send_welcome_email)

# Add middleware for request logging
def request_logging_middleware(ctx: Context) -> Context:
    """Log incoming requests"""
    if ctx.metadata.get('trigger_type') == 'http':
        method = ctx.metadata.get('method', 'UNKNOWN')
        path = ctx.metadata.get('path', 'unknown')
        print(f"🌐 {method} {path}")
    return ctx

modulink_app.use(request_logging_middleware)

# FastAPI endpoints using ModuLink
@fastapi_app.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreateRequest) -> Dict[str, Any]:
    """Create a new user using ModuLink chain"""
    
    # Create context from request data
    ctx = Context.from_http_request(
        data=user_data.dict(),
        method='POST',
        path='/users'
    )
    
    # Execute ModuLink chain
    result = modulink_app.chain([
        'validate_user_data',
        'normalize_user_data',
        'save_user',
        'generate_welcome_message',
        'send_welcome_email'
    ], ctx)
    
    # Handle errors
    if result.has_errors():
        error_messages = [error['message'] for error in result.get_errors()]
        raise HTTPException(status_code=400, detail=error_messages)
    
    # Return response
    return result.data

@fastapi_app.get("/users/{user_id}")
async def get_user(user_id: int) -> Dict[str, Any]:
    """Get user by ID (simulated)"""
    
    # Create context for lookup
    ctx = Context.from_http_request(
        data={'user_id': user_id},
        method='GET',
        path=f'/users/{user_id}'
    )
    
    # Simulate user lookup
    def lookup_user(ctx: Context) -> Context:
        ctx.start_step('user_lookup')
        
        # Simulate database lookup
        if ctx.data['user_id'] == 1234:
            ctx.data.update({
                'id': 1234,
                'name': 'John Doe',
                'email': 'john@example.com',
                'age': 30,
                'status': 'active',
                'welcome_message': 'Welcome back, John!'
            })
        else:
            ctx.add_error('User not found', 'NOT_FOUND')
        
        ctx.end_step('user_lookup')
        return ctx
    
    # Execute lookup
    result = modulink_app.chain(['lookup_user'], ctx, {'lookup_user': lookup_user})
    
    if result.has_errors():
        raise HTTPException(status_code=404, detail="User not found")
    
    return result.data

@fastapi_app.put("/users/{user_id}")
async def update_user(user_id: int, user_data: UserCreateRequest) -> Dict[str, Any]:
    """Update user using ModuLink chain"""
    
    # Create context with both user_id and update data
    ctx = Context.from_http_request(
        data={**user_data.dict(), 'user_id': user_id},
        method='PUT',
        path=f'/users/{user_id}'
    )
    
    # Update-specific function
    def update_user_record(ctx: Context) -> Context:
        ctx.start_step('user_update')
        
        user_id = ctx.data['user_id']
        print(f"📝 Updating user {user_id}")
        
        # Simulate update
        ctx.data['updated'] = True
        ctx.data['id'] = user_id
        
        ctx.end_step('user_update')
        return ctx
    
    # Execute update chain
    result = modulink_app.chain([
        'validate_user_data',
        'normalize_user_data',
        'update_user_record',
        'generate_welcome_message'
    ], ctx, {'update_user_record': update_user_record})
    
    if result.has_errors():
        error_messages = [error['message'] for error in result.get_errors()]
        raise HTTPException(status_code=400, detail=error_messages)
    
    return result.data

@fastapi_app.delete("/users/{user_id}")
async def delete_user(user_id: int) -> Dict[str, str]:
    """Delete user"""
    
    ctx = Context.from_http_request(
        data={'user_id': user_id},
        method='DELETE',
        path=f'/users/{user_id}'
    )
    
    def delete_user_record(ctx: Context) -> Context:
        ctx.start_step('user_deletion')
        
        user_id = ctx.data['user_id']
        print(f"🗑️  Deleting user {user_id}")
        
        # Simulate deletion
        ctx.data['deleted'] = True
        
        ctx.end_step('user_deletion')
        return ctx
    
    result = modulink_app.chain(['delete_user_record'], ctx, {'delete_user_record': delete_user_record})
    
    return {'message': f'User {user_id} deleted successfully'}

@fastapi_app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'modulink-fastapi'}

@fastapi_app.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get ModuLink metrics"""
    
    # Get registered functions
    registered_functions = list(modulink_app.registry.keys())
    
    return {
        'registered_functions': len(registered_functions),
        'function_names': registered_functions,
        'middleware_count': len(modulink_app.middleware),
        'service': 'modulink-fastapi'
    }

# Add CORS middleware if needed
from fastapi.middleware.cors import CORSMiddleware

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    print("🚀 Starting ModuLink FastAPI Example")
    print("Available endpoints:")
    print("  POST   /users        - Create user")
    print("  GET    /users/{id}   - Get user")
    print("  PUT    /users/{id}   - Update user")
    print("  DELETE /users/{id}   - Delete user")
    print("  GET    /health       - Health check")
    print("  GET    /metrics      - ModuLink metrics")
    print("\nExample requests:")
    print("curl -X POST http://localhost:8000/users \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"name\": \"Alice Smith\", \"email\": \"alice@example.com\", \"age\": 25}'")
    print("\nStarting server on http://localhost:8000")
    
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, reload=True)
