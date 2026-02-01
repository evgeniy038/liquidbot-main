"""
Content submission handler for the anti-slop system.

Handles:
- New submissions in guild channels
- Vote reactions from T1+ members
- Guild lead decisions
- DM feedback for revisions
- Forwarding approved content
- Cooldowns and blacklisting
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set

import discord
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput

from src.moderation.submission_storage import (
    SubmissionStorage,
    SubmissionStatus,
    VoteType,
    Submission,
    get_submission_storage,
)
from src.utils import get_logger

logger = get_logger(__name__)

# Reaction emojis
EMOJI_KEEP = "🟢"
EMOJI_REVISE = "🟡"
EMOJI_SLOP = "🔴"
EMOJI_APPROVE = "✅"
EMOJI_SPOTLIGHT = "⭐"

VOTE_EMOJI_MAP = {
    EMOJI_KEEP: VoteType.KEEP,
    EMOJI_REVISE: VoteType.REVISE,
    EMOJI_SLOP: VoteType.SLOP,
}

# Cooldown tiers (consecutive rejections -> hours)
COOLDOWN_TIERS = {
    2: 6,    # 2 rejections = 6 hour cooldown
    3: 12,   # 3 rejections = 12 hour cooldown
    4: 24,   # 4 rejections = 24 hour cooldown
    5: 48,   # 5+ rejections = 48 hour cooldown
}


class FeedbackModal(Modal, title="Provide Feedback"):
    """Modal for guild lead to provide feedback on revision."""
    
    feedback = TextInput(
        label="Feedback for the creator",
        style=discord.TextStyle.paragraph,
        placeholder="Explain what needs to be improved...",
        required=True,
        max_length=1000,
    )
    
    def __init__(self, handler: "SubmissionHandler", submission: Submission):
        super().__init__()
        self.handler = handler
        self.submission = submission
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        success = await self.handler.process_revision_decision(
            submission=self.submission,
            decision_by=interaction.user,
            feedback=self.feedback.value,
        )
        
        if success:
            await interaction.followup.send(
                f"✅ feedback sent to <@{self.submission.author_id}>",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "❌ failed to send feedback",
                ephemeral=True,
            )


class RejectModal(Modal, title="Rejection Reason"):
    """Modal for guild lead to provide rejection reason."""
    
    reason = TextInput(
        label="Reason for rejection",
        style=discord.TextStyle.paragraph,
        placeholder="Why is this being rejected?",
        required=False,
        max_length=500,
    )
    
    def __init__(self, handler: "SubmissionHandler", submission: Submission):
        super().__init__()
        self.handler = handler
        self.submission = submission
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        success = await self.handler.process_rejection(
            submission=self.submission,
            decision_by=interaction.user,
            reason=self.reason.value or "Content did not meet quality standards",
        )
        
        if success:
            await interaction.followup.send(
                f"🔴 submission rejected and content blacklisted",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "❌ failed to process rejection",
                ephemeral=True,
            )


class DecisionView(View):
    """View with decision buttons for guild leads."""
    
    def __init__(self, handler: "SubmissionHandler", submission_id: int):
        super().__init__(timeout=None)
        self.handler = handler
        self.submission_id = submission_id
    
    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green, emoji="✅", custom_id="submission_approve")
    async def approve_button(self, interaction: discord.Interaction, button: Button):
        if not await self.handler.check_guild_lead(interaction):
            return
        
        submission = self.handler.storage.get_submission(self.submission_id)
        if not submission:
            await interaction.response.send_message("submission not found", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        success = await self.handler.process_approval(
            submission=submission,
            decision_by=interaction.user,
        )
        
        if success:
            await interaction.followup.send("✅ approved and forwarded to content channel", ephemeral=True)
            self.stop()
        else:
            await interaction.followup.send("❌ failed to approve", ephemeral=True)
    
    @discord.ui.button(label="Needs Work", style=discord.ButtonStyle.secondary, emoji="🟡", custom_id="submission_revise")
    async def revise_button(self, interaction: discord.Interaction, button: Button):
        if not await self.handler.check_guild_lead(interaction):
            return
        
        submission = self.handler.storage.get_submission(self.submission_id)
        if not submission:
            await interaction.response.send_message("submission not found", ephemeral=True)
            return
        
        modal = FeedbackModal(self.handler, submission)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="submission_reject")
    async def reject_button(self, interaction: discord.Interaction, button: Button):
        if not await self.handler.check_guild_lead(interaction):
            return
        
        submission = self.handler.storage.get_submission(self.submission_id)
        if not submission:
            await interaction.response.send_message("submission not found", ephemeral=True)
            return
        
        modal = RejectModal(self.handler, submission)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Spotlight", style=discord.ButtonStyle.primary, emoji="⭐", custom_id="submission_spotlight")
    async def spotlight_button(self, interaction: discord.Interaction, button: Button):
        if not await self.handler.check_guild_lead(interaction):
            return
        
        submission = self.handler.storage.get_submission(self.submission_id)
        if not submission:
            await interaction.response.send_message("submission not found", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # First approve, then spotlight
        success = await self.handler.process_approval(
            submission=submission,
            decision_by=interaction.user,
            spotlight=True,
        )
        
        if success:
            await interaction.followup.send("⭐ approved and spotlighted!", ephemeral=True)
            self.stop()
        else:
            await interaction.followup.send("❌ failed to spotlight", ephemeral=True)


class SubmissionHandler:
    """
    Handles the content submission workflow.
    
    Flow:
    1. User posts in submission channel
    2. Bot creates submission record and adds vote reactions
    3. T1+ members vote with reactions
    4. Guild lead makes final decision via buttons
    5. Content is approved/revised/rejected
    """
    
    def __init__(self, bot: discord.Client, config: dict):
        """
        Initialize submission handler.
        
        Args:
            bot: Discord bot instance
            config: Submission system configuration
        """
        self.bot = bot
        self.config = config
        self.storage = get_submission_storage()
        
        # Cache channel IDs
        self.submission_channels: Dict[str, int] = {}  # guild_path -> channel_id
        self.approved_channel_id: Optional[int] = None
        self.spotlight_channel_id: Optional[int] = None
        
        # Cache role IDs
        self.t1_role_ids: Set[int] = set()
        self.guild_lead_role_ids: Set[int] = set()
        
        self._load_config()
    
    def _load_config(self):
        """Load configuration values."""
        channels = self.config.get("channels", {})
        
        # Submission channels per guild
        self.submission_channels = {
            "traders": int(channels.get("traders") or 0),
            "content": int(channels.get("content") or 0),
            "designers": int(channels.get("designers") or 0),
        }
        
        self.approved_channel_id = int(channels.get("approved") or 0)
        self.spotlight_channel_id = int(channels.get("spotlight") or 0) or self.approved_channel_id
        
        # Roles
        roles = self.config.get("roles", {})
        self.t1_role_ids = set(int(r) for r in roles.get("t1_voters", []) if r)
        self.guild_lead_role_ids = set(int(r) for r in roles.get("guild_leads", []) if r)
        
        # Decision timeout (hours)
        self.decision_timeout_hours = self.config.get("decision_timeout_hours", 24)
        
        # Max revisions before auto-reject
        self.max_revisions = self.config.get("max_revisions", 2)
    
    def is_submission_channel(self, channel_id: int) -> Optional[str]:
        """Check if channel is a submission channel. Returns guild path or None."""
        for guild_path, ch_id in self.submission_channels.items():
            if ch_id == channel_id:
                return guild_path
        return None
    
    def has_t1_role(self, member: discord.Member) -> bool:
        """Check if member has T1+ role for voting."""
        member_role_ids = {role.id for role in member.roles}
        return bool(member_role_ids & self.t1_role_ids)
    
    def is_guild_lead(self, member: discord.Member) -> bool:
        """Check if member is a guild lead."""
        if member.guild_permissions.administrator:
            return True
        member_role_ids = {role.id for role in member.roles}
        return bool(member_role_ids & self.guild_lead_role_ids)
    
    async def check_guild_lead(self, interaction: discord.Interaction) -> bool:
        """Check if interaction user is guild lead, send error if not."""
        if not self.is_guild_lead(interaction.user):
            await interaction.response.send_message(
                "❌ only guild leads can make decisions",
                ephemeral=True,
            )
            return False
        return True
    
    async def handle_new_submission(self, message: discord.Message) -> bool:
        """
        Handle a new submission in a submission channel.
        
        Returns True if message was processed as submission.
        """
        guild_path = self.is_submission_channel(message.channel.id)
        if not guild_path:
            return False
        
        # Check for cooldown
        cooldown = self.storage.get_cooldown(str(message.author.id), guild_path)
        if cooldown:
            remaining = cooldown - datetime.utcnow()
            hours = int(remaining.total_seconds() / 3600)
            minutes = int((remaining.total_seconds() % 3600) / 60)
            
            try:
                await message.delete()
            except:
                pass
            
            try:
                await message.author.send(
                    f"you can submit again in **{hours}h {minutes}m**"
                )
            except:
                pass
            
            return True
        
        # Get content and attachments
        content = message.content
        attachment_urls = [a.url for a in message.attachments]
        
        # Check if content is blacklisted before creating
        content_id = self.storage.generate_content_id(content, attachment_urls)
        if self.storage.is_content_blacklisted(content_id):
            try:
                await message.delete()
            except:
                pass
            
            try:
                await message.author.send(
                    "this content has been previously rejected and cannot be resubmitted."
                )
            except:
                pass
            
            return True
        
        # Create submission
        submission = self.storage.create_submission(
            message_id=str(message.id),
            channel_id=str(message.channel.id),
            guild_path=guild_path,
            author_id=str(message.author.id),
            author_name=message.author.name,
            content=content,
            attachment_urls=attachment_urls,
            expires_hours=self.decision_timeout_hours,
        )
        
        if not submission:
            # Content was blacklisted
            try:
                await message.delete()
            except:
                pass
            return True
        
        # Add vote reactions
        for emoji in [EMOJI_KEEP, EMOJI_REVISE, EMOJI_SLOP]:
            try:
                await message.add_reaction(emoji)
            except Exception as e:
                logger.error(f"failed to add reaction: {e}")
        
        # Create decision view for guild leads
        view = DecisionView(self, submission.id)
        
        # Send decision panel in thread or reply
        try:
            embed = self._create_submission_embed(submission, message.author)
            decision_msg = await message.reply(
                embed=embed,
                view=view,
                mention_author=False,
            )
        except Exception as e:
            logger.error(f"failed to send decision panel: {e}")
        
        logger.info(
            "submission_created",
            submission_id=submission.id,
            author=message.author.name,
            guild_path=guild_path,
        )
        
        return True
    
    def _create_submission_embed(
        self,
        submission: Submission,
        author: discord.Member,
    ) -> discord.Embed:
        """Create embed for submission decision panel."""
        embed = discord.Embed(
            title="📝 content submission",
            description=f"submitted by {author.mention}",
            color=0x83C2EB,
            timestamp=datetime.utcnow(),
        )
        
        embed.add_field(
            name="guild path",
            value=submission.guild_path,
            inline=True,
        )
        
        embed.add_field(
            name="status",
            value="⏳ pending review",
            inline=True,
        )
        
        if submission.revision_count > 0:
            embed.add_field(
                name="revision",
                value=f"#{submission.revision_count}",
                inline=True,
            )
        
        expires_dt = datetime.fromisoformat(submission.expires_at)
        embed.add_field(
            name="expires",
            value=f"<t:{int(expires_dt.timestamp())}:R>",
            inline=True,
        )
        
        embed.set_footer(text="guild leads: use buttons below to decide")
        
        if author.avatar:
            embed.set_thumbnail(url=author.avatar.url)
        
        return embed
    
    async def handle_reaction(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> bool:
        """
        Handle vote reaction on a submission.
        
        Returns True if reaction was processed.
        """
        # Check if it's a vote emoji
        emoji_str = str(payload.emoji)
        if emoji_str not in VOTE_EMOJI_MAP:
            return False
        
        # Get the submission
        submission = self.storage.get_submission_by_message(str(payload.message_id))
        if not submission:
            return False
        
        # Check if submission is still pending
        if submission.status != SubmissionStatus.PENDING.value:
            return False
        
        # Get the member
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return False
        
        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return False
        
        # Check if member has T1+ role
        if not self.has_t1_role(member):
            # Remove their reaction silently
            try:
                channel = self.bot.get_channel(payload.channel_id)
                if channel:
                    message = await channel.fetch_message(payload.message_id)
                    await message.remove_reaction(payload.emoji, member)
            except:
                pass
            return True
        
        # Record the vote
        vote_type = VOTE_EMOJI_MAP[emoji_str]
        self.storage.add_vote(
            submission_id=submission.id,
            voter_id=str(member.id),
            voter_name=member.name,
            vote_type=vote_type,
        )
        
        logger.info(
            "vote_recorded",
            submission_id=submission.id,
            voter=member.name,
            vote_type=vote_type.value,
        )
        
        return True
    
    async def handle_reaction_remove(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> bool:
        """Handle vote reaction removal."""
        emoji_str = str(payload.emoji)
        if emoji_str not in VOTE_EMOJI_MAP:
            return False
        
        submission = self.storage.get_submission_by_message(str(payload.message_id))
        if not submission:
            return False
        
        self.storage.remove_vote(submission.id, str(payload.user_id))
        return True
    
    async def process_approval(
        self,
        submission: Submission,
        decision_by: discord.Member,
        spotlight: bool = False,
    ) -> bool:
        """Process approval of a submission."""
        # Update submission status
        success = self.storage.decide_submission(
            submission_id=submission.id,
            status=SubmissionStatus.APPROVED,
            decision_by=str(decision_by.id),
        )
        
        if not success:
            return False
        
        # Forward to approved channel
        approved_channel = self.bot.get_channel(self.approved_channel_id)
        if not approved_channel:
            logger.error("approved channel not found")
            return False
        
        # Get original message
        try:
            submission_channel = self.bot.get_channel(int(submission.channel_id))
            original_message = await submission_channel.fetch_message(int(submission.message_id))
        except:
            original_message = None
        
        # Create forward embed
        author = self.bot.get_user(int(submission.author_id))
        embed = discord.Embed(
            description=submission.content if submission.content else None,
            color=0x00FF00 if not spotlight else 0xFFD700,
            timestamp=datetime.utcnow(),
        )
        
        if author:
            embed.set_author(
                name=author.display_name,
                icon_url=author.avatar.url if author.avatar else None,
            )
        
        if spotlight:
            embed.title = "⭐ spotlight"
        
        embed.set_footer(text=f"guild: {submission.guild_path}")
        
        # Handle attachments
        import json
        attachment_urls = json.loads(submission.attachment_urls) if submission.attachment_urls else []
        if attachment_urls:
            embed.set_image(url=attachment_urls[0])
        
        # Send to approved channel
        try:
            target_channel = self.spotlight_channel_id if spotlight else self.approved_channel_id
            channel = self.bot.get_channel(target_channel) or approved_channel
            
            forwarded_msg = await channel.send(embed=embed)
            
            # Update with forwarded message ID
            self.storage.update_forwarded_message(submission.id, str(forwarded_msg.id))
            
            # Add to spotlight if requested
            if spotlight:
                self.storage.add_to_spotlight(
                    submission_id=submission.id,
                    spotlighted_by=str(decision_by.id),
                    spotlight_message_id=str(forwarded_msg.id),
                )
        except Exception as e:
            logger.error(f"failed to forward content: {e}")
            return False
        
        # Delete original from submission channel
        if original_message:
            try:
                await original_message.delete()
            except:
                pass
        
        # DM the author
        if author:
            try:
                status_emoji = "⭐" if spotlight else "✅"
                await author.send(
                    f"{status_emoji} your submission has been {'spotlighted' if spotlight else 'approved'}!\n"
                    f"view it here: {forwarded_msg.jump_url}"
                )
            except:
                pass
        
        logger.info(
            "submission_approved",
            submission_id=submission.id,
            decision_by=decision_by.name,
            spotlight=spotlight,
        )
        
        return True
    
    async def process_revision_decision(
        self,
        submission: Submission,
        decision_by: discord.Member,
        feedback: str,
    ) -> bool:
        """Process 'needs work' decision with feedback."""
        # Check max revisions
        if submission.revision_count >= self.max_revisions:
            # Auto-reject after max revisions
            return await self.process_rejection(
                submission=submission,
                decision_by=decision_by,
                reason=f"exceeded maximum revisions ({self.max_revisions})",
            )
        
        # Update status
        success = self.storage.decide_submission(
            submission_id=submission.id,
            status=SubmissionStatus.NEEDS_REVISION,
            decision_by=str(decision_by.id),
            reason=feedback,
        )
        
        if not success:
            return False
        
        # Delete original message
        try:
            channel = self.bot.get_channel(int(submission.channel_id))
            message = await channel.fetch_message(int(submission.message_id))
            await message.delete()
        except:
            pass
        
        # DM the author with feedback
        author = self.bot.get_user(int(submission.author_id))
        if author:
            try:
                embed = discord.Embed(
                    title="🟡 revision requested",
                    description=f"your submission in **{submission.guild_path}** needs work.",
                    color=0xFFFF00,
                )
                
                embed.add_field(
                    name="feedback",
                    value=feedback,
                    inline=False,
                )
                
                embed.add_field(
                    name="your content",
                    value=submission.content[:500] + "..." if len(submission.content) > 500 else submission.content,
                    inline=False,
                )
                
                embed.add_field(
                    name="revisions remaining",
                    value=f"{self.max_revisions - submission.revision_count}",
                    inline=True,
                )
                
                embed.set_footer(text="resubmit your improved content to the same channel")
                
                await author.send(embed=embed)
            except Exception as e:
                logger.error(f"failed to DM author: {e}")
        
        logger.info(
            "submission_needs_revision",
            submission_id=submission.id,
            decision_by=decision_by.name,
        )
        
        return True
    
    async def process_rejection(
        self,
        submission: Submission,
        decision_by: discord.Member,
        reason: str,
    ) -> bool:
        """Process rejection of a submission."""
        # Update status (this also blacklists the content)
        success = self.storage.decide_submission(
            submission_id=submission.id,
            status=SubmissionStatus.REJECTED,
            decision_by=str(decision_by.id),
            reason=reason,
        )
        
        if not success:
            return False
        
        # Delete original message
        try:
            channel = self.bot.get_channel(int(submission.channel_id))
            message = await channel.fetch_message(int(submission.message_id))
            await message.delete()
        except:
            pass
        
        # Check for cooldown
        consecutive = self.storage.get_consecutive_rejections(
            submission.author_id,
            submission.guild_path,
        )
        
        cooldown_hours = 0
        for threshold, hours in sorted(COOLDOWN_TIERS.items()):
            if consecutive >= threshold:
                cooldown_hours = hours
        
        if cooldown_hours > 0:
            self.storage.set_cooldown(
                user_id=submission.author_id,
                guild_path=submission.guild_path,
                hours=cooldown_hours,
                reason=f"repeated rejections ({consecutive})",
            )
        
        # DM the author
        author = self.bot.get_user(int(submission.author_id))
        if author:
            try:
                embed = discord.Embed(
                    title="🔴 submission rejected",
                    description=f"your submission in **{submission.guild_path}** was not approved.",
                    color=0xFF0000,
                )
                
                if reason:
                    embed.add_field(
                        name="reason",
                        value=reason,
                        inline=False,
                    )
                
                if cooldown_hours > 0:
                    embed.add_field(
                        name="cooldown",
                        value=f"you can submit again in **{cooldown_hours} hours**",
                        inline=False,
                    )
                
                embed.set_footer(text="this content cannot be resubmitted")
                
                await author.send(embed=embed)
            except Exception as e:
                logger.error(f"failed to DM author: {e}")
        
        logger.info(
            "submission_rejected",
            submission_id=submission.id,
            decision_by=decision_by.name,
            cooldown_hours=cooldown_hours,
        )
        
        return True
    
    async def process_expired_submissions(self):
        """Process submissions that expired without a decision."""
        expired = self.storage.get_expired_submissions()
        
        for submission in expired:
            # Mark as expired
            self.storage.decide_submission(
                submission_id=submission.id,
                status=SubmissionStatus.EXPIRED,
                decision_by="system",
                reason="no decision within timeout period",
            )
            
            # Delete the message
            try:
                channel = self.bot.get_channel(int(submission.channel_id))
                message = await channel.fetch_message(int(submission.message_id))
                await message.delete()
            except:
                pass
            
            # Notify the author
            author = self.bot.get_user(int(submission.author_id))
            if author:
                try:
                    await author.send(
                        f"⏰ your submission in **{submission.guild_path}** expired without a decision. "
                        f"feel free to resubmit."
                    )
                except:
                    pass
            
            logger.info("submission_expired", submission_id=submission.id)
    
    async def start_expiry_checker(self):
        """Start background task to check for expired submissions."""
        while True:
            try:
                await self.process_expired_submissions()
            except Exception as e:
                logger.error(f"expiry checker error: {e}")
            
            await asyncio.sleep(300)  # Check every 5 minutes


def setup_submission_commands(bot: discord.Client, handler: SubmissionHandler):
    """Setup slash commands for submission system."""
    
    @app_commands.command(
        name="portfolio",
        description="view your approved content portfolio",
    )
    async def portfolio_cmd(interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        approved = handler.storage.get_user_approved_content(str(target.id), limit=10)
        
        if not approved:
            await interaction.response.send_message(
                f"{target.mention} has no approved content yet.",
                ephemeral=True,
            )
            return
        
        embed = discord.Embed(
            title=f"📁 {target.display_name}'s portfolio",
            description=f"{len(approved)} approved submissions",
            color=0x83C2EB,
        )
        
        for i, sub in enumerate(approved[:5], 1):
            content_preview = sub.content[:100] + "..." if len(sub.content) > 100 else sub.content
            embed.add_field(
                name=f"{i}. {sub.guild_path}",
                value=content_preview or "[attachment]",
                inline=False,
            )
        
        if target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="submission_stats",
        description="view submission statistics (guild leads only)",
    )
    async def stats_cmd(interaction: discord.Interaction, guild_path: str = None):
        if not handler.is_guild_lead(interaction.user):
            await interaction.response.send_message(
                "❌ only guild leads can view stats",
                ephemeral=True,
            )
            return
        
        if guild_path:
            stats = handler.storage.get_guild_stats(guild_path)
            embed = discord.Embed(
                title=f"📊 {guild_path} submission stats",
                color=0x83C2EB,
            )
            embed.add_field(name="total", value=stats.get("total", 0), inline=True)
            embed.add_field(name="approved", value=stats.get("approved", 0), inline=True)
            embed.add_field(name="pending", value=stats.get("pending", 0), inline=True)
            embed.add_field(name="revisions", value=stats.get("revisions", 0), inline=True)
            embed.add_field(name="rejected", value=stats.get("rejected", 0), inline=True)
        else:
            embed = discord.Embed(
                title="📊 overall submission stats",
                color=0x83C2EB,
            )
            for path in ["traders", "content", "designers"]:
                stats = handler.storage.get_guild_stats(path)
                if stats.get("total", 0) > 0:
                    embed.add_field(
                        name=path,
                        value=f"✅ {stats.get('approved', 0)} | 🔴 {stats.get('rejected', 0)} | ⏳ {stats.get('pending', 0)}",
                        inline=False,
                    )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    bot.tree.add_command(portfolio_cmd)
    bot.tree.add_command(stats_cmd)
    
    return handler
