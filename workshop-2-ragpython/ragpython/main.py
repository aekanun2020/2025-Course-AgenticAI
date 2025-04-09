#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Make this file executable with: chmod +x main.py
"""
RAG Docs MCP Server
This server provides a Model Context Protocol (MCP) server for RAG functionality, 
converted from Node.js to Python.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from server import RagDocsServer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if exists
load_dotenv()

async def main():
    """Main function to start the server."""
    # Display startup information
    logger.info("Starting RAG Docs MCP Server")
    logger.info("Environment Configuration:")
    logger.info(f"OLLAMA_URL: {os.environ.get('OLLAMA_URL', 'http://localhost:11434')}")
    logger.info(f"QDRANT_URL: {os.environ.get('QDRANT_URL', 'http://127.0.0.1:6333')}")
    logger.info(f"EMBEDDING_PROVIDER: {os.environ.get('EMBEDDING_PROVIDER', 'ollama')}")
    logger.info(f"EMBEDDING_MODEL: {os.environ.get('EMBEDDING_MODEL', 'Not specified')}")
    
    # Create and run the server
    server = RagDocsServer()
    await server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
