"""Test cases for AutoData logging functionality."""

import os
import tempfile
from pathlib import Path
import pytest
from loguru import logger
import time

from AutoData.utils.logging import setup_logging


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_console_logging(capsys):
    """Test console logging configuration."""
    # Setup logging with default settings
    setup_logging(log_level="INFO")

    # Log a test message
    test_message = "Test console logging"
    logger.info(test_message)

    # Capture the output
    captured = capsys.readouterr()

    # Verify the log format
    assert "INFO" in captured.err
    assert test_message in captured.err
    assert "test_console_logging" in captured.err  # Function name
    assert "test_logging" in captured.err  # Module name


def test_file_logging(temp_log_dir):
    """Test file logging configuration."""
    # Create a log file path
    log_file = Path(temp_log_dir) / "test.log"

    # Setup logging with file output
    setup_logging(log_level="DEBUG", log_file=str(log_file))

    # Log a test message
    test_message = "Test file logging"
    logger.debug(test_message)

    # Verify the log file was created
    assert log_file.exists()

    # Read the log file
    log_content = log_file.read_text()

    # Verify the log format and content
    assert "DEBUG" in log_content
    assert test_message in log_content
    assert "test_file_logging" in log_content  # Function name


def test_log_levels(capsys):
    """Test different log levels."""
    # Setup logging with DEBUG level
    setup_logging(log_level="DEBUG")

    # Log messages at different levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    # Capture the output
    captured = capsys.readouterr()

    # Verify all levels are present
    assert "DEBUG" in captured.err
    assert "INFO" in captured.err
    assert "WARNING" in captured.err
    assert "ERROR" in captured.err


def test_invalid_log_level():
    """Test handling of invalid log level."""
    with pytest.raises(ValueError):
        setup_logging(log_level="INVALID_LEVEL")


def test_log_file_permissions(temp_log_dir):
    """Test log file permissions and directory creation."""
    # Create a nested directory structure
    nested_dir = Path(temp_log_dir) / "nested" / "dir" / "structure"
    log_file = nested_dir / "test.log"

    # Setup logging
    setup_logging(log_file=str(log_file))

    # Verify directory was created
    assert nested_dir.exists()

    # Verify log file was created
    assert log_file.exists()

    # Verify file permissions
    assert os.access(log_file, os.W_OK)  # Check if file is writable
