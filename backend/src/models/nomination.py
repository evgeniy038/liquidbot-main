"""Nomination and voting models."""

from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Nomination(Base):
    """Role promotion nominations for Parliament voting."""
    
    __tablename__ = "nominations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    discord_id: Mapped[str] = mapped_column(String(20), index=True)
    
    # Nomination details
    from_role: Mapped[str] = mapped_column(String(50))
    to_role: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    portfolio_id: Mapped[int | None] = mapped_column(ForeignKey("portfolios.id"), nullable=True)
    
    # Discord message tracking
    message_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    channel_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Vote counts (cached)
    approve_count: Mapped[int] = mapped_column(Integer, default=0)
    reject_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="nominations")
    votes = relationship("Vote", back_populates="nomination", lazy="selectin")


class Vote(Base):
    """Parliament votes on nominations."""
    
    __tablename__ = "votes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nomination_id: Mapped[int] = mapped_column(ForeignKey("nominations.id"))
    voter_discord_id: Mapped[str] = mapped_column(String(20), index=True)
    
    # Vote
    vote_type: Mapped[str] = mapped_column(String(10))  # approve, reject
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    nomination = relationship("Nomination", back_populates="votes")
