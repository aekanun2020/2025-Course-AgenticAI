"""Logging utilities for PyRAGDoc."""

import sys
import logging
from typing import Optional


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> None:
    """Set up logging configuration.
    
    Args:
        log_file: Path to log file (optional)
        level: Logging level
    """
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Silence noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
