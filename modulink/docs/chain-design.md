# Chain Design and Visualization

## Motivation

As chains grow in complexity—with multiple links, conditional connectors, and both chain-level and link-level middleware—the structure can become difficult to trace, debug, and visualize. This document outlines design patterns and strategies for making chain structures easily inspectable and visualizable.

## Goals
- Make the structure of any chain (links, connections, middleware) easy to inspect programmatically and visually.
- Enable tools or utilities to generate clear, human-readable representations (e.g., trees, graphs, diagrams) of chain logic.
- Support debugging, documentation, and onboarding by making complex chains transparent.

## Design Patterns

### 1. Introspectable Chain Structure
- Each `Chain` instance should provide a method (e.g., `.inspect()`) that returns a complete, structured representation of:
  - All links (in order)
  - All connections (branching, error handling, etc.)
  - All middleware (chain-level and link-level, with positions)

### 2. Connection Representation
- Connections should be stored as explicit objects or dicts, including:
  - Source link
  - Target link
  - Condition (callable or description)

### 3. Middleware Representation
- Chain-level middleware: List of middleware attached to the chain.
- Link-level middleware: Each link can have `_before_middleware` and `_after_middleware` lists.
- Middleware objects should expose their type, position, and index for clarity.

### 4. Visualization Utilities
- Provide a utility function (e.g., `chain.visualize()`) that outputs a diagram (text tree, graphviz, etc.) of the chain structure.
- Show links as nodes, connections as edges, and middleware as annotations.
- Optionally, export to formats like DOT/Graphviz for advanced visualization.

### 5. Example: Inspect Output
```python
{
  'links': ['step1', 'step2', 'step3'],
  'connections': [
    {'source': 'step1', 'target': 'step2', 'condition': 'on_success'},
    {'source': 'step1', 'target': 'step3', 'condition': 'on_error'}
  ],
  'middleware': [
    {'type': 'Logging', 'position': 'chain-before', 'index': 0},
    {'type': 'Timing', 'position': 'chain-after', 'index': 1}
  ],
  'link_middleware': {
    'step2': {
      'before': [{'type': 'Custom', 'index': 0}],
      'after': []
    }
  }
}
```

## Visualization Approach

To make ModuLink Next chains easily inspectable and visualizable, we will support both CLI and VS Code extension visualization using industry-standard tools:

### Python/CLI: Graphviz

- Use the `graphviz` Python package to generate `.dot`, `.svg`, or `.png` files representing the structure of a chain.
- Add a CLI command:
  ```sh
  modulink visualize --format svg --output chain.svg
  ```
- Optionally, support `--format mermaid` to output a Mermaid diagram for VS Code.

### VS Code Extension: Mermaid

- The VS Code extension will accept Mermaid diagram text (from file or API).
- Render the diagram in a webview or markdown preview using Mermaid.js (supported natively in VS Code markdown).
- Example workflow:
  ```sh
  modulink visualize --format mermaid --output chain.mmd
  ```
  Then open/view in the extension.

## Implementation Steps

- [ ] Add `to_graphviz()` and `to_mermaid()` methods to the `Chain` class or as utilities.
- [ ] Add a CLI command: `modulink visualize --format svg|mermaid|dot`.
- [ ] Update documentation and cheatsheet with visualization usage.
- [ ] In the VS Code extension, add support for loading and rendering Mermaid diagrams.

## Example Usage

```sh
modulink visualize --format svg --output chain.svg
modulink visualize --format mermaid --output chain.mmd
```

Open the `.svg` in any viewer, or the `.mmd` in the VS Code extension for interactive visualization.

---

This approach ensures ModuLink Next chains are always easy to inspect, debug, and share—both in the terminal and in your editor.

## Future Directions
- Add visualization hooks to the chain API.
- Support exporting chain structure to external tools (e.g., Graphviz, Mermaid).
- Enable interactive exploration of chain logic in notebooks or web UIs.

---

Add further ideas, requirements, or sketches below!
