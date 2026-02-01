# 🤖 Liquid Bot - Setup Guide

AI-powered Discord bot with RAG, scam detection, and community analytics.

## 📋 Prerequisites

- Python 3.9+
- Discord Bot Token
- OpenRouter API Key (for Grok-4)
- OpenAI API Key (for embeddings)

---

## 🚀 Quick Setup

### 1. Clone Repository

```bash
git clone https://github.com/luminchik/lumabot.git
cd lumabot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Edit `.env` with your credentials:**

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here

# LLM Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Embeddings Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
PRODUCTION_MODE=true
```

### 4. Configure Bot Settings

**Edit `config/config.yaml`:**

#### Discord Settings:
```yaml
discord:
  guild_id: ${DISCORD_GUILD_ID}
  # Add channel IDs you want to monitor
```

#### Alert Channel (for scam detection):
```yaml
moderation:
  enabled: true
  alert_channel_id: "YOUR_ALERT_CHANNEL_ID"  # Change this!
```

#### Daily Reports:
```yaml
reports:
  enabled: true
  channel_id: "YOUR_REPORTS_CHANNEL_ID"  # Change this!
  schedule:
    hour: 5  # UTC time
    minute: 0
```

### 5. Configure Agent Personality

**Edit `config/agents.yaml`:**

Change the agent name and personality to match your community:

```yaml
agents:
  general_agent:
    name: YourBotName  # Change from "Luma"
    description: Your bot description
    
    system_prompt: |
      You are YourBotName - customize personality here
      
      ## Liquid Platform Quick Facts  # Update with your platform
      - Your platform info here
```

### 6. Run the Bot

```bash
python src/main.py
```

---

## 🔑 Getting API Keys

### Discord Bot Token:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application
3. Go to "Bot" → Reset Token
4. Enable these Privileged Gateway Intents:
   - `PRESENCE INTENT`
   - `SERVER MEMBERS INTENT`
   - `MESSAGE CONTENT INTENT`
5. Copy token to `.env`

### OpenRouter API Key:
1. Sign up at [OpenRouter](https://openrouter.ai)
2. Go to Keys → Create Key
3. Copy to `.env`

**Recommended model:** `x-ai/grok-4-fast` (fast + prompt caching)

### OpenAI API Key:
1. Sign up at [OpenAI](https://platform.openai.com)
2. Go to API Keys → Create
3. Copy to `.env`

**Used for:** `text-embedding-3-large` (message embeddings)

---

## ⚙️ Configuration Checklist

**Before first run, change these:**

- [ ] `.env` - All API keys and tokens
- [ ] `config/config.yaml`:
  - [ ] `discord.guild_id`
  - [ ] `moderation.alert_channel_id`
  - [ ] `reports.channel_id`
  - [ ] Add your domains to `moderation.url_whitelist`
- [ ] `config/agents.yaml`:
  - [ ] Agent `name`
  - [ ] Agent `description`
  - [ ] Update `system_prompt` personality
  - [ ] Update platform info in prompt

---

## 📊 Features

### 1. RAG-Powered Q&A
- Searches chat history for relevant context
- Semantic search using Qdrant vector DB
- Automatic message indexing

### 2. Scam Detection
- Pattern matching (keywords + regex)
- AI-powered risk analysis
- Automatic alerts with user actions
- Tracks user history

### 3. Daily Reports
- Automated daily at 5 AM UTC
- Manual trigger: `/report` (Admin only)
- Shows top contributors & channels
- Engagement metrics

### 4. Auto-Indexing
- Saves all messages to vector database
- Scrapes historical messages on startup
- Enables semantic search

---

## 🛠️ Advanced Configuration

### Change LLM Model:
```yaml
llm:
  model: x-ai/grok-4-fast  # or anthropic/claude-3.5-sonnet
```

### Disable Features:
```yaml
auto_indexing:
  enabled: false  # Disable message indexing

moderation:
  enabled: false  # Disable scam detection

reports:
  enabled: false  # Disable daily reports
```

### Production vs Development Logs:
```env
PRODUCTION_MODE=true   # Emoji-oriented simple logs
PRODUCTION_MODE=false  # Detailed development logs
```

---

## 🐛 Troubleshooting

### Bot doesn't respond:
- Check bot has `MESSAGE CONTENT INTENT` enabled
- Verify bot is mentioned with `@BotName`
- Check logs for errors

### Scam detection too sensitive:
```yaml
moderation:
  ai_analysis:
    trigger_threshold: 50  # Increase (default: 30)
```

### Daily report not sending:
- Verify `reports.channel_id` is correct
- Check bot has permissions in that channel
- Logs will show: `daily_report_scheduler_running`

---

## 📦 Docker Deployment (Optional)

```bash
docker-compose up -d
```

**Note:** Uses local Qdrant storage, no external DB needed.

---

## 🔒 Security Notes

- Never commit `.env` file
- Keep API keys secret
- Use environment variables only
- `.gitignore` already configured

---

## 📝 Project Structure

```
lumabot/
├── src/
│   ├── bot/          # Discord bot logic
│   ├── agents/       # Agent system
│   ├── llm/          # OpenRouter client
│   ├── rag/          # RAG + Qdrant
│   ├── moderation/   # Scam detection
│   ├── analytics/    # Daily reports
│   └── utils/        # Config, logging
├── config/
│   ├── config.yaml   # Main config
│   └── agents.yaml   # Agent personalities
├── .env.example      # Template
├── requirements.txt
└── README.md
```

---

## 💡 Tips

1. **Test in dev channel first** before deploying to main server
2. **Monitor logs** for first 24h to tune scam detection
3. **Customize agent personality** to match your community tone
4. **Add trusted domains** to `url_whitelist` to reduce false positives
5. **Use prompt caching** - Grok caches system prompts (75% cost reduction)

---

## 🤝 Support

- Check logs: `logs/bot.log`
- Review config: `config/config.yaml`
- Test patterns: `test_scam_patterns.py`

---

**Ready to deploy?** Run `python src/main.py` and watch the logs! 🚀
