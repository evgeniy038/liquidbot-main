"""
Base filter class for content filtering.

Provides common interface for all content filters.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Message


class BaseFilter(ABC):
    """Abstract base class for message filters."""
    
    @abstractmethod
    async def filter_message(self, message: "Message") -> bool:
        """
        Filter a message.
        
        Args:
            message: Discord message to filter
            
        Returns:
            True if message was filtered (deleted), False otherwise
        """
        pass
    
    @abstractmethod
    def should_filter(self, message: "Message") -> bool:
        """
        Check if message should be filtered.
        
        Args:
            message: Discord message to check
            
        Returns:
            True if message should be checked by this filter
        """
        pass
