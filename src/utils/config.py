"""
Configuration management with environment variable substitution.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()


class DiscordConfig(BaseModel):
    """Discord bot configuration."""
    token: str
    guild_id: str
    command_prefix: str = "!"
    intents: list[str] = Field(default_factory=lambda: ["messages", "guilds", "message_content"])
    allowed_guilds: list[int] = Field(default_factory=list)  # Whitelist of allowed guild IDs


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: str = "openrouter"
    api_key: str
    provisioning_key: Optional[str] = None  # For Analytics API access
    model: str = "x-ai/grok-beta"
    vision_model: Optional[str] = None  # Model for image captions (must support vision)
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    base_url: str = "https://openrouter.ai/api/v1"


class EmbeddingsConfig(BaseModel):
    """Embeddings configuration."""
    provider: str = "openai"
    api_key: str
    model: str = "text-embedding-3-large"
    dimension: int = 3072
    clip_model: str = "openai/clip-vit-large-patch14"
    batch_size: int = 100
    base_url: Optional[str] = None


class VectorDBConfig(BaseModel):
    """Vector database configuration."""
    provider: str = "qdrant"
    url: Optional[str] = None  # For remote Qdrant
    path: Optional[str] = None  # For local storage (no Docker)
    api_key: Optional[str] = None
    collection_prefix: str = "discord_bot"
    distance_metric: str = "cosine"
    
    # Nested configs
    chunking: Dict[str, Any] = Field(default_factory=dict)
    retrieval: Dict[str, Any] = Field(default_factory=dict)


class AutoIndexingConfig(BaseModel):
    """Auto-indexing configuration."""
    enabled: bool = True
    queue_size: int = 1000
    batch_size: int = 50  # Messages per batch for indexing
    batch_timeout: int = 5
    parallel_channels: int = 5  # Max channels to scrape in parallel
    exclude_channels: list[str] = Field(default_factory=list)
    exclude_bots: bool = True
    ignored_categories: list[str] = Field(default_factory=list)  # Discord category IDs to exclude
    scrape_on_startup: bool = True
    scrape_limit_per_channel: Optional[int] = None  # None = scrape all messages


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    file: str = "logs/bot.log"
    rotation: str = "100MB"
    retention: str = "30 days"
    include_fields: list[str] = Field(default_factory=list)
    log_llm_calls: bool = True
    log_rag_retrievals: bool = True
    log_indexing: bool = True


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    langsmith: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class PerformanceConfig(BaseModel):
    """Performance configuration."""
    max_concurrent_requests: int = 10
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_backoff: int = 2
    cache: Dict[str, Any] = Field(default_factory=dict)


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    enabled: bool = True
    requests_per_minute: int = 10
    burst: int = 5


class ModerationConfig(BaseModel):
    """Moderation configuration."""
    enabled: bool = True
    alert_channel_id: str = ""
    check_roles: list[str] = Field(default_factory=list)
    url_whitelist: list[str] = Field(default_factory=list)
    strict_link_filter: Dict[str, Any] = Field(default_factory=dict)
    patterns: Dict[str, Any] = Field(default_factory=dict)
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    actions: Dict[str, Any] = Field(default_factory=dict)


class ReportsConfig(BaseModel):
    """Daily reports configuration."""
    enabled: bool = True
    channel_id: Optional[str] = None
    schedule: Dict[str, int] = Field(default_factory=lambda: {"hour": 5, "minute": 0})
    days_to_analyze: int = 1


class AboutAdditionalEmbedConfig(BaseModel):
    """About command additional embed configuration."""
    title: str
    description: str
    color: int
    image_url: Optional[str] = None   # ✅ ADD THIS

class AboutSectionConfig(BaseModel):
    """About command section configuration."""
    title: str
    description: str
    color: int
    image_url: Optional[str] = None   # ✅ ADD THIS
    additional_embed: Optional[AboutAdditionalEmbedConfig] = None


class AboutFooterConfig(BaseModel):
    """About command footer configuration."""
    text: str = "Liquid Community"
    icon_url: str = ""


class AboutMainConfig(BaseModel):
    """About command main embed configuration."""
    title: str
    description: str
    color: int
    image_url: str = ""


class EventsPingConfig(BaseModel):
    """Events ping button configuration."""
    role_id: str = ""


class AboutCommandConfig(BaseModel):
    """About command configuration."""
    enabled: bool = True
    cooldown_seconds: int = 60
    button_emojis: Dict[str, str] = Field(default_factory=lambda: {
        "links": "🔗",
        "rules": "📜",
        "roles": "🎭",
        "events": "🔔",
    })
    main: AboutMainConfig
    sections: Dict[str, AboutSectionConfig]
    footer: AboutFooterConfig
    events_ping: EventsPingConfig = Field(default_factory=lambda: EventsPingConfig())


class AntiImpersonationConfig(BaseModel):
    """Anti-impersonation configuration."""
    enabled: bool = True
    similarity_threshold: float = 0.75
    hard_threshold: float = 0.90
    log_channel_id: str = ""
    protected_names: list[str] = Field(default_factory=list)
    trusted_role_ids: list[str] = Field(default_factory=list)


class EmbedConfig(BaseModel):
    """Embed configuration for announcements."""
    color: int = 0x00D9FF
    title: str = "⭐️ promotion"
    thumbnail_enabled: bool = True
    image_url: str = ""
    footer_text: str = "Liquid Community"
    footer_icon_url: str = ""


class PromotionsConfig(BaseModel):
    """Promotions configuration."""
    enabled: bool = True
    channel_id: str = ""
    debounce_seconds: int = 5
    promotion_role_ids: list[str] = Field(default_factory=list)
    embed: EmbedConfig = Field(default_factory=lambda: EmbedConfig())


class MemberUpdateConfig(BaseModel):
    """Member update features configuration."""
    anti_impersonation: AntiImpersonationConfig = Field(default_factory=lambda: AntiImpersonationConfig())
    promotions: PromotionsConfig = Field(default_factory=lambda: PromotionsConfig())


class ActivityCheckerConfig(BaseModel):
    """Activity checker configuration."""
    enabled: bool = True
    guild_id: str = ""
    monitored_roles: list[str] = Field(default_factory=list)
    whitelisted_roles: list[str] = Field(default_factory=list)
    min_messages: int = 5
    days_to_check: int = 7
    report_channel_id: str = ""
    schedule: Dict[str, int] = Field(default_factory=lambda: {"hour": 10, "minute": 0})
    embed_color: int = 0xFF6B6B


class NominationsConfig(BaseModel):
    """Nominations configuration."""
    enabled: bool = True
    nomination_channel_id: str = ""
    tweets_search_channel_id: str = ""  # Channel to search for tweets, empty = search all
    allowed_nominator_roles: list[str] = Field(default_factory=list)
    embed_color: int = 0x00D9FF
    footer_text: str = "Vote with ✅ or ❌"


class ContentFilterConfig(BaseModel):
    """Content filter configuration."""
    enabled: bool = True
    filtered_channels: list[str] = Field(default_factory=list)
    whitelisted_roles: list[str] = Field(default_factory=list)
    send_warning: bool = True
    warning_message: str = "{user}, only messages with x.com links or images are allowed in this channel."
    warning_delete_after: int = 5


class ReactAllConfig(BaseModel):
    """React all command configuration."""
    enabled: bool = True
    reactions: list[str] = Field(default_factory=lambda: ["✅", "❌"])
    required_roles: list[str] = Field(default_factory=list)
    message_limit: int = 100
    skip_bot_messages: bool = True


class ContentSubmissionChannelsConfig(BaseModel):
    """Content submission channels configuration."""
    traders: str = ""
    content: str = ""
    designers: str = ""
    approved: str = ""
    spotlight: str = ""


class ContentSubmissionRolesConfig(BaseModel):
    """Content submission roles configuration."""
    t1_voters: list[str] = Field(default_factory=list)
    guild_leads: list[str] = Field(default_factory=list)


class ContentSubmissionsConfig(BaseModel):
    """Content submission system (anti-slop) configuration."""
    enabled: bool = True
    decision_timeout_hours: int = 24
    max_revisions: int = 2
    channels: ContentSubmissionChannelsConfig = Field(default_factory=lambda: ContentSubmissionChannelsConfig())
    roles: ContentSubmissionRolesConfig = Field(default_factory=lambda: ContentSubmissionRolesConfig())
    cooldown_tiers: Dict[str, int] = Field(default_factory=lambda: {
        "2": 6,
        "3": 12,
        "4": 24,
        "5": 48,
    })
    embed_color: int = 0x83C2EB


class Config(BaseModel):
    """Main application configuration."""
    discord: DiscordConfig
    llm: LLMConfig
    embeddings: EmbeddingsConfig
    vector_db: VectorDBConfig
    auto_indexing: AutoIndexingConfig
    logging: LoggingConfig
    monitoring: MonitoringConfig
    performance: PerformanceConfig
    rate_limit: RateLimitConfig
    moderation: ModerationConfig = Field(default_factory=lambda: ModerationConfig())
    reports: ReportsConfig = Field(default_factory=lambda: ReportsConfig())
    about_command: AboutCommandConfig = Field(default_factory=lambda: AboutCommandConfig())
    member_update: MemberUpdateConfig = Field(default_factory=lambda: MemberUpdateConfig())
    activity_checker: ActivityCheckerConfig = Field(default_factory=lambda: ActivityCheckerConfig())
    nominations: NominationsConfig = Field(default_factory=lambda: NominationsConfig())
    content_filter: ContentFilterConfig = Field(default_factory=lambda: ContentFilterConfig())
    react_all: ReactAllConfig = Field(default_factory=lambda: ReactAllConfig())
    content_submissions: ContentSubmissionsConfig = Field(default_factory=lambda: ContentSubmissionsConfig())


class AgentConfig(BaseModel):
    """Agent configuration."""
    name: str
    description: str
    channels: list[str]
    system_prompt: str
    rag_enabled: bool = True
    supports_vision: bool = True
    include_images: bool = True
    max_history: int = 10
    tools: list[str] = Field(default_factory=list)
    response: Dict[str, Any] = Field(default_factory=dict)


class AgentsConfig(BaseModel):
    """Agents configuration."""
    agents: Dict[str, AgentConfig]
    routing: Dict[str, Any]


def load_external_configs(config_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load external configuration files (channels, roles, etc.).
    
    Args:
        config_dir: Directory containing config files
    
    Returns:
        Dictionary with loaded external configs
    """
    external_configs = {}
    
    # Load channels.yaml
    channels_path = config_dir / "channels.yaml"
    if channels_path.exists():
        with open(channels_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            # Extract from nested structure if it exists
            external_configs["channels"] = data.get("channels", data)
            # Also load channel purposes
            external_configs["channel_purposes"] = data.get("channel_purposes", {})
    
    # Load roles.yaml
    roles_path = config_dir / "roles.yaml"
    if roles_path.exists():
        with open(roles_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            # Extract from nested structure if it exists
            external_configs["roles"] = data.get("roles", data)
    
    return external_configs


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """
    Get nested value from dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., 'channels.daily_report')
    
    Returns:
        Value at path or None if not found
    """
    keys = path.split('.')
    value = data
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value


def substitute_config_refs(
    config_dict: Dict[str, Any],
    external_configs: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Recursively substitute configuration references.
    
    Supports ${channels.xxx}, ${roles.xxx} syntax.
    
    Args:
        config_dict: Configuration dictionary
        external_configs: External configuration data
    
    Returns:
        Dictionary with substituted values
    """
    def substitute_value(value: Any) -> Any:
        if isinstance(value, str):
            # Check if the entire string is a single reference
            pattern = r'^\$\{([a-zA-Z_]+)\.([a-zA-Z_.]+)\}$'
            match = re.match(pattern, value)
            
            if match:
                # Entire string is a reference
                config_type = match.group(1)  # e.g., 'channels' or 'roles'
                config_path = match.group(2)  # e.g., 'daily_report' or 'whitelists.activity_exempt'
                
                if config_type in external_configs:
                    full_path = f"{config_type}.{config_path}"
                    nested_value = get_nested_value(external_configs, full_path)
                    
                    if nested_value is not None:
                        # Return the value as-is (list, dict, string, etc.)
                        return nested_value
                
                # Reference not found, return empty string to avoid errors
                return ""
            else:
                # String contains text with possibly embedded references
                # Pattern: ${channels.daily_report} or ${roles.admin}
                pattern = r'\$\{([a-zA-Z_]+)\.([a-zA-Z_.]+)\}'
                
                def replace_match(match):
                    config_type = match.group(1)
                    config_path = match.group(2)
                    
                    if config_type in external_configs:
                        full_path = f"{config_type}.{config_path}"
                        nested_value = get_nested_value(external_configs, full_path)
                        
                        if nested_value is not None:
                            # For embedded references, convert to string
                            return str(nested_value)
                    
                    return match.group(0)  # Return original if not found
                
                return re.sub(pattern, replace_match, value)
        elif isinstance(value, dict):
            return {k: substitute_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [substitute_value(item) for item in value]
        else:
            return value
    
    return substitute_value(config_dict)


def substitute_env_vars(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively substitute environment variables in config.
    
    Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
    
    Args:
        config_dict: Configuration dictionary
    
    Returns:
        Dictionary with substituted values
    """
    def substitute_value(value: Any) -> Any:
        if isinstance(value, str):
            # Pattern: ${VAR_NAME} or ${VAR_NAME:default}
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
            
            def replace_match(match):
                var_name = match.group(1)
                default_value = match.group(2)
                return os.getenv(var_name, default_value or "")
            
            return re.sub(pattern, replace_match, value)
        elif isinstance(value, dict):
            return {k: substitute_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [substitute_value(item) for item in value]
        else:
            return value
    
    return substitute_value(config_dict)


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Dictionary to merge into base
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: str = "config/config.yaml") -> Config:
    """
    Load configuration from YAML file(s).
    
    Supports both single config.yaml and modular config files.
    If config_path points to config.yaml and it doesn't exist,
    will automatically load modular configs from config/ directory.
    
    Args:
        config_path: Path to main config YAML file
    
    Returns:
        Loaded configuration
    """
    config_path = Path(config_path)
    
    # If running from src/ directory, go up one level
    if not config_path.exists() and Path.cwd().name == "src":
        config_path = Path("..") / config_path
    
    # Check if using modular configs
    config_dir = config_path.parent
    modular_configs = [
        config_dir / "discord.yaml",
        config_dir / "llm.yaml",
        config_dir / "database.yaml",
        config_dir / "system.yaml",
        config_dir / "moderation.yaml",
        config_dir / "features.yaml",
    ]
    
    # Use modular configs if they exist
    if all(p.exists() for p in modular_configs):
        # Load and merge all modular configs
        config_dict = {}
        for mod_config in modular_configs:
            with open(mod_config, "r", encoding="utf-8") as f:
                mod_dict = yaml.safe_load(f) or {}
                config_dict = merge_dicts(config_dict, mod_dict)
    elif config_path.exists():
        # Use single config.yaml (backward compatibility)
        with open(config_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
    else:
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Expected either {config_path} or modular configs in {config_dir}/"
        )
    
    # Load external configs (channels, roles)
    external_configs = load_external_configs(config_dir)
    
    # Substitute configuration references (${channels.xxx}, ${roles.xxx})
    config_dict = substitute_config_refs(config_dict, external_configs)
    
    # Substitute environment variables
    config_dict = substitute_env_vars(config_dict)
    
    # Parse with Pydantic
    return Config(**config_dict)


def load_agents_config(
    agents_path: Path = Path("config/agents.yaml")
) -> AgentsConfig:
    """
    Load and parse agents configuration from YAML file.
    
    Args:
        agents_path: Path to agents YAML file
    
    Returns:
        Parsed agents configuration
    """
    with open(agents_path, "r", encoding="utf-8") as f:
        agents_dict = yaml.safe_load(f)
    
    return AgentsConfig(**agents_dict)


# Singleton instance
_config: Optional[Config] = None
_agents_config: Optional[AgentsConfig] = None
_channel_purposes: Optional[Dict[str, str]] = None


def get_config() -> Config:
    """Get singleton config instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_agents_config() -> AgentsConfig:
    """Get singleton agents config instance."""
    global _agents_config
    if _agents_config is None:
        _agents_config = load_agents_config()
    return _agents_config


def get_channel_purposes() -> Dict[str, str]:
    """
    Get channel purposes mapping (channel_id -> description).
    
    Returns:
        Dictionary mapping channel IDs to their purpose descriptions
    """
    global _channel_purposes
    if _channel_purposes is None:
        config_dir = Path("config")
        if not config_dir.exists() and Path.cwd().name == "src":
            config_dir = Path("..") / "config"
        external_configs = load_external_configs(config_dir)
        _channel_purposes = external_configs.get("channel_purposes", {})
        
        # Log loaded channel purposes
        if _channel_purposes:
            print(f"📍 Loaded {len(_channel_purposes)} channel purposes from config")
            for channel_id, purpose in list(_channel_purposes.items())[:5]:
                print(f"   • <#{channel_id}>: {purpose[:50]}...")
            if len(_channel_purposes) > 5:
                print(f"   • ... and {len(_channel_purposes) - 5} more")
    return _channel_purposes
