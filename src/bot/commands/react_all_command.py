"""
React All command for admins.

Features:
- Add reactions to all messages in a channel
- Admin-only command
- Configurable reactions
- Progress feedback
"""

from typing import List, Optional

import discord
from discord import app_commands

from src.utils import get_logger

logger = get_logger(__name__)


class ReactAllCommand:
    """
    Handle /react_all command to add reactions to all messages in a channel.
    """
    
    def __init__(self, bot: discord.Client, config: dict):
        """
        Initialize react_all command.
        
        Args:
            bot: Discord bot instance
            config: Configuration dictionary
        """
        self.bot = bot
        self.config = config
        
        # Silent init
    
    async def react_all(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message_limit: int = None,
        clear_existing: bool = False,
        emoji1: str = None,
        emoji2: str = None,
        emoji3: str = None,
        emoji4: str = None,
        emoji5: str = None,
    ):
        """
        Add reactions to all messages in a channel.
        
        Args:
            interaction: Discord interaction
            channel: Target channel
            message_limit: Number of messages to react to
            clear_existing: Whether to clear existing reactions first
            emoji1-5: Optional custom emojis to add
        """
        # Defer response since this will take time
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if command is enabled
            if not self.config.get("enabled", False):
                await interaction.followup.send("react all command is currently disabled.", ephemeral=True)
                return
            
            # Check if user has access (admin permission OR allowed role)
            allowed_role_ids = {1436799852171235472, 1436767320239243519}  # Staff, Mish
            config_role_ids = set(int(r) for r in self.config.get("required_roles", []) if r)
            all_allowed = allowed_role_ids | config_role_ids
            
            user_role_ids = {role.id for role in interaction.user.roles}
            
            has_access = (
                interaction.user.guild_permissions.administrator or
                bool(user_role_ids & all_allowed)
            )
            
            if not has_access:
                await interaction.followup.send(
                    "you don't have permission to use this command.",
                    ephemeral=True,
                )
                return
            
            # Get reactions from command or config
            custom_emojis = [e for e in [emoji1, emoji2, emoji3, emoji4, emoji5] if e]
            
            if custom_emojis:
                reactions = custom_emojis
            else:
                reactions = self.config.get("reactions", ["✅", "❌"])
            
            if not reactions:
                await interaction.followup.send("no reactions configured.", ephemeral=True)
                return
            
            logger.info(
                "react_all_started",
                admin_id=str(interaction.user.id),
                admin_name=interaction.user.name,
                channel_id=str(channel.id),
                channel_name=channel.name,
                reactions=reactions,
            )
            
            # Send initial progress message
            await interaction.followup.send(
                f"🔄 starting to add reactions to all messages in {channel.mention}...",
                ephemeral=True,
            )
            
            # Fetch and react to messages
            success_count = 0
            error_count = 0
            total_processed = 0
            
            # Get message limit from param or config
            limit = message_limit or self.config.get("message_limit", 100)
            
            async for message in channel.history(limit=limit):
                try:
                    total_processed += 1
                    
                    # Skip bot messages if configured
                    if self.config.get("skip_bot_messages", True) and message.author.bot:
                        continue
                    
                    # Clear existing reactions if requested
                    if clear_existing:
                        try:
                            await message.clear_reactions()
                        except discord.Forbidden:
                            pass  # No permission to clear
                        except discord.NotFound:
                            continue  # Message deleted
                    
                    # Add each reaction
                    for reaction in reactions:
                        try:
                            await message.add_reaction(reaction)
                        except discord.HTTPException as e:
                            logger.warning(
                                "failed_to_add_reaction",
                                message_id=str(message.id),
                                reaction=reaction,
                                error=str(e),
                            )
                    
                    success_count += 1
                    
                    # Send progress update every N messages
                    if total_processed % 10 == 0:
                        logger.debug(
                            "react_all_progress",
                            processed=total_processed,
                            success=success_count,
                        )
                
                except discord.Forbidden:
                    error_count += 1
                    logger.error(
                        "missing_permissions_to_react",
                        message_id=str(message.id),
                        channel_id=str(channel.id),
                    )
                
                except Exception as e:
                    error_count += 1
                    logger.error(
                        "failed_to_react_to_message",
                        error=str(e),
                        message_id=str(message.id),
                    )
            
            # Send completion message
            completion_message = (
                f"✅ completed adding reactions to {channel.mention}!\n\n"
                f"**results:**\n"
                f"• total messages processed: {total_processed}\n"
                f"• successfully reacted: {success_count}\n"
                f"• errors: {error_count}\n"
                f"• reactions used: {', '.join(reactions)}"
                + (f"\n• cleared existing: yes" if clear_existing else "")
            )
            
            await interaction.followup.send(completion_message, ephemeral=True)
            
            logger.info(
                "react_all_completed",
                admin_id=str(interaction.user.id),
                channel_id=str(channel.id),
                total_processed=total_processed,
                success_count=success_count,
                error_count=error_count,
            )
        
        except Exception as e:
            logger.error(
                "react_all_failed",
                error=str(e),
                admin_id=str(interaction.user.id),
                channel_id=str(channel.id) if channel else None,
            )
            await interaction.followup.send(
                "an error occurred while adding reactions.",
                ephemeral=True,
            )


def setup_react_all_command(bot: discord.Client, config: dict) -> ReactAllCommand:
    """
    Setup and register /react_all command.
    
    Args:
        bot: Discord bot instance
        config: Configuration dictionary
    
    Returns:
        ReactAllCommand instance
    """
    react_all_cmd = ReactAllCommand(bot, config)
    
    @app_commands.command(
        name="react_all",
        description="add reactions to all messages in a channel (admin only)",
    )
    @app_commands.describe(
        channel="the channel to add reactions to",
        message_limit="number of messages to react to (default: 100)",
        clear_existing="clear existing reactions before adding new ones",
        emoji1="first emoji to add (optional, supports server emojis)",
        emoji2="second emoji to add (optional)",
        emoji3="third emoji to add (optional)",
        emoji4="fourth emoji to add (optional)",
        emoji5="fifth emoji to add (optional)",
    )
    async def react_all_slash(
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message_limit: int = None,
        clear_existing: bool = False,
        emoji1: str = None,
        emoji2: str = None,
        emoji3: str = None,
        emoji4: str = None,
        emoji5: str = None,
    ):
        await react_all_cmd.react_all(interaction, channel, message_limit, clear_existing, emoji1, emoji2, emoji3, emoji4, emoji5)
    
    # Add command to bot's tree
    bot.tree.add_command(react_all_slash)
    
    # Registered
    
    return react_all_cmd
