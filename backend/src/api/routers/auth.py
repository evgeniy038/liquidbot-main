"""Discord OAuth2 authentication routes."""

import os
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, Response, Request
from fastapi.responses import RedirectResponse
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import get_db, User

router = APIRouter(prefix="/auth", tags=["auth"])

# Discord OAuth2 configuration
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7

DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_OAUTH_URL = "https://discord.com/api/oauth2"
GUILD_ID = os.getenv("DISCORD_GUILD_ID", "1436216692299796563")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserInfo(BaseModel):
    id: str
    username: str
    discriminator: str
    avatar: Optional[str]
    global_name: Optional[str]


def create_jwt_token(user_data: dict) -> str:
    """Create a JWT token for the user."""
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    to_encode = {
        "sub": user_data["id"],
        "username": user_data.get("global_name") or user_data["username"],
        "avatar": user_data.get("avatar"),
        "exp": expire,
    }
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.JWTError:
        return None


@router.get("/login")
async def discord_login():
    """Redirect to Discord OAuth2 authorization page."""
    if not DISCORD_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Discord OAuth not configured")
    
    scopes = "identify guilds"
    oauth_url = (
        f"{DISCORD_OAUTH_URL}/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={scopes}"
    )
    return RedirectResponse(url=oauth_url)


@router.get("/callback")
async def discord_callback(code: str = Query(...)):
    """Handle Discord OAuth2 callback."""
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Discord OAuth not configured")
    
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            f"{DISCORD_OAUTH_URL}/token",
            data={
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        token_data = token_response.json()
        access_token = token_data["access_token"]
        
        # Get user info from Discord
        user_response = await client.get(
            f"{DISCORD_API_BASE}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_data = user_response.json()
    
    # Create JWT token
    jwt_token = create_jwt_token(user_data)
    
    # Redirect to frontend with token
    redirect_url = f"{FRONTEND_URL}/auth/callback?token={jwt_token}"
    return RedirectResponse(url=redirect_url)


@router.get("/me")
async def get_current_user(request: Request):
    """Get current user from JWT token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    payload = verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Build avatar URL
    avatar_url = None
    if payload.get("avatar"):
        avatar_url = f"https://cdn.discordapp.com/avatars/{payload['sub']}/{payload['avatar']}.png"
    
    # Fetch user roles from Discord guild
    roles = []
    bot_token = os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD_BOT_TOKEN")
    if bot_token and GUILD_ID:
        try:
            async with httpx.AsyncClient() as client:
                member_response = await client.get(
                    f"{DISCORD_API_BASE}/guilds/{GUILD_ID}/members/{payload['sub']}",
                    headers={"Authorization": f"Bot {bot_token}"},
                )
                if member_response.status_code == 200:
                    member_data = member_response.json()
                    roles = member_data.get("roles", [])
        except Exception as e:
            print(f"Failed to fetch member roles: {e}")
    
    return {
        "id": payload["sub"],
        "username": payload["username"],
        "avatar_url": avatar_url,
        "roles": roles,
    }


@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)."""
    return {"message": "Logged out successfully"}
