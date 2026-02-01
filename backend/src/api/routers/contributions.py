"""Contributions API routes."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.contribution import (
    ContributionCreate,
    ContributionResponse,
    ContributionVoteRequest,
    ContributionVotesResponse,
    EligibilityResponse,
)
from ...models import get_db, User, Contribution, ContributionVote

router = APIRouter(prefix="/contributions", tags=["contributions"])

AUTO_APPROVE_THRESHOLD = 3  # Upvotes needed for auto-approval


@router.get("/eligibility/{discord_id}", response_model=EligibilityResponse)
async def check_eligibility(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Check if user can submit a contribution."""
    # Check for recent submissions (1 per day limit)
    yesterday = datetime.utcnow() - timedelta(days=1)
    result = await db.execute(
        select(Contribution).where(
            Contribution.discord_id == discord_id,
            Contribution.created_at > yesterday
        )
    )
    recent = result.scalars().all()
    
    if recent:
        oldest = min(c.created_at for c in recent)
        cooldown_ends = oldest + timedelta(days=1)
        return EligibilityResponse(
            eligible=False,
            reason="You can only submit one contribution per day",
            cooldown_ends=cooldown_ends,
        )
    
    return EligibilityResponse(eligible=True)


@router.post("/submit", response_model=ContributionResponse)
async def submit_contribution(data: ContributionCreate, db: AsyncSession = Depends(get_db)):
    """Submit a new contribution."""
    # Check eligibility
    eligibility = await check_eligibility(data.discord_id, db)
    if not eligibility.eligible:
        raise HTTPException(status_code=429, detail=eligibility.reason)
    
    # Get or create user
    result = await db.execute(select(User).where(User.discord_id == data.discord_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please use the bot first.")
    
    contribution = Contribution(
        user_id=user.id,
        discord_id=data.discord_id,
        title=data.title,
        description=data.description,
        content_url=data.content_url,
        category=data.category,
    )
    db.add(contribution)
    await db.commit()
    await db.refresh(contribution)
    
    return ContributionResponse(
        id=contribution.id,
        discord_id=contribution.discord_id,
        title=contribution.title,
        description=contribution.description,
        content_url=contribution.content_url,
        category=contribution.category,
        status=contribution.status,
        is_featured=contribution.is_featured,
        upvotes=contribution.upvotes,
        downvotes=contribution.downvotes,
        created_at=contribution.created_at,
        author_username=user.username,
    )


@router.post("/vote", response_model=ContributionVotesResponse)
async def vote_on_contribution(data: ContributionVoteRequest, db: AsyncSession = Depends(get_db)):
    """Vote on a contribution."""
    # Get contribution
    result = await db.execute(select(Contribution).where(Contribution.id == data.contribution_id))
    contribution = result.scalar_one_or_none()
    
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")
    
    # Can't vote on own contribution
    if contribution.discord_id == data.voter_discord_id:
        raise HTTPException(status_code=400, detail="Cannot vote on your own contribution")
    
    # Check for existing vote
    existing = await db.execute(
        select(ContributionVote).where(
            ContributionVote.contribution_id == data.contribution_id,
            ContributionVote.voter_discord_id == data.voter_discord_id
        )
    )
    existing_vote = existing.scalar_one_or_none()
    
    if existing_vote:
        if existing_vote.vote_type == data.vote_type:
            raise HTTPException(status_code=400, detail="Already voted")
        
        # Change vote
        old_type = existing_vote.vote_type
        existing_vote.vote_type = data.vote_type
        
        if old_type == "upvote":
            contribution.upvotes -= 1
        else:
            contribution.downvotes -= 1
    else:
        # New vote
        vote = ContributionVote(
            contribution_id=data.contribution_id,
            voter_discord_id=data.voter_discord_id,
            vote_type=data.vote_type,
        )
        db.add(vote)
    
    # Update counts
    if data.vote_type == "upvote":
        contribution.upvotes += 1
    else:
        contribution.downvotes += 1
    
    # Check for auto-approval
    if contribution.upvotes >= AUTO_APPROVE_THRESHOLD and contribution.status == "pending":
        contribution.status = "approved"
        contribution.approved_at = datetime.utcnow()
        
        # Award points to author
        user_result = await db.execute(select(User).where(User.discord_id == contribution.discord_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.contribution_points += 10
    
    await db.commit()
    
    return ContributionVotesResponse(
        contribution_id=contribution.id,
        upvotes=contribution.upvotes,
        downvotes=contribution.downvotes,
        net_votes=contribution.upvotes - contribution.downvotes,
    )


@router.get("/", response_model=list[ContributionResponse])
async def list_contributions(
    category: str = None,
    status: str = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List contributions."""
    query = select(Contribution).order_by(Contribution.created_at.desc())
    
    if category:
        query = query.where(Contribution.category == category)
    if status:
        query = query.where(Contribution.status == status)
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    contributions = result.scalars().all()
    
    # Get usernames
    response = []
    for c in contributions:
        user_result = await db.execute(select(User).where(User.discord_id == c.discord_id))
        user = user_result.scalar_one_or_none()
        
        response.append(ContributionResponse(
            id=c.id,
            discord_id=c.discord_id,
            title=c.title,
            description=c.description,
            content_url=c.content_url,
            category=c.category,
            status=c.status,
            is_featured=c.is_featured,
            upvotes=c.upvotes,
            downvotes=c.downvotes,
            created_at=c.created_at,
            approved_at=c.approved_at,
            author_username=user.username if user else "Unknown",
        ))
    
    return response


@router.get("/featured", response_model=list[ContributionResponse])
async def get_featured(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get featured contributions."""
    result = await db.execute(
        select(Contribution).where(Contribution.is_featured == True).order_by(Contribution.approved_at.desc()).limit(limit)
    )
    contributions = result.scalars().all()
    
    response = []
    for c in contributions:
        user_result = await db.execute(select(User).where(User.discord_id == c.discord_id))
        user = user_result.scalar_one_or_none()
        
        response.append(ContributionResponse(
            id=c.id,
            discord_id=c.discord_id,
            title=c.title,
            description=c.description,
            content_url=c.content_url,
            category=c.category,
            status=c.status,
            is_featured=c.is_featured,
            upvotes=c.upvotes,
            downvotes=c.downvotes,
            created_at=c.created_at,
            approved_at=c.approved_at,
            author_username=user.username if user else "Unknown",
        ))
    
    return response


@router.get("/user/{discord_id}", response_model=list[ContributionResponse])
async def get_user_contributions(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Get user's contributions."""
    result = await db.execute(
        select(Contribution).where(Contribution.discord_id == discord_id).order_by(Contribution.created_at.desc())
    )
    contributions = result.scalars().all()
    
    user_result = await db.execute(select(User).where(User.discord_id == discord_id))
    user = user_result.scalar_one_or_none()
    username = user.username if user else "Unknown"
    
    return [
        ContributionResponse(
            id=c.id,
            discord_id=c.discord_id,
            title=c.title,
            description=c.description,
            content_url=c.content_url,
            category=c.category,
            status=c.status,
            is_featured=c.is_featured,
            upvotes=c.upvotes,
            downvotes=c.downvotes,
            created_at=c.created_at,
            approved_at=c.approved_at,
            author_username=username,
        )
        for c in contributions
    ]


@router.get("/{contribution_id}/votes", response_model=ContributionVotesResponse)
async def get_contribution_votes(contribution_id: int, db: AsyncSession = Depends(get_db)):
    """Get vote counts for a contribution."""
    result = await db.execute(select(Contribution).where(Contribution.id == contribution_id))
    contribution = result.scalar_one_or_none()
    
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found")
    
    return ContributionVotesResponse(
        contribution_id=contribution.id,
        upvotes=contribution.upvotes,
        downvotes=contribution.downvotes,
        net_votes=contribution.upvotes - contribution.downvotes,
    )
