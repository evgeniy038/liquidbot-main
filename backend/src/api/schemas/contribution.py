"""Contribution schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ContributionCreate(BaseModel):
    """Create contribution request."""
    discord_id: str
    title: str
    description: str
    content_url: Optional[str] = None
    category: str  # article, video, tool, design, etc.


class ContributionVoteRequest(BaseModel):
    """Vote on contribution request."""
    contribution_id: int
    voter_discord_id: str
    vote_type: str  # upvote, downvote


class ContributionResponse(BaseModel):
    """Contribution response."""
    id: int
    discord_id: str
    title: str
    description: str
    content_url: Optional[str] = None
    category: str
    status: str
    is_featured: bool
    upvotes: int
    downvotes: int
    created_at: datetime
    approved_at: Optional[datetime] = None
    author_username: Optional[str] = None

    class Config:
        from_attributes = True


class ContributionVotesResponse(BaseModel):
    """Contribution votes response."""
    contribution_id: int
    upvotes: int
    downvotes: int
    net_votes: int


class EligibilityResponse(BaseModel):
    """Eligibility check response."""
    eligible: bool
    reason: Optional[str] = None
    cooldown_ends: Optional[datetime] = None
