"""
General agent for casual conversation.
"""

from typing import Optional

import discord

from src.agents.base_agent import AgentConfig, BaseAgent
from src.llm import OpenRouterClient
from src.rag import HybridRetriever
from src.utils import get_logger

logger = get_logger(__name__)


class GeneralAgent(BaseAgent):
    """
    Luma - community AI that vibes with the chat.
    
    Features:
    - Casual conversation with humor and sarcasm
    - Liquid platform help when needed
    - Context-aware tone switching
    - RAG-powered with chat history
    """
    
    # Channel routing map
    ROUTING_MAP = {
        "liquid": ["expert", "liquid-info"],
        "trading": ["expert", "liquid-info"],
        "vaults": ["expert", "liquid-info"],
        "news": ["expert", "liquid-info"],
        "referral": ["expert", "liquid-info"],
        "technical": ["expert", "liquid-info"],
        "documentation": ["expert", "liquid-info"],
    }
    
    def __init__(
        self,
        config: AgentConfig,
        llm_client: OpenRouterClient,
        retriever: Optional[HybridRetriever] = None,
        channel_reader = None,
    ):
        """Initialize general agent."""
        super().__init__(config, llm_client, retriever)
        self.channel_reader = channel_reader
        logger.info("general_agent_initialized")
    
    def _detect_specialized_topic(self, query: str) -> Optional[str]:
        """
        Detect if query is about a specialized topic.
        
        Args:
            query: User query
            
        Returns:
            Suggested channel or None
        """
        query_lower = query.lower()
        
        for topic, channels in self.ROUTING_MAP.items():
            if topic in query_lower:
                return channels[0]  # Return primary channel
        
        return None
    
    def _detect_channel_list_request(self, query: str) -> bool:
        """
        Detect if user is asking for list of all channels.
        
        Returns True if user wants channel list.
        """
        query_lower = query.lower()
        
        # Patterns for channel list requests
        list_patterns = [
            "list channels",
            "show channels",
            "all channels",
            "what channels",
            "available channels",
            "список каналов",
            "покажи каналы",
            "какие каналы",
            "все каналы",
        ]
        
        return any(pattern in query_lower for pattern in list_patterns)
    
    def _detect_channel_read_request(self, query: str, message: discord.Message) -> Optional[str]:
        """
        Detect if user is asking to read a channel.
        
        Returns channel name or None.
        """
        import re
        
        query_lower = query.lower()
        
        # Patterns for channel reading requests
        patterns = [
            r"what.*in\s+#?(\w+)",
            r"what.*happening.*#?(\w+)",
            r"read\s+#?(\w+)",
            r"check\s+#?(\w+)",
            r"что.*в\s+#?(\w+)",
            r"прочитай\s+#?(\w+)",
            r"покажи.*#?(\w+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                return match.group(1)
        
        # Check for direct channel mentions like <#123456> - always read if mentioned
        channel_mention = re.search(r'<#(\d+)>', query)
        if channel_mention:
            channel_id = int(channel_mention.group(1))
            if message.guild:
                channel = message.guild.get_channel(channel_id)
                if channel:
                    return channel.name
        
        return None
    
    def _detect_user_mention(self, query: str, message: discord.Message) -> Optional[discord.Member]:
        """
        Detect if a user is mentioned in the message.
        
        Returns Member object or None.
        """
        import re
        
        # Check for direct user mentions like <@123456> or <@!123456>
        user_mention = re.search(r'<@!?(\d+)>', query)
        if user_mention:
            user_id = int(user_mention.group(1))
            if message.guild:
                member = message.guild.get_member(user_id)
                if member and not member.bot:
                    return member
        
        return None
    
    def _format_user_info(self, member: discord.Member) -> str:
        """Format user info for response."""
        lines = [f"**User Info: {member.display_name}** (@{member.name})"]
        
        # Account age
        created = member.created_at.strftime("%Y-%m-%d")
        lines.append(f"📅 Account created: {created}")
        
        # Join date
        if member.joined_at:
            joined = member.joined_at.strftime("%Y-%m-%d")
            lines.append(f"📥 Joined server: {joined}")
        
        # Roles (excluding @everyone)
        roles = [r.name for r in member.roles if r.name != "@everyone"]
        if roles:
            lines.append(f"🎭 Roles: {', '.join(roles)}")
        else:
            lines.append("🎭 Roles: None")
        
        # Status
        status_emoji = {"online": "🟢", "idle": "🟡", "dnd": "🔴", "offline": "⚫"}
        lines.append(f"Status: {status_emoji.get(str(member.status), '⚫')} {member.status}")
        
        return "\n".join(lines)
    
    async def _execute_tools(
        self,
        query: str,
        message: discord.Message,
    ) -> Optional[str]:
        """Execute tools: check channel list, reading, or routing suggestions."""
        
        if self.channel_reader and message.guild:
            # Check if user wants list of all channels
            if self._detect_channel_list_request(query):
                logger.info(
                    "channel_list_request",
                    query=query[:50],
                    guild_id=message.guild.id,
                )
                
                channels = await self.channel_reader.get_all_channels(
                    guild_id=message.guild.id,
                    only_text=True,
                )
                
                if channels:
                    formatted = self.channel_reader.format_channels_list(channels)
                    return formatted
                else:
                    return "couldn't get channels list bro, something went wrong 🤷"
            
            # Check if user wants to read a specific channel
            channel_name = self._detect_channel_read_request(query, message)
            
            if channel_name:
                logger.info(
                    "channel_read_request",
                    query=query[:50],
                    channel_name=channel_name,
                )
                
                messages = await self.channel_reader.read_channel_by_name(
                    guild_id=message.guild.id,
                    channel_name=channel_name,
                    limit=10,
                )
                
                if messages:
                    formatted = self.channel_reader.format_messages_for_context(
                        messages=messages,
                        channel_name=channel_name,
                    )
                    return formatted
                else:
                    return f"couldn't find or read #{channel_name} bro, maybe it doesn't exist or I don't have access 🤷"
        
        # Check if a user is mentioned - return their info
        if message.guild:
            mentioned_user = self._detect_user_mention(query, message)
            if mentioned_user:
                logger.info(f"user_info_request | @{mentioned_user.name}")
                return self._format_user_info(mentioned_user)
        
        # Check if topic needs specialized channel
        suggested_channel = self._detect_specialized_topic(query)
        
        if suggested_channel:
            logger.info(
                "general_agent_routing_suggestion",
                query=query[:50],
                suggested_channel=suggested_channel,
            )
            
            channel_info = {
                "expert": "💡 For detailed Liquid platform questions, try the **#expert** or **#liquid-info** channel!",
                "liquid-info": "💡 For detailed Liquid platform questions, try the **#expert** or **#liquid-info** channel!",
            }
            
            routing_msg = channel_info.get(
                suggested_channel,
                f"💡 You might get better help in the **#{suggested_channel}** channel!",
            )
            
            return f"{routing_msg}\n\n_I can still answer your question, but the specialized agent there will provide more detailed help!_"
        
        return None
    
    async def _format_response(
        self,
        response: str,
        context: str,
    ) -> str:
        """Format response (no footer - stay casual)."""
        # Fix markdown
        formatted = response.replace("####", "###")
        
        # No footer - just send the response naturally
        return formatted
    
    def get_name(self) -> str:
        """Get agent name."""
        return "Luma"
    
    def get_description(self) -> str:
        """Get agent description."""
        return "Community AI with the vibes"
