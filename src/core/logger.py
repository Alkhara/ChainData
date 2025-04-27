import logging
import sys
from pathlib import Path
from typing import Optional

from .config import config

def setup_logger(
    name: str = "chaindata",
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Setup and configure the logger"""
    logger = logging.getLogger(name)
    
    # Set log level from config or default to INFO
    log_level = level or config.log_level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create default logger instance
logger = setup_logger()

class APIError(Exception):
    """Base exception for API-related errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ChainlistError(APIError):
    """Exception for Chainlist API errors"""
    pass

class DefiLlamaError(APIError):
    """Exception for DefiLlama API errors"""
    pass

class CacheError(Exception):
    """Exception for cache-related errors"""
    pass

class ValidationError(Exception):
    """Exception for data validation errors"""
    pass 