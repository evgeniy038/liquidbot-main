"""
Check Activity command - Manual activity check for admins.

Features:
- Check user activity manually
- Customize thresholds on-the-fly
- View inactive users
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord import app_commands

from src.analytics.activity_checker import ActivityChecker
from src.utils import get_logger

logger = get_logger(__name__)


class CheckActivityCommand:
    """
    Handle /check_activity command for manual activity checks.
    """
    
    def __init__(self, bot: discord.Client, config: dict):
        """
        Initialize check activity command.
        
        Args:
            bot: Discord bot instance
            config: Configuration dictionary
        """
        self.bot = bot
        self.config = config
        self.activity_checker = ActivityChecker(bot, config)
        
        # Silent init
    
    async def check_activity(
        self,
        interaction: discord.Interaction,
        min_messages: Optional[int] = None,
        days: Optional[int] = None,
    ):
        """
        Manually check user activity.
        
        Args:
            interaction: Discord interaction
            min_messages: Minimum message threshold (optional)
            days: Days to check (optional)
        """
        # Defer response since this will take time
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user has access (admin permission OR allowed role)
            allowed_role_ids = {1436799852171235472, 1436767320239243519}  # Staff, Mish
            user_role_ids = {role.id for role in interaction.user.roles}
            
            has_access = (
                interaction.user.guild_permissions.administrator or
                bool(user_role_ids & allowed_role_ids)
            )
            
            if not has_access:
                await interaction.followup.send(
                    "You don't have permission to use this command.",
                    ephemeral=True,
                )
                return
            
            # Get settings
            use_min_messages = min_messages if min_messages is not None else self.config.get("min_messages", 5)
            use_days = days if days is not None else self.config.get("days_to_check", 7)
            
            logger.info(
                "check_activity_manual",
                admin_id=str(interaction.user.id),
                min_messages=use_min_messages,
                days=use_days,
            )
            
            # Send initial message
            await interaction.followup.send(
                f"🔍 Checking activity...\n"
                f"Settings: **{use_min_messages}** messages in last **{use_days}** days",
                ephemeral=True,
            )
            
            # Temporarily override config
            original_min = self.config.get("min_messages")
            original_days = self.config.get("days_to_check")
            
            self.config["min_messages"] = use_min_messages
            self.config["days_to_check"] = use_days
            
            # Run check (returns tuple of embed and inactive_users list)
            embed, inactive_users = await self.activity_checker.check_activity()
            
            # Restore original config
            self.config["min_messages"] = original_min
            self.config["days_to_check"] = original_days
            
            logger.info(
                "check_activity_result",
                admin_id=str(interaction.user.id),
                inactive_count=len(inactive_users) if inactive_users else 0,
                has_embed=embed is not None,
            )
            
            if embed:
                # Send results to user
                await interaction.followup.send(
                    "✅ Activity check complete! Results:",
                    embed=embed,
                    ephemeral=True,
                )
                
                logger.info(
                    "check_activity_complete",
                    admin_id=str(interaction.user.id),
                    found_inactive=True,
                )
            else:
                await interaction.followup.send(
                    "✅ activity check complete!\n\n"
                    f"**no inactive users found** with threshold:\n"
                    f"• min messages: **{use_min_messages}**\n"
                    f"• days: **{use_days}**\n\n"
                    "everyone is active! 🎉",
                    ephemeral=True,
                )
                
                logger.info(
                    "check_activity_complete",
                    admin_id=str(interaction.user.id),
                    found_inactive=False,
                )
        
        except Exception as e:
            logger.error(
                "check_activity_failed",
                error=str(e),
                admin_id=str(interaction.user.id),
            )
            await interaction.followup.send(
                "An error occurred while checking activity.",
                ephemeral=True,
            )


def setup_check_activity_command(bot: discord.Client, config: dict) -> CheckActivityCommand:
    """
    Setup and register /check_activity command.
    
    Args:
        bot: Discord bot instance
        config: Configuration dictionary
    
    Returns:
        CheckActivityCommand instance
    """
    check_activity_cmd = CheckActivityCommand(bot, config)
    
    @app_commands.command(
        name="check_activity",
        description="Manually check user activity (Admin only)",
    )
    @app_commands.describe(
        min_messages="Minimum messages required (default: from config)",
        days="Number of days to check (default: from config)",
    )
    async def check_activity_slash(
        interaction: discord.Interaction,
        min_messages: Optional[int] = None,
        days: Optional[int] = None,
    ):
        await check_activity_cmd.check_activity(interaction, min_messages, days)
    
    # Add command to bot's tree
    bot.tree.add_command(check_activity_slash)
    
    # Registered
    
    return check_activity_cmd
