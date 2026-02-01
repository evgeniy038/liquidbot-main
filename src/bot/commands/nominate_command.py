"""
Nomination command for promoting users.

Features:
- Nominate users for promotion
- Show nominee stats (messages, content count)
- Display tweets/content links
- Voting reactions
"""

import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import discord
from discord import app_commands

from src.rag import get_message_storage
from src.utils import get_logger

logger = get_logger(__name__)


class NominateCommand:
    """
    Handle /nominate command for user promotions.
    """
    
    def __init__(self, bot: discord.Client, config: dict):
        """
        Initialize nominate command.
        
        Args:
            bot: Discord bot instance
            config: Configuration dictionary
        """
        self.bot = bot
        self.config = config
        self.storage = get_message_storage()
        
        # Silent init
    
    async def nominate(
        self,
        interaction: discord.Interaction,
        nominee: discord.Member,
        reason: str,
    ):
        """
        Nominate a user for promotion.
        
        Args:
            interaction: Discord interaction
            nominee: User being nominated
            reason: Reason for nomination
        """
        # Defer response since this might take a while
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if command is enabled
            if not self.config.get("enabled", False):
                await interaction.followup.send("Nomination system is currently disabled.", ephemeral=True)
                return
            
            # Check if user has permission to nominate
            admin_role_ids = {1436799852171235472, 1436767320239243519}  # Staff, Mish
            config_role_ids = set(int(r) for r in self.config.get("allowed_nominator_roles", []) if r)
            all_allowed = admin_role_ids | config_role_ids
            
            user_role_ids = {role.id for role in interaction.user.roles}
            
            has_permission = (
                interaction.user.guild_permissions.administrator or
                bool(user_role_ids & all_allowed)
            )
            
            if not has_permission:
                await interaction.followup.send("you don't have permission to nominate users.", ephemeral=True)
                return
            
            # Check if nominee is not a bot
            if nominee.bot:
                await interaction.followup.send("you cannot nominate bots.", ephemeral=True)
                return
            
            # Check if nominee is not nominating themselves
            if nominee.id == interaction.user.id:
                await interaction.followup.send("you cannot nominate yourself.", ephemeral=True)
                return
            
            logger.info(
                "nomination_started",
                nominator_id=str(interaction.user.id),
                nominator_name=interaction.user.name,
                nominee_id=str(nominee.id),
                nominee_name=nominee.name,
            )
            
            # Gather nominee statistics
            stats = await self._gather_nominee_stats(nominee)
            
            # Get tweets/content
            tweets = await self._get_user_tweets(str(nominee.id))
            
            # Create nomination embed
            embed = await self._create_nomination_embed(
                nominator=interaction.user,
                nominee=nominee,
                reason=reason,
                stats=stats,
                tweets=tweets,
            )
            
            # Send to nomination channel
            nomination_channel_id = self.config.get("nomination_channel_id")
            if not nomination_channel_id:
                await interaction.followup.send("nomination channel is not configured.", ephemeral=True)
                logger.error("nomination_channel_not_configured")
                return
            
            nomination_channel = self.bot.get_channel(int(nomination_channel_id))
            if not nomination_channel:
                await interaction.followup.send("nomination channel not found.", ephemeral=True)
                logger.error("nomination_channel_not_found", channel_id=nomination_channel_id)
                return
            
            # Send nomination
            message = await nomination_channel.send(embed=embed)
            
            # Add voting reactions
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            logger.info(
                "nomination_sent",
                nominator_id=str(interaction.user.id),
                nominee_id=str(nominee.id),
                message_id=str(message.id),
                channel_id=nomination_channel_id,
            )
            
            await interaction.followup.send(
                f"✅ successfully nominated {nominee.mention} for promotion!",
                ephemeral=True,
            )
        
        except Exception as e:
            logger.error(
                "nomination_failed",
                error=str(e),
                nominator_id=str(interaction.user.id),
                nominee_id=str(nominee.id),
            )
            await interaction.followup.send(
                "an error occurred while processing the nomination.",
                ephemeral=True,
            )
    
    async def _gather_nominee_stats(self, nominee: discord.Member) -> dict:
        """
        Gather statistics about the nominee from SQLite.
        """
        try:
            stats = self.storage.get_user_stats(str(nominee.id))
            return stats
        except Exception as e:
            logger.error("failed_to_gather_stats", error=str(e), nominee_id=str(nominee.id))
            return {
                "total_messages": 0,
                "channels_active": 0,
                "first_message": None,
                "last_message": None,
                "avg_message_length": 0,
            }
    
    async def _get_user_tweets(self, user_id: str, limit: int = 50) -> List[dict]:
        """
        Get user's tweets (messages with x.com links) from SQLite.
        """
        try:
            tweets_channel_id = self.config.get("tweets_search_channel_id", "")
            
            # Get tweets from SQLite
            raw_tweets = self.storage.get_user_tweets(
                user_id=user_id,
                channel_id=tweets_channel_id if tweets_channel_id else None,
                limit=limit
            )
            
            # Extract x.com URLs from content
            twitter_pattern = re.compile(r'https?://(?:twitter\.com|x\.com)/\S+')
            tweets = []
            
            for tweet in raw_tweets:
                content = tweet.get("content", "")
                matches = twitter_pattern.findall(content)
                
                for match in matches:
                    tweets.append({
                        "url": match,
                        "timestamp": tweet.get("timestamp"),
                        "message_url": tweet.get("url"),
                    })
                    if len(tweets) >= limit:
                        return tweets
            
            return tweets
        
        except Exception as e:
            logger.error("failed_to_get_tweets", error=str(e), user_id=user_id)
            return []
    
    async def _create_nomination_embed(
        self,
        nominator: discord.Member,
        nominee: discord.Member,
        reason: str,
        stats: dict,
        tweets: List[dict],
    ) -> discord.Embed:
        """
        Create nomination embed.
        
        Args:
            nominator: User who nominated
            nominee: User being nominated
            reason: Reason for nomination
            stats: Nominee statistics
            tweets: List of tweets
        
        Returns:
            Discord embed
        """
        embed = discord.Embed(
            title="✨ new nomination",
            description=f"{nominee.mention} has been nominated for promotion!".lower(),
            color=self.config.get("embed_color", 0x00D9FF),
            timestamp=datetime.now(timezone.utc),
        )
        
        # Nominee info
        embed.add_field(
            name="👤 nominee",
            value=f"{nominee.mention}",
            inline=True,
        )
        
        # Nominator info
        embed.add_field(
            name="🙋 nominated by",
            value=f"{nominator.mention}",
            inline=True,
        )
        
        # Empty field for spacing
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        
        # Reason
        embed.add_field(
            name="💬 reason",
            value=reason[:1024],  # Discord field limit
            inline=False,
        )
        
        # Statistics
        stats_text = f"**messages:** {stats['total_messages']}"
        
        # Add joined server date
        if nominee.joined_at:
            joined_date = nominee.joined_at.strftime("%b %d, %Y")
            stats_text += f"\n**joined server:** {joined_date}"
        
        if stats['first_message']:
            try:
                # Parse ISO format timestamp from SQLite
                first_msg_str = stats['first_message'][:19]  # Remove timezone suffix
                first_msg_dt = datetime.strptime(first_msg_str, "%Y-%m-%dT%H:%M:%S")
                days_active = (datetime.utcnow() - first_msg_dt).days
                stats_text += f"\n**days active:** {days_active}"
            except:
                pass  # Skip if parse fails
        
        embed.add_field(
            name="📊 statistics",
            value=stats_text,
            inline=False,
        )
        
        # Content (tweets)
        if tweets:
            # Remove duplicates (same URL)
            unique_tweets = []
            seen_urls = set()
            for tweet in tweets:
                if tweet['url'] not in seen_urls:
                    unique_tweets.append(tweet)
                    seen_urls.add(tweet['url'])
            
            content_lines = []
            for i, tweet in enumerate(unique_tweets, 1):
                # Get the full URL
                tweet_url = tweet['url']
                # Create clickable link with full URL
                content_lines.append(f"[Tweet {i}]({tweet_url})")
            
            # Discord field limit is 1024 chars, split if needed
            content_text = "\n".join(content_lines)
            if len(content_text) > 1024:
                content_text = content_text[:1020] + "..."
            
            embed.add_field(
                name=f"🐦 content ({len(unique_tweets)} tweets found)".lower(),
                value=content_text,
                inline=False,
            )
        else:
            embed.add_field(
                name="🐦 content",
                value="no x.com links found",
                inline=False,
            )
        
        # Nominee thumbnail
        if nominee.avatar:
            embed.set_thumbnail(url=nominee.avatar.url)
        
        # Footer with branding
        from src.utils.branding import get_footer_kwargs
        embed.set_footer(**get_footer_kwargs())
        
        return embed


def setup_nominate_command(bot: discord.Client, config: dict) -> NominateCommand:
    """
    Setup and register /nominate command.
    
    Args:
        bot: Discord bot instance
        config: Configuration dictionary
    
    Returns:
        NominateCommand instance
    """
    nominate_cmd = NominateCommand(bot, config)
    
    @app_commands.command(
        name="nominate",
        description="nominate a user for promotion",
    )
    @app_commands.describe(
        nominee="the user you want to nominate",
        reason="why do you want to nominate this user?",
    )
    async def nominate_slash(
        interaction: discord.Interaction,
        nominee: discord.Member,
        reason: str,
    ):
        await nominate_cmd.nominate(interaction, nominee, reason)
    
    # Add command to bot's tree
    bot.tree.add_command(nominate_slash)
    
    # Registered
    
    return nominate_cmd
