"""
Main.py - Entry point cho AutoData system (Async version).
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import config
from core.auto import run_workflow_async
from utils.logging import setup_logging
from utils.cli import parse_arguments


def main():
    """Main function"""

    # Setup logging
    logger = setup_logging()

    logger.info("=" * 80)
    logger.info("AutoData - AI Agent Crawler System")
    logger.info("=" * 80)

    # Parse arguments
    args = parse_arguments()

    # Display configuration if requested
    if args.show_config:
        config.display_config()
        return

    # Validate configuration
    if not config.validate_config():
        logger.error("Configuration validation failed. Please check your setup.")
        return

    # Get target URL and project name
    target_url = args.url or "https://mst.gov.vn/van-ban-phap-luat/du-thao/2256.htm"
    project_name = args.project or "Luật Khoa học, công nghệ và đổi mới sáng tạo 2025"

    logger.info(f"Target URL: {target_url}")
    logger.info(f"Project Name: {project_name}")

    try:
        # Run workflow asynchronously
        logger.info("Running workflow asynchronously...")
        final_state = asyncio.run(run_workflow_async(target_url, project_name))

        # Display results
        logger.info("=" * 80)
        logger.info(" Workflow completed successfully!")
        logger.info("=" * 80)

        # Show key results
        if final_state.get('csv_output_path'):
            logger.info(f" CSV Output: {final_state['csv_output_path']}")

        if final_state.get('pdf_local_path'):
            logger.info(f" PDF Downloaded: {final_state['pdf_local_path']}")

        comments_count = len(final_state.get('collected_comments', []))
        logger.info(f" Comments Collected: {comments_count}")

        if final_state.get('vector_db_collection'):
            logger.info(f" Vector DB Collection: {final_state['vector_db_collection']}")

        # Show errors if any
        errors = final_state.get('errors', [])
        if errors:
            logger.warning(f" Errors encountered: {len(errors)}")
            for error in errors[:5]:  # Show first 5 errors
                logger.warning(f"  - {error.get('message')}")

        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.info("\n Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f" Workflow failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
