"""
Discord bot client with multi-agent system and RAG integration.

REFACTORED VERSION:
- Modular handlers for message, member, moderation, scraping, scheduling
- Consolidated filters (gliquid, content)
- Cleaner code structure (~800 lines vs ~2400 lines)
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands

from src.agents import AgentFactory
from src.bot.ai_router import AIRouter
from src.bot.about_command import AboutCommand, AboutView, PingsCommand
try:
    from src.bot.about_command import NotificationPingsView
except ImportError:
    NotificationPingsView = None

from src.bot.contribute_command import ContributeCommand, ContributeView, GuildSelectView, RolesSubView
from src.bot.commands.usage_command import setup_usage_command

# Handlers
from src.bot.handlers.message_handler import MessageHandler
from src.bot.handlers.member_handler import MemberHandler
from src.bot.handlers.mod_handler import ModHandler
from src.bot.handlers.scraper_handler import ScraperHandler
from src.bot.handlers.scheduler_handler import SchedulerHandler
from src.bot.filters.gliquid_filter import get_gliquid_filter

from src.llm import OpenRouterClient
from src.rag import HybridRetriever, MultimodalEmbedder, MultimodalIndexer
from src.rag import get_message_storage
from src.moderation import (
    ScamDetector, 
    ImpersonationChecker, 
    PromotionNotifier, 
    SubmissionHandler, 
    setup_submission_commands
)
from src.rag.announcement_indexer import get_announcement_indexer
from src.analytics import DailyReportGenerator
from src.utils import (
    get_config, 
    get_logger, 
    PRODUCTION_MODE, 
    console_print, 
    ScraperProgress
)

logger = get_logger(__name__)


class DiscordBot(commands.Bot):
    """
    Liquid Discord Bot with multi-agent system and multimodal RAG.
    
    Features:
    - Multi-agent channel routing
    - Multimodal RAG (text + images)
    - Real-time indexing
    - Prompt caching
    - Modular handlers for clean code
    """
    
    def __init__(self):
        """Initialize Discord bot."""
        self.config = get_config()
        
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix=self.config.discord.command_prefix,
            intents=intents,
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                roles=False,
                users=True,
                replied_user=True,
            ),
        )
        
        # Core components
        self.embedder: Optional[MultimodalEmbedder] = None
        self.indexer: Optional[MultimodalIndexer] = None
        self.retriever: Optional[HybridRetriever] = None
        self.llm_client: Optional[OpenRouterClient] = None
        self.message_storage = None
        self.agent_factory: Optional[AgentFactory] = None
        self.ai_router: Optional[AIRouter] = None
        
        # Moderation components
        self.scam_detector: Optional[ScamDetector] = None
        self.impersonation_checker: Optional[ImpersonationChecker] = None
        self.promotion_notifier: Optional[PromotionNotifier] = None
        self.submission_handler: Optional[SubmissionHandler] = None
        
        # Commands
        self.about_command: Optional[AboutCommand] = None
        self.pings_command: Optional[PingsCommand] = None
        self.contribute_command: Optional[ContributeCommand] = None
        
        # Handlers
        self.message_handler: Optional[MessageHandler] = None
        self.member_handler: Optional[MemberHandler] = None
        self.mod_handler: Optional[ModHandler] = None
        self.scraper_handler: Optional[ScraperHandler] = None
        self.scheduler_handler: Optional[SchedulerHandler] = None
        
        # Other components
        self.channel_reader = None
        self.report_generator: Optional[DailyReportGenerator] = None
        self.activity_checker = None
        self.content_filter = None
        self.announcement_indexer = None
    
    async def setup_hook(self):
        """Setup bot components."""
        self.message_storage = get_message_storage()
        
        # Initialize LLM client
        self.llm_client = OpenRouterClient(
            api_key=self.config.llm.api_key,
            model=self.config.llm.model,
            base_url=self.config.llm.base_url,
        )
        
        # Initialize embedder/indexer/retriever
        self.embedder = MultimodalEmbedder(
            openai_api_key=self.config.embeddings.api_key,
            text_model=self.config.embeddings.model,
            clip_model=self.config.embeddings.clip_model,
            base_url=self.config.embeddings.base_url,
        )
        
        self.indexer = MultimodalIndexer(
            embedder=self.embedder,
            llm_client=self.llm_client,
            qdrant_url=self.config.vector_db.url,
            qdrant_path=self.config.vector_db.path,
            qdrant_api_key=self.config.vector_db.api_key,
            collection_prefix=self.config.vector_db.collection_prefix,
        )
        
        self.retriever = HybridRetriever(
            embedder=self.embedder,
            qdrant_url=self.config.vector_db.url,
            qdrant_path=self.config.vector_db.path,
            qdrant_api_key=self.config.vector_db.api_key,
            collection_prefix=self.config.vector_db.collection_prefix,
            ignored_categories=self.config.auto_indexing.ignored_categories,
        )
        
        # Initialize agent factory
        self.agent_factory = AgentFactory(
            config_path=Path("config/agents.yaml"),
            llm_client=self.llm_client,
            retriever=self.retriever,
        )
        
        # Initialize AI Router
        self.ai_router = AIRouter(llm_client=self.llm_client)
        
        # Initialize moderation components
        self._init_moderation()
        
        # Initialize commands
        self._init_commands()
        
        # Initialize content filter
        if hasattr(self.config, 'content_filter') and self.config.content_filter.enabled:
            from src.moderation.content_filter import ContentFilter
            self.content_filter = ContentFilter(
                bot=self,
                config=self.config.content_filter.model_dump(),
            )
        
        # Initialize submission handler
        if hasattr(self.config, 'content_submissions') and self.config.content_submissions.enabled:
            self.submission_handler = SubmissionHandler(
                bot=self,
                config=self.config.content_submissions.model_dump(),
            )
        
        # Components initialized silently
    
    def _init_moderation(self):
        """Initialize moderation components."""
        if self.config.moderation.enabled:
            self.scam_detector = ScamDetector(
                llm_client=self.llm_client,
                bot=self,
                config=self.config.moderation.model_dump(),
            )
        
        if self.config.member_update.anti_impersonation.enabled:
            self.impersonation_checker = ImpersonationChecker(
                message_storage=self.message_storage
            )
        
        if self.config.member_update.promotions.enabled:
            self.promotion_notifier = PromotionNotifier()
    
    def _init_commands(self):
        """Initialize command handlers."""
        if self.config.about_command.enabled:
            self.about_command = AboutCommand()
            self.pings_command = PingsCommand()
        
        self.contribute_command = ContributeCommand()
    
    def _init_handlers(self):
        """Initialize modular handlers (called in on_ready)."""
        # Mod handler
        self.mod_handler = ModHandler(
            bot=self,
            llm_client=self.llm_client,
        )
        
        # Member handler
        self.member_handler = MemberHandler(
            bot=self,
            impersonation_checker=self.impersonation_checker,
            promotion_notifier=self.promotion_notifier,
        )
        
        # Message handler
        self.message_handler = MessageHandler(
            bot=self,
            config=self.config,
            agent_factory=self.agent_factory,
            ai_router=self.ai_router,
            scam_detector=self.scam_detector,
            content_filter=self.content_filter,
            mod_handler=self.mod_handler,
            submission_handler=self.submission_handler,
            announcement_indexer=self.announcement_indexer,
        )
        
        # Scraper handler
        self.scraper_handler = ScraperHandler(
            bot=self,
            config=self.config,
            message_storage=self.message_storage,
            announcement_indexer=self.announcement_indexer,
        )
        
        # Scheduler handler
        self.scheduler_handler = SchedulerHandler(
            bot=self,
            config=self.config,
            report_generator=self.report_generator,
            activity_checker=self.activity_checker,
        )
    
    async def _set_avatar(self):
        """Set bot avatar from local file."""
        avatar_path = Path("assets/avatar.gif")
        
        if not avatar_path.exists():
            return
        
        try:
            avatar_data = avatar_path.read_bytes()
            await self.user.edit(avatar=avatar_data)
            logger.info("avatar_set", path=str(avatar_path))
        except discord.HTTPException as e:
            if e.code != 50035:
                logger.warning("avatar_set_failed", error=str(e))
        except Exception as e:
            logger.warning("avatar_set_error", error=str(e))
    
    async def on_ready(self):
        """Called when bot is ready."""
        # Set status
        await self.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="tryliquid.xyz"
            )
        )
        
        await self._set_avatar()
        
        # Initialize channel reader
        from src.tools import ChannelReader
        self.channel_reader = ChannelReader(bot=self)
        
        if self.agent_factory:
            self.agent_factory.set_channel_reader(self.channel_reader)
        
        # Register persistent views
        self._register_views()
        
        # Initialize report generator
        from src.rag.qdrant_singleton import get_qdrant_client
        self.report_generator = DailyReportGenerator(get_qdrant_client())
        
        # Register slash commands
        await self._register_slash_commands()
        
        # Initialize activity checker
        if hasattr(self.config, 'activity_checker') and self.config.activity_checker.enabled:
            from src.analytics.activity_checker import ActivityChecker
            self.activity_checker = ActivityChecker(
                bot=self,
                config=self.config.activity_checker.model_dump(),
            )
        
        # Initialize announcement indexer
        await self._init_announcement_indexer()
        
        # Initialize handlers
        self._init_handlers()
        
        # Start schedulers
        self.scheduler_handler.start_all()
        
        # Start submission expiry checker
        if self.submission_handler:
            asyncio.create_task(self.submission_handler.start_expiry_checker())
        
        # Start background scraper
        if self.config.auto_indexing.enabled and self.config.auto_indexing.scrape_on_startup:
            asyncio.create_task(self.scraper_handler.start_background_scraper())
        
        # Sync commands
        await self.tree.sync()
        
        # Single clean ready message
        logger.info(f"✅ {self.user.name} online | {len(self.guilds)} guild(s)")
        
        # Print startup info
        if not PRODUCTION_MODE:
            self._print_startup_info()
    
    def _register_views(self):
        """Register persistent views."""
        if self.config.moderation.enabled:
            from src.moderation.alert_sender import ScamAlertView
            self.add_view(ScamAlertView(message_id="", user_id="", guild=None))
        
        if self.config.about_command.enabled:
            self.add_view(AboutView(self.config.about_command))
            if NotificationPingsView:
                self.add_view(NotificationPingsView())
        
        self.add_view(ContributeView())
        self.add_view(GuildSelectView())
        self.add_view(RolesSubView())
        
        if self.submission_handler:
            from src.moderation.submission_handler import DecisionView
            self.add_view(DecisionView(self.submission_handler, 0))
    
    async def _register_slash_commands(self):
        """Register slash commands."""
        # /report command
        @discord.app_commands.command(
            name="report", 
            description="Generate community activity report (Admin only)"
        )
        async def report_slash(interaction: discord.Interaction):
            allowed_role_ids = {1436799852171235472, 1436767320239243519}
            user_role_ids = {role.id for role in interaction.user.roles}
            
            has_access = (
                interaction.user.guild_permissions.administrator or
                bool(user_role_ids & allowed_role_ids)
            )
            
            if not has_access:
                await interaction.response.send_message(
                    "❌ This command is only available to administrators.",
                    ephemeral=True
                )
                return
            
            await interaction.response.defer()
            
            try:
                report_data = await self.report_generator.generate_report(
                    bot=self,
                    days=self.config.reports.days_to_analyze,
                )
                embed = self.report_generator.format_embed(report_data)
                await interaction.followup.send(embed=embed)
            except Exception as e:
                logger.error("report_generation_failed", error=str(e))
                await interaction.followup.send("❌ Failed to generate report.")
        
        self.tree.add_command(report_slash)
        
        # /usage command
        self.tree.add_command(setup_usage_command(self))
        
        # Optional commands
        if hasattr(self.config, 'nominations') and self.config.nominations.enabled:
            from src.bot.commands.nominate_command import setup_nominate_command
            setup_nominate_command(self, self.config.nominations.model_dump())
        
        if hasattr(self.config, 'react_all') and self.config.react_all.enabled:
            from src.bot.commands.react_all_command import setup_react_all_command
            setup_react_all_command(self, self.config.react_all.model_dump())
        
        if hasattr(self.config, 'activity_checker') and self.config.activity_checker.enabled:
            from src.bot.commands.check_activity_command import setup_check_activity_command
            setup_check_activity_command(self, self.config.activity_checker.model_dump())
        
        if self.submission_handler:
            setup_submission_commands(self, self.submission_handler)
        
        # Portfolio, Guild, Parliament commands
        try:
            from src.bot.commands.portfolio_command import setup_portfolio_commands
            portfolio_config = {
                "review_channel_id": os.getenv("REVIEW_CHANNEL_ID", ""),
            }
            setup_portfolio_commands(self, portfolio_config)
        except Exception as e:
            logger.warning(f"Portfolio commands not loaded: {e}")
        
        try:
            from src.bot.commands.guild_command import setup_guild_commands
            setup_guild_commands(self, {})
        except Exception as e:
            logger.warning(f"Guild commands not loaded: {e}")
        
        try:
            from src.bot.commands.parliament_command import setup_parliament_commands
            parliament_config = {
                "channel_id": os.getenv("PARLIAMENT_CHANNEL_ID", ""),
            }
            setup_parliament_commands(self, parliament_config)
        except Exception as e:
            logger.warning(f"Parliament commands not loaded: {e}")
        
        # Error handler
        @self.tree.error
        async def on_app_command_error(
            interaction: discord.Interaction, 
            error: discord.app_commands.AppCommandError
        ):
            if isinstance(error, discord.app_commands.errors.MissingPermissions):
                await interaction.response.send_message(
                    "❌ You don't have permission to use this command.",
                    ephemeral=True
                )
            else:
                logger.error("slash_command_error", error=str(error))
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ An error occurred.",
                        ephemeral=True
                    )
    
    async def _init_announcement_indexer(self):
        """Initialize announcement indexer."""
        try:
            import yaml
            with open('config/channels.yaml') as f:
                channels_config = yaml.safe_load(f)
            indexed_channels = channels_config.get('channels', {}).get('indexed_for_rag', [])
            if indexed_channels:
                self.announcement_indexer = get_announcement_indexer(
                    bot=self,
                    channel_ids=indexed_channels,
                )
                asyncio.create_task(self._index_announcements())
        except Exception as e:
            logger.debug(f"Announcement indexer not initialized: {e}")
    
    async def _index_announcements(self):
        """Index announcement channels."""
        try:
            await asyncio.sleep(3)
            if self.announcement_indexer:
                await self.announcement_indexer.index_all_channels(limit=50)
        except Exception as e:
            logger.error(f"Failed to index announcements: {e}")
    
    def _print_startup_info(self):
        """Print startup information."""
        print(f"\n{'='*80}")
        print(f"{'💧 LIQUID DISCORD BOT - MULTI-AGENT SYSTEM ONLINE':^80}")
        print(f"{'='*80}")
        print(f"\n📊 System Info:")
        print(f"  Bot User: {self.user}")
        print(f"  Guilds: {len(self.guilds)}")
        print(f"  LLM Model: {self.config.llm.model}")
        print(f"  RAG: ✅ Enabled")
        print(f"\n{'='*80}")
        print(f"✅ Bot ready! Mention @{self.user.name} in any channel to start.")
        print(f"{'='*80}\n")
    
    # ==================== EVENT HANDLERS ====================
    
    async def on_message(self, message: discord.Message):
        """Handle incoming messages."""
        # Handle prefix commands first
        if self.about_command and message.content.strip().startswith("!about"):
            if await self.about_command.handle_command(message):
                return
        
        if self.pings_command and message.content.strip().startswith("!pings"):
            if await self.pings_command.handle_command(message):
                return
        
        if self.contribute_command and message.content.strip().startswith("!contribute"):
            if await self.contribute_command.handle_command(message):
                return
        
        await self.process_commands(message)
        
        # Delegate to message handler
        if self.message_handler:
            handled = await self.message_handler.handle_message(message)
            if handled:
                return
        
        # Auto-index if enabled
        if self.config.auto_indexing.enabled and self.scraper_handler:
            asyncio.create_task(self.scraper_handler.auto_index_message(message))
    
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle reaction additions."""
        if payload.user_id == self.user.id:
            return
        if self.submission_handler:
            await self.submission_handler.handle_reaction(payload)
    
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Handle reaction removals."""
        if payload.user_id == self.user.id:
            return
        if self.submission_handler:
            await self.submission_handler.handle_reaction_remove(payload)
    
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Handle edited messages."""
        if before.content == after.content:
            return
        if after.author.bot or not after.guild:
            return
        
        # Scam detection
        if self.scam_detector and self.config.moderation.enabled:
            result = await self.scam_detector.analyze_message(after)
            if result and result.is_scam:
                try:
                    await after.delete()
                    logger.info(f"🗑️ Deleted edited scam message from @{after.author.name}")
                except:
                    pass
                return
        
        # Gliquid filter
        gliquid_filter = get_gliquid_filter()
        await gliquid_filter.filter_message(after, log_prefix="_edit")
    
    async def on_member_join(self, member: discord.Member):
        """Handle new member joins."""
        if self.member_handler:
            await self.member_handler.handle_member_join(member)
    
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Handle member updates."""
        if self.member_handler:
            await self.member_handler.handle_member_update(before, after)
    
    async def on_user_update(self, before: discord.User, after: discord.User):
        """Handle user updates."""
        if self.member_handler:
            await self.member_handler.handle_user_update(before, after)
    
    async def close(self):
        """Cleanup on shutdown."""
        logger.info("bot_shutting_down")
        
        if self.scheduler_handler:
            self.scheduler_handler.cancel_all()
        
        if self.llm_client:
            await self.llm_client.close()
        
        await super().close()
        logger.info("bot_closed")


async def run_bot():
    """Run the Discord bot."""
    bot = DiscordBot()
    
    try:
        config = get_config()
        token = config.discord.token
        
        if not token or token == "${DISCORD_TOKEN}":
            logger.error("token_not_configured")
            print("❌ ERROR: DISCORD_TOKEN environment variable is not set!")
            return
        
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("bot_interrupted")
    except asyncio.CancelledError:
        logger.info("bot_cancelled")
    except Exception as e:
        logger.error("bot_run_error", error=str(e))
    finally:
        if not bot.is_closed():
            await bot.close()
        logger.info("⏹️ bot_stopped")
