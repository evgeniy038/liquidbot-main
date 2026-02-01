"""
Channel reader tool for reading recent messages from Discord channels.
"""

from typing import List, Dict, Optional
import discord
from datetime import datetime

from src.utils import get_logger

logger = get_logger(__name__)


class ChannelReader:
    """
    Tool for reading recent messages from Discord channels.
    
    Allows the bot to fetch and summarize recent channel activity.
    """
    
    def __init__(self, bot: discord.Client):
        """
        Initialize channel reader.
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
    
    async def read_recent_messages(
        self,
        channel_id: int,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """
        Read recent messages from a channel.
        
        Args:
            channel_id: Discord channel ID
            limit: Number of recent messages to fetch (default: 10)
            
        Returns:
            List of message dictionaries with author, content, and timestamp
        """
        try:
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                logger.warning(
                    "channel_not_found",
                    channel_id=channel_id,
                )
                return []
            
            if not isinstance(channel, discord.TextChannel):
                logger.warning(
                    "channel_not_text_channel",
                    channel_id=channel_id,
                )
                return []
            
            # Fetch recent messages
            messages = []
            async for message in channel.history(limit=limit):
                # Skip bot messages
                if message.author.bot:
                    continue
                
                # Format message
                messages.append({
                    "author": message.author.display_name or message.author.name,
                    "content": message.content,
                    "timestamp": message.created_at.strftime("%Y-%m-%d %H:%M"),
                    "url": message.jump_url,
                })
            
            # Reverse to show oldest first
            messages.reverse()
            
            logger.info(
                "channel_messages_read",
                channel_id=channel_id,
                messages_count=len(messages),
            )
            
            return messages
            
        except Exception as e:
            logger.error(
                "channel_read_error",
                channel_id=channel_id,
                error=str(e),
                exc_info=True,
            )
            return []
    
    async def read_channel_by_name(
        self,
        guild_id: int,
        channel_name: str,
        limit: int = 10,
    ) -> Optional[List[Dict[str, str]]]:
        """
        Read recent messages from a channel by name.
        
        Args:
            guild_id: Discord guild (server) ID
            channel_name: Channel name (without #)
            limit: Number of recent messages to fetch
            
        Returns:
            List of messages or None if channel not found
        """
        try:
            guild = self.bot.get_guild(guild_id)
            
            if not guild:
                logger.warning("guild_not_found", guild_id=guild_id)
                return None
            
            # Find channel by name
            channel = discord.utils.get(guild.channels, name=channel_name)
            
            if not channel:
                logger.warning(
                    "channel_not_found_by_name",
                    guild_id=guild_id,
                    channel_name=channel_name,
                )
                return None
            
            return await self.read_recent_messages(channel.id, limit)
            
        except Exception as e:
            logger.error(
                "channel_read_by_name_error",
                guild_id=guild_id,
                channel_name=channel_name,
                error=str(e),
                exc_info=True,
            )
            return None
    
    def format_messages_for_context(
        self,
        messages: List[Dict[str, str]],
        channel_name: str,
    ) -> str:
        """
        Format messages for LLM context.
        
        Args:
            messages: List of message dictionaries
            channel_name: Name of the channel
            
        Returns:
            Formatted string for LLM context
        """
        if not messages:
            return f"No recent messages found in #{channel_name}"
        
        formatted = f"**Recent messages from #{channel_name}:**\n\n"
        
        for msg in messages:
            formatted += f"**{msg['author']}** ({msg['timestamp']}): {msg['content']}\n"
        
        return formatted
    
    async def get_all_channels(
        self,
        guild_id: int,
        only_text: bool = True,
    ) -> List[Dict[str, any]]:
        """
        Get list of all channels in a guild.
        
        Args:
            guild_id: Discord guild (server) ID
            only_text: If True, return only text channels (default: True)
            
        Returns:
            List of channel dictionaries with id, name, type, category
        """
        try:
            guild = self.bot.get_guild(guild_id)
            
            if not guild:
                logger.warning(
                    "guild_not_found",
                    guild_id=guild_id,
                )
                return []
            
            channels = []
            
            for channel in guild.channels:
                # Filter by type if only_text is True
                if only_text and not isinstance(channel, discord.TextChannel):
                    continue
                
                channel_info = {
                    "id": channel.id,
                    "name": channel.name,
                    "type": str(channel.type),
                    "category": channel.category.name if channel.category else None,
                    "position": channel.position,
                }
                
                channels.append(channel_info)
            
            # Sort by category and position
            channels.sort(key=lambda x: (x["category"] or "", x["position"]))
            
            logger.info(
                "channels_retrieved",
                guild_id=guild_id,
                count=len(channels),
            )
            
            return channels
            
        except Exception as e:
            logger.error(
                "get_channels_failed",
                guild_id=guild_id,
                error=str(e),
                exc_info=True,
            )
            return []
    
    def format_channels_list(
        self,
        channels: List[Dict[str, any]],
    ) -> str:
        """
        Format channels list for display.
        
        Args:
            channels: List of channel dictionaries
            
        Returns:
            Formatted string with channels grouped by category
        """
        if not channels:
            return "No channels found"
        
        # Group by category
        by_category = {}
        for channel in channels:
            category = channel["category"] or "No Category"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(channel)
        
        # Format output
        formatted = "**Available channels:**\n\n"
        
        for category, cat_channels in by_category.items():
            formatted += f"**{category}:**\n"
            for ch in cat_channels:
                formatted += f"  • #{ch['name']} (ID: {ch['id']})\n"
            formatted += "\n"
        
        return formatted
