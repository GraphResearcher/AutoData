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
  # Run with keywords (NEW - RECOMMENDED)
  python main.py --keywords "Luật Khoa học công nghệ 2025"

  # Run with keywords and custom project name
  python main.py --keywords "Nghị định 123" --project "Nghị định 123/2025"

  # Run with custom URL (old method - still supported)
  python main.py --url "https://example.com/draft" --project "Luật ABC 2025"

  # Show configuration
  python main.py --show-config
        """
    )

    parser.add_argument(
        '--keywords',
        type=str,
        help='Keywords to search for legal documents (e.g., "Luật Khoa học công nghệ 2025")'
    )

    parser.add_argument(
        '--url',
        type=str,
        help='[DEPRECATED] Target URL to crawl (use --keywords instead for automatic search)'
    )

    parser.add_argument(
        '--project',
        type=str,
        help='Project name for this crawl session (auto-generated from keywords if not provided)'
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