"""Base document processor."""

import uuid
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...models.documents import DocumentChunk, DocumentMetadata
from ...utils.errors import ProcessingError


class DocumentProcessor(ABC):
    """Base class for document processors."""
    
    def __init__(self, logger: Optional[logging.Logger] = None, max_chunk_size: int = 1000):
        """Initialize the document processor.
        
        Args:
            logger: Logger instance
            max_chunk_size: Maximum chunk size in characters
        """
        self.logger = logger or logging.getLogger(__name__)
        self.max_chunk_size = max_chunk_size
    
    @abstractmethod
    async def process_content(self, content: bytes) -> List[DocumentChunk]:
        """Process document content and return chunks.
        
        Args:
            content: Document content
            
        Returns:
            List of document chunks
            
        Raises:
            ProcessingError: If processing fails
        """
        pass
    
    @abstractmethod
    def can_process(self, file_path: str, mime_type: Optional[str] = None) -> bool:
        """Check if this processor can handle the given document.
        
        Args:
            file_path: Path to the document
            mime_type: MIME type of the document (optional)
            
        Returns:
            True if the processor can handle the document
        """
        pass
    
    async def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks of maximum size.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            current_text = " ".join(current_chunk)
            
            if len(current_text) >= self.max_chunk_size:
                chunks.append(current_text)
                current_chunk = []
        
        # Add any remaining text as a chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
    
    def create_chunk(
        self, 
        text: str, 
        metadata: Dict[str, Any] = None
    ) -> DocumentChunk:
        """Create a document chunk with metadata.
        
        Args:
            text: Chunk text
            metadata: Additional metadata
            
        Returns:
            Document chunk
        """
        meta_dict = metadata or {}
        doc_metadata = DocumentMetadata(**meta_dict)
        
        return DocumentChunk(
            text=text,
            metadata=doc_metadata,
            timestamp=datetime.now(),
            id=str(uuid.uuid4())
        )
