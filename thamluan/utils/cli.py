"""
CLI module - Parse command-line arguments.
"""

import argparse
from typing import Any


def parse_arguments() -> Any:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="AutoData - AI Agent Crawler System for Vietnamese Law Documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default URL
  python main.py

  # Run with custom URL and project name
  python main.py --url "https://example.com/draft" --project "Luật ABC 2025"

  # Run in async mode
  python main.py --async

  # Show configuration
  python main.py --show-config
        """
    )

    parser.add_argument(
        '--url',
        type=str,
        help='Target URL to crawl (default: MST law draft page)'
    )

    parser.add_argument(
        '--project',
        type=str,
        help='Project name for this crawl session'
    )

    parser.add_argument(
        '--async',
        dest='async_mode',
        action='store_true',
        help='Run workflow in async mode (default: sync)'
    )

    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Display current configuration and exit'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--no-selenium',
        action='store_true',
        help='Disable Selenium for web crawling (use requests only)'
    )

    parser.add_argument(
        '--max-comments',
        type=int,
        help='Maximum number of comments to collect per source'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for results (default: ./data)'
    )

    args = parser.parse_args()

    return args


# Export
__all__ = ["parse_arguments"]