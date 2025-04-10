"""Base embedding class for RAGDocs."""

import logging
from abc import ABC, abstractmethod
from typing import List


class BaseEmbedding(ABC):
    """Base class for embedding providers."""
    
    def __init__(self, model: str, logger: logging.Logger = None):
        """Initialize the embedding provider.
        
        Args:
            model: Embedding model name
            logger: Logger instance
        """
        self.model = model
        self.logger = logger or logging.getLogger(__name__)
        self._dimension = None
    
    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        if not self._dimension:
            raise ValueError("Embedding dimension not initialized")
        return self._dimension
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate an embedding for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        pass
