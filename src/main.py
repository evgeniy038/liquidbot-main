"""
Liquid Discord Multimodal Bot - Main Entry Point

Features:
- Multi-agent system with channel routing
- Multimodal RAG (text + images)
- Automatic prompt caching
- Real-time indexing
"""

import argparse
import asyncio
from pathlib import Path

from src.utils import get_config, get_logger, setup_logging

logger = get_logger(__name__)


async def main():
    """Main application entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Liquid Discord Multimodal Bot")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="Path to configuration file",
    )
    args = parser.parse_args()
    
    # Setup logging with structlog (colored, detailed)
    setup_logging(
        log_level=args.log_level,
        log_file=Path("logs/bot.log"),
        json_format=False,
    )
    
    logger.info(
        "bot_starting",
        log_level=args.log_level,
        config_path=str(args.config),
    )
    
    try:
        # Load configuration
        config = get_config()
        
        logger.info(
            "configuration_loaded",
            discord_guild=config.discord.guild_id,
            llm_model=config.llm.model,
            vector_db=config.vector_db.provider,
        )
        
        # Import and run bot
        from src.bot.client import run_bot
        
        logger.info("starting_discord_bot")
        
        # Run bot
        await run_bot()
        
    except KeyboardInterrupt:
        logger.info("bot_shutdown_requested")
    
    except Exception as e:
        logger.error(
            "bot_error",
            error=str(e),
            exc_info=True,
        )
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        pass
