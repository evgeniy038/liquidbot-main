"""
Promotion notifier for Discord role updates.

Sends congratulatory messages when members receive specific promotion roles.
Now includes personalized image generation with username overlays.
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime
import discord
from src.utils import get_config, get_logger
from src.moderation.image_generator import get_image_generator

logger = get_logger(__name__)

# Guild role mapping: role_id -> {guild, role_name, tier}
GUILD_ROLES = {
    # traders
    "1449055127049605312": {"guild": "traders", "role": "tide", "tier": 1},
    "1449055171685515354": {"guild": "traders", "role": "degen", "tier": 2},
    "1449055325020754100": {"guild": "traders", "role": "speculator", "tier": 3},
    # content
    "1449054897486954506": {"guild": "content creators", "role": "drip", "tier": 1},
    "1449054975107010673": {"guild": "content creators", "role": "frame", "tier": 2},
    "1449055051829084353": {"guild": "content creators", "role": "orator", "tier": 3},
    # designers
    "1449054607899758726": {"guild": "designers", "role": "ink", "tier": 1},
    "1449054761650225244": {"guild": "designers", "role": "sketch", "tier": 2},
    "1449054806038675569": {"guild": "designers", "role": "sculptor", "tier": 3},
}

EVENT_WINNER_ROLE_IDS = {
    1443237596384985263,  # event winner role id
}

def get_role_guild_info(role_id: str) -> Optional[Dict]:
    """Get guild info for a role ID."""
    return GUILD_ROLES.get(str(role_id))

def get_member_guilds(member: discord.Member) -> List[str]:
    """Get list of guild names the member is in based on their roles."""
    guilds = set()
    for role in member.roles:
        info = get_role_guild_info(str(role.id))
        if info:
            guilds.add(info["guild"])
    return list(guilds)


class PromotionNotifier:
    """
    handles promotion announcements when members receive special roles.
    
    monitors role changes and sends congratulatory messages to a
    designated channel when promotion roles are added.
    """
    
    def __init__(self):
        """Initialize promotion notifier."""
        self.config = get_config()
        self.promo_config = self.config.member_update.promotions
        
        self.enabled = self.promo_config.enabled
        self.channel_id = self.promo_config.channel_id
        self.promotion_role_ids = [
            str(role_id) for role_id in self.promo_config.promotion_role_ids
        ]
        self.debounce_seconds = self.promo_config.debounce_seconds
        
        # Debounce tracking: {user_id: last_announcement_timestamp}
        self.last_announcement: Dict[int, float] = {}
        
        # Silent init
    
    def get_role_changes(
        self,
        before: discord.Member,
        after: discord.Member,
    ) -> Dict[str, Set[str]]:
        """
        Get role changes between before and after states.
        
        Args:
            before: Member state before update
            after: Member state after update
            
        Returns:
            Dictionary with 'added' and 'removed' role ID sets
        """
        before_roles = {str(role.id) for role in before.roles}
        after_roles = {str(role.id) for role in after.roles}
        
        return {
            "added": after_roles - before_roles,
            "removed": before_roles - after_roles,
        }
    
    def get_promotion_roles_added(
        self,
        before: discord.Member,
        after: discord.Member,
    ) -> List[discord.Role]:
        """
        Get promotion roles that were added to member.
        
        Args:
            before: Member state before update
            after: Member state after update
            
        Returns:
            List of promotion roles that were added
        """
        if not self.enabled:
            return []
        
        # Get role changes
        changes = self.get_role_changes(before, after)
        added_role_ids = changes["added"]
        
        # Filter for promotion roles
        promotion_role_ids_added = added_role_ids.intersection(
            self.promotion_role_ids
        )
        
        if not promotion_role_ids_added:
            return []
        
        # Get actual role objects
        promotion_roles = []
        for role_id in promotion_role_ids_added:
            role = after.guild.get_role(int(role_id))
            if role:
                promotion_roles.append(role)
        
        return promotion_roles
    
    def should_announce(self, member: discord.Member) -> bool:
        """
        Check if we should announce promotion for this member.
        
        Uses debouncing to prevent spam from rapid role changes.
        
        Args:
            member: Member to check
            
        Returns:
            True if announcement should be sent, False if debounced
        """
        now = datetime.now().timestamp()
        last_time = self.last_announcement.get(member.id, 0)
        
        # Check debounce
        if now - last_time < self.debounce_seconds:
            logger.debug(
                "promotion_announcement_debounced",
                user_id=str(member.id),
                seconds_since_last=now - last_time,
            )
            return False
        
        # Update last announcement time
        self.last_announcement[member.id] = now
        return True
    
    async def announce_promotion(
        self,
        member: discord.Member,
        roles: List[discord.Role],
    ) -> None:
        """
        Send promotion announcement to configured channel.
        
        Args:
            member: Member who received promotion
            roles: List of promotion roles that were added
        """
        if not self.enabled:
            return
        
        if not roles:
            return
        
        # Check debounce
        if not self.should_announce(member):
            return
        
        try:
            # Validate channel config
            if not self.channel_id or self.channel_id == "YOUR_PROMOTION_CHANNEL_ID":
                logger.warning("promotion_channel_not_configured")
                return
            
            # Get channel
            channel = member.guild.get_channel(int(self.channel_id))
            if not channel:
                channel = await member.guild.fetch_channel(int(self.channel_id))
            
            if not channel or not isinstance(channel, discord.TextChannel):
                logger.error(
                    "promotion_channel_not_found",
                    channel_id=self.channel_id,
                )
                return
            
            is_event_winner = any(role.id in EVENT_WINNER_ROLE_IDS for role in roles)
            
            # Build role mentions
            role_mentions = " · ".join([f"<@&{role.id}>" for role in roles])
            
            # Build embed
            embed_config = self.promo_config.embed
            
            # Build detailed info for guild roles
            role_details = []
            for role in roles:
                guild_info = get_role_guild_info(str(role.id))
                if guild_info:
                    role_details.append({
                        "role": role,
                        "guild": guild_info["guild"],
                        "tier": guild_info["tier"],
                        "role_name": guild_info["role"],
                    })
            
            # Get member's current guilds
            member_guilds = get_member_guilds(member)
                
            if is_event_winner:
                # Event winner promotion
                embed_title = "⭐ achievement"
                description = (
                    f"congrats {member.mention}.\n\n"
                    f"you won a community event.\n\n"
                    f"well played."
                )

            elif role_details:
                # Guild role promotion
                detail = role_details[0]
                guild_text = detail["guild"]

                description = (
                    f"congrats {member.mention}, you just unlocked {role_mentions}.\n\n"
                    f"new rank: **level {detail['tier']}** in **{guild_text}**\n\n"
                    f"keep going. this counts."
                )

            else:
                # Non-guild role promotion
                description = (
                    f"congrats {member.mention}, you just unlocked {role_mentions}.\n\n"
                    f"the work was noticed.\n\n"
                    f"keep going."
                )
            
            embed = discord.Embed(
                color=embed_config.color,
                title=embed_config.title,
                description=description,
            )

            if is_event_winner:
                # Event winner promotion
                embed_title = "⭐ achievement"
            
            # Add thumbnail (user avatar)
            if embed_config.thumbnail_enabled:
                embed.set_thumbnail(
                    url=member.display_avatar.url
                )
            
            # Generate personalized image with username
            # Get role info for image generation
            primary_role = roles[0]
            primary_role_id = str(primary_role.id)
            primary_role_name = primary_role.name
            
            # For guild roles, use the guild role name
            if role_details:
                primary_role_name = role_details[0]["role_name"].capitalize()
            
            image_generator = get_image_generator()
            personalized_image = await image_generator.generate_promotion_image(
                username=member.name,
                role_id=primary_role_id,
                role_name=primary_role_name,
            )
            
            # Prepare file attachment if image was generated
            file_attachment = None
            if personalized_image:
                file_attachment = discord.File(
                    personalized_image,
                    filename=f"promotion_{member.id}.png"
                )
                embed.set_image(url=f"attachment://promotion_{member.id}.png")
            elif embed_config.image_url:
                # Fallback to static image URL if generation failed
                embed.set_image(url=embed_config.image_url)
            

            
            # Send message with personalized image
            send_kwargs = {
                "content": member.mention,
                "embed": embed,
                "allowed_mentions": discord.AllowedMentions(users=[member]),
            }
            if file_attachment:
                send_kwargs["file"] = file_attachment
            
            await channel.send(**send_kwargs)
            
            logger.info(
                "promotion_announced",
                user_id=str(member.id),
                user_tag=str(member),
                roles=[role.name for role in roles],
                channel_id=self.channel_id,
                personalized_image=personalized_image is not None,
            )
            
        except Exception as e:
            logger.error(
                "promotion_announcement_failed",
                user_id=str(member.id),
                error=str(e),
                exc_info=True,
            )
    
    async def check_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ) -> None:
        """
        Check member update for promotion roles and announce if found.
        
        Args:
            before: Member state before update
            after: Member state after update
        """
        if not self.enabled:
            return
        
        # Skip bots
        if after.bot:
            return
        
        # Get promotion roles added
        promotion_roles = self.get_promotion_roles_added(before, after)
        
        if promotion_roles:
            logger.debug(
                "promotion_roles_detected",
                user_id=str(after.id),
                roles=[role.name for role in promotion_roles],
            )
            
            await self.announce_promotion(after, promotion_roles)
