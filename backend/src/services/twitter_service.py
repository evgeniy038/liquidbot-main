"""Twitter/X integration service using twitterapi.io"""

import os
import aiohttp
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TweetData:
    """Parsed tweet data"""
    tweet_id: str
    url: str
    author_username: str
    text: str
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    quotes: int = 0
    views: int = 0
    bookmarks: int = 0
    engagement_rate: float = 0.0
    media_urls: List[str] = field(default_factory=list)
    created_at: str = None
    author_followers: int = 0
    is_blue_verified: bool = False
    
    def __post_init__(self):
        if self.views > 0:
            self.engagement_rate = round(
                (self.likes + self.retweets + self.replies + self.quotes) / self.views * 100, 2
            )


@dataclass 
class UserProfile:
    """Twitter user profile data"""
    user_id: str
    username: str
    name: str
    followers: int = 0
    following: int = 0
    tweet_count: int = 0
    description: str = ""
    profile_picture: str = ""
    banner_url: str = ""
    is_blue_verified: bool = False
    created_at: str = None


class TwitterService:
    """Service for Twitter/X data extraction using twitterapi.io"""
    
    BASE_URL = "https://api.twitterapi.io/twitter"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TWITTER_API_KEY") or os.getenv("TWITTERAPI_KEY")
        self.headers = {}
        
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
    
    def _parse_tweet_response(self, tweet_data: dict) -> TweetData:
        """Parse raw tweet response into TweetData object."""
        author = tweet_data.get("author", {})
        
        media_urls = []
        if tweet_data.get("media"):
            for m in tweet_data["media"]:
                if m.get("url"):
                    media_urls.append(m["url"])
                elif m.get("media_url_https"):
                    media_urls.append(m["media_url_https"])
        
        return TweetData(
            tweet_id=tweet_data.get("id", ""),
            url=tweet_data.get("url", ""),
            author_username=author.get("userName", ""),
            text=tweet_data.get("text", ""),
            likes=tweet_data.get("likeCount", 0),
            retweets=tweet_data.get("retweetCount", 0),
            replies=tweet_data.get("replyCount", 0),
            quotes=tweet_data.get("quoteCount", 0),
            views=tweet_data.get("viewCount", 0),
            bookmarks=tweet_data.get("bookmarkCount", 0),
            media_urls=media_urls,
            created_at=tweet_data.get("createdAt"),
            author_followers=author.get("followers", 0),
            is_blue_verified=author.get("isBlueVerified", False),
        )
    
    async def fetch_tweet_data(self, tweet_id: str) -> Optional[TweetData]:
        """Fetch data for a single tweet."""
        if not self.api_key:
            return None
            
        url = f"{self.BASE_URL}/tweets"
        params = {"tweet_ids": tweet_id}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "success" and data.get("tweets"):
                            return self._parse_tweet_response(data["tweets"][0])
        except Exception as e:
            print(f"Error fetching tweet {tweet_id}: {e}")
        
        return None
    
    async def fetch_tweets_batch(self, tweet_ids: List[str]) -> List[TweetData]:
        """Fetch data for multiple tweets at once."""
        if not self.api_key or not tweet_ids:
            return []
            
        url = f"{self.BASE_URL}/tweets"
        params = {"tweet_ids": ",".join(tweet_ids)}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "success":
                            return [self._parse_tweet_response(t) for t in data.get("tweets", [])]
        except Exception as e:
            print(f"Error fetching tweets batch: {e}")
        
        return []
    
    async def fetch_user_profile(self, username: str) -> Optional[UserProfile]:
        """Fetch Twitter user profile."""
        if not self.api_key:
            return None
            
        username = username.lstrip("@")
        
        url = f"{self.BASE_URL}/user/info"
        params = {"userName": username}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "success" and data.get("data"):
                            user = data["data"]
                            return UserProfile(
                                user_id=user.get("id", ""),
                                username=user.get("userName", username),
                                name=user.get("name", ""),
                                followers=user.get("followers", 0),
                                following=user.get("following", 0),
                                tweet_count=user.get("statusesCount", 0),
                                description=user.get("description", ""),
                                profile_picture=user.get("profilePicture", ""),
                                banner_url=user.get("coverPicture", ""),
                                is_blue_verified=user.get("isBlueVerified", False),
                                created_at=user.get("createdAt"),
                            )
        except Exception as e:
            print(f"Error fetching user profile {username}: {e}")
        
        return None
    
    async def get_user_tweets(self, username: str, limit: int = 20) -> List[TweetData]:
        """Get user's recent tweets."""
        if not self.api_key:
            return []
            
        url = f"{self.BASE_URL}/user/last_tweets"
        params = {"userName": username, "limit": min(limit, 100)}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "success":
                            tweets = data.get("data", {}).get("tweets", [])
                            return [self._parse_tweet_response(t) for t in tweets]
        except Exception as e:
            print(f"Error fetching user tweets for {username}: {e}")
        
        return []
    
    def calculate_total_stats(self, tweets: List[TweetData]) -> Dict[str, Any]:
        """Calculate total engagement stats from a list of tweets."""
        if not tweets:
            return {
                "total_tweets": 0,
                "total_likes": 0,
                "total_retweets": 0,
                "total_views": 0,
                "total_replies": 0,
                "avg_likes": 0,
                "avg_views": 0,
                "avg_engagement_rate": 0,
                "overall_engagement_rate": 0,
            }
        
        total_likes = sum(t.likes for t in tweets)
        total_retweets = sum(t.retweets for t in tweets)
        total_views = sum(t.views for t in tweets)
        total_replies = sum(t.replies for t in tweets)
        
        count = len(tweets)
        
        overall_er = 0
        if total_views > 0:
            overall_er = round(
                (total_likes + total_retweets + total_replies) / total_views * 100, 2
            )
        
        return {
            "total_tweets": count,
            "total_likes": total_likes,
            "total_retweets": total_retweets,
            "total_views": total_views,
            "total_replies": total_replies,
            "avg_likes": round(total_likes / count, 1) if count > 0 else 0,
            "avg_views": round(total_views / count, 1) if count > 0 else 0,
            "avg_engagement_rate": round(sum(t.engagement_rate for t in tweets) / count, 2) if count > 0 else 0,
            "overall_engagement_rate": overall_er,
        }
    
    def to_dict(self, tweet: TweetData) -> Dict[str, Any]:
        """Convert TweetData to dictionary."""
        return {
            "tweet_id": tweet.tweet_id,
            "url": tweet.url,
            "author_username": tweet.author_username,
            "text": tweet.text,
            "likes": tweet.likes,
            "retweets": tweet.retweets,
            "replies": tweet.replies,
            "quotes": tweet.quotes,
            "views": tweet.views,
            "bookmarks": tweet.bookmarks,
            "engagement_rate": tweet.engagement_rate,
            "media_urls": tweet.media_urls,
            "created_at": tweet.created_at,
            "author_followers": tweet.author_followers,
            "is_blue_verified": tweet.is_blue_verified,
        }
    
    def profile_to_dict(self, profile: UserProfile) -> Dict[str, Any]:
        """Convert UserProfile to dictionary."""
        return {
            "user_id": profile.user_id,
            "username": profile.username,
            "name": profile.name,
            "followers": profile.followers,
            "following": profile.following,
            "tweet_count": profile.tweet_count,
            "description": profile.description,
            "profile_picture": profile.profile_picture,
            "banner_url": profile.banner_url,
            "is_blue_verified": profile.is_blue_verified,
            "created_at": profile.created_at,
        }


# Singleton instance
_twitter_service: Optional[TwitterService] = None


def get_twitter_service() -> TwitterService:
    """Get or create TwitterService instance."""
    global _twitter_service
    if _twitter_service is None:
        _twitter_service = TwitterService()
    return _twitter_service
