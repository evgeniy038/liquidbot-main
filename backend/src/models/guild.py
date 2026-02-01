"""Guild and Quest models."""

from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class GuildMember(Base):
    """Guild membership tracking."""
    
    __tablename__ = "guild_members"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[str] = mapped_column(String(20), index=True)
    
    # Guild info
    guild_name: Mapped[str] = mapped_column(String(50))  # traders, content, designers
    role_type: Mapped[str] = mapped_column(String(50))  # e.g., educator, creator, helper, artist
    tier: Mapped[int] = mapped_column(Integer, default=1)
    
    # Stats
    points: Mapped[int] = mapped_column(Integer, default=0)
    quests_completed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quest_submissions = relationship("QuestSubmission", back_populates="member", lazy="selectin")


class Quest(Base):
    """Guild quests/tasks."""
    
    __tablename__ = "quests"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Quest details
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    guild_name: Mapped[str] = mapped_column(String(50))
    
    # Rewards
    points: Mapped[int] = mapped_column(Integer, default=10)
    max_completions: Mapped[int | None] = mapped_column(Integer, nullable=True)  # null = unlimited
    
    # Creator
    creator_discord_id: Mapped[str] = mapped_column(String(20))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    submissions = relationship("QuestSubmission", back_populates="quest", lazy="selectin")


class QuestSubmission(Base):
    """Quest completion submissions."""
    
    __tablename__ = "quest_submissions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    quest_id: Mapped[int] = mapped_column(ForeignKey("quests.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("guild_members.id"))
    discord_id: Mapped[str] = mapped_column(String(20), index=True)
    
    # Submission
    work_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Review
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected
    reviewer_discord_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    review_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    quest = relationship("Quest", back_populates="submissions")
    member = relationship("GuildMember", back_populates="quest_submissions")
