"""
Bot handlers module.

Contains modular message, member, moderation, and scraper handlers
extracted from the main client.py for better maintainability.
"""

from src.bot.handlers.message_handler import MessageHandler
from src.bot.handlers.member_handler import MemberHandler
from src.bot.handlers.mod_handler import ModHandler
from src.bot.handlers.scraper_handler import ScraperHandler
from src.bot.handlers.scheduler_handler import SchedulerHandler

__all__ = [
    "MessageHandler",
    "MemberHandler",
    "ModHandler",
    "ScraperHandler",
    "SchedulerHandler",
]
