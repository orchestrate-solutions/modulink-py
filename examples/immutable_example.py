"""
Immutable ModuLink Example - Universal Types System

This example demonstrates immutable patterns using the universal types system:
- Pure functional transformations with immutable contexts
- Error handling without mutating original context
- Comparison between different transformation approaches
- Functional composition patterns
"""

from modulink import Ctx, chain, when, catch_errors
import asyncio
from datetime import datetime
import json

# ===== IMMUTABLE PATTERN FUNCTIONS =====

async def validate_input_immutable(ctx: Ctx) -> Ctx:
    """Validate input using immutable pattern"""
    print("🔍 Validating input (immutable)...")
    
    data = ctx.get('data', {})
    errors = []
    
    if not data.get('name'):
        errors.append({'message': 'Name is required', 'code': 'VALIDATION_ERROR'})
    
    if not data.get('email'):
        errors.append({'message': 'Email is required', 'code': 'VALIDATION_ERROR'})
    
    # Return new context with validation results
    return {
        **ctx,
        'errors': ctx.get('errors', []) + errors,
        'validation_completed': True,
        'validation_timestamp': datetime.utcnow().isoformat()
    }

async def normalize_data_immutable(ctx: Ctx) -> Ctx:
    """Normalize data using immutable pattern"""
    if ctx.get('errors'):
        return ctx  # Pass through unchanged if there are errors
    
    print("🧹 Normalizing data (immutable)...")
    
    data = ctx.get('data', {})
    
    # Create normalized data without mutating original
    normalized_data = {
        **data,
        'name': data.get('name', '').strip().title(),
        'email': data.get('email', '').strip().lower(),
        'normalized_at': datetime.utcnow().isoformat()
    }
    
    # Return new context with normalized data
    return {
        **ctx,
        'data': normalized_data,
        'normalization_completed': True
    }

async def enrich_data_immutable(ctx: Ctx) -> Ctx:
    """Enrich data using immutable pattern"""
    if ctx.get('errors'):
        return ctx
    
    print("✨ Enriching data (immutable)...")
    
    data = ctx.get('data', {})
    email = data.get('email', '')
    
    # Extract domain from email
    domain = email.split('@')[1] if '@' in email else 'unknown'
    
    # Create enriched data
    enriched_data = {
        **data,
        'domain': domain,
        'greeting': f"Hello, {data.get('name', 'there')}!",
        'user_info': {
            'domain_type': 'business' if domain.endswith('.com') else 'other',
            'email_length': len(email),
            'name_length': len(data.get('name', ''))
        },
        'enriched_at': datetime.utcnow().isoformat()
    }
    
    return {
        **ctx,
        'data': enriched_data,
        'enrichment_completed': True
    }

async def save_result_immutable(ctx: Ctx) -> Ctx:
    """Save result using immutable pattern"""
    if ctx.get('errors'):
        return ctx
    
    print("💾 Saving result (immutable)...")
    
    data = ctx.get('data', {})
    
    # Create save metadata
    save_metadata = {
        'saved': True,
        'id': hash(json.dumps(data, sort_keys=True)) % 100000,  # Simulated ID
        'saved_at': datetime.utcnow().isoformat(),
        'save_method': 'immutable_pattern'
    }
    
    print(f"✅ [Immutable] Saved user: {data.get('name')} ({data.get('email')})")
    
    return {
        **ctx,
        'data': {**data, **save_metadata},
        'save_completed': True
    }

# ===== FUNCTIONAL COMPOSITION HELPERS =====

def create_user_processor():
    """Create a user processing pipeline using immutable functions"""
    return chain(
        validate_input_immutable,
        normalize_data_immutable,
        enrich_data_immutable,
        save_result_immutable
    )

def create_conditional_processor():
    """Create a processor with conditional enrichment"""
    
    async def premium_enrichment(ctx: Ctx) -> Ctx:
        data = ctx.get('data', {})
        return {
            **ctx,
            'data': {
                **data,
                'premium_features': ['priority_support', 'advanced_analytics', 'custom_domain'],
                'account_tier': 'premium',
                'premium_since': datetime.utcnow().isoformat()
            }
        }
    
    # Apply premium enrichment only for premium users
    conditional_enrichment = when(
        lambda ctx: ctx.get('data', {}).get('user_type') == 'premium',
        premium_enrichment
    )
    
    return chain(
        validate_input_immutable,
        normalize_data_immutable,
        enrich_data_immutable,
        conditional_enrichment,
        save_result_immutable
    )

