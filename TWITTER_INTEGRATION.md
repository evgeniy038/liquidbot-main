# Twitter Integration - Complete Documentation

## Overview

The project uses Twitter/X integration in two ways:

1. **Frontend:** `react-tweet` library for embedding tweets in UI
2. **Backend:** `twitterapi.io` API for fetching tweet stats and user profiles

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           TWITTER INTEGRATION                                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Discord Bot   │────────▶│   messages.db   │◀────────│   Backend API   │
│  Collects URLs  │         │  Stores tweets  │         │  Reads tweets   │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                    │
                                    ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  twitterapi.io  │◀────────│ TwitterService  │────────▶│  Tweet Stats    │
│   External API  │         │   (Backend)     │         │  User Profiles  │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                    │
                                    ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Next.js API   │◀────────│   Dashboard     │────────▶│   react-tweet   │
│   Routes        │         │   Data          │         │   UI Embeds     │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

---

## Part 1: Tweet Collection (Discord → Database)

### How Tweets Are Collected

The Discord bot monitors a specific "Twitter channel" where users post their tweet URLs.

**Channel ID:** Defined in environment as `TWITTER_CHANNEL_ID`

When users post messages containing `x.com/*/status/*` or `twitter.com/*/status/*` URLs, these are stored in `messages.db`.

### Database Query

**File:** `backend/src/repositories/messages_db.py`

```python
TWITTER_CHANNEL_ID = os.getenv("TWITTER_CHANNEL_ID", "1267829631430938765")

def get_user_tweets(self, user_id: int) -> list[str]:
    """Get tweet IDs posted by user in Twitter channel."""
    cursor.execute("""
        SELECT content FROM messages 
        WHERE author_id = ? AND channel_id = ?
    """, (str(user_id), TWITTER_CHANNEL_ID))
    
    tweet_ids = []
    for (content,) in cursor.fetchall():
        # Extract tweet IDs from URLs
        patterns = [
            r'x\.com/\w+/status/(\d+)',
            r'twitter\.com/\w+/status/(\d+)'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, content)
            tweet_ids.extend(matches)
    
    return list(set(tweet_ids))  # Remove duplicates
```

### Get Full URLs with Username Detection

```python
def get_user_tweet_urls(self, user_id: int) -> tuple[list[str], str | None]:
    """Get full tweet URLs and detect Twitter username from user's posts."""
    
    tweet_urls = []
    detected_username = None
    
    for (content,) in cursor.fetchall():
        pattern = r'(https?://(?:x|twitter)\.com/(\w+)/status/(\d+))'
        matches = re.findall(pattern, content)
        
        for full_url, username, tweet_id in matches:
            # Normalize to x.com
            normalized_url = f"https://x.com/{username}/status/{tweet_id}"
            tweet_urls.append(normalized_url)
            
            # Detect username (skip 'i', 'intent', 'share')
            if username.lower() not in ['i', 'intent', 'share']:
                detected_username = username
    
    return list(set(tweet_urls)), detected_username
```

---

## Part 2: Twitter API Service (twitterapi.io)

### Service Configuration

**File:** `backend/src/services/twitter_service.py`

```python
class TwitterService:
    """Service for Twitter/X data extraction using twitterapi.io"""
    
    BASE_URL = "https://api.twitterapi.io/twitter"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers["X-API-Key"] = api_key
```

### Environment Variable

```env
TWITTER_API_KEY=your_twitterapi_io_key
```

### Data Classes

```python
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
    is_blue_verified: bool = False
    created_at: str = None
```

---

## Part 3: API Endpoints

### Fetch Single Tweet

```python
async def fetch_tweet_data(self, tweet_id: str) -> Optional[TweetData]:
    url = f"{self.BASE_URL}/tweets"
    params = {"tweet_ids": tweet_id}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=self.headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "success" and data.get("tweets"):
                    return self._parse_tweet_response(data["tweets"][0])
```

**twitterapi.io Response:**
```json
{
  "status": "success",
  "tweets": [{
    "id": "1234567890",
    "url": "https://x.com/user/status/1234567890",
    "text": "Tweet content...",
    "likeCount": 100,
    "retweetCount": 25,
    "replyCount": 10,
    "quoteCount": 5,
    "viewCount": 5000,
    "bookmarkCount": 15,
    "createdAt": "2024-01-15T12:00:00Z",
    "author": {
      "userName": "username",
      "followers": 10000,
      "isBlueVerified": true
    }
  }]
}
```

### Fetch Multiple Tweets (Batch)

```python
async def fetch_tweets_batch(self, tweet_ids: List[str]) -> List[TweetData]:
    url = f"{self.BASE_URL}/tweets"
    params = {"tweet_ids": ",".join(tweet_ids)}  # Comma-separated
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=self.headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "success":
                    return [self._parse_tweet_response(t) for t in data.get("tweets", [])]
```

