# PyRAGDoc - FastMCP Version

This directory contains a reimplementation of the PyRAGDoc server using FastMCP, a simplified API for MCP servers that leverages Python type hints and docstrings to automatically generate tool definitions.

## Advantages of FastMCP

- **Simplified Code**: Significantly reduces boilerplate code with decorator-based API
- **Type-Safety**: Uses Python type hints for parameter validation
- **Auto-Documentation**: Tool documentation is generated from docstrings automatically
- **Easy Maintenance**: Simpler code structure makes maintenance easier
- **Consistent Error Handling**: Standardized error handling through return values

## Running the Server

You can run the FastMCP server using:

```bash
# Give execute permissions (first time only)
chmod +x run_fastmcp.sh

# Run the server
./run_fastmcp.sh
```

Or directly with Python:

```bash
python run_fastmcp.py
```

### Command Line Options

The server supports the same command line options as the original version:

- `--mode`: Server mode (`mcp` or `http`, default is `mcp`)
- `--log-file`: Path to log file for logging
- `--debug`: Enable debug logging

Example:
```bash
./run_fastmcp.sh --debug --log-file=/tmp/pyragdoc.log
```

## Implementation Details

The primary changes from the original version:

1. Replaced `Server` with `FastMCP` instance
2. Removed handler functions like `handle_list_tools` and `handle_call_tool`
3. Added decorators `@mcp.tool()` for each tool function
4. Simplified the return values to strings instead of `TextContent` objects
5. Used Python type hints and docstrings for parameter definitions

## Tools Available

The FastMCP version provides the same tools as the original:

- `add_documentation`: Add documentation from a URL
- `search_documentation`: Search through stored documentation
- `list_sources`: List all documentation sources
- `add_directory`: Add files from a directory to the database
