"""
Structured logging configuration with JSON formatting and usage metrics tracking.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger
from colorama import init, Fore, Back, Style

from src.utils.color_logger import ColoredFormatter
from src.utils.production_logger import (
    PRODUCTION_MODE,
    production_console_renderer,
    development_console_renderer,
    add_production_emoji_processor,
    skip_processor,
)

# Initialize colorama for Windows color support
init(autoreset=True)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        if not log_record.get("timestamp"):
            log_record["timestamp"] = self.formatTime(record, self.datefmt)
        
        # Add level name
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


# Custom processor to add emojis
def add_emoji_processor(logger, method_name, event_dict):
    """Add emojis to log events for better readability."""
    emoji_map = {
        "bot_starting": "🚀",
        "bot_ready": "✅",
        "bot_stopped": "⏹️",
        "bot_shutdown_requested": "🛑",
        "bot_error": "❌",
        "configuration_loaded": "⚙️",
        "setting_up_bot_components": "🔧",
        "bot_components_ready": "✅",
        "starting_discord_bot": "🤖",
        "message_received": "📨",
        "routing_to_agent": "🔀",
        "agent_processing_message": "⚙️",
        "searching_rag": "🔍",
        "rag_retrieval": "📚",
        "no_rag_results": "⚠️",
        "generating_llm_response": "🤖",
        "llm_request_completed": "✨",
        "response_sent_successfully": "✉️",
        "message_handling_error": "❌",
        "openrouter_http_error": "🚫",
        "document_indexed": "📝",
    }
    
    event = event_dict.get("event", "")
    if event in emoji_map:
        event_dict["event"] = f"{emoji_map[event]} {event}"
    
    return event_dict


def custom_console_renderer(logger, name, event_dict):
    """Custom console renderer with clean, brief formatting."""
    level = event_dict.pop("level", "info").upper()
    event = event_dict.pop("event", "")
    timestamp = event_dict.pop("timestamp", "")
    
    # Remove logger field - not needed in output
    event_dict.pop("logger", None)
    
    # Color mapping
    level_colors = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA + Style.BRIGHT,
    }
    
    color = level_colors.get(level, Fore.WHITE)
    
    # Build the log line - BRIEF format
    parts = []
    
    # Timestamp
    parts.append(f"{Fore.BLUE}{timestamp}{Style.RESET_ALL}")
    
    # Event (main message)
    parts.append(f"{Style.BRIGHT}{event}{Style.RESET_ALL}")
    
    # Only show most important fields in compact format
    important_fields = {
        "agent", "agent_name", "query", "channel", "channel_id",
        "results_count", "response_length", "error", "model",
        "prompt_tokens", "completion_tokens", "latency_ms", "tools"
    }
    
    if event_dict:
        compact_parts = []
        for key, value in event_dict.items():
            # Skip internal and verbose fields
            if key.startswith("_") or key not in important_fields:
                continue
            
            # Format value - keep it short
            if isinstance(value, str):
                if len(value) > 50:
                    value = value[:50] + "..."
                # Escape special chars
                value = f'"{value}"'
            elif isinstance(value, list):
                if len(value) > 3:
                    value = f"[{len(value)} items]"
                else:
                    value = str(value)
            
            # Color code by importance
            if key in ["error"]:
                compact_parts.append(f"{Fore.RED}{key}={value}{Style.RESET_ALL}")
            elif key in ["agent", "agent_name", "model"]:
                compact_parts.append(f"{Fore.CYAN}{key}={value}{Style.RESET_ALL}")
            elif key in ["prompt_tokens", "completion_tokens", "latency_ms"]:
                compact_parts.append(f"{Fore.YELLOW}{key}={value}{Style.RESET_ALL}")
            else:
                compact_parts.append(f"{key}={value}")
        
        if compact_parts:
            parts.append(f"| {' | '.join(compact_parts)}")
    
    return " ".join(parts)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        json_format: Use JSON formatting if True, else use plain text
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Choose renderer based on production mode
    console_renderer = production_console_renderer if PRODUCTION_MODE else development_console_renderer
    emoji_processor = add_production_emoji_processor if PRODUCTION_MODE else add_emoji_processor
    
    # Build processor list
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%H:%M:%S"),
        emoji_processor,  # Add emojis (production or development)
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Add skip processor if production mode
    if PRODUCTION_MODE:
        processors.append(skip_processor)
    
    # Add final renderer
    processors.append(console_renderer)
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()  # Clear existing handlers
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        root_logger.addHandler(file_handler)
    
    # Silence noisy libraries
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.ERROR)
    logging.getLogger("discord.client").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Suppress PyNaCl warning from discord.py
    import warnings
    warnings.filterwarnings("ignore", message="PyNaCl is not installed")
    
    # Print startup banner
    mode_str = "PRODUCTION MODE" if PRODUCTION_MODE else "DEVELOPMENT MODE"
    mode_color = Fore.GREEN if PRODUCTION_MODE else Fore.YELLOW
    
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{Style.BRIGHT}{'💧 LIQUID DISCORD BOT':^80}{Style.RESET_ALL}")
    print(f"{mode_color}{Style.BRIGHT}{mode_str:^80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


# Convenience functions for common log events

def log_llm_request(
    logger: structlog.BoundLogger,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0,
    total_tokens: int = 0,
    cost_usd: float = 0.0,
    cache_discount_usd: float = 0.0,
    latency_ms: float = 0.0,
    **extra
) -> None:
    """Log LLM request with usage metrics."""
    logger.info(
        "llm_request_completed",
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cached_tokens=cached_tokens,
        total_tokens=total_tokens or (prompt_tokens + completion_tokens),
        cost_usd=cost_usd,
        cache_discount_usd=cache_discount_usd,
        latency_ms=latency_ms,
        **extra
    )


def log_rag_retrieval(
    logger: structlog.BoundLogger,
    query: str,
    channel_id: str,
    results_count: int,
    text_chunks: int = 0,
    images_found: int = 0,
    latency_ms: float = 0.0,
    **extra
) -> None:
    """Log RAG retrieval operation."""
    logger.info(
        "rag_retrieval",
        query=query,
        channel_id=channel_id,
        results_count=results_count,
        text_chunks=text_chunks,
        images_found=images_found,
        latency_ms=latency_ms,
        **extra
    )


def log_document_indexed(
    logger: structlog.BoundLogger,
    message_id: str,
    channel_id: str,
    chunks_created: int = 0,
    images_indexed: int = 0,
    processing_time_ms: float = 0.0,
    **extra
) -> None:
    """Log document indexing operation."""
    logger.info(
        "document_indexed",
        message_id=message_id,
        channel_id=channel_id,
        chunks_created=chunks_created,
        images_indexed=images_indexed,
        processing_time_ms=processing_time_ms,
        **extra
    )


def log_agent_response(
    logger: structlog.BoundLogger,
    agent_name: str,
    channel_id: str,
    user_id: str,
    query_length: int,
    response_length: int,
    images_returned: int = 0,
    latency_ms: float = 0.0,
    **extra
) -> None:
    """Log agent response."""
    logger.info(
        "agent_response",
        agent_name=agent_name,
        channel_id=channel_id,
        user_id=user_id,
        query_length=query_length,
        response_length=response_length,
        images_returned=images_returned,
        latency_ms=latency_ms,
        **extra
    )