### Fetch User Profile

```python
async def fetch_user_profile(self, username: str) -> Optional[UserProfile]:
    username = username.lstrip("@")
    
    url = f"{self.BASE_URL}/user/info"
    params = {"userName": username}
    
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
                        is_blue_verified=user.get("isBlueVerified", False)
                    )
```

### Get User's Recent Tweets

```python
async def get_user_tweets(self, username: str, limit: int = 20) -> List[TweetData]:
    url = f"{self.BASE_URL}/user/last_tweets"
    params = {"userName": username, "limit": min(limit, 100)}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=self.headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "success":
                    tweets = data.get("data", {}).get("tweets", [])
                    return [self._parse_tweet_response(t) for t in tweets]
```

---

## Part 4: Stats Calculation

### Calculate Total Stats

```python
def calculate_total_stats(self, tweets: List[TweetData]) -> Dict[str, Any]:
    total_likes = sum(t.likes for t in tweets)
    total_retweets = sum(t.retweets for t in tweets)
    total_views = sum(t.views for t in tweets)
    total_replies = sum(t.replies for t in tweets)
    
    count = len(tweets)
    
    # Overall engagement rate
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
        "avg_likes": round(total_likes / count, 1),
        "avg_views": round(total_views / count, 1),
        "avg_engagement_rate": round(sum(t.engagement_rate for t in tweets) / count, 2),
        "overall_engagement_rate": overall_er
    }
```

---

## Part 5: Backend API Routes

### Twitter Router

**File:** `backend/src/api/routers/twitter.py`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/twitter/profile/{username}` | Get Twitter profile |
| GET | `/api/twitter/stats/{discord_id}` | Get engagement stats for user |

### Profile Endpoint

```python
@router.get("/profile/{username}")
async def get_twitter_profile(username: str, twitter_service):
    profile = await twitter_service.fetch_user_profile(username)
    
    return {
        "username": profile.username,
        "name": profile.name,
        "followers": profile.followers,
        "tweet_count": profile.tweet_count,
        "profile_picture": profile.profile_picture,
        "is_verified": profile.is_blue_verified
    }
```

### Stats Endpoint

```python
@router.get("/stats/{discord_id}")
async def get_twitter_stats(discord_id: str, twitter_service, messages_repo):
    # 1. Get tweet IDs from Discord messages
    tweet_ids = messages_repo.get_user_tweets(int(discord_id))
    
    # 2. Fetch tweet data (limit to 20)
    tweets_data = await twitter_service.fetch_tweets_batch(tweet_ids[:20])
    
    # 3. Calculate stats
    stats = twitter_service.calculate_total_stats(tweets_data)
    
    return {
        "total_likes": stats.get("total_likes", 0),
        "total_retweets": stats.get("total_retweets", 0),
        "total_replies": stats.get("total_replies", 0),
        "total_views": stats.get("total_views", 0),
        "tweet_count": len(tweet_ids)
    }
```

---

## Part 6: Frontend Tweet Embedding

### Library: react-tweet

**Package:** `react-tweet` (npm)

**Install:**
```bash
npm install react-tweet
```

### Basic Usage

**File:** `web/src/app/contributions/page.tsx`

```tsx
import { Tweet } from 'react-tweet';
import { Suspense } from 'react';

// Tweet wrapper with loading skeleton
function TweetCard({ tweetId }: { tweetId: string }) {
  return (
    <div className="tweet-wrapper">
      <Suspense fallback={<TweetSkeleton />}>
        <Tweet id={tweetId} />
      </Suspense>
    </div>
  );
}

// Loading skeleton
function TweetSkeleton() {
  return (
    <div className="tweet-skeleton">
      <div className="skeleton-header">
        <div className="skeleton-avatar"></div>
        <div className="skeleton-name"></div>
      </div>
      <div className="skeleton-text"></div>
      <div className="skeleton-text short"></div>
    </div>
  );
}

// Usage in component
export default function ContributionsPage() {
  const [tweetIds, setTweetIds] = useState<string[]>([]);
  
  return (
    <div className="tweets-grid">
      {tweetIds.map((tweetId) => (
        <TweetCard key={tweetId} tweetId={tweetId} />
      ))}
    </div>
  );
}
```

### Extract Tweet ID from URL

```typescript
function extractTweetId(url: string): string | null {
  const patterns = [
    /twitter\.com\/\w+\/status\/(\d+)/,
    /x\.com\/\w+\/status\/(\d+)/,
    /x\.com\/i\/status\/(\d+)/,
  ];
  
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
}

