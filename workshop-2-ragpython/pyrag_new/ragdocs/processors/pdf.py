"""PDF processor for RAGDocs."""

import os
import logging
from typing import List, Dict, Any, Optional

import fitz  # PyMuPDF
from ..storage import Document


class PDFProcessor:
    """Processor for PDF documents."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the PDF processor.
        
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
        return file_path.lower().endswith('.pdf')
    
    async def process(self, file_path: str) -> List[Document]:
        """Process a PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of document chunks
        """
        try:
            self.logger.info(f"Processing PDF: {file_path}")
            
            # Open PDF
            pdf = fitz.open(file_path)
            
            # Extract metadata
            metadata = {
                "source": file_path,
                "title": os.path.basename(file_path),
                "page_count": pdf.page_count
            }
            
            # Try to get PDF title
            pdf_title = pdf.metadata.get("title")
            if pdf_title:
                metadata["title"] = pdf_title
            
            # Extract text page by page
            chunks = []
            for page_num in range(pdf.page_count):
                page = pdf[page_num]
                text = page.get_text()
                
                # Skip if page is empty
                if not text.strip():
                    continue
                
                # Create page-specific metadata
                page_metadata = metadata.copy()
                page_metadata["page"] = page_num + 1
                
                # Create document
                chunks.append(Document(
                    text=text,
                    metadata=page_metadata
                ))
            
            pdf.close()
            self.logger.info(f"Extracted {len(chunks)} chunks from PDF")
            return chunks
        
        except Exception as e:
            self.logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return []
