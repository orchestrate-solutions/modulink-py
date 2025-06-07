"""
Basic ModuLink Example - Universal Types System

This example demonstrates the core concepts of ModuLink using universal types:
- Simple function composition and chaining
- Context flow with pure dictionary contexts
- Error handling with universal patterns
- Timing and middleware
- Clean functional approach without complex classes
"""

from modulink import Ctx, create_modulink, chain, when, catch_errors, timing
import asyncio
from datetime import datetime

# Create a ModuLink instance using universal types
modulink = create_modulink()

# Define individual functions (links in the chain)
async def validate_input(ctx: Ctx) -> Ctx:
    """Validate the input data"""
    print("🔍 Validating input...")
    
    data = ctx.get('data', {})
    errors = ctx.get('errors', [])
    
    if not data.get('name'):
        errors.append({'message': 'Name is required', 'code': 'VALIDATION_ERROR'})
    
    if not data.get('email'):
        errors.append({'message': 'Email is required', 'code': 'VALIDATION_ERROR'})
    
    return {
        **ctx,
        'errors': errors,
        'steps': ctx.get('steps', []) + [{'name': 'validation', 'completed_at': datetime.utcnow().isoformat()}]
    }

async def normalize_data(ctx: Ctx) -> Ctx:
    """Normalize and clean the data"""
    if ctx.get('errors'):
        return ctx  # Skip if validation failed
    
    print("🧹 Normalizing data...")
    
    data = ctx.get('data', {})
    
    # Normalize name (title case)
    normalized_data = {
        **data,
        'name': data['name'].strip().title() if data.get('name') else '',
        'email': data['email'].strip().lower() if data.get('email') else '',
        'processed_at': datetime.utcnow().isoformat()
    }
    
    return {
        **ctx,
        'data': normalized_data,
        'steps': ctx.get('steps', []) + [{'name': 'normalization', 'completed_at': datetime.utcnow().isoformat()}]
    }

async def enrich_data(ctx: Ctx) -> Ctx:
    """Enrich data with additional information"""
    if ctx.get('errors'):
        return ctx
    
    print("✨ Enriching data...")
    
    data = ctx.get('data', {})
    email = data.get('email', '')
    
    # Add domain from email
    domain = email.split('@')[1] if '@' in email else 'unknown'
    
    enriched_data = {
        **data,
        'domain': domain,
        'greeting': f"Hello, {data.get('name', 'there')}!"
    }
    
    return {
        **ctx,
        'data': enriched_data,
        'steps': ctx.get('steps', []) + [{'name': 'enrichment', 'completed_at': datetime.utcnow().isoformat()}]
    }

async def save_result(ctx: Ctx) -> Ctx:
    """Save the processed result"""
    if ctx.get('errors'):
        return ctx
    
    print("💾 Saving result...")
    
    data = ctx.get('data', {})
    
    # Simulate saving to database
    saved_data = {
        **data,
        'saved': True,
        'id': 12345,  # Simulated ID
        'saved_at': datetime.utcnow().isoformat()
    }
    
    print(f"✅ Saved user: {data.get('name')} ({data.get('email')})")
    
    return {
        **ctx,
        'data': saved_data,
        'steps': ctx.get('steps', []) + [{'name': 'saving', 'completed_at': datetime.utcnow().isoformat()}]
    }

# Create processing chain
processing_chain = chain(
    validate_input,
    normalize_data,
    enrich_data,
    save_result
)

async def demo_successful_flow():
    """Demonstrate a successful processing flow"""
    print("🔄 Demo: Successful Flow")
    print("-" * 40)
    
    # Create context with valid data
    ctx: Ctx = {
        'data': {
            'name': '  alice smith  ',
            'email': '  ALICE@EXAMPLE.COM  '
        },
        'request_id': 'demo-001'
    }
    
    # Execute the chain
    result = await processing_chain(ctx)
    
    # Display results
    print(f"Final data: {result.get('data')}")
    print(f"Steps completed: {len(result.get('steps', []))}")
    print(f"Errors: {result.get('errors', [])}")
    print()

async def demo_validation_errors():
    """Demonstrate error handling"""
    print("❌ Demo: Validation Errors")
    print("-" * 40)
    
    # Create context with invalid data
    ctx: Ctx = {
        'data': {
            'name': '',  # Missing name
            # Missing email entirely
        },
        'request_id': 'demo-002'
    }
    
    # Execute the chain
    result = await processing_chain(ctx)
    
    # Display results
    print(f"Final data: {result.get('data')}")
    print(f"Errors: {result.get('errors', [])}")
    print(f"Steps completed: {len(result.get('steps', []))}")
    print()