// Example
extractTweetId("https://x.com/user/status/1234567890")  // "1234567890"
extractTweetId("https://twitter.com/user/status/9876")  // "9876"
```

### CSS Styling

**File:** `web/src/app/globals.css`

```css
/* Tweet container styling */
.tweet-wrapper {
  width: 100%;
  max-width: 550px;
}

/* Override react-tweet default styles */
[data-theme="light"] .react-tweet-theme {
  --tweet-bg-color: #ffffff;
  --tweet-border-color: rgba(0, 0, 0, 0.1);
}

[data-theme="dark"] .react-tweet-theme {
  --tweet-bg-color: #15202b;
  --tweet-border-color: rgba(255, 255, 255, 0.1);
}
```

---

## Part 7: Dashboard Integration

### User Dashboard Data Flow

**File:** `backend/src/api/routers/user.py`

```python
@router.get("/{discord_id}/dashboard")
async def get_user_dashboard(discord_id: str, messages_repo, twitter_service):
    # 1. Get Discord stats
    stats = messages_repo.get_user_stats(int(discord_id))
    
    # 2. Get tweet IDs from messages.db
    tweet_ids = messages_repo.get_user_tweets(int(discord_id))
    
    # 3. Get full URLs with detected username
    tweet_urls, detected_twitter_username = messages_repo.get_user_tweet_urls(int(discord_id))
    
    # 4. Fetch Twitter profile if username detected
    twitter_profile = None
    twitter_stats = None
    
    if detected_twitter_username and twitter_service:
        twitter_profile = await twitter_service.fetch_user_profile(detected_twitter_username)
        
        if tweet_ids:
            tweets_data = await twitter_service.fetch_tweets_batch(tweet_ids[:20])
            twitter_stats = twitter_service.calculate_total_stats(tweets_data)
    
    return {
        "discord": stats,
        "twitter": {
            "profile": twitter_profile,
            "stats": twitter_stats,
            "username": detected_twitter_username,
            "tweet_count": len(tweet_ids),
            "tweet_ids": tweet_ids,
            "tweet_urls": tweet_urls
        }
    }
```

### Frontend Display

```typescript
// Dashboard data structure
interface DashboardData {
  twitter?: {
    profile: {
      username: string;
      name: string;
      followers: number;
      profile_picture: string;
      is_verified: boolean;
    } | null;
    stats: {
      total_likes: number;
      total_retweets: number;
      total_views: number;
      avg_engagement_rate: number;
    } | null;
    tweet_count: number;
    tweet_ids: string[];
    tweet_urls: string[];
  };
}
```

---

## Complete Data Flow Example

```
1. User posts tweet URL in #twitter-showcase Discord channel
   ↓
2. Discord bot stores message in messages.db
   ↓
3. User visits /portfolio page
   ↓
4. Frontend calls GET /api/dashboard
   ↓
5. Backend reads tweet IDs from messages.db
   SELECT content FROM messages WHERE author_id = ? AND channel_id = ?
   ↓
6. Backend extracts tweet IDs using regex
   r'x\.com/\w+/status/(\d+)'
   ↓
7. Backend calls twitterapi.io to get stats
   GET https://api.twitterapi.io/twitter/tweets?tweet_ids=123,456,789
   ↓
8. Backend calculates total engagement
   total_likes, total_views, engagement_rate
   ↓
9. Frontend receives dashboard data
   ↓
10. Frontend uses react-tweet to embed selected tweets
    <Tweet id="1234567890" />
```

---

## Environment Variables

```env
# Twitter Channel in Discord (where users post tweets)
TWITTER_CHANNEL_ID=1267829631430938765

# twitterapi.io API Key
TWITTER_API_KEY=your_api_key_here

# Path to messages.db (Discord message history)
MESSAGES_DB_PATH=./data/messages.db
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/services/twitter_service.py` | twitterapi.io integration |
| `backend/src/repositories/messages_db.py` | Read tweets from SQLite |
| `backend/src/api/routers/twitter.py` | Twitter API endpoints |
| `backend/src/api/routers/user.py` | Dashboard with Twitter data |
| `web/src/app/contributions/page.tsx` | Tweet embedding with react-tweet |
| `web/src/app/portfolios/page.tsx` | Tweet display in portfolio modal |

---

## react-tweet Features

- **Server-side rendering** - Works with Next.js SSR
- **Automatic theme** - Light/dark mode support
- **Lazy loading** - Only loads when visible
- **Fallback handling** - Shows skeleton while loading
- **No API key needed** - Uses Twitter's oEmbed internally

---

## twitterapi.io Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/twitter/tweets` | GET | Fetch tweet data by IDs |
| `/twitter/user/info` | GET | Fetch user profile |
| `/twitter/user/last_tweets` | GET | Fetch user's recent tweets |

**Docs:** https://docs.twitterapi.io/
