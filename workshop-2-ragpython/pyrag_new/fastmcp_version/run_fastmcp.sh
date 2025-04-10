#!/bin/bash
# Script to run FastMCP version of PyRAGDoc server

# Change to the script directory
cd "$(dirname "$0")"

# Add executable permission to run_fastmcp.py if needed
chmod +x run_fastmcp.py

# Run the FastMCP server
python run_fastmcp.py "$@"
