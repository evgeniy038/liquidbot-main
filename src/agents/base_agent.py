"""
Base agent class for multi-agent system.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import discord

from src.llm import OpenRouterClient
from src.rag import HybridRetriever
from src.utils import get_logger

logger = get_logger(__name__)


@dataclass
class AgentConfig:
    """Agent configuration from YAML."""
    
    name: str
    description: str
    channels: List[str]
    system_prompt: str
    rag_enabled: bool
    rag_sources: List[str]  # 'docs', 'channels', or specific collection names
    supports_vision: bool
    include_images: bool
    max_history: int
    tools: List[str]
    response: Dict[str, Any]


class BaseAgent(ABC):
    """
    Base class for all agents.
    
    Provides common functionality:
    - RAG retrieval
    - LLM generation
    - Message formatting
    - Tool execution
    """
    
    def __init__(
        self,
        config: AgentConfig,
        llm_client: OpenRouterClient,
        retriever: Optional[HybridRetriever] = None,
    ):
        """Initialize agent."""
        self.config = config
        self.llm_client = llm_client
        self.retriever = retriever
        self._guild_channels: Optional[str] = None  # Cached channel list
        self._channel_purposes: Optional[Dict[str, str]] = None  # Channel purposes
        
        logger.info(
            "agent_initialized",
            agent_name=config.name,
            rag_enabled=config.rag_enabled,
            tools=config.tools,
        )
    
    def set_guild_channels(self, channels_info: str):
        """Set current guild channels for context."""
        self._guild_channels = channels_info
    
    def set_channel_purposes(self, purposes: Dict[str, str]):
        """Set channel purposes for context (channel_id -> description)."""
        self._channel_purposes = purposes
    
    async def process_message(
        self,
        message: discord.Message,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Process incoming message and generate response.
        
        Args:
            message: Discord message object
            query: User query text
            conversation_history: Previous messages in conversation (optional)
            
        Returns:
            Generated response text
        """
        logger.info(
            "agent_processing_message",
            agent=self.config.name,
            query=query[:50],
        )
        
        # Store message for channel link formatting
        self._message = message
        
        # Build context
        context = await self._build_context(query, message)
        
        # Execute tools if needed
        tool_results = await self._execute_tools(query, message)
        if tool_results:
            context = f"{context}\n\n**Tool Results:**\n{tool_results}"
        
        # Generate response with conversation history and images
        response = await self._generate_response(query, context, conversation_history or [], message)
        
        # Format response
        formatted_response = await self._format_response(response, context)
        
        logger.info(
            "agent_response_generated",
            agent=self.config.name,
            response_length=len(formatted_response),
        )
        
        return formatted_response
    
    def _clean_query_for_rag(self, query: str, message: discord.Message) -> str:
        """
        Clean query for better RAG search.
        
        Replaces Discord mentions with actual usernames for semantic search.
        """
        import re
        
        # Replace user mentions <@123456> with usernames
        def replace_mention(match):
            user_id = match.group(1)
            # Try to get user from message.mentions
            for user in message.mentions:
                if str(user.id) == user_id:
                    # Use display_name (with discriminator fallback) for better matching
                    username = user.global_name or user.display_name or user.name
                    return f"@{username}"
            return match.group(0)  # Keep original if not found
        
        cleaned = re.sub(r'<@!?(\d+)>', replace_mention, query)
        
        # Replace channel mentions <#123456> with channel names
        def replace_channel(match):
            channel_id = match.group(1)
            if message.guild:
                channel = message.guild.get_channel(int(channel_id))
                if channel:
                    return f"#{channel.name}"
            return match.group(0)
        
        cleaned = re.sub(r'<#(\d+)>', replace_channel, cleaned)
        
        # Replace role mentions <@&123456> with role names
        def replace_role(match):
            role_id = match.group(1)
            if message.guild:
                role = message.guild.get_role(int(role_id))
                if role:
                    return f"@{role.name}"
            return match.group(0)
        
        cleaned = re.sub(r'<@&(\d+)>', replace_role, cleaned)
        
        logger.debug(
            "query_cleaned_for_rag",
            original=query,
            cleaned=cleaned,
        )
        
        return cleaned
    
    def _should_skip_rag(self, query: str) -> bool:
        """
        Determine if RAG search should be skipped for simple queries.
        
        Skip RAG for:
        - Simple greetings (gm, hi, hello, привет, etc.)
        - Short reactions (lmao, lol, nice, etc.)
        - Very short queries (<10 chars)
        
        Args:
            query: User query text
        
        Returns:
            True if RAG should be skipped
        """
        query_lower = query.lower().strip()
        
        # Very short queries (likely not informational)
        if len(query_lower) < 10:
            # Check if it's a simple greeting or reaction
            simple_patterns = [
                'gm', 'gn', 'hi', 'hey', 'hello', 'sup', 'yo',
                'привет', 'пока', 'ку', 'здарова',
                'lmao', 'lol', 'kek', 'nice', 'cool', 'bruh',
                'thanks', 'ty', 'thx', 'ok', 'okay',
                '👍', '👋', '🔥', '💀', '😂',
            ]
            
            # Exact match or query starts with pattern
            for pattern in simple_patterns:
                if query_lower == pattern or query_lower.startswith(pattern + ' '):
                    return True
        
        return False
    
    async def _build_context(
        self,
        query: str,
        message: discord.Message,
    ) -> str:
        """Build context from RAG and other sources."""
        logger.debug(
            "build_context_called",
            agent=self.config.name,
            rag_enabled=self.config.rag_enabled,
            has_retriever=self.retriever is not None,
        )
        
        if not self.config.rag_enabled:
            logger.debug(
                "rag_disabled",
                agent=self.config.name,
            )
            return ""
        
        if not self.retriever:
            logger.warning(
                "rag_retriever_not_initialized",
                agent=self.config.name,
                rag_enabled=self.config.rag_enabled,
            )
            return ""
        
        # Skip RAG for simple queries (cost optimization)
        if self._should_skip_rag(query):
            logger.debug(
                "rag_skipped_simple_query",
                agent=self.config.name,
                query=query[:50],
            )
            return ""
        
        logger.info(f"🔍 Searching | {self.config.name}")
        
        # Clean query for better semantic search (replace mentions with names)
        cleaned_query = self._clean_query_for_rag(query, message)
        
        # Get collections to search based on rag_sources config
        collections_to_search = await self._get_rag_collections(message)
        
        if not collections_to_search:
            logger.debug(f"no_collections | {self.config.name}")
            return ""
        
        # Search all collections in parallel for speed
        async def search_collection(collection_id: str):
            """Search a single collection."""
            try:
                results = await self.retriever.retrieve(
                    query=cleaned_query,
                    channel_id=collection_id,
                    top_k=3,
                )
                return results
            except Exception as e:
                logger.warning(
                    "collection_search_failed",
                    collection=collection_id,
                    error=str(e),
                )
                return []
        
        # Execute all searches in parallel
        search_tasks = [search_collection(cid) for cid in collections_to_search]
        results_lists = await asyncio.gather(*search_tasks)
        
        # Combine all results
        all_results = []
        for results in results_lists:
            all_results.extend(results)
        
        # Filter out current message (don't reference the user's own message they just sent)
        current_message_id = str(message.id)
        all_results = [
            r for r in all_results
            if r.metadata.get('message_id') != current_message_id
        ]
        
        if not all_results:
            logger.info(f"⚠️ No context found | {self.config.name}")
            return ""
        
        # Sort by score and take top 3 (reduced from 5 for cost optimization)
        all_results.sort(key=lambda x: x.score, reverse=True)
        top_results = all_results[:3]
        
        # Build context string with message links
        context_parts = []
        for r in top_results:
            # Get message link if available
            message_url = r.metadata.get('url')
            channel_name = r.metadata.get('channel_name', 'Unknown')
            
            if message_url:
                # Use Discord message link
                source_info = f"[Source: Message in #{channel_name}]({message_url})"
            else:
                # Fallback to channel name only
                source_info = f"[Source: #{channel_name}]"
            
            context_parts.append(f"{source_info}\n{r.content}")
        
        context = "\n\n".join(context_parts)
        
        # Add instruction to use message links (optional, not mandatory)
        context = (
            "**Chat History** (recent messages for context):\n\n"
            + context
            + "\n\n(You can reference these messages if relevant, but don't force it into every response)"
        )
        
        # Log what was found
        for i, r in enumerate(top_results, 1):
            content_preview = r.content[:80].replace("\n", " ")
            source = r.metadata.get('channel_name', r.type)
            logger.info(f"   📄 {i}. [{source}] {content_preview}...")
        
        return context
    
    async def _get_rag_collections(
        self,
        message: discord.Message,
    ) -> List[str]:
        """
        Get list of collections to search based on rag_sources config.
        
        Sources can be:
        - 'docs': search documentation collections (arc_docs, liquid_docs, etc.)
        - 'channels': search channel message collections
        - specific collection name: search that specific collection
        """
        from src.rag.qdrant_singleton import get_qdrant_client
        
        qdrant = get_qdrant_client()
        all_collections = qdrant.get_collections().collections
        collection_names = [c.name for c in all_collections]
        
        collections_to_search = []
        
        for source in self.config.rag_sources:
            if source == 'docs':
                # Add all doc collections (not channel IDs)
                doc_collections = [
                    name for name in collection_names
                    if not name.split('_')[-1].isdigit()  # Not a channel ID (numeric)
                ]
                collections_to_search.extend(doc_collections)
            
            elif source == 'channels':
                # Add all channel message collections (have numeric channel IDs)
                # Extract just the channel ID part (last segment after prefix)
                for name in collection_names:
                    if name.split('_')[-1].isdigit():  # Is a channel ID (numeric)
                        # Extract channel_id: discord_bot_1234567890 -> 1234567890
                        channel_id = name.replace(f"{self.retriever.collection_prefix}_", "")
                        collections_to_search.append(channel_id)
            
            else:
                # Specific collection name
                full_name = f"{self.retriever.collection_prefix}_{source}"
                if full_name in collection_names:
                    collections_to_search.append(source)
                elif source in collection_names:
                    # Extract just the ID part
                    collections_to_search.append(source.replace(f"{self.retriever.collection_prefix}_", ""))
        
        # Remove duplicates
        collections_to_search = list(set(collections_to_search))
        
        return collections_to_search
    
    async def _execute_tools(
        self,
        query: str,
        message: discord.Message,
    ) -> Optional[str]:
        """Execute agent tools if needed."""
        if not self.config.tools:
            return None
        
        # Subclasses override this to implement tool execution
        return None
    
    async def _generate_response(
        self,
        query: str,
        context: str,
        conversation_history: List[Dict[str, str]],
        message: discord.Message = None,
    ) -> str:
        """Generate LLM response with conversation history and optional images."""
        # Build base system prompt
        base_prompt = self.config.system_prompt
        
        # Add channel list if available
        if self._guild_channels:
            base_prompt += f"\n\n**available server channels (use exact names when mentioning):**\n{self._guild_channels}"
        
        # Add channel purposes if available
        if self._channel_purposes:
            purposes_text = "\n".join([f"<#{cid}>: {desc}" for cid, desc in self._channel_purposes.items()])
            base_prompt += f"""

**CHANNEL GUIDE (CRITICAL - follow these rules strictly):**
{purposes_text}

**CHANNEL ACCESS RULES:**
- "open to all users" = ANYONE can write messages there, no special roles needed
- "read only" = users can ONLY read, cannot post messages (official announcements, etc.)

**NEVER give wrong info about channels:**
- NEVER say a channel requires special roles if it's marked "open to all users"
- NEVER suggest users can post in "read only" channels
- when directing users to a channel, mention if they can post there or just read"""
            logger.debug(
                "channel_purposes_injected",
                agent=self.config.name,
                purposes_count=len(self._channel_purposes),
            )
        
        # Build system prompt with context
        if context:
            system_prompt = f"""{base_prompt}

**IMPORTANT - Use this retrieved information to answer:**

{context}

**CRITICAL RULES for using context:**
- If context contains URLs/links - use them EXACTLY as provided, don't make up alternatives
- If context contains specific facts (APY, fees, features) - use the exact numbers/details
- Only say "I don't know" if the context truly doesn't have the answer
- Never guess or make up information when precise details are in the context"""
        else:
            system_prompt = base_prompt
        
        # Build messages with conversation history
        messages = []
        
        # Add conversation history (last N messages based on max_history)
        max_history = self.config.max_history
        if conversation_history and max_history > 0:
            # Take last max_history pairs (user + assistant)
            recent_history = conversation_history[-(max_history * 2):]
            messages.extend(recent_history)
        
        # Build current query message with images if present
        if message and (message.attachments or message.stickers):
            # Multimodal content with text + images
            content = [{"type": "text", "text": query}]
            
            # Add image attachments
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": attachment.url}
                    })
            
            # Add stickers (they have URLs too)
            for sticker in message.stickers:
                if hasattr(sticker, 'url') and sticker.url:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": sticker.url}
                    })
            
            messages.append({"role": "user", "content": content})
        else:
            # Text-only message
            messages.append({"role": "user", "content": query})
        
        # Generate response
        response = await self.llm_client.chat_completion(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=self.config.response.get("max_tokens", 1000),
            temperature=0.7,
        )
        
        return response.content.strip()
    
    def _format_channel_links(
        self,
        response: str,
        guild_id: int,
    ) -> str:
        """
        Convert #channel mentions to Discord links.
        
        Converts #channel-name to clickable links:
        https://discord.com/channels/GUILD_ID/CHANNEL_ID
        """
        import re
        
        # Pattern to match #channel-name
        pattern = r'#([\w-]+)'
        
        def replace_channel(match):
            channel_name = match.group(1)
            
            # Try to find channel by name in the guild
            if hasattr(self, '_message') and self._message and self._message.guild:
                guild = self._message.guild
                channel = discord.utils.get(guild.channels, name=channel_name)
                
                if channel:
                    # Return Discord link format
                    return f"<#{channel.id}>"
            
            # If not found, keep original
            return match.group(0)
        
        return re.sub(pattern, replace_channel, response)
    
    async def _format_response(
        self,
        response: str,
        context: str,
    ) -> str:
        """Format response with citations and disclaimer."""
        # Fix markdown
        formatted = response.replace("####", "###")
        
        # Convert #channel mentions to Discord links
        if hasattr(self, '_message') and self._message and self._message.guild:
            formatted = self._format_channel_links(formatted, self._message.guild.id)
        
        # Add citations if enabled
        if self.config.response.get("include_citations") and context:
            formatted += "\n\n-# ⚠️ AI-generated response. Please verify critical information."
        
        return formatted
    
    @abstractmethod
    def get_name(self) -> str:
        """Get agent name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get agent description."""
        pass
