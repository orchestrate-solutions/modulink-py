# ModuLink Python - Immutable Context Patterns

## Overview

ModuLink Python now supports immutable Context patterns that provide better data flow control, prevent accidental mutations, and enable functional programming approaches while maintaining backward compatibility with existing code.

## Key Benefits

### 🔒 **Data Safety**
- Prevents accidental mutations of shared context objects
- Creates predictable data flow through function chains
- Eliminates side effects between processing steps

### 🧠 **Memory Management**
- Each function creates a new Context object instead of mutating the existing one
- Original contexts remain unchanged, allowing for better debugging and tracing
- Garbage collection can clean up intermediate contexts automatically

### 🔧 **Functional Programming**
- Enables pure functional transformations
- Supports method chaining for readable code
- Makes testing easier with immutable inputs and outputs

### 🔄 **Backward Compatibility**
- All existing tests and code continue to work
- Gradual migration path from mutable to immutable patterns
- Hybrid approaches allow mixing both patterns

## Usage Patterns

### Basic Immutable Operations

```python
from modulink import Context

# Create initial context
ctx = Context.from_data({'user': 'alice', 'email': 'alice@example.com'})

# Immutable transformations - each creates a new context
ctx2 = ctx.with_data('role', 'admin')
ctx3 = ctx2.with_data({'active': True, 'last_login': '2025-05-31'})
ctx4 = ctx3.with_body({'request_data': 'sample'})
ctx5 = ctx4.with_params({'page': 1, 'limit': 10})

# Original context is unchanged
print(ctx.data)   # {'user': 'alice', 'email': 'alice@example.com'}
print(ctx5.data)  # Contains all accumulated data
```

### Method Chaining

```python
# Functional-style chaining
result = (ctx
          .with_data('processed', True)
          .with_data('timestamp', datetime.utcnow().isoformat())
          .with_result({'status': 'success'})
          .start_step('processing')
          .end_step('processing'))
```

### Function Implementation Patterns

#### Pure Immutable Function
```python
def pure_immutable_processor(ctx: Context) -> Context:
    """Process data using pure immutable pattern"""
    if ctx.has_errors():
        return ctx
    
    # Create new context with transformations
    return (ctx
            .start_step('processing')
            .with_data('processed', True)
            .with_data('processor_version', '2.0')
            .end_step('processing'))
```

#### Hybrid Function (Backward Compatible)
```python
def hybrid_processor(ctx: Context) -> Context:
    """Hybrid function supporting both patterns"""
    new_ctx = ctx.start_step('hybrid_processing')
    
    # Use immutable methods when available
    if hasattr(new_ctx, 'with_data'):
        # New immutable pattern
        result_ctx = new_ctx.with_data('method', 'immutable')
    else:
        # Fallback to mutable pattern
        new_ctx.data['method'] = 'mutable'
        result_ctx = new_ctx
    
    return result_ctx.end_step('hybrid_processing')
```

## Helper Methods

### `with_data(key_or_dict, value=None)`
Adds or updates data in the context.

```python
# Single key-value pair
ctx2 = ctx.with_data('status', 'active')

# Multiple values via dictionary
ctx3 = ctx.with_data({'role': 'admin', 'permissions': ['read', 'write']})
```

### `with_result(result_dict)`
Merges result data into the main context data.

```python
ctx2 = ctx.with_result({'computed_value': 42, 'success': True})
```

### `with_body(body_dict)`
Sets request body data under the 'body' key.

```python
ctx2 = ctx.with_body({'request_data': 'sample', 'content_type': 'json'})
```

### `with_params(params_dict)`
Sets parameter data under the 'params' key.

```python
ctx2 = ctx.with_params({'page': 1, 'limit': 10, 'sort': 'name'})
```

## Error Handling

### Immutable Error Addition
```python
def validator(ctx: Context) -> Context:
    """Add errors using immutable pattern"""
    new_ctx = ctx.start_step('validation')
    
    if not ctx.data.get('email'):
        new_ctx = new_ctx.add_error('Email is required', 'EMAIL_REQUIRED')
    
    if not ctx.data.get('name'):
        new_ctx = new_ctx.add_error('Name is required', 'NAME_REQUIRED')
    
    return new_ctx.end_step('validation')
```

### Error Recovery Patterns
```python
def error_recovery(ctx: Context) -> Context:
    """Recover from errors with default values"""
    if ctx.has_errors():
        # Provide default values and continue processing
        return (ctx
                .with_data('recovered', True)
                .with_data('default_applied', True)
                .with_data('recovery_timestamp', datetime.utcnow().isoformat()))
    return ctx
```

## Performance Considerations

### Benchmark Results
Based on our testing with 1000 iterations:

- **Mutable operations**: ~0.018ms per operation
- **Immutable operations**: ~0.048ms per operation
- **Performance overhead**: ~2.7x slower for immutable operations

### When to Use Each Pattern

#### Use **Immutable** when:
- Data integrity is critical
- You need to trace data transformations
- Working with shared contexts across multiple functions
- Building pure functional pipelines
- Testing complex data flows

#### Use **Mutable** when:
- Performance is critical (high-frequency operations)
- Working with large data objects where copying is expensive
- Legacy code that requires mutation semantics
- Simple, linear processing workflows

## Migration Strategies

### 1. Gradual Migration
Start by converting leaf functions to immutable patterns:

