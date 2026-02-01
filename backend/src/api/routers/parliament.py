"""Parliament API routes for bot polling."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.nomination import NominationResponse, PendingNominationResponse, VoteRequest
from ...models import get_db, User, Nomination, Vote, Portfolio

router = APIRouter(prefix="/parliament", tags=["parliament"])

MIN_VOTES_REQUIRED = 5
APPROVAL_RATE_THRESHOLD = 0.6


@router.get("/pending", response_model=list[PendingNominationResponse])
async def get_pending_nominations(db: AsyncSession = Depends(get_db)):
    """Get pending nominations for Parliament voting (bot polls this)."""
    result = await db.execute(
        select(Nomination).where(
            Nomination.status == "pending",
            Nomination.is_processed == False
        ).order_by(Nomination.created_at.asc())
    )
    nominations = result.scalars().all()
    
    response = []
    for nom in nominations:
        user_result = await db.execute(select(User).where(User.discord_id == nom.discord_id))
        user = user_result.scalar_one_or_none()
        
        # Get portfolio URL if exists
        portfolio_url = None
        if nom.portfolio_id:
            portfolio_result = await db.execute(select(Portfolio).where(Portfolio.id == nom.portfolio_id))
            portfolio = portfolio_result.scalar_one_or_none()
            if portfolio:
                portfolio_url = portfolio.notion_url
        
        response.append(PendingNominationResponse(
            id=nom.id,
            discord_id=nom.discord_id,
            username=user.username if user else "Unknown",
            avatar_url=user.avatar_url if user else None,
            from_role=nom.from_role,
            to_role=nom.to_role,
            reason=nom.reason,
            portfolio_url=portfolio_url,
            created_at=nom.created_at,
        ))
    
    return response


@router.post("/processed/{nomination_id}")
async def mark_as_processed(nomination_id: int, message_id: str, channel_id: str, db: AsyncSession = Depends(get_db)):
    """Mark nomination as processed (bot has created the voting message)."""
    result = await db.execute(select(Nomination).where(Nomination.id == nomination_id))
    nomination = result.scalar_one_or_none()
    
    if not nomination:
        raise HTTPException(status_code=404, detail="Nomination not found")
    
    nomination.is_processed = True
    nomination.message_id = message_id
    nomination.channel_id = channel_id
    await db.commit()
    
    return {"success": True}


@router.post("/vote", response_model=NominationResponse)
async def vote_on_nomination(data: VoteRequest, db: AsyncSession = Depends(get_db)):
    """Record a vote on a nomination."""
    result = await db.execute(select(Nomination).where(Nomination.id == data.nomination_id))
    nomination = result.scalar_one_or_none()
    
    if not nomination:
        raise HTTPException(status_code=404, detail="Nomination not found")
    
    if nomination.status != "pending":
        raise HTTPException(status_code=400, detail="Nomination is no longer open for voting")
    
    # Check for existing vote
    existing = await db.execute(
        select(Vote).where(
            Vote.nomination_id == data.nomination_id,
            Vote.voter_discord_id == data.voter_discord_id
        )
    )
    existing_vote = existing.scalar_one_or_none()
    
    if existing_vote:
        if existing_vote.vote_type == data.vote_type:
            raise HTTPException(status_code=400, detail="Already voted")
        
        # Change vote
        old_type = existing_vote.vote_type
        existing_vote.vote_type = data.vote_type
        existing_vote.reason = data.reason
        
        if old_type == "approve":
            nomination.approve_count -= 1
        else:
            nomination.reject_count -= 1
    else:
        # New vote
        vote = Vote(
            nomination_id=data.nomination_id,
            voter_discord_id=data.voter_discord_id,
            vote_type=data.vote_type,
            reason=data.reason,
        )
        db.add(vote)
    
    # Update counts
    if data.vote_type == "approve":
        nomination.approve_count += 1
    else:
        nomination.reject_count += 1
    
    await db.commit()
    await db.refresh(nomination)
    
    # Get user info
    user_result = await db.execute(select(User).where(User.discord_id == nomination.discord_id))
    user = user_result.scalar_one_or_none()
    
    return NominationResponse(
        id=nomination.id,
        discord_id=nomination.discord_id,
        from_role=nomination.from_role,
        to_role=nomination.to_role,
        reason=nomination.reason,
        status=nomination.status,
        approve_count=nomination.approve_count,
        reject_count=nomination.reject_count,
        created_at=nomination.created_at,
        expires_at=nomination.expires_at,
        finalized_at=nomination.finalized_at,
        username=user.username if user else None,
        avatar_url=user.avatar_url if user else None,
    )


@router.get("/check/{nomination_id}")
async def check_vote_status(nomination_id: int, db: AsyncSession = Depends(get_db)):
    """Check if nomination should be finalized based on votes."""
    result = await db.execute(select(Nomination).where(Nomination.id == nomination_id))
    nomination = result.scalar_one_or_none()
    
    if not nomination:
        raise HTTPException(status_code=404, detail="Nomination not found")
    
    total_votes = nomination.approve_count + nomination.reject_count
    
    if total_votes < MIN_VOTES_REQUIRED:
        return {
            "ready": False,
            "reason": f"Need {MIN_VOTES_REQUIRED - total_votes} more votes",
            "approve_count": nomination.approve_count,
            "reject_count": nomination.reject_count,
            "total_votes": total_votes,
        }
    
    approval_rate = nomination.approve_count / total_votes if total_votes > 0 else 0
    
    return {
        "ready": True,
        "approved": approval_rate >= APPROVAL_RATE_THRESHOLD,
        "approval_rate": approval_rate,
        "approve_count": nomination.approve_count,
        "reject_count": nomination.reject_count,
        "total_votes": total_votes,
    }


@router.post("/finalize/{nomination_id}")
async def finalize_nomination(nomination_id: int, approved: bool, db: AsyncSession = Depends(get_db)):
    """Finalize a nomination after voting completes."""
    result = await db.execute(select(Nomination).where(Nomination.id == nomination_id))
    nomination = result.scalar_one_or_none()
    
    if not nomination:
        raise HTTPException(status_code=404, detail="Nomination not found")
    
    nomination.status = "approved" if approved else "rejected"
    nomination.finalized_at = datetime.utcnow()
    
    # Also update portfolio if linked
    if nomination.portfolio_id:
        from .portfolio import finalize_portfolio
        await finalize_portfolio(nomination.discord_id, approved, db)
    
    await db.commit()
    
    return {
        "success": True,
        "status": nomination.status,
        "discord_id": nomination.discord_id,
        "to_role": nomination.to_role if approved else None,
    }


@router.get("/{nomination_id}", response_model=NominationResponse)
async def get_nomination(nomination_id: int, db: AsyncSession = Depends(get_db)):
    """Get nomination details."""
    result = await db.execute(select(Nomination).where(Nomination.id == nomination_id))
    nomination = result.scalar_one_or_none()
    
    if not nomination:
        raise HTTPException(status_code=404, detail="Nomination not found")
    
    user_result = await db.execute(select(User).where(User.discord_id == nomination.discord_id))
    user = user_result.scalar_one_or_none()
    
    return NominationResponse(
        id=nomination.id,
        discord_id=nomination.discord_id,
        from_role=nomination.from_role,
        to_role=nomination.to_role,
        reason=nomination.reason,
        status=nomination.status,
        approve_count=nomination.approve_count,
        reject_count=nomination.reject_count,
        created_at=nomination.created_at,
        expires_at=nomination.expires_at,
        finalized_at=nomination.finalized_at,
        username=user.username if user else None,
        avatar_url=user.avatar_url if user else None,
    )
