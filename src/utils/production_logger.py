"""
Production-ready simplified logging with emoji-oriented output.
Clean, readable logs for production environment.
"""

import os
import structlog
from colorama import Fore, Style


# Production mode flag
PRODUCTION_MODE = os.getenv("PRODUCTION_MODE", "true").lower() == "true"


def production_console_renderer(logger, name, event_dict):
    """
    Ultra-clean console renderer for production.
    Shows only essential information with clear emojis.
    """
    event = event_dict.pop("event", "")
    timestamp = event_dict.pop("timestamp", "")
    
    # Remove unnecessary fields
    for key in ["level", "logger", "log_level"]:
        event_dict.pop(key, None)
    
    # Build clean output
    parts = []
    
    # Timestamp (with seconds)
    time_short = timestamp.split(":")[0:3]
    parts.append(f"{Fore.BLUE}{':'.join(time_short)}{Style.RESET_ALL}")
    
    # Event with emoji
    parts.append(f"{Style.BRIGHT}{event}{Style.RESET_ALL}")
    
    # Only show critical fields
    if event_dict:
        info_parts = []
        
        # Agent info
        if "agent" in event_dict or "agent_name" in event_dict:
            agent = event_dict.get("agent") or event_dict.get("agent_name")
            info_parts.append(f"{Fore.CYAN}{agent}{Style.RESET_ALL}")
        
        # Query (truncated)
        if "query" in event_dict:
            query = event_dict["query"]
            if len(query) > 30:
                query = query[:30] + "..."
            info_parts.append(f'"{query}"')
        
        # Channel
        if "channel" in event_dict:
            info_parts.append(f"#{event_dict['channel']}")
        
        # Error
        if "error" in event_dict:
            error = event_dict["error"]
            if len(error) > 50:
                error = error[:50] + "..."
            info_parts.append(f"{Fore.RED}{error}{Style.RESET_ALL}")
        
        # Results count (RAG)
        if "results_count" in event_dict:
            count = event_dict["results_count"]
            if count > 0:
                info_parts.append(f"{Fore.GREEN}{count} results{Style.RESET_ALL}")
        
        # Response length
        if "response_length" in event_dict:
            length = event_dict["response_length"]
            info_parts.append(f"{length} chars")
        
        # Model (only for LLM calls)
        if "model" in event_dict and "llm" in event:
            model = event_dict["model"].split("/")[-1]  # Just model name
            info_parts.append(f"{Fore.YELLOW}{model}{Style.RESET_ALL}")
        
        # Tokens (compact format)
        if "prompt_tokens" in event_dict and "completion_tokens" in event_dict:
            prompt = event_dict["prompt_tokens"]
            completion = event_dict["completion_tokens"]
            info_parts.append(f"{Fore.YELLOW}{prompt}→{completion} tokens{Style.RESET_ALL}")
        
        if info_parts:
            parts.append(f"| {' | '.join(info_parts)}")
    
    return " ".join(parts)


def development_console_renderer(logger, name, event_dict):
    """
    Detailed console renderer for development.
    Shows more technical details.
    """
    level = event_dict.pop("level", "info").upper()
    event = event_dict.pop("event", "")
    timestamp = event_dict.pop("timestamp", "")
    
    # Remove logger field
    event_dict.pop("logger", None)
    
    # Build the log line
    parts = []
    
    # Timestamp
    parts.append(f"{Fore.BLUE}{timestamp}{Style.RESET_ALL}")
    
    # Event
    parts.append(f"{Style.BRIGHT}{event}{Style.RESET_ALL}")
    
    # Show all fields in compact format
    important_fields = {
        "agent", "agent_name", "query", "channel", "channel_id",
        "results_count", "response_length", "error", "model",
        "prompt_tokens", "completion_tokens", "latency_ms", "tools",
        "user_id", "message_id"
    }
    
    if event_dict:
        compact_parts = []
        for key, value in event_dict.items():
            if key.startswith("_") or key not in important_fields:
                continue
            
            # Format value
            if isinstance(value, str):
                if len(value) > 50:
                    value = value[:50] + "..."
                value = f'"{value}"'
            elif isinstance(value, list):
                if len(value) > 3:
                    value = f"[{len(value)} items]"
                else:
                    value = str(value)
            
            # Color code
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


