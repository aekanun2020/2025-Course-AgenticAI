"""PDF document processor."""

import os
import logging
from typing import List, Dict, Any, Optional, BinaryIO, Union

import fitz  # PyMuPDF
from ...models.documents import DocumentChunk, DocumentMetadata
from ...utils.errors import ProcessingError
from .base import DocumentProcessor


class PDFProcessor(DocumentProcessor):
    """Processor for PDF documents."""
    
    def __init__(
        self, 
        logger: Optional[logging.Logger] = None, 
        max_chunk_size: int = 1000
    ):
        """Initialize the PDF processor.
        
        Args:
            logger: Logger instance
            max_chunk_size: Maximum chunk size in characters
        """
        super().__init__(logger, max_chunk_size)
    
    async def process_content(self, content: Union[bytes, str, BinaryIO]) -> List[DocumentChunk]:
        """Process PDF content and return chunks.
        
        Args:
            content: PDF content as bytes, file path, or file-like object
            
        Returns:
            List of document chunks
            
        Raises:
            ProcessingError: If processing fails
        """
        try:
            self.logger.info("Processing PDF document")
            
            # Open the PDF document
            if isinstance(content, str) and os.path.exists(content):
                # Content is a file path
                pdf_document = fitz.open(content)
                file_path = content
            else:
                # Content is bytes or file-like object
                pdf_document = fitz.open(stream=content, filetype="pdf")
                file_path = "unknown"
            
            num_pages = len(pdf_document)
            self.logger.info(f"PDF has {num_pages} pages")
            
            # Extract document metadata
            metadata = {}
            pdf_metadata = pdf_document.metadata
            if pdf_metadata:
                if "title" in pdf_metadata and pdf_metadata["title"]:
                    metadata["title"] = pdf_metadata["title"]
                if "author" in pdf_metadata and pdf_metadata["author"]:
                    metadata["author"] = pdf_metadata["author"]
            
            # Use filename as title if no title in metadata
            if "title" not in metadata and os.path.exists(file_path):
                filename = os.path.basename(file_path)
                metadata["title"] = os.path.splitext(filename)[0]
            
            # Set source
            if os.path.exists(file_path):
                metadata["source"] = file_path
            
            # Set file type
            metadata["file_type"] = "pdf"
            
            chunks = []
            for page_num in range(num_pages):
                try:
                    self.logger.debug(f"Processing page {page_num + 1}/{num_pages}")
                    
                    # Get page and extract text
                    page = pdf_document[page_num]
                    text = page.get_text()
                    
                    # Skip empty pages
                    if not text.strip():
                        self.logger.debug(f"Skipping empty page {page_num + 1}")
                        continue
                    
                    # Chunk the text
                    text_chunks = await self.chunk_text(text)
                    
                    # Create document chunks with metadata
                    page_metadata = metadata.copy()
                    page_metadata["page_number"] = page_num + 1
                    
                    for i, chunk_text in enumerate(text_chunks):
                        chunk_metadata = page_metadata.copy()
                        chunk_metadata["chunk_index"] = i
                        
                        chunks.append(self.create_chunk(chunk_text, chunk_metadata))
                except Exception as e:
                    self.logger.error(f"Error processing page {page_num + 1}: {str(e)}")
                    continue
            
            pdf_document.close()
            self.logger.info(f"Successfully processed PDF: extracted {len(chunks)} chunks")
            return chunks
        except Exception as e:
            error_msg = f"Failed to process PDF: {str(e)}"
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
        if mime_type and mime_type.lower() == "application/pdf":
            return True
        
        return file_path.lower().endswith(".pdf")
