"""Configuration models for PyRAGDoc."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Server configuration settings."""
    
    port: int = Field(default=3000, description="Port for the server to listen on")
    max_concurrent_requests: int = Field(
        default=10, 
        description="Maximum number of concurrent requests"
    )
    request_timeout: int = Field(
        default=30000, 
        description="Request timeout in milliseconds"
    )


class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    
    url: str = Field(
        default="http://localhost:6333", 
        description="URL for the Qdrant server"
    )
    collection: str = Field(
        default="documentation", 
        description="Collection name in Qdrant"
    )
    max_batch_size: int = Field(
        default=100, 
        description="Maximum batch size for operations"
    )
    backup_dir: str = Field(
        default="./backup", 
        description="Directory for backups"
    )


class EmbeddingConfig(BaseModel):
    """Embedding service configuration settings."""
    
    provider: str = Field(
        default="ollama", 
        description="Provider for embeddings (ollama or openai)"
    )
    model: Optional[str] = Field(
        default=None, 
        description="Model to use for embeddings"
    )
    max_retries: int = Field(
        default=3, 
        description="Maximum retries for embedding generation"
    )
    api_key: Optional[str] = Field(
        default=None, 
        description="API key for the provider"
    )


class SecurityConfig(BaseModel):
    """Security configuration settings."""
    
    rate_limit_requests: int = Field(
        default=100, 
        description="Number of requests allowed in window"
    )
    rate_limit_window: int = Field(
        default=60000, 
        description="Rate limiting window in milliseconds"
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024, 
        description="Maximum file size in bytes"
    )


class ProcessingConfig(BaseModel):
    """Document processing configuration settings."""
    
    max_chunk_size: int = Field(
        default=1000, 
        description="Maximum chunk size in characters"
    )
    max_memory_usage: int = Field(
        default=512 * 1024 * 1024, 
        description="Maximum memory usage in bytes"
    )
    supported_file_types: List[str] = Field(
        default=["pdf", "txt", "md"], 
        description="Supported file types"
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024, 
        description="Maximum file size in bytes"
    )


class AppConfig(BaseModel):
    """Main application configuration."""
    
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
