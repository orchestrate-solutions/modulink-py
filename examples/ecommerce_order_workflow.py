"""
E-commerce Order Processing Workflow Demo

This example demonstrates a complex, real-world e-commerce order processing
system using ModuLink chains. It includes:

- User authentication and authorization
- Inventory management
- Payment processing
- Order fulfillment
- Email notifications
- Analytics tracking
- Error handling and rollback mechanisms
- Audit logging
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

# Import ModuLink
from modulink import chain, when, parallel, catch_errors, ctx
from modulink.utils import (
    timing, logging, validate, performance_tracker,
    transform, set_values, validators, error_handlers
)

# Export all testable functions and classes
__all__ = [
    # Enums and Data Classes
    'PaymentStatus', 'OrderStatus', 'Product', 'OrderItem', 'Order',
    
    # Database and State
    'USERS_DB', 'PRODUCTS_DB', 'ORDERS_DB', 'INVENTORY_DB', 'AUDIT_LOG',
    
    # Core Workflow Functions
    'authenticate_user', 'authorize_order_creation', 'validate_order_items',
    'reserve_inventory', 'process_payment', 'create_order_record',
    'initiate_fulfillment', 'calculate_shipping', 'send_order_confirmation_email',
    'send_internal_notifications', 'track_order_analytics', 'audit_log_order',
    
    # Error Handlers
    'handle_payment_failure', 'handle_inventory_failure',
    
    # Chain Creation
    'create_order_processing_chain',
    
    # Demo Functions
    'demo_successful_order', 'demo_payment_failure', 'demo_inventory_shortage',
    'demo_large_vip_order', 'print_system_state',
    
    # Utility Functions
    'reset_system_state', 'get_system_metrics'
]

# Mock external services
class PaymentStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    FAILED = "failed"

class OrderStatus(Enum):
    CREATED = "created"
    VALIDATED = "validated"
    PAYMENT_PROCESSING = "payment_processing"
    PAID = "paid"
    FULFILLING = "fulfilling"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"

@dataclass
class Product:
    id: str
    name: str
    price: float
    stock_quantity: int
    category: str

@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: float

@dataclass
class Order:
    id: str
    user_id: str
    items: List[OrderItem]
    total_amount: float
    status: OrderStatus
    created_at: datetime
    payment_method: str
    shipping_address: Dict[str, str]

# Mock databases
USERS_DB = {
    "user_123": {
        "id": "user_123",
        "email": "john@example.com",
        "name": "John Doe",
        "is_premium": True,
        "credit_limit": 5000.0,
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip": "12345"
        }
    },
    "user_456": {
        "id": "user_456",
        "email": "jane@example.com",
        "name": "Jane Smith",
        "is_premium": False,
        "credit_limit": 1000.0,
        "address": {
            "street": "456 Oak Ave",
            "city": "Somewhere",
            "state": "NY",
            "zip": "67890"
        }
    }
}

PRODUCTS_DB = {
    "prod_001": Product("prod_001", "Laptop", 999.99, 50, "Electronics"),
    "prod_002": Product("prod_002", "Mouse", 29.99, 200, "Electronics"),
    "prod_003": Product("prod_003", "Book", 19.99, 100, "Books"),
    "prod_004": Product("prod_004", "Coffee Mug", 12.99, 75, "Home")
}

ORDERS_DB = {}
INVENTORY_DB = {product_id: product.stock_quantity for product_id, product in PRODUCTS_DB.items()}
AUDIT_LOG = []

# Authentication and Authorization Links
async def authenticate_user(context: Dict[str, Any]) -> Dict[str, Any]:
    """Authenticate user and add user info to context."""
    user_id = context.get("user_id")
    
    if not user_id:
        raise ValueError("User ID is required")
    
    user = USERS_DB.get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    return {
        **context,
        "user": user,
        "authenticated": True,
        "_metadata": {
            **context.get("_metadata", {}),
            "auth_timestamp": datetime.now().isoformat()
        }
    }

async def authorize_order_creation(context: Dict[str, Any]) -> Dict[str, Any]:
    """Check if user is authorized to create orders."""
    user = context.get("user", {})
    order_total = context.get("order_total", 0)
    
    # Check credit limit for non-premium users
    if not user.get("is_premium", False) and order_total > user.get("credit_limit", 0):
        raise ValueError(f"Order total ${order_total} exceeds credit limit ${user.get('credit_limit', 0)}")
    
    return {
        **context,
        "authorized": True
    }

# Order Validation Links
async def validate_order_items(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that all order items exist and are available."""
    items = context.get("order_items", [])
    
    if not items:
        raise ValueError("Order must contain at least one item")
    
    validated_items = []
    total_amount = 0.0
    
    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 0)
        
        if not product_id or quantity <= 0:
            raise ValueError(f"Invalid item: {item}")
        
        product = PRODUCTS_DB.get(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        if INVENTORY_DB.get(product_id, 0) < quantity:
            raise ValueError(f"Insufficient stock for {product.name}. Available: {INVENTORY_DB.get(product_id, 0)}, Requested: {quantity}")
        
        validated_items.append(OrderItem(
            product_id=product_id,
            quantity=quantity,
            unit_price=product.price
        ))
        total_amount += product.price * quantity
    
    return {
        **context,
        "validated_items": validated_items,
        "order_total": total_amount,
        "validation_passed": True
    }

async def reserve_inventory(context: Dict[str, Any]) -> Dict[str, Any]:
    """Reserve inventory for the order items."""
    validated_items = context.get("validated_items", [])
    reservations = []
    
    try:
        for item in validated_items:
            current_stock = INVENTORY_DB.get(item.product_id, 0)
            if current_stock >= item.quantity:
                INVENTORY_DB[item.product_id] = current_stock - item.quantity
                reservations.append({
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "reserved_at": datetime.now().isoformat()
                })
            else:
                # Rollback previous reservations
                for prev_reservation in reservations:
                    INVENTORY_DB[prev_reservation["product_id"]] += prev_reservation["quantity"]
                raise ValueError(f"Failed to reserve inventory for {item.product_id}")
        
        return {
            **context,
            "inventory_reservations": reservations,
            "inventory_reserved": True
        }
    except Exception as e:
        # Rollback any partial reservations
        for reservation in reservations:
            INVENTORY_DB[reservation["product_id"]] += reservation["quantity"]
        raise e

# Payment Processing Links
async def process_payment(context: Dict[str, Any]) -> Dict[str, Any]:
    """Process payment for the order."""
    order_total = context.get("order_total", 0)
    payment_method = context.get("payment_method", "credit_card")
    user = context.get("user", {})
    
    # Simulate payment processing time
    await asyncio.sleep(0.1)
    
    # Simulate payment scenarios
    if order_total > 2000:
        # Large orders need manual approval
        payment_status = PaymentStatus.PENDING
    elif user.get("email", "").endswith("@test.com"):
        # Test accounts get declined
        payment_status = PaymentStatus.DECLINED
    elif order_total < 10:
        # Very small orders might fail
        payment_status = PaymentStatus.FAILED
    else:
        payment_status = PaymentStatus.APPROVED
    
    if payment_status == PaymentStatus.DECLINED:
        raise ValueError("Payment was declined")
    elif payment_status == PaymentStatus.FAILED:
        raise ValueError("Payment processing failed")
    
    payment_id = f"pay_{int(time.time() * 1000)}"
    
    return {
        **context,
        "payment_status": payment_status.value,
        "payment_id": payment_id,
        "payment_processed": True,
        "payment_timestamp": datetime.now().isoformat()
    }

# Order Creation Links
async def create_order_record(context: Dict[str, Any]) -> Dict[str, Any]:
    """Create the order record in the database."""
    order_id = f"order_{int(time.time() * 1000)}"
    user = context.get("user", {})
    validated_items = context.get("validated_items", [])
    
    order = Order(
        id=order_id,
        user_id=user.get("id"),
        items=validated_items,
        total_amount=context.get("order_total", 0),
        status=OrderStatus.PAID if context.get("payment_processed") else OrderStatus.CREATED,
        created_at=datetime.now(),
        payment_method=context.get("payment_method", "credit_card"),
        shipping_address=context.get("shipping_address", user.get("address", {}))
    )
    
    ORDERS_DB[order_id] = order
    
    return {
        **context,
        "order": asdict(order),
        "order_id": order_id,
        "order_created": True
    }

# Fulfillment Links
async def initiate_fulfillment(context: Dict[str, Any]) -> Dict[str, Any]:
    """Initiate order fulfillment process."""
    order_id = context.get("order_id")
    order = ORDERS_DB.get(order_id)
    
    if not order:
        raise ValueError(f"Order {order_id} not found")
    
    # Simulate fulfillment initiation
    fulfillment_id = f"fulfill_{int(time.time() * 1000)}"
    estimated_ship_date = datetime.now() + timedelta(days=2)
    
    order.status = OrderStatus.FULFILLING
    
    return {
        **context,
        "fulfillment_id": fulfillment_id,
        "estimated_ship_date": estimated_ship_date.isoformat(),
        "fulfillment_initiated": True
    }

async def calculate_shipping(context: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate shipping costs and estimated delivery."""
    order = context.get("order", {})
    shipping_address = order.get("shipping_address", {})
    
    # Simple shipping calculation
    base_shipping = 5.99
    order_total = order.get("total_amount", 0)
    
    # Free shipping for orders over $50
    shipping_cost = 0.0 if order_total > 50 else base_shipping
    
    # Estimate delivery based on state
    state = shipping_address.get("state", "CA")
    if state in ["CA", "NV", "AZ"]:
        estimated_delivery_days = 1
    elif state in ["OR", "WA", "UT", "TX"]:
        estimated_delivery_days = 2
    else:
        estimated_delivery_days = 3
    
    estimated_delivery = datetime.now() + timedelta(days=estimated_delivery_days)
    
    return {
        **context,
        "shipping_cost": shipping_cost,
        "estimated_delivery": estimated_delivery.isoformat(),
        "estimated_delivery_days": estimated_delivery_days
    }

# Notification Links
async def send_order_confirmation_email(context: Dict[str, Any]) -> Dict[str, Any]:
    """Send order confirmation email to customer."""
    user = context.get("user", {})
    order = context.get("order", {})
    
    # Simulate email sending
    email_content = {
        "to": user.get("email"),
        "subject": f"Order Confirmation - #{order.get('id')}",
        "template": "order_confirmation",
        "data": {
            "customer_name": user.get("name"),
            "order_id": order.get("id"),
            "total_amount": order.get("total_amount"),
            "estimated_delivery": context.get("estimated_delivery")
        }
    }
    
    # Simulate email service
    await asyncio.sleep(0.05)
    
    return {
        **context,
        "confirmation_email_sent": True,
        "confirmation_email": email_content
    }

async def send_internal_notifications(context: Dict[str, Any]) -> Dict[str, Any]:
    """Send notifications to internal teams."""
    order = context.get("order", {})
    
    notifications = []
    
    # Notify fulfillment team
    notifications.append({
        "team": "fulfillment",
        "type": "new_order",
        "order_id": order.get("id"),
        "priority": "high" if order.get("total_amount", 0) > 500 else "normal"
    })
    
    # Notify customer service for large orders
    if order.get("total_amount", 0) > 1000:
        notifications.append({
            "team": "customer_service",
            "type": "vip_order",
            "order_id": order.get("id"),
            "customer_email": context.get("user", {}).get("email")
        })
    
    return {
        **context,
        "internal_notifications": notifications,
        "notifications_sent": True
    }

# Analytics and Logging Links
async def track_order_analytics(context: Dict[str, Any]) -> Dict[str, Any]:
    """Track order analytics and metrics."""
    order = context.get("order", {})
    user = context.get("user", {})
    
    analytics_event = {
        "event_type": "order_created",
        "timestamp": datetime.now().isoformat(),
        "user_id": user.get("id"),
        "order_id": order.get("id"),
        "order_value": order.get("total_amount"),
        "item_count": len(order.get("items", [])),
        "user_type": "premium" if user.get("is_premium") else "standard",
        "payment_method": order.get("payment_method"),
        "shipping_state": order.get("shipping_address", {}).get("state")
    }
    
    return {
        **context,
        "analytics_tracked": True,
        "analytics_event": analytics_event
    }

async def audit_log_order(context: Dict[str, Any]) -> Dict[str, Any]:
    """Create audit log entry for the order."""
    order = context.get("order", {})
    user = context.get("user", {})
    
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "order_created",
        "user_id": user.get("id"),
        "order_id": order.get("id"),
        "order_total": order.get("total_amount"),
        "ip_address": context.get("client_ip", "unknown"),
        "user_agent": context.get("user_agent", "unknown"),
        "processing_time_ms": context.get("_metadata", {}).get("performance", {}).get("total_time", 0)
    }
    
    AUDIT_LOG.append(audit_entry)
    
    return {
        **context,
        "audit_logged": True,
        "audit_entry": audit_entry
    }

# Error Handling Links
async def handle_payment_failure(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle payment failure by releasing inventory and notifying customer."""
    if "error" in context and "payment" in str(context["error"]).lower():
        # Release reserved inventory
        reservations = context.get("inventory_reservations", [])
        for reservation in reservations:
            INVENTORY_DB[reservation["product_id"]] += reservation["quantity"]
        
        # Notify customer of payment failure
        user = context.get("user", {})
        if user:
            context["payment_failure_notification"] = {
                "to": user.get("email"),
                "subject": "Payment Failed - Order Not Processed",
                "message": "We were unable to process your payment. Please try again."
            }
        
        context["inventory_released"] = True
        context["payment_failure_handled"] = True
    
    return context

async def handle_inventory_failure(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle inventory failure by notifying customer and suggesting alternatives."""
    if "error" in context and "inventory" in str(context["error"]).lower():
        user = context.get("user", {})
        if user:
            context["inventory_failure_notification"] = {
                "to": user.get("email"),
                "subject": "Item Unavailable - Order Cannot Be Completed",
                "message": "Some items in your order are no longer available."
            }
        
        context["inventory_failure_handled"] = True
    
    return context

# Create the main order processing chain
def create_order_processing_chain():
    """Create the complete order processing chain with middleware."""
    
    # Main order processing chain
    main_chain = chain(
        # Authentication and Authorization
        authenticate_user,
        authorize_order_creation,
        
        # Order Validation
        validate_order_items,
        reserve_inventory,
        
        # Payment Processing
        process_payment,
        
        # Order Creation
        create_order_record,
        
        # Fulfillment
        parallel(
            initiate_fulfillment,
            calculate_shipping
        ),
        
        # Notifications
        parallel(
            send_order_confirmation_email,
            send_internal_notifications
        ),
        
        # Analytics and Auditing
        parallel(
            track_order_analytics,
            audit_log_order
        )
    )
    
    # Add middleware
    main_chain.use(timing("order_processing"))
    main_chain.use(logging(log_input=True, log_output=True, log_timing=True))
    main_chain.use(performance_tracker())
    
    # Add error handling
    main_chain.use(catch_errors(handle_payment_failure))
    main_chain.use(catch_errors(handle_inventory_failure))
    
    return main_chain

# Demo functions
async def demo_successful_order():
    """Demo a successful order processing workflow."""
    print("\n=== DEMO: Successful Order Processing ===")
    
    order_chain = create_order_processing_chain()
    
    # Create order context
    order_context = ctx(
        user_id="user_123",
        order_items=[
            {"product_id": "prod_001", "quantity": 1},  # Laptop
            {"product_id": "prod_002", "quantity": 2}   # Mouse
        ],
        payment_method="credit_card",
        shipping_address=None,  # Will use user's default address
        client_ip="192.168.1.1",
        user_agent="Mozilla/5.0..."
    )
    
    result = await order_chain(order_context)
    
    print(f"Order Status: {'SUCCESS' if not result.get('error') else 'FAILED'}")
    if result.get("order_created"):
        print(f"Order ID: {result.get('order_id')}")
        print(f"Total Amount: ${result.get('order_total'):.2f}")
        print(f"Payment ID: {result.get('payment_id')}")
        print(f"Estimated Delivery: {result.get('estimated_delivery')}")
    
    if result.get("error"):
        print(f"Error: {result['error']}")
    
    return result

async def demo_payment_failure():
    """Demo order processing with payment failure."""
    print("\n=== DEMO: Payment Failure Handling ===")
    
    order_chain = create_order_processing_chain()
    
    # Create order context with test email (will trigger payment decline)
    order_context = ctx(
        user_id="user_456",  # Non-premium user
        order_items=[
            {"product_id": "prod_001", "quantity": 1}  # Laptop - will be declined
        ],
        payment_method="credit_card",
        client_ip="192.168.1.2"
    )
    
    # Change user email to trigger payment decline
    USERS_DB["user_456"]["email"] = "jane@test.com"
    
    result = await order_chain(order_context)
    
    print(f"Order Status: {'FAILED (Expected)' if result.get('error') else 'UNEXPECTED SUCCESS'}")
    print(f"Error: {result.get('error', 'No error')}")
    print(f"Payment Failure Handled: {result.get('payment_failure_handled', False)}")
    print(f"Inventory Released: {result.get('inventory_released', False)}")
    
    # Restore email
    USERS_DB["user_456"]["email"] = "jane@example.com"
    
    return result

async def demo_inventory_shortage():
    """Demo order processing with inventory shortage."""
    print("\n=== DEMO: Inventory Shortage Handling ===")
    
    # Temporarily reduce inventory
    original_stock = INVENTORY_DB["prod_001"]
    INVENTORY_DB["prod_001"] = 0
    
    order_chain = create_order_processing_chain()
    
    order_context = ctx(
        user_id="user_123",
        order_items=[
            {"product_id": "prod_001", "quantity": 1}  # Laptop - out of stock
        ],
        payment_method="credit_card"
    )
    
    result = await order_chain(order_context)
    
    print(f"Order Status: {'FAILED (Expected)' if result.get('error') else 'UNEXPECTED SUCCESS'}")
    print(f"Error: {result.get('error', 'No error')}")
    print(f"Inventory Failure Handled: {result.get('inventory_failure_handled', False)}")
    
    # Restore inventory
    INVENTORY_DB["prod_001"] = original_stock
    
    return result

async def demo_large_vip_order():
    """Demo processing a large VIP order."""
    print("\n=== DEMO: Large VIP Order Processing ===")
    
    order_chain = create_order_processing_chain()
    
    order_context = ctx(
        user_id="user_123",  # Premium user
        order_items=[
            {"product_id": "prod_001", "quantity": 3},  # 3 Laptops
            {"product_id": "prod_002", "quantity": 10}, # 10 Mice
            {"product_id": "prod_003", "quantity": 5}   # 5 Books
        ],
        payment_method="credit_card"
    )
    
    result = await order_chain(order_context)
    
    print(f"Order Status: {'SUCCESS' if not result.get('error') else 'FAILED'}")
    if result.get("order_created"):
        print(f"Order ID: {result.get('order_id')}")
        print(f"Total Amount: ${result.get('order_total'):.2f}")
        print(f"VIP Notifications: {len([n for n in result.get('internal_notifications', []) if n.get('type') == 'vip_order'])}")
        print(f"Free Shipping: {'Yes' if result.get('shipping_cost', 0) == 0 else 'No'}")
    
    return result

def print_system_state():
    """Print current system state for debugging."""
    print("\n=== SYSTEM STATE ===")
    print("Inventory Levels:")
    for product_id, stock in INVENTORY_DB.items():
        product = PRODUCTS_DB[product_id]
        print(f"  {product.name}: {stock} units")
    
    print(f"\nOrders Created: {len(ORDERS_DB)}")
    print(f"Audit Log Entries: {len(AUDIT_LOG)}")

def reset_system_state():
    """Reset system state to initial values for testing."""
    global ORDERS_DB, AUDIT_LOG, INVENTORY_DB
    
    ORDERS_DB.clear()
    AUDIT_LOG.clear()
    
    # Reset inventory to original values
    INVENTORY_DB.update({
        "prod_001": 50,  # Laptop
        "prod_002": 200, # Mouse
        "prod_003": 100, # Book
        "prod_004": 75   # Coffee Mug
    })
    
    # Reset user states if needed
    USERS_DB["user_456"]["email"] = "jane@example.com"

def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics for testing."""
    return {
        "total_orders": len(ORDERS_DB),
        "total_audit_entries": len(AUDIT_LOG),
        "inventory_levels": dict(INVENTORY_DB),
        "total_inventory_value": sum(
            PRODUCTS_DB[pid].price * stock 
            for pid, stock in INVENTORY_DB.items()
        ),
        "orders_by_status": {
            status.value: len([o for o in ORDERS_DB.values() if o.status == status])
            for status in OrderStatus
        }
    }

async def main():
    """Run all demos."""
    print("🛒 E-commerce Order Processing Workflow Demo")
    print("=" * 50)
    
    # Show initial system state
    print_system_state()
    
    # Run demos
    await demo_successful_order()
    await demo_payment_failure()
    await demo_inventory_shortage()
    await demo_large_vip_order()
    
    # Show final system state
    print_system_state()
    
    print("\n✅ All demos completed!")

if __name__ == "__main__":
    asyncio.run(main())
