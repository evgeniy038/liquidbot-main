"""
Gliquid channel filter - consolidated logic for the gliquid gm channel.

This filter ensures only valid "gliquid" messages are allowed in the gm channel.
Previously this logic was duplicated 3 times in client.py.
"""

import re
from typing import Set, Optional, TYPE_CHECKING

import discord

from src.utils import get_logger

if TYPE_CHECKING:
    from discord import Message, Member

logger = get_logger(__name__)


class GliquidFilter:
    """
    Filter for the gliquid channel - only allows pure "gliquid" messages.
    
    Valid messages must contain "gliquid" and optionally:
    - gm, gn, gl, morning, night, good
    - Emojis (custom or unicode)
    - User mentions
    """
    
    # Channel ID for gliquid channel
    GLIQUID_CHANNEL_ID = 1436228451676848129
    
    # Trusted role IDs that bypass the filter
    TRUSTED_ROLE_IDS: Set[int] = {
        1436799852171235472,  # Staff
        1436767320239243519,  # Mish
        1436233268134678600,  # Automata
        1436217207825629277,  # Moderator
    }
    
    # Allowed words in gliquid messages
    ALLOWED_WORDS: Set[str] = {
        'gliquid', 'gm', 'gn', 'gl', 
        'morning', 'night', 'good'
    }
    
    # Gliquid emoji for reactions
    GLIQUID_EMOJI = "<:gliquid:1443222117318398122>"
    
    def __init__(self):
        """Initialize gliquid filter."""
        pass
    
    def is_gliquid_channel(self, channel_id: int) -> bool:
        """Check if channel is the gliquid channel."""
        return channel_id == self.GLIQUID_CHANNEL_ID
    
    def is_trusted_user(self, member: "Member") -> bool:
        """
        Check if user is trusted (has admin or trusted role).
        
        Args:
            member: Discord member to check
            
        Returns:
            True if user is trusted and bypasses filter
        """
        if not isinstance(member, discord.Member):
            return False
        
        # Check for admin permissions
        if member.guild_permissions.administrator:
            return True
        
        # Check for trusted roles
        user_role_ids = {role.id for role in member.roles}
        return bool(user_role_ids & self.TRUSTED_ROLE_IDS)
    
    def clean_message_content(self, content: str) -> str:
        """
        Clean message content for validation.
        
        Removes:
        - Custom Discord emojis <:name:id> and <a:name:id>
        - Unicode emojis
        - User mentions <@123> and <@!123>
        - Role mentions <@&123>
        - Channel mentions <#123>
        - Punctuation and extra whitespace
        
        Args:
            content: Raw message content
            
        Returns:
            Cleaned content with only words
        """
        clean = content.lower()
        
        # Remove custom Discord emojis (animated and static)
        clean = re.sub(r'<a?:\w+:\d+>', '', clean)
        
        # Remove unicode emojis
        clean = re.sub(
            r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FAFF]', 
            '', 
            clean
        )
        
        # Remove user mentions
        clean = re.sub(r'<@!?\d+>', '', clean)
        
        # Remove role mentions
        clean = re.sub(r'<@&\d+>', '', clean)
        
        # Remove channel mentions
        clean = re.sub(r'<#\d+>', '', clean)
        
        # Remove punctuation and extra whitespace
        clean = re.sub(r'[^\w\s]', '', clean).strip()
        
        return clean
    
    def is_valid_message(self, content: str) -> bool:
        """
        Check if message content is valid for gliquid channel.
        
        Valid messages:
        - Must contain the word "gliquid"
        - Can only contain allowed words (gm, gn, gl, etc.)
        - Emojis and mentions are ignored (allowed)
        
        Args:
            content: Raw message content
            
        Returns:
            True if message is valid
        """
        clean_content = self.clean_message_content(content)
        
        # Empty after cleaning = only emojis/mentions (not valid without gliquid)
        if not clean_content:
            return False
        
        words = clean_content.split()
        
        # Must have at least one word
        if not words:
            return False
        
        # Must contain "gliquid"
        if 'gliquid' not in words:
            return False
        
        # All words must be in allowed list
        return all(word in self.ALLOWED_WORDS for word in words)
    
    async def filter_message(
        self, 
        message: "Message",
        log_prefix: str = ""
    ) -> bool:
        """
        Filter a message in the gliquid channel.
        
        Args:
            message: Discord message to filter
            log_prefix: Prefix for log messages (e.g., "EDIT", "")
            
        Returns:
            True if message was deleted (invalid), False if valid
        """
        # Not gliquid channel - no filtering
        if not self.is_gliquid_channel(message.channel.id):
            return False
        
        # Trusted users bypass filter
        if self.is_trusted_user(message.author):
            return False
        
        # Check if valid
        if self.is_valid_message(message.content):
            # Valid message - add reaction
            try:
                await message.add_reaction(self.GLIQUID_EMOJI)
            except Exception:
                pass
            return False
        
        # Invalid message - delete
        try:
            await message.delete()
            log_type = f"gliquid_filter{log_prefix}"
            logger.info(
                f"🗑️ {log_type} | deleted | @{message.author.name} | "
                f"{message.content[:100]}"
            )
            return True
        except discord.NotFound:
            return True  # Already deleted
        except discord.Forbidden:
            logger.warning(f"gliquid_filter{log_prefix}_no_permission")
            return False
        except Exception as e:
            logger.error(f"gliquid_filter{log_prefix}_error: {e}")
            return False


# Singleton instance
_filter: Optional[GliquidFilter] = None


def get_gliquid_filter() -> GliquidFilter:
    """Get singleton gliquid filter instance."""
    global _filter
    if _filter is None:
        _filter = GliquidFilter()
    return _filter
