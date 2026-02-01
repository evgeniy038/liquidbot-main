"""
Member event handler.

Handles member-related events:
- on_member_join: New member checks (impersonation, suspicious Unicode)
- on_member_update: Nickname changes, role promotions
- on_user_update: Username/global name changes

Extracted from client.py for better maintainability.
"""

from typing import Optional, List, Set, TYPE_CHECKING

import discord

from src.utils import get_logger

if TYPE_CHECKING:
    from src.moderation import ImpersonationChecker, PromotionNotifier

logger = get_logger(__name__)


class MemberHandler:
    """
    Handler for member-related Discord events.
    
    Features:
    - Suspicious Unicode detection in names
    - Impersonation prevention
    - Promotion announcements
    - Name change logging
    """
    
    # Suspicious Unicode ranges (scam prevention)
    SUSPICIOUS_RANGES = [
        (0x0600, 0x06FF),  # Arabic (includes diacritics)
        (0x0750, 0x077F),  # Arabic Supplement
        (0x08A0, 0x08FF),  # Arabic Extended-A
        (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
        (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
        (0x200B, 0x200F),  # Zero-width spaces and direction marks
        (0x2028, 0x202F),  # Line/paragraph separators
        (0x2060, 0x206F),  # Word joiner, invisible operators
        (0xFEFF, 0xFEFF),  # Zero-width no-break space (BOM)
    ]
    
    def __init__(
        self,
        bot: discord.Client,
        impersonation_checker: Optional["ImpersonationChecker"] = None,
        promotion_notifier: Optional["PromotionNotifier"] = None,
    ):
        """
        Initialize member handler.
        
        Args:
            bot: Discord bot instance
            impersonation_checker: Impersonation checker instance
            promotion_notifier: Promotion notifier instance
        """
        self.bot = bot
        self.impersonation_checker = impersonation_checker
        self.promotion_notifier = promotion_notifier
    
    def contains_suspicious_unicode(self, text: str) -> bool:
        """
        Check if text contains suspicious Unicode characters.
        
        Detects:
        - Arabic diacritics and invisible modifiers
        - Zero-width characters
        - Other invisible/combining characters
        
        Args:
            text: Text to check
            
        Returns:
            True if suspicious characters found
        """
        if not text:
            return False
        
        for char in text:
            code = ord(char)
            for start, end in self.SUSPICIOUS_RANGES:
                if start <= code <= end:
                    return True
        
        return False
    
    async def ban_user_in_guilds(
        self, 
        user: discord.User, 
        reason: str
    ) -> List[str]:
        """
        Ban user in all mutual guilds.
        
        Args:
            user: Discord user to ban
            reason: Reason for the ban
            
        Returns:
            List of guild names where user was banned
        """
        banned_in = []
        
        for guild in self.bot.guilds:
            try:
                member = guild.get_member(user.id)
                if not member:
                    continue
                
                # Skip bots and admins
                if member.bot or member.guild_permissions.administrator:
                    continue
                
                # Check if bot has permissions
                if not guild.me.guild_permissions.ban_members:
                    logger.warning(f"No ban_members permission in {guild.name}")
                    continue
                
                # Ban user
                await guild.ban(user, reason=reason, delete_message_days=1)
                banned_in.append(guild.name)
                
                logger.warning(
                    f"🔨 AUTO_BAN | @{user.name} ({user.id}) | "
                    f"Guild: {guild.name} | Reason: {reason}"
                )
                
            except discord.Forbidden:
                logger.warning(f"Cannot ban {user.name} in {guild.name} - forbidden")
            except Exception as e:
                logger.error(f"Failed to ban {user.name} in {guild.name}: {e}")
        
        return banned_in
    
    async def handle_member_join(self, member: discord.Member):
        """
        Handle new member joins.
        
        Checks:
        - Suspicious Unicode in name
        - Impersonation attempt
        
        Args:
            member: New member
        """
        if member.bot:
            return
        
        # Check for suspicious Unicode in name
        display_name = member.global_name or member.name
        if self.contains_suspicious_unicode(display_name):
            logger.warning(
                f"🚨 NEW_MEMBER_SUSPICIOUS | @{member.name} ({member.id}) | "
                f"Name: '{display_name}' | Contains suspicious Unicode"
            )
            
            # Auto-ban for suspicious Unicode names
            try:
                if member.guild.me.guild_permissions.ban_members:
                    await member.guild.ban(
                        member, 
                        reason=f"Suspicious Unicode in name on join: '{display_name}'",
                        delete_message_days=1
                    )
                    logger.warning(
                        f"🔨 AUTO_BAN_ON_JOIN | @{member.name} ({member.id}) | "
                        f"Guild: {member.guild.name}"
                    )
            except Exception as e:
                logger.error(f"Failed to ban suspicious new member: {e}")
        
        # Check for impersonation on join
        if self.impersonation_checker:
            result = self.impersonation_checker.score_name_impersonation(
                member, member.display_name
            )
            
            if result["is_impersonation"]:
                logger.warning(
                    f"⚠️ New member with suspicious name: @{member.name} "
                    f"({member.display_name}) matches '{result['closest_match']}'"
                )
                
                # Send alert
                impersonation_data = {
                    **result,
                    "member": member,
                    "old_name": "(new member)",
                    "new_name": member.display_name,
                }
                await self.impersonation_checker.send_alert(
                    member.guild, 
                    impersonation_data
                )
    
    async def handle_member_update(
        self, 
        before: discord.Member, 
        after: discord.Member
    ):
        """
        Handle member updates (nickname, roles).
        
        Features:
        - Anti-impersonation check
        - Nickname change logging
        - Promotion announcements
        
        Args:
            before: Member before update
            after: Member after update
        """
        try:
            if after.bot:
                return
            
            logger.debug(
                "member_update_event",
                user_id=str(after.id),
                user_tag=str(after),
                guild=after.guild.name,
            )
            
            # === Anti-Impersonation Check ===
            if self.impersonation_checker:
                impersonation_data = await self.impersonation_checker.check_member_update(
                    before, after
                )
                
                if impersonation_data:
                    logger.warning(
                        "impersonation_detected",
                        user_id=str(after.id),
                        old_name=impersonation_data["old_name"],
                        new_name=impersonation_data["new_name"],
                        similarity=impersonation_data["score"],
                    )
                    
                    # Try to reset nickname
                    reset_success = await self.impersonation_checker.reset_nickname(after)
                    
                    if reset_success:
                        logger.info(f"🔄 Nickname reset: @{after.name}")
                    
                    # Send alert to security channel
                    await self.impersonation_checker.send_alert(
                        after.guild,
                        impersonation_data,
                    )
            
            # === Log Nickname Changes ===
            if before.nick != after.nick:
                logger.info(
                    f"📝 NICKNAME_CHANGE | @{after.name} ({after.id}) | "
                    f"'{before.nick or '(none)'}' → '{after.nick or '(none)'}' | "
                    f"Guild: {after.guild.name}"
                )
            
            # === Promotion Announcements ===
            if self.promotion_notifier:
                await self.promotion_notifier.check_member_update(before, after)
        
        except Exception as e:
            logger.error(
                "member_update_error",
                user_id=str(after.id) if after else "unknown",
                error=str(e),
                exc_info=True,
            )
    
    async def handle_user_update(
        self, 
        before: discord.User, 
        after: discord.User
    ):
        """
        Handle user profile updates (username, global name, avatar).
        
        Features:
        - Log username changes
        - Log global name changes
        - Auto-ban for suspicious Unicode
        
        Args:
            before: User before update
            after: User after update
        """
        try:
            # Log username changes
            if before.name != after.name:
                logger.info(
                    f"🔄 USERNAME_CHANGE | @{before.name} → @{after.name} | "
                    f"User ID: {after.id}"
                )
            
            # Log global display name changes
            if before.global_name != after.global_name:
                logger.info(
                    f"🌐 GLOBAL_NAME_CHANGE | @{after.name} ({after.id}) | "
                    f"'{before.global_name or '(none)'}' → '{after.global_name or '(none)'}'"
                )
            
            # === Auto-ban for suspicious Unicode characters ===
            new_name = after.global_name or after.name
            old_name = before.global_name or before.name
            
            # Only check if name actually changed
            if new_name != old_name and self.contains_suspicious_unicode(new_name):
                logger.warning(
                    f"🚨 SUSPICIOUS_NAME_DETECTED | @{after.name} ({after.id}) | "
                    f"Name: '{new_name}' | Contains suspicious Unicode"
                )
                
                # Auto-ban for suspicious Unicode names
                banned_guilds = await self.ban_user_in_guilds(
                    after,
                    reason=f"Suspicious Unicode in name: '{new_name}' - scam attempt",
                )
                
                if banned_guilds:
                    logger.warning(
                        f"🔨 SCAM_PREVENTION | @{after.name} ({after.id}) "
                        f"banned in: {', '.join(banned_guilds)}"
                    )
        
        except Exception as e:
            logger.error(
                "user_update_error",
                user_id=str(after.id) if after else "unknown",
                error=str(e),
                exc_info=True,
            )
