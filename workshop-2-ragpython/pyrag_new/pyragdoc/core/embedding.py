"""Embedding services for converting text to vector representations."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union

from openai import OpenAI
import ollama

from ..utils.logging import get_logger
from ..utils.errors import EmbeddingError


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""
    
    def __init__(self, model: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """Initialize the embedding provider.
        
        Args:
            model: Model name
            logger: Logger instance
        """
        self.model = model
        self.logger = logger or get_logger(__name__)
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def get_vector_size(self) -> int:
        """Get the size of the embedding vector.
        
        Returns:
            Size of the embedding vector
        """
        pass


class OllamaProvider(EmbeddingProvider):
    """Embedding provider using Ollama."""
    
    def __init__(
        self, 
        model: str = "nomic-embed-text",
        base_url: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the Ollama embedding provider.
        
        Args:
            model: Model name
            base_url: Base URL for Ollama API
            logger: Logger instance
        """
        super().__init__(model, logger)
        
        import os
        self.base_url = base_url or os.environ.get("OLLAMA_URL", "http://localhost:11434")
        
        # Initialize client
        self.client = ollama.Client(host=self.base_url)
        
        self.logger.info(f"Initialized Ollama provider with URL: {self.base_url}, model: {self.model}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding using Ollama.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            # Truncate text if too long
            text_preview = text[:50] + "..." if len(text) > 50 else text
            self.logger.debug(f"Generating embedding for: {text_preview}")
            
            # Convert to async using asyncio.to_thread
            import asyncio
            response = await asyncio.to_thread(
                self.client.embeddings,
                model=self.model,
                prompt=text
            )
            
            embedding = response.get("embedding", [])
            
            if not embedding:
                raise EmbeddingError("Ollama returned empty embedding")
            
            self.logger.debug(f"Generated embedding with size: {len(embedding)}")
            
            return embedding
        except Exception as e:
            error_msg = f"Failed to generate embedding with Ollama: {str(e)}"
            self.logger.error(error_msg)
            raise EmbeddingError(error_msg)
    
    def get_vector_size(self) -> int:
        """Get the size of the embedding vector.
        
        Returns:
            Size of the embedding vector
        """
        # Different models have different vector sizes
        vector_sizes = {
            "nomic-embed-text": 768,
            "nomic-embed-text-v1.5": 768,
            "all-minilm": 384,
            "e5-small": 384,
            "e5-large": 1024
        }
        
        return vector_sizes.get(self.model, 768)


class OpenAIProvider(EmbeddingProvider):
    """Embedding provider using OpenAI API."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name
            logger: Logger instance
        """
        super().__init__(model, logger)
        
        # Initialize client
        self.client = OpenAI(api_key=api_key)
        
        self.logger.info(f"Initialized OpenAI provider with model: {self.model}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding using OpenAI API.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            # Truncate text if too long
            text_preview = text[:50] + "..." if len(text) > 50 else text
            self.logger.debug(f"Generating embedding for: {text_preview}")
            
            # Convert to async using asyncio.to_thread
            import asyncio
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            self.logger.debug(f"Generated embedding with size: {len(embedding)}")
            
            return embedding
        except Exception as e:
            error_msg = f"Failed to generate embedding with OpenAI: {str(e)}"
            self.logger.error(error_msg)
            raise EmbeddingError(error_msg)
    
    def get_vector_size(self) -> int:
        """Get the size of the embedding vector.
        
        Returns:
            Size of the embedding vector
        """
        # Different models have different vector sizes
        vector_sizes = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        
        return vector_sizes.get(self.model, 1536)


class EmbeddingService:
    """Service for generating embeddings."""
    
    def __init__(self, provider: EmbeddingProvider):
        """Initialize the embedding service.
        
        Args:
            provider: Embedding provider
        """
        self.provider = provider
        self.logger = provider.logger
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        return await self.provider.generate_embedding(text)
    
    def get_vector_size(self) -> int:
        """Get the size of the embedding vector.
        
        Returns:
            Size of the embedding vector
        """
        return self.provider.get_vector_size()


def create_embedding_service(config: Dict[str, Any]) -> EmbeddingService:
    """Create an embedding service from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Embedding service
        
    Raises:
        EmbeddingError: If provider is invalid or configuration is missing
    """
    logger = get_logger("embedding")
    
    provider = config.get("provider", "ollama").lower()
    model = config.get("model")
    api_key = config.get("api_key")
    
    if provider == "ollama":
        import os
        base_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        # Use default model if not specified
        ollama_model = model or "nomic-embed-text"
        
        logger.info(f"Creating Ollama provider with model: {ollama_model}")
        provider_instance = OllamaProvider(
            model=ollama_model,
            base_url=base_url,
            logger=logger
        )
    elif provider == "openai":
        if not api_key:
            raise EmbeddingError("OpenAI API key is required")
        
        # Use default model if not specified
        openai_model = model or "text-embedding-3-small"
        
        logger.info(f"Creating OpenAI provider with model: {openai_model}")
        provider_instance = OpenAIProvider(
            api_key=api_key,
            model=openai_model,
            logger=logger
        )
    else:
        raise EmbeddingError(f"Unknown embedding provider: {provider}")
    
    return EmbeddingService(provider_instance)
