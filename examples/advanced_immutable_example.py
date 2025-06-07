"""
Advanced Immutable ModuLink Example - Universal Types System

This example demonstrates advanced immutable patterns using universal types:
- Complex functional composition and transformation chains
- Advanced error handling and recovery strategies
- Parallel processing with immutable contexts
- Context branching and merging patterns
- Performance optimizations with immutable data
"""

from modulink import Ctx, chain, when, catch_errors, timing, parallel
import asyncio
from datetime import datetime
import json
from typing import List, Dict, Any
import uuid

# ===== ADVANCED IMMUTABLE TRANSFORMATIONS =====

async def create_processing_context(ctx: Ctx) -> Ctx:
    """Create enhanced processing context with metadata"""
    processing_id = str(uuid.uuid4())
    
    return {
        **ctx,
        'processing_id': processing_id,
        'processing_started_at': datetime.utcnow().isoformat(),
        'pipeline_version': '2.0.0',
        'stage': 'initialization',
        'context_created': True
    }

async def validate_complex_input(ctx: Ctx) -> Ctx:
    """Advanced validation with detailed error tracking"""
    print(f"🔍 Complex validation for {ctx.get('processing_id', 'unknown')}")
    
    data = ctx.get('data', {})
    validation_errors = []
    validation_warnings = []
    
    # Required field validation
    required_fields = ['name', 'email', 'age']
    for field in required_fields:
        if not data.get(field):
            validation_errors.append({
                'field': field,
                'message': f'{field.title()} is required',
                'code': f'MISSING_{field.upper()}',
                'severity': 'error'
            })
    
    # Format validation
    if data.get('email') and '@' not in data['email']:
        validation_errors.append({
            'field': 'email',
            'message': 'Invalid email format',
            'code': 'INVALID_EMAIL',
            'severity': 'error'
        })
    
    # Business rule validation
    if data.get('age') and (not isinstance(data['age'], int) or data['age'] < 0 or data['age'] > 150):
        validation_errors.append({
            'field': 'age',
            'message': 'Age must be between 0 and 150',
            'code': 'INVALID_AGE',
            'severity': 'error'
        })
    
    # Warning-level validations
    if data.get('age') and data['age'] < 18:
        validation_warnings.append({
            'field': 'age',
            'message': 'User is under 18',
            'code': 'MINOR_USER',
            'severity': 'warning'
        })
    
    return {
        **ctx,
        'validation_errors': validation_errors,
        'validation_warnings': validation_warnings,
        'validation_completed': True,
        'stage': 'validation'
    }

async def enrich_with_external_data(ctx: Ctx) -> Ctx:
    """Simulate enrichment with external API data"""
    if ctx.get('validation_errors'):
        return ctx
    
    print(f"🌐 Enriching with external data for {ctx.get('processing_id')}")
    
    data = ctx.get('data', {})
    
    # Simulate API calls for enrichment
    await asyncio.sleep(0.1)  # Simulate network delay
    
    # Mock external data based on email domain
    email = data.get('email', '')
    domain = email.split('@')[1] if '@' in email else 'unknown'
    
    # Simulate company data lookup
    company_data = {
        'example.com': {'company': 'Example Corp', 'industry': 'Technology', 'size': 'Large'},
        'test.com': {'company': 'Test Inc', 'industry': 'Testing', 'size': 'Medium'},
        'gmail.com': {'company': 'Personal', 'industry': 'Consumer', 'size': 'Individual'},
    }.get(domain, {'company': 'Unknown', 'industry': 'Unknown', 'size': 'Unknown'})
    
    # Simulate geo data lookup
    geo_data = {
        'country': 'US',
        'timezone': 'UTC-8',
        'region': 'California'
    }
    
    enriched_data = {
        **data,
        'company_info': company_data,
        'geo_info': geo_data,
        'enrichment_sources': ['company_api', 'geo_api'],
        'enriched_at': datetime.utcnow().isoformat()
    }
    
    return {
        **ctx,
        'data': enriched_data,
        'external_enrichment_completed': True,
        'stage': 'enrichment'
    }

