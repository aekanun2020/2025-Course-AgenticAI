"""Base storage class for RAGDocs."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class Document:
    """Document with text and metadata."""
    
    text: str
    metadata: Dict[str, Any]


@dataclass
class SearchResult:
    """Search result with document and score."""
    
    chunk: Document
    score: float


class BaseStorage(ABC):
    """Base class for storage providers."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the storage provider.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    @abstractmethod
    async def add(self, embeddings: List[List[float]], documents: List[Document]) -> None:
        """Add documents with embeddings to the storage.
        
        Args:
            embeddings: List of embedding vectors
            documents: List of documents
        """
        pass
    
    @abstractmethod
    async def search(
        self, 
        embedding: List[float], 
        limit: int = 5, 
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """Search for similar documents.
        
        Args:
            embedding: Query embedding vector
            limit: Maximum number of results
            filters: Optional metadata filters
            min_score: Minimum similarity score
            
        Returns:
            List of search results
        """
        pass
    
    @abstractmethod
    async def list_sources(self) -> List[str]:
        """List all document sources.
        
        Returns:
            List of source identifiers
        """
        pass