# ===== COMPARISON FUNCTIONS =====

async def mutable_style_processor(ctx: Ctx) -> Ctx:
    """Example of mutable-style processing for comparison"""
    print("⚠️  Processing with mutable style...")
    
    # This modifies the context directly (not recommended in universal types)
    data = ctx.get('data', {}).copy()  # At least copy the data
    errors = ctx.get('errors', []).copy()
    
    # Validation
    if not data.get('name'):
        errors.append({'message': 'Name is required', 'code': 'VALIDATION_ERROR'})
    if not data.get('email'):
        errors.append({'message': 'Email is required', 'code': 'VALIDATION_ERROR'})
    
    if not errors:
        # Normalization
        data['name'] = data['name'].strip().title()
        data['email'] = data['email'].strip().lower()
        
        # Enrichment
        domain = data['email'].split('@')[1] if '@' in data['email'] else 'unknown'
        data['domain'] = domain
        data['greeting'] = f"Hello, {data['name']}!"
        
        # Save simulation
        data['saved'] = True
        data['id'] = 54321
        data['processed_with'] = 'mutable_style'
    
    return {**ctx, 'data': data, 'errors': errors}

# ===== DEMONSTRATION FUNCTIONS =====

async def demo_immutable_processing():
    """Demonstrate immutable processing patterns"""
    print("🔒 Demo: Immutable Processing")
    print("-" * 50)
    
    # Create processor
    processor = create_user_processor()
    
    # Test with valid data
    original_ctx: Ctx = {
        'data': {
            'name': '  john doe  ',
            'email': '  JOHN.DOE@EXAMPLE.COM  '
        },
        'request_id': 'immutable-001',
        'source': 'demo'
    }
    
    print(f"Original context: {original_ctx}")
    print(f"Original context ID: {id(original_ctx)}")
    
    # Process immutably
    result = await processor(original_ctx)
    
    print(f"\nResult context: {result.get('data')}")
    print(f"Result context ID: {id(result)}")
    print(f"Original context unchanged: {original_ctx}")
    print(f"Contexts are different objects: {id(original_ctx) != id(result)}")
    print(f"Processing steps: {[k for k in result.keys() if k.endswith('_completed')]}")
    print()

async def demo_error_handling():
    """Demonstrate error handling with immutable patterns"""
    print("❌ Demo: Error Handling (Immutable)")
    print("-" * 50)
    
    processor = create_user_processor()
    
    # Test with invalid data
    ctx_with_errors: Ctx = {
        'data': {
            'name': '',  # Invalid
            'email': 'invalid-email'  # Invalid
        },
        'request_id': 'immutable-002'
    }
    
    result = await processor(ctx_with_errors)
    
    print(f"Input: {ctx_with_errors['data']}")
    print(f"Errors: {result.get('errors', [])}")
    print(f"Processing stopped early: {not result.get('save_completed', False)}")
    print(f"Validation completed: {result.get('validation_completed', False)}")
    print()

async def demo_conditional_processing():
    """Demonstrate conditional processing with immutable patterns"""
    print("🔀 Demo: Conditional Processing (Immutable)")
    print("-" * 50)
    
    conditional_processor = create_conditional_processor()
    
    # Test with regular user
    regular_user: Ctx = {
        'data': {
            'name': 'Regular User',
            'email': 'regular@example.com',
            'user_type': 'regular'
        },
        'request_id': 'conditional-001'
    }
    
    # Test with premium user
    premium_user: Ctx = {
        'data': {
            'name': 'Premium User',
            'email': 'premium@example.com',
            'user_type': 'premium'
        },
        'request_id': 'conditional-002'
    }
    
    regular_result = await conditional_processor(regular_user)
    premium_result = await conditional_processor(premium_user)
    
    print("Regular user result:")
    print(f"  Premium features: {regular_result.get('data', {}).get('premium_features', 'None')}")
    print(f"  Account tier: {regular_result.get('data', {}).get('account_tier', 'regular')}")
    
    print("\nPremium user result:")
    print(f"  Premium features: {premium_result.get('data', {}).get('premium_features', 'None')}")
    print(f"  Account tier: {premium_result.get('data', {}).get('account_tier', 'regular')}")
    print()

