"""
CLI argument parsing utilities for AutoData.

This module contains functions for parsing command-line arguments and setting up CLI options.
"""

import argparse
from pathlib import Path
from typing import Optional
from argparse import Namespace


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for AutoData CLI.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="AutoData - Automated Web Data Collection",
        prog="autodata",
        epilog="For more information, visit the documentation.",
    )

    parser.add_argument(
        "instruction", help="User instruction for data collection", type=str
    )

    parser.add_argument(
        "--config", type=Path, help="Path to configuration file", metavar="FILE"
    )

    parser.add_argument(
        "--env-path",
        dest="env_path",
        type=Path,
        help="Path to .env file containing API keys and environment variables (default: .env in current directory)",
        metavar="FILE",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: %(default)s)",
    )

    parser.add_argument(
        "--output", type=Path, help="Output directory for collected data", metavar="DIR"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    return parser


def parse_arguments(args: Optional[list] = None) -> Namespace:
    """
    Parse command-line arguments.

    Args:
        args: List of arguments to parse. If None, uses sys.argv

    Returns:
        Namespace: Parsed arguments
    """
    parser = create_parser()
    return parser.parse_args(args)


def validate_arguments(args: Namespace) -> None:
    """
    Validate parsed arguments and perform any necessary checks.

    Args:
        args: Parsed arguments namespace

    Raises:
        ValueError: If arguments are invalid
    """
    # Validate config file exists if provided
    if args.config and not args.config.exists():
        raise ValueError(f"Configuration file not found: {args.config}")

    # Validate env file exists if provided
    if hasattr(args, "env_path") and args.env_path and not args.env_path.exists():
        raise ValueError(f"Environment file not found: {args.env_path}")

    # Validate output directory is writable if provided
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        if not args.output.is_dir():
            raise ValueError(f"Output path is not a directory: {args.output}")

    # Validate instruction is not empty
    if not args.instruction.strip():
        raise ValueError("Instruction cannot be empty")
