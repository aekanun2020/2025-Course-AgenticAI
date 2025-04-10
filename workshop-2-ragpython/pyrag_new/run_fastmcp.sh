#!/bin/bash
# Run PyRAGDoc with FastMCP

# Change to the directory of this script
cd "$(dirname "$0")"

# Run the server with FastMCP
python -c "from pyragdoc.server.fastmcp_wrapper import run_fastmcp_server; run_fastmcp_server()" "$@"
