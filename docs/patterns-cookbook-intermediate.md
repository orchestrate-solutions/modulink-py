# ModuLink Patterns Cookbook - Intermediate

## Overview

This intermediate cookbook builds upon the fundamental patterns covered in the beginner guide, introducing more sophisticated orchestration techniques, middleware strategies, and architectural patterns. You'll learn to handle complex business scenarios with confidence and maintainability.

**Prerequisites:**
- Completed [Patterns Cookbook - Beginner](patterns-cookbook-beginner.md)
- Understanding of basic chain composition
- Familiarity with context flow management

**Time Investment:** 4-8 hours to master these patterns

## Table of Contents

1. [Advanced Orchestration Patterns](#advanced-orchestration-patterns)
2. [Middleware and Cross-Cutting Concerns](#middleware-and-cross-cutting-concerns)
3. [State Management Patterns](#state-management-patterns)
4. [Conditional Execution Patterns](#conditional-execution-patterns)
5. [Resource Management Patterns](#resource-management-patterns)
6. [Integration Patterns](#integration-patterns)
7. [Performance Patterns](#performance-patterns)
8. [Real-World Scenarios](#real-world-scenarios)

---

## Advanced Orchestration Patterns

### Parallel Execution with Synchronization

When you need to execute multiple independent operations and wait for all to complete:

```python
from modulink import chain
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

def parallel_processor_factory(operations):
    """Factory for creating parallel processing chains"""
    
    def execute_parallel_operations(context):
        """Execute multiple operations in parallel and collect results"""
        results = {}
        errors = []
        
        # Use ThreadPoolExecutor for I/O bound operations
        with ThreadPoolExecutor(max_workers=len(operations)) as executor:
            # Submit all operations
            future_to_name = {
                executor.submit(op, context): name 
                for name, op in operations.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_name):
                operation_name = future_to_name[future]
                try:
                    results[operation_name] = future.result()
                except Exception as e:
                    errors.append({
                        'operation': operation_name,
                        'error': str(e)
                    })
        
        return {
            **context,
            'parallel_results': results,
            'parallel_errors': errors,
            'parallel_success': len(errors) == 0
        }
    
    return execute_parallel_operations

# Usage example: Order processing with parallel validations
def validate_inventory(context):
    # Simulate inventory check
    import time
    time.sleep(0.1)  # Simulate database call
    return {'inventory_valid': True}

def validate_payment(context):
    # Simulate payment validation
    import time
    time.sleep(0.1)  # Simulate API call
    return {'payment_valid': True}

def validate_shipping(context):
    # Simulate shipping validation
    import time
    time.sleep(0.1)  # Simulate service call
    return {'shipping_valid': True}

parallel_validations = parallel_processor_factory({
    'inventory': validate_inventory,
    'payment': validate_payment,
    'shipping': validate_shipping
})

order_processing_chain = chain(
    lambda ctx: {'order_id': ctx['order_id'], 'timestamp': '2024-01-01'},
    parallel_validations,
    lambda ctx: {
        **ctx, 
        'all_validations_passed': all([
            ctx['parallel_results']['inventory']['inventory_valid'],
            ctx['parallel_results']['payment']['payment_valid'],
            ctx['parallel_results']['shipping']['shipping_valid']
        ])
    }
)
```

### Fan-Out/Fan-In Pattern

Distribute work to multiple processors and aggregate results:

```python
def fan_out_fan_in_factory(processors, aggregator):
    """Create a fan-out/fan-in processing pattern"""
    
    def fan_out_processor(context):
        """Distribute context to multiple processors"""
        results = []
        errors = []
        
        for i, processor in enumerate(processors):
            try:
                result = processor(context)
                results.append({
                    'processor_index': i,
                    'result': result,
                    'success': True
                })
            except Exception as e:
                errors.append({
                    'processor_index': i,
                    'error': str(e),
                    'success': False
                })
        
        # Aggregate results
        aggregated_result = aggregator(results, errors)
        
        return {
            **context,
            'fan_out_results': results,
            'fan_out_errors': errors,
            'aggregated_result': aggregated_result
        }
    
    return fan_out_processor

# Example: Multi-model ML prediction aggregation
def model_a_predictor(context):
    # Simulate ML model A prediction
    return {'prediction': 0.8, 'confidence': 0.9}

def model_b_predictor(context):
    # Simulate ML model B prediction
    return {'prediction': 0.75, 'confidence': 0.85}

def model_c_predictor(context):
    # Simulate ML model C prediction
    return {'prediction': 0.82, 'confidence': 0.88}

def ensemble_aggregator(results, errors):
    """Aggregate multiple model predictions using weighted average"""
    if errors:
        # Handle partial failures gracefully
        successful_results = [r for r in results if r['success']]
    else:
        successful_results = results
    
    if not successful_results:
        return {'ensemble_prediction': None, 'error': 'All models failed'}
    
    # Weighted average by confidence
    total_weight = sum(r['result']['confidence'] for r in successful_results)
    weighted_prediction = sum(
        r['result']['prediction'] * r['result']['confidence'] 
        for r in successful_results
    ) / total_weight
    
    return {
        'ensemble_prediction': weighted_prediction,
        'model_count': len(successful_results),
        'average_confidence': total_weight / len(successful_results)
    }

ml_ensemble_processor = fan_out_fan_in_factory(
    [model_a_predictor, model_b_predictor, model_c_predictor],
    ensemble_aggregator
)
```

### Dynamic Chain Assembly

Build chains dynamically based on runtime conditions:

```python
def dynamic_chain_builder(config, available_processors):
    """Build processing chain dynamically based on configuration"""
    
    def build_chain(context):
        """Build and execute chain based on context and config"""
        chain_steps = []
        
        # Determine required steps based on context
        if context.get('requires_validation'):
            chain_steps.extend(config.get('validation_steps', []))
        
        if context.get('requires_transformation'):
            chain_steps.extend(config.get('transformation_steps', []))
        
        if context.get('requires_enrichment'):
            chain_steps.extend(config.get('enrichment_steps', []))
        
        # Build the actual processing functions
        processors = []
        for step_name in chain_steps:
            if step_name in available_processors:
                processors.append(available_processors[step_name])
            else:
                raise ValueError(f"Processor '{step_name}' not available")
        
        # Execute the dynamic chain
        current_context = context
        for processor in processors:
            current_context = processor(current_context)
        
        return {
            **current_context,
            'executed_steps': chain_steps,
            'dynamic_chain_complete': True
        }
    
    return build_chain

# Configuration and available processors
processing_config = {
    'validation_steps': ['validate_schema', 'validate_business_rules'],
    'transformation_steps': ['normalize_data', 'apply_mappings'],
    'enrichment_steps': ['add_metadata', 'lookup_references']
}

available_processors = {
    'validate_schema': lambda ctx: {**ctx, 'schema_valid': True},
    'validate_business_rules': lambda ctx: {**ctx, 'business_rules_valid': True},
    'normalize_data': lambda ctx: {**ctx, 'data_normalized': True},
    'apply_mappings': lambda ctx: {**ctx, 'mappings_applied': True},
    'add_metadata': lambda ctx: {**ctx, 'metadata_added': True},
    'lookup_references': lambda ctx: {**ctx, 'references_resolved': True}
}

dynamic_processor = dynamic_chain_builder(processing_config, available_processors)
```

---

## Middleware and Cross-Cutting Concerns

### Logging Middleware Pattern

Implement comprehensive logging across your chains:

```python
import logging
import time
import uuid
from functools import wraps

def logging_middleware_factory(logger_name="modulink", log_level=logging.INFO):
    """Factory for creating logging middleware"""
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    def create_logging_wrapper(stage_name=None):
        """Create a logging wrapper for a specific stage"""
        
        def logging_wrapper(func):
            @wraps(func)
            def wrapper(context):
                # Generate correlation ID if not present
                correlation_id = context.get('correlation_id', str(uuid.uuid4()))
                
                # Create enriched context
                enriched_context = {
                    **context,
                    'correlation_id': correlation_id
                }
                
                stage = stage_name or func.__name__
                start_time = time.time()
                
                logger.info(f"[{correlation_id}] Starting stage: {stage}")
                logger.debug(f"[{correlation_id}] Input context keys: {list(context.keys())}")
                
                try:
                    result = func(enriched_context)
                    execution_time = time.time() - start_time
                    
                    logger.info(f"[{correlation_id}] Completed stage: {stage} in {execution_time:.3f}s")
                    logger.debug(f"[{correlation_id}] Output context keys: {list(result.keys())}")
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"[{correlation_id}] Failed stage: {stage} after {execution_time:.3f}s - {str(e)}")
                    raise
            
            return wrapper
        return logging_wrapper
    
    return create_logging_wrapper

# Usage example
create_logged_function = logging_middleware_factory("order_processing")

@create_logged_function("validate_order")
def validate_order(context):
    return {**context, 'order_valid': True}

@create_logged_function("process_payment")
def process_payment(context):
    return {**context, 'payment_processed': True}

@create_logged_function("fulfill_order")
def fulfill_order(context):
    return {**context, 'order_fulfilled': True}

logged_order_chain = chain(
    validate_order,
    process_payment,
    fulfill_order
)
```

### Metrics Collection Pattern

Collect performance and business metrics:

```python
from collections import defaultdict
import threading
import time

class MetricsCollector:
    """Thread-safe metrics collection for ModuLink chains"""
    
    def __init__(self):
        self._metrics = defaultdict(list)
        self._counters = defaultdict(int)
        self._lock = threading.Lock()
    
    def record_timing(self, metric_name, duration):
        """Record a timing metric"""
        with self._lock:
            self._metrics[f"{metric_name}_duration"].append(duration)
    
    def increment_counter(self, counter_name):
        """Increment a counter metric"""
        with self._lock:
            self._counters[counter_name] += 1
    
    def record_value(self, metric_name, value):
        """Record a value metric"""
        with self._lock:
            self._metrics[metric_name].append(value)
    
    def get_summary(self):
        """Get summary of all collected metrics"""
        with self._lock:
            summary = {}
            
            # Timing metrics summary
            for metric_name, values in self._metrics.items():
                if values:
                    summary[metric_name] = {
                        'count': len(values),
                        'avg': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values)
                    }
            
            # Counter summary
            summary['counters'] = dict(self._counters)
            
            return summary

# Global metrics collector
metrics = MetricsCollector()

def metrics_middleware_factory(metrics_collector):
    """Factory for creating metrics collection middleware"""
    
    def create_metrics_wrapper(stage_name=None, collect_business_metrics=None):
        """Create a metrics wrapper for a specific stage"""
        
        def metrics_wrapper(func):
            @wraps(func)
            def wrapper(context):
                stage = stage_name or func.__name__
                start_time = time.time()
                
                try:
                    result = func(context)
                    execution_time = time.time() - start_time
                    
                    # Record timing metrics
                    metrics_collector.record_timing(f"stage_{stage}", execution_time)
                    metrics_collector.increment_counter(f"stage_{stage}_success")
                    
                    # Collect business metrics if specified
                    if collect_business_metrics:
                        business_metrics = collect_business_metrics(context, result)
                        for metric_name, value in business_metrics.items():
                            metrics_collector.record_value(metric_name, value)
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    metrics_collector.record_timing(f"stage_{stage}", execution_time)
                    metrics_collector.increment_counter(f"stage_{stage}_error")
                    raise
            
            return wrapper
        return metrics_wrapper
    
    return create_metrics_wrapper

# Usage example
create_metrics_function = metrics_middleware_factory(metrics)

def collect_order_metrics(context, result):
    """Collect business-specific metrics for order processing"""
    business_metrics = {}
    
    if 'order_value' in result:
        business_metrics['order_value'] = result['order_value']
    
    if 'items_count' in result:
        business_metrics['items_count'] = result['items_count']
    
    return business_metrics

@create_metrics_function("process_order", collect_order_metrics)
def process_order(context):
    return {
        **context, 
        'order_processed': True,
        'order_value': 150.00,
        'items_count': 3
    }
```

### Circuit Breaker Pattern

Implement fault tolerance with circuit breakers:

```python
import time
from enum import Enum
from threading import Lock

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker implementation for external service calls"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self):
        """Check if enough time has passed to attempt reset"""
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            self.failure_count = 0
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

def circuit_breaker_middleware_factory(circuit_breakers):
    """Factory for creating circuit breaker middleware"""
    
    def create_circuit_breaker_wrapper(service_name):
        """Create a circuit breaker wrapper for a specific service"""
        
        def circuit_breaker_wrapper(func):
            @wraps(func)
            def wrapper(context):
                if service_name not in circuit_breakers:
                    circuit_breakers[service_name] = CircuitBreaker()
                
                circuit_breaker = circuit_breakers[service_name]
                
                try:
                    result = circuit_breaker.call(func, context)
                    return {
                        **result,
                        'circuit_breaker_state': circuit_breaker.state.value,
                        'service_available': True
                    }
                except Exception as e:
                    return {
                        **context,
                        'circuit_breaker_state': circuit_breaker.state.value,
                        'service_available': False,
                        'service_error': str(e)
                    }
            
            return wrapper
        return circuit_breaker_wrapper
    
    return create_circuit_breaker_wrapper

# Usage example
circuit_breakers = {}
create_protected_function = circuit_breaker_middleware_factory(circuit_breakers)

@create_protected_function("payment_service")
def call_payment_service(context):
    # Simulate external service call
    import random
    if random.random() < 0.3:  # 30% failure rate
        raise Exception("Payment service unavailable")
    
    return {**context, 'payment_authorized': True}

@create_protected_function("inventory_service")
def call_inventory_service(context):
    # Simulate external service call
    import random
    if random.random() < 0.2:  # 20% failure rate
        raise Exception("Inventory service unavailable")
    
    return {**context, 'inventory_reserved': True}
```

---

## State Management Patterns

### Context State Machine

Manage complex state transitions within your chains:

```python
from enum import Enum
from typing import Dict, Set, Callable

class OrderState(Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class StateMachine:
    """Generic state machine for managing context state transitions"""
    
    def __init__(self, initial_state, transitions):
        self.initial_state = initial_state
        self.transitions = transitions  # Dict[current_state, Set[allowed_next_states]]
        self.transition_handlers = {}  # Dict[transition, handler_function]
    
    def add_transition_handler(self, from_state, to_state, handler):
        """Add a handler for a specific state transition"""
        self.transition_handlers[(from_state, to_state)] = handler
    
    def create_state_processor(self, target_state):
        """Create a processor that transitions to target state"""
        
        def state_processor(context):
            current_state = context.get('state', self.initial_state)
            
            # Validate transition is allowed
            if current_state not in self.transitions:
                raise ValueError(f"Invalid current state: {current_state}")
            
            if target_state not in self.transitions[current_state]:
                raise ValueError(f"Invalid transition from {current_state} to {target_state}")
            
            # Execute transition handler if exists
            handler = self.transition_handlers.get((current_state, target_state))
            if handler:
                context = handler(context)
            
            return {
                **context,
                'previous_state': current_state,
                'state': target_state,
                'state_transition_timestamp': time.time()
            }
        
        return state_processor

# Define order processing state machine
order_transitions = {
    OrderState.PENDING: {OrderState.VALIDATED, OrderState.CANCELLED},
    OrderState.VALIDATED: {OrderState.PAID, OrderState.CANCELLED},
    OrderState.PAID: {OrderState.SHIPPED, OrderState.CANCELLED},
    OrderState.SHIPPED: {OrderState.DELIVERED},
    OrderState.DELIVERED: set(),  # Terminal state
    OrderState.CANCELLED: set()   # Terminal state
}

order_state_machine = StateMachine(OrderState.PENDING, order_transitions)

# Add transition handlers
def handle_validation_transition(context):
    """Handle transition to validated state"""
    return {
        **context,
        'validation_timestamp': time.time(),
        'validated_by': 'system'
    }

def handle_payment_transition(context):
    """Handle transition to paid state"""
    return {
        **context,
        'payment_timestamp': time.time(),
        'payment_method': context.get('payment_method', 'unknown')
    }

order_state_machine.add_transition_handler(
    OrderState.PENDING, OrderState.VALIDATED, handle_validation_transition
)
order_state_machine.add_transition_handler(
    OrderState.VALIDATED, OrderState.PAID, handle_payment_transition
)

# Create state transition processors
validate_order_state = order_state_machine.create_state_processor(OrderState.VALIDATED)
pay_order_state = order_state_machine.create_state_processor(OrderState.PAID)
ship_order_state = order_state_machine.create_state_processor(OrderState.SHIPPED)
```

### Context Snapshot and Rollback

Implement context versioning for rollback capabilities:

```python
import copy
from datetime import datetime

class ContextSnapshot:
    """Immutable snapshot of context at a point in time"""
    
    def __init__(self, context, timestamp=None, label=None):
        self.context = copy.deepcopy(context)
        self.timestamp = timestamp or datetime.now()
        self.label = label or f"snapshot_{self.timestamp.isoformat()}"
    
    def restore(self):
        """Return a copy of the snapshotted context"""
        return copy.deepcopy(self.context)

def snapshot_middleware_factory():
    """Factory for creating context snapshot middleware"""
    
    def create_snapshot_wrapper(snapshot_label=None, auto_snapshot=True):
        """Create a snapshot wrapper"""
        
        def snapshot_wrapper(func):
            @wraps(func)
            def wrapper(context):
                # Take snapshot before processing if auto_snapshot is enabled
                if auto_snapshot:
                    pre_label = f"{snapshot_label or func.__name__}_pre"
                    pre_snapshot = ContextSnapshot(context, label=pre_label)
                    
                    context = {
                        **context,
                        '_snapshots': context.get('_snapshots', []) + [pre_snapshot]
                    }
                
                try:
                    result = func(context)
                    
                    # Take snapshot after successful processing
                    post_label = f"{snapshot_label or func.__name__}_post"
                    post_snapshot = ContextSnapshot(result, label=post_label)
                    
                    return {
                        **result,
                        '_snapshots': result.get('_snapshots', []) + [post_snapshot]
                    }
                    
                except Exception as e:
                    # On error, add error information but preserve snapshots
                    raise
            
            return wrapper
        return snapshot_wrapper
    
    return create_snapshot_wrapper

def rollback_processor_factory():
    """Factory for creating rollback processors"""
    
    def create_rollback_processor(target_label=None, steps_back=1):
        """Create a processor that rolls back to a specific snapshot"""
        
        def rollback_processor(context):
            snapshots = context.get('_snapshots', [])
            
            if not snapshots:
                raise ValueError("No snapshots available for rollback")
            
            if target_label:
                # Find snapshot by label
                target_snapshot = None
                for snapshot in reversed(snapshots):
                    if snapshot.label == target_label:
                        target_snapshot = snapshot
                        break
                
                if not target_snapshot:
                    raise ValueError(f"Snapshot with label '{target_label}' not found")
            else:
                # Rollback by steps
                if len(snapshots) < steps_back:
                    raise ValueError(f"Not enough snapshots for rollback of {steps_back} steps")
                
                target_snapshot = snapshots[-(steps_back + 1)]
            
            # Restore context from snapshot
            restored_context = target_snapshot.restore()
            
            return {
                **restored_context,
                'rollback_performed': True,
                'rollback_timestamp': datetime.now(),
                'rollback_target': target_snapshot.label
            }
        
        return rollback_processor
    
    return create_rollback_processor

# Usage example
create_snapshot_function = snapshot_middleware_factory()
create_rollback_function = rollback_processor_factory()

@create_snapshot_function("data_processing")
def process_data(context):
    return {**context, 'data_processed': True, 'processing_time': time.time()}

@create_snapshot_function("validation")
def validate_processed_data(context):
    # Simulate validation that might fail
    if context.get('force_validation_error'):
        raise ValueError("Validation failed")
    
    return {**context, 'data_validated': True}

# Rollback processor for validation failures
rollback_to_processing = create_rollback_function(target_label="data_processing_post")
```

---

## Conditional Execution Patterns

### Rule-Based Execution

Implement business rule engines within your chains:

```python
from typing import Any, Callable, List, Dict

class Rule:
    """Business rule with condition and action"""
    
    def __init__(self, name: str, condition: Callable, action: Callable, priority: int = 0):
        self.name = name
        self.condition = condition
        self.action = action
        self.priority = priority
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate if rule condition is met"""
        try:
            return bool(self.condition(context))
        except Exception:
            return False
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rule action"""
        return self.action(context)

class RuleEngine:
    """Engine for managing and executing business rules"""
    
    def __init__(self):
        self.rules: List[Rule] = []
    
    def add_rule(self, rule: Rule):
        """Add a rule to the engine"""
        self.rules.append(rule)
        # Sort by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def execute_rules(self, context: Dict[str, Any], strategy: str = "first_match") -> Dict[str, Any]:
        """Execute rules based on strategy"""
        executed_rules = []
        current_context = context.copy()
        
        for rule in self.rules:
            if rule.evaluate(current_context):
                executed_rules.append(rule.name)
                current_context = rule.execute(current_context)
                
                if strategy == "first_match":
                    break
                elif strategy == "all_matching":
                    continue
        
        return {
            **current_context,
            'executed_rules': executed_rules,
            'rules_engine_complete': True
        }

def rule_engine_processor_factory(rules_config):
    """Factory for creating rule engine processors"""
    
    def create_rule_processor(strategy="first_match"):
        """Create a rule engine processor"""
        
        def rule_processor(context):
            engine = RuleEngine()
            
            # Build rules from configuration
            for rule_config in rules_config:
                rule = Rule(
                    name=rule_config['name'],
                    condition=rule_config['condition'],
                    action=rule_config['action'],
                    priority=rule_config.get('priority', 0)
                )
                engine.add_rule(rule)
            
            return engine.execute_rules(context, strategy)
        
        return rule_processor
    
    return create_rule_processor

# Example: Customer tier-based pricing rules
pricing_rules_config = [
    {
        'name': 'vip_discount',
        'condition': lambda ctx: ctx.get('customer_tier') == 'VIP',
        'action': lambda ctx: {**ctx, 'discount_rate': 0.2, 'applied_rule': 'vip_discount'},
        'priority': 100
    },
    {
        'name': 'premium_discount',
        'condition': lambda ctx: ctx.get('customer_tier') == 'Premium',
        'action': lambda ctx: {**ctx, 'discount_rate': 0.15, 'applied_rule': 'premium_discount'},
        'priority': 90
    },
    {
        'name': 'large_order_discount',
        'condition': lambda ctx: ctx.get('order_total', 0) > 500,
        'action': lambda ctx: {**ctx, 'discount_rate': 0.1, 'applied_rule': 'large_order_discount'},
        'priority': 80
    },
    {
        'name': 'new_customer_discount',
        'condition': lambda ctx: ctx.get('is_new_customer', False),
        'action': lambda ctx: {**ctx, 'discount_rate': 0.05, 'applied_rule': 'new_customer_discount'},
        'priority': 70
    }
]

pricing_rule_processor = rule_engine_processor_factory(pricing_rules_config)()
```

### Feature Flag Pattern

Implement feature toggles for gradual rollouts:

```python
import random
from typing import Dict, Any, Callable

class FeatureFlag:
    """Feature flag with various activation strategies"""
    
    def __init__(self, name: str, enabled: bool = False, strategy: str = "simple"):
        self.name = name
        self.enabled = enabled
        self.strategy = strategy
        self.config = {}
    
    def set_config(self, **kwargs):
        """Set strategy-specific configuration"""
        self.config.update(kwargs)
        return self
    
    def is_enabled(self, context: Dict[str, Any]) -> bool:
        """Check if feature is enabled for given context"""
        if not self.enabled:
            return False
        
        if self.strategy == "simple":
            return True
        elif self.strategy == "percentage":
            percentage = self.config.get('percentage', 0)
            return random.random() * 100 < percentage
        elif self.strategy == "user_list":
            user_id = context.get('user_id')
            allowed_users = self.config.get('allowed_users', [])
            return user_id in allowed_users
        elif self.strategy == "custom":
            condition = self.config.get('condition')
            return condition(context) if condition else False
        
        return False

class FeatureFlagManager:
    """Manager for feature flags"""
    
    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
    
    def add_flag(self, flag: FeatureFlag):
        """Add a feature flag"""
        self.flags[flag.name] = flag
    
    def is_enabled(self, flag_name: str, context: Dict[str, Any]) -> bool:
        """Check if feature flag is enabled"""
        flag = self.flags.get(flag_name)
        return flag.is_enabled(context) if flag else False

def feature_flag_processor_factory(feature_manager):
    """Factory for creating feature flag processors"""
    
    def create_feature_processor(flag_name: str, enabled_processor: Callable, disabled_processor: Callable = None):
        """Create a processor that executes based on feature flag"""
        
        def feature_processor(context):
            if feature_manager.is_enabled(flag_name, context):
                result = enabled_processor(context)
                return {**result, f'feature_{flag_name}_enabled': True}
            else:
                if disabled_processor:
                    result = disabled_processor(context)
                else:
                    result = context
                return {**result, f'feature_{flag_name}_enabled': False}
        
        return feature_processor
    
    return create_feature_processor

# Example: Feature flag setup
feature_manager = FeatureFlagManager()

# Add various feature flags
feature_manager.add_flag(
    FeatureFlag("new_recommendation_engine", enabled=True, strategy="percentage")
    .set_config(percentage=50)
)

feature_manager.add_flag(
    FeatureFlag("premium_features", enabled=True, strategy="user_list")
    .set_config(allowed_users=["user123", "user456", "user789"])
)

feature_manager.add_flag(
    FeatureFlag("beta_checkout", enabled=True, strategy="custom")
    .set_config(condition=lambda ctx: ctx.get('customer_tier') in ['VIP', 'Premium'])
)

create_feature_processor = feature_flag_processor_factory(feature_manager)

# Feature-flagged processors
def new_recommendation_processor(context):
    return {**context, 'recommendations': ['item1', 'item2', 'item3'], 'engine_version': 'v2'}

def old_recommendation_processor(context):
    return {**context, 'recommendations': ['itemA', 'itemB'], 'engine_version': 'v1'}

recommendation_processor = create_feature_processor(
    "new_recommendation_engine",
    new_recommendation_processor,
    old_recommendation_processor
)
```

---

## Real-World Scenarios

### E-commerce Order Processing Pipeline

Let's put it all together in a comprehensive e-commerce example:

```python
# Complete e-commerce order processing with all patterns
from modulink import chain

# Setup feature flags and rules
feature_manager = FeatureFlagManager()
feature_manager.add_flag(
    FeatureFlag("fraud_detection_v2", enabled=True, strategy="percentage")
    .set_config(percentage=75)
)

# Setup metrics collection
metrics = MetricsCollector()
create_metrics_function = metrics_middleware_factory(metrics)
create_logged_function = logging_middleware_factory("ecommerce")
create_feature_processor = feature_flag_processor_factory(feature_manager)

# Circuit breakers for external services
circuit_breakers = {}
create_protected_function = circuit_breaker_middleware_factory(circuit_breakers)

# Core processing functions
@create_logged_function("order_validation")
@create_metrics_function("order_validation")
def validate_order(context):
    """Validate order structure and business rules"""
    order = context.get('order', {})
    
    # Basic validation
    if not order.get('items'):
        raise ValueError("Order must contain items")
    
    if not order.get('customer_id'):
        raise ValueError("Order must have customer ID")
    
    return {
        **context,
        'order_valid': True,
        'validation_timestamp': time.time()
    }

@create_protected_function("inventory_service")
@create_logged_function("inventory_check")
def check_inventory(context):
    """Check item availability"""
    # Simulate inventory service call
    items = context['order']['items']
    
    for item in items:
        # Simulate occasional inventory issues
        if random.random() < 0.1:
            raise Exception(f"Item {item['id']} out of stock")
    
    return {
        **context,
        'inventory_confirmed': True,
        'reserved_items': items
    }

# Fraud detection with feature flagging
def fraud_detection_v1(context):
    """Legacy fraud detection"""
    return {**context, 'fraud_score': 0.1, 'fraud_engine': 'v1'}

def fraud_detection_v2(context):
    """New fraud detection engine"""
    return {**context, 'fraud_score': 0.05, 'fraud_engine': 'v2'}

fraud_detection_processor = create_feature_processor(
    "fraud_detection_v2",
    fraud_detection_v2,
    fraud_detection_v1
)

@create_protected_function("payment_service")
@create_logged_function("payment_processing")
def process_payment(context):
    """Process payment with circuit breaker protection"""
    fraud_score = context.get('fraud_score', 0)
    
    if fraud_score > 0.8:
        raise Exception("Payment blocked due to fraud risk")
    
    # Simulate payment processing
    if random.random() < 0.05:  # 5% payment failure rate
        raise Exception("Payment processing failed")
    
    return {
        **context,
        'payment_processed': True,
        'transaction_id': f"txn_{int(time.time())}"
    }

@create_logged_function("order_fulfillment")
def fulfill_order(context):
    """Fulfill the order"""
    return {
        **context,
        'order_fulfilled': True,
        'fulfillment_timestamp': time.time(),
        'estimated_delivery': time.time() + (24 * 60 * 60)  # 24 hours from now
    }

# Error handling and fallback
def handle_order_failure(context):
    """Handle order processing failures gracefully"""
    error_info = context.get('error_info', {})
    
    return {
        **context,
        'order_status': 'failed',
        'failure_reason': error_info.get('message', 'Unknown error'),
        'requires_manual_review': True
    }

# Build the complete order processing chain
def build_order_processing_chain():
    """Build the complete order processing chain with error handling"""
    
    def order_processor(context):
        try:
            # Main processing chain
            result = chain(
                validate_order,
                check_inventory,
                fraud_detection_processor,
                process_payment,
                fulfill_order
            )(context)
            
            return {
                **result,
                'order_status': 'completed',
                'processing_complete': True
            }
            
        except Exception as e:
            # Handle failures gracefully
            error_context = {
                **context,
                'error_info': {
                    'message': str(e),
                    'timestamp': time.time()
                }
            }
            return handle_order_failure(error_context)
    
    return order_processor

# Usage example
order_processing_chain = build_order_processing_chain()

# Test with sample order
sample_order = {
    'order': {
        'id': 'order_123',
        'customer_id': 'customer_456',
        'items': [
            {'id': 'item_1', 'quantity': 2, 'price': 25.00},
            {'id': 'item_2', 'quantity': 1, 'price': 50.00}
        ],
        'total': 100.00
    },
    'customer_tier': 'Premium',
    'user_id': 'user123'
}

# Process the order
result = order_processing_chain(sample_order)

# View metrics summary
print("Processing Metrics:")
print(metrics.get_summary())
```

## Summary

This intermediate cookbook has introduced sophisticated patterns for:

- **Advanced Orchestration**: Parallel execution, fan-out/fan-in, and dynamic chain assembly
- **Middleware Patterns**: Logging, metrics collection, and circuit breakers for resilient applications
- **State Management**: State machines and context snapshots for complex business processes
- **Conditional Execution**: Rule engines and feature flags for flexible business logic
- **Real-World Integration**: Comprehensive e-commerce example combining all patterns

These patterns provide the foundation for building robust, maintainable, and scalable applications with ModuLink's chain-based architecture.

**Next Steps:**
- Explore [Patterns Cookbook - Advanced](patterns-cookbook-advanced.md) for enterprise-scale patterns
- Review your existing applications to identify opportunities for pattern application
- Practice implementing these patterns in isolation before combining them

**Remember**: Start with simple patterns and gradually introduce complexity as your understanding deepens. Each pattern solves specific problems - use them judiciously based on your actual requirements.
