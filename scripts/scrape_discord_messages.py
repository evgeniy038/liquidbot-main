"""
Script to scrape all historical Discord messages from accessible channels.

Features:
- Scrapes all messages from all accessible channels
- Stores messages with author, channel, and timestamp metadata
- Supports analytics for user/channel activity
- Handles rate limits and pagination
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import discord
from dotenv import load_dotenv

from src.rag import MultimodalEmbedder, MultimodalIndexer
from src.rag.indexer import DocumentMetadata
from src.llm import OpenRouterClient
from src.utils import get_config, get_logger

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = get_logger(__name__)


class DiscordMessageScraper:
    """
    Scrapes Discord messages and indexes them for analytics.
    """
    
    def __init__(self):
        """Initialize message scraper."""
        load_dotenv()
        self.config = get_config()
        
        # Setup Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        self.client = discord.Client(intents=intents)
        
        # Initialize components
        self.embedder: Optional[MultimodalEmbedder] = None
        self.indexer: Optional[MultimodalIndexer] = None
        self.llm_client: Optional[OpenRouterClient] = None
        
        # Statistics
        self.stats = {
            "total_messages": 0,
            "total_channels": 0,
            "messages_by_channel": {},
            "messages_by_user": {},
            "errors": 0,
        }
        
        logger.info("message_scraper_initialized")
    
    async def setup(self):
        """Setup scraper components."""
        logger.info("setting_up_scraper_components")
        
        # Initialize embedder
        self.embedder = MultimodalEmbedder(
            openai_api_key=self.config.embeddings.api_key,
            text_model=self.config.embeddings.model,
            clip_model=self.config.embeddings.clip_model,
        )
        
        # Initialize LLM client
        self.llm_client = OpenRouterClient(
            api_key=self.config.llm.api_key,
            model=self.config.llm.model,
            base_url=self.config.llm.base_url,
        )
        
        # Initialize indexer
        self.indexer = MultimodalIndexer(
            embedder=self.embedder,
            llm_client=self.llm_client,
            qdrant_url=self.config.vector_db.url,
            qdrant_path=self.config.vector_db.path,
            qdrant_api_key=self.config.vector_db.api_key,
            collection_prefix=self.config.vector_db.collection_prefix,
        )
        
        logger.info("scraper_components_ready")
    
    async def scrape_channel(
        self,
        channel: discord.TextChannel,
        limit: Optional[int] = None,
    ) -> Dict[str, int]:
        """
        Scrape messages from a single channel.
        
        Args:
            channel: Discord text channel
            limit: Maximum number of messages to scrape (None = all)
        
        Returns:
            Stats dictionary with message counts
        """
        channel_name = channel.name
        channel_id = str(channel.id)
        
        logger.info(
            "scraping_channel_started",
            channel_name=channel_name,
            channel_id=channel_id,
        )
        
        print(f"\n{'='*80}")
        print(f"📨 Scraping Channel: #{channel_name}")
        print(f"{'='*80}")
        
        messages_scraped = 0
        messages_indexed = 0
        
        try:
            # Fetch messages with pagination
            async for message in channel.history(limit=limit, oldest_first=False):
                # Skip bot messages
                if message.author.bot:
                    continue
                
                # Skip empty messages
                if not message.content and not message.attachments:
                    continue
                
                messages_scraped += 1
                
                # Create metadata
                metadata = DocumentMetadata(
                    message_id=str(message.id),
                    channel_id=channel_id,
                    channel_name=channel_name,
                    author_id=str(message.author.id),
                    timestamp=message.created_at.isoformat(),
                    title=f"Message from {message.author.name}",
                    source=f"discord://channel/{channel_id}/message/{message.id}",
                    url=message.jump_url,
                )
                
                # Index message content
                if message.content:
                    try:
                        # Create enriched content with author info
                        enriched_content = (
                            f"Author: {message.author.name} ({message.author.display_name})\n"
                            f"Channel: #{channel_name}\n"
                            f"Timestamp: {message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                            f"---\n{message.content}"
                        )
                        
                        chunks = await self.indexer.index_text(
                            text=enriched_content,
                            metadata=metadata,
                        )
                        
                        if chunks > 0:
                            messages_indexed += 1
                            
                            # Update stats
                            self.stats["messages_by_user"][str(message.author.id)] = \
                                self.stats["messages_by_user"].get(str(message.author.id), 0) + 1
                        
                    except Exception as e:
                        logger.error(
                            "message_indexing_failed",
                            message_id=str(message.id),
                            error=str(e),
                        )
                        self.stats["errors"] += 1
                
                # Index attachments (images)
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        try:
                            await self.indexer.index_image(
                                image_url=attachment.url,
                                metadata=metadata,
                            )
                        except Exception as e:
                            logger.error(
                                "image_indexing_failed",
                                message_id=str(message.id),
                                attachment_url=attachment.url,
                                error=str(e),
                            )
                            self.stats["errors"] += 1
                
                # Progress update
                if messages_scraped % 100 == 0:
                    print(f"  ⏳ Scraped {messages_scraped} messages, indexed {messages_indexed}...")
            
            # Update channel stats
            self.stats["messages_by_channel"][channel_id] = messages_indexed
            
            print(f"\n✅ Channel Complete:")
            print(f"   Messages scraped: {messages_scraped}")
            print(f"   Messages indexed: {messages_indexed}")
            print(f"{'='*80}\n")
            
            logger.info(
                "channel_scraping_complete",
                channel_name=channel_name,
                messages_scraped=messages_scraped,
                messages_indexed=messages_indexed,
            )
            
            return {
                "scraped": messages_scraped,
                "indexed": messages_indexed,
            }
            
        except discord.Forbidden:
            logger.error(
                "channel_access_denied",
                channel_name=channel_name,
            )
            print(f"❌ Access denied to #{channel_name}")
            return {"scraped": 0, "indexed": 0}
        
        except Exception as e:
            logger.error(
                "channel_scraping_error",
                channel_name=channel_name,
                error=str(e),
                exc_info=True,
            )
            print(f"❌ Error scraping #{channel_name}: {e}")
            return {"scraped": 0, "indexed": 0}
    
    async def scrape_all_channels(
        self,
        guild_id: Optional[int] = None,
        limit_per_channel: Optional[int] = None,
    ) -> None:
        """
        Scrape all accessible channels in all guilds.
        
        Args:
            guild_id: Specific guild ID to scrape (None = all guilds)
            limit_per_channel: Max messages per channel (None = all)
        """
        await self.client.wait_until_ready()
        
        print(f"\n{'='*80}")
        print(f"{'🤖 DISCORD MESSAGE SCRAPER':^80}")
        print(f"{'='*80}")
        print(f"\n📊 Bot Info:")
        print(f"   Bot User: {self.client.user}")
        print(f"   Bot ID: {self.client.user.id}")
        print(f"   Total Guilds: {len(self.client.guilds)}")
        
        # Filter guilds
        guilds = self.client.guilds
        if guild_id:
            guilds = [g for g in guilds if g.id == guild_id]
        
        print(f"   Target Guilds: {len(guilds)}")
        print(f"\n{'='*80}\n")
        
        # Scrape each guild
        for guild in guilds:
            print(f"\n🏢 Guild: {guild.name} (ID: {guild.id})")
            print(f"   Total Channels: {len(guild.text_channels)}")
            
            # Scrape each text channel
            for channel in guild.text_channels:
                try:
                    stats = await self.scrape_channel(
                        channel=channel,
                        limit=limit_per_channel,
                    )
                    
                    self.stats["total_messages"] += stats["indexed"]
                    self.stats["total_channels"] += 1
                    
                    # Rate limit protection
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(
                        "channel_scraping_failed",
                        channel_name=channel.name,
                        error=str(e),
                    )
                    self.stats["errors"] += 1
        
        # Print final statistics
        self.print_statistics()
    
    def print_statistics(self):
        """Print scraping statistics."""
        print(f"\n{'='*80}")
        print(f"{'📊 SCRAPING STATISTICS':^80}")
        print(f"{'='*80}")
        print(f"\n📈 Overall Stats:")
        print(f"   Total Channels: {self.stats['total_channels']}")
        print(f"   Total Messages: {self.stats['total_messages']}")
        print(f"   Errors: {self.stats['errors']}")
        
        print(f"\n📊 Top Channels by Activity:")
        sorted_channels = sorted(
            self.stats["messages_by_channel"].items(),
            key=lambda x: x[1],
            reverse=True,
        )
        for channel_id, count in sorted_channels[:10]:
            print(f"   Channel {channel_id}: {count} messages")
        
        print(f"\n👥 Top Users by Activity:")
        sorted_users = sorted(
            self.stats["messages_by_user"].items(),
            key=lambda x: x[1],
            reverse=True,
        )
        for user_id, count in sorted_users[:10]:
            print(f"   User {user_id}: {count} messages")
        
        print(f"\n{'='*80}\n")
        
        logger.info(
            "scraping_complete",
            total_channels=self.stats["total_channels"],
            total_messages=self.stats["total_messages"],
            errors=self.stats["errors"],
        )
    
    async def run(
        self,
        guild_id: Optional[int] = None,
        limit_per_channel: Optional[int] = None,
    ):
        """
        Run the scraper.
        
        Args:
            guild_id: Specific guild ID (None = all)
            limit_per_channel: Max messages per channel (None = all)
        """
        @self.client.event
        async def on_ready():
            print(f"✅ Bot connected as {self.client.user}")
            
            # Setup components
            await self.setup()
            
            # Start scraping
            await self.scrape_all_channels(
                guild_id=guild_id,
                limit_per_channel=limit_per_channel,
            )
            
            # Cleanup
            await self.llm_client.close()
            await self.client.close()
        
        # Start client
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("DISCORD_TOKEN not found in environment")
        
        await self.client.start(token)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scrape Discord messages for analytics"
    )
    parser.add_argument(
        "--guild-id",
        type=int,
        help="Specific guild ID to scrape (optional)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Max messages per channel (default: all)",
    )
    
    args = parser.parse_args()
    
    scraper = DiscordMessageScraper()
    
    try:
        await scraper.run(
            guild_id=args.guild_id,
            limit_per_channel=args.limit,
        )
    except KeyboardInterrupt:
        logger.info("scraper_interrupted")
        print("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        logger.error("scraper_error", error=str(e), exc_info=True)
        print(f"\n❌ Scraping error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
