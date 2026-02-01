"""
Moderation command handler.

Handles natural language moderation commands from admins/mods:
- ban, kick, mute/timeout, unmute, unban, warn

Extracted from client.py for better maintainability.
"""

import re
import random
from datetime import timedelta
from typing import Optional, Set, TYPE_CHECKING

import discord

from src.utils import get_logger, console_print

if TYPE_CHECKING:
    from src.llm import OpenRouterClient

logger = get_logger(__name__)


class ModHandler:
    """
    Handler for moderation commands via natural language.
    
    Supports:
    - ban @user [reason]
    - kick @user [reason]
    - mute/timeout @user [duration] [reason]
    - unmute @user
    - unban @user
    - warn @user [reason]
    """
    
    # Mod role IDs that can use moderation commands
    MOD_ROLE_IDS: Set[int] = {
        1436799852171235472,  # Staff
        1436767320239243519,  # Mish
        1436233268134678600,  # Automata
        1436217207825629277,  # Moderator
    }
    
    def __init__(self, bot: discord.Client, llm_client: "OpenRouterClient"):
        """
        Initialize mod handler.
        
        Args:
            bot: Discord bot instance
            llm_client: LLM client for AI responses
        """
        self.bot = bot
        self.llm_client = llm_client
    
    def is_mod(self, member: discord.Member) -> bool:
        """Check if member has mod role."""
        if not member.guild:
            return False
        author_role_ids = {role.id for role in member.roles}
        return bool(author_role_ids & self.MOD_ROLE_IDS)
    
    def parse_duration(self, text: str) -> Optional[timedelta]:
        """
        Parse duration from text (e.g., "5 min", "1 hour", "30s", "2h", "1d").
        
        Args:
            text: Text containing duration
            
        Returns:
            timedelta or None if no duration found
        """
        # First check for "a/an hour", "a minute", etc.
        if re.search(r'\b(a|an|one)\s*(?:hour|hr)\b', text, re.IGNORECASE):
            return timedelta(hours=1)
        if re.search(r'\b(a|an|one)\s*(?:day)\b', text, re.IGNORECASE):
            return timedelta(days=1)
        if re.search(r'\b(a|an|one)\s*(?:min|minute)\b', text, re.IGNORECASE):
            return timedelta(minutes=1)
        
        # Then check for numeric patterns
        patterns = [
            (r'(\d+)\s*(?:sec|seconds?|s)\b', lambda m: timedelta(seconds=int(m.group(1)))),
            (r'(\d+)\s*(?:min|minutes?|m)\b', lambda m: timedelta(minutes=int(m.group(1)))),
            (r'(\d+)\s*(?:hour|hours?|hr|h)\b', lambda m: timedelta(hours=int(m.group(1)))),
            (r'(\d+)\s*(?:day|days?|d)\b', lambda m: timedelta(days=int(m.group(1)))),
        ]
        for pattern, converter in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return converter(match)
        return None
    
    async def find_target(
        self, 
        message: discord.Message
    ) -> Optional[discord.Member]:
        """
        Find the target user for a mod command.
        
        Checks:
        1. Direct mentions in message
        2. User mentioned in replied message
        3. Author of replied message
        
        Args:
            message: The command message
            
        Returns:
            Target member or None
        """
        # First check for directly mentioned users
        targets = [m for m in message.mentions if m.id != self.bot.user.id]
        if targets:
            return targets[0]
        
        # If no direct mention, check reply context
        if message.reference and message.reference.message_id:
            try:
                referenced_msg = await message.channel.fetch_message(
                    message.reference.message_id
                )
                if referenced_msg:
                    # If replied message is FROM the bot, look for mentioned users
                    if referenced_msg.author.id == self.bot.user.id:
                        mentioned_in_bot_msg = [
                            m for m in referenced_msg.mentions 
                            if m.id != self.bot.user.id
                        ]
                        if mentioned_in_bot_msg:
                            target = message.guild.get_member(mentioned_in_bot_msg[0].id)
                            if target:
                                console_print(
                                    f"  📎 Reply to bot msg: targeting @{target.name}"
                                )
                                return target
                        
                        # Try to extract user ID from content
                        user_mention_match = re.search(
                            r'<@!?(\d+)>', 
                            referenced_msg.content
                        )
                        if user_mention_match:
                            user_id = int(user_mention_match.group(1))
                            if user_id != self.bot.user.id:
                                target = message.guild.get_member(user_id)
                                if target:
                                    console_print(
                                        f"  📎 Reply to bot msg: targeting @{target.name}"
                                    )
                                    return target
                    else:
                        # Normal message - use its author
                        target = message.guild.get_member(referenced_msg.author.id)
                        if target:
                            console_print(
                                f"  📎 Reply-based mod: targeting @{target.name}"
                            )
                            return target
            except Exception as e:
                logger.debug(f"could not fetch replied message for mod: {e}")
        
        return None
    
    def detect_action(self, text: str) -> Optional[str]:
        """
        Detect moderation action from text.
        
        Args:
            text: Command text
            
        Returns:
            Action type or None
        """
        text = text.lower()
        
        # UNMUTE (check before mute!)
        if re.search(r'\b(unmute|untimeout|размуть|анмут)\b', text):
            return "unmute"
        
        # UNBAN (check before ban!)
        if re.search(r'\b(unban|разбань|анбан)\b', text):
            return "unban"
        
        # BAN
        if re.search(r'\b(ban|забань|бан)\b', text):
            return "ban"
        
        # KICK
        if re.search(r'\b(kick|кик|кикни)\b', text):
            return "kick"
        
        # MUTE/TIMEOUT
        if re.search(r'\b(mute|timeout|мут|замуть|тайм.?аут)\b', text):
            return "mute"
        
        # WARN
        if re.search(r'\b(warn|предупреди)\b', text):
            return "warn"
        
        return None
    
    async def generate_response(
        self,
        action: str,
        target_name: str,
        target_mention: str,
        duration_str: Optional[str] = None
    ) -> str:
        """
        Generate AI response for mod action.
        
        Args:
            action: Action type (ban, kick, mute, etc.)
            target_name: Target username
            target_mention: Target mention string
            duration_str: Duration string for mute
            
        Returns:
            AI-generated response
        """
        duration_info = f" for {duration_str}" if duration_str else ""
        
        action_contexts = {
            "ban": "permanent ban from server",
            "kick": "kicked from server",
            "mute": f"timeout/mute{duration_info}",
            "unmute": "unmuted, can speak again",
            "unban": "unbanned, allowed back",
            "warn": "received a warning",
        }
        
        prompt = f"""you're a chill discord mod bot. write a SHORT funny response (max 10 words) for this mod action:

action: {action} ({action_contexts.get(action, action)})
user: {target_mention}
{f'duration: {duration_str}' if duration_str else ''}

rules:
- MUST include {target_mention} in response
- be playful but not mean or offensive
- use crypto/liquid themed phrases ("liquidated", "sent to the vault", "got rugged", "wen unmute", "ngmi behavior", "touch grass first")
- avoid harsh phrases like "rip bozo", "skill issue", "L + ratio"
- keep it light and fun, like teasing a friend
- lowercase only
- no quotes or extra formatting
- vary your responses, never repeat the same phrase

response:"""

        try:
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=40,
                temperature=0.85,
            )
            result = response.content.strip().lower()
            
            # Ensure target mention is in response
            if target_mention.lower() not in result.lower():
                result = f"{target_mention} {result}"
            
            console_print(f"  🤖 AI mod response: {result}")
            return result
            
        except Exception as e:
            logger.error(f"ai_mod_response_failed: {e}", exc_info=True)
            return self._get_fallback_response(action, target_mention, duration_info)
    
    def _get_fallback_response(
        self, 
        action: str, 
        target_mention: str, 
        duration_info: str = ""
    ) -> str:
        """Get fallback response if AI fails."""
        fallbacks = {
            "ban": [
                f"{target_mention} has been liquidated 💀",
                f"{target_mention} sent to the vault, permanently 🔒",
                f"aaaaand {target_mention} is gone 👋",
            ],
            "kick": [
                f"{target_mention} got yeeted out 👢",
                f"bye {target_mention}, door's that way 🚪",
            ],
            "mute": [
                f"{target_mention} needs a moment to chill{duration_info} 🤫",
                f"shhhh {target_mention}{duration_info} 🔇",
                f"{target_mention} sent to timeout corner{duration_info} 🪑",
            ],
            "unmute": [
                f"{target_mention} is back in the game 🔊",
                f"welcome back {target_mention} 🎤",
                f"{target_mention} freed, behave now 😌",
            ],
            "unban": [
                f"{target_mention} got a second chance ✅",
                f"redemption arc for {target_mention} 🔄",
                f"welcome back {target_mention}, don't make us regret it 😏",
            ],
            "warn": [
                f"heads up {target_mention}, easy there ⚠️",
                f"{target_mention} got a gentle reminder to chill 👀",
            ],
        }
        options = fallbacks.get(action, [f"{action} {target_mention}"])
        return random.choice(options)
    
    async def handle_command(self, message: discord.Message) -> bool:
        """
        Handle moderation command from message.
        
        Args:
            message: Discord message
            
        Returns:
            True if command was handled, False otherwise
        """
        # Check if user has mod role
        if not message.guild:
            return False
        
        if not self.is_mod(message.author):
            return False
        
        # Get command text (without bot mention)
        text = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
        
        # Find target user
        target = await self.find_target(message)
        if not target:
            return False
        
        # Detect action
        action = self.detect_action(text)
        if not action:
            return False
        
        # Parse duration for mute
        duration = None
        if action == "mute":
            duration = self.parse_duration(text)
            if not duration:
                duration = timedelta(minutes=5)  # Default 5 min
        
        console_print(
            f"  🛡️ MOD COMMAND: {action} @{target.name} by @{message.author.name}"
        )
        
        try:
            await self._execute_action(message, target, action, duration)
            return True
        except discord.Forbidden:
            await message.reply(f"❌ no permission to {action} {target.mention}")
            logger.error(f"mod_action_forbidden | action={action} | target={target.name}")
            return True
        except Exception as e:
            await message.reply(f"❌ failed to {action}: {str(e)[:100]}")
            logger.error(f"mod_action_failed | action={action} | error={e}")
            return True
    
    async def _execute_action(
        self,
        message: discord.Message,
        target: discord.Member,
        action: str,
        duration: Optional[timedelta] = None
    ):
        """Execute the moderation action."""
        duration_str = str(duration).split('.')[0] if duration else None
        
        if action == "ban":
            await target.ban(reason=f"By {message.author.name}")
            reply = await self.generate_response("ban", target.name, target.mention)
            await message.reply(reply)
            logger.info(f"🔨 BAN | @{target.name} by @{message.author.name}")
            
        elif action == "kick":
            await target.kick(reason=f"By {message.author.name}")
            reply = await self.generate_response("kick", target.name, target.mention)
            await message.reply(reply)
            logger.info(f"👢 KICK | @{target.name} by @{message.author.name}")
            
        elif action == "mute":
            await target.timeout(duration, reason=f"By {message.author.name}")
            reply = await self.generate_response(
                "mute", target.name, target.mention, duration_str
            )
            await message.reply(reply)
            logger.info(f"🔇 MUTE | @{target.name} for {duration} by @{message.author.name}")
            
        elif action == "unmute":
            await target.edit(timed_out_until=None)
            reply = await self.generate_response("unmute", target.name, target.mention)
            await message.reply(reply)
            logger.info(f"🔊 UNMUTE | @{target.name} by @{message.author.name}")
            
        elif action == "unban":
            try:
                await message.guild.unban(target, reason=f"By {message.author.name}")
                reply = await self.generate_response("unban", target.name, target.mention)
                await message.reply(reply)
                logger.info(f"✅ UNBAN | @{target.name} by @{message.author.name}")
            except discord.NotFound:
                await message.reply(f"yo {target.mention} isn't even banned lol")
                
        elif action == "warn":
            try:
                await target.send(
                    f"⚠️ **Warning from {message.guild.name}**\n\n"
                    f"You have received a warning from the moderation team.\n"
                    f"Please review the server rules and behave accordingly."
                )
                reply = await self.generate_response("warn", target.name, target.mention)
                await message.reply(reply)
            except discord.Forbidden:
                await message.reply(
                    f"tried to warn {target.mention} but their dms are closed 🤷"
                )
            logger.info(f"⚠️ WARN | @{target.name} by @{message.author.name}")
