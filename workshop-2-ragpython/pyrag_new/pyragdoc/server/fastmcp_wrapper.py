"""FastMCP Wrapper for PyRAGDoc."""

import asyncio
import logging
from typing import Dict, Any

from ..config import load_config
from ..utils.logging import setup_logging, get_logger
from .mcp import run_mcp_server


def run_fastmcp_server(log_file=None, debug=False):
    """Run the FastMCP server.
    
    Args:
        log_file: Path to log file
        debug: Enable debug logging
    """
    # Set up logging
    log_level = logging.DEBUG if debug else logging.INFO
    setup_logging(log_file, log_level)
    logger = get_logger("fastmcp_wrapper")
    
    # Load configuration
    config = load_config()
    
    # Run server
    logger.info("Starting PyRAGDoc with FastMCP")
    
    try:
        asyncio.run(run_mcp_server(config))
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_fastmcp_server()
