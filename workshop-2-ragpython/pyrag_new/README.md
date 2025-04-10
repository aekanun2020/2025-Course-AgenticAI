# RAGDocs - FastMCP Server for Documentation Retrieval

A lightweight, FastMCP-based server for Retrieval Augmented Generation with documentation.

## Features

- Add documentation from URLs
- Process local files and directories
- Search through indexed documentation
- List available sources
- Built with FastMCP for clean, type-safe code

## Quick Install

### Using pip (default)

```bash
# Give execute permission to installer
chmod +x install.sh

# Run installer
./install.sh
```

### Using Conda

```bash
# Give execute permission to installer
chmod +x install_conda.sh

# Run installer
./install_conda.sh
```

See [INSTALL.md](INSTALL.md) for pip-based installation or [README_CONDA.md](README_CONDA.md) for Conda-based installation.

## Environment Variables

- `QDRANT_URL`: URL for Qdrant server (default: http://localhost:6333)
- `QDRANT_COLLECTION`: Collection name in Qdrant (default: ragdocs)
- `EMBEDDING_PROVIDER`: Provider for embeddings (ollama or openai)
- `OLLAMA_URL`: URL for Ollama API (default: http://localhost:11434)
- `EMBEDDING_MODEL`: Model to use for embeddings (default: nomic-embed-text)
- `OPENAI_API_KEY`: API key for OpenAI (if using OpenAI provider)

## Usage

### Running the Server

```bash
# Run with pip installation
python -m ragdocs.server

# Run with Conda installation
./run_conda.sh

# Enable debug logging
python -m ragdocs.server --debug
```

### Claude Desktop Configuration

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ragdocs": {
      "command": "python",
      "args": [
        "-m",
        "ragdocs.server"
      ],
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_COLLECTION": "documentation",
        "EMBEDDING_PROVIDER": "ollama",
        "OLLAMA_URL": "http://localhost:11434"
      }
    }
  }
}
```

For Conda, replace `"command": "python"` with the full path to your Conda environment's Python.

## Requirements

- Python 3.10+
- [Qdrant](https://qdrant.tech/) vector database (local or remote)
- [Ollama](https://ollama.ai/) for local embeddings or OpenAI API key

## Tools

RAGDocs provides the following tools:

1. **add_documentation** - Add documentation from a URL
2. **search_documentation** - Search through stored documentation
3. **list_sources** - List all documentation sources
4. **add_directory** - Add files from a directory to the database

## License

MIT
