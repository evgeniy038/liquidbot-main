"""
Alert sender for scam detection notifications.
"""

from datetime import datetime
from typing import List, Optional

import discord

from src.utils import get_logger

logger = get_logger(__name__)


class ScamAlertView(discord.ui.View):
    """Interactive view with buttons for scam alerts."""
    
    def __init__(self, message_id: str = "", user_id: str = "", guild: Optional[discord.Guild] = None):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.user_id = user_id
        self.guild = guild
    
    @discord.ui.button(
        label="mark as scam",
        style=discord.ButtonStyle.danger,
        custom_id="mark_scam"
    )
    async def mark_scam(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        """Mark message as confirmed scam and ban the user."""
        # Get guild from interaction
        guild = interaction.guild or self.guild
        
        # Extract user_id from embed if not set
        if not self.user_id and interaction.message and interaction.message.embeds:
            embed = interaction.message.embeds[0]
            for field in embed.fields:
                if field.name == "user":
                    # Extract user ID from mention or value
                    import re
                    match = re.search(r'\((\d+)\)', field.value)
                    if match:
                        self.user_id = match.group(1)
                        break
        
        # Ban the scammer
        ban_success = False
        user_already_gone = False
        
        if guild and self.user_id:
            try:
                # First try to get member (if still in server)
                user = guild.get_member(int(self.user_id))
                
                if user:
                    # User is still in server - ban them
                    await guild.ban(
                        user,
                        reason=f"Scam confirmed by moderator {interaction.user.name}"
                    )
                    ban_success = True
                    logger.info(
                        "scammer_banned_by_moderator",
                        user_id=self.user_id,
                        moderator=str(interaction.user.id),
                    )
                else:
                    # User not in server - try to ban by ID (works for users who left)
                    try:
                        user_obj = await self.bot.fetch_user(int(self.user_id)) if hasattr(self, 'bot') else None
                        if user_obj:
                            await guild.ban(
                                user_obj,
                                reason=f"Scam confirmed by moderator {interaction.user.name}"
                            )
                            ban_success = True
                            logger.info(
                                "scammer_banned_by_id",
                                user_id=self.user_id,
                                moderator=str(interaction.user.id),
                            )
                        else:
                            # Try ban by discord.Object (ID only)
                            await guild.ban(
                                discord.Object(id=int(self.user_id)),
                                reason=f"Scam confirmed by moderator {interaction.user.name}"
                            )
                            ban_success = True
                            logger.info(
                                "scammer_banned_by_object_id",
                                user_id=self.user_id,
                                moderator=str(interaction.user.id),
                            )
                    except discord.NotFound:
                        # User account deleted or never existed
                        user_already_gone = True
                        logger.info(
                            "scammer_already_gone",
                            user_id=self.user_id,
                            note="user account not found, may be deleted"
                        )
                    except discord.Forbidden:
                        logger.warning(
                            "ban_forbidden",
                            user_id=self.user_id,
                            note="no permission to ban"
                        )
                        
            except discord.NotFound:
                user_already_gone = True
                logger.info(
                    "scammer_not_found",
                    user_id=self.user_id,
                    note="user already left or banned"
                )
            except discord.Forbidden:
                logger.warning(
                    "ban_forbidden",
                    user_id=self.user_id,
                    note="no permission to ban this user"
                )
            except Exception as e:
                logger.error(
                    "failed_to_ban_scammer_via_button",
                    error=str(e),
                    user_id=self.user_id,
                )
        
        # Build response message
        if ban_success:
            response_msg = "✅ Marked as scam. User banned."
        elif user_already_gone:
            response_msg = "✅ Marked as scam. User already left/banned - no action needed."
        elif guild:
            response_msg = "✅ Marked as scam. Could not ban (check permissions)."
        else:
            response_msg = "✅ Marked as scam. Action logged."
        
        await interaction.response.send_message(
            response_msg,
            ephemeral=True
        )
        
        logger.info(
            "scam_confirmed_by_moderator",
            message_id=self.message_id,
            user_id=self.user_id,
            moderator=str(interaction.user.id),
            banned=ban_success,
        )
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.message.edit(view=self)
    
    @discord.ui.button(
        label="false positive",
        style=discord.ButtonStyle.secondary,
        custom_id="false_positive"
    )
    async def false_positive(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        """Mark as false positive - no action taken."""
        await interaction.response.send_message(
            f"✅ Marked as false positive. No action taken.",
            ephemeral=True
        )
        
        logger.info(
            "false_positive_marked",
            message_id=self.message_id,
            user_id=self.user_id,
            moderator=str(interaction.user.id),
        )
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.message.edit(view=self)


class AlertSender:
    """
    Sends scam detection alerts to moderation channel.
    """
    
    def __init__(self, bot: discord.Client):
        """
        Initialize alert sender.
        
        Args:
            bot: Discord bot client
        """
        self.bot = bot
        logger.info("alert_sender_initialized")
    
    async def send_scam_alert(
        self,
        alert_channel_id: str,
        message: discord.Message,
        risk_score: float,
        risk_level: str,
        reasons: List[str],
        matched_keywords: List[str],
        matched_patterns: List[str],
        domains: List[str],
    ) -> bool:
        """
        Send scam detection alert to moderation channel.
        
        Args:
            alert_channel_id: Channel ID to send alert
            message: Original message that was flagged
            risk_score: Risk confidence score (0-1)
            risk_level: Risk level (low/medium/high/critical)
            reasons: List of reasons for flagging
            matched_keywords: Keywords that matched
            matched_patterns: Regex patterns that matched
            domains: Domains found in message
        
        Returns:
            True if alert sent successfully
        """
        try:
            # Get alert channel
            alert_channel = self.bot.get_channel(int(alert_channel_id))
            if not alert_channel:
                logger.error(
                    "alert_channel_not_found",
                    channel_id=alert_channel_id,
                )
                return False
            
            # Build embed
            embed = self._build_alert_embed(
                message=message,
                risk_score=risk_score,
                risk_level=risk_level,
                reasons=reasons,
                matched_keywords=matched_keywords,
                matched_patterns=matched_patterns,
                domains=domains,
            )
            
            # Create interactive view
            view = ScamAlertView(
                message_id=str(message.id),
                user_id=str(message.author.id),
                guild=message.guild if hasattr(message, 'guild') else None,
            )
            
            # Send alert
            await alert_channel.send(embed=embed, view=view)
            
            logger.info(
                "scam_alert_sent",
                message_id=str(message.id),
                alert_channel=alert_channel_id,
                risk_score=risk_score,
            )
            
            return True
        
        except Exception as e:
            logger.error(
                "alert_send_failed",
                error=str(e),
                exc_info=True,
            )
            return False
    
    def _build_alert_embed(
        self,
        message: discord.Message,
        risk_score: float,
        risk_level: str,
        reasons: List[str],
        matched_keywords: List[str],
        matched_patterns: List[str],
        domains: List[str],
    ) -> discord.Embed:
        """Build alert embed."""
        
        # Color based on risk level
        colors = {
            "low": discord.Color.yellow(),
            "medium": discord.Color.orange(),
            "high": discord.Color.red(),
            "critical": discord.Color.dark_red(),
        }
        color = colors.get(risk_level, discord.Color.red())
        
        # Create embed
        embed = discord.Embed(
            title="🚫 blocked message",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # User info (clickable)
        embed.add_field(
            name="user",
            value=f"<@{message.author.id}> ({message.author.id})",
            inline=True
        )
        
        # Channel (clickable)
        embed.add_field(
            name="channel",
            value=f"<#{message.channel.id}>",
            inline=True
        )
        
        # Reasons
        reasons_text = "\n".join(f"• {reason}" for reason in reasons[:5])
        if len(reasons) > 5:
            reasons_text += f"\n• ... and {len(reasons) - 5} more"
        
        embed.add_field(
            name="reasons",
            value=reasons_text,
            inline=False
        )
        
        # Matched indicators
        if matched_keywords:
            keywords_text = ", ".join(f"`{kw}`" for kw in matched_keywords[:5])
            if len(matched_keywords) > 5:
                keywords_text += f" +{len(matched_keywords) - 5} more"
            embed.add_field(
                name="matched keywords",
                value=keywords_text,
                inline=False
            )
        
        if matched_patterns:
            patterns_text = f"{len(matched_patterns)} regex pattern(s) matched"
            embed.add_field(
                name="matched patterns",
                value=patterns_text,
                inline=False
            )
        
        # Full message (truncated if needed)
        full_message = message.content
        if len(full_message) > 1000:
            full_message = full_message[:1000] + "..."
        
        embed.add_field(
            name="message",
            value=full_message,
            inline=False
        )
        
        # Footer with branding
        from src.utils.branding import get_footer_kwargs
        embed.set_footer(**get_footer_kwargs())
        
        return embed
