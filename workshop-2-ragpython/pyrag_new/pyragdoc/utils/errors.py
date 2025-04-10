"""Error classes for PyRAGDoc."""

from typing import Optional, Dict, Any


class PyRAGDocError(Exception):
    """Base exception class for PyRAGDoc errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize the exception.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ProcessingError(PyRAGDocError):
    """Error raised for document processing issues."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, details)


class EmbeddingError(PyRAGDocError):
    """Error raised for embedding generation issues."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, details)


class StorageError(PyRAGDocError):
    """Error raised for storage issues."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, details)


class NotFoundError(PyRAGDocError):
    """Error raised when a resource is not found."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 404, details)



