"""Command line interface for PyRAGDoc."""

import sys
import logging
import argparse
from typing import Dict, Any

from .config import load_config
from .utils.logging import setup_logging


def main():
    """Main entry point for the CLI."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PyRAGDoc Server")
    parser.add_argument(
        "--mode", 
        choices=["mcp", "http"], 
        default="mcp",
        help="Server mode (mcp or http)"
    )
    parser.add_argument(
        "--log-file", 
        help="Path to log file"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(args.log_file, log_level)
    
    # Load configuration
    config = load_config()
    
    # Run appropriate server
    try:
        if args.mode == "mcp":
            logging.info("Starting MCP server")
            from .server.mcp import run_mcp_server
            import asyncio
            asyncio.run(run_mcp_server(config))
        else:
            logging.info("Starting HTTP server")
            from .server.api import run_http_server
            run_http_server(config)
    except KeyboardInterrupt:
        logging.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Error running server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
