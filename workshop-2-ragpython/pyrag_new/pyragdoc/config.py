"""Configuration management for PyRAGDoc."""

import os
import logging
from typing import Dict, Any


DEFAULT_CONFIG = {
    "server": {
        "port": 3000,
        "max_concurrent_requests": 10,
        "request_timeout": 30000  # 30 seconds
    },
    "database": {
        "url": "http://localhost:6333",
        "collection": "documentation",
        "backup_dir": "./backup"
    },
    "embedding": {
        "provider": "ollama",
        "model": "nomic-embed-text",
        "max_retries": 3,
        "api_key": None
    },
    "security": {
        "max_file_size": 10 * 1024 * 1024  # 10MB
    },
    "processing": {
        "max_chunk_size": 1000,
        "supported_file_types": [
            "pdf",
            "txt",
            "md",
            "js",
            "ts",
            "py",
            "java",
            "c",
            "cpp",
            "h",
            "hpp"
        ],
        "max_file_size": 10 * 1024 * 1024  # 10MB
    }
}


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables.
    
    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Database configuration
    if os.environ.get("QDRANT_URL"):
        config["database"]["url"] = os.environ.get("QDRANT_URL")
    
    # Embedding configuration
    if os.environ.get("EMBEDDING_PROVIDER"):
        config["embedding"]["provider"] = os.environ.get("EMBEDDING_PROVIDER")
    
    if os.environ.get("EMBEDDING_MODEL"):
        config["embedding"]["model"] = os.environ.get("EMBEDDING_MODEL")
    
    if os.environ.get("OPENAI_API_KEY"):
        config["embedding"]["api_key"] = os.environ.get("OPENAI_API_KEY")
    
    # Server configuration
    if os.environ.get("PORT"):
        config["server"]["port"] = int(os.environ.get("PORT"))
    
    logging.debug(f"Loaded configuration: {config}")
    
    return config
