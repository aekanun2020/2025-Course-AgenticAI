# Contributing to PyRAGDoc

Thank you for considering contributing to PyRAGDoc! This document outlines the process for contributing to the project.

## Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pyragdoc.git
cd pyragdoc
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Code Style

We follow PEP 8 style guidelines for Python code. Please ensure your code adheres to these standards.

Use the following tools to check and format your code:
- `black` for code formatting
- `isort` for import sorting
- `flake8` for linting

## Testing

Write tests for new features and bug fixes. Run tests using pytest:

```bash
pytest
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write or update tests
5. Run tests and make sure they pass
6. Submit a pull request

## Project Structure

- `pyragdoc/` - Main package
  - `server/` - Server components (MCP, HTTP API)
  - `core/` - Core functionality (embedding, storage, processors)
  - `models/` - Data models
  - `utils/` - Utility functions
- `tests/` - Test suite
- `examples/` - Example code

## Adding a New Processor

To add a new document processor:

1. Create a new file in `pyragdoc/core/processors/`
2. Implement a processor class that inherits from `DocumentProcessor`
3. Register the processor in `pyragdoc/core/processors/__init__.py`

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
