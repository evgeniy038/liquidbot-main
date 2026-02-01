# BuildLiquid - Architecture Overview

## Table of Contents
1. [Project Structure](#project-structure)
2. [Voting Systems](#voting-systems)
3. [API Endpoints](#api-endpoints)
4. [Bot-Website Connection](#bot-website-connection)
5. [Database Models](#database-models)
6. [Role Hierarchy](#role-hierarchy)

---

## Project Structure

```
buildliquid/
├── backend/                 # FastAPI Backend Server
│   └── src/
│       ├── api/            # REST API endpoints
│       │   ├── routers/    # Route handlers
│       │   └── schemas/    # Pydantic models
│       ├── services/       # Business logic
│       └── models/         # Database models
├── src/
│   ├── bot/                # Discord Bot (discord.py)
│   │   ├── commands/       # Slash commands
│   │   ├── handlers/       # Event handlers
│   │   └── tasks/          # Background tasks
│   ├── app/                # Next.js Frontend
│   │   └── api/            # Frontend API routes
│   └── services/           # Shared services
├── config/                 # YAML configuration files
└── data/                   # SQLite databases
```

---

## Voting Systems

### 1. Portfolio Voting System

**Location:** `src/bot/commands/portfolio.py`

**Flow:**
1. User creates portfolio via `/portfolio` command
2. User fills data and submits via `/submit`
3. AI analyzes the portfolio content
4. Submission goes to review channel with buttons
5. Moderators/Parliament can: Approve, Request Changes, Reject

**Commands:**
| Command | Description |
|---------|-------------|
| `/portfolio` | Create portfolio (requires email) |
| `/portfolio_view` | View your portfolio link |
| `/submit` | Submit portfolio for AI analysis and review |

**Review Buttons:**
- ✅ **Approve** - Approves portfolio, notifies user
- ⏸️ **Request Changes** - Opens modal for feedback
- ❌ **Reject** - Opens modal for rejection reason

**Permission Check:**
```python
def _has_permission(self, user: discord.Member) -> bool:
    role_ids = [r.id for r in user.roles]
    return (
        self.config.roles.moderator in role_ids or
        self.config.roles.parliament in role_ids or
        user.guild_permissions.administrator
    )
```

---

### 2. Guild Leaders System

**Location:** `src/bot/commands/guild.py`

**Guilds Available:**
- **Content Guild** - Educator, Creator/Shitposter
- **Helpers Guild** - Helper
- **Artists Guild** - Artist

**Commands:**
| Command | Description | Access |
|---------|-------------|--------|
| `/guild join` | Join a guild with role type | Everyone |
| `/guild leave` | Leave current guild | Everyone |
| `/guild info` | View your guild stats | Everyone |
| `/guild leaderboard` | View guild rankings | Everyone |
| `/quest create` | Create new quest | Guild Leaders only |
| `/quest list` | List active quests | Everyone |
| `/quest submit` | Submit quest completion | Guild members |
| `/quest review` | Review submissions | Guild Leaders only |
| `/quest approve` | Approve submission | Guild Leaders only |
| `/quest reject` | Reject submission | Guild Leaders only |

**Guild Leader Check:**
```python
def _is_guild_leader(self, member: discord.Member) -> bool:
    role_ids = [r.id for r in member.roles]
    return (
        self.config.roles.guild_leader in role_ids or
        member.guild_permissions.administrator
    )
```

**Quest System:**
- Guild Leaders create quests with title, description, points, deadline
- Members submit work URLs
- Leaders approve/reject submissions
- Points awarded on approval
- Top 3 monthly get nominated for promotions

---

### 3. Parliament Voting System

**Location:** `src/bot/commands/parliament.py`

**Flow:**
1. Portfolio approved by Guild Lead on website
2. Backend sends to `/api/parliament/pending`
3. Bot polls API every 30 seconds
4. Creates voting embed in Parliament channel
5. Members vote with ✅ Approve / ❌ Reject buttons
6. After 5+ votes with 60% approval → Role assigned

**Vote Thresholds:**
- Minimum votes required: **5**
- Approval rate needed: **60%**
- Auto-reject if rejection rate > 40%

**Role IDs (Environment Variables):**
```python
ROLE_IDS = {
    "Droplet": 1445308513663324243,
    "Current": 1444006094283477085,
    "Founding_Droplet": 1069142027784171623,
    "Tide": 1069140617239744572,
    "Wave": 1068785740068159590,
    "Tsunami": 957362763267702815,
    "Allinliquid": 1377229341418852402,
}
```

**Parliament Channel ID:** `1442411279179321415`

---

## API Endpoints

### Backend API (FastAPI) - Base URL: `/api`

#### Portfolio Routes (`/api/portfolio`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/create` | Create new portfolio |
| GET | `/{discord_id}` | Get portfolio by Discord ID |
| POST | `/submit` | Submit portfolio for review |
| POST | `/save` | Save portfolio draft data |
| DELETE | `/{discord_id}` | Delete portfolio |
| GET | `/{discord_id}/can-resubmit` | Check resubmit cooldown |
| GET | `/{discord_id}/history` | Get promotion history |
| POST | `/review` | Approve/reject portfolio (sends to Discord) |

#### User Routes (`/api/user`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{discord_id}/stats` | Get user statistics |
| GET | `/{discord_id}/tweets` | Get user's shared tweets |
| GET | `/{discord_id}/dashboard` | Comprehensive dashboard data |
| GET | `/server/stats` | Get server statistics |
| GET | `/leaderboard` | Get top users |

#### Stats Routes (`/api/stats`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Dashboard statistics |
| GET | `/portfolios` | List all portfolios |

#### Contributions Routes (`/api/contributions`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/eligibility/{discord_id}` | Check submission eligibility |
| POST | `/submit` | Submit new contribution |
| POST | `/vote` | Vote on contribution |
| GET | `/` | List contributions |
| GET | `/featured` | Get featured contributions |
| GET | `/user/{discord_id}` | Get user's contributions |
| GET | `/{contribution_id}/votes` | Get vote counts |

#### Other Routes
| Route | Description |
|-------|-------------|
| `/api/twitter/*` | Twitter integration |
| `/api/roles/*` | Role management |
| `/api/health` | Health check |

---

## Bot-Website Connection

### Communication Flow

```
┌─────────────┐     HTTP POST      ┌─────────────┐
│   Website   │ ─────────────────► │  Backend    │
│  (Next.js)  │                    │  (FastAPI)  │
└─────────────┘                    └──────┬──────┘
                                          │
                                          │ Discord API
                                          ▼
┌─────────────┐    Poll /pending   ┌─────────────┐
│   Discord   │ ◄───────────────── │  Discord    │
│   Channel   │                    │    Bot      │
└─────────────┘                    └─────────────┘
```

### Key Integration Points

1. **Portfolio Review → Discord Voting**
   - Website calls `POST /api/portfolio/review`
   - Backend sends message with buttons to Discord channel
   - Uses Discord API directly via `httpx`

2. **Parliament Polling**
   - Bot polls `GET /api/parliament/pending` every 30 seconds
   - Creates voting embeds for new approvals
   - Marks as processed via `POST /api/parliament/processed/{user_id}`

3. **Vote Finalization**
   - Bot calls `POST /api/portfolio/finalize` when vote completes
   - Backend updates status, bot assigns role

### Discord API Integration (Backend)
```python
async def send_discord_message_with_buttons(channel_id: str, embed: dict, components: list):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}"},
            json={"embeds": [embed], "components": components}
        )
```

---

## Database Models

### Main Tables

| Table | Purpose |
|-------|---------|
| `users` | Discord user data |
| `portfolios` | User portfolios (Notion linked) |
| `portfolio_history` | Archived portfolios after promotion |
| `portfolio_tweets` | Tweets used in portfolios |
| `nominations` | Role promotion nominations |
| `votes` | Parliament votes on nominations |
| `guild_members` | Guild memberships |
| `quests` | Guild quests/tasks |
| `quest_submissions` | Quest completion submissions |
| `contributions` | Community contributions |
| `contribution_votes` | Votes on contributions |
| `reports` | User reports |
| `spotlights` | Weekly spotlight themes |

### Portfolio Statuses
- `draft` - Being edited
- `submitted` - Awaiting review
- `pending_vote` - In Parliament voting
- `approved` - Approved, awaiting role
- `rejected` - Rejected (7-day cooldown)
- `promoted` - Role assigned

---

## Role Hierarchy

### Community Roles (Progression)
```
Droplet → Current → Tide → Wave → Tsunami → Allinliquid
```

### Guild Path Roles

**Traders Guild:**
- Tide (T1) → Degen (T2) → Speculator (T3)

**Content Guild:**
- Drip (T1) → Frame (T2) → Orator (T3)

**Designers Guild:**
- Ink (T1) → Sketch (T2) → Sculptor (T3)

### Role Mapping (Production)
```yaml
community:
  wave: "1436827617993953361"
  tide: "1436827751922274386"
  current: "1436827711288119466"
  all_in_liquid: "1436825727029874698"
  founding_droplets: "1436826732043698370"
  liquid_frens: "1436826786821312663"
  tsunami: "1443238384234659881"
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Discord Bot | discord.py (Python) |
| Backend API | FastAPI (Python) |
| Frontend | Next.js (TypeScript) |
| Database | PostgreSQL + SQLite (messages.db) |
| ORM | SQLAlchemy (async) |
| External APIs | Notion, Twitter/X, Discord |
| Deployment | Docker, Netlify |

---

## Environment Variables

```env
# Discord
DISCORD_TOKEN=
DISCORD_GUILD_ID=
NOMINATION_CHANNEL_ID=

# Database
DATABASE_URL=postgresql://...

# Notion
NOTION_TOKEN=
NOTION_DATABASE_ID=

# Twitter
TWITTER_API_KEY=
TWITTER_API_SECRET=

# Roles
Droplet=1445308513663324243
Current=1444006094283477085
Tide=1069140617239744572
Wave=1068785740068159590
Tsunami=957362763267702815
Allinliquid=1377229341418852402
```

---

## Quick Reference

### Cooldowns
- Portfolio resubmit after rejection: **7 days**
- About command cooldown: **60 seconds**

### Voting Rules
- Parliament votes: **5+ votes, 60% approval**
- Contribution auto-approve: **3+ upvotes**
- Vote deadline: **48 hours**

### API Base URLs
- Backend: `http://localhost:8000/api`
- Frontend: `http://localhost:3000`
- Production: `https://tryliquid.xyz`
