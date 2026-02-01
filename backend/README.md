# Liquid Backend API

FastAPI backend for the Liquid Discord Bot ecosystem.

## Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

## Run

```bash
# Development
python main.py

# Or with uvicorn
uvicorn main:app --reload --port 8000
```

## API Endpoints

### Portfolio (`/api/portfolio`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/create` | Create new portfolio |
| GET | `/{discord_id}` | Get portfolio by Discord ID |
| POST | `/save` | Save portfolio draft |
| POST | `/submit` | Submit for review |
| POST | `/review` | Review portfolio |
| DELETE | `/{discord_id}` | Delete portfolio |
| GET | `/{discord_id}/can-resubmit` | Check resubmit cooldown |
| GET | `/{discord_id}/history` | Get promotion history |
| POST | `/finalize` | Finalize after vote |

### User (`/api/user`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{discord_id}/stats` | Get user stats |
| GET | `/{discord_id}/tweets` | Get shared tweets |
| GET | `/{discord_id}/dashboard` | Full dashboard |
| GET | `/server/stats` | Server stats |
| GET | `/leaderboard` | Top users |

### Contributions (`/api/contributions`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/eligibility/{discord_id}` | Check eligibility |
| POST | `/submit` | Submit contribution |
| POST | `/vote` | Vote on contribution |
| GET | `/` | List contributions |
| GET | `/featured` | Get featured |
| GET | `/user/{discord_id}` | User's contributions |

### Guilds (`/api/guilds`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/join` | Join guild |
| POST | `/leave` | Leave guild |
| GET | `/member/{discord_id}` | Get member info |
| GET | `/leaderboard` | Guild leaderboard |
| POST | `/quests/create` | Create quest |
| GET | `/quests` | List quests |
| POST | `/quests/{id}/submit` | Submit quest |
| GET | `/quests/submissions/pending` | Pending submissions |
| POST | `/quests/submissions/{id}/approve` | Approve |
| POST | `/quests/submissions/{id}/reject` | Reject |

### Parliament (`/api/parliament`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pending` | Get pending nominations |
| POST | `/processed/{id}` | Mark as processed |
| POST | `/vote` | Vote on nomination |
| GET | `/check/{id}` | Check vote status |
| POST | `/finalize/{id}` | Finalize vote |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |

## Database

SQLite with SQLAlchemy async. Tables:
- `users` - Discord users
- `portfolios` - User portfolios
- `portfolio_history` - Promotion history
- `portfolio_tweets` - Linked tweets
- `nominations` - Parliament nominations
- `votes` - Parliament votes
- `guild_members` - Guild memberships
- `quests` - Guild quests
- `quest_submissions` - Quest submissions
- `contributions` - Community contributions
- `contribution_votes` - Contribution votes