async def demo_with_middleware():
    """Demonstrate middleware functionality"""
    print("🔧 Demo: Middleware")
    print("-" * 40)
    
    # Create logging middleware
    async def logging_middleware(ctx: Ctx) -> Ctx:
        request_id = ctx.get('request_id', 'unknown')
        print(f"  🔍 Processing request: {request_id}")
        return ctx
    
    # Create timing middleware
    async def timing_middleware(ctx: Ctx) -> Ctx:
        start_time = datetime.utcnow()
        new_ctx = {**ctx, '_start_time': start_time.isoformat()}
        return new_ctx
    
    # Compose with middleware
    chain_with_middleware = chain(
        logging_middleware,
        timing_middleware,
        validate_input,
        normalize_data
    )
    
    # Execute chain with middleware
    ctx: Ctx = {
        'data': {'name': 'Charlie', 'email': 'charlie@example.com'},
        'request_id': 'demo-003'
    }
    
    result = await chain_with_middleware(ctx)
    
    print(f"Result: {result.get('data')}")
    print(f"Processing started at: {result.get('_start_time')}")
    print()

async def demo_error_handling():
    """Demonstrate error handling with catch_errors utility"""
    print("🛡️  Demo: Error Handling")
    print("-" * 40)
    
    # Create a function that might fail
    async def risky_operation(ctx: Ctx) -> Ctx:
        data = ctx.get('data', {})
        if data.get('name') == 'error':
            raise ValueError("Simulated processing error")
        
        return {**ctx, 'risky_completed': True}
    
    # Wrap with error handling
    safe_risky_operation = catch_errors(risky_operation)
    
    # Create chain with error handling
    safe_chain = chain(
        validate_input,
        safe_risky_operation,
        normalize_data
    )
    
    # Test with error-triggering data
    ctx: Ctx = {
        'data': {'name': 'error', 'email': 'error@test.com'},
        'request_id': 'demo-004'
    }
    
    result = await safe_chain(ctx)
    
    print(f"Result: {result.get('data')}")
    print(f"Errors: {result.get('errors', [])}")
    print(f"Risk operation completed: {result.get('risky_completed', False)}")
    print()

async def demo_conditional_processing():
    """Demonstrate conditional processing with when utility"""
    print("🔀 Demo: Conditional Processing")
    print("-" * 40)
    
    # Create conditional enrichment
    async def premium_enrichment(ctx: Ctx) -> Ctx:
        data = ctx.get('data', {})
        return {
            **ctx,
            'data': {
                **data,
                'premium_features': True,
                'priority_support': True
            }
        }
    
    # Only apply premium enrichment if user is premium
    conditional_enrichment = when(
        lambda ctx: ctx.get('data', {}).get('user_type') == 'premium',
        premium_enrichment
    )
    
    # Create chain with conditional processing
    conditional_chain = chain(
        validate_input,
        normalize_data,
        conditional_enrichment
    )
    
    # Test with premium user
    premium_ctx: Ctx = {
        'data': {
            'name': 'Premium User',
            'email': 'premium@example.com',
            'user_type': 'premium'
        },
        'request_id': 'demo-005-premium'
    }
    
    premium_result = await conditional_chain(premium_ctx)
    
    # Test with regular user  
    regular_ctx: Ctx = {
        'data': {
            'name': 'Regular User',
            'email': 'regular@example.com',
            'user_type': 'regular'
        },
        'request_id': 'demo-005-regular'
    }
    
    regular_result = await conditional_chain(regular_ctx)
    
    print(f"Premium user result: {premium_result.get('data')}")
    print(f"Regular user result: {regular_result.get('data')}")
    print()

async def demo_timing():
    """Demonstrate timing utility"""
    print("⏱️  Demo: Timing")
    print("-" * 40)
    
    # Create a slow operation
    async def slow_operation(ctx: Ctx) -> Ctx:
        import time
        time.sleep(0.1)  # Simulate slow operation
        return {**ctx, 'slow_completed': True}
    
    # Wrap with timing
    timed_operation = timing(slow_operation)
    
    # Create timed chain
    timed_chain = chain(
        timing(validate_input),
        timing(normalize_data),
        timed_operation
    )
    
    ctx: Ctx = {
        'data': {'name': 'Timed User', 'email': 'timed@example.com'},
        'request_id': 'demo-006'
    }
    
    result = await timed_chain(ctx)
    
    print(f"Result: {result.get('data')}")
    print(f"Timing info: {result.get('timing', {})}")
    print()

async def main():
    """Run all demos"""
    print("ModuLink Python - Basic Example (Universal Types)")
    print("=" * 60)
    print()
    
    await demo_successful_flow()
    await demo_validation_errors()
    await demo_with_middleware()
    await demo_error_handling()
    await demo_conditional_processing()
    await demo_timing()
    
    print("✨ All demos completed!")
    print("\n💡 Try other universal examples:")
    print("  python examples/basic_universal.py")
    print("  python examples/simple_universal.py")

if __name__ == "__main__":
    asyncio.run(main())
