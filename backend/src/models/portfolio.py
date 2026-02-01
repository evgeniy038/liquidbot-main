"""Portfolio models."""

from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class PortfolioStatus(str, Enum):
    """Portfolio status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_VOTE = "pending_vote"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROMOTED = "promoted"


class Portfolio(Base):
    """User portfolio for role promotion."""
    
    __tablename__ = "portfolios"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    discord_id: Mapped[str] = mapped_column(String(20), index=True)
    
    # Portfolio content
    notion_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    twitter_handle: Mapped[str | None] = mapped_column(String(50), nullable=True)
    achievements: Mapped[str | None] = mapped_column(Text, nullable=True)
    other_works: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of links
    
    # Target role
    target_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default=PortfolioStatus.DRAFT.value)
    
    # AI Analysis
    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Review
    reviewer_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    review_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    voting_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    tweets = relationship("PortfolioTweet", back_populates="portfolio", lazy="selectin")
    history = relationship("PortfolioHistory", back_populates="portfolio", lazy="selectin")
    votes = relationship("PortfolioVote", back_populates="portfolio", lazy="selectin")


class PortfolioHistory(Base):
    """Archived portfolio history after promotion."""
    
    __tablename__ = "portfolio_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    discord_id: Mapped[str] = mapped_column(String(20), index=True)
    
    # Snapshot
    from_role: Mapped[str] = mapped_column(String(50))
    to_role: Mapped[str] = mapped_column(String(50))
    snapshot_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    
    # Timestamps
    promoted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="history")


class PortfolioTweet(Base):
    """Tweets used in portfolios."""
    
    __tablename__ = "portfolio_tweets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    
    tweet_url: Mapped[str] = mapped_column(String(500))
    tweet_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: likes, retweets, etc.
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="tweets")


class PortfolioVote(Base):
    """Parliament votes on portfolio submissions."""
    
    __tablename__ = "portfolio_votes"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    voter_discord_id: Mapped[str] = mapped_column(String(20), index=True)
    
    vote_type: Mapped[str] = mapped_column(String(10))  # approve, reject
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="votes")


class UserSavedTweet(Base):
    """User's saved tweets that persist across portfolio deletions."""
    
    __tablename__ = "user_saved_tweets"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[str] = mapped_column(String(20), index=True)
    
    tweet_url: Mapped[str] = mapped_column(String(500))
    tweet_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
