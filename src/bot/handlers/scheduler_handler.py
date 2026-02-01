"""
Scheduler handler for periodic tasks.

Handles scheduled tasks:
- Daily reports
- Activity checks

Extracted from client.py for better maintainability.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

import discord

from src.utils import get_logger

if TYPE_CHECKING:
    from src.analytics import DailyReportGenerator
    from src.analytics.activity_checker import ActivityChecker

logger = get_logger(__name__)


class SchedulerHandler:
    """
    Handler for scheduled periodic tasks.
    
    Features:
    - Daily report generation
    - Activity checking
    - Configurable schedules
    """
    
    def __init__(
        self,
        bot: discord.Client,
        config,
        report_generator: Optional["DailyReportGenerator"] = None,
        activity_checker: Optional["ActivityChecker"] = None,
    ):
        """
        Initialize scheduler handler.
        
        Args:
            bot: Discord bot instance
            config: Bot configuration
            report_generator: Daily report generator
            activity_checker: Activity checker instance
        """
        self.bot = bot
        self.config = config
        self.report_generator = report_generator
        self.activity_checker = activity_checker
        
        # Task references
        self.daily_report_task: Optional[asyncio.Task] = None
        self.activity_check_task: Optional[asyncio.Task] = None
    
    def start_all(self):
        """Start all scheduled tasks."""
        if self.config.reports.enabled and self.report_generator:
            self.daily_report_task = asyncio.create_task(
                self._daily_report_scheduler()
            )
        
        if (hasattr(self.config, 'activity_checker') and 
            self.config.activity_checker.enabled and 
            self.activity_checker):
            self.activity_check_task = asyncio.create_task(
                self._activity_check_scheduler()
            )
    
    def cancel_all(self):
        """Cancel all scheduled tasks."""
        if self.daily_report_task:
            self.daily_report_task.cancel()
        
        if self.activity_check_task:
            self.activity_check_task.cancel()
    
    async def _daily_report_scheduler(self):
        """Background task to send daily reports at scheduled time."""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                now = datetime.utcnow()
                scheduled_hour = self.config.reports.schedule["hour"]
                scheduled_minute = self.config.reports.schedule["minute"]
                
                target_time = now.replace(
                    hour=scheduled_hour,
                    minute=scheduled_minute,
                    second=0,
                    microsecond=0
                )
                
                if now >= target_time:
                    target_time += timedelta(days=1)
                
                sleep_seconds = (target_time - now).total_seconds()
                
                await asyncio.sleep(sleep_seconds)
                await self._send_scheduled_report()
                
            except asyncio.CancelledError:
                logger.info("daily_report_scheduler_cancelled")
                break
            except Exception as e:
                logger.error("daily_report_scheduler_error", error=str(e), exc_info=True)
                await asyncio.sleep(3600)
    
    async def _send_scheduled_report(self):
        """Send daily report to configured channel."""
        try:
            if not self.config.reports.channel_id:
                logger.warning("report_channel_not_configured")
                return
            
            channel_id = int(self.config.reports.channel_id)
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                logger.error("report_channel_not_found", channel_id=channel_id)
                return
            
            await self._send_daily_report(channel)
            
        except Exception as e:
            logger.error("scheduled_report_send_failed", error=str(e), exc_info=True)
    
    async def _send_daily_report(self, channel: discord.TextChannel):
        """Generate and send daily activity report."""
        try:
            logger.info("generating_daily_report", channel=channel.name)
            
            status_msg = await channel.send("📊 Generating community activity report...")
            
            report_data = await self.report_generator.generate_report(
                bot=self.bot,
                days=self.config.reports.days_to_analyze,
            )
            
            embed = self.report_generator.format_embed(report_data)
            await status_msg.delete()
            await channel.send(embed=embed)
            
            logger.info(
                "daily_report_sent",
                channel=channel.name,
                total_messages=report_data["total_messages"],
                total_users=report_data["total_users"],
            )
            
        except Exception as e:
            logger.error(
                "daily_report_send_failed", 
                channel=channel.name if channel else "unknown", 
                error=str(e), 
                exc_info=True
            )
            await channel.send("❌ Failed to generate report. Check logs for details.")
    
    async def _activity_check_scheduler(self):
        """Background task to check user activity at scheduled time."""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                now = datetime.utcnow()
                scheduled_hour = self.config.activity_checker.schedule["hour"]
                scheduled_minute = self.config.activity_checker.schedule["minute"]
                
                target_time = now.replace(
                    hour=scheduled_hour,
                    minute=scheduled_minute,
                    second=0,
                    microsecond=0
                )
                
                if now >= target_time:
                    target_time += timedelta(days=1)
                
                sleep_seconds = (target_time - now).total_seconds()
                
                await asyncio.sleep(sleep_seconds)
                await self._send_activity_report()
                
            except asyncio.CancelledError:
                logger.info("activity_check_scheduler_cancelled")
                break
            except Exception as e:
                logger.error("activity_check_scheduler_error", error=str(e), exc_info=True)
                await asyncio.sleep(3600)
    
    async def _send_activity_report(self):
        """Check activity and send report."""
        try:
            report_channel_id = self.config.activity_checker.report_channel_id
            if not report_channel_id:
                logger.warning("activity_report_channel_not_configured")
                return
            
            channel_id = int(report_channel_id)
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                logger.error("activity_report_channel_not_found", channel_id=channel_id)
                return
            
            logger.info("checking_user_activity", channel=channel.name)
            
            # Check activity
            embed, inactive_users = await self.activity_checker.check_activity()
            
            # Send report only if there are inactive users
            if embed:
                await channel.send(embed=embed)
                logger.info("activity_report_sent", channel=channel.name)
                
                # Send DMs to inactive users
                if inactive_users:
                    success, failed = await self.activity_checker.send_dm_to_inactive_users(
                        inactive_users=inactive_users,
                        min_messages=self.config.activity_checker.min_messages,
                        days=self.config.activity_checker.days_to_check,
                    )
                    if success > 0:
                        logger.info(f"📬 Sent {success} DMs to inactive users ({failed} failed)")
            else:
                logger.info("no_inactive_users_to_report")
            
        except Exception as e:
            logger.error("activity_report_send_failed", error=str(e), exc_info=True)
