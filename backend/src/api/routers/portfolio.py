"""Portfolio API routes."""

import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from ..schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioSubmit,
    PortfolioReview,
    CanResubmitResponse,
    PortfolioHistoryResponse,
)
from ...models import get_db, User, Portfolio, PortfolioHistory, PortfolioTweet, PortfolioStatus, PortfolioVote
from ...services.twitter_service import get_twitter_service
import logging
import yaml
import re
from pathlib import Path

# Load roles config for guild role IDs
_config_path = Path(__file__).parent.parent.parent.parent.parent / "config" / "roles.yaml"
with open(_config_path) as f:
    ROLES_CONFIG = yaml.safe_load(f)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN")
REVIEW_CHANNEL_ID = os.getenv("REVIEW_CHANNEL_ID", "")
PARLIAMENT_CHANNEL_ID = os.getenv("PARLIAMENT_CHANNEL_ID", "")
RESUBMIT_COOLDOWN_DAYS = 7

# Log channel configuration on startup
logger.info(f"=== PORTFOLIO CHANNEL CONFIG ===")
logger.info(f"REVIEW_CHANNEL_ID: {REVIEW_CHANNEL_ID or 'NOT SET'}")
logger.info(f"PARLIAMENT_CHANNEL_ID: {PARLIAMENT_CHANNEL_ID or 'NOT SET'}")
logger.info(f"DISCORD_BOT_TOKEN: {'SET' if DISCORD_BOT_TOKEN else 'NOT SET'}")
logger.info(f"================================")


async def send_discord_embed(channel_id: str, embed: dict, components: list = None) -> Optional[str]:
    """Send embed message to Discord channel with optional voting buttons."""
    logger.info(f"📤 send_discord_embed called")
    logger.info(f"   Channel ID: {channel_id}")
    logger.info(f"   Bot Token: {'SET' if DISCORD_BOT_TOKEN else 'NOT SET'}")
    
    if not DISCORD_BOT_TOKEN:
        logger.error("❌ DISCORD_BOT_TOKEN is not set! Cannot send message.")
        return None
    if not channel_id:
        logger.error("❌ channel_id is empty! Cannot send message.")
        return None
    
    async with httpx.AsyncClient() as client:
        payload = {"embeds": [embed]}
        if components:
            payload["components"] = components
        
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        logger.info(f"   Sending to: {url}")
        
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30.0,
        )
        
        if response.status_code == 200:
            msg_id = response.json().get("id")
            logger.info(f"✅ Message sent successfully! Message ID: {msg_id}")
            return msg_id
        logger.error(f"❌ Discord API error: {response.status_code} - {response.text}")
        return None


@router.post("/create", response_model=PortfolioResponse)
async def create_portfolio(data: PortfolioCreate, db: AsyncSession = Depends(get_db)):
    """Create a new portfolio."""
    # Check if user exists, create if not
    result = await db.execute(select(User).where(User.discord_id == data.discord_id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            discord_id=data.discord_id,
            username=data.username,
            email=data.email,
        )
        db.add(user)
        await db.flush()
    
    # Check for existing draft portfolio
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.discord_id == data.discord_id,
            Portfolio.status.in_([PortfolioStatus.DRAFT.value, PortfolioStatus.SUBMITTED.value])
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active portfolio")
    
    portfolio = Portfolio(
        user_id=user.id,
        discord_id=data.discord_id,
        status=PortfolioStatus.DRAFT.value,
    )
    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio)
    
    return portfolio


