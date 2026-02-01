"""Portfolio schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class PortfolioTweetSchema(BaseModel):
    """Tweet schema for portfolio."""
    tweet_url: str
    tweet_id: Optional[str] = None
    content: Optional[str] = None
    metrics: Optional[dict] = None


class PortfolioCreate(BaseModel):
    """Create portfolio request."""
    discord_id: str
    email: Optional[str] = None
    username: str


class PortfolioUpdate(BaseModel):
    """Update portfolio data."""
    bio: Optional[str] = None
    twitter_handle: Optional[str] = None
    achievements: Optional[str] = None
    notion_url: Optional[str] = None
    target_role: Optional[str] = None
    tweets: Optional[List[PortfolioTweetSchema]] = None
    other_works: Optional[List[str]] = None


class PortfolioSubmit(BaseModel):
    """Submit portfolio for review."""
    discord_id: str


class PortfolioReview(BaseModel):
    """Review portfolio request."""
    discord_id: str
    reviewer_id: str
    action: str = Field(..., pattern="^(approve|reject|request_changes)$")
    feedback: Optional[str] = None


class PortfolioResponse(BaseModel):
    """Portfolio response."""
    id: int
    discord_id: str
    status: str
    bio: Optional[str] = None
    twitter_handle: Optional[str] = None
    achievements: Optional[str] = None
    notion_url: Optional[str] = None
    target_role: Optional[str] = None
    current_role: Optional[str] = None
    ai_score: Optional[int] = None
    ai_feedback: Optional[str] = None
    review_feedback: Optional[str] = None
    rejection_reason: Optional[str] = None
    other_works: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    tweets: List[PortfolioTweetSchema] = []

    @validator('other_works', pre=True)
    def parse_other_works(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return []
        return v

    class Config:
        from_attributes = True


class CanResubmitResponse(BaseModel):
    """Can resubmit check response."""
    can_resubmit: bool
    cooldown_ends: Optional[datetime] = None
    days_remaining: Optional[int] = None


class PortfolioHistoryResponse(BaseModel):
    """Portfolio history response."""
    from_role: str
    to_role: str
    promoted_at: datetime
    snapshot_data: Optional[dict] = None

    class Config:
        from_attributes = True
