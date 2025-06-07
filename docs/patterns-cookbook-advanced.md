# ModuLink Advanced Patterns Cookbook

## Table of Contents
1. [Enterprise Architecture Patterns](#enterprise-architecture-patterns)
2. [Performance Optimization](#performance-optimization)
3. [Scalability Patterns](#scalability-patterns)
4. [Production Deployment Strategies](#production-deployment-strategies)
5. [Security Patterns](#security-patterns)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Real-World Case Studies](#real-world-case-studies)

## Overview

This advanced cookbook covers enterprise-grade patterns, performance optimization techniques, and production deployment strategies for ModuLink applications. These patterns are designed for large-scale systems requiring high availability, performance, and maintainability.

**Prerequisites:**
- Completion of [Beginner](patterns-cookbook-beginner.md) and [Intermediate](patterns-cookbook-intermediate.md) cookbooks
- Understanding of distributed systems concepts
- Experience with production deployment environments

---

## Enterprise Architecture Patterns

### 1. Microservice Chain Orchestration

```python
from modulink import ModuLink
from typing import Dict, Any, List
import asyncio
import aiohttp
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ServiceEndpoint:
    name: str
    url: str
    timeout: int = 30
    retry_count: int = 3
    circuit_breaker_threshold: int = 5

class MicroserviceOrchestrator:
    def __init__(self, services: List[ServiceEndpoint]):
        self.services = {service.name: service for service in services}
        self.circuit_breakers = {}
        self.performance_metrics = {}
    
    def create_service_chain(self, service_flow: List[str]) -> ModuLink:
        """Create a chain that orchestrates multiple microservices"""
        chain = ModuLink()
        
        for service_name in service_flow:
            if service_name not in self.services:
                raise ValueError(f"Unknown service: {service_name}")
            
            chain.link(self._create_service_function(service_name))
        
        return chain
    
    def _create_service_function(self, service_name: str):
        service = self.services[service_name]
        
        async def service_call(context: Dict[str, Any]) -> Dict[str, Any]:
            # Circuit breaker check
            if self._is_circuit_open(service_name):
                raise Exception(f"Circuit breaker open for {service_name}")
            
            start_time = datetime.now()
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        service.url,
                        json=context,
                        timeout=aiohttp.ClientTimeout(total=service.timeout)
                    ) as response:
                        result = await response.json()
                        
                        # Record success
                        self._record_success(service_name, start_time)
                        
                        return {**context, f"{service_name}_result": result}
            
            except Exception as e:
                # Record failure
                self._record_failure(service_name, start_time)
                raise Exception(f"Service {service_name} failed: {str(e)}")
        
        return service_call
    
    def _is_circuit_open(self, service_name: str) -> bool:
        breaker = self.circuit_breakers.get(service_name, {})
        failure_count = breaker.get('failure_count', 0)
        last_failure = breaker.get('last_failure')
        
        if failure_count >= self.services[service_name].circuit_breaker_threshold:
            if last_failure and datetime.now() - last_failure < timedelta(minutes=5):
                return True
        
        return False
    
    def _record_success(self, service_name: str, start_time: datetime):
        duration = (datetime.now() - start_time).total_seconds()
        
        # Reset circuit breaker
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name]['failure_count'] = 0
        
        # Record metrics
        metrics = self.performance_metrics.setdefault(service_name, {
            'total_calls': 0,
            'success_calls': 0,
            'total_duration': 0,
            'avg_duration': 0
        })
        
        metrics['total_calls'] += 1
        metrics['success_calls'] += 1
        metrics['total_duration'] += duration
        metrics['avg_duration'] = metrics['total_duration'] / metrics['total_calls']
    
    def _record_failure(self, service_name: str, start_time: datetime):
        # Update circuit breaker
        breaker = self.circuit_breakers.setdefault(service_name, {
            'failure_count': 0,
            'last_failure': None
        })
        breaker['failure_count'] += 1
        breaker['last_failure'] = datetime.now()
        
        # Record metrics
        metrics = self.performance_metrics.setdefault(service_name, {
            'total_calls': 0,
            'success_calls': 0,
            'total_duration': 0,
            'avg_duration': 0
        })
        metrics['total_calls'] += 1

# Usage Example
services = [
    ServiceEndpoint("user_service", "http://user-service:8001/process"),
    ServiceEndpoint("payment_service", "http://payment-service:8002/process"),
    ServiceEndpoint("inventory_service", "http://inventory-service:8003/process"),
    ServiceEndpoint("notification_service", "http://notification-service:8004/process")
]

orchestrator = MicroserviceOrchestrator(services)
order_processing_chain = orchestrator.create_service_chain([
    "user_service",
    "inventory_service", 
    "payment_service",
    "notification_service"
])

# Execute with error handling
try:
    result = await order_processing_chain.execute({
        "order_id": "ORD-12345",
        "user_id": "USR-67890",
        "items": [{"product_id": "PROD-001", "quantity": 2}]
    })
    print("Order processed successfully:", result)
except Exception as e:
    print("Order processing failed:", e)
```

### 2. Event-Driven Chain Architecture

```python
from modulink import ModuLink
from typing import Dict, Any, Callable, List
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid

class EventPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Event:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str = ""
    source: str = ""

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_store: List[Event] = []
        self.processing_chains: Dict[str, ModuLink] = {}
    
    def subscribe(self, event_type: str, chain: ModuLink):
        """Subscribe a chain to handle specific event types"""
        self.processing_chains[event_type] = chain
        
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(self._create_chain_handler(chain))
    
    def _create_chain_handler(self, chain: ModuLink):
        async def handler(event: Event):
            try:
                context = {
                    "event": event,
                    "event_data": event.payload,
                    "correlation_id": event.correlation_id,
                    "timestamp": event.timestamp
                }
                
                result = await chain.execute(context)
                
                # Publish completion event
                completion_event = Event(
                    type=f"{event.type}_completed",
                    payload={"original_event_id": event.id, "result": result},
                    correlation_id=event.correlation_id,
                    source="event_processor"
                )
                
                await self.publish(completion_event)
                
            except Exception as e:
                # Publish error event
                error_event = Event(
                    type=f"{event.type}_failed",
                    payload={
                        "original_event_id": event.id,
                        "error": str(e),
                        "event_data": event.payload
                    },
                    priority=EventPriority.HIGH,
                    correlation_id=event.correlation_id,
                    source="event_processor"
                )
                
                await self.publish(error_event)
        
        return handler
    
    async def publish(self, event: Event):
        """Publish an event to all subscribers"""
        self.event_store.append(event)
        
        handlers = self.subscribers.get(event.type, [])
        if handlers:
            # Execute handlers based on priority
            sorted_handlers = sorted(
                handlers, 
                key=lambda h: event.priority.value, 
                reverse=True
            )
            
            # Execute critical events immediately, others can be queued
            if event.priority == EventPriority.CRITICAL:
                await asyncio.gather(*[handler(event) for handler in sorted_handlers])
            else:
                # Queue for async processing
                asyncio.create_task(
                    asyncio.gather(*[handler(event) for handler in sorted_handlers])
                )

# Event Processing Chains
def create_user_registration_chain() -> ModuLink:
    """Chain to process user registration events"""
    
    def validate_user_data(context: Dict[str, Any]) -> Dict[str, Any]:
        user_data = context["event_data"]
        
        required_fields = ["email", "username", "password"]
        for field in required_fields:
            if field not in user_data:
                raise ValueError(f"Missing required field: {field}")
        
        return {**context, "validation_passed": True}
    
    def create_user_account(context: Dict[str, Any]) -> Dict[str, Any]:
        user_data = context["event_data"]
        
        # Simulate user creation
        user_id = f"USR-{uuid.uuid4().hex[:8]}"
        
        return {
            **context, 
            "user_created": True,
            "user_id": user_id,
            "account_status": "pending_verification"
        }
    
    def send_verification_email(context: Dict[str, Any]) -> Dict[str, Any]:
        user_id = context["user_id"]
        email = context["event_data"]["email"]
        
        # Simulate email sending
        verification_token = f"VTK-{uuid.uuid4().hex[:16]}"
        
        return {
            **context,
            "verification_email_sent": True,
            "verification_token": verification_token
        }
    
    return (ModuLink()
            .link(validate_user_data)
            .link(create_user_account)
            .link(send_verification_email))

def create_order_processing_chain() -> ModuLink:
    """Chain to process order events"""
    
    def validate_inventory(context: Dict[str, Any]) -> Dict[str, Any]:
        order_data = context["event_data"]
        items = order_data.get("items", [])
        
        # Simulate inventory check
        for item in items:
            if item.get("quantity", 0) <= 0:
                raise ValueError(f"Invalid quantity for item {item.get('product_id')}")
        
        return {**context, "inventory_validated": True}
    
    def calculate_pricing(context: Dict[str, Any]) -> Dict[str, Any]:
        order_data = context["event_data"]
        items = order_data.get("items", [])
        
        # Simulate pricing calculation
        total_amount = sum(item.get("price", 0) * item.get("quantity", 0) for item in items)
        tax_amount = total_amount * 0.08  # 8% tax
        final_amount = total_amount + tax_amount
        
        return {
            **context,
            "pricing_calculated": True,
            "subtotal": total_amount,
            "tax": tax_amount,
            "total": final_amount
        }
    
    def process_payment(context: Dict[str, Any]) -> Dict[str, Any]:
        total = context["total"]
        order_data = context["event_data"]
        
        # Simulate payment processing
        payment_id = f"PAY-{uuid.uuid4().hex[:8]}"
        
        return {
            **context,
            "payment_processed": True,
            "payment_id": payment_id,
            "payment_status": "completed"
        }
    
    return (ModuLink()
            .link(validate_inventory)
            .link(calculate_pricing)
            .link(process_payment))

# Usage Example
async def main():
    event_bus = EventBus()
    
    # Subscribe chains to events
    event_bus.subscribe("user_registration", create_user_registration_chain())
    event_bus.subscribe("order_created", create_order_processing_chain())
    
    # Publish events
    registration_event = Event(
        type="user_registration",
        payload={
            "email": "user@example.com",
            "username": "newuser",
            "password": "securepassword"
        },
        correlation_id="REG-001"
    )
    
    order_event = Event(
        type="order_created",
        payload={
            "user_id": "USR-12345",
            "items": [
                {"product_id": "PROD-001", "quantity": 2, "price": 29.99},
                {"product_id": "PROD-002", "quantity": 1, "price": 49.99}
            ]
        },
        priority=EventPriority.HIGH,
        correlation_id="ORD-001"
    )
    
    await event_bus.publish(registration_event)
    await event_bus.publish(order_event)
    
    # Wait for processing
    await asyncio.sleep(2)

# Run the example
# asyncio.run(main())
```

---

## Performance Optimization

### 1. Parallel Chain Execution with Resource Pools

```python
from modulink import ModuLink
from typing import Dict, Any, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
from dataclasses import dataclass
import time
import functools

@dataclass
class ResourcePool:
    thread_pool_size: int = 4
    process_pool_size: int = 2
    max_concurrent_chains: int = 10
    
class PerformanceOptimizedChain:
    def __init__(self, resource_pool: ResourcePool):
        self.resource_pool = resource_pool
        self.thread_executor = ThreadPoolExecutor(max_workers=resource_pool.thread_pool_size)
        self.process_executor = ProcessPoolExecutor(max_workers=resource_pool.process_pool_size)
        self.semaphore = asyncio.Semaphore(resource_pool.max_concurrent_chains)
        self.performance_metrics = {}
    
    def create_parallel_chain(self, functions: List[callable], execution_mode: str = "async") -> ModuLink:
        """Create a chain optimized for parallel execution"""
        
        if execution_mode == "thread":
            return self._create_thread_optimized_chain(functions)
        elif execution_mode == "process":
            return self._create_process_optimized_chain(functions)
        else:
            return self._create_async_optimized_chain(functions)
    
    def _create_async_optimized_chain(self, functions: List[callable]) -> ModuLink:
        """Optimize for async I/O bound operations"""
        
        async def parallel_executor(context: Dict[str, Any]) -> Dict[str, Any]:
            async with self.semaphore:
                start_time = time.time()
                
                # Execute functions in parallel where possible
                if len(functions) <= 3:  # Small chains - execute in parallel
                    tasks = []
                    for func in functions:
                        if asyncio.iscoroutinefunction(func):
                            tasks.append(func(context))
                        else:
                            # Wrap sync function in async
                            tasks.append(asyncio.get_event_loop().run_in_executor(
                                self.thread_executor, func, context
                            ))
                    
                    results = await asyncio.gather(*tasks)
                    
                    # Merge results
                    final_context = context.copy()
                    for i, result in enumerate(results):
                        final_context.update(result)
                        final_context[f"step_{i}_result"] = result
                
                else:  # Large chains - execute sequentially with async optimization
                    final_context = context.copy()
                    for i, func in enumerate(functions):
                        if asyncio.iscoroutinefunction(func):
                            result = await func(final_context)
                        else:
                            result = await asyncio.get_event_loop().run_in_executor(
                                self.thread_executor, func, final_context
                            )
                        final_context.update(result)
                        final_context[f"step_{i}_result"] = result
                
                # Record performance metrics
                execution_time = time.time() - start_time
                self._record_performance("async_chain", execution_time, len(functions))
                
                return final_context
        
        chain = ModuLink()
        chain.link(parallel_executor)
        return chain
    
    def _create_thread_optimized_chain(self, functions: List[callable]) -> ModuLink:
        """Optimize for CPU-bound operations using thread pool"""
        
        def thread_executor(context: Dict[str, Any]) -> Dict[str, Any]:
            start_time = time.time()
            
            # Use thread pool for CPU-bound tasks
            with ThreadPoolExecutor(max_workers=self.resource_pool.thread_pool_size) as executor:
                futures = []
                for func in functions:
                    future = executor.submit(func, context.copy())
                    futures.append(future)
                
                # Collect results
                final_context = context.copy()
                for i, future in enumerate(futures):
                    result = future.result()
                    final_context.update(result)
                    final_context[f"step_{i}_result"] = result
            
            execution_time = time.time() - start_time
            self._record_performance("thread_chain", execution_time, len(functions))
            
            return final_context
        
        chain = ModuLink()
        chain.link(thread_executor)
        return chain
    
    def _create_process_optimized_chain(self, functions: List[callable]) -> ModuLink:
        """Optimize for heavy CPU-bound operations using process pool"""
        
        def process_executor(context: Dict[str, Any]) -> Dict[str, Any]:
            start_time = time.time()
            
            # Use process pool for heavy CPU work
            with ProcessPoolExecutor(max_workers=self.resource_pool.process_pool_size) as executor:
                futures = []
                for func in functions:
                    # Note: functions must be pickleable for process pool
                    future = executor.submit(func, context.copy())
                    futures.append(future)
                
                # Collect results
                final_context = context.copy()
                for i, future in enumerate(futures):
                    result = future.result()
                    final_context.update(result)
                    final_context[f"step_{i}_result"] = result
            
            execution_time = time.time() - start_time
            self._record_performance("process_chain", execution_time, len(functions))
            
            return final_context
        
        chain = ModuLink()
        chain.link(process_executor)
        return chain
    
    def _record_performance(self, chain_type: str, execution_time: float, function_count: int):
        """Record performance metrics"""
        if chain_type not in self.performance_metrics:
            self.performance_metrics[chain_type] = {
                'total_executions': 0,
                'total_time': 0,
                'average_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'average_functions_per_chain': 0
            }
        
        metrics = self.performance_metrics[chain_type]
        metrics['total_executions'] += 1
        metrics['total_time'] += execution_time
        metrics['average_time'] = metrics['total_time'] / metrics['total_executions']
        metrics['min_time'] = min(metrics['min_time'], execution_time)
        metrics['max_time'] = max(metrics['max_time'], execution_time)
        metrics['average_functions_per_chain'] = (
            (metrics['average_functions_per_chain'] * (metrics['total_executions'] - 1) + function_count) 
            / metrics['total_executions']
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            'metrics': self.performance_metrics,
            'resource_utilization': {
                'thread_pool_size': self.resource_pool.thread_pool_size,
                'process_pool_size': self.resource_pool.process_pool_size,
                'max_concurrent_chains': self.resource_pool.max_concurrent_chains
            },
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        for chain_type, metrics in self.performance_metrics.items():
            avg_time = metrics['average_time']
            if avg_time > 5.0:  # More than 5 seconds
                recommendations.append(
                    f"{chain_type}: Consider breaking down chains or optimizing functions (avg: {avg_time:.2f}s)"
                )
            
            if metrics['max_time'] > metrics['average_time'] * 3:
                recommendations.append(
                    f"{chain_type}: High variability in execution times, investigate outliers"
                )
        
        return recommendations

# Example CPU-bound functions for testing
def cpu_intensive_task_1(context: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate CPU-intensive work"""
    result = sum(i * i for i in range(100000))
    return {**context, "cpu_task_1_result": result}

def cpu_intensive_task_2(context: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate another CPU-intensive task"""
    result = sum(i ** 3 for i in range(50000))
    return {**context, "cpu_task_2_result": result}

async def io_bound_task_1(context: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate I/O bound task"""
    await asyncio.sleep(0.1)  # Simulate network call
    return {**context, "io_task_1_result": "completed"}

async def io_bound_task_2(context: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate another I/O bound task"""
    await asyncio.sleep(0.15)  # Simulate database query
    return {**context, "io_task_2_result": "completed"}

# Usage Example
async def performance_test():
    resource_pool = ResourcePool(
        thread_pool_size=4,
        process_pool_size=2,
        max_concurrent_chains=10
    )
    
    optimizer = PerformanceOptimizedChain(resource_pool)
    
    # Test different execution modes
    
    # 1. Async optimized for I/O bound
    async_chain = optimizer.create_parallel_chain(
        [io_bound_task_1, io_bound_task_2],
        execution_mode="async"
    )
    
    # 2. Thread optimized for CPU bound
    thread_chain = optimizer.create_parallel_chain(
        [cpu_intensive_task_1, cpu_intensive_task_2],
        execution_mode="thread"
    )
    
    # Execute chains
    start_time = time.time()
    
    async_result = await async_chain.execute({"test": "async"})
    print(f"Async chain completed in: {time.time() - start_time:.2f}s")
    
    start_time = time.time()
    thread_result = await thread_chain.execute({"test": "thread"})
    print(f"Thread chain completed in: {time.time() - start_time:.2f}s")
    
    # Get performance report
    report = optimizer.get_performance_report()
    print("\nPerformance Report:")
    for chain_type, metrics in report['metrics'].items():
        print(f"{chain_type}: avg={metrics['average_time']:.3f}s, "
              f"min={metrics['min_time']:.3f}s, max={metrics['max_time']:.3f}s")
    
    if report['recommendations']:
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"- {rec}")

# Run performance test
# asyncio.run(performance_test())
```

### 2. Memory-Efficient Chain Processing

```python
from modulink import ModuLink
from typing import Dict, Any, Generator, Iterator, Optional
import gc
import sys
from contextlib import contextmanager
import weakref
from dataclasses import dataclass
import psutil
import os

@dataclass
class MemoryConfig:
    max_memory_mb: int = 512
    gc_threshold: int = 700  # Number of objects before triggering GC
    enable_memory_monitoring: bool = True
    context_cleanup_interval: int = 10  # Clean up every N executions

class MemoryEfficientChain:
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.execution_count = 0
        self.memory_usage_history = []
        self.context_cache = weakref.WeakValueDictionary()
    
    @contextmanager
    def memory_monitor(self):
        """Context manager for monitoring memory usage"""
        if self.config.enable_memory_monitoring:
            process = psutil.Process(os.getpid())
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            yield
            
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = end_memory - start_memory
            
            self.memory_usage_history.append({
                'start_mb': start_memory,
                'end_mb': end_memory,
                'delta_mb': memory_delta
            })
            
            # Check memory limits
            if end_memory > self.config.max_memory_mb:
                self._trigger_memory_cleanup()
        else:
            yield
    
    def create_streaming_chain(self, functions: list) -> ModuLink:
        """Create a memory-efficient streaming chain for large datasets"""
        
        def streaming_processor(context: Dict[str, Any]) -> Dict[str, Any]:
            with self.memory_monitor():
                data_stream = context.get('data_stream', [])
                
                if not hasattr(data_stream, '__iter__'):
                    raise ValueError("data_stream must be iterable")
                
                # Process data in chunks to minimize memory usage
                def process_chunk(chunk_data):
                    chunk_context = {**context, 'current_chunk': chunk_data}
                    
                    # Apply all functions to the chunk
                    for func in functions:
                        chunk_context = func(chunk_context)
                    
                    return chunk_context['current_chunk']
                
                # Stream processing with generator
                def result_generator():
                    chunk_size = context.get('chunk_size', 100)
                    chunk = []
                    
                    for item in data_stream:
                        chunk.append(item)
                        
                        if len(chunk) >= chunk_size:
                            yield from process_chunk(chunk)
                            chunk = []
                            
                            # Trigger garbage collection periodically
                            if len(gc.get_objects()) > self.config.gc_threshold:
                                gc.collect()
                    
                    # Process remaining items
                    if chunk:
                        yield from process_chunk(chunk)
                
                # Return context with generator
                return {
                    **context,
                    'processed_stream': result_generator(),
                    'is_streaming': True
                }
        
        chain = ModuLink()
        chain.link(streaming_processor)
        return chain
    
    def create_batch_processing_chain(self, functions: list, batch_size: int = 50) -> ModuLink:
        """Create a chain that processes data in memory-efficient batches"""
        
        def batch_processor(context: Dict[str, Any]) -> Dict[str, Any]:
            with self.memory_monitor():
                data = context.get('data', [])
                
                if not isinstance(data, (list, tuple)):
                    raise ValueError("Data must be a list or tuple for batch processing")
                
                results = []
                
                # Process in batches
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]
                    batch_context = {**context, 'current_batch': batch}
                    
                    # Apply functions to batch
                    for func in functions:
                        batch_context = func(batch_context)
                    
                    # Extract batch results
                    batch_results = batch_context.get('current_batch', batch)
                    results.extend(batch_results)
                    
                    # Clean up batch context
                    del batch_context
                    
                    # Periodic garbage collection
                    if (i // batch_size) % 5 == 0:
                        gc.collect()
                
                self.execution_count += 1
                
                # Periodic context cleanup
                if self.execution_count % self.config.context_cleanup_interval == 0:
                    self._cleanup_context_cache()
                
                return {**context, 'processed_data': results}
        
        chain = ModuLink()
        chain.link(batch_processor)
        return chain
    
    def create_memory_optimized_chain(self, functions: list) -> ModuLink:
        """Create a chain optimized for minimal memory footprint"""
        
        def memory_optimized_processor(context: Dict[str, Any]) -> Dict[str, Any]:
            with self.memory_monitor():
                # Use generators and lazy evaluation where possible
                current_context = context.copy()
                
                for i, func in enumerate(functions):
                    # Only keep essential data in context
                    essential_keys = context.get('essential_keys', [])
                    if essential_keys:
                        filtered_context = {k: v for k, v in current_context.items() 
                                          if k in essential_keys or k.startswith('_')}
                        filtered_context.update({k: v for k, v in current_context.items() 
                                               if k in ['data', 'result', 'output']})
                    else:
                        filtered_context = current_context
                    
                    # Execute function
                    result = func(filtered_context)
                    
                    # Update context efficiently
                    current_context.clear()
                    current_context.update(result)
                    
                    # Force garbage collection for large chains
                    if i > 0 and i % 3 == 0:
                        gc.collect()
                
                return current_context
        
        chain = ModuLink()
        chain.link(memory_optimized_processor)
        return chain
    
    def _trigger_memory_cleanup(self):
        """Trigger aggressive memory cleanup"""
        # Clear context cache
        self.context_cache.clear()
        
        # Trigger garbage collection multiple times
        for _ in range(3):
            gc.collect()
        
        print(f"Warning: Memory usage exceeded {self.config.max_memory_mb}MB, triggered cleanup")
    
    def _cleanup_context_cache(self):
        """Clean up context cache"""
        # Context cache uses weak references, so this just ensures cleanup
        self.context_cache.clear()
        gc.collect()
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Get memory usage report"""
        if not self.memory_usage_history:
            return {"message": "No memory monitoring data available"}
        
        total_executions = len(self.memory_usage_history)
        avg_memory = sum(entry['end_mb'] for entry in self.memory_usage_history) / total_executions
        max_memory = max(entry['end_mb'] for entry in self.memory_usage_history)
        min_memory = min(entry['end_mb'] for entry in self.memory_usage_history)
        
        return {
            'total_executions': total_executions,
            'average_memory_mb': round(avg_memory, 2),
            'peak_memory_mb': round(max_memory, 2),
            'min_memory_mb': round(min_memory, 2),
            'memory_efficiency': 'Good' if max_memory < self.config.max_memory_mb else 'Needs Optimization',
            'recent_usage': self.memory_usage_history[-5:]  # Last 5 executions
        }

# Example functions for memory testing
def memory_intensive_function(context: Dict[str, Any]) -> Dict[str, Any]:
    """Function that processes large amounts of data"""
    current_batch = context.get('current_batch', context.get('data', []))
    
    # Simulate processing that creates temporary objects
    processed_items = []
    for item in current_batch:
        # Simulate some processing
        processed_item = {
            'original': item,
            'processed': item * 2 if isinstance(item, (int, float)) else f"processed_{item}",
            'metadata': {'processed_at': 'now', 'version': '1.0'}
        }
        processed_items.append(processed_item)
    
    return {**context, 'current_batch': processed_items}

def data_aggregation_function(context: Dict[str, Any]) -> Dict[str, Any]:
    """Function that aggregates data"""
    current_batch = context.get('current_batch', [])
    
    # Aggregate data
    if current_batch and isinstance(current_batch[0], dict):
        aggregated = {
            'count': len(current_batch),
            'processed_count': sum(1 for item in current_batch if 'processed' in item),
            'sample_data': current_batch[:3]  # Keep only sample for memory efficiency
        }
    else:
        aggregated = {'count': len(current_batch), 'data_type': type(current_batch[0]).__name__ if current_batch else 'empty'}
    
    return {**context, 'current_batch': current_batch, 'aggregation': aggregated}

# Usage Example
def memory_efficiency_demo():
    config = MemoryConfig(
        max_memory_mb=256,
        gc_threshold=500,
        enable_memory_monitoring=True
    )
    
    memory_chain = MemoryEfficientChain(config)
    
    # Create test data
    large_dataset = list(range(10000))  # Large dataset
    
    # 1. Batch processing chain
    batch_chain = memory_chain.create_batch_processing_chain(
        [memory_intensive_function, data_aggregation_function],
        batch_size=100
    )
    
    print("Testing batch processing...")
    result = batch_chain.execute({
        'data': large_dataset,
        'essential_keys': ['aggregation', 'processed_data']
    })
    
    print(f"Processed {len(result['processed_data'])} items")
    
    # 2. Streaming chain
    streaming_chain = memory_chain.create_streaming_chain(
        [memory_intensive_function, data_aggregation_function]
    )
    
    print("\nTesting streaming processing...")
    stream_result = streaming_chain.execute({
        'data_stream': iter(large_dataset),
        'chunk_size': 50
    })
    
    # Consume some of the stream
    processed_items = list(stream_result['processed_stream'])[:10]
    print(f"Streamed and processed first 10 items: {len(processed_items)}")
    
    # Get memory report
    report = memory_chain.get_memory_report()
    print(f"\nMemory Report:")
    print(f"Total executions: {report['total_executions']}")
    print(f"Average memory: {report['average_memory_mb']} MB")
    print(f"Peak memory: {report['peak_memory_mb']} MB")
    print(f"Efficiency: {report['memory_efficiency']}")

# Run demo
# memory_efficiency_demo()
```

---

## Scalability Patterns

### 1. Horizontal Scaling with Load Distribution

```python
from modulink import ModuLink
from typing import Dict, Any, List, Optional
import asyncio
import hashlib
import random
from dataclasses import dataclass
from enum import Enum
import time
import json

class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    HASH_BASED = "hash_based"
    RANDOM = "random"

@dataclass
class ChainNode:
    id: str
    chain: ModuLink
    weight: int = 1
    current_connections: int = 0
    max_connections: int = 100
    health_status: str = "healthy"
    avg_response_time: float = 0.0
    total_requests: int = 0

class HorizontalScalingManager:
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.nodes: List[ChainNode] = []
        self.current_node_index = 0
        self.request_metrics = {}
        self.auto_scaling_enabled = False
        self.scaling_thresholds = {
            'cpu_threshold': 80,
            'memory_threshold': 85,
            'response_time_threshold': 5.0,
            'queue_length_threshold': 100
        }
    
    def add_node(self, node: ChainNode):
        """Add a new chain node to the pool"""
        self.nodes.append(node)
        print(f"Added node {node.id} to the pool")
    
    def remove_node(self, node_id: str):
        """Remove a node from the pool"""
        self.nodes = [node for node in self.nodes if node.id != node_id]
        print(f"Removed node {node_id} from the pool")
    
    async def execute_distributed(self, context: Dict[str, Any], node_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a request using load balancing"""
        
        if node_id:
            # Execute on specific node
            node = next((n for n in self.nodes if n.id == node_id), None)
            if not node:
                raise ValueError(f"Node {node_id} not found")
            return await self._execute_on_node(node, context)
        
        # Select node based on strategy
        node = self._select_node(context)
        if not node:
            raise RuntimeError("No healthy nodes available")
        
        return await self._execute_on_node(node, context)
    
    def _select_node(self, context: Dict[str, Any]) -> Optional[ChainNode]:
        """Select a node based on the load balancing strategy"""
        healthy_nodes = [node for node in self.nodes if node.health_status == "healthy"]
        
        if not healthy_nodes:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            node = healthy_nodes[self.current_node_index % len(healthy_nodes)]
            self.current_node_index += 1
            return node
        
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            # Select based on weights
            total_weight = sum(node.weight for node in healthy_nodes)
            if total_weight == 0:
                return random.choice(healthy_nodes)
            
            # Weighted selection
            weights = [node.weight for node in healthy_nodes]
            return random.choices(healthy_nodes, weights=weights)[0]
        
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(healthy_nodes, key=lambda n: n.current_connections)
        
        elif self.strategy == LoadBalancingStrategy.HASH_BASED:
            # Hash based on request content or user ID
            hash_key = context.get('user_id', context.get('session_id', str(hash(str(context)))))
            hash_value = int(hashlib.md5(str(hash_key).encode()).hexdigest(), 16)
            node_index = hash_value % len(healthy_nodes)
            return healthy_nodes[node_index]
        
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(healthy_nodes)
        
        return healthy_nodes[0]  # Fallback
    
    async def _execute_on_node(self, node: ChainNode, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request on a specific node"""
        if node.current_connections >= node.max_connections:
            raise RuntimeError(f"Node {node.id} is at capacity")
        
        node.current_connections += 1
        start_time = time.time()
        
        try:
            # Add node information to context
            execution_context = {
                **context,
                '_node_id': node.id,
                '_execution_start': start_time
            }
            
            result = await node.chain.execute(execution_context)
            
            # Record success metrics
            execution_time = time.time() - start_time
            self._record_metrics(node, execution_time, success=True)
            
            return {
                **result,
                '_node_id': node.id,
                '_execution_time': execution_time
            }
        
        except Exception as e:
            # Record failure metrics
            execution_time = time.time() - start_time
            self._record_metrics(node, execution_time, success=False)
            raise e
        
        finally:
            node.current_connections -= 1
    
    def _record_metrics(self, node: ChainNode, execution_time: float, success: bool):
        """Record execution metrics"""
        node.total_requests += 1
        
        # Update average response time
        if node.total_requests == 1:
            node.avg_response_time = execution_time
        else:
            node.avg_response_time = (
                (node.avg_response_time * (node.total_requests - 1) + execution_time) 
                / node.total_requests
            )
        
        # Record in metrics
        if node.id not in self.request_metrics:
            self.request_metrics[node.id] = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0,
                'last_request_time': time.time()
            }
        
        metrics = self.request_metrics[node.id]
        metrics['total_requests'] += 1
        metrics['last_request_time'] = time.time()
        
        if success:
            metrics['successful_requests'] += 1
        else:
            metrics['failed_requests'] += 1
        
        metrics['avg_response_time'] = node.avg_response_time
        
        # Check if auto-scaling is needed
        if self.auto_scaling_enabled:
            self._check_scaling_conditions()
    
    def _check_scaling_conditions(self):
        """Check if scaling up or down is needed"""
        # Calculate overall metrics
        total_requests = sum(node.total_requests for node in self.nodes)
        if total_requests == 0:
            return
        
        avg_response_time = sum(node.avg_response_time * node.total_requests for node in self.nodes) / total_requests
        max_connections_ratio = max(node.current_connections / node.max_connections for node in self.nodes)
        
        # Scale up conditions
        if (avg_response_time > self.scaling_thresholds['response_time_threshold'] or
            max_connections_ratio > 0.8):  # 80% capacity
            self._trigger_scale_up()
        
        # Scale down conditions
        elif (avg_response_time < self.scaling_thresholds['response_time_threshold'] * 0.5 and
              max_connections_ratio < 0.3 and len(self.nodes) > 1):  # 30% capacity
            self._trigger_scale_down()
    
    def _trigger_scale_up(self):
        """Trigger scaling up (add more nodes)"""
        print("Scaling conditions met: Adding new node")
        # In a real implementation, this would create new instances
        # For demo, we'll create a clone of an existing node
        if self.nodes:
            template_node = self.nodes[0]
            new_node = ChainNode(
                id=f"node_{len(self.nodes) + 1}",
                chain=template_node.chain,  # In reality, this would be a new instance
                weight=template_node.weight,
                max_connections=template_node.max_connections
            )
            self.add_node(new_node)
    
    def _trigger_scale_down(self):
        """Trigger scaling down (remove nodes)"""
        if len(self.nodes) > 1:
            # Remove the node with least load
            least_loaded_node = min(self.nodes, key=lambda n: n.current_connections)
            print(f"Scaling down: Removing node {least_loaded_node.id}")
            self.remove_node(least_loaded_node.id)
    
    def enable_auto_scaling(self, **thresholds):
        """Enable auto-scaling with custom thresholds"""
        self.auto_scaling_enabled = True
        self.scaling_thresholds.update(thresholds)
        print("Auto-scaling enabled")
    
    def disable_auto_scaling(self):
        """Disable auto-scaling"""
        self.auto_scaling_enabled = False
        print("Auto-scaling disabled")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all nodes"""
        health_results = {}
        
        for node in self.nodes:
            try:
                # Simple health check - execute a minimal request
                start_time = time.time()
                await node.chain.execute({'_health_check': True})
                response_time = time.time() - start_time
                
                # Update health status based on response time
                if response_time > 10.0:  # 10 seconds timeout
                    node.health_status = "unhealthy"
                else:
                    node.health_status = "healthy"
                
                health_results[node.id] = {
                    'status': node.health_status,
                    'response_time': response_time,
                    'current_connections': node.current_connections,
                    'total_requests': node.total_requests
                }
            
            except Exception as e:
                node.health_status = "unhealthy"
                health_results[node.id] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'current_connections': node.current_connections
                }
        
        return health_results
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get comprehensive cluster status"""
        healthy_nodes = [n for n in self.nodes if n.health_status == "healthy"]
        
        return {
            'total_nodes': len(self.nodes),
            'healthy_nodes': len(healthy_nodes),
            'unhealthy_nodes': len(self.nodes) - len(healthy_nodes),
            'load_balancing_strategy': self.strategy.value,
            'auto_scaling_enabled': self.auto_scaling_enabled,
            'total_connections': sum(n.current_connections for n in self.nodes),
            'total_capacity': sum(n.max_connections for n in self.nodes),
            'capacity_utilization': (
                sum(n.current_connections for n in self.nodes) / 
                sum(n.max_connections for n in self.nodes) * 100
                if self.nodes else 0
            ),
            'node_metrics': self.request_metrics
        }

# Example usage
def create_sample_processing_chain() -> ModuLink:
    """Create a sample processing chain"""
    
    def process_request(context: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate processing time
        import time
        import random
        
        # Variable processing time to simulate different loads
        processing_time = random.uniform(0.1, 0.5)
        time.sleep(processing_time)
        
        return {
            **context,
            'processed': True,
            'processing_time': processing_time,
            'timestamp': time.time()
        }
    
    def add_metadata(context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            **context,
            'metadata': {
                'version': '1.0',
                'environment': 'production',
                'node_id': context.get('_node_id', 'unknown')
            }
        }
    
    return ModuLink().link(process_request).link(add_metadata)

async def scaling_demo():
    """Demonstrate horizontal scaling"""
    
    # Create scaling manager
    manager = HorizontalScalingManager(LoadBalancingStrategy.LEAST_CONNECTIONS)
    
    # Add initial nodes
    for i in range(3):
        node = ChainNode(
            id=f"node_{i+1}",
            chain=create_sample_processing_chain(),
            weight=1,
            max_connections=10
        )
        manager.add_node(node)
    
    # Enable auto-scaling
    manager.enable_auto_scaling(
        response_time_threshold=1.0,
        cpu_threshold=70
    )
    
    print("Initial cluster status:")
    status = manager.get_cluster_status()
    print(f"Nodes: {status['total_nodes']}, Capacity: {status['total_capacity']}")
    
    # Simulate load
    print("\nSimulating high load...")
    tasks = []
    
    for i in range(50):  # 50 concurrent requests
        context = {
            'request_id': f"req_{i}",
            'user_id': f"user_{i % 10}",  # 10 different users
            'data': f"payload_{i}"
        }
        
        task = manager.execute_distributed(context)
        tasks.append(task)
    
    # Execute all requests
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful_requests = sum(1 for r in results if not isinstance(r, Exception))
    print(f"Completed {successful_requests}/{len(tasks)} requests successfully")
    
    # Check final status
    print("\nFinal cluster status:")
    final_status = manager.get_cluster_status()
    print(f"Nodes: {final_status['total_nodes']}, Healthy: {final_status['healthy_nodes']}")
    print(f"Capacity utilization: {final_status['capacity_utilization']:.1f}%")
    
    # Health check
    health = await manager.health_check()
    print("\nNode health status:")
    for node_id, health_info in health.items():
        print(f"{node_id}: {health_info['status']} "
              f"(response_time: {health_info.get('response_time', 'N/A'):.3f}s)")

# Run the demo
# asyncio.run(scaling_demo())
```

This advanced patterns cookbook provides enterprise-grade patterns for:

1. **Enterprise Architecture Patterns** - Microservice orchestration and event-driven architectures
2. **Performance Optimization** - Parallel execution, resource pools, and memory-efficient processing
3. **Scalability Patterns** - Horizontal scaling with load balancing and auto-scaling

Each pattern includes:
- Complete, production-ready code examples
- Real-world use cases and scenarios
- Performance monitoring and metrics
- Error handling and resilience patterns
- Best practices and recommendations

The cookbook is designed for teams building large-scale, mission-critical applications that require high performance, scalability, and reliability.

---

## Production Deployment Strategies

### 1. Containerized Deployment with Docker and Kubernetes

Containerization provides consistent environments and simplifies deployment across different infrastructure platforms.

#### Production Dockerfile
```dockerfile
# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r modulink && useradd -r -g modulink modulink

# Copy installed packages from builder
COPY --from=builder /root/.local /home/modulink/.local

# Set up application
WORKDIR /app
COPY --chown=modulink:modulink . .

# Switch to non-root user
USER modulink

# Add local bin to PATH
ENV PATH=/home/modulink/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

EXPOSE 8080
CMD ["python", "-m", "modulink_app"]
```

#### Kubernetes Production Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: modulink-app
  namespace: production
  labels:
    app: modulink
    version: v1.2.0
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: modulink
  template:
    metadata:
      labels:
        app: modulink
        version: v1.2.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: modulink-service-account
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
      containers:
      - name: modulink
        image: your-registry/modulink:v1.2.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: modulink-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: modulink-secrets
              key: redis-url
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: modulink-config
      tolerations:
      - key: "high-memory"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
---
apiVersion: v1
kind: Service
metadata:
  name: modulink-service
  namespace: production
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: modulink
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: modulink-ingress
  namespace: production
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.modulink.com
    secretName: modulink-tls
  rules:
  - host: api.modulink.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: modulink-service
            port:
              number: 80
```

### 2. Blue-Green Deployment Strategy

Blue-green deployment provides zero-downtime updates by maintaining two identical production environments.

```python
from modulink import ModuLink
from typing import Dict, Any
import asyncio
import aiohttp
from datetime import datetime, timedelta

class BlueGreenDeploymentManager:
    def __init__(self, blue_endpoint: str, green_endpoint: str, health_check_path: str = "/health"):
        self.blue_endpoint = blue_endpoint
        self.green_endpoint = green_endpoint
        self.health_check_path = health_check_path
        self.active_environment = "blue"  # Start with blue as active
        self.deployment_history = []
    
    async def health_check(self, endpoint: str) -> bool:
        """Check if an environment is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}{self.health_check_path}", timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def validate_deployment(self, environment: str) -> Dict[str, Any]:
        """Validate a deployment with comprehensive checks"""
        endpoint = self.green_endpoint if environment == "green" else self.blue_endpoint
        
        validation_results = {
            "environment": environment,
            "endpoint": endpoint,
            "timestamp": datetime.now(),
            "checks": {}
        }
        
        # Health check
        validation_results["checks"]["health"] = await self.health_check(endpoint)
        
        # Performance check
        start_time = datetime.now()
        performance_ok = await self.health_check(endpoint)
        response_time = (datetime.now() - start_time).total_seconds()
        validation_results["checks"]["performance"] = {
            "response_time": response_time,
            "acceptable": response_time < 2.0
        }
        
        # Load test
        validation_results["checks"]["load_test"] = await self._run_load_test(endpoint)
        
        return validation_results
    
    async def _run_load_test(self, endpoint: str, concurrent_requests: int = 10) -> Dict[str, Any]:
        """Run a basic load test"""
        async def make_request():
            try:
                async with aiohttp.ClientSession() as session:
                    start = datetime.now()
                    async with session.get(f"{endpoint}/health", timeout=30) as response:
                        duration = (datetime.now() - start).total_seconds()
                        return {"success": response.status == 200, "duration": duration}
            except Exception:
                return {"success": False, "duration": 30.0}
        
        # Run concurrent requests
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        successful_requests = sum(1 for r in results if r["success"])
        avg_response_time = sum(r["duration"] for r in results) / len(results)
        
        return {
            "total_requests": len(results),
            "successful_requests": successful_requests,
            "success_rate": successful_requests / len(results),
            "avg_response_time": avg_response_time,
            "acceptable": successful_requests / len(results) > 0.95 and avg_response_time < 5.0
        }
    
    async def deploy_to_staging(self, environment: str) -> Dict[str, Any]:
        """Deploy new version to staging environment (inactive)"""
        staging_env = "green" if self.active_environment == "blue" else "blue"
        
        if environment != staging_env:
            raise ValueError(f"Can only deploy to staging environment ({staging_env})")
        
        print(f"Deploying to {staging_env} environment...")
        
        # In a real implementation, this would trigger the actual deployment
        # For demo purposes, we'll simulate deployment time
        await asyncio.sleep(2)
        
        deployment_record = {
            "environment": staging_env,
            "deployment_time": datetime.now(),
            "status": "deployed"
        }
        
        self.deployment_history.append(deployment_record)
        
        return deployment_record
    
    async def switch_traffic(self) -> Dict[str, Any]:
        """Switch traffic from active to staging environment"""
        old_active = self.active_environment
        new_active = "green" if old_active == "blue" else "blue"
        
        # Validate staging environment before switching
        validation = await self.validate_deployment(new_active)
        
        all_checks_passed = all(
            check.get("acceptable", check) if isinstance(check, dict) else check
            for check in validation["checks"].values()
        )
        
        if not all_checks_passed:
            raise RuntimeError(f"Validation failed for {new_active} environment: {validation}")
        
        # Switch traffic
        print(f"Switching traffic from {old_active} to {new_active}")
        self.active_environment = new_active
        
        switch_record = {
            "old_environment": old_active,
            "new_environment": new_active,
            "switch_time": datetime.now(),
            "validation_results": validation
        }
        
        self.deployment_history.append(switch_record)
        
        return switch_record
    
    async def rollback(self) -> Dict[str, Any]:
        """Rollback to previous environment"""
        old_active = self.active_environment
        rollback_env = "blue" if old_active == "green" else "green"
        
        print(f"Rolling back from {old_active} to {rollback_env}")
        
        # Validate rollback environment
        validation = await self.validate_deployment(rollback_env)
        
        if not validation["checks"]["health"]:
            raise RuntimeError(f"Cannot rollback to unhealthy {rollback_env} environment")
        
        self.active_environment = rollback_env
        
        rollback_record = {
            "type": "rollback",
            "from_environment": old_active,
            "to_environment": rollback_env,
            "rollback_time": datetime.now(),
            "reason": "Manual rollback triggered"
        }
        
        self.deployment_history.append(rollback_record)
        
        return rollback_record
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        return {
            "active_environment": self.active_environment,
            "blue_endpoint": self.blue_endpoint,
            "green_endpoint": self.green_endpoint,
            "deployment_history_count": len(self.deployment_history),
            "last_deployment": self.deployment_history[-1] if self.deployment_history else None
        }
```

### 3. Canary Deployment with Gradual Traffic Shifting

```python
from modulink import ModuLink
from typing import Dict, Any
import asyncio
import random
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass
class CanaryConfig:
    initial_traffic_percent: int = 5
    traffic_increment: int = 10
    evaluation_duration_minutes: int = 5
    max_error_rate: float = 0.01  # 1%
    max_latency_ms: int = 2000
    rollback_on_failure: bool = True

class CanaryDeploymentManager:
    def __init__(self, config: CanaryConfig):
        self.config = config
        self.canary_traffic_percent = 0
        self.production_endpoint = "http://prod.modulink.internal:8080"
        self.canary_endpoint = "http://canary.modulink.internal:8080"
        self.metrics_history = []
        self.deployment_active = False
    
    async def start_canary_deployment(self) -> Dict[str, Any]:
        """Start canary deployment with initial traffic percentage"""
        if self.deployment_active:
            raise RuntimeError("Canary deployment already active")
        
        self.deployment_active = True
        self.canary_traffic_percent = self.config.initial_traffic_percent
        
        print(f"🚀 Starting canary deployment with {self.canary_traffic_percent}% traffic")
        
        return {
            "status": "started",
            "initial_traffic_percent": self.canary_traffic_percent,
            "start_time": datetime.now()
        }
    
    async def evaluate_canary_metrics(self) -> Dict[str, Any]:
        """Evaluate canary deployment metrics"""
        if not self.deployment_active:
            raise RuntimeError("No active canary deployment")
        
        # Simulate metrics collection
        await asyncio.sleep(1)  # Simulate metrics gathering delay
        
        # In production, these would come from monitoring systems
        production_metrics = await self._collect_metrics(self.production_endpoint)
        canary_metrics = await self._collect_metrics(self.canary_endpoint)
        
        evaluation_result = {
            "timestamp": datetime.now(),
            "canary_traffic_percent": self.canary_traffic_percent,
            "production_metrics": production_metrics,
            "canary_metrics": canary_metrics,
            "evaluation": self._evaluate_performance(production_metrics, canary_metrics)
        }
        
        self.metrics_history.append(evaluation_result)
        
        return evaluation_result
    
    async def _collect_metrics(self, endpoint: str) -> Dict[str, Any]:
        """Collect metrics for an endpoint"""
        # Simulate realistic metrics
        base_error_rate = 0.005  # 0.5% base error rate
        base_latency = 150  # 150ms base latency
        
        # Add some randomness
        error_rate = base_error_rate + random.uniform(-0.002, 0.008)
        latency = base_latency + random.uniform(-50, 200)
        
        # Canary might have slightly different performance
        if "canary" in endpoint:
            error_rate += random.uniform(-0.001, 0.005)  # Slightly more variable
            latency += random.uniform(-20, 100)  # Potentially faster or slower
        
        return {
            "endpoint": endpoint,
            "error_rate": max(0, error_rate),
            "avg_latency_ms": max(50, latency),
            "request_count": random.randint(500, 1500),
            "cpu_usage": random.uniform(20, 80),
            "memory_usage": random.uniform(30, 70)
        }
    
    def _evaluate_performance(self, production_metrics: Dict[str, Any], canary_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate canary performance against production"""
        
        # Error rate comparison
        error_rate_ok = (
            canary_metrics["error_rate"] <= self.config.max_error_rate and
            canary_metrics["error_rate"] <= production_metrics["error_rate"] * 1.5  # Allow 50% increase
        )
        
        # Latency comparison
        latency_ok = (
            canary_metrics["avg_latency_ms"] <= self.config.max_latency_ms and
            canary_metrics["avg_latency_ms"] <= production_metrics["avg_latency_ms"] * 1.3  # Allow 30% increase
        )
        
        # Resource usage check
        resource_ok = (
            canary_metrics["cpu_usage"] <= 90 and
            canary_metrics["memory_usage"] <= 90
        )
        
        # Overall evaluation
        overall_healthy = error_rate_ok and latency_ok and resource_ok
        
        return {
            "error_rate_ok": error_rate_ok,
            "latency_ok": latency_ok,
            "resource_usage_ok": resource_ok,
            "overall_healthy": overall_healthy,
            "recommendation": "promote" if overall_healthy else "rollback"
        }
    
    async def promote_canary(self) -> Dict[str, Any]:
        """Increase canary traffic percentage"""
        if not self.deployment_active:
            raise RuntimeError("No active canary deployment")
        
        if self.canary_traffic_percent >= 100:
            # Complete the canary deployment
            return await self.complete_canary_deployment()
        
        # Increase traffic
        self.canary_traffic_percent = min(
            100,
            self.canary_traffic_percent + self.config.traffic_increment
        )
        
        print(f"📈 Promoting canary to {self.canary_traffic_percent}% traffic")
        
        return {
            "action": "promoted",
            "new_traffic_percent": self.canary_traffic_percent,
            "timestamp": datetime.now()
        }
    
    async def rollback_canary(self) -> Dict[str, Any]:
        """Rollback canary deployment"""
        if not self.deployment_active:
            raise RuntimeError("No active canary deployment")
        
        print("🔄 Rolling back canary deployment")
        
        self.deployment_active = False
        self.canary_traffic_percent = 0
        
        rollback_result = {
            "action": "rollback",
            "reason": "Manual rollback triggered",
            "timestamp": datetime.now(),
            "final_metrics": self.metrics_history[-1] if self.metrics_history else None
        }
        
        self.metrics_history.append(rollback_result)
        
        return rollback_result
    
    async def complete_canary_deployment(self) -> Dict[str, Any]:
        """Complete canary deployment (100% traffic to canary)"""
        print("🎉 Completing canary deployment - promoting to production")
        
        self.deployment_active = False
        self.canary_traffic_percent = 100
        
        completion_result = {
            "action": "completed",
            "total_duration": len(self.metrics_history) * self.config.evaluation_duration_minutes,
            "final_traffic_percent": 100,
            "timestamp": datetime.now(),
            "deployment_summary": self._generate_deployment_summary()
        }
        
        return completion_result
    
    def _generate_deployment_summary(self) -> Dict[str, Any]:
        """Generate summary of the canary deployment"""
        if not self.metrics_history:
            return {"message": "No metrics available"}
        
        avg_error_rate = sum(m["canary_metrics"]["error_rate"] for m in self.metrics_history) / len(self.metrics_history)
        avg_latency = sum(m["canary_metrics"]["avg_latency_ms"] for m in self.metrics_history) / len(self.metrics_history)
        total_evaluations = len(self.metrics_history)
        healthy_evaluations = sum(1 for m in self.metrics_history if m["evaluation"]["overall_healthy"])
        
        return {
            "total_evaluations": total_evaluations,
            "healthy_evaluations": healthy_evaluations,
            "health_rate": healthy_evaluations / total_evaluations if total_evaluations > 0 else 0,
            "avg_error_rate": avg_error_rate,
            "avg_latency_ms": avg_latency,
            "deployment_quality": "excellent" if healthy_evaluations / total_evaluations > 0.9 else "good" if healthy_evaluations / total_evaluations > 0.7 else "poor"
        }
    
    async def automated_canary_pipeline(self) -> Dict[str, Any]:
        """Run fully automated canary deployment pipeline"""
        try:
            # Start deployment
            start_result = await self.start_canary_deployment()
            print(f"✅ {start_result}")
            
            while self.deployment_active and self.canary_traffic_percent < 100:
                # Wait for evaluation period
                print(f"⏳ Evaluating for {self.config.evaluation_duration_minutes} minutes...")
                await asyncio.sleep(self.config.evaluation_duration_minutes * 60 // 10)  # Shortened for demo
                
                # Evaluate metrics
                evaluation = await self.evaluate_canary_metrics()
                print(f"📊 Evaluation: {evaluation['evaluation']['recommendation']}")
                
                if evaluation["evaluation"]["overall_healthy"]:
                    # Promote canary
                    promote_result = await self.promote_canary()
                    print(f"📈 {promote_result}")
                else:
                    # Rollback if configured
                    if self.config.rollback_on_failure:
                        rollback_result = await self.rollback_canary()
                        return rollback_result
                    else:
                        print("⚠️ Issues detected but rollback disabled")
            
            # If we reach 100%, complete deployment
            if self.canary_traffic_percent >= 100:
                completion_result = await self.complete_canary_deployment()
                return completion_result
            
        except Exception as e:
            print(f"❌ Canary deployment failed: {e}")
            if self.deployment_active:
                return await self.rollback_canary()
            raise

# Usage Example
async def canary_deployment_demo():
    """Demonstrate automated canary deployment"""
    
    config = CanaryConfig(
        initial_traffic_percent=10,
        traffic_increment=20,
        evaluation_duration_minutes=2,  # Shortened for demo
        max_error_rate=0.02,
        max_latency_ms=3000
    )
    
    manager = CanaryDeploymentManager(config)
    
    print("=== Automated Canary Deployment Demo ===")
    
    try:
        result = await manager.automated_canary_pipeline()
        print(f"🎯 Final result: {result['action']}")
        
        if result["action"] == "completed":
            summary = result["deployment_summary"]
            print(f"📋 Deployment Quality: {summary['deployment_quality']}")
            print(f"📋 Health Rate: {summary['health_rate']:.1%}")
            print(f"📋 Avg Latency: {summary['avg_latency_ms']:.0f}ms")
    
    except Exception as e:
        print(f"💥 Deployment pipeline failed: {e}")
`````

---

## Security Patterns

### 1. Authentication and Authorization Middleware

Secure your ModuLink chains with robust authentication and role-based access control.

```python
from modulink import ModuLink
from typing import Dict, Any, List
import jwt
import bcrypt
import time
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"
    SERVICE = "service"

class SecurityConfig:
    def __init__(self):
        self.jwt_secret = "your-super-secret-jwt-key"  # In production, use environment variable
        self.jwt_algorithm = "HS256"
        self.token_expiry_hours = 24
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30

class AuthenticationManager:
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.user_store = {}  # In production, use database
        self.failed_attempts = {}
        self.locked_accounts = {}
    
    def create_user(self, username: str, password: str, role: UserRole) -> Dict[str, Any]:
        """Create a new user with hashed password"""
        if username in self.user_store:
            raise ValueError(f"User {username} already exists")
        
        # Hash password with salt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
            "username": username,
            "password_hash": password_hash,
            "role": role.value,
            "created_at": datetime.now(),
            "last_login": None,
            "active": True
        }
        
        self.user_store[username] = user_data
        return {"username": username, "role": role.value, "created": True}
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return JWT token"""
        
        # Check if account is locked
        if self._is_account_locked(username):
            raise ValueError("Account is temporarily locked due to too many failed attempts")
        
        # Get user
        user = self.user_store.get(username)
        if not user or not user["active"]:
            self._record_failed_attempt(username)
            raise ValueError("Invalid credentials")
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
            self._record_failed_attempt(username)
            raise ValueError("Invalid credentials")
        
        # Reset failed attempts on successful login
        self.failed_attempts.pop(username, None)
        if username in self.locked_accounts:
            del self.locked_accounts[username]
        
        # Update last login
        user["last_login"] = datetime.now()
        
        # Generate JWT token
        token = self._generate_jwt_token(username, user["role"])
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.config.token_expiry_hours * 3600,
            "user": {
                "username": username,
                "role": user["role"]
            }
        }
    
    def _generate_jwt_token(self, username: str, role: str) -> str:
        """Generate JWT token"""
        payload = {
            "sub": username,
            "role": role,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.config.token_expiry_hours)
        }
        
        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
               """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def _record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        
        self.failed_attempts[username].append(datetime.now())
        
        # Clean old attempts (older than lockout duration)
        cutoff_time = datetime.now() - timedelta(minutes=self.config.lockout_duration_minutes)
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username] 
            if attempt > cutoff_time
        ]
        
        # Lock account if too many failed attempts
        if len(self.failed_attempts[username]) >= self.config.max_failed_attempts:
            self.locked_accounts[username] = datetime.now()
    
    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked"""
        if username not in self.locked_accounts:
            return False
        
        lock_time = self.locked_accounts[username]
        unlock_time = lock_time + timedelta(minutes=self.config.lockout_duration_minutes)
        
        if datetime.now() > unlock_time:
            # Unlock account
            del self.locked_accounts[username]
            return False
        
        return True

def create_auth_middleware(auth_manager: AuthenticationManager, required_roles: List[UserRole] = None):
    """Create authentication middleware for ModuLink chains"""
    
    def auth_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
        # Extract token from Authorization header
        auth_header = context.get("headers", {}).get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            raise ValueError("Missing or invalid Authorization header")
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Verify token
            payload = auth_manager.verify_jwt_token(token)
            
            # Check role if required
           
            if required_roles:
                user_role = UserRole(payload["role"])
                if user_role not in required_roles:
                    raise ValueError(f"Insufficient permissions. Required: {[r.value for r in required_roles]}")
            
            # Add user info to context
            return {
                **context,
                "authenticated_user": {
                    "username": payload["sub"],
                    "role": payload["role"]
                },
                "auth_token": token
            }
        
        except Exception as e:
            raise ValueError(f"Authentication failed: {str(e)}")
    
    return auth_middleware

# Usage Example
def create_secure_user_management_chain():
    """Create a secure chain for user management operations"""
    
    config = SecurityConfig()
    auth_manager = AuthenticationManager(config)
    
    # Create some test users
    auth_manager.create_user("admin", "admin123", UserRole.ADMIN)
    auth_manager.create_user("john", "user123", UserRole.USER)
    auth_manager.create_user("readonly", "readonly123", UserRole.READONLY)
    
    # Create auth middleware for admin-only operations
    admin_auth = create_auth_middleware(auth_manager, [UserRole.ADMIN])
    
    # Create auth middleware for any authenticated user
    user_auth = create_auth_middleware(auth_manager, [UserRole.ADMIN, UserRole.USER])
    
    def list_users(context: Dict[str, Any]) -> Dict[str, Any]:
        """List all users (admin only)"""
        users = []
        for username, user_data in auth_manager.user_store.items():
            users.append({
                "username": username,
                "role": user_data["role"],
                "active": user_data["active"],
                "last_login": user_data["last_login"].isoformat() if user_data["last_login"] else None
            })
        
        return {**context, "users": users}
    
    def get_user_profile(context: Dict[str, Any]) -> Dict[str, Any]:
        """Get current user's profile"""
        user_info = context["authenticated_user"]
        username = user_info["username"]
        
        user_data = auth_manager.user_store.get(username)
        if not user_data:
            raise ValueError("User not found")
        
        profile = {
            "username": username,
            "role": user_data["role"],
            "last_login": user_data["last_login"].isoformat() if user_data["last_login"] else None,
            "account_status": "active" if user_data["active"] else "inactive"
        }
        
        return {**context, "user_profile": profile}
    
    # Admin-only chain
    admin_chain = (ModuLink()
                  .link(admin_auth)
                  .link(list_users))
    
    # User profile chain (any authenticated user)
    profile_chain = (ModuLink()
                    .link(user_auth)
                    .link(get_user_profile))
    
    return {
        "auth_manager": auth_manager,
        "admin_chain": admin_chain,
        "profile_chain": profile_chain
    }
```

### 2. Input Validation and Sanitization

Protect against injection attacks and data corruption with comprehensive input validation.

```python
from modulink import ModuLink
from typing import Dict, Any, List, Union, Optional
import re
import html
import bleach
from pydantic import BaseModel, validator, ValidationError
from datetime import datetime
import ipaddress

class InputValidator:
    """Comprehensive input validation utilities"""
    
    # Common regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?1?-?\.?\s?\(?\d{3}\)?-?\.?\s?\d{3}-?\.?\s?\d{4}$')
    URL_PATTERN = re.compile(r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(select|insert|update|delete|drop|create|alter|exec|execute|union|script)\b)',
        r'(--|\|\||;|/\*|\*/|xp_)',
        r'(\b(or|and)\s+\d+\s*=\s*\d+)',
        r'(\b(or|and)\s+[\'\"]\w+[\'\"]\s*=\s*[\'\"]\w+[\'\"])'
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>'
    ]
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        return bool(InputValidator.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format"""
        return bool(InputValidator.PHONE_PATTERN.match(phone))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        return bool(InputValidator.URL_PATTERN.match(url))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        return bool(InputValidator.USERNAME_PATTERN.match(username))
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """Check for potential SQL injection patterns"""
        text_lower = text.lower()
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def check_xss(text: str) -> bool:
        """Check for potential XSS patterns"""
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def sanitize_html(text: str, allowed_tags: List[str] = None) -> str:
        """Sanitize HTML content"""
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
        
        return bleach.clean(text, tags=allowed_tags, strip=True)
    
    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML special characters"""
        return html.escape(text)

# Pydantic models for structured validation
class UserRegistrationModel(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if not InputValidator.validate_username(v):
            raise ValueError('Username must be 3-20 characters, alphanumeric and underscore only')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if not InputValidator.validate_email(v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not InputValidator.validate_phone(v):
            raise ValueError('Invalid phone number format')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if v:
            # Check for potential XSS
            if InputValidator.check_xss(v):
                raise ValueError('Invalid characters in name')
            # Sanitize
            v = InputValidator.sanitize_html(v, allowed_tags=[])
        return v

class CommentModel(BaseModel):
    content: str
    author_id: str
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Content cannot be empty')
        if len(v) > 5000:
            raise ValueError('Content too long (max 5000 characters)')
        
        # Check for SQL injection
        if InputValidator.check_sql_injection(v):
            raise ValueError('Content contains potentially dangerous patterns')
        
        # Check for XSS
        if InputValidator.check_xss(v):
            raise ValueError('Content contains potentially dangerous HTML')
        
        return v

def create_input_validation_middleware(model_class: BaseModel):
    """Create input validation middleware for Pydantic models"""
    
    def validation_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
        # Get input data
        input_data = context.get('input_data', context.get('data', {}))
        
        if not input_data:
            raise ValueError("No input data provided for validation")
        
        try:
            # Validate using Pydantic model
            validated_data = model_class(**input_data)
            
            return {
                **context,
                'validated_data': validated_data.dict(),
                'validation_passed': True
            }
        
        except ValidationError as e:
            validation_errors = []
            for error in e.errors():
                validation_errors.append({
                    'field': '.'.join(str(x) for x in error['loc']),
                    'message': error['msg'],
                    'type': error['type']
                })
            
            raise ValueError(f"Validation failed: {validation_errors}")
    
    return validation_middleware

def create_sanitization_middleware():
    """Create sanitization middleware"""
    
    def sanitization_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
        validated_data = context.get('validated_data', {})
        
        if not validated_data:
            return context
        
        sanitized_data = {}
        
        for key, value in validated_data.items():
            if isinstance(value, str):
                # Additional sanitization for string fields
                if key in ['full_name', 'content', 'description']:
                    # Sanitize HTML for text content
                    value = InputValidator.sanitize_html(value)
                elif key not in ['password']:  # Don't modify passwords
                    # Escape HTML for other string fields
                    value = InputValidator.escape_html(value)
            
            sanitized_data[key] = value
        
        return {
            **context,
            'sanitized_data': sanitized_data
        }
    
    return sanitization_middleware

# Usage Examples
def create_secure_user_registration_chain():
    """Create secure user registration chain with validation and sanitization"""
    
    def process_registration(context: Dict[str, Any]) -> Dict[str, Any]:
        sanitized_data = context['sanitized_data']
        
        # Simulate user creation
        user_id = f"USR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            **context,
            'user_created': True,
            'user_id': user_id,
            'username': sanitized_data['username']
        }
    
    return (ModuLink()
            .link(create_input_validation_middleware(UserRegistrationModel))
            .link(create_sanitization_middleware())
            .link(process_registration))

def create_secure_comment_chain():
    """Create secure comment processing chain"""
    
    def save_comment(context: Dict[str, Any]) -> Dict[str, Any]:
        sanitized_data = context['sanitized_data']
        
        # Simulate comment saving
        comment_id = f"CMT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            **context,
            'comment_saved': True,
            'comment_id': comment_id,
            'content_preview': sanitized_data['content'][:100] + '...' if len(sanitized_data['content']) > 100 else sanitized_data['content']
        }
    
    return (ModuLink()
            .link(create_input_validation_middleware(CommentModel))
            .link(create_sanitization_middleware())
            .link(save_comment))

# Demo function
async def security_validation_demo():
    """Demonstrate secure input validation"""
    
    print("=== Security Validation Demo ===")
    
    # Test user registration
    registration_chain = create_secure_user_registration_chain()
    
    # Valid input
    try:
        valid_input = {
            'input_data': {
                'username': 'john_doe',
                'email': 'john@example.com',
                'password': 'SecurePass123',
                'full_name': 'John Doe',
                'phone': '+1-555-123-4567'
            }
        }
        
        result = await registration_chain.execute(valid_input)
        print(f"✅ Valid registration: User {result['username']} created with ID {result['user_id']}")
    
    except Exception as e:
        print(f"❌ Registration failed: {e}")
    
    # Invalid input (SQL injection attempt)
    try:
        malicious_input = {
            'input_data': {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'password123',
                'full_name': "'; DROP TABLE users; --"
            }
        }
        
        result = await registration_chain.execute(malicious_input)
        print(f"❌ Malicious input was processed: {result}")
    
    except Exception as e:
        print(f"✅ Malicious input blocked: {e}")
    
    # Test comment processing
    comment_chain = create_secure_comment_chain()
    
    try:
        xss_input = {
            'input_data': {
                'content': '<script>alert("XSS")</script>This is a comment',
                'author_id': 'USR-123'
            }
        }
        
        result = await comment_chain.execute(xss_input)
        print(f"❌ XSS input was processed: {result}")
    
    except Exception as e:
        print(f"✅ XSS input blocked: {e}")

# Run the demo
# asyncio.run(security_validation_demo())
```

### 3. Secure Secret Management

```python
import os
import base64
from cryptography.fernet import Fernet
from typing import Dict, Any, Optional
import json
import boto3
from dataclasses import dataclass

@dataclass
class SecretConfig:
    encryption_key: Optional[str] = None
    use_aws_secrets: bool = False
    aws_region: str = "us-east-1"
    secret_prefix: str = "modulink/"

class SecretManager:
    """Secure secret management for ModuLink applications"""
    
    def __init__(self, config: SecretConfig):
        self.config = config
        self.cipher = None
        
        if config.encryption_key:
            self.cipher = Fernet(config.encryption_key.encode())
        
        if config.use_aws_secrets:
            self.aws_client = boto3.client('secretsmanager', region_name=config.aws_region)
    
    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a value"""
        if not self.cipher:
            raise ValueError("No encryption key configured")
        
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a value"""
        if not self.cipher:
            raise ValueError("No encryption key configured")
        
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    def get_secret(self, secret_name: str) -> str:
        """Get secret from configured source"""
        
        if self.config.use_aws_secrets:
            return self._get_aws_secret(secret_name)
        else:
            return self._get_env_secret(secret_name)
    
    def _get_env_secret(self, secret_name: str) -> str:
        """Get secret from environment variable"""
        env_var = secret_name.upper().replace('-', '_')
        value = os.getenv(env_var)
        
        if not value:
            raise ValueError(f"Secret {secret_name} not found in environment")
        
        # Try to decrypt if it looks encrypted
        if value.startswith('enc:') and self.cipher:
            try:
                return self.decrypt_value(value[4:])  # Remove 'enc:' prefix
            except Exception:
                pass  # If decryption fails, return as-is
        
        return value
    
    def _get_aws_secret(self, secret_name: str) -> str:
        """Get secret from AWS Secrets Manager"""
        try:
            response = self.aws_client.get_secret_value(
                SecretId=f"{self.config.secret_prefix}{secret_name}"
            )
            return response['SecretString']
        except Exception as e:
            raise ValueError(f"Failed to retrieve secret {secret_name} from AWS: {e}")

def create_secret_injection_middleware(secret_manager: SecretManager, secret_mappings: Dict[str, str]):
    """Create middleware to inject secrets into context"""
    
    def secret_injection_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
        secrets = {}
        
        for context_key, secret_name in secret_mappings.items():
            try:
                secrets[context_key] = secret_manager.get_secret(secret_name)
            except Exception as e:
                raise ValueError(f"Failed to load secret {secret_name}: {e}")
        
        return {
            **context,
            'secrets': secrets
        }
    
    return secret_injection_middleware

# Usage Example
def create_secure_database_chain():
    """Create chain with secure database connection"""
    
    # Configure secret manager
    config = SecretConfig(
        encryption_key=os.getenv('MODULINK_ENCRYPTION_KEY'),
        use_aws_secrets=os.getenv('USE_AWS_SECRETS', 'false').lower() == 'true'
    )
    secret_manager = SecretManager(config)
    
    # Define secret mappings
    secret_mappings = {
        'db_password': 'database-password',
        'api_key': 'external-api-key',
        'encryption_key': 'data-encryption-key'
    }
    
    def connect_to_database(context: Dict[str, Any]) -> Dict[str, Any]:
        secrets = context['secrets']
        
        # Simulate database connection using secrets
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'modulink'),
            'user': os.getenv('DB_USER', 'modulink'),
            'password': secrets['db_password']
        }
        
        # In production, create actual database connection
        # connection = psycopg2.connect(**db_config)
        
        return {
            **context,
            'database_connected': True,
            'connection_info': {k: v for k, v in db_config.items() if k != 'password'}
        }
    
    return (ModuLink()
            .link(create_secret_injection_middleware(secret_manager, secret_mappings))
            .link(connect_to_database))
`````

---

## Monitoring and Observability

### 1. Metrics Collection and Performance Monitoring

Comprehensive monitoring system for ModuLink chains with Prometheus metrics and custom dashboards.

```python
from modulink import ModuLink
from typing import Dict, Any, List, Optional
import time
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry
import logging
import json

@dataclass
class MetricsConfig:
    enable_prometheus: bool = True
    prometheus_port: int = 8000
    enable_custom_metrics: bool = True
    retention_days: int = 7
    aggregation_interval_seconds: int = 60

class ModuLinkMetrics:
    """Comprehensive metrics collection for ModuLink chains"""
    
    def __init__(self, config: MetricsConfig):
        self.config = config
        self.registry = CollectorRegistry()
        
        # Prometheus metrics
        if config.enable_prometheus:
            self.chain_executions = Counter(
                'modulink_chain_executions_total',
                'Total number of chain executions',
                ['chain_name', 'status'],
                registry=self.registry
            )
            
            self.execution_duration = Histogram(
                'modulink_execution_duration_seconds',
                'Chain execution duration in seconds',
                ['chain_name'],
                buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
                registry=self.registry
            )
            
            self.active_chains = Gauge(
                'modulink_active_chains',
                'Number of currently executing chains',
                ['chain_name'],
                registry=self.registry
            )
            
            self.function_executions = Counter(
                'modulink_function_executions_total',
                'Total number of function executions within chains',
                ['chain_name', 'function_name', 'status'],
                registry=self.registry
            )
            
            self.memory_usage = Gauge(
                'modulink_memory_usage_bytes',
                'Memory usage of chain executions',
                ['chain_name'],
                registry=self.registry
            )
        
        # Custom metrics storage
        self.custom_metrics = defaultdict(lambda: defaultdict(list))
        self.execution_history = deque(maxlen=10000)
        self.performance_cache = {}
        
        # Start metrics server
        if config.enable_prometheus:
            start_http_server(config.prometheus_port, registry=self.registry)
    
    def record_chain_execution(self, chain_name: str, duration: float, status: str, memory_usage: Optional[int] = None):
        """Record chain execution metrics"""
        
        # Prometheus metrics
        if self.config.enable_prometheus:
            self.chain_executions.labels(chain_name=chain_name, status=status).inc()
            self.execution_duration.labels(chain_name=chain_name).observe(duration)
            
            if memory_usage:
                self.memory_usage.labels(chain_name=chain_name).set(memory_usage)
        
        # Custom metrics
        if self.config.enable_custom_metrics:
            self.execution_history.append({
                'timestamp': datetime.now(),
                'chain_name': chain_name,
                'duration': duration,
                'status': status,
                'memory_usage': memory_usage
            })
            
            self.custom_metrics[chain_name]['executions'].append({
                'timestamp': datetime.now(),
                'duration': duration,
                'status': status
            })
    
    def record_function_execution(self, chain_name: str, function_name: str, duration: float, status: str):
        """Record individual function execution metrics"""
        
        if self.config.enable_prometheus:
            self.function_executions.labels(
                chain_name=chain_name, 
                function_name=function_name, 
                status=status
            ).inc()
    
    def increment_active_chains(self, chain_name: str):
        """Increment active chain counter"""
        if self.config.enable_prometheus:
            self.active_chains.labels(chain_name=chain_name).inc()
    
    def decrement_active_chains(self, chain_name: str):
        """Decrement active chain counter"""
        if self.config.enable_prometheus:
            self.active_chains.labels(chain_name=chain_name).dec()
    
    def get_performance_summary(self, chain_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for chains"""
        
        if chain_name:
            executions = [e for e in self.execution_history if e['chain_name'] == chain_name]
        else:
            executions = list(self.execution_history)
        
        if not executions:
            return {"message": "No execution data available"}
        
        successful_executions = [e for e in executions if e['status'] == 'success']
        failed_executions = [e for e in executions if e['status'] == 'error']
        
        durations = [e['duration'] for e in successful_executions]
        
        summary = {
            'total_executions': len(executions),
            'successful_executions': len(successful_executions),
            'failed_executions': len(failed_executions),
            'success_rate': len(successful_executions) / len(executions) if executions else 0,
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'p95_duration': self._calculate_percentile(durations, 0.95) if durations else 0,
            'p99_duration': self._calculate_percentile(durations, 0.99) if durations else 0
        }
        
        return summary
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile from list of values"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of ModuLink system"""
        
        recent_executions = [
            e for e in self.execution_history 
            if e['timestamp'] > datetime.now() - timedelta(minutes=5)
        ]
        
        if not recent_executions:
            return {
                'status': 'unknown',
                'message': 'No recent executions to evaluate health'
            }
        
        recent_errors = [e for e in recent_executions if e['status'] == 'error']
        error_rate = len(recent_errors) / len(recent_executions)
        
        avg_duration = sum(e['duration'] for e in recent_executions) / len(recent_executions)
        
        # Determine health status
        if error_rate > 0.1:  # More than 10% errors
            status = 'unhealthy'
            message = f'High error rate: {error_rate:.1%}'
        elif avg_duration > 30:  # Average duration > 30 seconds
            status = 'degraded'
            message = f'High average duration: {avg_duration:.2f}s'
        else:
            status = 'healthy'
            message = 'All systems operating normally'
        
        return {
            'status': status,
            'message': message,
            'recent_executions': len(recent_executions),
            'error_rate': error_rate,
            'avg_duration': avg_duration
        }

def create_monitoring_middleware(metrics: ModuLinkMetrics, chain_name: str):
    """Create monitoring middleware for ModuLink chains"""
    
    def monitoring_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        metrics.increment_active_chains(chain_name)
        
        try:
            # Add monitoring context
            monitoring_context = {
                **context,
                '_monitoring': {
                    'chain_name': chain_name,
                    'start_time': start_time,
                    'execution_id': f"{chain_name}_{int(start_time * 1000)}"
                }
            }
            
            return monitoring_context
        
        except Exception as e:
            # Record failed execution
            duration = time.time() - start_time
            metrics.record_chain_execution(chain_name, duration, 'error')
            metrics.decrement_active_chains(chain_name)
            raise e
    
    return monitoring_middleware

def create_completion_middleware(metrics: ModuLinkMetrics):
    """Create completion monitoring middleware"""
    
    def completion_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
        monitoring_info = context.get('_monitoring', {})
        
        if monitoring_info:
            chain_name = monitoring_info['chain_name']
            start_time = monitoring_info['start_time']
            duration = time.time() - start_time
            
            # Record successful execution
            metrics.record_chain_execution(chain_name, duration, 'success')
            metrics.decrement_active_chains(chain_name)
        
        # Remove internal tracing fields
        final_context = {k: v for k, v in context.items() if not k.startswith('_')}
        
        return final_context
    
    return completion_middleware
```

### 2. Distributed Tracing and Request Correlation

```python
from modulink import ModuLink
from typing import Dict, Any, Optional, List
import uuid
import time
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

@dataclass
class TracingConfig:
    service_name: str = "modulink-service"
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    enable_auto_instrumentation: bool = True
    sample_rate: float = 1.0  # Sample 100% of traces

@dataclass
class TraceSpan:
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = ""
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "unknown"
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)

class DistributedTracer:
    """Distributed tracing for ModuLink chains"""
    
    def __init__(self, config: TracingConfig):
        self.config = config
        self.active_spans = {}
        self.completed_spans = []
        self.local = threading.local()
        
        # Initialize OpenTelemetry if configured
        if config.jaeger_endpoint:
            self._setup_opentelemetry()
    
    def _setup_opentelemetry(self):
        """Setup OpenTelemetry with Jaeger exporter"""
        trace.set_tracer_provider(TracerProvider())
        
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )
        
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        if self.config.enable_auto_instrumentation:
            RequestsInstrumentor().instrument()
        
        self.tracer = trace.get_tracer(self.config.service_name)
    
    def start_trace(self, operation_name: str, trace_id: Optional[str] = None) -> TraceSpan:
        """Start a new trace"""
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        span = TraceSpan(
            trace_id=trace_id,
            operation_name=operation_name,
            start_time=datetime.now()
        )
        
        self.active_spans[span.span_id] = span
        self._set_current_span(span)
        
        return span
    
    def start_child_span(self, operation_name: str, parent_span: Optional[TraceSpan] = None) -> TraceSpan:
        """Start a child span"""
        if not parent_span:
            parent_span = self._get_current_span()
        
        if not parent_span:
            return self.start_trace(operation_name)
        
        child_span = TraceSpan(
            trace_id=parent_span.trace_id,
            parent_span_id=parent_span.span_id,
            operation_name=operation_name,
            start_time=datetime.now()
        )
        
        self.active_spans[child_span.span_id] = child_span
        self._set_current_span(child_span)
        
        return child_span
    
    def finish_span(self, span: TraceSpan, status: str = "success", tags: Optional[Dict[str, Any]] = None):
        """Finish a span"""
        span.end_time = datetime.now()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        
        if tags:
            span.tags.update(tags)
        
        # Move to completed spans
        if span.span_id in self.active_spans:
            del self.active_spans[span.span_id]
        
        self.completed_spans.append(span)
        
        # Set parent as current span if exists
        if span.parent_span_id and span.parent_span_id in self.active_spans:
            parent_span = self.active_spans[span.parent_span_id]
            self._set_current_span(parent_span)
        else:
            self._set_current_span(None)
    
    def add_span_tag(self, span: TraceSpan, key: str, value: Any):
        """Add tag to span"""
        span.tags[key] = value
    
    def add_span_log(self, span: TraceSpan, message: str, level: str = "info", **kwargs):
        """Add log entry to span"""
        log_entry = {
            'timestamp': datetime.now(),
            'level': level,
            'message': message,
            **kwargs
        }
        span.logs.append(log_entry)
    
    def _set_current_span(self, span: Optional[TraceSpan]):
        """Set current span in thread-local storage"""
        self.local.current_span = span
    
    def _get_current_span(self) -> Optional[TraceSpan]:
        """Get current span from thread-local storage"""
        return getattr(self.local, 'current_span', None)
    
    @contextmanager
    def trace_operation(self, operation_name: str, parent_span: Optional[TraceSpan] = None):
        """Context manager for tracing operations"""
        span = self.start_child_span(operation_name, parent_span)
        
        try:
            yield span
            self.finish_span(span, "success")
        except Exception as e:
            self.add_span_tag(span, "error", str(e))
            self.add_span_log(span, f"Operation failed: {str(e)}", "error")
            self.finish_span(span, "error")
            raise
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get summary of a trace"""
        trace_spans = [span for span in self.completed_spans if span.trace_id == trace_id]
        
        if not trace_spans:
            return {"message": "Trace not found"}
        
        root_spans = [span for span in trace_spans if span.parent_span_id is None]
        total_duration = sum(span.duration_ms for span in trace_spans if span.duration_ms)
        
        error_spans = [span for span in trace_spans if span.status == "error"]
        
        return {
            'trace_id': trace_id,
            'total_spans': len(trace_spans),
            'root_spans': len(root_spans),
            'total_duration_ms': total_duration,
            'error_count': len(error_spans),
            'status': 'error' if error_spans else 'success',
            'operations': list(set(span.operation_name for span in trace_spans))
        }

def create_tracing_middleware(tracer: DistributedTracer, operation_name: str):
    """Create distributed tracing middleware"""
    
    def tracing_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
        # Check if there's already a trace context
        existing_trace_id = context.get('trace_id')
        existing_span_id = context.get('span_id')
        
        if existing_trace_id and existing_span_id:
            # Continue existing trace
            parent_span = TraceSpan(
                span_id=existing_span_id,
                trace_id=existing_trace_id,
                operation_name="parent_operation"
            )
            span = tracer.start_child_span(operation_name, parent_span)
        else:
            # Start new trace
            span = tracer.start_trace(operation_name)
        
        # Add tracing context
        tracing_context = {
            **context,
            'trace_id': span.trace_id,
            'span_id': span.span_id,
            '_current_span': span
        }
        
        # Add context tags to span
        tracer.add_span_tag(span, 'chain_operation', operation_name)
        if 'user_id' in context:
            tracer.add_span_tag(span, 'user_id', context['user_id'])
        if 'request_id' in context:
            tracer.add_span_tag(span, 'request_id', context['request_id'])
        
        return tracing_context
    
    return tracing_middleware

def create_span_completion_middleware(tracer: DistributedTracer):
    """Create span completion middleware"""
    
    def span_completion_middleware(context: Dict[str, Any]) -> Dict[str, Any]:
        current_span = context.get('_current_span')
        
        if current_span:
            # Add final context information to span
            tracer.add_span_tag(current_span, 'execution_completed', True)
            
            # Add performance metrics
            if '_performance_metrics' in context:
                metrics = context['_performance_metrics']
                for key, value in metrics.items():
                    tracer.add_span_tag(current_span, f'perf_{key}', value)
            
            tracer.finish_span(current_span, "success")
        
        # Remove internal tracing fields
        final_context = {
            k: v for k, v in context.items() 
            if not k.startswith('_') or k in ['trace_id', 'span_id']
        }
        
        return final_context
    
    return span_completion_middleware
```

### 3. Logging and Alerting

Effective logging and alerting are crucial for maintaining system health and diagnosing issues promptly.

*   **Structured Logging**: Implement structured logging (e.g., JSON format) to make logs easily machine-readable and searchable. Include contextual information like request IDs, user IDs, and chain/module names.
*   **Centralized Logging**: Use a centralized logging solution (e.g., ELK stack, Splunk, Grafana Loki) to aggregate logs from all services.
*   **Alerting Rules**: Define alert rules based on critical metrics (e.g., error rates, latency spikes, resource saturation) and log patterns (e.g., specific error messages).
*   **Notification Channels**: Configure alerts to notify the appropriate teams via channels like email, Slack, or PagerDuty.

```python
import logging
import json
import uuid

class StructuredLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = self.extra.copy()
        extra.update(kwargs.get("extra", {}))
        return \'\'\'[%s] %s\'\'\' % (json.dumps(extra), msg), kwargs

# Configure root logger for structured logging
logger = logging.getLogger("modulink_app")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(\'\'\'{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}\'\'\')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_contextual_logger(context_data=None):
    base_extra = {"app_version": "1.0.0"}
    if context_data:
        base_extra.update(context_data)
    return StructuredLoggerAdapter(logger, base_extra)

# Example usage in a ModuLink module
async def process_payment_module(data: dict, context: dict):
    request_id = context.get("request_id", str(uuid.uuid4()))
    user_id = data.get("user_id")
    module_logger = get_contextual_logger({"request_id": request_id, "user_id": user_id, "module": "process_payment"})

    module_logger.info("Processing payment")
    try:
        # ... payment processing logic ...
        if data.get("amount", 0) > 10000: # Example condition for an alert
            module_logger.error("Large transaction detected", extra={"amount": data.get("amount")})
            # Here, an external system would pick up this structured error log and trigger an alert
        module_logger.info("Payment processed successfully")
        return {"status": "success", "transaction_id": str(uuid.uuid4())}
    except Exception as e:
        module_logger.exception("Payment processing failed")
        # Alerting system would also pick up on high rates of "Payment processing failed"
        raise

# --- Alerting (Conceptual - actual implementation depends on monitoring system) ---
# Assume a monitoring system (e.g., Prometheus Alertmanager, Grafana Alerts) is configured
# to scrape logs or metrics and trigger alerts based on rules.

# Example Alertmanager rule (conceptual, in YAML):
# groups:
# - name: ModuLinkAppAlerts
#   rules:
#   - alert: HighPaymentErrorRate
#     expr: rate(modulink_payment_errors_total[5m]) > 0.1 # If error rate exceeds 10% in 5 mins
#     for: 1m
#     labels:
#       severity: critical
#     annotations:
#       summary: High payment error rate in ModuLink
#       description: "The payment processing module is experiencing an error rate of {{ $value }}%. Please investigate."
#
#   - alert: LargeTransactionDetected
#     expr: \'\'\'ALERTS{alertname="LargeTransactionDetected", job="modulink_app_logs"} == 1\'\'\' # Based on log pattern
#     for: 0m
#     labels:
#       severity: warning
#     annotations:
#       summary: Large transaction detected
#       description: "A transaction exceeding the threshold was processed. Amount: {{ $labels.amount }}. Request ID: {{ $labels.request_id }}"

async def main_monitoring_example():
    # Simulate a request
    await process_payment_module({"amount": 15000, "user_id": "user123"}, {"request_id": "req-abc-123"})
    await process_payment_module({"amount": 50, "user_id": "user456"}, {"request_id": "req-def-456"})
    try:
        await process_payment_module({"user_id": "user789"}, {"request_id": "req-ghi-789"}) # Missing amount, will cause error
    except:
        pass

if __name__ == "__main__":
    # This example focuses on logging. For actual metrics and tracing,
    # you'd integrate Prometheus and OpenTelemetry as shown previously.
    import asyncio
    asyncio.run(main_monitoring_example())
```

This concludes the Monitoring and Observability section. By implementing these patterns, you can gain deep insights into your ModuLink application's behavior, performance, and health, enabling proactive maintenance and rapid issue resolution.

## Real-World Case Studies

This section explores how ModuLink's advanced patterns can be applied to solve complex, real-world problems across different domains. These case studies are illustrative and aim to inspire architects and developers to leverage ModuLink's flexibility.

### Case Study 1: E-commerce Order Processing Pipeline

**Scenario**: A large e-commerce platform needs a robust and scalable order processing system. The process involves multiple steps: inventory check, payment authorization, fraud detection, order confirmation (email/SMS), and warehouse notification. Each step might involve different microservices or third-party APIs.

**ModuLink Application**:

*   **Pattern**: Event-Driven Chain Architecture combined with Microservice Chain Orchestration.
*   **Chain Structure**:
    1.  `OrderReceivedEventTrigger`: Initiates the chain when a new order event is received (e.g., from Kafka or RabbitMQ).
    2.  `InventoryCheckModule`: Calls the inventory microservice.
        *   **Advanced Pattern**: Circuit Breaker for resilience against inventory service unavailability.
    3.  `PaymentAuthorizationModule`: Integrates with a payment gateway.
        *   **Advanced Pattern**: Secure Secret Management for API keys; Idempotency for payment requests.
    4.  `FraudDetectionModule`: Calls a fraud detection service.
        *   **Advanced Pattern**: Conditional Execution (e.g., skip for low-value orders or trusted customers).
    5.  `OrderConfirmationModule`: Sends email and SMS notifications.
        *   **Advanced Pattern**: Parallel Execution (send email and SMS concurrently). Retry mechanisms for transient notification failures.
    6.  `WarehouseNotificationModule`: Pushes order details to the warehouse management system.
*   **Scalability**: Horizontal scaling of chain workers. Resource pools for I/O-bound tasks like API calls.
*   **Monitoring**: Distributed tracing to track an order across all modules and services. Metrics for processing time per module, error rates, and throughput. Alerts for payment failures or high fraud scores.
*   **Deployment**: Containerized deployment on Kubernetes, allowing individual components (like chain workers or specific microservice proxies if used) to scale independently.

**Benefits**:
*   **Decoupling**: Each step is an independent module, simplifying development and maintenance.
*   **Resilience**: Patterns like Circuit Breaker and Retries improve system robustness.
*   **Scalability**: Handles peak loads by scaling chain workers and leveraging asynchronous processing.
*   **Observability**: Clear visibility into the order lifecycle.

### Case Study 2: Financial Data Aggregation and Reporting Service

**Scenario**: A fintech company needs to aggregate financial data from multiple sources (banks, investment platforms, crypto exchanges via APIs), normalize it, perform complex calculations (e.g., portfolio valuation, risk assessment), and generate customized reports for users. Data privacy and accuracy are paramount.

**ModuLink Application**:

*   **Pattern**: Hybrid of Sequential and Parallel Chain Execution.
*   **Chain Structure**:
    *   **Outer Chain (User-Specific Aggregation)**:
        1.  `UserAuthenticationModule`: Verifies user identity.
            *   **Security**: JWT-based authentication middleware.
        2.  `DataSourceConfigurationModule`: Fetches user-configured data sources.
        3.  `ParallelDataFetchingBranch`: A dynamic parallel execution branch.
            *   For each configured data source, a sub-chain is spawned:
                *   `ApiConnectorModule`: Connects to the specific financial API (e.g., Plaid for banks, exchange-specific API for crypto).
                    *   **Advanced Pattern**: Secure Secret Management for API tokens. Rate Limiting to respect API quotas.
                *   `DataNormalizationModule`: Transforms fetched data into a standard internal format.
                    *   **Advanced Pattern**: Input Validation and Sanitization for incoming API data.
        4.  `DataConsolidationModule`: Merges normalized data from all sources.
        5.  `CalculationEngineModule`: Performs portfolio valuation, risk analysis, etc.
            *   **Advanced Pattern**: Memory-Efficient Chain Processing if dealing with very large datasets for a user.
        6.  `ReportGenerationModule`: Creates a personalized report (e.g., PDF, JSON).
        7.  `SecureReportDeliveryModule`: Makes the report available to the user securely.
*   **Security**: End-to-end encryption for sensitive data. Strict input validation. Role-based access control for different data types and operations. Regular security audits.
*   **Performance**: Parallel fetching of data from multiple sources significantly reduces aggregation time. Caching for frequently accessed, non-volatile data.
*   **Deployment**: Blue-Green deployment for critical updates to the calculation engine or API connectors to ensure zero downtime.

**Benefits**:
*   **Accuracy & Security**: Strong focus on data integrity and protection through validation and security patterns.
*   **Efficiency**: Parallel processing speeds up data aggregation.
*   **Flexibility**: Easily add new data source types by creating new API connector and normalization modules.
*   **Maintainability**: Modular design allows for easier updates and bug fixes in specific parts of the pipeline.

### Case Study 3: IoT Data Ingestion and Real-time Analytics Platform

**Scenario**: A smart city initiative deploys thousands of IoT sensors (traffic, environmental, energy usage). Data needs to be ingested, processed in real-time for anomalies or critical events, and stored for historical analysis and dashboarding.

**ModuLink Application**:

*   **Pattern**: High-throughput Event-Driven Chain Architecture.
*   **Chain Structure (per data stream/sensor type)**:
    1.  `MqttIngestionModule` / `HttpIngestionModule`: Receives data from sensors via MQTT or HTTP endpoints.
        *   **Scalability**: Horizontally scaled ingestion endpoints.
    2.  `DataValidationAndEnrichmentModule`: Validates sensor data format, enriches with metadata (sensor ID, location, timestamp).
        *   **Advanced Pattern**: Schema validation (e.g., using Pydantic).
    3.  `RealtimeAnalyticsBranch` (Parallel Execution):
        *   `AnomalyDetectionModule`: Uses statistical models or ML to detect unusual patterns (e.g., sudden traffic jams, pollution spikes).
            *   **Action**: If anomaly detected, triggers an `AlertingSubChain`.
        *   `CriticalEventFilteringModule`: Checks for predefined critical event signatures.
            *   **Action**: If critical event, triggers an `EmergencyResponseSubChain`.
    4.  `TimeSeriesStorageModule`: Persists processed data into a time-series database (e.g., InfluxDB, TimescaleDB).
    5.  `DashboardUpdateModule` (Optional, could be event-driven from DB): Pushes aggregated data or event summaries to a real-time dashboarding service.
*   **Advanced Patterns**:
    *   **Resource Pools**: For managing connections to the time-series database.
    *   **Backpressure Handling**: If the processing chain cannot keep up with ingestion rates, implement strategies like dropping non-critical data or scaling workers.
    *   **Dynamic Chain Configuration**: Potentially adjust analytics parameters or thresholds dynamically based on external inputs or system learning.
*   **Monitoring**: Metrics on data ingestion rates, processing latency per module, anomaly detection rates, and database write performance. Alerts for ingestion pipeline failures or critical event detections.
*   **Deployment**: Canary deployment for new versions of analytics modules to test their impact on a subset of sensor data before full rollout.

**Benefits**:
*   **Real-time Insights**: Enables immediate response to critical events and anomalies.
*   **Scalability**: Designed to handle massive volumes of data from numerous sensors.
*   **Modularity**: Analytics modules can be updated or replaced independently (e.g., swapping out an ML model).
*   **Data Integrity**: Validation ensures data quality before storage and analysis.

These case studies demonstrate the versatility of ModuLink in building sophisticated, scalable, and maintainable applications. By combining core ModuLink concepts with advanced patterns, developers can tackle a wide array of complex challenges.

## Conclusion and Future Directions

As we conclude this advanced patterns cookbook, it's essential to recognize that the journey of building scalable, resilient, and high-performance applications with ModuLink is continuous. The patterns and practices outlined in this cookbook provide a robust foundation, but the ever-evolving tech landscape requires constant learning and adaptation.

### Key Takeaways
-   **Modularity and Flexibility**: ModuLink's core strength lies in its modularity. Each pattern demonstrated in this cookbook showcases how to break down complex processes into manageable, independent modules. This approach not only simplifies development and testing but also enhances maintainability and scalability.
-   **Performance Optimization**: Leveraging asynchronous processing, parallel execution, and resource pooling can significantly enhance application performance. Always monitor and profile applications to identify bottlenecks and optimize resource utilization.
-   **Scalability**: Horizontal scaling, whether through microservice orchestration or event-driven architectures, provides the flexibility to handle varying loads. Coupled with auto-scaling mechanisms, applications can achieve high availability and resilience.
-   **Security**: Implementing robust authentication, authorization, input validation, and secure secret management is paramount. Security should be integrated into every layer of the application, from data ingestion to processing and storage.
-   **Monitoring and Observability**: Comprehensive monitoring, tracing, and logging are crucial for maintaining system health and diagnosing issues. Implementing these from the outset ensures that potential problems are detected and addressed proactively.

### Future Directions
-   **Emerging Technologies**: Stay abreast of emerging technologies and frameworks that can complement or enhance ModuLink applications, such as serverless architectures, micro-frontends, and advanced data processing frameworks.
-   **Community and Ecosystem**: Engage with the ModuLink community. Sharing experiences, patterns, and solutions fosters a richer ecosystem and accelerates collective learning.
-   **Continuous Learning**: The patterns in this cookbook are a starting point. Delve deeper into each pattern, experiment with variations, and adapt them to fit specific use cases and requirements.

In closing, ModuLink offers a powerful and flexible foundation for building the next generation of distributed applications. By mastering these advanced patterns, developers and architects are well-equipped to tackle the challenges of today and innovate for the opportunities of tomorrow.