async def calculate_user_score(ctx: Ctx) -> Ctx:
    """Calculate user score based on various factors"""
    if ctx.get('validation_errors'):
        return ctx
    
    print(f"📊 Calculating user score for {ctx.get('processing_id')}")
    
    data = ctx.get('data', {})
    
    # Base score calculation
    score = 50  # Base score
    
    # Age factor
    age = data.get('age', 0)
    if 18 <= age <= 65:
        score += 20
    elif age > 65:
        score += 10
    
    # Email domain factor
    email = data.get('email', '')
    if email.endswith('.edu'):
        score += 15  # Educational institution
    elif email.endswith('.gov'):
        score += 20  # Government
    elif email.endswith('.com'):
        score += 10  # Commercial
    
    # Company size factor
    company_size = data.get('company_info', {}).get('size', 'Unknown')
    size_scores = {'Large': 15, 'Medium': 10, 'Small': 5, 'Individual': 0}
    score += size_scores.get(company_size, 0)
    
    # Industry factor
    industry = data.get('company_info', {}).get('industry', 'Unknown')
    industry_scores = {'Technology': 15, 'Finance': 12, 'Healthcare': 10, 'Education': 8}
    score += industry_scores.get(industry, 0)
    
    # Warnings penalty
    warnings_count = len(ctx.get('validation_warnings', []))
    score -= warnings_count * 5
    
    # Ensure score is in valid range
    score = max(0, min(100, score))
    
    score_data = {
        'user_score': score,
        'score_factors': {
            'age_bonus': 20 if 18 <= age <= 65 else (10 if age > 65 else 0),
            'email_bonus': 15 if email.endswith('.edu') else (20 if email.endswith('.gov') else (10 if email.endswith('.com') else 0)),
            'company_bonus': size_scores.get(company_size, 0),
            'industry_bonus': industry_scores.get(industry, 0),
            'warnings_penalty': warnings_count * 5
        },
        'score_calculated_at': datetime.utcnow().isoformat()
    }
    
    return {
        **ctx,
        'data': {**data, **score_data},
        'score_calculation_completed': True,
        'stage': 'scoring'
    }

async def generate_recommendations(ctx: Ctx) -> Ctx:
    """Generate personalized recommendations"""
    if ctx.get('validation_errors'):
        return ctx
    
    print(f"💡 Generating recommendations for {ctx.get('processing_id')}")
    
    data = ctx.get('data', {})
    score = data.get('user_score', 0)
    age = data.get('age', 0)
    industry = data.get('company_info', {}).get('industry', 'Unknown')
    
    recommendations = []
    
    # Score-based recommendations
    if score >= 80:
        recommendations.append({
            'type': 'premium_upgrade',
            'message': 'You qualify for our premium features!',
            'priority': 'high'
        })
    elif score >= 60:
        recommendations.append({
            'type': 'feature_suggestion',
            'message': 'Try our advanced analytics tools',
            'priority': 'medium'
        })
    else:
        recommendations.append({
            'type': 'onboarding',
            'message': 'Complete your profile for better recommendations',
            'priority': 'high'
        })
    
    # Age-based recommendations
    if age < 25:
        recommendations.append({
            'type': 'education',
            'message': 'Check out our student discount program',
            'priority': 'medium'
        })
    elif age > 50:
        recommendations.append({
            'type': 'accessibility',
            'message': 'Enable large font mode for better readability',
            'priority': 'low'
        })
    
    # Industry-based recommendations
    if industry == 'Technology':
        recommendations.append({
            'type': 'integration',
            'message': 'Connect with your development tools',
            'priority': 'medium'
        })
    elif industry == 'Finance':
        recommendations.append({
            'type': 'security',
            'message': 'Enable two-factor authentication',
            'priority': 'high'
        })
    
    return {
        **ctx,
        'data': {**data, 'recommendations': recommendations},
        'recommendations_generated': True,
        'stage': 'recommendations'
    }