# Enhanced emoji map for production - CLEAN startup logs
PRODUCTION_EMOJI_MAP = {
    # Bot lifecycle (essential)
    "bot_starting": "🚀 Starting Luma",
    "bot_ready": "",  # Skip - we have custom log in on_ready
    "bot_stopped": "⏹️ Bot stopped",
    "bot_error": "❌ Bot error",
    "bot_cancelled": "",  # Skip
    "bot_interrupted": "",  # Skip
    "bot_shutting_down": "",  # Skip - redundant
    "bot_closed": "",  # Skip - redundant
    
    # Configuration (minimal)
    "configuration_loaded": "⚙️ Config loaded",
    
    # Skip ALL component initialization logs - too verbose for startup
    "starting_discord_bot": "",  # Skip
    "discord_bot_initialized": "",  # Skip
    "setting_up_bot_components": "",  # Skip
    "bot_components_ready": "",  # Skip
    
    # Skip embedders/indexers during startup
    "text_embedder_initialized": "",  # Skip
    "image_embedder_initialized": "",  # Skip
    "multimodal_embedder_initialized": "",  # Skip
    "openrouter_client_initialized": "",  # Skip
    "qdrant_client_initialized": "",  # Skip
    "multimodal_indexer_initialized": "",  # Skip
    "hybrid_retriever_initialized": "",  # Skip
    
    # Skip agents init logs
    "loading_agent_config": "",  # Skip
    "agent_config_loaded": "",  # Skip
    "creating_agent": "",  # Skip
    "agent_initialized": "",  # Skip
    "general_agent_initialized": "",  # Skip
    "agent_created": "",  # Skip
    "agent_factory_initialized": "",  # Skip
    
    # Skip other init logs
    "ai_router_initialized": "",  # Skip
    "pattern_matcher_initialized": "",  # Skip
    "ai_analyzer_initialized": "",  # Skip
    "scam_detector_initialized": "",  # Skip
    "scam_detector_enabled": "",  # Skip
    "alert_sender_initialized": "",  # Skip
    "message_analytics_initialized": "",  # Skip
    "user_history_check_enabled": "",  # Skip
    "channel_reader_initialized": "",  # Skip
    "channel_reader_set_on_general_agent": "",  # Skip
    "channel_reader_set_on_agents": "",  # Skip
    "persistent_scam_view_registered": "",  # Skip
    "content_filter_initialized": "",  # Skip
    "strict_link_filter_enabled": "",  # Skip
    "avatar_set": "",  # Skip
    
    # Important runtime logs
    "message_received": "📨 New message",
    "routing_to_agent": "➡️ Routing",
    "agent_processing_message": "⚙️ Processing",
    
    # RAG operations (minimal)
    "searching_rag": "🔍 Searching",
    "rag_retrieval": "",  # Skip
    "collections_determined": "",  # Skip
    "starting_parallel_search": "",  # Skip
    "searching_collection": "",  # Skip
    "collection_search_completed": "",  # Skip
    "rag_results_found": "",  # Skip - too verbose
    "no_rag_results": "",  # Skip
    
    # Indexing (minimal for scraper)
    "text_indexed": "",  # Skip
    "image_indexed": "",  # Skip
    "document_indexed": "",  # Skip in production
    
    # LLM (essential)
    "generating_llm_response": "",  # Skip
    "llm_request_completed": "✨ Generated",
    
    # Response (essential)
    "agent_response_generated": "✅ Response ready",
    "response_sent_successfully": "",  # Skip - redundant
    
    # Errors (always show)
    "message_handling_error": "❌ Error",
    "openrouter_http_error": "🚫 API error",
    "caption_generation_failed": "",  # Skip
    
    # Scraping (minimal)
    "scraping_guild_started": "",  # Skip
    "channel_scraping_started": "",  # Skip
    "channel_scraping_completed": "",  # Skip
    "channel_skipped_no_permissions": "",  # Skip
    "scraper_progress_saved": "",  # Skip
    "scraping_completed": "📊 Scraping done",
    
    # Database/SQLite
    "MESSAGE_SAVED_TO_DB": "",  # Skip
    "IMAGE_SAVED_TO_DB": "",  # Skip
    "HISTORICAL_IMAGE_SAVED": "",  # Skip
    
    # Daily report scheduler
    "daily_report_scheduler_started": "",  # Skip
    "daily_report_scheduler_cancelled": "",  # Skip
    "activity_check_scheduler_started": "",  # Skip
    "activity_check_scheduler_cancelled": "",  # Skip
    
    # OpenRouter client
    "openrouter_client_closed": "",  # Skip
    
    # Announcement indexer
    "announcement_indexer_initialized": "",  # Skip
    
    # Scraper logs (all skipped for cleaner startup)
    "BATCH_INDEXED_SQLITE": "📦 Batch indexed",
    "MESSAGE_SAVED_SQLITE": "💾 Saved msg",
    "background_scraper_starting": "📚 Scraper started",
}


def add_production_emoji_processor(logger, method_name, event_dict):
    """Add emojis and filter events for production mode."""
    event = event_dict.get("event", "")
    
    if PRODUCTION_MODE:
        # Get production-friendly message
        emoji_message = PRODUCTION_EMOJI_MAP.get(event, event)
        
        # Skip empty events (filtered out)
        if not emoji_message:
            # Return None to skip this log entry
            event_dict["_skip"] = True
            return event_dict
        
        event_dict["event"] = emoji_message
    else:
        # Development mode: use simple emoji map
        simple_emoji_map = {
            "bot_starting": "🚀",
            "bot_ready": "✅",
            "message_received": "📨",
            "searching_rag": "🔍",
            "rag_retrieval": "📚",
            "llm_request_completed": "✨",
            "response_sent_successfully": "✉️",
            "message_handling_error": "❌",
            "openrouter_http_error": "🚫",
        }
        
        emoji = simple_emoji_map.get(event, "")
        if emoji:
            event_dict["event"] = f"{emoji} {event}"
    
    return event_dict


def skip_processor(logger, method_name, event_dict):
    """Skip log entries marked for skipping."""
    if event_dict.get("_skip"):
        raise structlog.DropEvent
    return event_dict


def console_print(*args, **kwargs):
    """
    Production-aware console print.
    Only prints if in development mode.
    """
    if not PRODUCTION_MODE:
        print(*args, **kwargs)
