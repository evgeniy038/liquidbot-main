"""
Message scraper handler.

Handles background message scraping and indexing:
- Historical message scraping
- Progress tracking for incremental scraping
- Batch message indexing to SQLite

Extracted from client.py for better maintainability.
"""

import asyncio
from typing import Dict, Set, Any, Optional, TYPE_CHECKING

import discord

from src.utils import get_logger, console_print, ScraperProgress
from src.rag import get_message_storage, StoredMessage

if TYPE_CHECKING:
    from src.rag import MultimodalIndexer
    from src.rag.announcement_indexer import AnnouncementIndexer

logger = get_logger(__name__)


class ScraperHandler:
    """
    Handler for background message scraping.
    
    Features:
    - Incremental scraping (resume from last message)
    - Parallel channel scraping
    - Batch indexing to SQLite
    - Progress tracking
    """
    
    def __init__(
        self,
        bot: discord.Client,
        config: Any,
        message_storage = None,
        announcement_indexer: Optional["AnnouncementIndexer"] = None,
    ):
        """
        Initialize scraper handler.
        
        Args:
            bot: Discord bot instance
            config: Bot configuration
            message_storage: SQLite message storage
            announcement_indexer: Announcement indexer for RAG
        """
        self.bot = bot
        self.config = config
        self.message_storage = message_storage or get_message_storage()
        self.announcement_indexer = announcement_indexer
        self.scraper_progress = ScraperProgress()
        
        # Scraping statistics
        self.scraping_enabled = False
        self.stats: Dict[str, Any] = {
            "messages_scraped": 0,
            "messages_indexed": 0,
            "channels_scraped": 0,
            "users_tracked": set(),
        }
    
    async def start_background_scraper(self):
        """
        Background task to scrape historical messages.
        
        If scrape_on_startup=False:
          - Skip historical scraping
          - Initialize progress tracking
        
        If scrape_on_startup=True:
          - Scrape full history or incremental
        """
        try:
            # Wait for bot to be fully ready
            await asyncio.sleep(5)
            
            # Check if historical scraping is disabled
            if not self.config.auto_indexing.scrape_on_startup:
                logger.info("📌 INITIALIZING_PROGRESS_TRACKING")
                console_print(f"\n{'='*80}")
                console_print(f"{'📌 PROGRESS TRACKING INITIALIZATION':^80}")
                console_print(f"{'Historical scraping disabled - tracking latest messages':^80}")
                console_print(f"{'='*80}\n")
                
                await self._initialize_progress_tracking()
                
                console_print(f"\n{'='*80}")
                console_print(f"{'✅ PROGRESS TRACKING INITIALIZED':^80}")
                console_print(f"{'Bot will scrape only NEW messages from now on':^80}")
                console_print(f"{'='*80}\n")
                
                self.scraping_enabled = False
                return
            
            logger.info("background_scraper_starting")
            console_print(f"\n{'='*80}")
            console_print(f"{'📚 BACKGROUND MESSAGE SCRAPER STARTED':^80}")
            console_print(f"{'='*80}\n")
            
            self.scraping_enabled = True
            
            # Get all guilds (only allowed ones)
            allowed_guilds = self.config.discord.allowed_guilds
            for guild in self.bot.guilds:
                if allowed_guilds and guild.id not in allowed_guilds:
                    logger.debug(f"skipped_guild: {guild.name}")
                    continue
                
                await self._scrape_guild(guild)
            
            # Print final statistics
            self._log_final_stats()
            self.scraping_enabled = False
            
        except Exception as e:
            logger.error("background_scraper_error", error=str(e), exc_info=True)
            self.scraping_enabled = False
    
    async def _scrape_guild(self, guild: discord.Guild):
        """Scrape all channels in a guild."""
        logger.debug(f"scraping_guild: {guild.name}")
        console_print(f"🏢 Scraping Guild: {guild.name}")
        console_print(f"   Channels: {len(guild.text_channels)}")
        
        # Filter valid channels
        valid_channels = []
        for channel in guild.text_channels:
            # Check exclusion by name or ID
            if channel.name in self.config.auto_indexing.exclude_channels:
                continue
            if str(channel.id) in self.config.auto_indexing.exclude_channels:
                continue
            
            permissions = channel.permissions_for(guild.me)
            if not permissions.read_message_history:
                console_print(f"   ⏭️  Skipped #{channel.name} (no permission)")
                continue
            
            valid_channels.append(channel)
        
        # Parallel scraping
        if valid_channels:
            max_parallel = self.config.auto_indexing.parallel_channels
            console_print(
                f"   🚀 Scraping {len(valid_channels)} channels "
                f"(max {max_parallel} concurrent)..."
            )
            
            semaphore = asyncio.Semaphore(max_parallel)
            
            async def scrape_with_limit(channel):
                async with semaphore:
                    try:
                        await self._scrape_channel(
                            channel,
                            limit=self.config.auto_indexing.scrape_limit_per_channel
                        )
                    except discord.Forbidden:
                        console_print(f"   ⚠️  No access to #{channel.name}")
                    except Exception as e:
                        logger.error(f"channel_scraping_error: {channel.name}: {e}")
            
            await asyncio.gather(*[scrape_with_limit(ch) for ch in valid_channels])
    
    async def _initialize_progress_tracking(self):
        """Initialize progress tracking without scraping."""
        channels_initialized = 0
        
        for guild in self.bot.guilds:
            console_print(f"🏢 Guild: {guild.name}")
            
            for channel in guild.text_channels:
                try:
                    if channel.name in self.config.auto_indexing.exclude_channels:
                        continue
                    
                    # Check category
                    if hasattr(channel, 'category') and channel.category:
                        category_id = str(channel.category.id)
                        if category_id in self.config.auto_indexing.ignored_categories:
                            console_print(f"   ⏭️  Skipped #{channel.name} (ignored category)")
                            continue
                    
                    permissions = channel.permissions_for(guild.me)
                    if not permissions.read_message_history:
                        console_print(f"   ⏭️  Skipped #{channel.name} (no permissions)")
                        continue
                    
                    channel_id = str(channel.id)
                    existing = self.scraper_progress.get_last_message_id(channel_id)
                    
                    if existing:
                        console_print(f"   ✅ #{channel.name} - Already tracked")
                        channels_initialized += 1
                        continue
                    
                    # Get most recent message
                    latest_message = None
                    async for message in channel.history(limit=1):
                        latest_message = message
                        break
                    
                    if latest_message:
                        self.scraper_progress.update_progress(
                            channel_id=channel_id,
                            channel_name=channel.name,
                            last_message_id=str(latest_message.id),
                            messages_scraped=0,
                        )
                        console_print(
                            f"   📌 #{channel.name} - Tracking from "
                            f"{str(latest_message.id)[-8:]}"
                        )
                        channels_initialized += 1
                    else:
                        console_print(f"   ⚠️  #{channel.name} - Empty channel")
                
                except discord.Forbidden:
                    console_print(f"   ⚠️  #{channel.name} - No access")
                except Exception as e:
                    logger.error(f"progress_init_error: {channel.name}: {e}")
        
        console_print(f"\n   📊 Initialized tracking for {channels_initialized} channels")
    
    async def _scrape_channel(
        self, 
        channel: discord.TextChannel, 
        limit: Optional[int] = None
    ):
        """
        Scrape historical messages from a channel.
        
        Uses incremental scraping - only new messages since last run.
        """
        channel_name = channel.name
        channel_id = str(channel.id)
        
        # Check category
        if hasattr(channel, 'category') and channel.category:
            category_id = str(channel.category.id)
            if category_id in self.config.auto_indexing.ignored_categories:
                console_print(
                    f"   ⏭️  Skipped #{channel_name} "
                    f"(ignored category: {channel.category.name})"
                )
                return
        
        # Check if channel was scraped before
        last_message_id = self.scraper_progress.get_last_message_id(channel_id)
        
        messages_count = 0
        indexed_count = 0
        batch_count = 0
        latest_message_id = None
        message_batch = []
        BATCH_SIZE = self.config.auto_indexing.batch_size
        
        # Skip counters
        skipped_bots = 0
        skipped_empty = 0
        skipped_duplicates = 0
        
        try:
            after = discord.Object(id=int(last_message_id)) if last_message_id else None
            
            async for message in channel.history(limit=limit, oldest_first=False, after=after):
                # Skip bot messages
                if message.author.bot and self.config.auto_indexing.exclude_bots:
                    skipped_bots += 1
                    continue
                
                # Skip empty messages
                if not self._has_content(message):
                    skipped_empty += 1
                    continue
                
                messages_count += 1
                batch_count += 1
                
                if latest_message_id is None:
                    latest_message_id = str(message.id)
                
                # Progress indicator
                if batch_count >= 100:
                    console_print(
                        f"     📦 #{channel_name}: {messages_count} processed, "
                        f"{indexed_count} indexed..."
                    )
                    batch_count = 0
                
                # Check for duplicate
                if self.message_storage.message_exists(str(message.id)):
                    skipped_duplicates += 1
                    continue
                
                message_batch.append(message)
                
                # Process batch
                if len(message_batch) >= BATCH_SIZE:
                    indexed_count += await self._index_batch(
                        message_batch, channel_id, channel_name
                    )
                    message_batch = []
            
            # Process remaining
            if message_batch:
                indexed_count += await self._index_batch(
                    message_batch, channel_id, channel_name
                )
            
            # Update statistics
            self.stats["messages_scraped"] += messages_count
            self.stats["messages_indexed"] += indexed_count
            self.stats["channels_scraped"] += 1
            
            # Save progress
            if latest_message_id:
                self.scraper_progress.update_progress(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    last_message_id=latest_message_id,
                    messages_scraped=indexed_count,
                )
            
            # Log
            total_skipped = skipped_bots + skipped_empty + skipped_duplicates
            if total_skipped > 0 or indexed_count > 0:
                console_print(
                    f"   ✅ #{channel_name}: {indexed_count} indexed | "
                    f"skipped: {skipped_bots} bots, {skipped_duplicates} dupes, "
                    f"{skipped_empty} empty"
                )
        
        except Exception as e:
            logger.error(f"channel_scraping_error: {channel_name}: {e}", exc_info=True)
    
    def _has_content(self, message: discord.Message) -> bool:
        """Check if message has any content."""
        return bool(
            message.content or 
            message.attachments or 
            message.stickers or 
            message.embeds
        )
    
    async def _index_batch(
        self, 
        messages: list, 
        channel_id: str, 
        channel_name: str
    ) -> int:
        """
        Index a batch of messages to SQLite.
        
        Returns:
            Number of successfully indexed messages
        """
        stored_messages = []
        
        for message in messages:
            try:
                author_roles = [
                    str(role.id) for role in message.author.roles
                ] if hasattr(message.author, 'roles') else []
                
                category_id = None
                if hasattr(message.channel, 'category') and message.channel.category:
                    category_id = str(message.channel.category.id)
                
                content = self._build_content(message)
                
                stored_msg = StoredMessage(
                    message_id=str(message.id),
                    channel_id=channel_id,
                    channel_name=channel_name,
                    guild_id=str(message.guild.id) if message.guild else None,
                    category_id=category_id,
                    author_id=str(message.author.id),
                    author_name=message.author.name,
                    author_display_name=message.author.display_name,
                    author_roles=author_roles,
                    content=content,
                    timestamp=message.created_at.isoformat(),
                    url=message.jump_url,
                    attachments_count=len(message.attachments),
                )
                stored_messages.append(stored_msg)
                self.stats["users_tracked"].add(str(message.author.id))
                
            except Exception as e:
                logger.error(f"message_conversion_failed: {message.id}: {e}")
        
        indexed_count = self.message_storage.store_messages_batch(stored_messages)
        
        if indexed_count > 0:
            logger.info(
                "BATCH_INDEXED_SQLITE",
                channel=channel_name,
                indexed=indexed_count,
            )
        
        return indexed_count
    
    def _build_content(self, message: discord.Message) -> str:
        """Build content string for message."""
        content = message.content
        if not content:
            parts = []
            if message.attachments:
                att_types = [
                    a.content_type.split('/')[0] if a.content_type else 'file' 
                    for a in message.attachments
                ]
                parts.append(f"[{len(message.attachments)} attachment(s): {', '.join(att_types)}]")
            if message.stickers:
                sticker_names = [s.name for s in message.stickers]
                parts.append(f"[sticker: {', '.join(sticker_names)}]")
            if message.embeds:
                parts.append(f"[{len(message.embeds)} embed(s)]")
            content = " ".join(parts) if parts else "[empty]"
        return content
    
    def _log_final_stats(self):
        """Log final scraping statistics."""
        logger.info(
            "📊 SCRAPING_COMPLETED",
            total_scraped=self.stats.get("messages_scraped", 0),
            total_indexed=self.stats["messages_indexed"],
            total_channels=self.stats["channels_scraped"],
            total_users=len(self.stats["users_tracked"]),
        )
        
        console_print(f"\n{'='*80}")
        console_print(f"{'📊 SCRAPING COMPLETED':^80}")
        console_print(f"{'='*80}")
        console_print(f"  Messages Scraped: {self.stats.get('messages_scraped', 0)}")
        console_print(f"  Messages Indexed: {self.stats['messages_indexed']}")
        console_print(
            f"  Difference (skipped): "
            f"{self.stats.get('messages_scraped', 0) - self.stats['messages_indexed']}"
        )
        console_print(f"  Channels Scraped: {self.stats['channels_scraped']}")
        console_print(f"  Users Tracked: {len(self.stats['users_tracked'])}")
        console_print(f"{'='*80}\n")
    
    async def auto_index_message(self, message: discord.Message):
        """
        Auto-index a new message in background.
        
        Args:
            message: Discord message to index
        """
        try:
            if not self._has_content(message):
                return
            
            # Guild check
            allowed_guilds = self.config.discord.allowed_guilds
            if message.guild and allowed_guilds and message.guild.id not in allowed_guilds:
                return
            
            channel_name = message.channel.name if hasattr(message.channel, 'name') else 'dm'
            channel_id = str(message.channel.id)
            
            # Exclude check
            if channel_name in self.config.auto_indexing.exclude_channels:
                return
            
            # Category check
            category_id = None
            if hasattr(message.channel, 'category') and message.channel.category:
                category_id = str(message.channel.category.id)
                if category_id in self.config.auto_indexing.ignored_categories:
                    return
            
            # Duplicate check
            if self.message_storage.message_exists(str(message.id)):
                return
            
            # Build and store message
            author_roles = [
                str(role.id) for role in message.author.roles
            ] if hasattr(message.author, 'roles') else []
            
            content = self._build_content(message)
            
            stored_msg = StoredMessage(
                message_id=str(message.id),
                channel_id=channel_id,
                channel_name=channel_name,
                guild_id=str(message.guild.id) if message.guild else None,
                category_id=category_id,
                author_id=str(message.author.id),
                author_name=message.author.name,
                author_display_name=message.author.display_name,
                author_roles=author_roles,
                content=content,
                timestamp=message.created_at.isoformat(),
                url=message.jump_url,
                attachments_count=len(message.attachments),
            )
            
            if self.message_storage.store_message(stored_msg):
                logger.info("MESSAGE_SAVED_SQLITE", channel=channel_name)
                console_print(
                    f"  💾 Saved to SQLite: Message from {message.author.name} "
                    f"in #{channel_name}"
                )
            
            # Index for RAG
            if self.announcement_indexer:
                await self.announcement_indexer.index_new_message(message)
        
        except Exception as e:
            logger.error(f"auto_indexing_failed: {message.id}: {e}")
