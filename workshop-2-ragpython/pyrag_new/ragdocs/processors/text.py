"""Text processor for RAGDocs."""

import os
import logging
from typing import List, Dict, Any, Optional

from ..storage import Document


class TextProcessor:
    """Processor for text documents."""
    
    SUPPORTED_EXTENSIONS = [
        '.txt', '.md', '.markdown', '.rst', '.py', '.js', '.html', '.htm',
        '.css', '.json', '.xml', '.yaml', '.yml', '.ini', '.cfg', '.conf'
    ]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the text processor.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def can_process(self, file_path: str) -> bool:
        """Check if file can be processed.
        
        Args:
            file_path: Path to file
        
        Returns:
            True if file can be processed
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.SUPPORTED_EXTENSIONS
    
    async def process(self, file_path: str) -> List[Document]:
        """Process a text file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            List of document chunks
        """
        try:
            self.logger.info(f"Processing text file: {file_path}")
            
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()
            
            # Skip if file is empty
            if not text.strip():
                return []
            
            # Extract metadata
            metadata = {
                "source": file_path,
                "title": os.path.basename(file_path),
                "extension": os.path.splitext(file_path)[1][1:].lower()
            }
            
            # Chunking (4000 characters per chunk)
            chunk_size = 4000
            chunks = []
            
            for i in range(0, len(text), chunk_size):
                chunk_text = text[i:i+chunk_size]
                
                # Create chunk-specific metadata
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = len(chunks)
                
                # Create document
                chunks.append(Document(
                    text=chunk_text,
                    metadata=chunk_metadata
                ))
            
            self.logger.info(f"Extracted {len(chunks)} chunks from text file")
            return chunks
        
        except Exception as e:
            self.logger.error(f"Error processing text file {file_path}: {str(e)}")
            return []
