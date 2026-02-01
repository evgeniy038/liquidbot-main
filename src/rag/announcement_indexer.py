"""
Announcement channel indexer for RAG.

Indexes messages from announcement channels into Qdrant
so the bot can use them to answer questions.
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Set

import discord

from src.rag import MultimodalEmbedder, MultimodalIndexer
from src.rag.indexer import DocumentMetadata
from src.rag.qdrant_singleton import get_qdrant_client
from src.llm import OpenRouterClient
from src.utils import get_config, get_logger

logger = get_logger(__name__)


class AnnouncementIndexer:
    """Indexes announcement channel messages into Qdrant for RAG."""
    
    def __init__(
        self,
        bot: discord.Client,
        channel_ids: List[str],
    ):
        """
        Initialize announcement indexer.
        
        Args:
            bot: Discord bot client
            channel_ids: List of channel IDs to index
        """
        self.bot = bot
        self.channel_ids = channel_ids
        self.indexed_message_ids: Set[str] = set()
        
        # Initialize components
        config = get_config()
        
        self.embedder = MultimodalEmbedder(
            openai_api_key=config.llm.api_key,
            base_url=config.embeddings.base_url if hasattr(config, 'embeddings') else 'https://openrouter.ai/api/v1'
        )
        
        self.llm = OpenRouterClient(
            api_key=config.llm.api_key,
            model=config.llm.model
        )
        
        self.indexer = MultimodalIndexer(
            embedder=self.embedder,
            llm_client=self.llm,
            qdrant_path=config.vector_db.path,
            collection_prefix=config.vector_db.collection_prefix
        )
        
        logger.info("announcement_indexer_initialized", channels=len(channel_ids))
    
    async def index_channel(
        self,
        channel_id: str,
        limit: int = 100,
    ) -> int:
        """
        Index messages from a channel.
        
        Args:
            channel_id: Channel ID to index
            limit: Max messages to fetch
            
        Returns:
            Number of messages indexed
        """
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            logger.warning(f"Channel {channel_id} not found")
            return 0
        
        indexed_count = 0
        
        try:
            async for message in channel.history(limit=limit):
                # Skip if already indexed
                if str(message.id) in self.indexed_message_ids:
                    continue
                
                # Skip empty messages
                if not message.content or len(message.content.strip()) < 10:
                    continue
                
                # Skip bot messages
                if message.author.bot:
                    continue
                
                # Create metadata
                metadata = DocumentMetadata(
                    message_id=str(message.id),
                    channel_id=str(channel.id),
                    channel_name=channel.name,
                    category_id=str(channel.category_id) if channel.category_id else None,
                    guild_id=str(message.guild.id) if message.guild else None,
                    author_id=str(message.author.id),
                    timestamp=message.created_at.isoformat(),
                    title=f"Announcement from #{channel.name}",
                    source="discord_announcement",
                    url=message.jump_url,
                )
                
                # Index the message
                try:
                    await self.indexer.index_text(
                        text=message.content,
                        metadata=metadata,
                    )
                    self.indexed_message_ids.add(str(message.id))
                    indexed_count += 1
                except Exception as e:
                    logger.debug(f"Failed to index message {message.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error indexing channel {channel_id}: {e}")
        
        if indexed_count > 0:
            logger.debug(f"announcements_indexed: {channel.name}, count={indexed_count}")
        
        return indexed_count
    
    async def index_all_channels(self, limit: int = 100) -> int:
        """
        Index all configured announcement channels.
        
        Args:
            limit: Max messages per channel
            
        Returns:
            Total messages indexed
        """
        total = 0
        for channel_id in self.channel_ids:
            count = await self.index_channel(channel_id, limit)
            total += count
        
        logger.debug(f"total_announcements_indexed: {total}")
        return total
    
    async def index_new_message(self, message: discord.Message) -> bool:
        """
        Index a single new message (call on message event).
        
        Args:
            message: Discord message to index
            
        Returns:
            True if indexed, False otherwise
        """
        # Check if from indexed channel
        if str(message.channel.id) not in self.channel_ids:
            return False
        
        # Skip if already indexed
        if str(message.id) in self.indexed_message_ids:
            return False
        
        # Skip empty/short messages
        if not message.content or len(message.content.strip()) < 10:
            return False
        
        # Skip bot messages
        if message.author.bot:
            return False
        
        try:
            metadata = DocumentMetadata(
                message_id=str(message.id),
                channel_id=str(message.channel.id),
                channel_name=message.channel.name,
                category_id=str(message.channel.category_id) if message.channel.category_id else None,
                guild_id=str(message.guild.id) if message.guild else None,
                author_id=str(message.author.id),
                timestamp=message.created_at.isoformat(),
                title=f"Announcement from #{message.channel.name}",
                source="discord_announcement",
                url=message.jump_url,
            )
            
            await self.indexer.index_text(
                text=message.content,
                metadata=metadata,
            )
            self.indexed_message_ids.add(str(message.id))
            logger.debug(f"new_announcement_indexed: {message.channel.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index new announcement: {e}")
            return False


# Singleton instance
_announcement_indexer: Optional[AnnouncementIndexer] = None


def get_announcement_indexer(
    bot: discord.Client = None,
    channel_ids: List[str] = None,
) -> Optional[AnnouncementIndexer]:
    """
    Get or create announcement indexer singleton.
    
    Args:
        bot: Discord bot client (required for first call)
        channel_ids: Channel IDs to index (required for first call)
        
    Returns:
        AnnouncementIndexer instance or None
    """
    global _announcement_indexer
    
    if _announcement_indexer is None and bot and channel_ids:
        _announcement_indexer = AnnouncementIndexer(bot, channel_ids)
    
    return _announcement_indexer
