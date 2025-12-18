# API Reference & Generation Guide

This document provides an overview of the Null-Lang standard library APIs and instructions for generating the full API documentation from source.

## API Overview

### Core Modules
- **`std::io`**: Input/Output operations.
- **`std::collections`**: Lists, Maps, Sets.
- **`std::async`**: Async/Await primitives.

### Advanced Modules
- **`ml`**: Machine Learning interface (PyTorch wrapper).
- **`nlp`**: Natural Language Processing utilities.
- **`kg`**: Knowledge Graph operations.
- **`quantum`**: Quantum circuit simulation.
- **`opt`**: Mathematical optimization solvers.

## Generating API Documentation

The authoritative API reference is generated from docstrings in the `src/null_system` source code.

### Prerequisites
- Python 3.11+
- `pdoc` or `sphinx` (we recommend `pdoc` for simplicity)

### Instructions

1. **Install generation tools**:
   ```bash
   pip install pdoc
   ```

2. **Generate HTML documentation**:
   ```bash
   # From project root
   pdoc --html --output-dir docs/api src/null_system
   ```

3. **View Documentation**:
   Open `docs/api/null_system/index.html` in your browser.

### Keeping Docs Synchronized

It is recommended to run the documentation generation as part of the CI/CD pipeline.

**Example GitHub Action Step**:
```yaml
- name: Generate API Docs
  run: |
    pip install pdoc
    pdoc --html --output-dir public/docs src/null_system
```

## Module Highlights

### ML Module (`src/null_system/ml/`)
Exposes tensor operations and model inference.
- `Tensor`: N-dimensional array.
- `Module`: Base class for neural networks.

### NLP Module (`src/null_system/lib/nlp.py`)
Provides tokenization and embedding utilities.
- `tokenize(text: str) -> List[str]`
- `embed(text: str) -> Tensor`
