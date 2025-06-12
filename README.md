# ModuLink Python 🐍

A lightweight function composition framework for Python using universal types - simple, consistent patterns that work across multiple languages.

## 🌟 Core Philosophy

- **Universal Types**: Simple function signatures that work across languages
- **Functional Composition**: Pure functions connected through context flow
- **Minimal API**: Only 5 core types you need to learn
- **Context Flow**: Rich context dictionaries carry data through function chains

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from modulink import Ctx, chain

# Define simple functions that take context and return context
async def validate_user(ctx: Ctx) -> Ctx:
    if not ctx.get('email'):
        return {**ctx, 'errors': [{'message': 'Email is required', 'code': 'VALIDATION_ERROR'}]}
    return ctx

async def send_welcome(ctx: Ctx) -> Ctx:
    if not ctx.get('errors'):
        print(f"Welcome email sent to {ctx.get('email')}")
        return {**ctx, 'sent': True}
    return ctx

# Compose functions into a chain
user_flow = chain(validate_user, send_welcome)

# Execute with context
result = await user_flow({'email': 'alice@example.com'})
print(result)  # {'email': 'alice@example.com', 'sent': True}
```

## 🎯 Universal Types

ModuLink uses 5 simple universal types that create a consistent API:

### 1. **Ctx** - Context Dictionary
```python
# Simple dictionary for passing data
ctx: Ctx = {
    'user_id': 123,
    'email': 'user@example.com',
    'processed_at': '2024-01-01T12:00:00Z'
}
```

### 2. **Link** - Async Function
```python
# Function that transforms context
async def process_user(ctx: Ctx) -> Ctx:
    return {**ctx, 'processed': True}
```

### 3. **Chain** - Function Composition
```python
# Compose multiple links
from modulink import chain

pipeline = chain(validate_input, process_data, save_result)
```

### 4. **Trigger** - Event Handler
```python
# HTTP endpoint that returns a composed function
from modulink import http_trigger

@http_trigger('/api/users', method='POST')
async def handle_user_creation(ctx: Ctx) -> Ctx:
    return await user_creation_pipeline(ctx)
```

### 5. **Middleware** - Function Wrapper
```python
# Function that wraps other functions
from modulink import timing

timed_function = timing(process_user)
```

## 🔧 Functional Utilities

ModuLink provides utilities for common patterns:

### Conditional Execution
```python
from modulink import when

# Only execute if condition is met
premium_flow = when(
    lambda ctx: ctx.get('user_type') == 'premium',
    add_premium_features
)
```

### Error Handling
```python
from modulink import catch_errors

# Gracefully handle errors
safe_operation = catch_errors(risky_function, fallback_function)
```

### Timing & Performance
```python
from modulink import timing

# Track execution time
timed_flow = timing(expensive_operation)
```

### Parallel Execution
```python
from modulink import parallel

# Run functions in parallel
parallel_flow = parallel([process_images, generate_thumbnails, extract_metadata])
```

### Interactive Object Discovery
```python
from modulink import discover

def greet(name: str) -> str:
    """Return a friendly greeting."""
    return f"Hello {name}"

# Print info to the console
discover(greet)

# Get info string for IDE hover tooltips
tooltip = discover(greet, show=False)
```

## 🌐 Integration Examples

### FastAPI Integration
```python
from fastapi import FastAPI
from modulink import Ctx, chain, catch_errors

app = FastAPI()

# Define processing pipeline
user_pipeline = chain(
    validate_user_data,
    save_to_database,
    send_confirmation_email
)

@app.post("/api/users")
async def create_user(request_data: dict):
    # Convert to ModuLink context
    ctx: Ctx = {'request_data': request_data}
    
    # Run pipeline with error handling
    safe_pipeline = catch_errors(user_pipeline)
    result = await safe_pipeline(ctx)
    
    if result.get('errors'):
        return {"success": False, "errors": result['errors']}
    
    return {"success": True, "user": result.get('user')}
