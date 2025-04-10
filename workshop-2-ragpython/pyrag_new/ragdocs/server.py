#!/usr/bin/env python
"""
RAGDocs - FastMCP Server for Documentation Retrieval
---------------------------------------------------
A simple FastMCP implementation for RAG with documentation.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional

# Import FastMCP
from mcp.server.fastmcp import FastMCP
import mcp.types as types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ragdocs")

# Initialize FastMCP instance
mcp = FastMCP("ragdocs-server")

# Global variables for services
embedding_service = None
storage_service = None

def setup_services():
    """Initialize embedding and storage services."""
    global embedding_service, storage_service
    
    # Get environment variables
    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    qdrant_collection = os.environ.get("QDRANT_COLLECTION", "ragdocs")
    embedding_provider = os.environ.get("EMBEDDING_PROVIDER", "ollama")
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    embedding_model = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
    
    logger.info(f"Setting up services with: QDRANT_URL={qdrant_url}, EMBEDDING_PROVIDER={embedding_provider}")
    
    # Import and create services
    try:
        # Create embedding service
        if embedding_provider.lower() == "ollama":
            from ragdocs.embeddings import OllamaEmbedding
            embedding_service = OllamaEmbedding(
                base_url=ollama_url,
                model=embedding_model,
                logger=logger
            )
            logger.info(f"Initialized Ollama embedding service with model: {embedding_model}")
        
        elif embedding_provider.lower() == "openai":
            from ragdocs.embeddings import OpenAIEmbedding
            embedding_service = OpenAIEmbedding(
                api_key=openai_api_key,
                model=embedding_model,
                logger=logger
            )
            logger.info(f"Initialized OpenAI embedding service with model: {embedding_model}")
        
        else:
            raise ValueError(f"Unsupported embedding provider: {embedding_provider}")
        
        # Create storage service
        from ragdocs.storage import QdrantStorage
        storage_service = QdrantStorage(
            url=qdrant_url,
            collection_name=qdrant_collection,
            embedding_dimension=embedding_service.dimension,
            logger=logger
        )
        logger.info(f"Initialized Qdrant storage service at: {qdrant_url} with collection: {qdrant_collection}")
        
    except ImportError as e:
        logger.error(f"Error importing modules: {e}")
        raise
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        raise

# Define FastMCP tools
@mcp.tool()
async def add_documentation(url: str) -> str:
    """Add documentation from a URL to the RAG database.
    
    Args:
        url: URL of the documentation to fetch
    """
    logger.info(f"Adding documentation from URL: {url}")
    
    try:
        # Import web fetcher
        from ragdocs.fetchers import WebFetcher
        
        # Create fetcher
        fetcher = WebFetcher(logger=logger)
        
        # Fetch content
        content = await fetcher.fetch(url)
        
        if not content:
            return f"Error: Could not fetch content from {url}"
        
        # Process content
        chunks = await fetcher.process(content, metadata={"url": url})
        
        if not chunks or len(chunks) == 0:
            return f"Error: No content extracted from {url}"
        
        # Generate embeddings
        embeddings = []
        for chunk in chunks:
            embedding = await embedding_service.embed(chunk.text)
            embeddings.append(embedding)
        
        # Store embeddings
        await storage_service.add(embeddings, chunks)
        
        return f"Successfully added {len(chunks)} chunks from {url}"
    except Exception as e:
        error_msg = f"Error adding documentation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

@mcp.tool()
async def search_documentation(query: str, limit: int = 5) -> str:
    """Search through stored documentation.
    
    Args:
        query: Search query
        limit: Maximum number of results to return (default: 5)
    """
    logger.info(f"Searching documentation with query: {query}")
    
    try:
        # Generate query embedding
        embedding = await embedding_service.embed(query)
        
        # Search database
        results = await storage_service.search(embedding, limit=limit)
        
        if not results or len(results) == 0:
            return "No results found for your query."
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results):
            score = result.score
            chunk = result.chunk
            
            # Get metadata
            source = "Unknown source"
            if hasattr(chunk, 'metadata') and hasattr(chunk.metadata, 'url'):
                source = chunk.metadata.url
            
            formatted = f"[{i+1}] Source: {source} (Score: {score:.2f})\n\n"
            formatted += chunk.text
            
            formatted_results.append(formatted)
        
        return "\n\n---\n\n".join(formatted_results)
    except Exception as e:
        error_msg = f"Error searching documentation: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

@mcp.tool()
async def list_sources() -> str:
    """List all documentation sources currently stored."""
    logger.info("Listing documentation sources")
    
    try:
        sources = await storage_service.list_sources()
        
        if not sources or len(sources) == 0:
            return "No documentation sources found."
        
        formatted = "Documentation sources:\n\n"
        for i, source in enumerate(sources):
            formatted += f"{i+1}. {source}\n"
        
        return formatted
    except Exception as e:
        error_msg = f"Error listing sources: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

@mcp.tool()
async def add_directory(path: str) -> str:
    """Add all supported files from a directory to the RAG database.
    
    Args:
        path: Path to the directory containing documents
    """
    logger.info(f"Adding documentation from directory: {path}")
    
    try:
        import os
        from ragdocs.processors import PDFProcessor, TextProcessor
        
        # Check if directory exists
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a directory or doesn't exist"
        
        # Create processors
        pdf_processor = PDFProcessor(logger=logger)
        text_processor = TextProcessor(logger=logger)
        
        # Statistics
        stats = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "total_chunks": 0
        }
        
        processed_files = []
        failed_files = []
        
        # Process files
        for root, _, files in os.walk(path):
            for filename in files:
                file_path = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1][1:].lower()
                
                try:
                    # Check supported file types
                    if pdf_processor.can_process(file_path):
                        logger.info(f"Processing PDF file: {file_path}")
                        chunks = await pdf_processor.process(file_path)
                    elif text_processor.can_process(file_path):
                        logger.info(f"Processing text file: {file_path}")
                        chunks = await text_processor.process(file_path)
                    else:
                        logger.info(f"Skipping unsupported file: {file_path}")
                        stats["skipped"] += 1
                        continue
                    
                    if not chunks:
                        logger.info(f"No content extracted from: {file_path}")
                        stats["skipped"] += 1
                        continue
                    
                    # Generate embeddings
                    embeddings = []
                    for chunk in chunks:
                        embedding = await embedding_service.embed(chunk.text)
                        embeddings.append(embedding)
                    
                    # Store in database
                    await storage_service.add(embeddings, chunks)
                    
                    processed_files.append(file_path)
                    stats["processed"] += 1
                    stats["total_chunks"] += len(chunks)
                    logger.info(f"Successfully processed {file_path}: {len(chunks)} chunks")
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}")
                    failed_files.append(file_path)
                    stats["failed"] += 1
        
        # Create response summary
        summary = f"Directory Processing Results:\n\n"
        summary += f"Processed {stats['processed']} files successfully\n"
        summary += f"Failed to process {stats['failed']} files\n"
        summary += f"Skipped {stats['skipped']} unsupported files\n"
        summary += f"Added {stats['total_chunks']} total chunks to the database\n\n"
        
        if processed_files:
            summary += "Successfully processed files:\n"
            for i, file_path in enumerate(processed_files[:10], 1):
                summary += f"{i}. {file_path}\n"
            
            if len(processed_files) > 10:
                summary += f"...and {len(processed_files) - 10} more files\n"
        
        if failed_files:
            summary += "\nFailed files:\n"
            for i, file_path in enumerate(failed_files[:5], 1):
                summary += f"{i}. {file_path}\n"
            
            if len(failed_files) > 5:
                summary += f"...and {len(failed_files) - 5} more files\n"
        
        return summary
    except Exception as e:
        error_msg = f"Error adding directory: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg

def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="RAGDocs FastMCP Server")
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        # Initialize services
        setup_services()
        
        # Start MCP server
        logger.info("Starting RAGDocs FastMCP Server")
        mcp.run(transport='stdio')
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