@router.get("/list/all")
async def list_all_portfolios(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """List all portfolios for Lead review."""
    query = select(Portfolio).order_by(Portfolio.submitted_at.desc().nullsfirst())
    
    if status:
        query = query.where(Portfolio.status == status)
    
    result = await db.execute(query)
    portfolios = result.scalars().all()
    
    # Get user info for each portfolio
    portfolio_list = []
    for p in portfolios:
        user_result = await db.execute(select(User).where(User.id == p.user_id))
        user = user_result.scalar_one_or_none()
        
        portfolio_list.append({
            "id": p.id,
            "discord_id": p.discord_id,
            "username": user.username if user else "Unknown",
            "avatar_url": user.avatar_url if user else None,
            "status": p.status,
            "bio": p.bio,
            "twitter_handle": p.twitter_handle,
            "achievements": p.achievements,
            "target_role": p.target_role,
            "current_role": p.current_role,
            "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "tweets": [{"tweet_url": t.tweet_url, "tweet_id": t.tweet_id} for t in p.tweets],
        })
    
    return portfolio_list


@router.get("/{discord_id}", response_model=PortfolioResponse)
async def get_portfolio(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Get portfolio by Discord ID."""
    result = await db.execute(
        select(Portfolio).where(Portfolio.discord_id == discord_id).order_by(Portfolio.created_at.desc())
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return portfolio


@router.post("/save", response_model=PortfolioResponse)
async def save_portfolio(discord_id: str, data: PortfolioUpdate, db: AsyncSession = Depends(get_db)):
    """Save portfolio draft data. Also allows editing submitted and rejected portfolios."""
    # Find portfolio with draft, submitted, or rejected status (allow editing all)
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.discord_id == discord_id,
            Portfolio.status.in_([
                PortfolioStatus.DRAFT.value, 
                PortfolioStatus.SUBMITTED.value,
                PortfolioStatus.REJECTED.value
            ])
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="No editable portfolio found. Create one first.")
    
    # Reset to draft when editing
    portfolio.status = PortfolioStatus.DRAFT.value
    
    # Update fields
    if data.bio is not None:
        portfolio.bio = data.bio
    if data.twitter_handle is not None:
        portfolio.twitter_handle = data.twitter_handle
    if data.achievements is not None:
        portfolio.achievements = data.achievements
    if data.notion_url is not None:
        portfolio.notion_url = data.notion_url
    if data.target_role is not None:
        portfolio.target_role = data.target_role
    if data.other_works is not None:
        import json
        portfolio.other_works = json.dumps(data.other_works)
    
    # Handle tweets
    if data.tweets is not None:
        # Remove existing tweets
        for tweet in portfolio.tweets:
            await db.delete(tweet)
        
        # Add new tweets
        for tweet_data in data.tweets:
            tweet = PortfolioTweet(
                portfolio_id=portfolio.id,
                tweet_url=tweet_data.tweet_url,
                tweet_id=tweet_data.tweet_id,
                content=tweet_data.content,
            )
            db.add(tweet)
    
    portfolio.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(portfolio)
    
    return portfolio


@router.post("/submit", response_model=PortfolioResponse)
async def submit_portfolio(data: PortfolioSubmit, db: AsyncSession = Depends(get_db)):
    """Submit portfolio for review."""
    # Allow submitting draft, re-submitting submitted, or resubmitting rejected portfolio
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.discord_id == data.discord_id,
            Portfolio.status.in_([
                PortfolioStatus.DRAFT.value, 
                PortfolioStatus.SUBMITTED.value,
                PortfolioStatus.REJECTED.value
            ])
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="No portfolio found to submit")
    
    # Validate required fields - only twitter handle is required now
    if not portfolio.twitter_handle:
        raise HTTPException(status_code=400, detail="Twitter handle is required")
    
    portfolio.status = PortfolioStatus.SUBMITTED.value
    portfolio.submitted_at = datetime.utcnow()
    await db.commit()
    await db.refresh(portfolio)
    
    return portfolio


@router.post("/review")
async def review_portfolio(data: PortfolioReview, db: AsyncSession = Depends(get_db)):
    """Review a submitted portfolio and send to Parliament for voting if approved."""
    logger.info(f"")
    logger.info(f"{'='*50}")
    logger.info(f"🔍 PORTFOLIO REVIEW STARTED")
    logger.info(f"{'='*50}")
    logger.info(f"   Discord ID: {data.discord_id}")
    logger.info(f"   Reviewer: {data.reviewer_id}")
    logger.info(f"   Action: {data.action}")
    logger.info(f"   Feedback: {data.feedback}")
    
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.discord_id == data.discord_id,
            Portfolio.status == PortfolioStatus.SUBMITTED.value
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        logger.error(f"❌ No submitted portfolio found for {data.discord_id}")
        raise HTTPException(status_code=404, detail="No submitted portfolio found")
    
    logger.info(f"   Portfolio ID: {portfolio.id}")
    logger.info(f"   Current Status: {portfolio.status}")
    
    # Get user info
    user_result = await db.execute(select(User).where(User.id == portfolio.user_id))
    user = user_result.scalar_one_or_none()
    username = user.username if user else "Unknown"
    avatar_url = user.avatar_url if user else None
    logger.info(f"   Username: {username}")
    
    portfolio.reviewer_id = data.reviewer_id
    portfolio.reviewed_at = datetime.utcnow()
    
    discord_message_id = None
    
    if data.action == "approve":
        portfolio.status = PortfolioStatus.PENDING_VOTE.value
        portfolio.review_feedback = data.feedback
        
        # Get user's current guild role
        from src.models import GuildMember
        guild_result = await db.execute(
            select(GuildMember).where(GuildMember.discord_id == data.discord_id)
        )
        guild_member = guild_result.scalar_one_or_none()
        current_role_name = guild_member.role_type if guild_member else None
        current_tier = guild_member.tier if guild_member else 0
        
        # Format Twitter as clickable link
        twitter_value = f"[@{portfolio.twitter_handle}](https://twitter.com/{portfolio.twitter_handle})" if portfolio.twitter_handle else "N/A"
        
        # Get guild role ID for tagging
        target_guild = (portfolio.target_role or "").lower()
        guild_config = ROLES_CONFIG.get("roles", {}).get("guilds", {}).get(target_guild, {})
        guild_role_id = guild_config.get("role_id")
        
        # Format target guild as role mention or text
        if guild_role_id:
            target_guild_value = f"<@&{guild_role_id}>"
        else:
            target_guild_value = portfolio.target_role or "Unknown"
        
        # Calculate voting deadline (24h from now)
        voting_deadline = datetime.utcnow() + timedelta(hours=24)
        
        # Portfolio URL
        frontend_url = os.getenv("FRONTEND_URL", "https://liquid.community")
        portfolio_url = f"{frontend_url}/portfolios/{data.discord_id}"
        
        # Create Discord embed for Parliament voting - simple style
        embed = {
            "title": "voting",
            "description": f"<@{data.reviewer_id}> approved this portfolio for <@&1447972806339067925> voting.\n\n⏰ **deadline:** <t:{int(voting_deadline.timestamp())}:R>",
            "color": 0x00D4AA,
            "fields": [
                {"name": "user", "value": f"<@{data.discord_id}>", "inline": True},
                {"name": "target guild", "value": target_guild_value, "inline": True},
                {"name": "portfolio", "value": f"[view portfolio]({portfolio_url})", "inline": True},
            ],
            "footer": {"text": f"portfolio id: {portfolio.id} • voting ends in 24h or when all parliament members vote"},
            "timestamp": datetime.utcnow().isoformat(),
            "image": {"url": "https://files.catbox.moe/udvofw.png"},
        }
        
        # Store voting deadline in portfolio
        portfolio.voting_deadline = voting_deadline
        
        # Create voting buttons - show counts in labels, no text
        components = [
            {
                "type": 1,  # Action Row
                "components": [
                    {
                        "type": 2,  # Button
                        "style": 3,  # Green
                        "label": "0",
                        "emoji": {"name": "✅"},
                        "custom_id": f"portfolio_vote_approve_{data.discord_id}"
                    },
                    {
                        "type": 2,  # Button
                        "style": 4,  # Red
                        "label": "0",
                        "emoji": {"name": "❌"},
                        "custom_id": f"portfolio_vote_reject_{data.discord_id}"
                    },
                    {
                        "type": 2,  # Button
                        "style": 2,  # Grey
                        "emoji": {"name": "🗑️"},
                        "custom_id": f"portfolio_withdraw_{data.discord_id}"
                    }
                ]
            }
        ]
        
        # Send to Discord Parliament channel
        logger.info(f"")
        logger.info(f"🏛️ SENDING TO PARLIAMENT")
        logger.info(f"   PARLIAMENT_CHANNEL_ID: {PARLIAMENT_CHANNEL_ID or 'NOT SET!'}")
        
        if PARLIAMENT_CHANNEL_ID:
            discord_message_id = await send_discord_embed(PARLIAMENT_CHANNEL_ID, embed, components)
            if discord_message_id:
                logger.info(f"✅ SUCCESS! Sent to Parliament channel {PARLIAMENT_CHANNEL_ID}")
            else:
                logger.error(f"❌ FAILED to send to Parliament channel!")
        else:
            logger.error(f"❌ PARLIAMENT_CHANNEL_ID is not configured!")
        
    elif data.action == "reject":
        portfolio.status = PortfolioStatus.REJECTED.value
        portfolio.rejection_reason = data.feedback
    elif data.action == "request_changes":
        portfolio.status = PortfolioStatus.DRAFT.value
        portfolio.review_feedback = data.feedback
    
    await db.commit()
    
    return {
        "success": True, 
        "status": portfolio.status,
        "discord_message_id": discord_message_id,
    }


@router.delete("/{discord_id}")
async def delete_portfolio(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a portfolio and related records, but preserve tweets."""
    from sqlalchemy import delete
    from src.models import UserSavedTweet
    
    result = await db.execute(
        select(Portfolio).where(Portfolio.discord_id == discord_id)
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio_id = portfolio.id
    
    # Save tweets to UserSavedTweet before deletion (preserve them)
    if portfolio.tweets:
        # First remove old saved tweets for this user
        await db.execute(delete(UserSavedTweet).where(UserSavedTweet.discord_id == discord_id))
        
        # Save current tweets
        for tweet in portfolio.tweets:
            saved_tweet = UserSavedTweet(
                discord_id=discord_id,
                tweet_url=tweet.tweet_url,
                tweet_id=tweet.tweet_id,
            )
            db.add(saved_tweet)
    
    # Delete related history records first
    await db.execute(delete(PortfolioHistory).where(PortfolioHistory.portfolio_id == portfolio_id))
    
    # Delete related votes
    await db.execute(delete(PortfolioVote).where(PortfolioVote.portfolio_id == portfolio_id))
    
    # Delete related tweets (they're saved in UserSavedTweet now)
    await db.execute(delete(PortfolioTweet).where(PortfolioTweet.portfolio_id == portfolio_id))
    
    # Now delete the portfolio
    await db.execute(delete(Portfolio).where(Portfolio.id == portfolio_id))
    await db.commit()
    
    return {"success": True}


@router.get("/{discord_id}/can-resubmit", response_model=CanResubmitResponse)
async def can_resubmit(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Check if user can resubmit after rejection."""
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.discord_id == discord_id,
            Portfolio.status == PortfolioStatus.REJECTED.value
        ).order_by(Portfolio.reviewed_at.desc())
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio or not portfolio.reviewed_at:
        return CanResubmitResponse(can_resubmit=True)
    
    cooldown_ends = portfolio.reviewed_at + timedelta(days=RESUBMIT_COOLDOWN_DAYS)
    now = datetime.utcnow()
    
    if now >= cooldown_ends:
        return CanResubmitResponse(can_resubmit=True)
    
    days_remaining = (cooldown_ends - now).days + 1
    return CanResubmitResponse(
        can_resubmit=False,
        cooldown_ends=cooldown_ends,
        days_remaining=days_remaining,
    )


@router.get("/{discord_id}/history", response_model=list[PortfolioHistoryResponse])
async def get_history(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Get portfolio promotion history."""
    result = await db.execute(
        select(PortfolioHistory).where(
            PortfolioHistory.discord_id == discord_id
        ).order_by(PortfolioHistory.promoted_at.desc())
    )
    history = result.scalars().all()
    
    return history


@router.post("/vote")
async def vote_portfolio(
    discord_id: str,
    voter_discord_id: str,
    vote_type: str,
    db: AsyncSession = Depends(get_db)
):
    """Cast a vote on a portfolio. Returns current vote counts."""
    # Find portfolio
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.discord_id == discord_id,
            Portfolio.status == PortfolioStatus.PENDING_VOTE.value
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="No pending portfolio found")
    
    # Check if already voted
    existing_vote = await db.execute(
        select(PortfolioVote).where(
            PortfolioVote.portfolio_id == portfolio.id,
            PortfolioVote.voter_discord_id == voter_discord_id
        )
    )
    if existing_vote.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already voted on this portfolio")
    
    # Create vote
    vote = PortfolioVote(
        portfolio_id=portfolio.id,
        voter_discord_id=voter_discord_id,
        vote_type=vote_type,
    )
    db.add(vote)
    await db.commit()
    
    # Count votes
    approve_count = sum(1 for v in portfolio.votes if v.vote_type == "approve") + (1 if vote_type == "approve" else 0)
    reject_count = sum(1 for v in portfolio.votes if v.vote_type == "reject") + (1 if vote_type == "reject" else 0)
    
    return {
        "success": True,
        "approve_count": approve_count,
        "reject_count": reject_count,
        "total": approve_count + reject_count,
    }


@router.get("/vote-check/{discord_id}")
async def check_vote_status(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Check if voting should be finalized.
    
    Voting ends when:
    1. 24h deadline passed, OR
    2. All parliament members have voted
    
    Approved if majority (>50%) votes yes.
    """
    PARLIAMENT_ROLE_ID = ROLES_CONFIG.get("roles", {}).get("parliament", "1447972806339067925")
    
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.discord_id == discord_id,
            Portfolio.status == PortfolioStatus.PENDING_VOTE.value
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        return {"ready": False, "reason": "Portfolio not found"}
    
    approve_count = sum(1 for v in portfolio.votes if v.vote_type == "approve")
    reject_count = sum(1 for v in portfolio.votes if v.vote_type == "reject")
    total = approve_count + reject_count
    
    # Check if deadline passed (24h)
    deadline_passed = False
    if portfolio.voting_deadline and datetime.utcnow() >= portfolio.voting_deadline:
        deadline_passed = True
    
    # Get parliament member count from Discord
    parliament_count = 0
    all_voted = False
    if DISCORD_BOT_TOKEN:
        try:
            async with httpx.AsyncClient() as client:
                # Get guild members with parliament role
                guild_id = os.getenv("DISCORD_GUILD_ID", "1436216692299796563")
                response = await client.get(
                    f"https://discord.com/api/v10/guilds/{guild_id}/members?limit=1000",
                    headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
                    timeout=30.0,
                )
                if response.status_code == 200:
                    members = response.json()
                    parliament_members = [m for m in members if PARLIAMENT_ROLE_ID in m.get("roles", [])]
                    parliament_count = len(parliament_members)
                    all_voted = total >= parliament_count and parliament_count > 0
        except Exception as e:
            logger.warning(f"Failed to fetch parliament members: {e}")
    
    # Voting is ready if deadline passed OR all parliament members voted
    if deadline_passed or all_voted:
        # Majority wins (>50%)
        approval_rate = approve_count / total if total > 0 else 0
        approved = approve_count > reject_count  # Majority wins
        
        return {
            "ready": True,
            "approved": approved,
            "approve_count": approve_count,
            "reject_count": reject_count,
            "approval_rate": approval_rate,
            "reason": "deadline_passed" if deadline_passed else "all_voted",
            "parliament_count": parliament_count,
        }
    
    return {
        "ready": False,
        "approve_count": approve_count,
        "reject_count": reject_count,
        "total": total,
        "parliament_count": parliament_count,
        "deadline": portfolio.voting_deadline.isoformat() if portfolio.voting_deadline else None,
    }


@router.post("/finalize")
async def finalize_portfolio(discord_id: str, approved: bool, db: AsyncSession = Depends(get_db)):
    """Finalize portfolio after Parliament vote."""
    result = await db.execute(
        select(Portfolio).where(
            Portfolio.discord_id == discord_id,
            Portfolio.status == PortfolioStatus.PENDING_VOTE.value
        )
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="No pending portfolio found")
    
    # Get user for response
    user_result = await db.execute(select(User).where(User.id == portfolio.user_id))
    user = user_result.scalar_one_or_none()
    
    # Count votes for response
    approve_count = sum(1 for v in portfolio.votes if v.vote_type == "approve")
    reject_count = sum(1 for v in portfolio.votes if v.vote_type == "reject")
    
    if approved:
        portfolio.status = PortfolioStatus.PROMOTED.value
        
        # Create history entry
        history = PortfolioHistory(
            portfolio_id=portfolio.id,
            discord_id=discord_id,
            from_role=portfolio.current_role or "Droplet",
            to_role=portfolio.target_role or "Current",
        )
        db.add(history)
    else:
        portfolio.status = PortfolioStatus.REJECTED.value
        portfolio.reviewed_at = datetime.utcnow()  # For cooldown tracking
    
    await db.commit()
    
    return {
        "success": True,
        "status": portfolio.status,
        "discord_id": discord_id,
        "username": user.username if user else "Unknown",
        "to_role": portfolio.target_role,
        "approve_count": approve_count,
        "reject_count": reject_count,
    }
