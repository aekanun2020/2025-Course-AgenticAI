"""OpenAI embedding provider for RAGDocs."""

import logging
from typing import List, Dict, Any

import aiohttp
from .base import BaseEmbedding


class OpenAIEmbedding(BaseEmbedding):
    """OpenAI embedding provider."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small", logger: logging.Logger = None):
        """Initialize the OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model name
            logger: Logger instance
        """
        super().__init__(model, logger)
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        
        # Set up model dimensions
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        
        self._dimension = model_dimensions.get(model, 1536)
        self.logger.info(f"Using OpenAI model {model} with dimension {self._dimension}")
    
    async def embed(self, text: str) -> List[float]:
        """Generate an embedding for the given text using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            # Prepare request
            url = f"{self.base_url}/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "input": text,
                "model": self.model
            }
            
            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"OpenAI API error: {error_text}")
                        raise ValueError(f"Failed to get embedding from OpenAI: {error_text}")
                    
                    # Parse response
                    response_data = await response.json()
                    embedding = response_data["data"][0]["embedding"]
                    
                    return embedding
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP error when connecting to OpenAI: {str(e)}")
            raise
        except KeyError as e:
            self.logger.error(f"Unexpected response format from OpenAI: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error when generating embedding: {str(e)}")
            raise
