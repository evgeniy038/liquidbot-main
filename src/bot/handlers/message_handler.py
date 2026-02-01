"""
Message handler for processing Discord messages.

Handles the main message flow:
- Command processing
- Scam detection
- Content filtering
- Agent routing
- Response generation

Extracted from client.py for better maintainability.
"""

import re
import asyncio
from datetime import timedelta
from typing import Optional, Dict, List, TYPE_CHECKING

import discord

from src.bot.filters.gliquid_filter import get_gliquid_filter
from src.utils import get_logger, console_print, get_channel_purposes

if TYPE_CHECKING:
    from src.agents import AgentFactory
    from src.bot.ai_router import AIRouter
    from src.moderation import ScamDetector, SubmissionHandler
    from src.moderation.content_filter import ContentFilter
    from src.bot.handlers.mod_handler import ModHandler
    from src.rag.announcement_indexer import AnnouncementIndexer

logger = get_logger(__name__)


class MessageHandler:
    """
    Handler for processing Discord messages.
    
    Features:
    - Multi-agent routing
    - Scam detection
    - Content filtering (gliquid, etc.)
    - Conversation history management
    - Smart response splitting
    """
    
    def __init__(
        self,
        bot: discord.Client,
        config,
        agent_factory: "AgentFactory",
        ai_router: Optional["AIRouter"] = None,
        scam_detector: Optional["ScamDetector"] = None,
        content_filter: Optional["ContentFilter"] = None,
        mod_handler: Optional["ModHandler"] = None,
        submission_handler: Optional["SubmissionHandler"] = None,
        announcement_indexer: Optional["AnnouncementIndexer"] = None,
    ):
        """
        Initialize message handler.
        
        Args:
            bot: Discord bot instance
            config: Bot configuration
            agent_factory: Agent factory for routing
            ai_router: AI router for intelligent routing
            scam_detector: Scam detection system
            content_filter: Content filter
            mod_handler: Moderation command handler
            submission_handler: Content submission handler
            announcement_indexer: Announcement indexer
        """
        self.bot = bot
        self.config = config
        self.agent_factory = agent_factory
        self.ai_router = ai_router
        self.scam_detector = scam_detector
        self.content_filter = content_filter
        self.mod_handler = mod_handler
        self.submission_handler = submission_handler
        self.announcement_indexer = announcement_indexer
        
        # Gliquid filter (singleton)
        self.gliquid_filter = get_gliquid_filter()
        
        # Conversation history per user
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    async def handle_message(self, message: discord.Message) -> bool:
        """
        Handle incoming Discord message.
        
        Args:
            message: Discord message
            
        Returns:
            True if message was fully handled, False otherwise
        """
        # Ignore bot messages
        if message.author.bot:
            return True
        
        # Guild whitelist check
        if message.guild:
            allowed_guilds = self.config.discord.allowed_guilds
            if allowed_guilds and message.guild.id not in allowed_guilds:
                logger.info(
                    "guild_not_whitelisted",
                    guild_id=message.guild.id,
                    guild_name=message.guild.name,
                )
                return True
        
        # Handle submission system
        if self.submission_handler:
            is_submission = await self.submission_handler.handle_new_submission(message)
            if is_submission:
                return True
        
        # Scam detection
        if await self._handle_scam_detection(message):
            return True
        
        # Gliquid channel filter
        if await self.gliquid_filter.filter_message(message):
            return True
        
        # Content filter
        if self.content_filter:
            await self.content_filter.filter_message(message)
            try:
                await message.channel.fetch_message(message.id)
            except discord.NotFound:
                return True
            except:
                pass
        
        # Valid gliquid message - add reaction
        if self.gliquid_filter.is_gliquid_channel(message.channel.id):
            if self.gliquid_filter.is_valid_message(message.content):
                try:
                    await message.add_reaction(self.gliquid_filter.GLIQUID_EMOJI)
                except:
                    pass
        
        # Ignore messages without direct bot mention
        if self.bot.user not in message.mentions:
            return False  # Not handled - allow other processing
        
        # Skip indexed channels
        if self.announcement_indexer:
            if str(message.channel.id) in self.announcement_indexer.channel_ids:
                logger.debug(f"Skipping response in indexed channel #{message.channel.name}")
                return True
        
        # Handle moderation commands
        if self.mod_handler:
            if await self.mod_handler.handle_command(message):
                return True
        
        # Process with agent
        await self._process_with_agent(message)
        return True
    
    async def _handle_scam_detection(self, message: discord.Message) -> bool:
        """
        Handle scam detection for message.
        
        Returns:
            True if message was deleted (scam), False otherwise
        """
        if not self.scam_detector or not self.config.moderation.enabled:
            return False
        
        # Pre-filter gliquid channel (faster than AI)
        pre_deleted = False
        if self.gliquid_filter.is_gliquid_channel(message.channel.id):
            if not self.gliquid_filter.is_trusted_user(message.author):
                if not self.gliquid_filter.is_valid_message(message.content):
                    try:
                        await message.delete()
                        pre_deleted = True
                        logger.info(
                            f"🗑️ PRE_DELETE gliquid channel | "
                            f"@{message.author.name} | {message.content[:50]}..."
                        )
                    except discord.NotFound:
                        pre_deleted = True
                    except Exception as e:
                        logger.error(f"pre_delete_error: {e}")
        
        # Run scam detector
        detection_result = await self.scam_detector.analyze_message(message)
        
        if detection_result and detection_result.is_scam:
            logger.warning(
                "🚫 SCAM_MESSAGE_BLOCKED",
                message_id=message.id,
                author_id=message.author.id,
                channel=message.channel.name if hasattr(message.channel, 'name') else 'dm',
                confidence=detection_result.confidence,
                risk_level=detection_result.risk_level,
            )
            
            # Delete if not already pre-deleted
            if detection_result.action in ["delete", "ban"] and not pre_deleted:
                try:
                    await message.delete()
                    logger.info("scam_message_deleted", message_id=message.id)
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    logger.warning("no_permission_to_delete_scam")
                except Exception as e:
                    logger.error(f"delete_error: {e}")
            
            # Apply 24-hour timeout while alert is being reviewed
            if isinstance(message.author, discord.Member):
                try:
                    await message.author.timeout(
                        timedelta(hours=24),
                        reason=f"Scam detected (pending review) - Risk: {detection_result.risk_level}, Confidence: {detection_result.confidence:.0%}"
                    )
                    logger.info(
                        f"🔇 TIMEOUT: @{message.author.name} for 24h (scam pending review)"
                    )
                except discord.Forbidden:
                    logger.warning("no_permission_to_timeout_scammer")
                except Exception as e:
                    logger.error(f"timeout_error: {e}")
            
            return True
        
        # Pre-deleted but not scam - still blocked
        if pre_deleted:
            return True
        
        return False
    
    async def _process_with_agent(self, message: discord.Message):
        """Process message with appropriate agent."""
        channel_name = message.channel.name if hasattr(message.channel, 'name') else 'dm'
        channel_id = message.channel.id
        
        console_print(f"\n{'─'*80}")
        console_print(f"📨 NEW MESSAGE")
        console_print(f"  From: {message.author.name} ({message.author.id})")
        console_print(f"  Channel: #{channel_name} ({channel_id})")
        console_print(f"  Length: {len(message.content)} chars")
        
        try:
            # Extract query
            query = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            
            # Add reply context
            query = await self._add_reply_context(message, query)
            
            # Add channel content if mentioned
            channel_context = await self._fetch_mentioned_channel_content(message, query)
            if channel_context:
                query = f"{query}\n\n[CHANNEL CONTENT]\n{channel_context}"
                console_print(f"  📺 Added channel context: {len(channel_context)} chars")
            
            # Handle empty query with attachments
            if not query and (message.attachments or message.stickers):
                query = "what's this showing?" if message.attachments else "what's this sticker about?"
            
            if not query:
                await message.reply("yo what's good? drop your question 👀")
                return
            
            # Get agent
            agent = await self._get_agent(query, channel_name, channel_id)
            
            logger.info(f"💬 @{message.author.name}: {query[:60]}{'...' if len(query) > 60 else ''}")
            
            # Update agent with guild context
            if message.guild:
                channel_list = ", ".join([
                    f"<#{ch.id}>" for ch in message.guild.text_channels
                    if ch.permissions_for(message.guild.me).view_channel
                ][:30])
                agent.set_guild_channels(channel_list)
                
                channel_purposes = get_channel_purposes()
                if channel_purposes:
                    agent.set_channel_purposes(channel_purposes)
            
            # Process with typing indicator
            async with message.channel.typing():
                console_print(f"\n⚙️  PROCESSING")
                console_print(f"  Agent: {agent.get_name()}")
                console_print(f"  RAG: {'✅ Enabled' if agent.config.rag_enabled else '❌ Disabled'}")
                
                # Get conversation history
                user_id = str(message.author.id)
                conversation_history = self.conversation_history.get(user_id, [])
                
                if conversation_history:
                    console_print(f"  Memory: {len(conversation_history) // 2} previous messages")
                
                # Generate response
                full_response = await agent.process_message(message, query, conversation_history)
                
                # Post-process response
                full_response = self._post_process_response(full_response)
                
                # Send response
                await self._send_response(message, full_response)
                
                # Update conversation history
                self._update_history(user_id, query, full_response, agent.config.max_history)
                
                console_print(f"\n✅ RESPONSE SENT")
                console_print(f"  Response Length: {len(full_response)} chars")
                console_print(f"  Agent: {agent.get_name()}")
                console_print(f"{'─'*80}\n")
                
                logger.info(f"🤖 Luma: {full_response[:60]}{'...' if len(full_response) > 60 else ''}")
        
        except Exception as e:
            logger.error("message_handling_error", error=str(e), exc_info=True)
            await message.reply("bruh something broke on my end 💀 try again in a sec")
    
    async def _add_reply_context(self, message: discord.Message, query: str) -> str:
        """Add context from replied message."""
        if message.reference and message.reference.message_id:
            try:
                referenced_msg = await message.channel.fetch_message(
                    message.reference.message_id
                )
                if referenced_msg and referenced_msg.content:
                    reply_context = (
                        f"[replying to @{referenced_msg.author.name}: "
                        f"\"{referenced_msg.content[:500]}\"]\n\n"
                    )
                    console_print(
                        f"  📎 Reply context: @{referenced_msg.author.name}: "
                        f"{referenced_msg.content[:60]}..."
                    )
                    return reply_context + query
            except Exception as e:
                logger.debug(f"could not fetch referenced message: {e}")
        return query
    
    async def _fetch_mentioned_channel_content(
        self,
        message: discord.Message,
        query: str,
        max_messages: int = 10,
    ) -> Optional[str]:
        """Fetch content from explicitly mentioned channel."""
        channel_match = re.search(r'<#(\d+)>', query)
        
        if not channel_match:
            return None
        
        channel_id = int(channel_match.group(1))
        target_channel = message.guild.get_channel(channel_id) if message.guild else None
        
        if not target_channel:
            return None
        
        if not target_channel.permissions_for(message.guild.me).read_messages:
            return None
        
        try:
            messages_content = []
            async for msg in target_channel.history(limit=max_messages):
                if msg.content:
                    timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
                    messages_content.append(
                        f"[{timestamp}] @{msg.author.name}: {msg.content[:500]}"
                    )
            
            if not messages_content:
                return None
            
            messages_content.reverse()
            logger.info(f"📺 Fetched {len(messages_content)} messages from #{target_channel.name}")
            
            return f"Recent messages from #{target_channel.name}:\n\n" + "\n\n".join(messages_content)
            
        except Exception as e:
            logger.error(f"failed to fetch channel content: {e}")
            return None
    
    async def _get_agent(self, query: str, channel_name: str, channel_id: int):
        """Get appropriate agent for the query."""
        use_ai_routing = self.agent_factory.config.get('routing', {}).get('use_ai_routing', False)
        
        if use_ai_routing and self.ai_router:
            routing_decision = await self.ai_router.route(
                query=query,
                channel_name=channel_name
            )
            
            agent = self.agent_factory.get_agent(routing_decision.agent)
            
            if not agent:
                logger.warning("agent_not_found", requested_agent=routing_decision.agent)
                agent = self.agent_factory.get_agent('general_agent')
            
            console_print(f"\n🔀 AI ROUTING")
            console_print(f"  Agent: {agent.get_name()} ({routing_decision.agent})")
            console_print(f"  Confidence: {routing_decision.confidence:.2f}")
        else:
            default_agent_id = self.agent_factory.config.get('routing', {}).get(
                'default_agent', 'general_agent'
            )
            agent = self.agent_factory.get_agent(default_agent_id)
            
            console_print(f"\n⚡ DIRECT ROUTING")
            console_print(f"  Agent: {agent.get_name()} ({default_agent_id})")
        
        return agent
    
    def _post_process_response(self, response: str) -> str:
        """Post-process response (lowercase, dashes)."""
        response = response.lower()
        response = response.replace('—', '-').replace('–', '-')
        return response
    
    async def _send_response(self, message: discord.Message, response: str):
        """Send response, splitting if too long."""
        max_length = 1950
        
        if len(response) <= max_length:
            await message.reply(response)
            return
        
        parts = []
        remaining = response
        
        while remaining:
            if len(remaining) <= max_length:
                parts.append(remaining)
                break
            
            split_pos = max_length
            
            # Try paragraph split
            para_split = remaining.rfind("\n\n", 0, max_length)
            if para_split > max_length * 0.5:
                split_pos = para_split + 2
            else:
                # Try sentence split
                sent_split = max(
                    remaining.rfind(". ", 0, max_length),
                    remaining.rfind("! ", 0, max_length),
                    remaining.rfind("? ", 0, max_length),
                )
                if sent_split > max_length * 0.5:
                    split_pos = sent_split + 2
                else:
                    # Word boundary
                    space_split = remaining.rfind(" ", 0, max_length)
                    if space_split > 0:
                        split_pos = space_split + 1
            
            parts.append(remaining[:split_pos])
            remaining = remaining[split_pos:]
        
        for i, part in enumerate(parts):
            if i == 0:
                await message.reply(part)
            else:
                await message.channel.send(part)
    
    def _update_history(
        self, 
        user_id: str, 
        query: str, 
        response: str, 
        max_pairs: int
    ):
        """Update conversation history for user."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({"role": "user", "content": query})
        self.conversation_history[user_id].append({"role": "assistant", "content": response})
        
        # Trim to max pairs
        if len(self.conversation_history[user_id]) > max_pairs * 2:
            self.conversation_history[user_id] = self.conversation_history[user_id][-(max_pairs * 2):]
        
        logger.debug(
            "conversation_history_updated",
            user_id=user_id,
            history_length=len(self.conversation_history[user_id]) // 2,
        )
