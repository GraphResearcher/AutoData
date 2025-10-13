"""
Logging configuration for AutoData package.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

from core.config import config


def setup_logging(log_level: str = None) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Root logger
    """
    # Determine log level
    if log_level is None:
        log_level = config.LOG_LEVEL

    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create logs directory
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = config.LOGS_DIR / f"autodata_{timestamp}.log"

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (with colors if possible)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(console_handler)

    # File handler (rotating)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.LOG_FILE_MAX_BYTES,
        backupCount=config.LOG_FILE_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Log initial message
    root_logger.info("=" * 60)
    root_logger.info("Logging initialized")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info("=" * 60)

    return root_logger


class ColoredFormatter(logging.Formatter):
    """
    Colored log formatter for console output.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'  # Reset
    }

    def format(self, record):
        """Format log record with colors"""
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )

        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger for a specific module.

    Args:
        name: Module name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Export
__all__ = ["setup_logging", "get_logger"]