async def finalize_processing(ctx: Ctx) -> Ctx:
    """Finalize processing with summary and cleanup"""
    print(f"🏁 Finalizing processing for {ctx.get('processing_id')}")
    
    processing_summary = {
        'processing_id': ctx.get('processing_id'),
        'started_at': ctx.get('processing_started_at'),
        'completed_at': datetime.utcnow().isoformat(),
        'stages_completed': [k.replace('_completed', '').replace('_', ' ').title() 
                           for k in ctx.keys() if k.endswith('_completed')],
        'errors_count': len(ctx.get('validation_errors', [])),
        'warnings_count': len(ctx.get('validation_warnings', [])),
        'final_score': ctx.get('data', {}).get('user_score', 0),
        'recommendations_count': len(ctx.get('data', {}).get('recommendations', [])),
        'status': 'error' if ctx.get('validation_errors') else 'success'
    }
    
    return {
        **ctx,
        'processing_summary': processing_summary,
        'processing_completed': True,
        'stage': 'completed'
    }

# ===== BRANCHING AND PARALLEL PROCESSING =====

async def create_user_profiles(ctx: Ctx) -> Ctx:
    """Create multiple user profiles in parallel"""
    if ctx.get('validation_errors'):
        return ctx
    
    print(f"👥 Creating user profiles for {ctx.get('processing_id')}")
    
    data = ctx.get('data', {})
    
    # Create different profile views in parallel
    async def create_public_profile(user_data: Dict) -> Dict:
        await asyncio.sleep(0.05)  # Simulate processing
        return {
            'type': 'public',
            'name': user_data.get('name'),
            'company': user_data.get('company_info', {}).get('company', 'Unknown'),
            'industry': user_data.get('company_info', {}).get('industry', 'Unknown'),
            'created_at': datetime.utcnow().isoformat()
        }
    
    async def create_private_profile(user_data: Dict) -> Dict:
        await asyncio.sleep(0.07)  # Simulate processing
        return {
            'type': 'private',
            'name': user_data.get('name'),
            'email': user_data.get('email'),
            'age': user_data.get('age'),
            'score': user_data.get('user_score'),
            'geo_info': user_data.get('geo_info'),
            'created_at': datetime.utcnow().isoformat()
        }
    
    async def create_analytics_profile(user_data: Dict) -> Dict:
        await asyncio.sleep(0.03)  # Simulate processing
        return {
            'type': 'analytics',
            'user_id': hash(user_data.get('email', '')) % 1000000,
            'score': user_data.get('user_score'),
            'score_factors': user_data.get('score_factors', {}),
            'recommendations_count': len(user_data.get('recommendations', [])),
            'processing_time': datetime.utcnow().isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }
    
    # Create profiles in parallel
    public_task = create_public_profile(data)
    private_task = create_private_profile(data)
    analytics_task = create_analytics_profile(data)
    
    public_profile, private_profile, analytics_profile = await asyncio.gather(
        public_task, private_task, analytics_task
    )
    
    profiles = {
        'public': public_profile,
        'private': private_profile,
        'analytics': analytics_profile
    }
    
    return {
        **ctx,
        'data': {**data, 'profiles': profiles},
        'profiles_created': True,
        'stage': 'profiles'
    }

# ===== COMPLEX PIPELINE COMPOSITIONS =====

def create_advanced_pipeline():
    """Create an advanced processing pipeline"""
    return chain(
        timing(create_processing_context),
        timing(validate_complex_input),
        timing(enrich_with_external_data),
        timing(calculate_user_score),
        timing(generate_recommendations),
        timing(create_user_profiles),
        timing(finalize_processing)
    )

def create_error_recovery_pipeline():
    """Create a pipeline with advanced error recovery"""
    
    async def error_recovery_wrapper(pipeline_func):
        """Wrapper that provides error recovery"""
        async def wrapper(ctx: Ctx) -> Ctx:
            try:
                return await pipeline_func(ctx)
            except Exception as e:
                print(f"⚠️  Error in pipeline: {e}")
                return {
                    **ctx,
                    'pipeline_error': {
                        'message': str(e),
                        'type': type(e).__name__,
                        'occurred_at': datetime.utcnow().isoformat()
                    }
                }
        return wrapper
    
    # Wrap each stage with error recovery
    return chain(
        catch_errors(create_processing_context),
        catch_errors(validate_complex_input),
        catch_errors(enrich_with_external_data),
        catch_errors(calculate_user_score),
        catch_errors(generate_recommendations),
        catch_errors(create_user_profiles),
        catch_errors(finalize_processing)
    )