```

### CLI Integration
```python
import click
from modulink import Ctx, chain

# File processing pipeline
file_pipeline = chain(
    validate_input_directory,
    scan_files,
    process_files,
    generate_report
)

@click.command()
@click.option('--input-dir', required=True)
@click.option('--output-dir', required=True)
def process_files(input_dir: str, output_dir: str):
    """Process files using ModuLink pipeline."""
    
    ctx: Ctx = {
        'input_dir': input_dir,
        'output_dir': output_dir,
        'start_time': datetime.utcnow().isoformat()
    }
    
    result = await file_pipeline(ctx)
    
    if result.get('errors'):
        print("Processing failed:", result['errors'])
        exit(1)
    
    print("Processing completed successfully!")
```

## 📁 Project Structure

```
modulink-py/
├── modulink/
│   ├── __init__.py              # Package exports
│   ├── universal.py             # Universal type definitions  
│   ├── universal_modulink.py    # Core implementation
│   └── universal_utils.py       # Utility functions
├── tests/
│   └── test_universal.py       # Universal types tests
└── README.md
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/test_universal.py -v

```


## 🧪 Testing Guide

ModuLink provides comprehensive testing cookbooks to help you build robust test suites:

### **[📖 Complete Testing Guide](docs/testing-guide-overview.md)**
Your roadmap to testing ModuLink workflows from simple functions to enterprise systems.

### Learning Path:
1. **[🌱 Beginner Cookbook](docs/testing-cookbook-beginner.md)** - Start here
   - Basic testing setup and patterns
   - Testing individual functions and simple chains
   - Working with context and common patterns

2. **[🚀 Intermediate Cookbook](docs/testing-cookbook-intermediate.md)** - Level up
   - Advanced error handling and mocking
   - Integration testing and async workflows
   - Performance testing patterns

3. **[🏢 Advanced Cookbook](docs/testing-cookbook-advanced.md)** - Master level
   - Complex enterprise workflows (DevOps, Financial)
   - Multi-environment and compliance testing
   - Comprehensive test architecture

### Real-World Test Examples:
- **570+ lines** of DevOps CI/CD pipeline tests
- **400+ lines** of Financial trading system tests
- Unit, integration, performance, and compliance testing patterns
- Mock strategies for external services
- Error handling and recovery testing

## 🔄 Migration from v1.x

ModuLink 2.0 uses universal types instead of classes:

```python
# v1.x (Legacy - No longer supported)
from modulink import ModuLink, Context
app = ModuLink()
ctx = Context.from_data({'user': 'alice'})

# v2.0 (Universal Types)
from modulink import Ctx, chain
ctx: Ctx = {'user': 'alice'}
pipeline = chain(validate, process, save)
```

**Key Changes:**
- ✅ Simple dictionaries instead of Context class
- ✅ Function composition instead of registration
- ✅ Consistent API across languages  
- ✅ Better TypeScript compatibility
- ✅ Reduced complexity and dependencies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite: `python -m pytest tests/test_universal.py -v`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## ⚠️ Limitations

- Basic function composition only
- Limited middleware capabilities
- No sophisticated execution model
- Utilities are mostly stubs

## 🏗️ Architecture

ModuLink Python 2.0 uses universal types for consistency:

- **Context as Data**: Simple dictionaries for maximum compatibility
- **Function Composition**: Pure functions connected through `chain()`
- **Async by Default**: All functions are async for better performance
- **Language Agnostic**: Same patterns across multiple languages
- **Minimal Dependencies**: Lightweight with only essential features

The universal types approach provides:
- 🚀 **Better Performance**: No class overhead, direct dictionary access
- 🧪 **Easier Testing**: Pure functions are simple to test
- 🔧 **Better IDE Support**: Full type hints and autocomplete
- 🌐 **Cross-Language**: Same patterns across multiple languages

# Test commit for TestPyPI publishing - workflow test 2
