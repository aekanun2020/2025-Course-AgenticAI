#!/usr/bin/env python3
"""Script to reimport 1-tool_use.pdf file into Qdrant."""

import os
import sys
import asyncio
import logging

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyragdoc.config import load_config
from pyragdoc.core.embedding import create_embedding_service
from pyragdoc.core.storage import create_storage_service
from pyragdoc.core.processors.pdf import PDFProcessor
from pyragdoc.utils.logging import setup_logging, get_logger

async def reimport_file():
    """Reimport 1-tool_use.pdf file."""
    # Set up logging
    setup_logging(None, logging.INFO)
    logger = get_logger("reimport")
    
    # Load configuration
    config = load_config()
    
    # Initialize services
    logger.info("Initializing services...")
    embedding_service = create_embedding_service(config["embedding"])
    storage_service = create_storage_service(config["database"])
    
    # Initialize PDF processor
    pdf_processor = PDFProcessor(logger=logger)
    
    # Process the PDF file
    file_path = "/Users/grizzlym1/Desktop/docs/1-tool_use.pdf"
    
    try:
        logger.info(f"Processing PDF file: {file_path}")
        chunks = await pdf_processor.process_content(file_path)
        
        if not chunks:
            logger.info(f"No content extracted from: {file_path}")
            return
        
        logger.info(f"Extracted {len(chunks)} chunks from {file_path}")
        
        # Generate embeddings and store chunks
        embeddings = []
        for chunk in chunks:
            # Generate embedding
            embedding = await embedding_service.generate_embedding(chunk.text)
            embeddings.append(embedding)
        
        # Store chunks
        await storage_service.add_documents(embeddings, chunks)
        
        logger.info(f"Successfully added {len(chunks)} chunks to Qdrant")
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}", exc_info=True)
        
    # List sources to verify
    try:
        sources = await storage_service.list_sources()
        logger.info(f"Sources in database: {sources}")
    except Exception as e:
        logger.error(f"Error listing sources: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(reimport_file())
