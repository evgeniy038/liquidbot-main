"""Nomination schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class VoteRequest(BaseModel):
    """Vote on nomination request."""
    nomination_id: int
    voter_discord_id: str
    vote_type: str  # approve, reject
    reason: Optional[str] = None


class NominationResponse(BaseModel):
    """Nomination response."""
    id: int
    discord_id: str
    from_role: str
    to_role: str
    reason: Optional[str] = None
    status: str
    approve_count: int
    reject_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    finalized_at: Optional[datetime] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class PendingNominationResponse(BaseModel):
    """Pending nomination for Parliament polling."""
    id: int
    discord_id: str
    username: str
    avatar_url: Optional[str] = None
    from_role: str
    to_role: str
    reason: Optional[str] = None
    portfolio_url: Optional[str] = None
    created_at: datetime
