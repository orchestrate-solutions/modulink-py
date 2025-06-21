# ModuLink VSCode Extension - TODO / Roadmap

## Goals

- Provide dynamic, instance-level docstring hovers for ModuLink objects in Python code.
- Support both human and AI developer workflows.

## Implementation Ideas

- Use VSCode's Python extension API to intercept hover events.
- On hover, identify if the variable is a ModuLink object (Chain, Listener, etc.).
- If so, attempt to fetch live documentation:
  - Communicate with a running Python process (e.g., via a socket or debug adapter) to call `inspect()` or access `__doc__`.
  - Fallback to static docstring if live info is not available.
- Display the fetched documentation in the hover tooltip.

## Stretch Goals

- Allow configuration for which objects/classes to support.
- Add commands to manually trigger docstring refresh.
- Integrate with test runner to show doc updates after code changes.

## Next Steps

- Research VSCode extension API for Python hover providers.
- Prototype a simple extension that customizes hover text.
- Explore communication between VSCode and a running Python process.
- Document findings and update this roadmap.
