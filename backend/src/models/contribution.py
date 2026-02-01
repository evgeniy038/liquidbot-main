"""Contribution models."""

from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class Contribution(Base):
    """Community contributions."""
    
    __tablename__ = "contributions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    discord_id: Mapped[str] = mapped_column(String(20), index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    content_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(String(50))  # article, video, tool, design, etc.
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected, featured
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Vote counts (cached)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    downvotes: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="contributions")
    votes = relationship("ContributionVote", back_populates="contribution", lazy="selectin")


class ContributionVote(Base):
    """Votes on contributions."""
    
    __tablename__ = "contribution_votes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    contribution_id: Mapped[int] = mapped_column(ForeignKey("contributions.id"))
    voter_discord_id: Mapped[str] = mapped_column(String(20), index=True)
    
    # Vote
    vote_type: Mapped[str] = mapped_column(String(10))  # upvote, downvote
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contribution = relationship("Contribution", back_populates="votes")
