"""FastAPI Backend for Liquid Discord Bot."""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load .env file before importing other modules
load_dotenv(Path(__file__).parent / ".env")

from src.models import init_db
from src.api import (
    portfolio_router,
    user_router,
    stats_router,
    contributions_router,
    parliament_router,
    guilds_router,
    auth_router,
    twitter_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Liquid API",
    description="Backend API for Liquid Discord Bot",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://tryliquid.xyz",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(portfolio_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(contributions_router, prefix="/api")
app.include_router(parliament_router, prefix="/api")
app.include_router(guilds_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(twitter_router, prefix="/api")

# Mount static files for images (serve from project root src/images)
images_path = Path(__file__).parent.parent / "src" / "images"
if images_path.exists():
    app.mount("/static/images", StaticFiles(directory=str(images_path)), name="images")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "liquid-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
