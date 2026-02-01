"""
Beautiful colored logging for console output.
"""

import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Colored formatter for beautiful console logs."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Event emoji
    EMOJI = {
        'bot_starting': '🚀',
        'bot_ready': '✅',
        'bot_stopped': '⏹️',
        'message_received': '📨',
        'searching_rag': '🔍',
        'rag_retrieval': '📚',
        'no_rag_results': '⚠️',
        'generating_llm_response': '🤖',
        'response_sent': '✉️',
        'message_handling_error': '❌',
        'openrouter_http_error': '🚫',
    }
    
    def format(self, record):
        """Format log record with colors."""
        # Get color for level
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format time
        time_str = self.formatTime(record, '%H:%M:%S')
        
        # Get emoji for event
        event = getattr(record, 'event', '')
        emoji = self.EMOJI.get(event, '')
        
        # Build message parts
        parts = []
        
        # Time and level
        parts.append(f"{color}{time_str} [{record.levelname:8}]{self.RESET}")
        
        # Logger name (shortened)
        logger_name = record.name.split('.')[-1]
        parts.append(f"{self.BOLD}{logger_name}{self.RESET}")
        
        # Emoji if available
        if emoji:
            parts.append(emoji)
        
        # Event name
        if event:
            parts.append(f"{color}{event}{self.RESET}")
        
        # Additional data - show important fields
        extra_data = {}
        skip_keys = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName', 
            'levelname', 'levelno', 'lineno', 'module', 'msecs', 
            'message', 'pathname', 'process', 'processName', 
            'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'logger', '_logger', '_name',
            'taskName', 'event'  # Skip event as we show it separately
        }
        
        for key, value in record.__dict__.items():
            if key not in skip_keys and not key.startswith('_'):
                # Format value appropriately
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + '...'
                extra_data[key] = value
        
        # Format extra data with colors
        if extra_data:
            data_parts = []
            for k, v in extra_data.items():
                if k in ['error', 'detail', 'exception']:
                    # Errors in red
                    data_parts.append(f"{self.COLORS['ERROR']}{k}={v}{self.RESET}")
                elif k in ['status_code', 'response_length', 'tokens_used', 'latency_ms']:
                    # Important metrics highlighted
                    data_parts.append(f"{self.BOLD}{k}={v}{self.RESET}")
                elif k in ['model', 'query', 'author', 'channel']:
                    # Key context in cyan
                    data_parts.append(f"{self.COLORS['DEBUG']}{k}={v}{self.RESET}")
                else:
                    data_parts.append(f"{k}={v}")
            
            data_str = ' '.join(data_parts)
            parts.append(f"({data_str})")
        
        # Exception info
        if record.exc_info:
            parts.append(f"\n{self.formatException(record.exc_info)}")
        
        return ' '.join(parts)


def setup_colored_logging(log_level: str = "INFO"):
    """
    Setup beautiful colored logging.
    
    Args:
        log_level: Logging level
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)
    
    # Silence noisy libraries
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
