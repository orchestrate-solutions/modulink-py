# ModuLink Patterns Cheatsheet (Code Examples)

Quick reference for ModuLink patterns with visual code examples.

## Quick Navigation

### [👶 Beginner Level Patterns](#-beginner-level-patterns)
-   [1. Core Design Principles](#1-core-design-principles)
    -   [Single Responsibility](#single-responsibility)
    -   [Immutable Context](#immutable-context)
    -   [Predictable Data Flow (Pure Functions)](#predictable-data-flow-pure-functions)
-   [2. Function Design Patterns](#2-function-design-patterns)
    -   [Validator Function](#validator-function)
    -   [Transformer Function](#transformer-function)
    -   [Enricher Function](#enricher-function)
    -   [Guard Function](#guard-function)
-   [3. Basic Chain Composition](#3-basic-chain-composition)
    -   [Linear Chain](#linear-chain)
-   [4. Context Flow Management](#4-context-flow-management)
    -   [Context Accumulation](#context-accumulation)
    -   [Context Cleaning](#context-cleaning)
-   [5. Simple Error Handling](#5-simple-error-handling)
    -   [Try-Catch in Functions](#try-catch-in-functions)

### [🧑 Intermediate Level Patterns](#-intermediate-level-patterns)
-   [1. Advanced Orchestration](#1-advanced-orchestration)
    -   [Parallel Execution (Conceptual)](#parallel-execution-conceptual)
-   [2. Middleware & Cross-Cutting Concerns](#2-middleware--cross-cutting-concerns)
    -   [Logging Middleware (Decorator Style)](#logging-middleware-decorator-style)
    -   [Circuit Breaker (Conceptual)](#circuit-breaker-conceptual)
-   [3. State Management](#3-state-management)
    -   [Context State Machine (Conceptual Update)](#context-state-machine-conceptual-update)
-   [4. Conditional Execution](#4-conditional-execution)
    -   [Rule-Based Execution (Simple)](#rule-based-execution-simple)
    -   [Feature Flag (Simple)](#feature-flag-simple)

### [🧙 Advanced Level Patterns](#-advanced-level-patterns)
-   [1. Enterprise Architecture](#1-enterprise-architecture)
    -   [Microservice Chain Orchestration (Conceptual Call)](#microservice-chain-orchestration-conceptual-call)
    -   [Event-Driven Chain (Conceptual Publish)](#event-driven-chain-conceptual-publish)
-   [2. Performance Optimization](#2-performance-optimization)
    -   [Parallel Execution with Resource Pools (Conceptual)](#parallel-execution-with-resource-pools-conceptual)
    -   [Memory-Efficient Processing (Streaming/Generators)](#memory-efficient-processing-streaminggenerators)
-   [3. Scalability Patterns](#3-scalability-patterns)
    -   [Horizontal Scaling (Conceptual - Infrastructure Level)](#horizontal-scaling-conceptual---infrastructure-level)
-   [4. Production Deployment Strategies](#4-production-deployment-strategies)
    -   [Containerized Deployment (Dockerfile Snippet)](#containerized-deployment-dockerfile-snippet)
    -   [Blue-Green / Canary (Conceptual - Traffic Shifting)](#blue-green--canary-conceptual---traffic-shifting)
-   [5. Security Patterns](#5-security-patterns)
    -   [Authentication Middleware (Conceptual)](#authentication-middleware-conceptual)
    -   [Input Validation (Pydantic Example)](#input-validation-pydantic-example)
    -   [Secure Secret Management (Conceptual Access)](#secure-secret-management-conceptual-access)
-   [6. Monitoring and Observability](#6-monitoring-and-observability)
    -   [Metrics Collection (Prometheus Client Snippet)](#metrics-collection-prometheus-client-snippet)
    -   [Distributed Tracing (Conceptual Span)](#distributed-tracing-conceptual-span)
    -   [Structured Logging](#structured-logging)

---

## 👶 Beginner Level Patterns

### 1. Core Design Principles

#### Single Responsibility
    ```python
    # Each function does one thing well
    async def validate_email(ctx: dict) -> dict:
        email = ctx.get("email")
        is_valid = "@" in email if email else False
        return {**ctx, "email_valid": is_valid}
    ```
[⬆️](#quick-navigation)

#### Immutable Context
    ```python
    async def add_timestamp(ctx: dict) -> dict:
        # Return a NEW dictionary
        return {**ctx, "timestamp": datetime.now()}
    ```
[⬆️](#quick-navigation)

#### Predictable Data Flow (Pure Functions)
    ```python
    async def calculate_total(ctx: dict) -> dict:
        price = ctx.get("price", 0)
        quantity = ctx.get("quantity", 0)
        # Same input -> same output, no side effects
        return {**ctx, "total": price * quantity}
    ```
[⬆️](#quick-navigation)

### 2. Function Design Patterns

#### Validator Function
    ```python
    async def check_age_limit(ctx: dict) -> dict:
        age = ctx.get("age", 0)
        if age < 18:
            return {**ctx, "age_error": "Must be 18 or older"}
        return {**ctx, "age_ok": True}
    ```
[⬆️](#quick-navigation)

#### Transformer Function
    ```python
    async def normalize_username(ctx: dict) -> dict:
        username = ctx.get("username", "")
        return {**ctx, "username_normalized": username.lower().strip()}
    ```
[⬆️](#quick-navigation)

#### Enricher Function
    ```python
    async def fetch_user_profile(ctx: dict) -> dict:
        user_id = ctx.get("user_id")
        # profile = await db.get_user(user_id) # Actual call
        profile = {"name": "Test User", "id": user_id} # Mock
        return {**ctx, "user_profile": profile}
    ```
[⬆️](#quick-navigation)

#### Guard Function
    ```python
    async def ensure_authenticated(ctx: dict) -> dict:
        if not ctx.get("user_is_authenticated"):
            raise PermissionError("User not authenticated")
        return ctx # No change if guard passes
    ```
[⬆️](#quick-navigation)

### 3. Basic Chain Composition

#### Linear Chain
    ```python
    from modulink import ModuLink

    async def step_one(ctx): return {**ctx, "step1_done": True}
    async def step_two(ctx): return {**ctx, "step2_done": True}

    my_chain = ModuLink().link(step_one).link(step_two)
    # result = await my_chain.execute({"initial_data": "value"})
    ```
[⬆️](#quick-navigation)

### 4. Context Flow Management

#### Context Accumulation
    ```python
    # Chain: fn1 -> fn2
    # fn1 adds "data1", fn2 adds "data2"
    # Final context: {"initial", "data1", "data2"}
    async def add_data_one(ctx): return {**ctx, "data_from_one": 1}
    async def add_data_two(ctx): return {**ctx, "data_from_two": 2}
    chain = ModuLink().link(add_data_one).link(add_data_two)
    # await chain.execute({}) -> {"data_from_one":1, "data_from_two":2}
    ```
[⬆️](#quick-navigation)

#### Context Cleaning
    ```python
    async def remove_sensitive_data(ctx: dict) -> dict:
        cleaned_ctx = ctx.copy()
        cleaned_ctx.pop("password_hash", None)
        cleaned_ctx.pop("session_token", None)
        return {**cleaned_ctx, "sensitive_data_removed": True}
    ```
[⬆️](#quick-navigation)

### 5. Simple Error Handling

#### Try-Catch in Functions
    ```python
    async def call_external_api(ctx: dict) -> dict:
        try:
            # response = await http_client.get(ctx["url"])
            # return {**ctx, "api_response": response.json()}
            raise ConnectionError("Simulated API failure") # Simulate
        except ConnectionError as e:
            return {**ctx, "api_error": str(e), "api_call_failed": True}
    ```
[⬆️](#quick-navigation)


---

## 🧑 Intermediate Level Patterns

### 1. Advanced Orchestration

#### Parallel Execution (Conceptual)
    ```python
    # Using ThreadPoolExecutor for I/O-bound tasks
    async def parallel_fetch(ctx: dict) -> dict:
        # with ThreadPoolExecutor() as executor:
        #    future1 = executor.submit(fetch_service_a, ctx)
        #    future2 = executor.submit(fetch_service_b, ctx)
        #    ctx["service_a_data"] = future1.result()
        #    ctx["service_b_data"] = future2.result()
        # return ctx
        # Simplified for cheatsheet:
        data_a = {"data": "service_a_result"} # await fetch_a(ctx)
        data_b = {"data": "service_b_result"} # await fetch_b(ctx)
        return {**ctx, "service_a_data": data_a, "service_b_data": data_b}
    ```
[⬆️](#quick-navigation)

### 2. Middleware & Cross-Cutting Concerns

#### Logging Middleware (Decorator Style)
    ```python
    from functools import wraps

    def log_execution(func):
        @wraps(func)
        async def wrapper(ctx: dict) -> dict:
            print(f"Entering {func.__name__}...")
            result_ctx = await func(ctx)
            print(f"Exiting {func.__name__}...")
            return result_ctx
        return wrapper

    @log_execution
    async def my_logged_function(ctx: dict) -> dict:
        return {**ctx, "logged_function_executed": True}
    ```
[⬆️](#quick-navigation)

#### Circuit Breaker (Conceptual)
    ```python
    # class CircuitBreaker:
    #     def call(self, func, *args):
    #         if self.is_open(): raise ServiceUnavailableError()
    #         try: result = func(*args); self.success(); return result
    #         except: self.failure(); raise

    async def protected_service_call(ctx: dict) -> dict:
        # cb = ctx.get_circuit_breaker("my_service")
        # return await cb.call(actual_api_call, ctx)
        return {**ctx, "service_data": "mocked_data_circuit_closed"}
    ```
[⬆️](#quick-navigation)

### 3. State Management

#### Context State Machine (Conceptual Update)
    ```python
    # FSM: PENDING -> PROCESSING -> COMPLETED
    async def advance_order_state(ctx: dict) -> dict:
        current_state = ctx.get("order_state")
        new_state = current_state # Default
        if current_state == "PENDING": new_state = "PROCESSING"
        elif current_state == "PROCESSING": new_state = "COMPLETED"
        return {**ctx, "order_state": new_state}
    ```
[⬆️](#quick-navigation)

### 4. Conditional Execution

#### Rule-Based Execution (Simple)
    ```python
    async def apply_discount_rule(ctx: dict) -> dict:
        if ctx.get("user_is_premium") and ctx.get("order_total", 0) > 100:
            discount = ctx["order_total"] * 0.10
            return {**ctx, "discount_applied": discount}
        return ctx
    ```
[⬆️](#quick-navigation)

#### Feature Flag (Simple)
    ```python
    async def new_feature_module(ctx: dict) -> dict:
        # feature_flags = ctx.get_feature_flags()
        # if feature_flags.is_enabled("new_checkout_flow", ctx.get("user_id")):
        if ctx.get("enable_new_feature_flag"):
            return {**ctx, "new_feature_active": True, "data": "from_new_feature"}
        return {**ctx, "new_feature_active": False, "data": "from_old_path"}
    ```
[⬆️](#quick-navigation)


---

## 🧙 Advanced Level Patterns

### 1. Enterprise Architecture

#### Microservice Chain Orchestration (Conceptual Call)
    ```python
    async def call_payment_service(ctx: dict) -> dict:
        # payload = {"order_id": ctx["order_id"], "amount": ctx["total"]}
        # payment_response = await http.post(ctx["payment_service_url"], json=payload)
        # return {**ctx, "payment_status": payment_response.json()["status"]}
        return {**ctx, "payment_status": "SUCCESS_MOCKED"}
    ```
[⬆️](#quick-navigation)

#### Event-Driven Chain (Conceptual Publish)
    ```python
    async def publish_order_confirmed_event(ctx: dict) -> dict:
        event_payload = {"order_id": ctx["order_id"], "user_id": ctx["user_id"]}
        # await event_bus.publish("OrderConfirmed", event_payload)
        return {**ctx, "event_published": "OrderConfirmed"}
    ```
[⬆️](#quick-navigation)

### 2. Performance Optimization

#### Parallel Execution with Resource Pools (Conceptual)
    ```python
    # from concurrent.futures import ThreadPoolExecutor
    # pool = ThreadPoolExecutor(max_workers=5)
    async def process_item_in_parallel(item_data: dict) -> dict:
        # result = await heavy_computation_async(item_data)
        # return {"processed_item": item_data["id"], "status": "done"}
        return {"processed_item": item_data.get("id"), "status": "done_mocked"}

    async def batch_parallel_processing(ctx: dict) -> dict:
        items = ctx.get("items_to_process", [])
        # tasks = [pool.submit(process_item_in_parallel, item) for item in items]
        # results = [task.result() for task in tasks]
        results = [await process_item_in_parallel(item) for item in items] # Simplified
        return {**ctx, "batch_results": results}
    ```
[⬆️](#quick-navigation)

#### Memory-Efficient Processing (Streaming/Generators)
    ```python
    async def process_large_file_stream(ctx: dict) -> dict:
        # async def line_processor(line):
        #     # process line
        #     return processed_line
        # output_lines = (await line_processor(line) async for line in ctx["input_file_stream"])
        # ctx["processed_lines_generator"] = output_lines
        # return ctx
        def generate_lines():
            for i in range(ctx.get("line_count", 3)):
                yield f"processed_line_{i}"
        return {**ctx, "processed_lines_generator": generate_lines()}
    ```
[⬆️](#quick-navigation)

### 3. Scalability Patterns

#### Horizontal Scaling (Conceptual - Infrastructure Level)
    ```
    # This is typically managed by orchestrators like Kubernetes.
    # ModuLink app is containerized and deployed with multiple replicas.
    # A load balancer (e.g., Nginx, ELB) distributes requests.
    # --- Kubernetes Deployment Snippet ---
    # apiVersion: apps/v1
    # kind: Deployment
    # metadata:
    #   name: modulink-worker
    # spec:
    #   replicas: 5 # Scale this number
    #   template:
    #     spec:
    #       containers:
    #       - name: modulink-app
    #         image: your-modulink-app-image
    ```
[⬆️](#quick-navigation)

### 4. Production Deployment Strategies

#### Containerized Deployment (Dockerfile Snippet)
    ```dockerfile
    # FROM python:3.11-slim
    # WORKDIR /app
    # COPY requirements.txt .
    # RUN pip install -r requirements.txt
    # COPY . .
    # CMD ["python", "app.py"]
    ```
    *(This is a very basic Dockerfile example)*
[⬆️](#quick-navigation)

#### Blue-Green / Canary (Conceptual - Traffic Shifting)
    ```
    # Managed by load balancer or service mesh (e.g., Istio, Linkerd)
    # config snippet for a service mesh virtual service:
    # http:
    # - route:
    #   - destination:
    #       host: my-service
    #       subset: v1 # Blue or current stable
    #     weight: 90
    #   - destination:
    #       host: my-service
    #       subset: v2 # Green or canary
    #     weight: 10
    ```
[⬆️](#quick-navigation)

### 5. Security Patterns

#### Authentication Middleware (Conceptual)
    ```python
    async def jwt_auth_middleware(ctx: dict) -> dict:
        token = ctx.get("headers", {}).get("Authorization", "").replace("Bearer ", "")
        # try:
        #     decoded_token = jwt.decode(token, "secret", algorithms=["HS256"])
        #     return {**ctx, "user_id": decoded_token["user_id"], "authenticated": True}
        # except: # Invalid token
        #     raise AuthenticationError("Invalid token")
        if token == "valid_token": # Mock
            return {**ctx, "user_id": "user123", "authenticated": True}
        raise Exception("AuthenticationError: Invalid token") # Mock
    ```
[⬆️](#quick-navigation)

#### Input Validation (Pydantic Example)
    ```python
    # from pydantic import BaseModel, ValidationError
    # class UserInput(BaseModel):
    #     username: str
    #     age: int
    async def validate_user_input_pydantic(ctx: dict) -> dict:
        # try:
        #     UserInput(**ctx.get("user_payload", {}))
        #     return {**ctx, "input_valid": True}
        # except ValidationError as e:
        #     return {**ctx, "input_valid": False, "validation_errors": e.errors()}
        payload = ctx.get("user_payload", {})
        if "username" in payload and isinstance(payload.get("age"), int):
            return {**ctx, "input_valid": True}
        return {**ctx, "input_valid": False, "validation_errors": "mocked_errors"}
    ```
[⬆️](#quick-navigation)

#### Secure Secret Management (Conceptual Access)
    ```python
    async def get_api_key_from_vault(ctx: dict) -> dict:
        # import os
        # api_key = os.environ.get("THIRD_PARTY_API_KEY")
        # or use a vault client: client.read("secrets/my_app/api_key")
        api_key = "mocked_api_key_from_secret_store"
        return {**ctx, "api_key_loaded": True, "_api_key": api_key}
    ```
[⬆️](#quick-navigation)

### 6. Monitoring and Observability

#### Metrics Collection (Prometheus Client Snippet)
    ```python
    # from prometheus_client import Counter
    # REQUEST_COUNT = Counter("modulink_requests_total", "Total requests processed", ["chain_name"])
    async def increment_request_counter(ctx: dict) -> dict:
        chain_name = ctx.get("chain_name", "unknown_chain")
        # REQUEST_COUNT.labels(chain_name=chain_name).inc()
        print(f"Metric: REQUEST_COUNT for {chain_name} incremented.")
        return {**ctx, "metric_incremented": True}
    ```
[⬆️](#quick-navigation)

#### Distributed Tracing (Conceptual Span)
    ```python
    # from opentelemetry import trace
    # tracer = trace.get_tracer(__name__)
    async def traced_module(ctx: dict) -> dict:
        # with tracer.start_as_current_span("my_module_execution") as span:
        #     span.set_attribute("order_id", ctx.get("order_id"))
        #     # ... module logic ...
        #     return {**ctx, "module_executed_trace_id": span.get_span_context().trace_id}
        print(f"Trace: Starting span for my_module_execution with order_id {ctx.get('order_id')}")
        return {**ctx, "module_executed_trace_id": "mock_trace_id"}
    ```
[⬆️](#quick-navigation)

#### Structured Logging
    ```python
    import json
    async def log_structured_event(ctx: dict) -> dict:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": "Order processed",
            "order_id": ctx.get("order_id"),
            "user_id": ctx.get("user_id"),
            "chain_name": ctx.get("chain_name")
        }
        # print(json.dumps(log_entry)) # Actual logging
        return {**ctx, "structured_log_created": True, "_log_entry_preview": log_entry["message"]}
    ```
[⬆️](#quick-navigation)
