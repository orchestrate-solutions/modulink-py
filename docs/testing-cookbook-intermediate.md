# ModuLink Testing Cookbook - Intermediate Guide

## Overview

This cookbook covers intermediate testing techniques for ModuLink workflows, including error handling, mocking external services, integration testing, and testing complex data flows. Build on the [Beginner's Guide](testing-cookbook-beginner.md) foundation.

## Table of Contents

1. [Advanced Error Handling Tests](#advanced-error-handling-tests)
2. [Mocking External Dependencies](#mocking-external-dependencies)
3. [Integration Testing](#integration-testing)
4. [Testing Async Workflows](#testing-async-workflows)
5. [Data Flow Testing](#data-flow-testing)
6. [Testing with Fixtures](#testing-with-fixtures)
7. [Performance and Timing Tests](#performance-and-timing-tests)
8. [Test Organization Strategies](#test-organization-strategies)

## Advanced Error Handling Tests

Learn to test how your workflows handle various error conditions and recovery scenarios.

### Testing Chain Error Propagation

```python
# workflows/order_processing.py
from modulink import chain

async def validate_order(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate order data."""
    order = ctx_data.get('order', {})
    
    if not order.get('customer_id'):
        raise ValueError("Customer ID is required")
    
    if order.get('total', 0) <= 0:
        raise ValueError("Order total must be positive")
    
    result = ctx_data.copy()
    result['validation_passed'] = True
    return result

async def check_inventory(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check if items are in stock."""
    order = ctx_data.get('order', {})
    items = order.get('items', [])
    
    for item in items:
        if item.get('quantity', 0) > item.get('stock', 0):
            raise RuntimeError(f"Insufficient stock for item {item.get('name')}")
    
    result = ctx_data.copy()
    result['inventory_checked'] = True
    return result

async def process_payment(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process payment for order."""
    order = ctx_data.get('order', {})
    
    if order.get('total', 0) > 10000:
        raise RuntimeError("Payment amount exceeds limit")
    
    result = ctx_data.copy()
    result['payment_processed'] = True
    result['transaction_id'] = f"txn_{hash(str(order)) % 100000}"
    return result

# Test error propagation through the chain
class TestOrderProcessingErrors:
    
    @pytest.mark.asyncio
    async def test_validation_error_stops_chain(self):
        """Test that validation errors prevent further processing."""
        order_workflow = chain([
            validate_order,
            check_inventory,
            process_payment
        ])
        
        # Invalid order (missing customer_id)
        context = {
            'order': {
                'total': 100.0,
                'items': [{'name': 'Product 1', 'quantity': 1, 'stock': 10}]
            }
        }
        
        with pytest.raises(ValueError, match="Customer ID is required"):
            await order_workflow(context)
    
    @pytest.mark.asyncio
    async def test_inventory_error_after_validation(self):
        """Test that inventory errors occur after validation passes."""
        order_workflow = chain([
            validate_order,
            check_inventory,
            process_payment
        ])
        
        # Valid order but insufficient stock
        context = {
            'order': {
                'customer_id': 'cust_123',
                'total': 100.0,
                'items': [{'name': 'Product 1', 'quantity': 15, 'stock': 5}]
            }
        }
        
        with pytest.raises(RuntimeError, match="Insufficient stock for item Product 1"):
            await order_workflow(context)
    
    @pytest.mark.asyncio
    async def test_payment_error_after_inventory(self):
        """Test that payment errors occur after inventory check passes."""
        order_workflow = chain([
            validate_order,
            check_inventory,
            process_payment
        ])
        
        # Valid order with sufficient stock but payment limit exceeded
        context = {
            'order': {
                'customer_id': 'cust_123',
                'total': 15000.0,  # Exceeds limit
                'items': [{'name': 'Expensive Item', 'quantity': 1, 'stock': 10}]
            }
        }
        
        with pytest.raises(RuntimeError, match="Payment amount exceeds limit"):
            await order_workflow(context)
```

### Testing Error Recovery Patterns

```python
# Error recovery with try/catch in chains
from modulink import chain

async def order_error_handler(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle order processing errors."""
    error = ctx_data.get('error')
    result = ctx_data.copy()
    
    if isinstance(error, ValueError):
        result['error_type'] = 'validation'
        result['error_handled'] = True
        result['retry_allowed'] = True
    elif isinstance(error, RuntimeError):
        result['error_type'] = 'processing'
        result['error_handled'] = True
        result['retry_allowed'] = False
    
    return result

def create_order_workflow_with_error_handling():
    """Create order workflow with error handling."""
    return chain([
        validate_order,
        check_inventory,
        process_payment
    ]).catch_errors({
        ValueError: order_error_handler,
        RuntimeError: order_error_handler
    })

class TestOrderErrorRecovery:
    
    @pytest.mark.asyncio
    async def test_validation_error_recovery(self):
        """Test that validation errors are handled gracefully."""
        workflow = create_order_workflow_with_error_handling()
        
        context = {
            'order': {'total': 100.0}  # Missing customer_id
        }
        
        result = await workflow(context)
        
        assert result['error_handled'] is True
        assert result['error_type'] == 'validation'
        assert result['retry_allowed'] is True
    
    @pytest.mark.asyncio
    async def test_processing_error_recovery(self):
        """Test that processing errors are handled gracefully."""
        workflow = create_order_workflow_with_error_handling()
        
        context = {
            'order': {
                'customer_id': 'cust_123',
                'total': 15000.0,  # Exceeds payment limit
                'items': [{'name': 'Expensive Item', 'quantity': 1, 'stock': 10}]
            }
        }
        
        result = await workflow(context)
        
        assert result['error_handled'] is True
        assert result['error_type'] == 'processing'
        assert result['retry_allowed'] is False
```

## Mocking External Dependencies

Learn to test workflows that depend on external services without actually calling them.

### Mocking HTTP APIs

```python
import httpx
from unittest.mock import patch, AsyncMock, MagicMock

# workflows/notification_service.py
async def send_notification(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification via external API."""
    notification = ctx_data.get('notification', {})
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://api.notifications.com/send',
            json={
                'recipient': notification.get('recipient'),
                'message': notification.get('message'),
                'type': notification.get('type', 'info')
            },
            headers={'Authorization': f"Bearer {ctx_data.get('api_token')}"}
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Notification failed: {response.text}")
    
    result = ctx_data.copy()
    result['notification_sent'] = True
    result['notification_id'] = response.json().get('id')
    return result

class TestNotificationMocking:
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_successful_notification(self, mock_client_class):
        """Test successful notification sending with mocked HTTP client."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'notif_123', 'status': 'sent'}
        mock_client.post.return_value = mock_response
        
        # Test data
        context = {
            'notification': {
                'recipient': 'user@example.com',
                'message': 'Welcome!',
                'type': 'welcome'
            },
            'api_token': 'test_token_123'
        }
        
        # Execute
        result = await send_notification(context)
        
        # Verify API was called correctly
        mock_client.post.assert_called_once_with(
            'https://api.notifications.com/send',
            json={
                'recipient': 'user@example.com',
                'message': 'Welcome!',
                'type': 'welcome'
            },
            headers={'Authorization': 'Bearer test_token_123'}
        )
        
        # Verify result
        assert result['notification_sent'] is True
        assert result['notification_id'] == 'notif_123'
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_notification_api_failure(self, mock_client_class):
        """Test handling of API failures."""
        # Setup mock to simulate API failure
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.post.return_value = mock_response
        
        context = {
            'notification': {
                'recipient': 'user@example.com',
                'message': 'Welcome!'
            },
            'api_token': 'test_token_123'
        }
        
        with pytest.raises(RuntimeError, match="Notification failed: Internal Server Error"):
            await send_notification(context)
```

### Mocking Database Operations

```python
from unittest.mock import patch, AsyncMock

# workflows/user_service.py
import asyncpg

async def save_user_to_db(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save user to database."""
    user_data = ctx_data.get('user_data', {})
    
    conn = await asyncpg.connect('postgresql://localhost/testdb')
    try:
        user_id = await conn.fetchval(
            "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3) RETURNING id",
            user_data['email'],
            user_data['username'],
            user_data['password_hash']
        )
        
        result = ctx_data.copy()
        result['user_id'] = user_id
        result['saved_to_db'] = True
        return result
    finally:
        await conn.close()

class TestDatabaseMocking:
    
    @patch('asyncpg.connect')
    @pytest.mark.asyncio
    async def test_user_save_success(self, mock_connect):
        """Test successful user save to database."""
        # Setup database mock
        mock_conn = AsyncMock()
        mock_connect.return_value = mock_conn
        mock_conn.fetchval.return_value = 12345  # Mock user ID
        
        context = {
            'user_data': {
                'email': 'test@example.com',
                'username': 'testuser',
                'password_hash': 'hashed_password_123'
            }
        }
        
        result = await save_user_to_db(context)
        
        # Verify database operations
        mock_connect.assert_called_once_with('postgresql://localhost/testdb')
        mock_conn.fetchval.assert_called_once_with(
            "INSERT INTO users (email, username, password_hash) VALUES ($1, $2, $3) RETURNING id",
            'test@example.com',
            'testuser',
            'hashed_password_123'
        )
        mock_conn.close.assert_called_once()
        
        # Verify result
        assert result['user_id'] == 12345
        assert result['saved_to_db'] is True
    
    @patch('asyncpg.connect')
    @pytest.mark.asyncio
    async def test_database_connection_failure(self, mock_connect):
        """Test handling of database connection failures."""
        # Mock connection failure
        mock_connect.side_effect = asyncpg.PostgresConnectionError("Connection failed")
        
        context = {
            'user_data': {
                'email': 'test@example.com',
                'username': 'testuser',
                'password_hash': 'hashed_password_123'
            }
        }
        
        with pytest.raises(asyncpg.PostgresConnectionError):
            await save_user_to_db(context)
```

## Integration Testing

Test how multiple components work together in realistic scenarios.

### Testing Multi-Service Workflows

```python
# Integration test for complete user registration workflow
class TestUserRegistrationIntegration:
    
    @patch('workflows.notification_service.httpx.AsyncClient')
    @patch('workflows.user_service.asyncpg.connect')
    @pytest.mark.asyncio
    async def test_complete_user_registration_flow(self, mock_db_connect, mock_http_client_class):
        """Test complete user registration from validation to notification."""
        # Setup database mock
        mock_db_conn = AsyncMock()
        mock_db_connect.return_value = mock_db_conn
        mock_db_conn.fetchval.return_value = 12345
        
        # Setup HTTP client mock
        mock_http_client = AsyncMock()
        mock_http_client_class.return_value.__aenter__.return_value = mock_http_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'notif_123'}
        mock_http_client.post.return_value = mock_response
        
        # Create complete workflow
        complete_workflow = chain([
            validate_user_data,
            save_user_to_db,
            create_welcome_notification,
            send_notification
        ])
        
        # Test data
        context = {
            'user_data': {
                'email': 'newuser@example.com',
                'username': 'newuser',
                'password': 'securepassword123'
            },
            'api_token': 'test_token_123'
        }
        
        # Execute complete workflow
        result = await complete_workflow(context)
        
        # Verify all steps completed
        assert result['is_valid'] is True
        assert result['user_id'] == 12345
        assert result['saved_to_db'] is True
        assert result['notification_sent'] is True
        assert result['notification_id'] == 'notif_123'
        
        # Verify external calls were made
        mock_db_conn.fetchval.assert_called_once()
        mock_http_client.post.assert_called_once()
```

### Testing with Test Fixtures

```python
# Using pytest fixtures for reusable test setup
@pytest.fixture
async def mock_database():
    """Fixture providing a mocked database connection."""
    with patch('asyncpg.connect') as mock_connect:
        mock_conn = AsyncMock()
        mock_connect.return_value = mock_conn
        mock_conn.fetchval.return_value = 12345
        yield mock_conn

@pytest.fixture
async def mock_notification_api():
    """Fixture providing a mocked notification API."""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'notif_123'}
        mock_client.post.return_value = mock_response
        
        yield mock_client

@pytest.fixture
def sample_user_data():
    """Fixture providing sample user data."""
    return {
        'email': 'test@example.com',
        'username': 'testuser',
        'password': 'securepassword123'
    }

class TestWithFixtures:
    
    @pytest.mark.asyncio
    async def test_user_registration_with_fixtures(
        self, 
        mock_database, 
        mock_notification_api, 
        sample_user_data
    ):
        """Test user registration using reusable fixtures."""
        complete_workflow = chain([
            validate_user_data,
            save_user_to_db,
            create_welcome_notification,
            send_notification
        ])
        
        context = {
            'user_data': sample_user_data,
            'api_token': 'test_token_123'
        }
        
        result = await complete_workflow(context)
        
        assert result['is_valid'] is True
        assert result['user_id'] == 12345
        assert result['notification_sent'] is True
```

## Testing Async Workflows

Handle the complexities of testing asynchronous workflows and concurrent operations.

### Testing Concurrent Operations

```python
# workflows/batch_processor.py
import asyncio

async def process_batch_items(ctx_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process multiple items concurrently."""
    items = ctx_data.get('items', [])
    
    async def process_single_item(item):
        # Simulate processing time
        await asyncio.sleep(0.1)
        return {
            'id': item['id'],
            'processed': True,
            'result': f"processed_{item['id']}"
        }
    
    # Process items concurrently
    processed_items = await asyncio.gather(
        *[process_single_item(item) for item in items]
    )
    
    result = ctx_data.copy()
    result['processed_items'] = processed_items
    result['batch_processed'] = True
    return result

class TestBatchProcessing:
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """Test that items are processed concurrently."""
        items = [
            {'id': 'item_1', 'data': 'test'},
            {'id': 'item_2', 'data': 'test'},
            {'id': 'item_3', 'data': 'test'}
        ]
        
        context = {'items': items}
        
        start_time = asyncio.get_event_loop().time()
        result = await process_batch_items(context)
        end_time = asyncio.get_event_loop().time()
        
        # Should complete in roughly 0.1 seconds (concurrent) not 0.3 (sequential)
        processing_time = end_time - start_time
        assert processing_time < 0.2, f"Processing took {processing_time}s, expected < 0.2s"
        
        # Verify all items were processed
        assert result['batch_processed'] is True
        assert len(result['processed_items']) == 3
        
        processed_ids = [item['id'] for item in result['processed_items']]
        assert 'item_1' in processed_ids
        assert 'item_2' in processed_ids
        assert 'item_3' in processed_ids
```

## Performance and Timing Tests

Test the performance characteristics of your workflows.

### Testing Execution Time

```python
import time
from datetime import datetime, timedelta

class TestPerformance:
    
    @pytest.mark.asyncio
    async def test_workflow_execution_time(self):
        """Test that workflow completes within expected time."""
        fast_workflow = chain([
            validate_user_data,
            create_user_account,
            send_welcome_email
        ])
        
        context = {
            'user_data': {
                'email': 'test@example.com',
                'username': 'testuser',
                'password': 'securepassword123'
            }
        }
        
        start_time = time.time()
        result = await fast_workflow(context)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Workflow should complete in under 1 second
        assert execution_time < 1.0, f"Workflow took {execution_time}s, expected < 1s"
        assert result['welcome_email_sent'] is True
    
    @pytest.mark.asyncio
    async def test_workflow_performance_under_load(self):
        """Test workflow performance when executed multiple times."""
        workflow = chain([validate_user_data, create_user_account])
        
        # Create multiple test contexts
        contexts = [
            {
                'user_data': {
                    'email': f'user{i}@example.com',
                    'username': f'user{i}',
                    'password': 'securepassword123'
                }
            }
            for i in range(10)
        ]
        
        start_time = time.time()
        
        # Execute workflow for all contexts concurrently
        results = await asyncio.gather(
            *[workflow(ctx) for ctx in contexts]
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete all 10 executions in reasonable time
        assert execution_time < 2.0, f"10 workflows took {execution_time}s, expected < 2s"
        assert len(results) == 10
        assert all(result['account_created'] for result in results)
```

## Test Organization Strategies

Structure your tests for maintainability and clarity.

### Grouping Related Tests

```python
class TestUserValidation:
    """Tests focused on user data validation."""
    
    # All validation-related tests here
    pass

class TestUserPersistence:
    """Tests focused on saving/loading user data."""
    
    # All database-related tests here
    pass

class TestUserNotifications:
    """Tests focused on user notifications."""
    
    # All notification-related tests here
    pass

class TestUserWorkflowIntegration:
    """Integration tests for complete user workflows."""
    
    # End-to-end workflow tests here
    pass
```

### Using Test Markers

```python
# Mark tests by category
@pytest.mark.unit
class TestUserValidation:
    pass

@pytest.mark.integration
class TestUserWorkflowIntegration:
    pass

@pytest.mark.slow
class TestPerformance:
    pass

# Run specific categories:
# pytest -m unit        # Run only unit tests
# pytest -m integration # Run only integration tests
# pytest -m "not slow"  # Skip slow tests
```

## Next Steps

Ready for advanced testing patterns? Continue with:

- **[Testing Cookbook - Advanced](testing-cookbook-advanced.md)** - Complex workflows, state management, and enterprise patterns

## Key Takeaways

1. **Mock external dependencies** to isolate your workflow logic
2. **Test error conditions** as thoroughly as success cases
3. **Use fixtures** to reduce test code duplication
4. **Test performance** to catch regressions early
5. **Organize tests logically** by functionality and test type
6. **Use async/await properly** in your test functions
7. **Test concurrent operations** to ensure they work as expected

These intermediate patterns will help you build robust, maintainable test suites for your ModuLink workflows!
