# Portfolio Page - Complete Documentation

## Overview

The `/portfolio` page is a multi-step user dashboard for creating, editing, and submitting portfolios for role promotion in the Liquid community.

**File:** `web/src/app/portfolio/page.tsx` (1078 lines)

---

## Page States (Steps)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    guild    │ ──► │    form     │ ──► │  dashboard  │
│  (select)   │     │   (edit)    │     │   (view)    │
└─────────────┘     └─────────────┘     └─────────────┘
```

| State | Description | When Shown |
|-------|-------------|------------|
| `guild` | Guild selection screen | New user, no portfolio |
| `form` | Portfolio editing form | Creating/editing portfolio |
| `dashboard` | View submitted portfolio | Portfolio exists |

---

## Authentication Flow

```
1. User visits /portfolio
2. useSession() checks Discord auth
3. If not authenticated → Show "Login with Discord" button
4. If authenticated → fetchDashboard()
```

**Auth Check:**
```typescript
const { data: session, status } = useSession();

if (!session) {
  // Show login screen
  return <button onClick={() => signIn('discord')}>Login with Discord</button>
}
```

---

## API Endpoints

### Frontend API Routes (Next.js → Backend proxy)

| Method | Frontend Route | Backend Route | Purpose |
|--------|----------------|---------------|---------|
| GET | `/api/dashboard` | `/api/user/{discord_id}/dashboard` | Get all user data |
| GET | `/api/portfolio/history` | `/api/portfolio/{discord_id}/history` | Get promotion history |
| POST | `/api/portfolio/save` | `/api/portfolio/save` | Save portfolio draft |
| POST | `/api/portfolio/submit` | `/api/portfolio/submit` | Submit for review |
| DELETE | `/api/portfolio/delete` | `/api/portfolio/{discord_id}` | Delete portfolio |

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        /portfolio Page                            │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  1. fetchDashboard() on mount                                     │
│     GET /api/dashboard                                            │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  Next.js API Route: /api/dashboard/route.ts                       │
│  - Gets session via getServerSession()                            │
│  - Calls: GET {BACKEND}/api/user/{discord_id}/dashboard           │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  FastAPI Backend: /api/user/{discord_id}/dashboard                │
│  Returns: DashboardData                                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## Dashboard Data Structure

```typescript
interface DashboardData {
  discord?: {
    message_count: number;      // Total messages in Discord
    days_active: number;        // Days since first message
    first_message_date: string; // ISO date
    username: string;           // Discord username
  };
  
  twitter?: {
    profile: {
      username: string;
      name: string;
      followers: number;
      tweet_count: number;
      profile_picture: string;
      is_verified: boolean;
    } | null;
    stats: {
      total_tweets: number;
      total_likes: number;
      total_retweets: number;
      total_replies: number;
      total_views: number;
      avg_engagement_rate: number;
    } | null;
    username: string | null;
    detected_username: string | null;
    tweet_count: number;
    tweet_ids: string[];
    tweet_urls?: string[];
  };
  
  portfolio?: {
    data: PortfolioFormData | null;
    status: 'draft' | 'submitted' | 'pending_vote' | 'approved' | 'rejected' | 'promoted' | null;
    current_role?: string;
    target_role?: string | null;
    next_role?: string | null;
    can_resubmit?: boolean;
    cooldown?: {
      cooldown_end: string;
      days_remaining: number;
      hours_remaining: number;
    } | null;
  };
  
  roles?: {
    current: string;
    current_id: string | null;
    next: string | null;
    next_id: string | null;
    hierarchy: string[];
  };
  
