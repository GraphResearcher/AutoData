"""
Main entry point for the AutoData package.

This module implements the core workflow of the multi-agent system for automated web data collection.
"""

import sys
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import asyncio

sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)

from autodata.core.auto import AutoData
from autodata.utils.cli import parse_arguments, validate_arguments


def debug_test_run():
    """Debug test function for development and testing purposes."""
    print("🔧 DEBUG MODE: Running test scenario...")

    # Mock arguments for testing
    class TestArgs:
        instruction = "Collect a dataset that contains all accepted papers from the Association for Computational Linguistics (ACL 2024)."
        config = None
        log_level = "DEBUG"
        output = Path("autodata/test_output")
        verbose = True
        env_path = None  # Will use default .env lookup

    try:
        args = TestArgs()
        validate_arguments(args)

        print(f"✅ Test instruction: {args.instruction}")
        print(f"✅ Log level: {args.log_level}")
        print(f"✅ Output directory: {args.output}")
        print(f"✅ Verbose mode: {args.verbose}")
        print(f"✅ Environment file: {args.env_path or 'Auto-detect'}")

        # Initialize AutoData with test arguments
        autodata = AutoData(
            config_path=args.config,
            log_level=args.log_level,
            output_dir=args.output,
            verbose=args.verbose,
            env_path=args.env_path,
        )

        print("🚀 Starting AutoData test run...")
        results = asyncio.run(autodata.arun(args.instruction))

        print("📊 Test Results:")
        print(f"Status: {results.get('status', 'unknown')}")
        if results.get("status") == "success":
            print("✅ Test completed successfully!")
            print(results.get("results", "No results"))
        else:
            print(f"❌ Test failed: {results.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Debug test error: {e}")
        logger.exception("Debug test failed")


def main():
    """Main entry point for the AutoData CLI."""
    try:
        # Parse and validate command-line arguments
        args = parse_arguments()
        validate_arguments(args)

        # Initialize AutoData with parsed arguments
        autodata = AutoData(
            config_path=args.config,
            log_level=args.log_level,
            output_dir=getattr(args, "output", None),
            verbose=getattr(args, "verbose", False),
            env_path=getattr(args, "env_path", None),
        )

        # Run the data collection process
        results = autodata.run(args.instruction)

        # Handle results
        if results["status"] == "success":
            print("Data collection completed successfully!")
            print("\nResults:")
            print(results["results"])
        else:
            print(f"Error: {results['error']}")
            sys.exit(1)

    except ValueError as e:
        print(f"Invalid arguments: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Debug test mode - uncomment the line below to run debug test instead of main
    debug_test_run()
    #main()
