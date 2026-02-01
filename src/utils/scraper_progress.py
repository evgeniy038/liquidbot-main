"""
Scraper progress tracker to persist scraping state across bot restarts.

Saves the last scraped message ID for each channel to avoid re-scraping.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from src.utils import get_logger

logger = get_logger(__name__)


class ScraperProgress:
    """
    Tracks scraping progress to avoid re-scraping messages after restart.
    
    Stores:
    - Last scraped message ID per channel
    - Timestamp of last scrape
    - Total messages scraped per channel
    """
    
    def __init__(self, progress_file: str = "data/scraper_progress.json"):
        """
        Initialize scraper progress tracker.
        
        Args:
            progress_file: Path to progress JSON file
        """
        self.progress_file = Path(progress_file)
        self.progress: Dict[str, Dict] = {}
        
        # Ensure data directory exists
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing progress
        self._load_progress()
        
        # Silent init
    
    def _load_progress(self):
        """Load progress from JSON file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    self.progress = json.load(f)
                
                pass  # Progress loaded
            except Exception as e:
                logger.error(
                    "failed_to_load_progress",
                    error=str(e),
                )
                self.progress = {}
        else:
            logger.info("no_existing_progress_found")
            self.progress = {}
    
    def _save_progress(self):
        """Save progress to JSON file."""
        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
            
            logger.debug("scraper_progress_saved")
        except Exception as e:
            logger.error(
                "failed_to_save_progress",
                error=str(e),
            )
    
    def get_last_message_id(self, channel_id: str) -> Optional[str]:
        """
        Get last scraped message ID for channel.
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            Last message ID or None if never scraped
        """
        channel_data = self.progress.get(channel_id, {})
        return channel_data.get("last_message_id")
    
    def update_progress(
        self,
        channel_id: str,
        channel_name: str,
        last_message_id: str,
        messages_scraped: int
    ):
        """
        Update scraping progress for channel.
        
        Args:
            channel_id: Discord channel ID
            channel_name: Channel name
            last_message_id: ID of last scraped message
            messages_scraped: Number of messages scraped in this session
        """
        if channel_id not in self.progress:
            self.progress[channel_id] = {
                "channel_name": channel_name,
                "first_scraped": datetime.utcnow().isoformat(),
                "total_messages": 0,
            }
        
        # Update data
        self.progress[channel_id].update({
            "channel_name": channel_name,  # Update in case renamed
            "last_message_id": last_message_id,
            "last_scraped": datetime.utcnow().isoformat(),
            "total_messages": self.progress[channel_id].get("total_messages", 0) + messages_scraped,
        })
        
        # Save to file
        self._save_progress()
        
        logger.debug(
            "progress_updated",
            channel_id=channel_id,
            channel_name=channel_name,
            messages_scraped=messages_scraped,
        )
    
    def get_channel_stats(self, channel_id: str) -> Optional[Dict]:
        """
        Get scraping stats for channel.
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            Channel stats dict or None
        """
        return self.progress.get(channel_id)
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get all channel scraping stats."""
        return self.progress.copy()
    
    def reset_channel(self, channel_id: str):
        """
        Reset progress for specific channel.
        
        Args:
            channel_id: Discord channel ID
        """
        if channel_id in self.progress:
            del self.progress[channel_id]
            self._save_progress()
            
            logger.info(
                "channel_progress_reset",
                channel_id=channel_id,
            )
    
    def reset_all(self):
        """Reset all scraping progress."""
        self.progress = {}
        self._save_progress()
        
        logger.info("all_progress_reset")
