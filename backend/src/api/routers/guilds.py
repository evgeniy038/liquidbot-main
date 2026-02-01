"""Guilds and Quests API routes."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ...models import get_db, User, GuildMember, Quest, QuestSubmission

router = APIRouter(prefix="/guilds", tags=["guilds"])


class GuildJoinRequest(BaseModel):
    discord_id: str
    guild_name: str
    role_type: str


class GuildLeaveRequest(BaseModel):
    discord_id: str


class QuestCreateRequest(BaseModel):
    title: str
    description: str
    guild_name: str
    points: int = 10
    deadline: Optional[str] = None
    creator_discord_id: str


class QuestSubmitRequest(BaseModel):
    discord_id: str
    work_url: str
    description: Optional[str] = None


class SubmissionReviewRequest(BaseModel):
    reviewer_discord_id: str
    feedback: Optional[str] = None


@router.post("/join")
async def join_guild(data: GuildJoinRequest, db: AsyncSession = Depends(get_db)):
    """Join a guild."""
    # Check if already in a guild
    result = await db.execute(
        select(GuildMember).where(GuildMember.discord_id == data.discord_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="You're already in a guild. Leave first with /guild leave")
    
    member = GuildMember(
        discord_id=data.discord_id,
        guild_name=data.guild_name,
        role_type=data.role_type,
        tier=1,
        points=0,
        quests_completed=0,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    
    return {"success": True, "guild": data.guild_name, "role_type": data.role_type}


@router.post("/leave")
async def leave_guild(data: GuildLeaveRequest, db: AsyncSession = Depends(get_db)):
    """Leave current guild."""
    result = await db.execute(
        select(GuildMember).where(GuildMember.discord_id == data.discord_id)
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="You're not in a guild")
    
    await db.delete(member)
    await db.commit()
    
    return {"success": True}


@router.get("/member/{discord_id}")
async def get_member(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Get guild member info."""
    result = await db.execute(
        select(GuildMember).where(GuildMember.discord_id == discord_id)
    )
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=404, detail="Not in a guild")
    
    return {
        "discord_id": member.discord_id,
        "guild_name": member.guild_name,
        "role_type": member.role_type,
        "tier": member.tier,
        "points": member.points,
        "quests_completed": member.quests_completed,
        "joined_at": member.joined_at.isoformat(),
    }


