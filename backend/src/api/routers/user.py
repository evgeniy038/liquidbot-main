"""User API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.user import UserResponse, UserStats, UserDashboard, ServerStats, LeaderboardEntry
from ...models import get_db, User, Portfolio, GuildMember, Contribution, PortfolioHistory

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/{discord_id}/stats", response_model=UserStats)
async def get_user_stats(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Get user statistics."""
    result = await db.execute(select(User).where(User.discord_id == discord_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Count portfolios
    portfolio_count = await db.execute(
        select(func.count(Portfolio.id)).where(Portfolio.discord_id == discord_id)
    )
    portfolios_submitted = portfolio_count.scalar() or 0
    
    # Count contributions
    contribution_count = await db.execute(
        select(func.count(Contribution.id)).where(Contribution.discord_id == discord_id)
    )
    contributions_made = contribution_count.scalar() or 0
    
    # Get guild info
    guild_result = await db.execute(
        select(GuildMember).where(GuildMember.discord_id == discord_id)
    )
    guild_member = guild_result.scalar_one_or_none()
    
    return UserStats(
        discord_id=user.discord_id,
        username=user.username,
        message_count=user.message_count,
        contribution_points=user.contribution_points,
        portfolios_submitted=portfolios_submitted,
        quests_completed=guild_member.quests_completed if guild_member else 0,
        contributions_made=contributions_made,
        guild=guild_member.guild_name if guild_member else None,
        guild_tier=guild_member.tier if guild_member else None,
    )


@router.get("/{discord_id}/tweets")
async def get_user_tweets(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Get user's shared tweets from portfolios or saved tweets."""
    from src.models import UserSavedTweet
    
    result = await db.execute(
        select(Portfolio).where(Portfolio.discord_id == discord_id).order_by(Portfolio.created_at.desc())
    )
    portfolio = result.scalar_one_or_none()
    
    # If portfolio exists with tweets, return those
    if portfolio and portfolio.tweets:
        return [
            {
                "tweet_url": t.tweet_url,
                "content": t.content,
                "tweet_id": t.tweet_id,
            }
            for t in portfolio.tweets
        ]
    
    # Otherwise, return saved tweets (persisted across portfolio deletions)
    saved_result = await db.execute(
        select(UserSavedTweet).where(UserSavedTweet.discord_id == discord_id)
    )
    saved_tweets = saved_result.scalars().all()
    
    return [
        {
            "tweet_url": t.tweet_url,
            "content": None,
            "tweet_id": t.tweet_id,
        }
        for t in saved_tweets
    ]


@router.get("/{discord_id}/dashboard", response_model=UserDashboard)
async def get_user_dashboard(discord_id: str, db: AsyncSession = Depends(get_db)):
    """Get comprehensive dashboard data."""
    # Get user
    result = await db.execute(select(User).where(User.discord_id == discord_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get stats
    stats = await get_user_stats(discord_id, db)
    
    # Get portfolio
    portfolio_result = await db.execute(
        select(Portfolio).where(Portfolio.discord_id == discord_id).order_by(Portfolio.created_at.desc())
    )
    portfolio = portfolio_result.scalar_one_or_none()
    
    # Get recent contributions
    contributions_result = await db.execute(
        select(Contribution).where(Contribution.discord_id == discord_id).order_by(Contribution.created_at.desc()).limit(5)
    )
    recent_contributions = [
        {
            "id": c.id,
            "title": c.title,
            "category": c.category,
            "upvotes": c.upvotes,
            "created_at": c.created_at.isoformat(),
        }
        for c in contributions_result.scalars().all()
    ]
    
    # Get tweets
    tweets = await get_user_tweets(discord_id, db)
    
    # Get guild info
    guild_result = await db.execute(
        select(GuildMember).where(GuildMember.discord_id == discord_id)
    )
    guild_member = guild_result.scalar_one_or_none()
    
    guild_info = None
    if guild_member:
        guild_info = {
            "name": guild_member.guild_name,
            "role_type": guild_member.role_type,
            "tier": guild_member.tier,
            "points": guild_member.points,
            "quests_completed": guild_member.quests_completed,
        }
    
    # Get promotion history
    history_result = await db.execute(
        select(PortfolioHistory).where(PortfolioHistory.discord_id == discord_id).order_by(PortfolioHistory.promoted_at.desc())
    )
    promotion_history = [
        {
            "from_role": h.from_role,
            "to_role": h.to_role,
            "promoted_at": h.promoted_at.isoformat(),
        }
        for h in history_result.scalars().all()
    ]
    
    return UserDashboard(
        user=UserResponse(
            discord_id=user.discord_id,
            username=user.username,
            avatar_url=user.avatar_url,
            message_count=user.message_count,
            contribution_points=user.contribution_points,
            created_at=user.created_at,
        ),
        stats=stats,
        portfolio_status=portfolio.status if portfolio else None,
        recent_contributions=recent_contributions,
        recent_tweets=tweets,
        guild_info=guild_info,
        promotion_history=promotion_history,
    )


@router.get("/server/stats", response_model=ServerStats)
async def get_server_stats(db: AsyncSession = Depends(get_db)):
    """Get server statistics."""
    total_users = await db.execute(select(func.count(User.id)))
    total_portfolios = await db.execute(select(func.count(Portfolio.id)))
    pending_portfolios = await db.execute(
        select(func.count(Portfolio.id)).where(Portfolio.status == "submitted")
    )
    approved_portfolios = await db.execute(
        select(func.count(Portfolio.id)).where(Portfolio.status == "promoted")
    )
    total_contributions = await db.execute(select(func.count(Contribution.id)))
    
    from ...models import Quest
    active_quests = await db.execute(
        select(func.count(Quest.id)).where(Quest.is_active == True)
    )
    
    return ServerStats(
        total_users=total_users.scalar() or 0,
        total_portfolios=total_portfolios.scalar() or 0,
        pending_portfolios=pending_portfolios.scalar() or 0,
        approved_portfolios=approved_portfolios.scalar() or 0,
        total_contributions=total_contributions.scalar() or 0,
        active_quests=active_quests.scalar() or 0,
    )


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get top users by contribution points."""
    result = await db.execute(
        select(User).order_by(User.contribution_points.desc()).limit(limit)
    )
    users = result.scalars().all()
    
    # Count contributions per user
    leaderboard = []
    for i, user in enumerate(users, 1):
        contrib_count = await db.execute(
            select(func.count(Contribution.id)).where(Contribution.discord_id == user.discord_id)
        )
        leaderboard.append(LeaderboardEntry(
            rank=i,
            discord_id=user.discord_id,
            username=user.username,
            avatar_url=user.avatar_url,
            points=user.contribution_points,
            contributions=contrib_count.scalar() or 0,
        ))
    
    return leaderboard


@router.get("/{discord_id}/discord-stats")
async def get_discord_activity_stats(discord_id: str):
    """Get real Discord activity stats from messages.db."""
    from ...repositories.messages_db import get_messages_repository
    
    messages_repo = get_messages_repository()
    stats = messages_repo.get_user_stats(int(discord_id))
    
    return {
        "message_count": stats.get("message_count", 0),
        "channels_active": stats.get("channels_active", 0),
    }
