# ModuLink Documentation CLI & API

## Motivation

To make ModuLink's documentation easily accessible to both humans and LMMs, we will provide:
- A CLI tool (`modulink-doc`) for querying and displaying documentation, usage examples, and API references.
- A Python API (`modulink.docs.get_doc(topic)`) for programmatic access to documentation.

This ensures that anyone (or any agent) using the library can quickly find relevant information, even from the terminal or code.

---

## CLI Usage

### Installation

The CLI will be installed alongside the library.

### Example Commands

```sh
modulink-doc --help
modulink-doc chain
modulink-doc middleware Logging
modulink-doc example usage
```

- `modulink-doc chain` — Shows documentation and usage for the Chain class.
- `modulink-doc middleware Logging` — Shows docs for the Logging middleware.
- `modulink-doc example usage` — Shows quick start and advanced examples.

### Output

The CLI will print Markdown-formatted documentation to the terminal, suitable for both humans and LMMs.

---

## Python API

```python
from modulink.docs import get_doc

print(get_doc("chain"))
print(get_doc("middleware.Logging"))
print(get_doc("example usage"))
```

- Returns documentation as a string for the given topic.
- Can be used in notebooks, scripts, or by LMMs.

---

## Implementation Details

- Documentation will be sourced from docstrings, README sections, and example files.
- The CLI and API will share a common backend for doc retrieval.
- Topics will be mapped to doc sources (e.g., class docstring, README anchor).
- Extensible: new topics and sources can be added as the library grows.

---

## LMM & Developer Experience

- LMMs can use the CLI or API to fetch up-to-date docs for any concept.
- Human users can quickly reference docs without leaving the terminal or editor.
- Encourages self-documenting code and discoverability.

---

## Contributing

- To add or update documentation, edit docstrings, README, or add new example files.
- To extend the CLI/API, update the topic mapping and retrieval logic.

---

## Status

This is a planned feature. See `TODO.md` for implementation progress.