@router.get("/leaderboard")
async def get_leaderboard(guild: str = None, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get guild leaderboard."""
    query = select(GuildMember).order_by(GuildMember.points.desc()).limit(limit)
    
    if guild:
        query = query.where(GuildMember.guild_name == guild)
    
    result = await db.execute(query)
    members = result.scalars().all()
    
    leaderboard = []
    for member in members:
        # Get username
        user_result = await db.execute(select(User).where(User.discord_id == member.discord_id))
        user = user_result.scalar_one_or_none()
        
        leaderboard.append({
            "discord_id": member.discord_id,
            "username": user.username if user else "Unknown",
            "guild_name": member.guild_name,
            "role_type": member.role_type,
            "tier": member.tier,
            "points": member.points,
            "quests_completed": member.quests_completed,
        })
    
    return leaderboard


# Quest routes
@router.post("/quests/create")
async def create_quest(data: QuestCreateRequest, db: AsyncSession = Depends(get_db)):
    """Create a new quest."""
    deadline = None
    if data.deadline:
        deadline = datetime.fromisoformat(data.deadline.replace("Z", "+00:00"))
    
    quest = Quest(
        title=data.title,
        description=data.description,
        guild_name=data.guild_name,
        points=data.points,
        deadline=deadline,
        creator_discord_id=data.creator_discord_id,
        is_active=True,
    )
    db.add(quest)
    await db.commit()
    await db.refresh(quest)
    
    return {
        "id": quest.id,
        "title": quest.title,
        "guild_name": quest.guild_name,
        "points": quest.points,
    }


@router.get("/quests")
async def list_quests(guild: str = None, active_only: bool = True, db: AsyncSession = Depends(get_db)):
    """List quests."""
    query = select(Quest).order_by(Quest.created_at.desc())
    
    if guild:
        query = query.where(Quest.guild_name == guild)
    if active_only:
        query = query.where(Quest.is_active == True)
    
    result = await db.execute(query)
    quests = result.scalars().all()
    
    return [
        {
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "guild_name": q.guild_name,
            "points": q.points,
            "deadline": q.deadline.isoformat() if q.deadline else None,
            "is_active": q.is_active,
            "created_at": q.created_at.isoformat(),
        }
        for q in quests
    ]


@router.post("/quests/{quest_id}/submit")
async def submit_quest(quest_id: int, data: QuestSubmitRequest, db: AsyncSession = Depends(get_db)):
    """Submit quest completion."""
    # Check quest exists
    quest_result = await db.execute(select(Quest).where(Quest.id == quest_id))
    quest = quest_result.scalar_one_or_none()
    
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    if not quest.is_active:
        raise HTTPException(status_code=400, detail="Quest is no longer active")
    
    # Check member is in the guild
    member_result = await db.execute(
        select(GuildMember).where(GuildMember.discord_id == data.discord_id)
    )
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(status_code=400, detail="You must be in a guild to submit quests")
    
    if member.guild_name != quest.guild_name:
        raise HTTPException(status_code=400, detail="This quest is for a different guild")
    
    # Check for existing submission
    existing = await db.execute(
        select(QuestSubmission).where(
            QuestSubmission.quest_id == quest_id,
            QuestSubmission.discord_id == data.discord_id,
            QuestSubmission.status == "pending"
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already have a pending submission for this quest")
    
    submission = QuestSubmission(
        quest_id=quest_id,
        member_id=member.id,
        discord_id=data.discord_id,
        work_url=data.work_url,
        description=data.description,
        status="pending",
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    
    return {"id": submission.id, "status": "pending"}


@router.get("/quests/submissions/pending")
async def get_pending_submissions(db: AsyncSession = Depends(get_db)):
    """Get pending quest submissions for review."""
    result = await db.execute(
        select(QuestSubmission).where(QuestSubmission.status == "pending").order_by(QuestSubmission.submitted_at.asc())
    )
    submissions = result.scalars().all()
    
    response = []
    for sub in submissions:
        quest_result = await db.execute(select(Quest).where(Quest.id == sub.quest_id))
        quest = quest_result.scalar_one_or_none()
        
        response.append({
            "id": sub.id,
            "quest_id": sub.quest_id,
            "quest_title": quest.title if quest else "Unknown",
            "discord_id": sub.discord_id,
            "work_url": sub.work_url,
            "description": sub.description,
            "submitted_at": sub.submitted_at.isoformat(),
        })
    
    return response


@router.post("/quests/submissions/{submission_id}/approve")
async def approve_submission(submission_id: int, data: SubmissionReviewRequest, db: AsyncSession = Depends(get_db)):
    """Approve a quest submission."""
    result = await db.execute(select(QuestSubmission).where(QuestSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="Submission already reviewed")
    
    # Get quest for points
    quest_result = await db.execute(select(Quest).where(Quest.id == submission.quest_id))
    quest = quest_result.scalar_one_or_none()
    points = quest.points if quest else 10
    
    # Update submission
    submission.status = "approved"
    submission.reviewer_discord_id = data.reviewer_discord_id
    submission.reviewed_at = datetime.utcnow()
    
    # Update member stats
    member_result = await db.execute(select(GuildMember).where(GuildMember.id == submission.member_id))
    member = member_result.scalar_one_or_none()
    
    if member:
        member.points += points
        member.quests_completed += 1
        member.last_active = datetime.utcnow()
    
    await db.commit()
    
    return {
        "success": True,
        "discord_id": submission.discord_id,
        "points": points,
    }


@router.post("/quests/submissions/{submission_id}/reject")
async def reject_submission(submission_id: int, data: SubmissionReviewRequest, db: AsyncSession = Depends(get_db)):
    """Reject a quest submission."""
    result = await db.execute(select(QuestSubmission).where(QuestSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if submission.status != "pending":
        raise HTTPException(status_code=400, detail="Submission already reviewed")
    
    submission.status = "rejected"
    submission.reviewer_discord_id = data.reviewer_discord_id
    submission.review_feedback = data.feedback
    submission.reviewed_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "success": True,
        "discord_id": submission.discord_id,
    }
