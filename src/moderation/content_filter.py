"""
Content filter for specific channels.

Features:
- Per-channel content rules
- Contributions channel: only x.com links allowed
- Content channel: only attachments allowed (no links)
- Configurable whitelist
"""

import re
from typing import List, Optional, Tuple

import discord

from src.utils import get_logger

logger = get_logger(__name__)

# Channel-specific rules
CHANNEL_RULES = {
    # Contributions channel: only x.com links allowed
    "1436229572403400887": {
        "rule": "x_links_only",
        "warning": "{user}, only **x.com links** are allowed in this channel.",
    },
    # Content channel: only attachments allowed, no links
    "1441524601187467404": {
        "rule": "attachments_only",
        "warning": "{user}, only **attachments (images/videos)** are allowed in this channel. no links.",
    },
}


class ContentFilter:
    """
    Filter messages in specific channels with per-channel rules.
    
    Rules:
    - x_links_only: Only x.com/twitter.com links allowed
    - attachments_only: Only attachments allowed, no links
    - default: x.com links OR images allowed
    """
    
    def __init__(self, bot: discord.Client, config: dict):
        """
        Initialize content filter.
        
        Args:
            bot: Discord bot instance
            config: Configuration dictionary
        """
        self.bot = bot
        self.config = config
        
        # Compile regex pattern for x.com and twitter.com links
        self.twitter_pattern = re.compile(
            r'https?://(twitter\.com|x\.com)/\S+',
            re.IGNORECASE
        )
        
        # Pattern to detect any URL
        self.url_pattern = re.compile(
            r'https?://\S+',
            re.IGNORECASE
        )
        
        # Silent init
    
    async def check_message(self, message: discord.Message) -> Tuple[bool, Optional[str]]:
        """
        Check if a message should be allowed in filtered channels.
        
        Args:
            message: Discord message
        
        Returns:
            Tuple of (should_delete, warning_message)
        """
        # Check if filter is enabled
        if not self.config.get("enabled", False):
            return False, None
        
        # Don't delete bot messages
        if message.author.bot:
            return False, None
        
        # Check if message is in a filtered channel
        filtered_channels = self.config.get("filtered_channels", [])
        channel_id_str = str(message.channel.id)
        
        if channel_id_str not in filtered_channels:
            return False, None
        
        # Check if user has whitelisted role
        if hasattr(message.author, 'roles'):
            whitelisted_roles = self.config.get("whitelisted_roles", [])
            user_role_ids = [str(role.id) for role in message.author.roles]
            
            if any(role_id in whitelisted_roles for role_id in user_role_ids):
                logger.debug(
                    "message_allowed_whitelisted_role",
                    user_id=str(message.author.id),
                    channel_id=str(message.channel.id),
                )
                return False, None
        
        # Get channel-specific rule
        channel_rule = CHANNEL_RULES.get(channel_id_str, {})
        rule_type = channel_rule.get("rule", "default")
        custom_warning = channel_rule.get("warning")
        
        # Check content based on rule type
        should_delete, warning = self._check_by_rule(message, rule_type, custom_warning)
        
        if should_delete:
            logger.info(
                "message_filtered",
                message_id=str(message.id),
                author_id=str(message.author.id),
                author_name=message.author.name,
                channel_id=str(message.channel.id),
                rule=rule_type,
                content_preview=message.content[:100] if message.content else "",
            )
        
        return should_delete, warning
    
    def _check_by_rule(
        self, 
        message: discord.Message, 
        rule_type: str,
        custom_warning: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check message against specific rule type.
        
        Args:
            message: Discord message
            rule_type: Type of rule to apply
            custom_warning: Custom warning message
            
        Returns:
            Tuple of (should_delete, warning_message)
        """
        has_twitter_link = bool(self.twitter_pattern.search(message.content))
        has_any_link = bool(self.url_pattern.search(message.content))
        
        has_attachment = bool(message.attachments)
        has_image = any(
            attachment.content_type and attachment.content_type.startswith('image/')
            for attachment in message.attachments
        )
        has_video = any(
            attachment.content_type and attachment.content_type.startswith('video/')
            for attachment in message.attachments
        )
        
        default_warning = self.config.get(
            "warning_message",
            "{user}, only messages with x.com links or images are allowed in this channel."
        )
        
        if rule_type == "x_links_only":
            # Only x.com/twitter.com links allowed
            if has_twitter_link:
                return False, None
            
            warning = custom_warning or "{user}, only **x.com links** are allowed in this channel."
            return True, warning
        
        elif rule_type == "attachments_only":
            # Only attachments allowed, no links at all
            if has_any_link:
                warning = custom_warning or "{user}, only **attachments** are allowed in this channel. no links."
                return True, warning
            
            if has_attachment:
                return False, None
            
            # No attachments and no valid content
            warning = custom_warning or "{user}, only **attachments (images/videos)** are allowed in this channel."
            return True, warning
        
        else:
            # Default rule: x.com links OR images allowed
            has_embed_image = any(
                embed.type == 'image' or embed.image or embed.thumbnail
                for embed in message.embeds
            )
            
            if has_twitter_link or has_image or has_embed_image:
                return False, None
            
            return True, default_warning
    
    async def filter_message(self, message: discord.Message):
        """
        Filter a message (delete if it doesn't meet criteria).
        
        Args:
            message: Discord message
        """
        try:
            should_delete, warning_text = await self.check_message(message)
            
            if should_delete:
                # Send warning message (optional)
                if self.config.get("send_warning", True) and warning_text:
                    # Replace {user} placeholder with mention
                    warning_message = warning_text.replace("{user}", message.author.mention)
                    
                    warning = await message.channel.send(warning_message)
                    
                    # Delete warning after delay
                    delete_after = self.config.get("warning_delete_after", 5)
                    if delete_after > 0:
                        await warning.delete(delay=delete_after)
                
                # Delete the original message
                await message.delete()
                
                logger.info(
                    "message_deleted",
                    message_id=str(message.id),
                    author_id=str(message.author.id),
                    channel_id=str(message.channel.id),
                )
        
        except discord.Forbidden:
            logger.error(
                "missing_permissions_to_delete",
                message_id=str(message.id),
                channel_id=str(message.channel.id),
            )
        
        except Exception as e:
            logger.error(
                "filter_message_failed",
                error=str(e),
                message_id=str(message.id),
                channel_id=str(message.channel.id),
            )