def create_conditional_pipeline():
    """Create a pipeline with conditional processing branches"""
    
    # High-priority processing for premium users
    premium_pipeline = chain(
        enrich_with_external_data,
        calculate_user_score,
        generate_recommendations,
        create_user_profiles
    )
    
    # Basic processing for regular users
    basic_pipeline = chain(
        calculate_user_score,
        generate_recommendations
    )
    
    # Conditional processor - manually implement conditional logic
    async def conditional_processor(ctx: Ctx) -> Ctx:
        if ctx.get('data', {}).get('user_type') == 'premium':
            return await premium_pipeline(ctx)
        else:
            return await basic_pipeline(ctx)
    
    return chain(
        create_processing_context,
        validate_complex_input,
        conditional_processor,
        finalize_processing
    )

# ===== DEMONSTRATION FUNCTIONS =====

async def demo_advanced_processing():
    """Demonstrate advanced processing pipeline"""
    print("🚀 Demo: Advanced Processing Pipeline")
    print("-" * 60)
    
    pipeline = create_advanced_pipeline()
    
    ctx: Ctx = {
        'data': {
            'name': 'Alice Johnson',
            'email': 'alice.johnson@example.com',
            'age': 28,
            'user_type': 'premium'
        },
        'source': 'advanced_demo'
    }
    
    result = await pipeline(ctx)
    
    # Display results
    summary = result.get('processing_summary', {})
    print(f"Processing ID: {summary.get('processing_id')}")
    print(f"Status: {summary.get('status')}")
    print(f"Stages completed: {len(summary.get('stages_completed', []))}")
    print(f"Final score: {summary.get('final_score')}")
    print(f"Recommendations: {summary.get('recommendations_count')}")
    
    # Show timing information
    timing_info = result.get('timing', {})
    if timing_info:
        print(f"\nTiming information:")
        for stage, duration in timing_info.items():
            print(f"  {stage}: {duration:.3f}s")
    
    print()

async def demo_error_recovery():
    """Demonstrate error recovery patterns"""
    print("🛡️  Demo: Error Recovery Pipeline")
    print("-" * 60)
    
    recovery_pipeline = create_error_recovery_pipeline()
    
    # Test with invalid data that will cause errors
    ctx: Ctx = {
        'data': {
            'name': '',  # Missing required field
            'email': 'invalid-email',  # Invalid format
            'age': -5  # Invalid age
        },
        'source': 'error_demo'
    }
    
    result = await recovery_pipeline(ctx)
    
    # Check error handling
    validation_errors = result.get('validation_errors', [])
    pipeline_error = result.get('pipeline_error')
    
    print(f"Validation errors: {len(validation_errors)}")
    for error in validation_errors:
        print(f"  - {error['field']}: {error['message']}")
    
    if pipeline_error:
        print(f"Pipeline error: {pipeline_error['message']}")
    
    print(f"Processing completed despite errors: {result.get('processing_completed', False)}")
    print()

async def demo_conditional_processing():
    """Demonstrate conditional processing branches"""
    print("🔀 Demo: Conditional Processing Branches")
    print("-" * 60)
    
    conditional_pipeline = create_conditional_pipeline()
    
    # Test with premium user
    premium_ctx: Ctx = {
        'data': {
            'name': 'Premium User',
            'email': 'premium@example.com',
            'age': 35,
            'user_type': 'premium'
        }
    }
    
    # Test with regular user
    regular_ctx: Ctx = {
        'data': {
            'name': 'Regular User',
            'email': 'regular@example.com',
            'age': 25,
            'user_type': 'regular'
        }
    }
    
    premium_result = await conditional_pipeline(premium_ctx)
    regular_result = await conditional_pipeline(regular_ctx)
    
    print("Premium user processing:")
    premium_summary = premium_result.get('processing_summary', {})
    print(f"  Stages: {len(premium_summary.get('stages_completed', []))}")
    print(f"  External enrichment: {premium_result.get('external_enrichment_completed', False)}")
    print(f"  Profiles created: {premium_result.get('profiles_created', False)}")
    
    print("\nRegular user processing:")
    regular_summary = regular_result.get('processing_summary', {})
    print(f"  Stages: {len(regular_summary.get('stages_completed', []))}")
    print(f"  External enrichment: {regular_result.get('external_enrichment_completed', False)}")
    print(f"  Profiles created: {regular_result.get('profiles_created', False)}")
    print()

