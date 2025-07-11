"""
Logging configuration for Bookology Backend.

This module sets up structured logging for the application with proper
formatting, levels, and output configuration.
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional
from config import settings


def setup_logger(
    name: str = "bookology",
    level: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger instance with both console and file output.
    
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
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Create file handler for general logs
    today = datetime.now().strftime("%Y-%m-%d")
    general_log_file = os.path.join(logs_dir, f"bookology_{today}.log")
    file_handler = logging.FileHandler(general_log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, level.upper()))
    
    # Create separate file handler for summary-related logs
    summary_log_file = os.path.join(logs_dir, f"summary_generation_{today}.log")
    summary_handler = logging.FileHandler(summary_log_file, encoding='utf-8')
    summary_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(funcName)s:%(lineno)d - %(message)s"
        )
    
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    summary_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Add summary handler only for summary-related loggers
    if "summary" in name.lower() or name == "bookology":
        logger.addHandler(summary_handler)
    
    return logger


def setup_summary_logger() -> logging.Logger:
    """
    Set up a dedicated logger for summary generation with enhanced file logging.
    
    Returns:
        logging.Logger: Configured logger for summary operations.
    """
    return setup_logger("summary_generation", "DEBUG")


# Create default logger instance
logger = setup_logger()

# Create summary-specific logger
summary_logger = setup_summary_logger()