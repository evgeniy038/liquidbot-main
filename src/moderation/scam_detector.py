"""
Main scam detection system with multi-layer analysis.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import timedelta

import discord

from src.llm import OpenRouterClient
from src.moderation.pattern_matcher import PatternMatcher
from src.moderation.ai_analyzer import AIAnalyzer, AIAnalysisResult
from src.moderation.alert_sender import AlertSender
from src.rag import get_message_storage
from src.utils import get_logger

logger = get_logger(__name__)


@dataclass
class DetectionResult:
    """Result of scam detection."""
    is_scam: bool
    confidence: float
    risk_level: str
    action: str
    reasons: List[str]
    pattern_score: int
    ai_result: Optional[AIAnalysisResult]


class ScamDetector:
    """
    Multi-layer scam detection system.
    
    Detection flow:
    1. Pattern matching (fast, rule-based)
    2. AI analysis (LLM-based, for suspicious messages)
    3. Alert sending (to moderation channel)
    """
    
    def __init__(
        self,
        llm_client: OpenRouterClient,
        bot: discord.Client,
        config: dict,
    ):
        """
        Initialize scam detector.
        
        Args:
            llm_client: LLM client for AI analysis
            bot: Discord bot client
            config: Moderation configuration
        """
        self.config = config
        self.enabled = config.get("enabled", False)
        
        if not self.enabled:
            logger.info("scam_detector_disabled")
            return
        
        # Initialize pattern matcher
        patterns_config = config.get("patterns", {})
        self.pattern_matcher = PatternMatcher(
            keywords=patterns_config.get("keywords", []),
            regex_patterns=patterns_config.get("regex_patterns", []),
            url_whitelist=config.get("url_whitelist", []),
        )
        
        # Initialize AI analyzer
        ai_config = config.get("ai_analysis", {})
        self.ai_enabled = ai_config.get("enabled", True)
        self.ai_trigger_threshold = ai_config.get("trigger_threshold", 30)
        self.ai_analyzer = AIAnalyzer(
            llm_client=llm_client,
            confidence_threshold=ai_config.get("confidence_threshold", 0.7),
        ) if self.ai_enabled else None
        
        # Initialize alert sender
        self.alert_sender = AlertSender(bot=bot)
        self.alert_channel_id = config.get("alert_channel_id")
        
        # Initialize message analytics for user history check
        user_history_config = config.get("user_history", {})
        self.user_history_enabled = user_history_config.get("enabled", True)
        self.min_message_threshold = user_history_config.get("min_message_threshold", 20)
        self.new_user_score_boost = user_history_config.get("new_user_score_boost", 20)
        self.trusted_message_threshold = user_history_config.get("trusted_message_threshold", 100)  # Skip AI for trusted users
        self.trusted_score_limit = user_history_config.get("trusted_score_limit", 70)  # Only skip if score is below this
        
        if self.user_history_enabled:
            try:
                self.storage = get_message_storage()
                logger.info("user_history_check_enabled")
            except Exception as e:
                logger.error("failed_to_init_storage", error=str(e))
                self.user_history_enabled = False
                self.storage = None
        else:
            self.storage = None
        
        # Role-based filtering (ONLY check specified roles)
        self.check_roles = set(config.get("check_roles", []))
        
        # Strict link filter (delete ALL non-whitelisted links)
        strict_filter_config = config.get("strict_link_filter", {})
        self.strict_link_filter_enabled = strict_filter_config.get("enabled", False)
        self.strict_link_delete = strict_filter_config.get("delete_message", True)
        self.strict_link_warn = strict_filter_config.get("warn_user", False)
        self.strict_link_warning = strict_filter_config.get("warning_message", "")
        self.strict_link_min_messages = strict_filter_config.get("min_messages_exempt", 50)
        
        if self.strict_link_filter_enabled:
            logger.info("strict_link_filter_enabled")
        
        logger.info("scam_detector_initialized")
    
    async def check_strict_link_filter(
        self,
        message: discord.Message,
    ) -> bool:
        """
        Check if message contains non-whitelisted links and handle deletion.
        
        Args:
            message: Discord message to check
            
        Returns:
            True if message was deleted (had non-whitelisted links), False otherwise
        """
        if not self.strict_link_filter_enabled:
            return False
        
        # Skip bots
        if message.author.bot:
            return False
        
        # Skip users with trusted roles (Staff, Mish, admins)
        if isinstance(message.author, discord.Member):
            # Trusted role IDs that bypass link filter
            trusted_role_ids = {1436799852171235472, 1436767320239243519, 1436233268134678600, 1436217207825629277}
            user_role_ids = {role.id for role in message.author.roles}
            
            if user_role_ids & trusted_role_ids:
                return False  # Trusted user, skip filter
            
            # Also skip if user has administrator permission
            if message.author.guild_permissions.administrator:
                return False
        
        # Skip users with enough messages (trusted by activity)
        if self.user_history_enabled and self.storage:
            try:
                user_message_count = self.storage.get_user_message_count(
                    user_id=str(message.author.id)
                )
                if user_message_count >= self.strict_link_min_messages:
                    return False  # User has enough messages, skip filter
            except Exception:
                pass  # If check fails, continue with filter
        
        # Extract URLs from message
        urls = self.pattern_matcher.extract_urls(message.content)
        
        if not urls:
            return False  # No links = OK
        
        # Check if ALL URLs are whitelisted
        if self.pattern_matcher._all_urls_whitelisted(urls):
            return False  # All links are from whitelist = OK
        
        # Found non-whitelisted links - take action
        domains = self.pattern_matcher.extract_domains(message.content)
        non_whitelisted = []
        
        for domain in domains:
            domain_lower = domain.lower()
            is_whitelisted = False
            for whitelisted in self.pattern_matcher.url_whitelist:
                if whitelisted in domain_lower or domain_lower.endswith(whitelisted):
                    is_whitelisted = True
                    break
            if not is_whitelisted:
                non_whitelisted.append(domain)
        
        logger.warning(
            f"🔗 Non-whitelisted link: @{message.author.name} | domains: {non_whitelisted}"
        )
        
        # Delete message
        if self.strict_link_delete:
            try:
                await message.delete()
                logger.info(
                    f"🗑️ Deleted message with non-whitelisted link from @{message.author.name}"
                )
                
                # Apply 24-hour timeout while alert is being reviewed
                if isinstance(message.author, discord.Member):
                    try:
                        await message.author.timeout(
                            timedelta(hours=24),
                            reason="Non-whitelisted link detected (pending review)"
                        )
                        logger.info(
                            f"🔇 TIMEOUT: @{message.author.name} for 24h (link filter)"
                        )
                    except discord.Forbidden:
                        logger.warning("no_permission_to_timeout_user")
                    except Exception as e:
                        logger.error(f"timeout_error: {e}")
            except discord.Forbidden:
                logger.error("cannot_delete_message_no_permission")
            except discord.NotFound:
                pass  # Already deleted
            except Exception as e:
                logger.error(f"delete_message_error: {e}")
        
        # Send alert to security channel
        if self.alert_channel_id:
            try:
                alert_sent = await self.alert_sender.send_scam_alert(
                    alert_channel_id=self.alert_channel_id,
                    message=message,
                    risk_score=1.0,
                    risk_level="high",
                    reasons=["Non-whitelisted link detected", f"Domains: {', '.join(non_whitelisted)}"],
                    matched_keywords=[],
                    matched_patterns=[],
                    domains=non_whitelisted,
                )
                if alert_sent:
                    logger.info(f"📢 Alert sent to security channel for @{message.author.name}")
                else:
                    logger.error(f"❌ Failed to send alert for @{message.author.name}")
            except Exception as e:
                logger.error(f"alert_send_error: {e}")
        
        # Warn user
        if self.strict_link_warn:
            try:
                # Try to send warning in channel (auto-delete after 10 sec)
                warning = await message.channel.send(
                    f"{message.author.mention} {self.strict_link_warning}",
                    delete_after=10.0,
                )
            except Exception as e:
                logger.error(f"send_warning_error: {e}")
        
        return True
    
    async def analyze_message(
        self,
        message: discord.Message,
    ) -> Optional[DetectionResult]:
        """
        Analyze message for scam indicators.
        
        Args:
            message: Discord message to analyze
        
        Returns:
            DetectionResult if scam detected, None otherwise
        """
        if not self.enabled:
            return None
        
        # Step 0: Strict link filter (delete ALL non-whitelisted links)
        if await self.check_strict_link_filter(message):
            # Message was already deleted by strict filter, no further processing needed
            return DetectionResult(
                is_scam=True,
                confidence=1.0,
                risk_level="high",
                action="already_deleted",  # Don't try to delete again
                reasons=["Non-whitelisted link detected"],
                pattern_score=100,
                ai_result=None,
            )
        
        # Check if user should be checked (for pattern-based scam detection)
        if not self._should_check_user(message.author):
            logger.debug(
                "user_whitelisted",
                user_id=message.author.id,
            )
            return None
        
        # Step 1: Pattern matching (fast)
        pattern_result = self.pattern_matcher.check_message(message.content)
        
        if not pattern_result.matched:
            # No patterns matched, message is clean
            return None
        
        # Check user message history
        user_message_count = 0
        is_new_user = False
        
        if self.user_history_enabled and self.storage:
            try:
                user_message_count = self.storage.get_user_message_count(
                    user_id=str(message.author.id)
                )
                
                if user_message_count < self.min_message_threshold:
                    is_new_user = True
                    # Boost pattern score for new users
                    pattern_result.score += self.new_user_score_boost
                    
                    logger.info(f"👤 New user: @{message.author.name} ({user_message_count} msgs, +{self.new_user_score_boost} score)")
            except Exception as e:
                logger.error(
                    "failed_to_check_user_history",
                    user_id=message.author.id,
                    error=str(e),
                )
        
        keywords_str = ", ".join(pattern_result.matched_keywords[:3]) if pattern_result.matched_keywords else "patterns"
        logger.info(f"🔍 Suspicious: @{message.author.name} | {user_message_count} msgs | score={pattern_result.score} | {keywords_str}")
        
        # Skip AI analysis for trusted users with lower scores
        if user_message_count >= self.trusted_message_threshold and pattern_result.score < self.trusted_score_limit:
            logger.info(f"✅ Trusted user skipped: @{message.author.name} ({user_message_count} msgs, score={pattern_result.score})")
            return None
        
        # Extract URLs and domains
        domains = self.pattern_matcher.extract_domains(message.content)
        
        # Check if AI analysis is needed
        if self.ai_enabled and pattern_result.score >= self.ai_trigger_threshold:
            # Step 2: AI analysis (accurate but slower)
            ai_result = await self.ai_analyzer.analyze_message(
                content=message.content,
                author_name=message.author.name,
                channel_name=message.channel.name if hasattr(message.channel, 'name') else 'dm',
                has_links=len(domains) > 0,
                has_mentions="@everyone" in message.content or "@here" in message.content,
                matched_patterns=pattern_result.matched_patterns,
                matched_keywords=pattern_result.matched_keywords,
            )
            
            # Determine action based on AI result
            if ai_result.is_scam and ai_result.confidence >= self.ai_analyzer.confidence_threshold:
                detection_result = DetectionResult(
                    is_scam=True,
                    confidence=ai_result.confidence,
                    risk_level=ai_result.risk_level,
                    action=ai_result.recommended_action,
                    reasons=ai_result.all_reasons,
                    pattern_score=pattern_result.score,
                    ai_result=ai_result,
                )
                
                # Truncate message for logging
                msg_preview = message.content[:100] + "..." if len(message.content) > 100 else message.content
                msg_preview = msg_preview.replace("\n", " ")
                
                logger.warning(
                    f"🚨 SCAM: @{message.author.name} ({ai_result.risk_level}, {ai_result.confidence*100:.0f}%): {msg_preview}"
                )
                
                # Step 3: Send alert
                if self.alert_channel_id:
                    await self.alert_sender.send_scam_alert(
                        alert_channel_id=self.alert_channel_id,
                        message=message,
                        risk_score=ai_result.confidence,
                        risk_level=ai_result.risk_level,
                        reasons=ai_result.all_reasons,
                        matched_keywords=pattern_result.matched_keywords,
                        matched_patterns=pattern_result.matched_patterns,
                        domains=domains,
                    )
                
                return detection_result
            
            else:
                # AI says not a scam
                logger.info(
                    "ai_cleared_message",
                    message_id=message.id,
                    confidence=ai_result.confidence,
                )
                return None
        
        else:
            # Pattern score not high enough for AI, but still suspicious
            # Log for monitoring
            logger.info(
                "low_risk_patterns_detected",
                message_id=message.id,
                pattern_score=pattern_result.score,
            )
            return None
    
    def _should_check_user(self, user: discord.User | discord.Member) -> bool:
        """
        Check if user should be analyzed.
        
        NEW LOGIC: Only check users whose HIGHEST role (by position) is in check_roles.
        This means users with multiple roles are checked only if their top role is in check_roles.
        If check_roles is empty, don't check anyone.
        
        Args:
            user: Discord user/member
            
        Returns:
            True if user should be checked, False otherwise
        """
        # Always skip bots
        if user.bot:
            return False
        
        # If no roles specified, don't check anyone
        if not self.check_roles:
            logger.debug(
                "no_check_roles_specified",
                user_id=user.id,
            )
            return False
        
        # Get user roles (only works if user is Member)
        if not isinstance(user, discord.Member):
            return False
        
        # Get all roles excluding @everyone, sorted by position (highest first)
        user_roles = [role for role in user.roles if role.name != "@everyone"]
        
        # No roles = don't check
        if not user_roles:
            return False
        
        # Sort by position (higher position = higher in hierarchy)
        user_roles.sort(key=lambda r: r.position, reverse=True)
        
        # Get highest role
        highest_role = user_roles[0]
        
        # Check if highest role ID is in check_roles (by ID, not name)
        if str(highest_role.id) in self.check_roles:
            logger.debug(
                "user_highest_role_matches",
                user_id=user.id,
                highest_role=highest_role.name,
                highest_role_id=highest_role.id,
                role_position=highest_role.position,
                total_roles=len(user_roles),
            )
            return True
        
        # Highest role not in check_roles
        logger.debug(
            "user_highest_role_not_matched",
            user_id=user.id,
            highest_role=highest_role.name,
            highest_role_id=highest_role.id,
            check_roles=list(self.check_roles),
        )
        
        return False
