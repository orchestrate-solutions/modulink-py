"""
Universal Type System Utilities

Helper functions and utilities for working with the universal types system
"""

import asyncio
import json
import time
from typing import Dict, Any, Callable, List, Optional, Union, Awaitable
from .universal import Ctx, Link, Chain, Trigger, Middleware

async def _ensure_async(fn: Callable) -> Callable[[Ctx], Awaitable[Ctx]]:
    """Helper function to ensure a function is async."""
    if asyncio.iscoroutinefunction(fn):
        return fn
    else:
        async def async_wrapper(ctx: Ctx) -> Ctx:
            return fn(ctx)
        return async_wrapper

from .utils import chain

def compose(*links: Link) -> Chain:
    """Legacy alias for chain function."""
    return chain(*links)

def when(predicate: Callable[[Ctx], bool], link: Link) -> Link:
    """Create a conditional link that only executes if predicate is true."""
    async def conditional_link(ctx: Ctx) -> Ctx:
        if predicate(ctx):
            return await link(ctx)
        return ctx
    
    return conditional_link

def catch_errors(error_handler: Callable[[Any, Ctx], Ctx]) -> Middleware:
    """Create a link that catches and handles errors."""
    async def error_middleware(ctx: Ctx) -> Ctx:
        try:
            return await _ensure_async(ctx)
        except Exception as error:
            return error_handler(error, ctx)
    
    return error_middleware

def timing(label: str = "execution") -> Middleware:
    """Create timing middleware."""
    async def timing_middleware(ctx: Ctx) -> Ctx:
        start = time.time() * 1000  # Convert to milliseconds
        
        # In a real middleware system, this would wrap the next function
        # For now, we'll just add timing info to context
        duration = time.time() * 1000 - start
        
        timing_info = ctx.get("timing", {})
        timing_info[label] = duration
        
        return {**ctx, "timing": timing_info}
    
    return timing_middleware

def logging(
    log_input: bool = True,
    log_output: bool = True, 
    log_timing: bool = True
) -> Middleware:
    """Create logging middleware."""
    async def logging_middleware(ctx: Ctx) -> Ctx:
        if log_input:
            print(f"[ModuLink] Input: {json.dumps(ctx, indent=2, default=str)}")
        
        start = time.time() * 1000
        
        # In a real implementation, this would wrap the chain execution
        # For now, we'll just add logging info
        duration = time.time() * 1000 - start
        
        if log_timing:
            print(f"[ModuLink] Execution time: {duration:.2f}ms")
        
        if log_output:
            print(f"[ModuLink] Output: {json.dumps(ctx, indent=2, default=str)}")
        
        return ctx
    
    return logging_middleware

def validate(schema: Callable[[Ctx], Union[bool, str]]) -> Middleware:
    """Create validation middleware."""
    async def validation_middleware(ctx: Ctx) -> Ctx:
        validation = schema(ctx)
        
        if validation is False:
            return {**ctx, "error": Exception("Validation failed")}
        
        if isinstance(validation, str):
            return {**ctx, "error": Exception(validation)}
        
        return ctx
    
    return validation_middleware

def retry(max_attempts: int, delay: float = 1.0) -> Middleware:
    """Create a retry wrapper for chains."""
    async def retry_middleware(ctx: Ctx) -> Ctx:
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                # In a real implementation, this would retry the chain
                # For now, we'll just add retry info to context
                if not ctx.get("error"):
                    return {**ctx, "attempt": attempt}
                last_error = ctx.get("error")
            except Exception as error:
                last_error = error
            if attempt < max_attempts:
                await asyncio.sleep(delay)

        return {**ctx, "error": last_error, "attempts": max_attempts}
    
    return retry_middleware

def transform(field: str, transformer: Callable[[Any, Ctx], Any]) -> Link:
    """Create a transform link that modifies specific fields."""
    async def transform_link(ctx: Ctx) -> Ctx:
        return {
            **ctx,
            field: transformer(ctx.get(field), ctx)
        }
    
    return transform_link

def set_values(values: Dict[str, Any]) -> Link:
    """Create a link that sets values in the context."""
    async def set_link(ctx: Ctx) -> Ctx:
        return {**ctx, **values}
    
    return set_link

def filter_context(predicate: Callable[[str, Any], bool]) -> Link:
    """Create a link that filters context properties."""
    async def filter_link(ctx: Ctx) -> Ctx:
        filtered = {}
        
        for key, value in ctx.items():
            if predicate(key, value):
                filtered[key] = value
        
        return filtered
    
    return filter_link

