# ModuLink Patterns Cookbook - Beginner's Guide

## Overview

This cookbook teaches you the fundamental patterns and design principles for building maintainable ModuLink applications. Perfect for developers new to chain-based architecture or those wanting to establish solid foundations.

## Table of Contents

1. [Core Design Principles](#core-design-principles)
2. [Function Design Patterns](#function-design-patterns)
3. [Basic Chain Composition](#basic-chain-composition)
4. [Context Flow Management](#context-flow-management)
5. [Simple Error Handling](#simple-error-handling)
6. [Code Organization](#code-organization)
7. [Best Practices](#best-practices)

## Core Design Principles

### Principle 1: Single Responsibility
Each function should have one clear purpose and do it well.

```python
# ✅ Good - Single responsibility
async def validate_user_email(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user email format and domain."""
    email = ctx_data.get('user_data', {}).get('email', '')
    
    if not email:
        return {**ctx_data, 'email_error': 'Email is required'}
    
    if '@' not in email or '.' not in email.split('@')[-1]:
        return {**ctx_data, 'email_error': 'Invalid email format'}
    
    return {**ctx_data, 'email_valid': True}

# ❌ Bad - Multiple responsibilities
async def validate_and_save_user(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validates user data AND saves to database."""
    # Don't mix validation and persistence!
    pass
```

### Principle 2: Immutable Context
Never modify the input context directly - always return a new context.

```python
# ✅ Good - Creates new context
async def add_timestamp(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add current timestamp to context."""
    result = ctx_data.copy()  # Create a copy
    result['timestamp'] = datetime.now().isoformat()
    return result

# ✅ Also good - Using dict unpacking
async def add_user_id(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate and add user ID."""
    return {
        **ctx_data,  # Spread existing data
        'user_id': f"user_{uuid.uuid4().hex[:8]}"
    }

# ❌ Bad - Mutates input
async def bad_add_timestamp(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    ctx_data['timestamp'] = datetime.now()  # Don't modify input!
    return ctx_data
```

### Principle 3: Predictable Data Flow
Functions should be pure and predictable - same input produces same output.

```python
# ✅ Good - Pure function
async def calculate_order_total(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate order total from items."""
    items = ctx_data.get('order_items', [])
    
    total = sum(
        item.get('price', 0) * item.get('quantity', 0) 
        for item in items
    )
    
    return {
        **ctx_data,
        'order_total': total,
        'tax_amount': total * 0.08,  # 8% tax
        'final_total': total * 1.08
    }

# ❌ Bad - Depends on external state
current_discount = 0.1  # Global variable

async def bad_calculate_total(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    # Don't depend on global state!
    total = calculate_base_total(ctx_data)
    return {**ctx_data, 'total': total * (1 - current_discount)}
```

## Function Design Patterns

### Pattern 1: Validator Functions
Functions that check data validity and add validation results.

```python
async def validate_order_items(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate order items are present and valid."""
    items = ctx_data.get('order_items', [])
    errors = []
    
    if not items:
        errors.append("Order must contain at least one item")
    
    for i, item in enumerate(items):
        if not item.get('product_id'):
            errors.append(f"Item {i+1}: Product ID is required")
        
        if item.get('quantity', 0) <= 0:
            errors.append(f"Item {i+1}: Quantity must be positive")
        
        if item.get('price', 0) <= 0:
            errors.append(f"Item {i+1}: Price must be positive")
    
    return {
        **ctx_data,
        'items_valid': len(errors) == 0,
        'validation_errors': errors
    }
```

### Pattern 2: Transformer Functions
Functions that convert or enhance data.

```python
async def normalize_user_data(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize user input data."""
    user_data = ctx_data.get('user_data', {})
    
    normalized = {
        'email': user_data.get('email', '').lower().strip(),
        'first_name': user_data.get('first_name', '').strip().title(),
        'last_name': user_data.get('last_name', '').strip().title(),
        'phone': ''.join(filter(str.isdigit, user_data.get('phone', '')))
    }
    
    return {
        **ctx_data,
        'user_data': normalized,
        'data_normalized': True
    }
```

### Pattern 3: Enricher Functions
Functions that add additional data from external sources.

```python
async def enrich_with_user_preferences(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add user preferences from profile service."""
    user_id = ctx_data.get('user_id')
    
    if not user_id:
        return {**ctx_data, 'preferences': {}}
    
    # In real app, this would call an external service
    preferences = {
        'language': 'en',
        'currency': 'USD',
        'notifications': True,
        'theme': 'light'
    }
    
    return {
        **ctx_data,
        'user_preferences': preferences,
        'preferences_loaded': True
    }
```

### Pattern 4: Guard Functions
Functions that check prerequisites and stop processing if not met.

```python
async def require_authenticated_user(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure user is authenticated before proceeding."""
    user_id = ctx_data.get('user_id')
    auth_token = ctx_data.get('auth_token')
    
    if not user_id or not auth_token:
        raise ValueError("Authentication required")
    
    # In real app, validate token here
    if not is_valid_token(auth_token):
        raise ValueError("Invalid authentication token")
    
    return {
        **ctx_data,
        'authentication_verified': True
    }

def is_valid_token(token: str) -> bool:
    """Mock token validation."""
    return token and len(token) > 10
```

## Basic Chain Composition

### Linear Chains
The simplest pattern - functions execute in sequence.

```python
from modulink import chain

# User registration workflow
user_registration = chain([
    validate_user_data,
    normalize_user_data,
    check_email_availability,
    create_user_account,
    send_welcome_email,
    add_to_newsletter
])

# Usage
initial_context = {
    'user_data': {
        'email': 'newuser@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'securepassword123'
    }
}

result = await user_registration(initial_context)
```

### Dependent Chains
Chains where later functions depend on earlier results.

```python
# Order processing workflow
order_processing = chain([
    validate_order_data,        # Must pass for next steps
    calculate_order_total,      # Needs validated data
    check_inventory_availability, # Needs order items
    reserve_inventory,          # Needs availability check
    process_payment,           # Needs total and reserved items
    create_order_record,       # Needs payment confirmation
    send_order_confirmation    # Needs order record
])
```

### Branching Chains
Using conditional logic within chains.

```python
async def choose_shipping_method(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Choose shipping method based on order value and user type."""
    order_total = ctx_data.get('order_total', 0)
    user_type = ctx_data.get('user_type', 'standard')
    
    if user_type == 'premium':
        shipping_method = 'express'
        shipping_cost = 0  # Free for premium users
    elif order_total > 100:
        shipping_method = 'standard'
        shipping_cost = 0  # Free shipping over $100
    else:
        shipping_method = 'standard'
        shipping_cost = 9.99
    
    return {
        **ctx_data,
        'shipping_method': shipping_method,
        'shipping_cost': shipping_cost
    }
```

## Context Flow Management

### Context Accumulation Pattern
How data builds up through a chain.

```python
async def step_one(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """First step adds initial data."""
    return {
        **ctx_data,
        'step_one_complete': True,
        'processing_started': datetime.now().isoformat()
    }

async def step_two(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Second step adds more data."""
    processing_started = ctx_data.get('processing_started')
    
    return {
        **ctx_data,
        'step_two_complete': True,
        'processing_duration': calculate_duration(processing_started),
        'validation_passed': True
    }

async def step_three(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Final step uses accumulated data."""
    return {
        **ctx_data,
        'step_three_complete': True,
        'total_steps': 3,
        'workflow_complete': True,
        'final_status': 'success'
    }

# Chain accumulates context data
workflow = chain([step_one, step_two, step_three])

result = await workflow({'user_id': '123'})
# Result contains all accumulated data:
# {
#   'user_id': '123',
#   'step_one_complete': True,
#   'processing_started': '...',
#   'step_two_complete': True,
#   'processing_duration': 0.1,
#   'validation_passed': True,
#   'step_three_complete': True,
#   'total_steps': 3,
#   'workflow_complete': True,
#   'final_status': 'success'
# }
```

### Context Cleaning Pattern
Sometimes you need to remove or filter context data.

```python
async def clean_sensitive_data(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive data before logging or returning."""
    # Create a copy without sensitive fields
    cleaned_data = {
        key: value for key, value in ctx_data.items()
        if key not in ['password', 'ssn', 'credit_card', 'auth_token']
    }
    
    # Mark as cleaned for audit purposes
    cleaned_data['sensitive_data_removed'] = True
    cleaned_data['cleaned_at'] = datetime.now().isoformat()
    
    return cleaned_data
```

## Simple Error Handling

### Try-Catch Pattern
Handle errors gracefully within functions.

```python
async def call_external_service(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Call external service with error handling."""
    try:
        # Simulate external service call
        response = await external_api_call(ctx_data.get('user_id'))
        
        return {
            **ctx_data,
            'external_data': response,
            'service_call_success': True
        }
        
    except ConnectionError:
        # Network issues - mark as retryable
        return {
            **ctx_data,
            'service_call_success': False,
            'error_type': 'connection',
            'retryable': True,
            'error_message': 'Service temporarily unavailable'
        }
        
    except ValueError as e:
        # Data issues - don't retry
        return {
            **ctx_data,
            'service_call_success': False,
            'error_type': 'validation',
            'retryable': False,
            'error_message': str(e)
        }

async def external_api_call(user_id: str) -> Dict[str, Any]:
    """Mock external API call."""
    import random
    if random.random() < 0.1:  # 10% failure rate
        raise ConnectionError("Service unavailable")
    return {'user_profile': {'id': user_id, 'status': 'active'}}
```

### Validation with Error Accumulation
Collect all errors instead of failing on the first one.

```python
async def comprehensive_validation(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform comprehensive validation and collect all errors."""
    user_data = ctx_data.get('user_data', {})
    errors = []
    warnings = []
    
    # Email validation
    email = user_data.get('email', '')
    if not email:
        errors.append("Email is required")
    elif '@' not in email:
        errors.append("Email must contain @ symbol")
    elif len(email) > 100:
        warnings.append("Email is unusually long")
    
    # Password validation
    password = user_data.get('password', '')
    if not password:
        errors.append("Password is required")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters")
    elif not any(c.isupper() for c in password):
        warnings.append("Password should contain uppercase letters")
    
    # Age validation
    age = user_data.get('age', 0)
    if age < 13:
        errors.append("Must be at least 13 years old")
    elif age > 120:
        warnings.append("Age seems unusually high")
    
    return {
        **ctx_data,
        'validation_errors': errors,
        'validation_warnings': warnings,
        'validation_passed': len(errors) == 0,
        'has_warnings': len(warnings) > 0
    }
```

### Graceful Degradation Pattern
Continue processing even when non-critical operations fail.

```python
async def optional_user_analytics(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Track user analytics - don't fail the main flow if this fails."""
    try:
        user_id = ctx_data.get('user_id')
        action = ctx_data.get('action', 'unknown')
        
        # Track the action (this might fail)
        await track_user_action(user_id, action)
        
        return {
            **ctx_data,
            'analytics_tracked': True
        }
        
    except Exception as e:
        # Log the error but don't fail the main flow
        print(f"Analytics tracking failed: {e}")
        
        return {
            **ctx_data,
            'analytics_tracked': False,
            'analytics_error': str(e)
        }

async def track_user_action(user_id: str, action: str):
    """Mock analytics tracking."""
    # Simulate occasional failures
    import random
    if random.random() < 0.05:  # 5% failure rate
        raise Exception("Analytics service unavailable")
```

## Code Organization

### File Structure Pattern
Organize your ModuLink functions logically.

```
your_project/
├── workflows/
│   ├── __init__.py
│   ├── user_management.py     # User-related workflows
│   ├── order_processing.py    # Order-related workflows
│   └── notification.py        # Notification workflows
├── functions/
│   ├── __init__.py
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── user_validation.py
│   │   └── order_validation.py
│   ├── external_services/
│   │   ├── __init__.py
│   │   ├── payment_service.py
│   │   └── email_service.py
│   └── utils/
│       ├── __init__.py
│       ├── formatters.py
│       └── calculators.py
└── tests/
    ├── test_workflows/
    └── test_functions/
```

### Module Organization Pattern
Group related functions together.

```python
# functions/validation/user_validation.py
"""User validation functions."""

from typing import Dict, Any

async def validate_user_email(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user email format."""
    # Implementation here
    pass

async def validate_user_password(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate password strength."""
    # Implementation here
    pass

async def validate_user_age(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user age requirements."""
    # Implementation here
    pass

# Export all validation functions
__all__ = [
    'validate_user_email',
    'validate_user_password', 
    'validate_user_age'
]
```

### Workflow Assembly Pattern
Assemble workflows from reusable functions.

```python
# workflows/user_management.py
"""User management workflows."""

from modulink import chain
from functions.validation.user_validation import (
    validate_user_email,
    validate_user_password,
    validate_user_age
)
from functions.external_services.email_service import send_welcome_email
from functions.utils.formatters import normalize_user_data

def create_user_registration_workflow():
    """Create a complete user registration workflow."""
    return chain([
        normalize_user_data,
        validate_user_email,
        validate_user_password,
        validate_user_age,
        check_email_availability,
        create_user_account,
        send_welcome_email
    ])

def create_user_login_workflow():
    """Create a user login workflow."""
    return chain([
        validate_login_credentials,
        check_account_status,
        generate_auth_token,
        update_last_login
    ])

# More workflow functions...
```

## Best Practices

### 1. Function Naming Conventions
Use clear, descriptive names that indicate what the function does.

```python
# ✅ Good naming
async def validate_user_email(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
async def calculate_order_total(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
async def send_welcome_email(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
async def check_inventory_availability(ctx_data: Dict[str, Any]) -> Dict[str, Any]:

# ❌ Bad naming
async def process(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
async def handle_data(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
async def do_stuff(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
```

### 2. Documentation Standards
Document your functions clearly.

```python
async def calculate_shipping_cost(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate shipping cost based on order details and destination.
    
    Expected context data:
        - order_total (float): Total order value
        - shipping_address (dict): Destination address
        - shipping_method (str): 'standard' or 'express'
        - user_type (str): 'standard' or 'premium'
    
    Adds to context:
        - shipping_cost (float): Calculated shipping cost
        - shipping_method_final (str): Final shipping method chosen
        - free_shipping_applied (bool): Whether free shipping was applied
    
    Returns:
        Updated context with shipping information
    """
    # Implementation here
    pass
```

### 3. Error Handling Standards
Be consistent in how you handle and report errors.

```python
async def standard_error_handling(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Example of standard error handling pattern."""
    try:
        # Main logic here
        result = perform_operation(ctx_data)
        
        return {
            **ctx_data,
            'operation_result': result,
            'operation_success': True
        }
        
    except ValueError as e:
        # Client errors - don't retry
        return {
            **ctx_data,
            'operation_success': False,
            'error_type': 'validation',
            'error_message': str(e),
            'retryable': False
        }
        
    except ConnectionError as e:
        # Service errors - can retry
        return {
            **ctx_data,
            'operation_success': False,
            'error_type': 'service',
            'error_message': 'Service temporarily unavailable',
            'retryable': True
        }

def perform_operation(ctx_data: Dict[str, Any]) -> str:
    """Mock operation that might fail."""
    return "success"
```

### 4. Context Key Conventions
Use consistent naming for context keys.

```python
# Recommended context key patterns:
{
    # Input data (what the user provided)
    'user_data': {...},
    'order_data': {...},
    
    # Processed/validated data
    'user_data_validated': {...},
    'order_items_normalized': [...],
    
    # Status flags
    'validation_passed': True,
    'payment_processed': False,
    'email_sent': True,
    
    # Error information
    'validation_errors': [...],
    'error_message': "...",
    'error_type': "validation",
    
    # Metadata
    'processing_started_at': "...",
    'current_step': "payment_processing",
    'total_steps': 5
}
```

### 5. Testing Considerations
Design functions to be easily testable.

```python
# ✅ Good - Easy to test
async def calculate_tax(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate tax for an order."""
    order_total = ctx_data.get('order_total', 0)
    tax_rate = ctx_data.get('tax_rate', 0.08)  # Default 8%
    
    tax_amount = order_total * tax_rate
    
    return {
        **ctx_data,
        'tax_amount': round(tax_amount, 2),
        'tax_rate_applied': tax_rate
    }

# Test is straightforward:
# result = await calculate_tax({'order_total': 100, 'tax_rate': 0.1})
# assert result['tax_amount'] == 10.0
```

## Next Steps

Once you're comfortable with these beginner patterns, you're ready for:

- **[Patterns Cookbook - Intermediate](patterns-cookbook-intermediate.md)** - Advanced orchestration, middleware strategies, and state management
- **[Patterns Cookbook - Advanced](patterns-cookbook-advanced.md)** - Enterprise architecture patterns and production deployment strategies

## Common Pitfalls to Avoid

1. **Functions doing too much** - Keep functions focused on single responsibilities
2. **Mutating input context** - Always create new contexts, never modify input
3. **Hidden dependencies** - All dependencies should be in the context or injected
4. **Inconsistent error handling** - Establish patterns and stick to them
5. **Poor naming** - Function and context key names should be self-documenting

Remember: Good patterns make your code more maintainable, testable, and understandable!