async def demo_parallel_processing():
    """Demonstrate parallel processing capabilities"""
    print("⚡ Demo: Parallel Processing")
    print("-" * 60)
    
    # Create multiple contexts to process in parallel
    contexts = [
        {'data': {'name': f'User {i}', 'email': f'user{i}@example.com', 'age': 20 + i}, 'batch_id': i}
        for i in range(1, 6)
    ]
    
    pipeline = create_advanced_pipeline()
    
    print(f"Processing {len(contexts)} users in parallel...")
    start_time = datetime.utcnow()
    
    # Process all contexts in parallel
    results = await asyncio.gather(*[pipeline(ctx) for ctx in contexts])
    
    end_time = datetime.utcnow()
    total_time = (end_time - start_time).total_seconds()
    
    print(f"Parallel processing completed in {total_time:.2f}s")
    print(f"Average time per user: {total_time / len(contexts):.2f}s")
    
    # Show results summary
    for i, result in enumerate(results, 1):
        summary = result.get('processing_summary', {})
        print(f"  User {i}: {summary.get('status', 'unknown')} (score: {summary.get('final_score', 0)})")
    
    print()

async def demo_context_branching():
    """Demonstrate context branching and merging patterns"""
    print("🌳 Demo: Context Branching and Merging")
    print("-" * 60)
    
    # Create a pipeline that branches context into multiple processing paths
    async def branch_and_merge(ctx: Ctx) -> Ctx:
        """Branch context into multiple processing paths and merge results"""
        
        data = ctx.get('data', {})
        
        # Branch 1: Personal processing
        personal_ctx = {**ctx, 'branch': 'personal'}
        personal_result = await chain(
            calculate_user_score,
            generate_recommendations
        )(personal_ctx)
        
        # Branch 2: Business processing  
        business_ctx = {**ctx, 'branch': 'business'}
        business_result = await chain(
            enrich_with_external_data,
            create_user_profiles
        )(business_ctx)
        
        # Merge results
        merged_data = {
            **data,
            'personal_score': personal_result.get('data', {}).get('user_score'),
            'personal_recommendations': personal_result.get('data', {}).get('recommendations', []),
            'business_profiles': business_result.get('data', {}).get('profiles', {}),
            'company_info': business_result.get('data', {}).get('company_info', {}),
            'branch_processing_completed': True
        }
        
        return {
            **ctx,
            'data': merged_data,
            'branches_processed': ['personal', 'business'],
            'merge_completed': True
        }
    
    branching_pipeline = chain(
        create_processing_context,
        validate_complex_input,
        branch_and_merge,
        finalize_processing
    )
    
    ctx: Ctx = {
        'data': {
            'name': 'Branching Test User',
            'email': 'branch@example.com',
            'age': 30
        }
    }
    
    result = await branching_pipeline(ctx)
    
    print(f"Branches processed: {result.get('branches_processed', [])}")
    print(f"Personal score: {result.get('data', {}).get('personal_score')}")
    print(f"Business profiles: {list(result.get('data', {}).get('business_profiles', {}).keys())}")
    print(f"Merge completed: {result.get('merge_completed', False)}")
    print()

async def main():
    """Run all advanced immutable pattern demonstrations"""
    print("ModuLink Python - Advanced Immutable Patterns (Universal Types)")
    print("=" * 80)
    print()
    
    await demo_advanced_processing()
    await demo_error_recovery()
    await demo_conditional_processing()
    await demo_parallel_processing()
    await demo_context_branching()
    
    print("✨ All advanced immutable pattern demos completed!")
    print("\n💡 Advanced patterns demonstrated:")
    print("  - Complex functional composition")
    print("  - Error recovery and resilience")
    print("  - Conditional processing branches")
    print("  - Parallel processing capabilities")
    print("  - Context branching and merging")
    print("  - Performance timing and monitoring")

if __name__ == "__main__":
    asyncio.run(main())
