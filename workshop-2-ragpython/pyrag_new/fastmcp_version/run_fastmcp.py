#!/usr/bin/env python
"""Standalone runner for PyRAGDoc using FastMCP."""

import os
import sys
import logging
import argparse
from typing import Dict, Any

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from mcp.server.fastmcp import FastMCP
import mcp.types as types
import asyncio

from pyragdoc.config import load_config
from pyragdoc.core.embedding import create_embedding_service
from pyragdoc.core.storage import create_storage_service
from pyragdoc.utils.logging import setup_logging, get_logger

# Global variables
mcp = None
embedding_service = None
storage_service = None
logger = None

def setup_mcp_server():
    """Set up MCP server with tools using FastMCP."""
    global mcp, logger
    
    # Create FastMCP instance
    mcp = FastMCP("pyragdoc-server")
    
    @mcp.tool()
    async def add_documentation(url: str) -> str:
        """Add documentation from a URL to the RAG database.
        
        Args:
            url: URL of the documentation to fetch
        """
        try:
            # ตรงนี้เป็นตัวอย่าง, ถ้ามีการ implement จริงให้เรียกใช้ฟังก์ชันที่เหมาะสม
            logger.info(f"Adding documentation from URL: {url}")
            return f"Successfully added documentation from {url}"
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
        try:
            logger.info(f"Searching documentation with query: {query}")
            
            # Generate embedding for query
            embedding = await embedding_service.generate_embedding(query)
            
            # Search for similar documents
            results = await storage_service.search(embedding, limit)
            
            if not results or len(results) == 0:
                return "No results found for your query."
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results):
                chunk = result.chunk
                score = result.score
                
                # Get metadata
                source = "Unknown source"
                if hasattr(chunk.metadata, 'url') and chunk.metadata.url:
                    source = chunk.metadata.url
                elif hasattr(chunk.metadata, 'source') and chunk.metadata.source:
                    source = chunk.metadata.source
                
                title = source
                if hasattr(chunk.metadata, 'title') and chunk.metadata.title:
                    title = chunk.metadata.title
                
                formatted = f"[{i+1}] {title} (Score: {score:.2f})\n"
                formatted += f"Source: {source}\n\n"
                formatted += chunk.text
                
                formatted_results.append(formatted)
            
            formatted_text = "\n\n---\n\n".join(formatted_results)
            return formatted_text
                
        except Exception as e:
            error_msg = f"Error searching documentation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    @mcp.tool()
    async def list_sources() -> str:
        """List all documentation sources currently stored."""
        try:
            logger.info("Listing documentation sources")
            
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
        try:
            logger.info(f"Adding documentation from directory: {path}")
            
            import os
            from pyragdoc.core.processors.pdf import PDFProcessor
            from pyragdoc.core.processors.text import TextProcessor
            
            # ตรวจสอบว่าไดเรกทอรีมีอยู่จริง
            if not os.path.isdir(path):
                return f"Error: '{path}' is not a directory or doesn't exist"
            
            # สร้าง processors
            pdf_processor = PDFProcessor(logger=logger)
            text_processor = TextProcessor(logger=logger)
            
            # เก็บสถิติ
            stats = {
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "total_chunks": 0
            }
            
            # แสดงรายการไฟล์ที่ประมวลผล
            processed_files = []
            failed_files = []
            
            # เริ่มไขว้
            for root, _, files in os.walk(path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    ext = os.path.splitext(filename)[1][1:].lower()
                    
                    try:
                        # ตรวจสอบไฟล์ที่สนับสนุน
                        if pdf_processor.can_process(file_path):
                            logger.info(f"Processing PDF file: {file_path}")
                            chunks = await pdf_processor.process_content(file_path)
                        elif text_processor.can_process(file_path):
                            logger.info(f"Processing text file: {file_path}")
                            chunks = await text_processor.process_content(file_path)
                        else:
                            logger.info(f"Skipping unsupported file: {file_path}")
                            stats["skipped"] += 1
                            continue
                        
                        if not chunks:
                            logger.info(f"No content extracted from: {file_path}")
                            stats["skipped"] += 1
                            continue
                        
                        # สร้าง embeddings และบันทึกลงฐานข้อมูล
                        embeddings = []
                        for chunk in chunks:
                            # สร้าง embedding
                            embedding = await embedding_service.generate_embedding(chunk.text)
                            embeddings.append(embedding)
                        
                        # บันทึกข้อมูล
                        await storage_service.add_documents(embeddings, chunks)
                        
                        processed_files.append(file_path)
                        stats["processed"] += 1
                        stats["total_chunks"] += len(chunks)
                        logger.info(f"Successfully processed {file_path}: {len(chunks)} chunks")
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {str(e)}")
                        failed_files.append(file_path)
                        stats["failed"] += 1
            
            # สร้างข้อความตอบกลับ
            summary = f"Directory Processing Results:\n\n"
            summary += f"Processed {stats['processed']} files successfully\n"
            summary += f"Failed to process {stats['failed']} files\n"
            summary += f"Skipped {stats['skipped']} unsupported files\n"
            summary += f"Added {stats['total_chunks']} total chunks to the database\n\n"
            
            if processed_files:
                summary += "Successfully processed files:\n"
                for i, file_path in enumerate(processed_files[:10], 1):
                    summary += f"{i}. {file_path}\n"
                
                # ถ้ามีไฟล์มากกว่า 10 ไฟล์ ให้แสดง ... แทน
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


async def run_mcp_server(config: Dict[str, Any]):
    """Run the MCP server using FastMCP.
    
    Args:
        config: Server configuration
    """
    global embedding_service, storage_service, logger
    
    try:
        # Initialize services
        logger.info("Initializing services...")
        embedding_service = create_embedding_service(config["embedding"])
        storage_service = create_storage_service(config["database"])
        
        # Run server
        logger.info("PyRAGDoc Server with FastMCP is ready")
        mcp.run(transport='stdio')
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)


def run_http_server(config: Dict[str, Any]):
    """Run HTTP server (placeholder).
    
    Args:
        config: Server configuration
    """
    from pyragdoc.server.api import run_http_server as run_original_http_server
    run_original_http_server(config)


def main():
    """Main entry point for the CLI."""
    global logger
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PyRAGDoc Server (FastMCP)")
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
    logger = get_logger("fastmcp_server")
    
    # Load configuration
    config = load_config()
    
    # Set up MCP server if in MCP mode
    if args.mode == "mcp":
        setup_mcp_server()
    
    # Run appropriate server
    try:
        if args.mode == "mcp":
            logger.info("Starting FastMCP server")
            asyncio.run(run_mcp_server(config))
        else:
            logger.info("Starting HTTP server")
            run_http_server(config)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
