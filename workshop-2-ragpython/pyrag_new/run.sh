#!/bin/bash
# Run RAGDocs FastMCP Server

# Change to script directory
cd "$(dirname "$0")"

# Run the server
python -m ragdocs.server "$@"
