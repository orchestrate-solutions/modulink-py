# Middleware, Chain Hooks, and Link-Specific Middleware: Design Discussion

## Current Patterns

- **Middleware**: Cross-cutting, reusable logic (logging, timing, etc.) that wraps every link in a chain. Middleware is now link-aware (readonly): when running before/after, it receives a reference to the link it is operating on, allowing introspection and targeted behavior.
- **Links**: The business logic steps in a chain.
- **Chain-level hooks**: (Proposed) Functions that run before/after the whole chain, or before/after every link.
- **Insert links**: For per-step logic (e.g., logging after a specific link).

## Middleware Context (mwctx) Pattern

- **Immutability:** Middleware is not allowed to modify the main `ctx` (context) passed through the chain and links.
- **mwctx:** Middleware can write to a separate `mwctx`, which is a `Context` object shared among all middleware executing in the same chain run.
- **Purpose:** This allows middleware to communicate or accumulate data (e.g., timing, logging, metrics) without affecting the main business logic context.
- **Caveat:** While this enables advanced middleware patterns, it introduces shared mutable state among middleware, which can lead to coupling or unexpected interactions. Use with caution and document intended usage clearly.

**Best Practice:**  
Prefer stateless middleware when possible. Use `mwctx` only for well-defined, cross-cutting concerns (e.g., timing, tracing) and avoid relying on it for business logic or critical workflow decisions.

## Middleware Queue Position & Metrics

- **Order Awareness:** Middleware should be aware of its position in the execution queue (e.g., chain-middleware-before, link-middleware-before, link, link-middleware-after, chain-middleware-after). This enables advanced introspection and debugging.
- **Execution Order:** Middleware is executed in the order it is added. The order is:
  1. Chain-level before middleware
  2. Link-level before middleware
  3. The link itself
  4. Link-level after middleware
  5. Chain-level after middleware
- **Metrics Association:** There should be a way to reference metrics and timing specifically around the `<link>` itself, not just the whole chain or middleware. This ensures accurate, non-overlapping measurements (e.g., timing, logging) for each link, regardless of other middleware or waits.
- **Observation, Not Interruption:** Middleware should observe and record everything about the execution process, but not interrupt or alter the flow of code execution.

## Making Middleware Order & Metrics Possible

### 1. Middleware Position Awareness
- **API:** When middleware is attached (to chain or link), assign it a `position` attribute (e.g., 'chain-before', 'link-before', 'link-after', 'chain-after') and an `index` (its order in the queue).
- **Implementation:**
    - When building the execution plan, enumerate all middleware and assign their position and index.
    - Pass these as readonly attributes to the middleware instance before execution.
- **Usage:** Middleware can inspect its `position` and `index` to know exactly where it is in the execution order.

### 2. Accurate Link-Specific Metrics
- **API:** Provide a `metrics` dict or context for each link execution, accessible to all middleware for that link.
- **Implementation:**
    - When running a link, create a fresh `metrics` dict (or Context) for that link.
    - Pass this `metrics` object to all before/after middleware for that link, as well as to the link itself if needed.
    - Middleware can record timing, logging, or other data in `metrics` without interfering with other links or the main context.
- **Usage:**
    - Timing middleware records start/end in `metrics`.
    - Logging middleware can append logs to `metrics['logs']`.
    - After execution, the chain can aggregate or export all per-link metrics.

### 3. Non-Interruptive Observation
- **API:** Middleware must not raise exceptions or alter control flow; it only observes and records.
- **Implementation:**
    - Catch and log any exceptions in middleware, but do not let them affect link or chain execution.
    - Optionally, provide a `safe=True` flag to enforce this.

### 4. Example Execution Plan

```python
for link in chain.links:
    for mw in chain.before_middleware:
        mw.position = 'chain-before'; mw.index = ...
        await mw.before(link, ctx, mwctx, metrics)
    for mw in link.before_middleware:
        mw.position = 'link-before'; mw.index = ...
        await mw.before(link, ctx, mwctx, metrics)
    result = await link(ctx)
    for mw in link.after_middleware:
        mw.position = 'link-after'; mw.index = ...
        await mw.after(link, ctx, result, mwctx, metrics)
    for mw in chain.after_middleware:
        mw.position = 'chain-after'; mw.index = ...
        await mw.after(link, ctx, result, mwctx, metrics)
```

### 5. API/Doc Implications
- Document the order and position attributes for middleware.
- Show how to use per-link `metrics` for accurate, isolated measurement.
- Emphasize that middleware is for observation, not control flow.

