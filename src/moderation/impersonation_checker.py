"""
Anti-impersonation checker for Discord member names and nicknames.

Detects when users try to impersonate staff or brand names by checking
similarity between their display names and protected names.
"""

from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple
import discord
from src.utils import get_config, get_logger

logger = get_logger(__name__)


class ImpersonationChecker:
    """
    Checks member nicknames and usernames for impersonation attempts.
    
    Uses similarity scoring to detect when users try to impersonate
    protected names (staff, brand, etc.).
    """
    
    def __init__(self, message_storage=None):
        """Initialize impersonation checker."""
        self.config = get_config()
        self.anti_imp_config = self.config.member_update.anti_impersonation
        self.message_storage = message_storage
        
        self.enabled = self.anti_imp_config.enabled
        self.similarity_threshold = self.anti_imp_config.similarity_threshold
        self.hard_threshold = self.anti_imp_config.hard_threshold
        self.protected_names = self.anti_imp_config.protected_names
        self.trusted_role_ids = [
            str(role_id) for role_id in self.anti_imp_config.trusted_role_ids
        ]
        self.trusted_message_count = getattr(
            self.anti_imp_config, 'trusted_message_count', 100
        )
        
        # Silent init
    
    def set_message_storage(self, storage):
        """Set message storage for checking user message count."""
        self.message_storage = storage
    
    def get_user_message_count(self, user_id: str) -> int:
        """
        Get the number of messages a user has sent.
        
        Args:
            user_id: Discord user ID
            
        Returns:
            Number of messages in database
        """
        if not self.message_storage:
            return 0
        
        try:
            stats = self.message_storage.get_user_stats(user_id)
            return stats.get("total_messages", 0)
        except Exception as e:
            logger.debug(f"could not get message count for {user_id}: {e}")
            return 0
    
    def is_trusted(self, member: discord.Member) -> bool:
        """
        Check if member has a trusted role.
        
        Args:
            member: Discord member to check
            
        Returns:
            True if member has a trusted role, False otherwise
        """
        if not member.roles:
            return False
        
        member_role_ids = {str(role.id) for role in member.roles}
        return bool(member_role_ids.intersection(self.trusted_role_ids))
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings.
        
        Uses SequenceMatcher for fuzzy string matching.
        Case-insensitive comparison.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings (lowercase, strip whitespace)
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        # Exact match
        if s1 == s2:
            return 1.0
        
        # Calculate similarity
        return SequenceMatcher(None, s1, s2).ratio()
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize name for comparison by removing common obfuscation characters.
        
        Args:
            name: Name to normalize
            
        Returns:
            Normalized name (lowercase, special chars removed)
        """
        if not name:
            return ""
        
        # Lowercase
        normalized = name.lower()
        
        # Remove common obfuscation characters
        obfuscation_chars = ['_', '-', '.', ' ', '|', '/', '\\', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '[', ']', '{', '}', '<', '>', '~', '`', "'", '"', ',', ';', ':', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        for char in obfuscation_chars:
            normalized = normalized.replace(char, '')
        
        return normalized
    
    def _check_contains_protected(self, display_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if display name CONTAINS any protected name.
        
        This catches cases like "MEE6_Support" or "Admin_Helper" etc.
        
        Args:
            display_name: Display name to check
            
        Returns:
            Tuple of (is_match, matched_name)
        """
        name_lower = display_name.lower()
        name_normalized = self._normalize_name(display_name)
        
        for protected_name in self.protected_names:
            protected_lower = protected_name.lower()
            protected_normalized = self._normalize_name(protected_name)
            
            # Skip very short names to avoid false positives (like "mod" in "modern")
            if len(protected_normalized) < 4:
                continue
            
            # Check if protected name is contained in display name
            if protected_lower in name_lower or protected_normalized in name_normalized:
                return True, protected_name
        
        return False, None
    
    def score_name_impersonation(
        self,
        member: discord.Member,
        display_name: str,
    ) -> Dict[str, any]:
        """
        Score a member's display name for impersonation.
        
        Checks similarity against all protected names and returns
        the highest similarity score.
        
        Args:
            member: Discord member being checked
            display_name: Display name to check (nickname or username)
            
        Returns:
            Dictionary with:
                - score: Highest similarity score (0.0-1.0)
                - closest_match: Name that was most similar
                - is_impersonation: Whether score exceeds threshold
                - is_high_confidence: Whether score exceeds hard threshold
        """
        if not display_name:
            return {
                "score": 0.0,
                "closest_match": None,
                "is_impersonation": False,
                "is_high_confidence": False,
            }
        
        # First check: Does the name CONTAIN a protected name?
        contains_match, contained_name = self._check_contains_protected(display_name)
        if contains_match:
            return {
                "score": 0.95,  # High score for direct containment
                "closest_match": contained_name,
                "is_impersonation": True,
                "is_high_confidence": True,
            }
        
        max_score = 0.0
        closest_match = None
        
        # Second check: Similarity scoring
        name_normalized = self._normalize_name(display_name)
        
        for protected_name in self.protected_names:
            # Standard similarity
            score = self.calculate_similarity(display_name, protected_name)
            
            # Also check normalized similarity (catches M_E_E_6 -> mee6)
            protected_normalized = self._normalize_name(protected_name)
            if name_normalized and protected_normalized:
                normalized_score = self.calculate_similarity(name_normalized, protected_normalized)
                score = max(score, normalized_score)
            
            if score > max_score:
                max_score = score
                closest_match = protected_name
        
        return {
            "score": max_score,
            "closest_match": closest_match,
            "is_impersonation": max_score >= self.similarity_threshold,
            "is_high_confidence": max_score >= self.hard_threshold,
        }
    
    async def check_member_update(
        self,
        before: discord.Member,
        after: discord.Member,
    ) -> Optional[Dict[str, any]]:
        """
        Check member update for impersonation attempt.
        
        Args:
            before: Member state before update
            after: Member state after update
            
        Returns:
            Impersonation data if detected, None otherwise
        """
        user_id = str(after.id)
        old_display = before.display_name
        new_display = after.display_name
        
        # Log all name changes for debugging
        if old_display != new_display:
            logger.info(
                f"👤 NAME_CHANGE | @{after.name} ({user_id}) | '{old_display}' → '{new_display}'"
            )
        
        if not self.enabled:
            logger.debug(f"impersonation_check_disabled | user={user_id}")
            return None
        
        # Skip bots
        if after.bot:
            logger.debug(f"impersonation_skip_bot | user={user_id}")
            return None
        
        # Skip trusted members (by role)
        if self.is_trusted(after):
            logger.info(
                f"✅ IMPERSONATION_SKIP | @{after.name} | reason=trusted_role"
            )
            return None
        
        # Skip users with 100+ messages (established community members)
        message_count = self.get_user_message_count(user_id)
        if message_count >= self.trusted_message_count:
            logger.info(
                f"✅ IMPERSONATION_SKIP | @{after.name} | reason=active_member ({message_count} msgs)"
            )
            return None
        
        # Check if name changed
        if old_display == new_display:
            return None
        
        # Score impersonation
        result = self.score_name_impersonation(after, new_display)
        
        # Log the check result
        logger.info(
            f"🔍 IMPERSONATION_CHECK | @{after.name} ({user_id}) | "
            f"name='{new_display}' | msgs={message_count} | "
            f"score={result['score']*100:.1f}% | match='{result['closest_match']}' | "
            f"flagged={result['is_impersonation']}"
        )
        
        # Return data if impersonation detected
        if result["is_impersonation"]:
            logger.warning(
                f"🚨 IMPERSONATION_DETECTED | @{after.name} ({user_id}) | "
                f"'{old_display}' → '{new_display}' | "
                f"score={result['score']*100:.1f}% | match='{result['closest_match']}' | "
                f"msgs={message_count} | high_confidence={result['is_high_confidence']}"
            )
            
            return {
                **result,
                "member": after,
                "old_name": old_display,
                "new_name": new_display,
                "message_count": message_count,
            }
        
        return None
    
    async def reset_nickname(
        self,
        member: discord.Member,
        reason: str = "Anti-impersonation: nickname too similar to protected name",
    ) -> bool:
        """
        Reset member's nickname.
        
        Args:
            member: Member whose nickname to reset
            reason: Reason for nickname reset (for audit log)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if member.guild_permissions.administrator:
                logger.warning(
                    "cannot_reset_admin_nickname",
                    user_id=str(member.id),
                    user_tag=str(member),
                )
                return False
            
            # Check if bot has permissions
            if not member.guild.me.guild_permissions.manage_nicknames:
                logger.warning("bot_lacks_manage_nicknames_permission")
                return False
            
            # Reset nickname
            await member.edit(nick=None, reason=reason)
            
            logger.info(
                "nickname_reset",
                user_id=str(member.id),
                user_tag=str(member),
                reason=reason,
            )
            
            return True
            
        except discord.Forbidden:
            logger.warning(
                "cannot_reset_nickname_forbidden",
                user_id=str(member.id),
                user_tag=str(member),
            )
            return False
        except Exception as e:
            logger.error(
                "nickname_reset_failed",
                user_id=str(member.id),
                user_tag=str(member),
                error=str(e),
            )
            return False
    
    async def send_alert(
        self,
        guild: discord.Guild,
        impersonation_data: Dict[str, any],
    ) -> None:
        """
        Send impersonation alert to log channel.
        
        Args:
            guild: Discord guild where impersonation occurred
            impersonation_data: Data from check_member_update
        """
        try:
            log_channel_id = self.anti_imp_config.log_channel_id
            
            if not log_channel_id or log_channel_id == "YOUR_SECURITY_LOG_CHANNEL_ID":
                logger.debug("impersonation_log_channel_not_configured")
                return
            
            # Get channel
            channel = guild.get_channel(int(log_channel_id))
            if not channel:
                channel = await guild.fetch_channel(int(log_channel_id))
            
            if not channel or not isinstance(channel, discord.TextChannel):
                logger.warning(
                    "impersonation_log_channel_not_found",
                    channel_id=log_channel_id,
                )
                return
            
            # Build embed
            member = impersonation_data["member"]
            score = impersonation_data["score"]
            is_high_confidence = impersonation_data["is_high_confidence"]
            message_count = impersonation_data.get("message_count", 0)
            
            color = 0xFF0033 if is_high_confidence else 0xFFA500
            title = "🚫 Strong Impersonation Attempt" if is_high_confidence else "⚠️ Possible Impersonation Attempt"
            
            embed = discord.Embed(
                color=color,
                title=title,
                description=(
                    f"**User:** {member.mention} ({member.name})\n"
                    f"**User ID:** `{member.id}`\n"
                    f"**Old Name:** `{impersonation_data['old_name']}`\n"
                    f"**New Name:** `{impersonation_data['new_name']}`\n\n"
                    f"**Closest Match:** `{impersonation_data['closest_match']}`\n"
                    f"**Similarity:** `{score * 100:.1f}%`\n"
                    f"**Messages in DB:** `{message_count}` (need {self.trusted_message_count}+ to be trusted)"
                ),
            )
            from src.utils.branding import get_footer_kwargs
            embed.set_footer(**get_footer_kwargs())
            embed.timestamp = discord.utils.utcnow()
            
            await channel.send(embed=embed)
            
            logger.info(
                f"⚠️ Impersonation: @{member.name} changed '{impersonation_data['old_name']}' → '{impersonation_data['new_name']}' ({score*100:.0f}% match to '{impersonation_data['closest_match']}')"
            )
            
        except Exception as e:
            logger.error(
                "impersonation_alert_failed",
                error=str(e),
                exc_info=True,
            )
