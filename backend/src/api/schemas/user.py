"""User schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class UserResponse(BaseModel):
    """User response."""
    discord_id: str
    username: str
    avatar_url: Optional[str] = None
    message_count: int = 0
    contribution_points: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """User statistics."""
    discord_id: str
    username: str
    message_count: int
    contribution_points: int
    portfolios_submitted: int
    quests_completed: int
    contributions_made: int
    current_role: Optional[str] = None
    guild: Optional[str] = None
    guild_tier: Optional[int] = None


class TweetInfo(BaseModel):
    """Tweet information."""
    tweet_url: str
    content: Optional[str] = None
    metrics: Optional[dict] = None


class UserDashboard(BaseModel):
    """Comprehensive user dashboard."""
    user: UserResponse
    stats: UserStats
    portfolio_status: Optional[str] = None
    recent_contributions: List[dict] = []
    recent_tweets: List[TweetInfo] = []
    guild_info: Optional[dict] = None
    promotion_history: List[dict] = []


class ServerStats(BaseModel):
    """Server statistics."""
    total_users: int
    total_portfolios: int
    pending_portfolios: int
    approved_portfolios: int
    total_contributions: int
    active_quests: int


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    rank: int
    discord_id: str
    username: str
    avatar_url: Optional[str] = None
    points: int
    contributions: int
