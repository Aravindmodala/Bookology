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
from app.core.config import settings


def setup_logger(
    name: str = "bookology",
    level: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger instance with both console and (best-effort) file output.
    Falls back to console-only when file handlers cannot be created (e.g., read-only FS).
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

    # Always add console handler
    logger.addHandler(console_handler)

    # Best-effort file handlers (guarded for container environments)
    try:
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        general_log_file = os.path.join(logs_dir, f"bookology_{today}.log")
        file_handler = logging.FileHandler(general_log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        summary_log_file = os.path.join(logs_dir, f"summary_generation_{today}.log")
        summary_handler = logging.FileHandler(summary_log_file, encoding='utf-8')
        summary_handler.setLevel(logging.DEBUG)
        summary_handler.setFormatter(formatter)
        if "summary" in name.lower() or name == "bookology":
            logger.addHandler(summary_handler)
    except Exception:
        # If we cannot write logs to disk, proceed with console-only logging
        pass

    return logger


def setup_summary_logger() -> logging.Logger:
    """
    Set up a dedicated logger for summary generation with enhanced file logging.
    """
    return setup_logger("summary_generation", "DEBUG")


# Create default logger instance
logger = setup_logger()

# Create summary-specific logger
summary_logger = setup_summary_logger()