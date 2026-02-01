"""
Daily activity checker for role-based activity monitoring.

Features:
- Check activity of specific roles once per day
- Report users with low message count
- Whitelist support for exempt roles
- Configurable thresholds
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import discord

from src.rag import get_message_storage
from src.utils import get_logger

logger = get_logger(__name__)


class ActivityChecker:
    """
    Checks user activity based on roles and reports inactive users.
    """
    
    def __init__(
        self,
        bot: discord.Client,
        config: dict,
    ):
        """
        Initialize activity checker.
        
        Args:
            bot: Discord bot instance
            config: Configuration dictionary
        """
        self.bot = bot
        self.config = config
        self.storage = get_message_storage()
        
        # Silent init
    
    async def check_activity(self) -> Tuple[Optional[discord.Embed], List[Dict]]:
        """
        Check activity of users with monitored roles.
        
        Returns:
            Tuple of (Embed with inactive users or None, list of inactive user dicts)
        """
        if not self.config.get("enabled", False):
            logger.info("activity_check_disabled")
            return None, []
        
        guild_id = self.config.get("guild_id")
        if not guild_id:
            logger.error("guild_id_not_configured")
            return None, []
        
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            logger.error("guild_not_found", guild_id=guild_id)
            return None, []
        
        # Get configuration
        monitored_role_ids = self.config.get("monitored_roles", [])
        whitelisted_role_ids = self.config.get("whitelisted_roles", [])
        min_messages = self.config.get("min_messages", 5)
        days_to_check = self.config.get("days_to_check", 7)
        
        if not monitored_role_ids:
            logger.info("no_monitored_roles_configured")
            return None, []
        
        # Calculate time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_to_check)
        
        logger.info(
            "checking_activity",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            min_messages=min_messages,
            monitored_roles=len(monitored_role_ids),
        )
        
        # Find inactive users
        inactive_users = []
        checked_users = 0
        whitelisted_count = 0
        
        # Debug: convert monitored_role_ids to strings for comparison
        monitored_role_ids = [str(r) for r in monitored_role_ids]
        whitelisted_role_ids = [str(r) for r in whitelisted_role_ids]
        
        logger.info(
            "activity_check_started",
            guild=guild.name,
            total_members=guild.member_count,
            monitored_roles=len(monitored_role_ids),
            whitelisted_roles=len(whitelisted_role_ids),
            min_messages=min_messages,
            days=days_to_check,
        )
        
        for member in guild.members:
            # Skip bots
            if member.bot:
                continue
            
            # Check if user has any monitored roles
            user_role_ids = [str(role.id) for role in member.roles]
            has_monitored_role = any(role_id in monitored_role_ids for role_id in user_role_ids)
            
            if not has_monitored_role:
                continue
            
            checked_users += 1
            
            # Check if user has any whitelisted roles
            has_whitelisted_role = any(role_id in whitelisted_role_ids for role_id in user_role_ids)
            
            if has_whitelisted_role:
                whitelisted_count += 1
                logger.debug("user_whitelisted", user_id=str(member.id), user_name=member.name)
                continue
            
            # Count messages in time range
            message_count = await self._count_user_messages_in_range(
                user_id=str(member.id),
                start_date=start_date,
                end_date=end_date,
            )
            
            # Check if below threshold
            if message_count < min_messages:
                inactive_users.append({
                    "member": member,
                    "message_count": message_count,
                })
                logger.info(
                    "inactive_user_found",
                    user_id=str(member.id),
                    user_name=member.name,
                    message_count=message_count,
                    min_required=min_messages,
                )
        
        # Create embed if there are inactive users
        logger.info(
            f"📊 Activity check complete: {checked_users} checked, {len(inactive_users)} inactive, {whitelisted_count} whitelisted"
        )
        
        if inactive_users:
            embed = self._create_activity_report_embed(
                inactive_users=inactive_users,
                min_messages=min_messages,
                days_to_check=days_to_check,
            )
            return embed, inactive_users
        else:
            return None, []
    
    async def _count_user_messages_in_range(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """
        Count messages for a user in date range using SQLite.
        """
        try:
            return self.storage.get_user_message_count_in_range(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as e:
            logger.error(
                "failed_to_count_messages_in_range",
                user_id=user_id,
                error=str(e),
            )
            return 0
    
    def _create_activity_report_embed(
        self,
        inactive_users: List[Dict],
        min_messages: int,
        days_to_check: int,
    ) -> discord.Embed:
        """
        Create embed for activity report.
        
        Args:
            inactive_users: List of inactive users with their message counts
            min_messages: Minimum required messages
            days_to_check: Number of days checked
        
        Returns:
            Discord embed
        """
        embed = discord.Embed(
            title="🚨 Activity Report",
            description=f"Found **{len(inactive_users)} users** below **{min_messages} messages** threshold in the last **{days_to_check} days**",
            color=self.config.get("embed_color", 0xFF6B6B),
            timestamp=datetime.now(timezone.utc),
        )
        
        # Group by HIGHEST role only (no duplicates)
        monitored_role_ids = self.config.get("monitored_roles", [])
        role_groups = {}
        
        for user_data in inactive_users:
            member = user_data["member"]
            message_count = user_data["message_count"]
            
            # Get monitored roles for this user
            user_monitored_roles = [
                role for role in member.roles 
                if str(role.id) in monitored_role_ids
            ]
            
            # Find highest role (by position)
            if user_monitored_roles:
                # Sort by position (highest first)
                user_monitored_roles.sort(key=lambda r: r.position, reverse=True)
                highest_role = user_monitored_roles[0]
                role_id = str(highest_role.id)
                
                # Add to role group
                if role_id not in role_groups:
                    role_groups[role_id] = {
                        "name": highest_role.name,
                        "users": []
                    }
                
                role_groups[role_id]["users"].append({
                    "id": member.id,
                    "messages": message_count
                })
        
        # Add fields for each role
        if role_groups:
            for role_id, group in role_groups.items():
                # Sort by message count
                group["users"].sort(key=lambda x: x["messages"])
                
                # Create user list
                user_lines = []
                for user in group["users"][:10]:  # Max 10 per role
                    user_lines.append(f"• <@{user['id']}> - {user['messages']} messages")
                
                if len(group["users"]) > 10:
                    user_lines.append(f"*... and {len(group['users']) - 10} more*")
                
                # Add field with role name in backticks
                embed.add_field(
                    name=f"📋 Role: `{group['name']}`",
                    value="\n".join(user_lines),
                    inline=False,
                )
        else:
            embed.add_field(
                name="ℹ️ Note",
                value="No users with monitored roles found",
                inline=False,
            )
        
        from src.utils.branding import get_footer_kwargs
        embed.set_footer(**get_footer_kwargs())
        
        return embed
    
    async def send_dm_to_inactive_users(
        self,
        inactive_users: List[Dict],
        min_messages: int = 5,
        days: int = 7,
    ) -> Tuple[int, int]:
        """
        Send DMs to inactive users with a friendly reminder.
        
        Args:
            inactive_users: List of inactive user dicts from check_activity
            min_messages: Minimum messages required
            days: Days period checked
            
        Returns:
            Tuple of (successful DMs, failed DMs)
        """
        if not self.config.get("dm_inactive_users", False):
            logger.info("dm_inactive_users_disabled")
            return 0, 0
        
        if not inactive_users:
            return 0, 0
        
        import random
        
        # Fun messages to send (rotating)
        dm_messages = [
            "hey! 👋 noticed you've been quiet lately. everything good? we miss your vibes in the server",
            "yo! the chat's been missing you. drop by when you get a chance, we don't bite (much) 🦈",
            "hey stranger! 👀 haven't seen you around lately. hope you're doing well. come say hi sometime",
            "gm! ☕ just a friendly nudge - we noticed you've been away. the community misses you!",
            "hey! quick check-in - you've been pretty quiet. no pressure, just wanted to say we're here if you need anything",
            "yo! 🌊 the server's been wondering where you went. hope everything's cool. see you around?",
            "hey there! noticed you've been on the low. just a reminder that the community is always here for you 💪",
            "gm gm! ☀️ haven't heard from you in a bit. hope life's treating you well. we're here when you're ready",
        ]
        
        success_count = 0
        fail_count = 0
        
        for user_data in inactive_users:
            member = user_data["member"]
            message_count = user_data["message_count"]
            
            try:
                # Pick a random message
                dm_text = random.choice(dm_messages)
                
                # Add context about activity
                dm_text += f"\n\n*ps: you've sent {message_count} messages in the last {days} days. no judgment, just keeping track* 📊"
                
                # Try to send DM
                await member.send(dm_text)
                
                logger.info(
                    f"📨 DM_SENT | @{member.name} ({member.id}) | msgs={message_count}"
                )
                success_count += 1
                
            except discord.Forbidden:
                # User has DMs disabled
                logger.debug(
                    f"dm_forbidden | user={member.name} | dms_closed"
                )
                fail_count += 1
                
            except Exception as e:
                logger.error(
                    f"dm_failed | user={member.name} | error={e}"
                )
                fail_count += 1
        
        logger.info(
            f"📬 DM_SUMMARY | sent={success_count} | failed={fail_count} | total={len(inactive_users)}"
        )
        
        return success_count, fail_count