```python
# Before (mutable)
def old_function(ctx: Context) -> Context:
    ctx.data['processed'] = True
    return ctx

# After (hybrid - supports both)
def new_function(ctx: Context) -> Context:
    # Create immutable result
    new_ctx = ctx.with_data('processed', True)
    
    # For backward compatibility during migration
    if hasattr(ctx, 'data'):
        ctx.data['processed'] = True
    
    return new_ctx
```

### 2. Pure Conversion
For new code or when full migration is desired:

```python
# Before (mutable)
def process_user(ctx: Context) -> Context:
    ctx.start_step('processing')
    ctx.data['name'] = ctx.data['name'].strip().title()
    ctx.data['email'] = ctx.data['email'].lower()
    ctx.data['processed_at'] = datetime.utcnow().isoformat()
    ctx.end_step('processing')
    return ctx

# After (pure immutable)
def process_user(ctx: Context) -> Context:
    return (ctx
            .start_step('processing')
            .with_data('name', ctx.data['name'].strip().title())
            .with_data('email', ctx.data['email'].lower())
            .with_data('processed_at', datetime.utcnow().isoformat())
            .end_step('processing'))
```

### 3. Testing Migration
Ensure both patterns work during migration:

```python
def test_both_patterns():
    """Test that function works with both patterns"""
    original_data = {'name': 'alice', 'email': 'alice@example.com'}
    
    # Test mutable pattern
    mutable_ctx = Context.from_data(original_data.copy())
    mutable_result = process_user_hybrid(mutable_ctx)
    
    # Test immutable pattern
    immutable_ctx = Context.from_data(original_data.copy())
    immutable_result = process_user_hybrid(immutable_ctx)
    
    # Both should produce the same final data
    assert mutable_result.data['name'] == immutable_result.data['name']
    assert mutable_result.data['email'] == immutable_result.data['email']
    
    # Original contexts should be different
    assert id(immutable_ctx) != id(immutable_result)  # Immutable creates new
```

## Best Practices

### 1. **Start Steps Early**
Always start steps before data transformations to ensure proper timing:

```python
def good_function(ctx: Context) -> Context:
    new_ctx = ctx.start_step('processing')  # Start first
    result_ctx = new_ctx.with_data('processed', True)  # Then transform
    return result_ctx.end_step('processing')  # End last
```

### 2. **Check for Errors Early**
Skip processing if errors exist:

```python
def safe_function(ctx: Context) -> Context:
    if ctx.has_errors():
        return ctx  # Skip processing if errors exist
    
    return ctx.with_data('safe_processing', True)
```

### 3. **Use Method Chaining for Readability**
Chain multiple transformations for better readability:

```python
def readable_function(ctx: Context) -> Context:
    return (ctx
            .start_step('multi_transform')
            .with_data('step1', 'completed')
            .with_data('step2', 'completed')
            .with_result({'final_status': 'success'})
            .end_step('multi_transform'))
```

### 4. **Handle Async Operations**
Immutable patterns work seamlessly with async operations:

```python
async def async_immutable_function(ctx: Context) -> Context:
    new_ctx = ctx.start_step('async_processing')
    
    # Simulate async operation
    await asyncio.sleep(0.1)
    
    return (new_ctx
            .with_data('async_completed', True)
            .with_data('processed_at', datetime.utcnow().isoformat())
            .end_step('async_processing'))
```

## Common Patterns

### Data Validation Pipeline
```python
def create_validation_pipeline():
    def validate_required_fields(ctx: Context) -> Context:
        errors = []
        for field in ['name', 'email']:
            if not ctx.data.get(field):
                errors.append(f"{field} is required")
        
        result_ctx = ctx.start_step('required_validation')
        for error in errors:
            result_ctx = result_ctx.add_error(error, 'VALIDATION_ERROR')
        
        return result_ctx.end_step('required_validation')
    
    def validate_formats(ctx: Context) -> Context:
        if ctx.has_errors():
            return ctx
        
        result_ctx = ctx.start_step('format_validation')
        
        if '@' not in ctx.data.get('email', ''):
            result_ctx = result_ctx.add_error('Invalid email format', 'FORMAT_ERROR')
        
        return result_ctx.end_step('format_validation')
    
    return [validate_required_fields, validate_formats]
```

### Data Transformation Pipeline
```python
def create_transform_pipeline():
    def normalize_data(ctx: Context) -> Context:
        if ctx.has_errors():
            return ctx
        
        return (ctx
                .start_step('normalization')
                .with_data('name', ctx.data['name'].strip().title())
                .with_data('email', ctx.data['email'].strip().lower())
                .end_step('normalization'))
    
    def enrich_data(ctx: Context) -> Context:
        if ctx.has_errors():
            return ctx
        
        domain = ctx.data['email'].split('@')[1]
        
        return (ctx
                .start_step('enrichment')
                .with_data('email_domain', domain)
                .with_data('display_name', ctx.data['name'])
                .with_data('enriched_at', datetime.utcnow().isoformat())
                .end_step('enrichment'))
    
    return [normalize_data, enrich_data]
```

## Examples

See the following example files for comprehensive demonstrations:

- `examples/basic_example.py` - Basic usage with both mutable and immutable patterns
- `examples/immutable_example.py` - Comprehensive immutable pattern examples
- `examples/advanced_immutable_example.py` - Advanced patterns and performance analysis

## Conclusion

The immutable Context pattern in ModuLink Python provides a powerful foundation for building reliable, maintainable data processing pipelines. While there is a small performance overhead, the benefits of data safety, predictability, and functional programming capabilities make it an excellent choice for most applications.

The hybrid approach allows for gradual migration and ensures that existing code continues to work while new features can take advantage of immutable patterns.
