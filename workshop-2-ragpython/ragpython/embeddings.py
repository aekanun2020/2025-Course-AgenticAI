import os
import logging
import ollama
import openai
from mcp.types import McpError, ErrorCode

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaProvider:
    def __init__(self, model='nomic-embed-text'):
        self.model = model
        self.base_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
        self.client = ollama.Client(host=self.base_url)
        logger.info(f'Initializing Ollama provider with URL: {self.base_url}')

    async def generate_embeddings(self, text):
        try:
            logger.info(f'Generating Ollama embeddings for text: {text[:50]}...')
            response = await self.client.embeddings(model=self.model, prompt=text)
            embedding = response.get('embedding', [])
            logger.info(f'Successfully generated Ollama embeddings with size: {len(embedding)}')
            return embedding
        except Exception as error:
            logger.error(f'Ollama embedding error: {error}')
            raise McpError(ErrorCode.InternalError, f'Failed to generate embeddings with Ollama: {error}')
    
    def get_vector_size(self):
        # nomic-embed-text produces 768-dimensional vectors
        return 768


class OpenAIProvider:
    def __init__(self, api_key, model='text-embedding-3-small'):
        self.client = openai.AsyncClient(api_key=api_key)
        self.model = model
    
    async def generate_embeddings(self, text):
        try:
            logger.info(f'Generating OpenAI embeddings for text: {text[:50]}...')
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embedding = response.data[0].embedding
            logger.info(f'Successfully generated OpenAI embeddings with size: {len(embedding)}')
            return embedding
        except Exception as error:
            logger.error(f'OpenAI embedding error: {error}')
            raise McpError(ErrorCode.InternalError, f'Failed to generate embeddings with OpenAI: {error}')
    
    def get_vector_size(self):
        # text-embedding-3-small produces 1536-dimensional vectors
        return 1536


class EmbeddingService:
    def __init__(self, provider):
        self.provider = provider
    
    async def generate_embeddings(self, text):
        return await self.provider.generate_embeddings(text)
    
    def get_vector_size(self):
        return self.provider.get_vector_size()
    
    @staticmethod
    def create_from_config(config):
        provider = config.get('provider', '').lower()
        
        if provider == 'ollama':
            return EmbeddingService(OllamaProvider(config.get('model')))
        elif provider == 'openai':
            api_key = config.get('api_key')
            if not api_key:
                raise McpError(ErrorCode.InvalidParams, 'OpenAI API key is required')
            return EmbeddingService(OpenAIProvider(api_key, config.get('model')))
        else:
            raise McpError(ErrorCode.InvalidParams, f'Unknown embedding provider: {provider}')