async def demo_functional_composition():
    """Demonstrate functional composition patterns"""
    print("🔧 Demo: Functional Composition")
    print("-" * 50)
    
    # Create different processors by composing functions differently
    validator_only = chain(validate_input_immutable)
    normalizer_only = chain(normalize_data_immutable)
    validator_normalizer = chain(validate_input_immutable, normalize_data_immutable)
    
    ctx: Ctx = {
        'data': {'name': '  alice  ', 'email': '  ALICE@TEST.COM  '},
        'request_id': 'composition-001'
    }
    
    # Test different compositions
    validation_result = await validator_only(ctx)
    print(f"Validation only: {validation_result.get('validation_completed', False)}")
    
    # Note: normalizer_only would skip if there are errors, so we use a clean context
    clean_ctx = {**ctx, 'errors': []}
    normalization_result = await normalizer_only(clean_ctx)
    print(f"Normalization only: {normalization_result.get('normalization_completed', False)}")
    
    combined_result = await validator_normalizer(ctx)
    print(f"Combined: validation={combined_result.get('validation_completed', False)}, normalization={combined_result.get('normalization_completed', False)}")
    print()

async def demo_comparison():
    """Compare immutable vs mutable-style processing"""
    print("⚖️  Demo: Immutable vs Mutable Style Comparison")
    print("-" * 50)
    
    ctx: Ctx = {
        'data': {'name': '  comparison test  ', 'email': '  TEST@EXAMPLE.COM  '},
        'request_id': 'comparison-001'
    }
    
    # Immutable processing
    immutable_processor = create_user_processor()
    immutable_result = await immutable_processor(ctx)
    
    # Mutable-style processing
    mutable_result = await mutable_style_processor(ctx)
    
    print("Immutable style result:")
    print(f"  Data: {immutable_result.get('data', {})}")
    print(f"  Processing metadata preserved: {[k for k in immutable_result.keys() if k.endswith('_completed')]}")
    
    print("\nMutable style result:")
    print(f"  Data: {mutable_result.get('data', {})}")
    print(f"  Processing metadata preserved: {[k for k in mutable_result.keys() if k.endswith('_completed')]}")
    
    print(f"\nOriginal context preserved: {ctx}")
    print()

async def demo_error_recovery():
    """Demonstrate error recovery patterns"""
    print("🛡️  Demo: Error Recovery Patterns")
    print("-" * 50)
    
    # Create a processor with error handling
    async def safe_processor(ctx: Ctx) -> Ctx:
        """Processor that handles errors gracefully"""
        
        # Try validation first
        validated = await validate_input_immutable(ctx)
        
        # If validation fails, provide default values and continue
        if validated.get('errors'):
            print("⚠️  Validation failed, applying defaults...")
            default_data = {
                'name': 'Anonymous User',
                'email': 'anonymous@example.com',
                'source': 'error_recovery'
            }
            
            # Clear errors and use defaults
            recovery_ctx = {
                **validated,
                'data': {**validated.get('data', {}), **default_data},
                'errors': [],  # Clear errors to continue processing
                'recovery_applied': True
            }
            
            # Continue with rest of pipeline
            return await chain(
                normalize_data_immutable,
                enrich_data_immutable,
                save_result_immutable
            )(recovery_ctx)
        
        # If validation passes, continue normally
        return await chain(
            normalize_data_immutable,
            enrich_data_immutable,
            save_result_immutable
        )(validated)
    
    # Test with invalid data
    invalid_ctx: Ctx = {
        'data': {'name': '', 'email': ''},  # Invalid data
        'request_id': 'recovery-001'
    }
    
    result = await safe_processor(invalid_ctx)
    
    print(f"Input: {invalid_ctx['data']}")
    print(f"Result: {result.get('data', {})}")
    print(f"Recovery applied: {result.get('recovery_applied', False)}")
    print(f"Processing completed: {result.get('save_completed', False)}")
    print()

async def main():
    """Run all immutable pattern demonstrations"""
    print("ModuLink Python - Immutable Patterns (Universal Types)")
    print("=" * 70)
    print()
    
    await demo_immutable_processing()
    await demo_error_handling()
    await demo_conditional_processing()
    await demo_functional_composition()
    await demo_comparison()
    await demo_error_recovery()
    
    print("✨ All immutable pattern demos completed!")
    print("\n💡 Key benefits of immutable patterns:")
    print("  - Predictable function behavior")
    print("  - Easy testing and debugging")
    print("  - Safe parallel processing")
    print("  - Clear data flow tracking")
    print("  - No side effects")

if __name__ == "__main__":
    asyncio.run(main())