  guild?: string | null;  // Auto-detected from Discord roles
}
```

---

## Form Data Structure

```typescript
interface FormData {
  guild: string;              // 'helpers' | 'creators' | 'artists'
  twitter_username: string;   // Twitter/X username
  top_content: string;        // Text with URLs
  top_content_links: string[];// Parsed URLs array
  unique_qualities: string;   // What makes you unique
  why_promotion: string;      // Why you deserve promotion
  proof_of_use: string;       // Screenshot link
  proof_images: string[];     // Image URLs array
  selected_tweets: string[];  // Tweet URLs/IDs
  avatar_url?: string;        // Discord avatar
}
```

---

## Portfolio Statuses

| Status | Label | Color | Icon | Can Edit | Can Submit |
|--------|-------|-------|------|----------|------------|
| `draft` | DRAFT | #6b7280 | 📝 | ✅ | ✅ |
| `submitted` | UNDER REVIEW | #f59e0b | ⏳ | ❌ | ❌ |
| `pending_vote` | PARLIAMENT VOTING | #8b5cf6 | 🗳️ | ❌ | ❌ |
| `approved` | APPROVED | #10b981 | ✅ | ❌ | ❌ |
| `rejected` | REJECTED | #ef4444 | ❌ | After cooldown | After cooldown |
| `promoted` | PROMOTED | #10b981 | 🎉 | ❌ | ❌ |

---

## User Actions & Handlers

### 1. Save Portfolio (Draft)

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  // Validate form
  if (!formData.unique_qualities.trim()) {
    setError('Please fill in "What makes you unique"');
    return;
  }
  
  // Prepare data
  const dataToSave = {
    ...formData,
    selected_tweets: availableTweets.map(url => extractTweetId(url)),
    avatar_url: session?.user?.image || null,
  };
  
  // POST to API
  const res = await fetch('/api/portfolio/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dataToSave),
  });
  
  if (data.success) {
    setStep('dashboard');
    fetchDashboard();
  }
};
```

**API Route:** `/api/portfolio/save/route.ts`
```typescript
// Proxies to backend
fetch(`${API_BASE_URL}/api/portfolio/save`, {
  method: 'POST',
  body: JSON.stringify({
    discord_id: session.user.id,
    data: body  // Form data
  }),
});
```

---

### 2. Submit for Review

```typescript
const handleSubmitPortfolio = async () => {
  // Optimistic UI update
  setDashboard({
    ...dashboard,
    portfolio: { ...dashboard.portfolio, status: 'submitted' }
  });
  
  const res = await fetch('/api/portfolio/submit', {
    method: 'POST',
  });
  
  if (!data.success) {
    // Revert on failure
    fetchDashboard();
  }
};
```

**API Route:** `/api/portfolio/submit/route.ts`
```typescript
fetch(`${API_BASE_URL}/api/portfolio/submit`, {
  method: 'POST',
  body: JSON.stringify({ discord_id: session.user.id }),
});
```

---

### 3. Delete Portfolio

```typescript
const handleDeletePortfolio = async () => {
  if (!confirm('Are you sure?')) return;
  
  const res = await fetch('/api/portfolio/delete', {
    method: 'DELETE',
  });
  
  if (data.success) {
    setDashboard(null);
    setFormData(initialFormData);
    setStep('guild');
  }
};
```

**API Route:** `/api/portfolio/delete/route.ts`
```typescript
fetch(`${API_BASE_URL}/api/portfolio/${session.user.id}`, {
  method: 'DELETE',
});
```

---

## Form Tabs

The form has two tabs:

### Tab 1: "🐦 Your Tweets"
- Twitter username input
- Available tweets pool (from DB)
- Add tweet URL manually
- Select tweets for highlights

### Tab 2: "📝 Application Details"
- What makes you unique (required)
- Why you deserve promotion (required)
- Proof of use (optional)
- Proof images (optional)

---

## Validation Rules

```typescript
// Required fields
if (!formData.unique_qualities.trim()) {
  setError('Please fill in "What makes you unique"');
  setFormTab('details');
  return;
}

if (!formData.why_promotion.trim()) {
  setError('Please fill in "Why you deserve promotion"');
  setFormTab('details');
  return;
}

if (availableTweets.length === 0) {
  setError('Please add at least one tweet');
  setFormTab('tweets');
  return;
}
```

---

## Cooldown System

After rejection, users must wait 7 days before resubmitting:

```typescript
// Display cooldown warning
{cooldown && !canResubmit && (
  <div className="cooldown-warning">
    <p>You can resubmit in {cooldown.days_remaining} days and {cooldown.hours_remaining} hours</p>
    <p>Available on: {new Date(cooldown.cooldown_end).toLocaleDateString()}</p>
  </div>
)}

// Disable edit/submit buttons
{(dashboard.portfolio?.status === 'draft' || 
  (dashboard.portfolio?.status === 'rejected' && canResubmit)) && (
  <button>Edit Portfolio</button>
  <button>Submit for Review</button>
)}
```

---

## Components Used