---

## TODO: Advanced Shadow State, Timestamping, and Extensibility

- By default, capture variable-level state changes and execution timeline, including timestamps (nanosecond precision, negligible overhead for most use cases).
- Allow users to opt out of timestamping for maximum performance, or extend the capture system to include additional state (external resources, memory, etc.) as needed.
- Rationale: This provides more than a black-box log—users can inspect, replay, and offload observability to the shadow self, minimizing impact on the main pipeline.
- For now, keep middleware and timeline tracking simple and integrated with the chain. In the future, consider abstracting the shadow state and offering advanced capture for users with specialized needs.
- Over-optimization is unnecessary at this stage; document the plan for extensibility and revisit if/when performance or feature demands arise.

### Shadow State & Execution Timeline ("Time Travel" Debugging)

- **Shadow State:** Maintain a complete, immutable record ("shadow state") of every context, link, middleware, and metric at each step of the chain execution.
- **Timeline:** Build a timeline/log of all events (middleware before/after, link execution, context changes, metrics) in the exact order they occurred.
- **Purpose:** This enables after-the-fact inspection, replay, or even "time travel" debugging—developers can see exactly what happened, when, and why, with all intermediate states preserved.
- **Implementation:**
    - At each step (before/after middleware, link execution), snapshot the current context, mwctx, metrics, and any relevant state.
    - Store these snapshots in a timeline list or tree, with timestamps and event types (e.g., 'before_middleware', 'link', 'after_middleware').
    - Optionally, allow replaying the timeline or extracting any intermediate state for analysis.
- **API:**
    - Expose the timeline/shadow state as a property of the chain run (e.g., `chain.last_run.timeline`).
    - Provide utilities to query, filter, or replay the timeline.
- **Best Practice:**
    - Use shadow state for debugging, auditing, and advanced analytics.
    - Avoid relying on it for business logic or control flow.

#### Example Timeline Entry
```python
{
    'event': 'before_middleware',
    'middleware': 'Logging',
    'link': 'step1',
    'ctx': <Context snapshot>,
    'mwctx': <mwctx snapshot>,
    'metrics': <metrics snapshot>,
    'timestamp': 1729632000.123,
    'position': 'chain-before',
    'index': 0
}
```

### True Shadow Self: Total State Preservation

- **Goal:** Go beyond debugging—create a "shadow self" of the entire chain execution, preserving every memory operation, every mutation, every value, and every event, as if the process were a living organism.
- **Analogy:** Like cell division, where the daughter cell contains a complete copy of the parent, the shadow state is a perfect, immutable record of the entire execution, not just a log or trace.
- **Implementation Ideas:**
    - **Deep Copy on Every Operation:** At every step (middleware, link, context mutation, even inside user code), perform a deep copy of all relevant state (context, mwctx, metrics, local variables, etc.).
    - **Instrumented Context/Objects:** Use custom Context and data structures that record every get/set/del operation, including timestamps and call stacks.
    - **Bytecode/AST Instrumentation:** For ultimate fidelity, instrument user code (links, middleware) at the bytecode or AST level to record every memory operation, variable assignment, and function call.
    - **Event Timeline:** Store all these snapshots and events in a timeline, with references to parent/child states (like a cell lineage tree).
    - **Replay/Branching:** Allow replaying or forking execution from any point in the timeline, creating "daughter" executions with their own shadow states.
- **Challenges:**
    - **Performance:** Deep copying and instrumenting every operation is expensive; may require C extensions or JIT techniques for efficiency.
    - **Storage:** The shadow state can grow very large; may need compression, pruning, or selective recording.
    - **Complexity:** Requires careful design to avoid interfering with normal execution or introducing side effects.
- **API/Usage:**
    - Expose the shadow self as a property of the chain run (e.g., `chain.last_run.shadow_self`).
    - Provide tools to query, replay, or branch from any point in the shadow timeline.
    - Optionally, allow users to opt-in to full shadow state recording for critical runs.
- **Best Practice:**
    - Use true shadow self for scientific, forensic, or highly regulated applications where total reproducibility is required.
    - For most use cases, a lighter timeline/log is sufficient.

#### Example Shadow State Entry
```python
{
    'event': 'setitem',
    'target': 'ctx',
    'key': 'user',
    'value': 'alice',
    'timestamp': 1729632000.123,
    'call_stack': [...],
    'parent_state': <ref>,
    'resulting_state': <deepcopy of ctx>
}
```
