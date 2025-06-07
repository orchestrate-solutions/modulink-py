# ModuLink Testing Cookbook - Beginner's Guide

## Overview

This cookbook teaches you how to test ModuLink workflows step by step, from simple individual functions to basic chains. Perfect for developers new to ModuLink or testing complex workflows.

## Table of Contents

1. [Why Test ModuLink Workflows?](#why-test-modulink-workflows)
2. [Basic Setup](#basic-setup)
3. [Testing Individual Functions](#testing-individual-functions)
4. [Testing Simple Chains](#testing-simple-chains)
5. [Working with Context](#working-with-context)
6. [Common Testing Patterns](#common-testing-patterns)
7. [Best Practices](#best-practices)

## Why Test ModuLink Workflows?

ModuLink workflows can be complex, with multiple functions chained together. Testing helps you:

- **Verify each step works correctly** - Catch bugs early in individual functions
- **Ensure data flows properly** - Confirm context data is passed correctly between functions
- **Test error handling** - Make sure failures are handled gracefully
- **Document expected behavior** - Tests serve as living documentation
- **Enable refactoring** - Change implementation confidently with test coverage

## Basic Setup

### Project Structure
```
your_project/
├── workflows/
│   ├── __init__.py
│   └── user_workflow.py
├── tests/
│   ├── __init__.py
│   └── test_user_workflow.py
└── requirements.txt
```

### Required Dependencies
```txt
# requirements.txt
modulink-py
pytest
pytest-asyncio
```

### Test File Template
```python
# tests/test_user_workflow.py
import pytest
import asyncio
from typing import Dict, Any

# Import your workflow functions
from workflows.user_workflow import (
    validate_user_data,
    create_user_account,
    send_welcome_email
)

class TestUserWorkflow:
    """Test suite for user registration workflow."""
    
    def setup_method(self):
        """Setup run before each test method."""
        # Reset any global state here
        pass
    
    def teardown_method(self):
        """Cleanup run after each test method."""
        # Clean up any resources here
        pass
```

## Testing Individual Functions

Start by testing each function in isolation. This helps you understand what each function does and catch basic errors.

### Example: Testing a Validation Function

```python
# workflows/user_workflow.py
async def validate_user_data(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user registration data."""
    user_data = ctx_data.get('user_data', {})
    
    errors = []
    
    # Check required fields
    if not user_data.get('email'):
        errors.append("Email is required")
    
    if not user_data.get('username'):
        errors.append("Username is required")
    
    if len(user_data.get('password', '')) < 8:
        errors.append("Password must be at least 8 characters")
    
    # Add validation results to context
    result = ctx_data.copy()
    result['validation_errors'] = errors
    result['is_valid'] = len(errors) == 0
    
    return result

# Test the function
class TestUserValidation:
    
    @pytest.mark.asyncio
    async def test_valid_user_data(self):
        """Test that valid user data passes validation."""
        # Arrange - Set up test data
        context = {
            'user_data': {
                'email': 'test@example.com',
                'username': 'testuser',
                'password': 'securepassword123'
            }
        }
        
        # Act - Call the function
        result = await validate_user_data(context)
        
        # Assert - Check the results
        assert result['is_valid'] is True
        assert result['validation_errors'] == []
        assert result['user_data']['email'] == 'test@example.com'
    
    @pytest.mark.asyncio
    async def test_missing_email(self):
        """Test that missing email fails validation."""
        context = {
            'user_data': {
                'username': 'testuser',
                'password': 'securepassword123'
            }
        }
        
        result = await validate_user_data(context)
        
        assert result['is_valid'] is False
        assert "Email is required" in result['validation_errors']
    
    @pytest.mark.asyncio
    async def test_short_password(self):
        """Test that short password fails validation."""
        context = {
            'user_data': {
                'email': 'test@example.com',
                'username': 'testuser',
                'password': '123'  # Too short
            }
        }
        
        result = await validate_user_data(context)
        
        assert result['is_valid'] is False
        assert "Password must be at least 8 characters" in result['validation_errors']
```

### Key Testing Principles

1. **Arrange, Act, Assert** - Structure your tests clearly
2. **Test one thing at a time** - Each test should verify one specific behavior
3. **Use descriptive names** - Test names should explain what they're testing
4. **Test both success and failure cases** - Don't just test the happy path

## Testing Simple Chains

Once individual functions work, test them chained together.

### Example: Simple Chain Test

```python
# workflows/user_workflow.py
from modulink import chain

async def create_user_account(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create user account if validation passed."""
    if not ctx_data.get('is_valid'):
        raise Exception("Cannot create account with invalid data")
    
    user_data = ctx_data['user_data']
    
    # Simulate account creation
    user_id = f"user_{hash(user_data['username']) % 10000}"
    
    result = ctx_data.copy()
    result['user_id'] = user_id
    result['account_created'] = True
    
    return result

async def send_welcome_email(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send welcome email to new user."""
    if not ctx_data.get('account_created'):
        raise Exception("Cannot send email without created account")
    
    user_data = ctx_data['user_data']
    
    # Simulate email sending
    result = ctx_data.copy()
    result['welcome_email_sent'] = True
    result['email_address'] = user_data['email']
    
    return result

# Create the chain
def create_user_registration_workflow():
    """Create complete user registration workflow."""
    return chain([
        validate_user_data,
        create_user_account,
        send_welcome_email
    ])

# Test the chain
class TestUserRegistrationChain:
    
    @pytest.mark.asyncio
    async def test_successful_registration(self):
        """Test complete successful user registration."""
        # Create the workflow
        registration_workflow = create_user_registration_workflow()
        
        # Prepare test data
        initial_context = {
            'user_data': {
                'email': 'newuser@example.com',
                'username': 'newuser',
                'password': 'verysecurepassword'
            }
        }
        
        # Execute the workflow
        result = await registration_workflow(initial_context)
        
        # Verify all steps completed
        assert result['is_valid'] is True
        assert result['account_created'] is True
        assert result['welcome_email_sent'] is True
        assert result['user_id'].startswith('user_')
        assert result['email_address'] == 'newuser@example.com'
    
    @pytest.mark.asyncio
    async def test_registration_with_invalid_data(self):
        """Test that registration fails with invalid data."""
        registration_workflow = create_user_registration_workflow()
        
        # Invalid data (missing email)
        initial_context = {
            'user_data': {
                'username': 'newuser',
                'password': 'verysecurepassword'
            }
        }
        
        # Workflow should fail at account creation
        with pytest.raises(Exception, match="Cannot create account with invalid data"):
            await registration_workflow(initial_context)
```

## Working with Context

Understanding how context flows through your workflow is crucial for effective testing.

### Context Flow Patterns

```python
# Example showing how context flows through functions
async def step_one(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """First step adds data to context."""
    result = ctx_data.copy()  # Always copy to avoid mutations
    result['step_one_complete'] = True
    result['processed_at'] = datetime.now().isoformat()
    return result

async def step_two(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Second step depends on first step."""
    if not ctx_data.get('step_one_complete'):
        raise Exception("Step one must complete first")
    
    result = ctx_data.copy()
    result['step_two_complete'] = True
    result['total_steps'] = 2
    return result

# Test context flow
class TestContextFlow:
    
    @pytest.mark.asyncio
    async def test_context_accumulates_data(self):
        """Test that context accumulates data through the chain."""
        workflow = chain([step_one, step_two])
        
        initial_context = {'user_id': '123'}
        
        result = await workflow(initial_context)
        
        # Verify all data is present
        assert result['user_id'] == '123'  # Original data preserved
        assert result['step_one_complete'] is True  # Added by step one
        assert result['step_two_complete'] is True  # Added by step two
        assert result['total_steps'] == 2  # Added by step two
        assert 'processed_at' in result  # Added by step one
```

### Testing Context Dependencies

```python
class TestContextDependencies:
    
    @pytest.mark.asyncio
    async def test_missing_dependency_fails(self):
        """Test that missing context dependencies cause failures."""
        # Skip step one, go directly to step two
        context_without_step_one = {'user_id': '123'}
        
        with pytest.raises(Exception, match="Step one must complete first"):
            await step_two(context_without_step_one)
    
    @pytest.mark.asyncio
    async def test_with_dependency_succeeds(self):
        """Test that having dependencies allows success."""
        context_with_step_one = {
            'user_id': '123',
            'step_one_complete': True
        }
        
        result = await step_two(context_with_step_one)
        
        assert result['step_two_complete'] is True
```

## Common Testing Patterns

### Pattern 1: Mock External Services

```python
from unittest.mock import patch, MagicMock

class TestWithMocks:
    
    @patch('workflows.user_workflow.send_email_service')
    @pytest.mark.asyncio
    async def test_email_sending_with_mock(self, mock_email_service):
        """Test email sending without actually sending emails."""
        # Configure the mock
        mock_email_service.send.return_value = {'status': 'sent', 'id': 'email_123'}
        
        context = {
            'user_data': {'email': 'test@example.com'},
            'account_created': True
        }
        
        result = await send_welcome_email(context)
        
        # Verify the mock was called
        mock_email_service.send.assert_called_once()
        
        # Verify the result
        assert result['welcome_email_sent'] is True
```

### Pattern 2: Test Data Helpers

```python
class TestDataHelpers:
    """Helper methods for creating test data."""
    
    @staticmethod
    def create_valid_user_data():
        """Create valid user data for testing."""
        return {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'securepassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    @staticmethod
    def create_context_with_user(user_data=None):
        """Create context with user data."""
        if user_data is None:
            user_data = TestDataHelpers.create_valid_user_data()
        
        return {
            'user_data': user_data,
            'request_id': 'test_request_123',
            'timestamp': datetime.now().isoformat()
        }

# Use helpers in tests
class TestWithHelpers:
    
    @pytest.mark.asyncio
    async def test_with_helper_data(self):
        """Test using helper data."""
        context = TestDataHelpers.create_context_with_user()
        
        result = await validate_user_data(context)
        
        assert result['is_valid'] is True
```

### Pattern 3: Parameterized Tests

```python
class TestParameterized:
    
    @pytest.mark.parametrize("email,expected_valid", [
        ("test@example.com", True),
        ("invalid-email", False),
        ("", False),
        ("user@domain", False),
        ("user@domain.com", True),
    ])
    @pytest.mark.asyncio
    async def test_email_validation(self, email, expected_valid):
        """Test email validation with different inputs."""
        context = {
            'user_data': {
                'email': email,
                'username': 'testuser',
                'password': 'securepassword123'
            }
        }
        
        result = await validate_user_data(context)
        
        assert result['is_valid'] == expected_valid
```

## Best Practices

### 1. Start Small, Build Up
- Test individual functions first
- Then test simple chains
- Finally test complex workflows

### 2. Use Clear Test Names
```python
# Good
async def test_user_registration_succeeds_with_valid_data(self):

# Bad
async def test_user_reg(self):
```

### 3. Test Both Success and Failure Cases
```python
class TestComprehensive:
    # Test the happy path
    async def test_successful_workflow(self):
        pass
    
    # Test error conditions
    async def test_workflow_fails_with_invalid_input(self):
        pass
    
    async def test_workflow_handles_service_unavailable(self):
        pass
```

### 4. Keep Tests Independent
```python
# Each test should work in isolation
class TestIndependent:
    
    def setup_method(self):
        """Reset state before each test."""
        # Clear any shared state
        pass
    
    async def test_one(self):
        # This test doesn't depend on test_two
        pass
    
    async def test_two(self):
        # This test doesn't depend on test_one
        pass
```

### 5. Use Descriptive Assertions
```python
# Good - Clear what went wrong
assert result['is_valid'] is True, f"Validation failed: {result['validation_errors']}"

# Bad - Unclear what the problem is
assert result['is_valid']
```

## Next Steps

Once you're comfortable with these basics, you're ready for:

- **[Testing Cookbook - Intermediate](testing-cookbook-intermediate.md)** - Error handling, mocking, and integration tests
- **[Testing Cookbook - Advanced](testing-cookbook-advanced.md)** - Complex workflows, performance testing, and test organization

## Common Pitfalls to Avoid

1. **Not copying context** - Always use `ctx_data.copy()` to avoid mutations
2. **Testing too much at once** - Break complex tests into smaller ones
3. **Ignoring error cases** - Test failure scenarios, not just success
4. **Hard-coded test data** - Use helpers and factories for flexible test data
5. **Not cleaning up** - Use setup/teardown methods to maintain test isolation

Remember: Good tests make you more confident in your code and help catch bugs before they reach production!
