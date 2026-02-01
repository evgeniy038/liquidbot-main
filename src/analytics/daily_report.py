"""
Daily community activity report generator.

Generates statistics from SQLite database:
- Total messages
- Active channels
- Active users
- Top contributors (spammers)
- Top active channels
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import discord

from src.rag import get_message_storage
from src.utils import get_logger

logger = get_logger(__name__)


class DailyReportGenerator:
    """Generate daily activity reports from SQLite message database."""
    
    def __init__(self, qdrant_client=None):
        """
        Initialize report generator.
        
        Args:
            qdrant_client: Deprecated, kept for compatibility
        """
        self.storage = get_message_storage()
    
    async def generate_report(
        self,
        bot: discord.Client,
        days: int = 1
    ) -> Dict:
        """
        Generate full community report from SQLite.
        
        Args:
            bot: Discord bot instance (to get user names)
            days: Number of days to analyze
        
        Returns:
            Dict with report data
        """
        logger.info("generating_daily_report", days=days)
        
        # Get stats from SQLite
        stats = self.storage.get_daily_stats(days=days)
        
        if stats["total_messages"] == 0:
            logger.warning("no_messages_in_period")
            return {
                "total_messages": 0,
                "total_channels": 0,
                "total_users": 0,
                "top_users": [],
                "top_channels": [],
                "engagement_level": "No Data",
            }
        
        # Format top users with Discord info
        top_users = []
        for author in stats["top_authors"][:5]:
            user_id = author["author_id"]
            display_name = author["author_display_name"] or author["author_name"]
            msg_count = author["message_count"]
            
            # Try to get updated user info from Discord
            try:
                user = await bot.fetch_user(int(user_id))
                if user:
                    display_name = user.display_name
            except:
                pass
            
            top_users.append({
                "user_id": user_id,
                "display_name": display_name,
                "message_count": msg_count,
            })
        
        # Format top channels
        top_channels = [
            {
                "channel_id": ch["channel_id"],
                "channel_name": ch["channel_name"],
                "message_count": ch["message_count"],
            }
            for ch in stats["top_channels"][:5]
        ]
        
        # Determine engagement level
        total = stats["total_messages"]
        if total >= 1000:
            engagement = "Very High 🔥"
        elif total >= 500:
            engagement = "High 🚀"
        elif total >= 100:
            engagement = "Medium 📈"
        elif total >= 20:
            engagement = "Low 📊"
        else:
            engagement = "Very Low 💤"
        
        # Get yesterday's date for the report
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        report_data = {
            "total_messages": stats["total_messages"],
            "total_channels": stats["total_channels"],
            "total_users": stats["total_authors"],
            "top_users": top_users,
            "top_channels": top_channels,
            "engagement_level": engagement,
            "days": days,
            "date": yesterday.strftime("%m/%d"),
        }
        
        logger.info(
            "daily_report_generated",
            total_messages=stats["total_messages"],
            total_channels=stats["total_channels"],
            total_users=stats["total_authors"],
        )
        
        return report_data
    
    def format_embed(self, report_data: Dict) -> discord.Embed:
        """
        Format report data as Discord embed.
        
        Args:
            report_data: Report data dict
        
        Returns:
            Discord embed
        """
        embed = discord.Embed(
            title=f"📊 **Liquid Daily Community Report** • {report_data['date']}",
            description="Liquid Community activity summary",
            color=0x00D9FF,
        )
        
        # Activity Overview
        activity_text = (
            f"**{report_data['total_messages']:,} total messages** sent across "
            f"**{report_data['total_channels']} active channels** by "
            f"**{report_data['total_users']:,} unique community members**\n"
            f"Current engagement level: {report_data['engagement_level']}"
        )
        embed.add_field(
            name="📈 **Activity Overview**",
            value=activity_text,
            inline=False,
        )
        
        # Top Spammers with mentions
        if report_data['top_users']:
            top_users_text = ""
            for i, user_data in enumerate(report_data['top_users'][:5], 1):
                user_id = user_data['user_id']
                count = user_data['message_count']
                top_users_text += f"{i}. <@{user_id}> ({count} messages)\n"
            
            embed.add_field(
                name="👑 **Top Spammers of the Day**",
                value=top_users_text,
                inline=False,
            )
        
        # Top Channels with mentions
        if report_data['top_channels']:
            top_channels_text = ""
            for i, channel_data in enumerate(report_data['top_channels'][:5], 1):
                channel_id = channel_data['channel_id']
                count = channel_data['message_count']
                if channel_id:
                    top_channels_text += f"{i}. <#{channel_id}> ({count} messages)\n"
                else:
                    channel_name = channel_data['channel_name']
                    top_channels_text += f"{i}. **#{channel_name}** ({count} messages)\n"
            
            embed.add_field(
                name="🔥 **Top Spam Channels**",
                value=top_channels_text,
                inline=False,
            )
        
        # Footer with branding
        from src.utils.branding import get_footer_kwargs
        embed.set_footer(**get_footer_kwargs())
        
        return embed
