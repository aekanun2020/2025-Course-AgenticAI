"""Document processors for handling different file types."""

import logging
import os
from typing import Dict, Optional, Type

from ...utils.logging import get_logger
from .base import DocumentProcessor


_PROCESSORS: Dict[str, Type[DocumentProcessor]] = {}


def register_processor(processor_class: Type[DocumentProcessor]) -> None:
    """Register a document processor.
    
    Args:
        processor_class: Processor class to register
    """
    global _PROCESSORS
    _PROCESSORS[processor_class.__name__] = processor_class
    logger = get_logger(__name__)
    logger.debug(f"Registered processor: {processor_class.__name__}")


def get_processor_for_file(file_path: str, mime_type: Optional[str] = None) -> Optional[DocumentProcessor]:
    """Get a processor for a file.
    
    Args:
        file_path: Path to the file
        mime_type: MIME type of the file (optional)
        
    Returns:
        Processor instance or None if no processor is available
    """
    logger = get_logger(__name__)
    
    # Import processors (this triggers registration)
    from . import pdf, text
    
    # Create processor instances
    processors = [cls(logger=logger) for cls in _PROCESSORS.values()]
    
    # Find a processor that can handle the file
    for processor in processors:
        if processor.can_process(file_path, mime_type):
            logger.debug(f"Using processor {processor.__class__.__name__} for file {file_path}")
            return processor
    
    logger.warning(f"No processor found for file {file_path}")
    return None


# Import processors to register them
from .pdf import PDFProcessor
register_processor(PDFProcessor)

from .text import TextProcessor
register_processor(TextProcessor)
