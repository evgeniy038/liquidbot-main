"""
Analytics for Discord message data stored in Qdrant.

Features:
- User activity rankings
- Channel activity rankings
- Time-based analytics
- Message search and filtering
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

from src.rag.qdrant_singleton import get_qdrant_client
from src.utils import get_logger

logger = get_logger(__name__)


class UserActivity(BaseModel):
    """User activity statistics."""
    user_id: str
    message_count: int
    channels: List[str]
    first_message: datetime
    last_message: datetime
    average_message_length: float


class ChannelActivity(BaseModel):
    """Channel activity statistics."""
    channel_id: str
    channel_name: str
    message_count: int
    unique_users: int
    first_message: datetime
    last_message: datetime
    average_message_length: float


class MessageAnalytics:
    """
    Analytics for Discord messages stored in Qdrant.
    """
    
    def __init__(
        self,
        collection_prefix: str = "discord_bot",
    ):
        """
        Initialize message analytics.
        
        Args:
            collection_prefix: Prefix for collection names
        """
        self.collection_prefix = collection_prefix
        self.qdrant = get_qdrant_client()
        
        logger.info(
            "message_analytics_initialized",
            collection_prefix=collection_prefix,
        )
    
    def _get_collection_name(self, channel_id: str) -> str:
        """Get collection name for channel."""
        return f"{self.collection_prefix}_{channel_id}"
    
    def get_all_collections(self) -> List[str]:
        """
        Get all message collections.
        
        Returns:
            List of collection names
        """
        collections = self.qdrant.get_collections().collections
        return [
            c.name for c in collections
            if c.name.startswith(self.collection_prefix)
        ]
    
    def get_user_activity(
        self,
        user_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[UserActivity]:
        """
        Get user activity statistics.
        
        Args:
            user_id: Filter by specific user (None = all users)
            channel_id: Filter by specific channel (None = all channels)
            limit: Maximum number of users to return
        
        Returns:
            List of user activity statistics
        """
        # Determine which collections to query
        if channel_id:
            collections = [self._get_collection_name(channel_id)]
        else:
            collections = self.get_all_collections()
        
        # Collect user data
        user_data = defaultdict(lambda: {
            "count": 0,
            "channels": set(),
            "timestamps": [],
            "message_lengths": [],
        })
        
        for collection_name in collections:
            try:
                # Build filter
                filter_conditions = []
                if user_id:
                    filter_conditions.append(
                        FieldCondition(
                            key="author_id",
                            match=MatchValue(value=user_id),
                        )
                    )
                
                # Scroll through all points
                offset = None
                while True:
                    result = self.qdrant.scroll(
                        collection_name=collection_name,
                        scroll_filter=Filter(must=filter_conditions) if filter_conditions else None,
                        limit=100,
                        offset=offset,
                        with_payload=True,
                        with_vectors=False,
                    )
                    
                    points, next_offset = result
                    
                    if not points:
                        break
                    
                    for point in points:
                        payload = point.payload
                        
                        # Skip non-text messages
                        if payload.get("type") != "text":
                            continue
                        
                        author_id = payload.get("author_id")
                        if not author_id:
                            continue
                        
                        # Update user data
                        user_data[author_id]["count"] += 1
                        user_data[author_id]["channels"].add(
                            payload.get("channel_id")
                        )
                        
                        timestamp_str = payload.get("timestamp")
                        if timestamp_str:
                            try:
                                timestamp = datetime.fromisoformat(
                                    timestamp_str.replace("Z", "+00:00")
                                )
                                user_data[author_id]["timestamps"].append(timestamp)
                            except:
                                pass
                        
                        content = payload.get("content", "")
                        user_data[author_id]["message_lengths"].append(len(content))
                    
                    if next_offset is None:
                        break
                    
                    offset = next_offset
            
            except Exception as e:
                logger.error(
                    "collection_query_failed",
                    collection_name=collection_name,
                    error=str(e),
                )
        
        # Convert to UserActivity objects
        activities = []
        for uid, data in user_data.items():
            if data["count"] == 0:
                continue
            
            timestamps = sorted(data["timestamps"]) if data["timestamps"] else []
            
            activity = UserActivity(
                user_id=uid,
                message_count=data["count"],
                channels=list(data["channels"]),
                first_message=timestamps[0] if timestamps else datetime.now(),
                last_message=timestamps[-1] if timestamps else datetime.now(),
                average_message_length=(
                    sum(data["message_lengths"]) / len(data["message_lengths"])
                    if data["message_lengths"] else 0
                ),
            )
            activities.append(activity)
        
        # Sort by message count
        activities.sort(key=lambda x: x.message_count, reverse=True)
        
        return activities[:limit]
    
    def get_channel_activity(
        self,
        channel_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ChannelActivity]:
        """
        Get channel activity statistics.
        
        Args:
            channel_id: Filter by specific channel (None = all channels)
            limit: Maximum number of channels to return
        
        Returns:
            List of channel activity statistics
        """
        # Determine which collections to query
        if channel_id:
            collections = [self._get_collection_name(channel_id)]
        else:
            collections = self.get_all_collections()
        
        # Collect channel data
        channel_data = defaultdict(lambda: {
            "name": "",
            "count": 0,
            "users": set(),
            "timestamps": [],
            "message_lengths": [],
        })
        
        for collection_name in collections:
            try:
                # Scroll through all points
                offset = None
                while True:
                    result = self.qdrant.scroll(
                        collection_name=collection_name,
                        limit=100,
                        offset=offset,
                        with_payload=True,
                        with_vectors=False,
                    )
                    
                    points, next_offset = result
                    
                    if not points:
                        break
                    
                    for point in points:
                        payload = point.payload
                        
                        # Skip non-text messages
                        if payload.get("type") != "text":
                            continue
                        
                        cid = payload.get("channel_id")
                        if not cid:
                            continue
                        
                        # Update channel data
                        channel_data[cid]["name"] = payload.get("channel_name", "")
                        channel_data[cid]["count"] += 1
                        
                        author_id = payload.get("author_id")
                        if author_id:
                            channel_data[cid]["users"].add(author_id)
                        
                        timestamp_str = payload.get("timestamp")
                        if timestamp_str:
                            try:
                                timestamp = datetime.fromisoformat(
                                    timestamp_str.replace("Z", "+00:00")
                                )
                                channel_data[cid]["timestamps"].append(timestamp)
                            except:
                                pass
                        
                        content = payload.get("content", "")
                        channel_data[cid]["message_lengths"].append(len(content))
                    
                    if next_offset is None:
                        break
                    
                    offset = next_offset
            
            except Exception as e:
                logger.error(
                    "collection_query_failed",
                    collection_name=collection_name,
                    error=str(e),
                )
        
        # Convert to ChannelActivity objects
        activities = []
        for cid, data in channel_data.items():
            if data["count"] == 0:
                continue
            
            timestamps = sorted(data["timestamps"]) if data["timestamps"] else []
            
            activity = ChannelActivity(
                channel_id=cid,
                channel_name=data["name"],
                message_count=data["count"],
                unique_users=len(data["users"]),
                first_message=timestamps[0] if timestamps else datetime.now(),
                last_message=timestamps[-1] if timestamps else datetime.now(),
                average_message_length=(
                    sum(data["message_lengths"]) / len(data["message_lengths"])
                    if data["message_lengths"] else 0
                ),
            )
            activities.append(activity)
        
        # Sort by message count
        activities.sort(key=lambda x: x.message_count, reverse=True)
        
        return activities[:limit]
    
    def get_activity_by_time_range(
        self,
        start_date: datetime,
        end_date: datetime,
        channel_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Get message activity within a time range.
        
        Args:
            start_date: Start of time range
            end_date: End of time range
            channel_id: Filter by specific channel (None = all channels)
        
        Returns:
            Dictionary with date -> message count
        """
        # Determine which collections to query
        if channel_id:
            collections = [self._get_collection_name(channel_id)]
        else:
            collections = self.get_all_collections()
        
        # Collect daily counts
        daily_counts = defaultdict(int)
        
        for collection_name in collections:
            try:
                # Scroll through all points
                offset = None
                while True:
                    result = self.qdrant.scroll(
                        collection_name=collection_name,
                        limit=100,
                        offset=offset,
                        with_payload=True,
                        with_vectors=False,
                    )
                    
                    points, next_offset = result
                    
                    if not points:
                        break
                    
                    for point in points:
                        payload = point.payload
                        
                        # Skip non-text messages
                        if payload.get("type") != "text":
                            continue
                        
                        timestamp_str = payload.get("timestamp")
                        if not timestamp_str:
                            continue
                        
                        try:
                            timestamp = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            )
                            
                            # Check if in range
                            if start_date <= timestamp <= end_date:
                                date_key = timestamp.date().isoformat()
                                daily_counts[date_key] += 1
                        except:
                            pass
                    
                    if next_offset is None:
                        break
                    
                    offset = next_offset
            
            except Exception as e:
                logger.error(
                    "collection_query_failed",
                    collection_name=collection_name,
                    error=str(e),
                )
        
        return dict(sorted(daily_counts.items()))
    
    def get_top_users(
        self,
        limit: int = 10,
        channel_id: Optional[str] = None,
    ) -> List[Tuple[str, int]]:
        """
        Get top users by message count.
        
        Args:
            limit: Number of top users to return
            channel_id: Filter by channel (None = all channels)
        
        Returns:
            List of (user_id, message_count) tuples
        """
        activities = self.get_user_activity(
            channel_id=channel_id,
            limit=limit,
        )
        
        return [(a.user_id, a.message_count) for a in activities]
    
    def get_top_channels(
        self,
        limit: int = 100,
    ) -> List[Tuple[str, str, int]]:
        """
        Get top channels by message count.
        
        Args:
            limit: Number of top channels to return
        
        Returns:
            List of (channel_id, channel_name, message_count) tuples
        """
        activities = self.get_channel_activity(limit=limit)
        
        return [
            (a.channel_id, a.channel_name, a.message_count)
            for a in activities
        ]
    
    def get_user_message_count(
        self,
        user_id: str,
        guild_id: Optional[str] = None,
    ) -> int:
        """
        Get total message count for a specific user.
        Fast method for scam detection.
        
        Args:
            user_id: User ID to check
            guild_id: Guild ID (optional, for future use)
        
        Returns:
            Total message count across all channels
        """
        try:
            # Get all collections
            collections = self.get_all_collections()
            
            total_count = 0
            
            for collection_name in collections:
                try:
                    # Count points with this author_id
                    result = self.qdrant.count(
                        collection_name=collection_name,
                        count_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="author_id",
                                    match=MatchValue(value=user_id),
                                )
                            ]
                        ),
                    )
                    
                    total_count += result.count
                
                except Exception as e:
                    # Collection might not exist or have issues
                    logger.debug(
                        "count_failed_for_collection",
                        collection_name=collection_name,
                        error=str(e),
                    )
                    continue
            
            logger.debug(
                "user_message_count_retrieved",
                user_id=user_id,
                message_count=total_count,
            )
            
            return total_count
        
        except Exception as e:
            logger.error(
                "failed_to_get_user_message_count",
                user_id=user_id,
                error=str(e),
            )
            return 0
    
    def search_messages(
        self,
        query: str,
        channel_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Search messages by content.
        
        Args:
            query: Search query
            channel_id: Filter by channel
            user_id: Filter by user
            limit: Maximum results
        
        Returns:
            List of message payloads
        """
        # Determine which collections to query
        if channel_id:
            collections = [self._get_collection_name(channel_id)]
        else:
            collections = self.get_all_collections()
        
        results = []
        
        for collection_name in collections:
            try:
                # Build filter
                filter_conditions = []
                if user_id:
                    filter_conditions.append(
                        FieldCondition(
                            key="author_id",
                            match=MatchValue(value=user_id),
                        )
                    )
                
                # Scroll and search
                offset = None
                while True:
                    result = self.qdrant.scroll(
                        collection_name=collection_name,
                        scroll_filter=Filter(must=filter_conditions) if filter_conditions else None,
                        limit=100,
                        offset=offset,
                        with_payload=True,
                        with_vectors=False,
                    )
                    
                    points, next_offset = result
                    
                    if not points:
                        break
                    
                    for point in points:
                        payload = point.payload
                        
                        # Skip non-text messages
                        if payload.get("type") != "text":
                            continue
                        
                        content = payload.get("content", "")
                        
                        # Simple text search
                        if query.lower() in content.lower():
                            results.append(payload)
                            
                            if len(results) >= limit:
                                return results
                    
                    if next_offset is None:
                        break
                    
                    offset = next_offset
            
            except Exception as e:
                logger.error(
                    "search_failed",
                    collection_name=collection_name,
                    error=str(e),
                )
        
        return results[:limit]
