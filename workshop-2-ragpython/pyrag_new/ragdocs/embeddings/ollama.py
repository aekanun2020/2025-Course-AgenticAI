"""Ollama embedding provider for RAGDocs."""

import json
import logging
from typing import List, Dict, Any

import aiohttp
from .base import BaseEmbedding


class OllamaEmbedding(BaseEmbedding):
    """Ollama embedding provider."""
    
    def __init__(self, base_url: str, model: str, logger: logging.Logger = None):
        """Initialize the Ollama embedding provider.
        
        Args:
            base_url: Ollama API base URL
            model: Embedding model name
            logger: Logger instance
        """
        super().__init__(model, logger)
        self.base_url = base_url.rstrip('/')
        self._dimension = 1536  # Default for most Ollama embedding models
        self.embeddings_endpoint = f"{self.base_url}/api/embeddings"
    
    async def embed(self, text: str) -> List[float]:
        """Generate an embedding for the given text using Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            # Prepare request
            payload = {
                "model": self.model,
                "prompt": text
            }
            
            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.post(self.embeddings_endpoint, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Ollama API error: {error_text}")
                        raise ValueError(f"Failed to get embedding from Ollama: {error_text}")
                    
                    # Parse response
                    response_data = await response.json()
                    embedding = response_data.get("embedding", [])
                    
                    # Update dimension if needed
                    if len(embedding) > 0 and self._dimension != len(embedding):
                        self._dimension = len(embedding)
                        self.logger.info(f"Updated embedding dimension to {self._dimension}")
                    
                    return embedding
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP error when connecting to Ollama: {str(e)}")
            raise
        except json.JSONDecodeError:
            self.logger.error("Failed to parse Ollama API response")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error when generating embedding: {str(e)}")
            raise