def parallel(*links: Link) -> Link:
    """Create a parallel execution utility."""
    async def parallel_link(ctx: Ctx) -> Ctx:
        results = await asyncio.gather(*[link(ctx) for link in links])
        
        # Merge all results, with later results taking precedence
        merged = {}
        for result in results:
            merged.update(result)
        
        return merged
    
    return parallel_link

def debounce(delay: float, link: Link) -> Link:
    """Create a debounced link."""
    last_call = {"time": 0, "task": None}
    
    async def debounced_link(ctx: Ctx) -> Ctx:
        current_time = time.time()
        
        # Cancel previous task if it exists
        if last_call["task"] and not last_call["task"].done():
            last_call["task"].cancel()
        
        # Create new task
        async def delayed_execution():
            await asyncio.sleep(delay)
            return await link(ctx)
        
        last_call["task"] = asyncio.create_task(delayed_execution())
        last_call["time"] = current_time
        
        return await last_call["task"]
    
    return debounced_link

def memoize(
    key_fn: Callable[[Ctx], str],
    link: Link,
    ttl: float = 60.0  # 1 minute default TTL
) -> Link:
    """Create a memoized link (caches results based on a key function)."""
    cache: Dict[str, Dict[str, Any]] = {}
    
    async def memoized_link(ctx: Ctx) -> Ctx:
        key = key_fn(ctx)
        now = time.time()
        cached = cache.get(key)
        
        if cached and cached["expires"] > now:
            return {**cached["result"], "from_cache": True}
        
        result = await link(ctx)
        cache[key] = {"result": result, "expires": now + ttl}
        
        # Clean up expired entries
        expired_keys = [k for k, v in cache.items() if v["expires"] <= now]
        for k in expired_keys:
            del cache[k]
        
        return result
    
    return memoized_link

# Common error handling patterns
class ErrorHandlers:
    @staticmethod
    def log_and_continue(error: Any, ctx: Ctx) -> Ctx:
        """Log errors and continue."""
        print(f"[ModuLink] Error: {error}")
        return {**ctx, "error": error}
    
    @staticmethod
    def user_friendly(error: Any, ctx: Ctx) -> Ctx:
        """Transform errors into user-friendly messages."""
        message = str(error) if isinstance(error, Exception) else "An unexpected error occurred"
        return {**ctx, "error": {"message": message, "user_friendly": True}}
    
    @staticmethod
    def retry_on(error_types: List[str], max_retries: int = 3):
        """Retry on specific error types."""
        def handler(error: Any, ctx: Ctx) -> Ctx:
            error_type = type(error).__name__ if isinstance(error, Exception) else "Unknown"
            should_retry = error_type in error_types
            retry_count = ctx.get("retry_count", 0) + 1
            
            if should_retry and retry_count <= max_retries:
                return {**ctx, "error": error, "retry_count": retry_count, "should_retry": True}
            
            return {**ctx, "error": error, "retry_count": retry_count}
        
        return handler

# Common validation patterns
class Validators:
    @staticmethod
    def required(fields: List[str]):
        """Require specific fields to be present."""
        def validator(ctx: Ctx) -> Union[bool, str]:
            missing = [field for field in fields if ctx.get(field) is None]
            return True if not missing else f"Missing required fields: {', '.join(missing)}"
        
        return validator
    
    @staticmethod
    def types(schema: Dict[str, str]):
        """Validate field types."""
        def validator(ctx: Ctx) -> Union[bool, str]:
            for field, expected_type in schema.items():
                value = ctx.get(field)
                actual_type = type(value).__name__
                
                if value is not None and actual_type != expected_type:
                    return f"Field '{field}' should be {expected_type} but got {actual_type}"
            
            return True
        
        return validator
    
    @staticmethod
    def custom(fn: Callable[[Ctx], Union[bool, str]]):
        """Custom validation function."""
        return fn

# Export commonly used instances
error_handlers = ErrorHandlers()
validators = Validators()

def performance_tracker() -> Middleware:
    """Performance tracker middleware."""
    async def performance_middleware(ctx: Ctx) -> Ctx:
        start_time = time.time()
        
        # In a real implementation, this would track memory usage, CPU time, etc.
        # For now, we'll just add timing info to context
        
        if "performance" not in ctx:
            ctx["performance"] = {}
        
        ctx["performance"]["start_time"] = start_time
        
        return ctx
    
    return performance_middleware
