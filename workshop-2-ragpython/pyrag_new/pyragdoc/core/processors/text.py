"""Text document processor."""

import os
import logging
from typing import List, Dict, Any, Optional, Union, BinaryIO

from ...models.documents import DocumentChunk
from ...utils.errors import ProcessingError
from .base import DocumentProcessor


class TextProcessor(DocumentProcessor):
    """Processor for text documents (txt, md, source code, etc.)."""
    
    # Supported extensions
    SUPPORTED_EXTENSIONS = [
        "txt", "md", "markdown", 
        "py", "js", "java", "c", "cpp", "h", "hpp",
        "html", "css", "json", "yaml", "yml", "xml"
    ]
    
    def __init__(
        self, 
        logger: Optional[logging.Logger] = None, 
        max_chunk_size: int = 1000
    ):
        """Initialize the text processor.
        
        Args:
            logger: Logger instance
            max_chunk_size: Maximum chunk size in characters
        """
        super().__init__(logger, max_chunk_size)
    
    async def process_content(self, content: Union[str, bytes, BinaryIO]) -> List[DocumentChunk]:
        """Process text content and return chunks.
        
        Args:
            content: Text content as string, bytes, file path, or file-like object
            
        Returns:
            List of document chunks
            
        Raises:
            ProcessingError: If processing fails
        """
        try:
            self.logger.info("Processing text document")
            
            # Get text content
            if isinstance(content, str):
                if os.path.exists(content):
                    # Content is a file path
                    with open(content, "r", encoding="utf-8") as f:
                        text = f.read()
                    file_path = content
                else:
                    # Content is text
                    text = content
                    file_path = "unknown"
            elif isinstance(content, bytes):
                # Content is bytes
                text = content.decode("utf-8")
                file_path = "unknown"
            else:
                # Content is file-like object
                text = content.read()
                if isinstance(text, bytes):
                    text = text.decode("utf-8")
                file_path = getattr(content, "name", "unknown")
            
            # Skip empty files
            if not text.strip():
                self.logger.debug("Skipping empty text")
                return []
            
            # Extract document metadata
            metadata = {}
            
            # Use filename as title
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                metadata["title"] = os.path.splitext(filename)[0]
                metadata["source"] = file_path
                metadata["file_type"] = os.path.splitext(filename)[1][1:].lower()
            
            # Chunk the text
            text_chunks = await self.chunk_text(text)
            
            # Create document chunks with metadata
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = i
                
                chunks.append(self.create_chunk(chunk_text, chunk_metadata))
            
            self.logger.info(f"Successfully processed text: extracted {len(chunks)} chunks")
            return chunks
        except Exception as e:
            error_msg = f"Failed to process text: {str(e)}"
            self.logger.error(error_msg)
            raise ProcessingError(error_msg)
    
    def can_process(self, file_path: str, mime_type: Optional[str] = None) -> bool:
        """Check if this processor can handle the given document.
        
        Args:
            file_path: Path to the document
            mime_type: MIME type of the document (optional)
            
        Returns:
            True if the processor can handle the document
        """
        # Check mime type
        if mime_type:
            if mime_type.startswith("text/"):
                return True
        
        # Check file extension
        ext = os.path.splitext(file_path)[1][1:].lower()
        return ext in self.SUPPORTED_EXTENSIONS