| Component | Purpose |
|-----------|---------|
| `Loader` | Loading state spinner |
| `StatsCharts` | Discord/Twitter activity graphs |
| `GUILDS` constant | Guild definitions |
| `ROLE_HIERARCHY` constant | Role progression |

---

## UI Sections (Dashboard View)

```
┌─────────────────────────────────────────────────────────┐
│ Header: Avatar, Username, Guild Badge, Role, Status     │
├─────────────────────────────────────────────────────────┤
│ Cooldown Warning (if rejected & in cooldown)            │
├─────────────────────────────────────────────────────────┤
│ Stats Charts: Discord activity, Twitter engagement      │
├─────────────────────────────────────────────────────────┤
│ Portfolio Content:                                       │
│   - 🏆 Top Content Highlights                           │
│   - ✨ What Makes You Unique                            │
│   - 🎯 Why You Deserve Promotion                        │
│   - 📱 Proof of Use (images)                            │
│   - 🐦 Your Shared Tweets                               │
├─────────────────────────────────────────────────────────┤
│ Promotion History (if any)                              │
├─────────────────────────────────────────────────────────┤
│ Actions: Edit | Submit | Delete                         │
└─────────────────────────────────────────────────────────┘
```

---

## Role Colors

```typescript
const ROLE_COLORS: Record<string, string> = {
  'Droplet': '#4FC3F7',
  'Current': '#29B6F6',
  'Tide': '#0288D1',
  'Wave': '#01579B',
  'Tsunami': '#004D40',
  'Allinliquid': '#FFD700',
};
```

---

## Guilds

```typescript
const GUILDS = [
  { id: 'helpers', emoji: '🛡️', description: 'Community helpers' },
  { id: 'creators', emoji: '🎨', description: 'Content creators' },
  { id: 'artists', emoji: '🎭', description: 'Art and design' },
];
```

---

## Helper Functions

### Clean Twitter Username
```typescript
const cleanTwitterUsername = (input: string): string => {
  let username = input.trim();
  // Handle x.com/username or twitter.com/username URLs
  if (username.includes('x.com/') || username.includes('twitter.com/')) {
    username = username.split('/').pop()?.split('?')[0] || username;
  }
  // Remove @ prefix
  return username.replace(/^@+/, '');
};
```

### Parse Links in Text
```typescript
const parseLinks = (text: string) => {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(urlRegex);
  return parts.map((part, i) => {
    if (part.match(urlRegex)) {
      return <a href={part} target="_blank">{part}</a>;
    }
    return part;
  });
};
```

---

## State Management

```typescript
// Core states
const [dashboard, setDashboard] = useState<DashboardData | null>(null);
const [loading, setLoading] = useState(true);
const [step, setStep] = useState<'guild' | 'form' | 'dashboard'>('form');

// Form states
const [formData, setFormData] = useState<FormData>(initialFormData);
const [formTab, setFormTab] = useState<'tweets' | 'details'>('tweets');
const [availableTweets, setAvailableTweets] = useState<string[]>([]);

// Action states
const [saving, setSaving] = useState(false);
const [submitting, setSubmitting] = useState(false);
const [deleting, setDeleting] = useState(false);

// Feedback states
const [error, setError] = useState('');
const [success, setSuccess] = useState('');

// History
const [history, setHistory] = useState<PortfolioHistoryItem[]>([]);
```

---

## Full Request Flow Example

### User Saves Portfolio:

```
1. User fills form, clicks "Save Draft"
   ↓
2. handleSubmit() validates form
   ↓
3. POST /api/portfolio/save (Next.js)
   Body: { guild, twitter_username, top_content, ... }
   ↓
4. Next.js route adds discord_id from session
   POST {BACKEND}/api/portfolio/save
   Body: { discord_id: "123", data: {...} }
   ↓
5. FastAPI backend saves to PostgreSQL
   Returns: { success: true }
   ↓
6. Frontend shows success, switches to dashboard view
   fetchDashboard() refreshes data
```

---

## CSS Files

- `styles/portfolio.css` - Main portfolio styles (14823 bytes)
- `styles/dashboard.css` - Dashboard styles (6166 bytes)

---

## Environment Variables

```env
# Backend API URL (for Next.js API routes)
BACKEND_API_URL=http://localhost:8000

# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret
DISCORD_CLIENT_ID=xxx
DISCORD_CLIENT_SECRET=xxx
```
