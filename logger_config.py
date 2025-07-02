"""
Logging configuration for Bookology Backend.

This module sets up structured logging for the application with proper
formatting, levels, and output configuration.
"""

import logging
import sys
from typing import Optional
from config import settings


def setup_logger(
    name: str = "bookology",
    level: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name (str): Logger name (default: "bookology").
        level (str, optional): Logging level. Defaults to DEBUG if settings.DEBUG is True, else INFO.
        format_string (str, optional): Custom format string for log messages.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Determine logging level
    if level is None:
        level = "DEBUG" if settings.DEBUG else "INFO"
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid adding multiple handlers to the same logger
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(funcName)s:%(lineno)d - %(message)s"
        )
    
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


# Create default logger instance
logger = setup_logger()