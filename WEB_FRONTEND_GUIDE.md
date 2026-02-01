# BuildLiquid Web Frontend Guide

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.0.7 | React framework (App Router) |
| **React** | 19.2.0 | UI library |
| **TailwindCSS** | 4.x | Styling |
| **GSAP** | 3.13.0 | Animations |
| **Lenis** | 1.3.15 | Smooth scrolling |
| **next-auth** | 4.24.13 | Discord OAuth |
| **react-tweet** | 3.2.2 | Embedded tweets |
| **recharts** | 3.5.1 | Charts/graphs |
| **lucide-react** | 0.556.0 | Icons |

---

## Project Structure

```
web/src/
├── app/                    # Next.js App Router pages
│   ├── api/               # API routes (proxy to backend)
│   ├── portfolio/         # User portfolio page
│   ├── portfolios/        # All portfolios list
│   ├── contributions/     # Community contributions
│   │   ├── submit/       # Submit contribution
│   │   ├── vote/         # Vote on contributions
│   │   └── best/         # Featured works
│   └── stats/            # Server statistics
├── components/            # Reusable components
│   ├── layout/           # Header, Navigation
│   ├── portfolio/        # Portfolio-specific components
│   ├── providers/        # Context providers
│   └── ui/               # Generic UI components
├── constants/            # App constants
├── hooks/                # Custom React hooks
├── lib/                  # Utilities, API client
├── styles/               # CSS files
└── types/                # TypeScript types
```

---

## Pages Overview

### 1. Home Page (`/`)

**File:** `src/app/page.tsx`

**Components:**
- `ParallaxHero` - Animated hero with parallax layers
- `OceanDive` - Interactive role hierarchy visualization

**Features:**
- GSAP-powered parallax scrolling
- Depth meter showing scroll position
- Role cards with animations (Droplet → Allinliquid)
- Floating ocean particles

**Data:** Static role definitions

---

### 2. Portfolio Page (`/portfolio`)

**File:** `src/app/portfolio/page.tsx` (1078 lines)

**Requires:** Discord authentication

**States:**
- `guild` - Guild selection step
- `form` - Portfolio editing form
- `dashboard` - View submitted portfolio

**Components Used:**
- `StatsCharts` - Discord/Twitter activity charts
- `Loader` - Loading state

**Form Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `guild` | Select | Guild selection (helpers/creators/artists) |
| `twitter_username` | Text | Twitter/X username |
| `top_content` | Textarea | Best content links |
| `top_content_links` | Array | Parsed URLs |
| `unique_qualities` | Textarea | What makes you unique |
| `why_promotion` | Textarea | Why deserve promotion |
| `proof_of_use` | Text | Proof of Liquid usage |
| `proof_images` | Array | Image URLs |
| `selected_tweets` | Array | Selected tweet URLs |

**Buttons:**
| Button | Action | Style |
|--------|--------|-------|
| Save Draft | `POST /api/portfolio/save` | Secondary |
| Submit for Review | `POST /api/portfolio/submit` | Primary |
| Delete Portfolio | `DELETE /api/portfolio/delete` | Danger |
| Login with Discord | `signIn('discord')` | Primary |

**API Calls:**
- `GET /api/dashboard` - Fetch user data
- `GET /api/portfolio/history` - Promotion history
- `POST /api/portfolio/save` - Save draft
- `POST /api/portfolio/submit` - Submit for review
- `DELETE /api/portfolio/delete` - Delete portfolio

---

### 3. All Portfolios (`/portfolios`)

**File:** `src/app/portfolios/page.tsx` (639 lines)

**Components:**
- `Tweet` (react-tweet) - Embedded tweets
- `StatsCharts` - User activity charts
- `TweetSkeleton` - Loading placeholder

**Data Displayed:**
- User avatar, username
- Portfolio status badge
- Guild emoji
- Discord stats (messages, days active)
- Tweet count
- Selected tweets (embedded)
- Portfolio answers

**Filters:** Status (draft, submitted, approved, rejected)

**API Calls:**
- `GET /api/portfolios` - Fetch all portfolios

---

### 4. Stats Page (`/stats`)

**File:** `src/app/stats/page.tsx` (461 lines)

**Charts (recharts):**
- `AreaChart` - Daily/weekly message activity
- `BarChart` - Top contributors
- `PieChart` - Portfolio status distribution

**Stats Cards:**
| Stat | Icon | Description |
|------|------|-------------|
| Total Users | Users | Server member count |
| Total Messages | MessageSquare | All-time messages |
| Messages Today | TrendingUp | Today's activity |
| Active This Week | Activity | Weekly active users |

**Period Filters:** Day / Week / Month

**Data:**
```typescript
interface StatsData {
  server: {
    total_users: number;
    total_messages: number;
    messages_today: number;
    active_users_week: number;
  };
  daily_messages: Array<{period, message_count, unique_users}>;
  weekly_messages: Array<{period, message_count, unique_users}>;
  top_contributors: {day, week, month};
  top_content_makers: {day, week, month};
}
```

**API Calls:**
- `GET /api/stats/dashboard`

---

### 5. Contributions Page (`/contributions`)

**File:** `src/app/contributions/page.tsx` (132 lines)

**Components:**
- `Tweet` - Embedded featured tweets
- `TweetCard` - Tweet wrapper with Suspense

**Buttons:**
| Button | Link | Icon |
|--------|------|------|
| Submit Your Work | `/contributions/submit` | ✨ |
| Vote for Works | `/contributions/vote` | 🗳️ |

**Data:**
- Featured/approved tweet IDs
- Sample tweet IDs (fallback)

**API Calls:**
- `GET /api/contributions/featured?limit=50`

---

### 6. Submit Contribution (`/contributions/submit`)

**File:** `src/app/contributions/submit/page.tsx` (131 lines)

**Requires:** Discord authentication

**Form Fields:**
| Field | Type | Required |
|-------|------|----------|
| Title | Text | Yes |
| Tweet URL | URL | Yes |

**Buttons:**
| Button | Action |
|--------|--------|
| Submit Contribution | `POST /api/contributions` |
| View Best Works | Link to `/contributions` |
| Vote for Works | Link to `/contributions/vote` |

**Guidelines Displayed:**
- Content must be Liquid-related
- Twitter threads preferred
- Original content only
- Submissions reviewed before voting
- Top voted = featured

---

### 7. Vote Page (`/contributions/vote`)

**File:** `src/app/contributions/vote/page.tsx` (201 lines)

**Requires:** Discord authentication for voting

**Components:**
- `Tweet` - Embedded contribution tweets

**Vote Buttons:**
| Button | Action | Icon |
|--------|--------|------|
| Upvote | `POST /api/contributions/vote` (upvote) | 👍 |
| Downvote | `POST /api/contributions/vote` (downvote) | 👎 |

**Data per Contribution:**
```typescript
interface Contribution {
  id: number;
  user_id: string;
  username: string;
  title: string;
  url: string;
  vote_count: number;
  status: string;
  is_featured: boolean;
}
```

**API Calls:**
- `GET /api/contributions?status=voting`
- `POST /api/contributions/vote`

---

## Components Reference

### Layout Components

#### Header (`components/layout/Header/`)
| File | Purpose |
|------|---------|
| `index.tsx` | Main header with GSAP animations |
| `Logo.tsx` | Liquid logo |
| `MenuButton.tsx` | Hamburger menu toggle |
| `AuthSection.tsx` | Login/user info |
| `NavigationMenu.tsx` | Fullscreen nav overlay |

**Features:**
- GSAP-powered menu animations
- Discord OAuth integration
- Guild badge display
- Escape key to close

---

### Portfolio Components (`components/portfolio/`)

| Component | Purpose |
|-----------|---------|
| `StatsCharts.tsx` | Discord/Twitter activity charts |
| `StatsCard.tsx` | Stat display card |
| `GuildSelect.tsx` | Guild selection dropdown |
| `PortfolioContent.tsx` | Portfolio view layout |
| `PortfolioHistory.tsx` | Promotion history list |
| `RoleProgression.tsx` | Role hierarchy display |
| `TwitterProfileCard.tsx` | Twitter profile card |
| `CooldownWarning.tsx` | Resubmission cooldown notice |

---

### UI Components (`components/ui/`)

| Component | Purpose |
|-----------|---------|
| `RoleBadge.tsx` | Role name with color |
| `StatusBadge.tsx` | Portfolio status indicator |

---

### Animation Components

| Component | Purpose |
|-----------|---------|
| `ParallaxHero.tsx` | GSAP parallax hero section |
| `OceanDive.tsx` | Interactive role visualization |
| `SmoothScroll.tsx` | Lenis smooth scroll wrapper |
| `Loader.tsx` | Loading spinner |
| `FeaturedTweet.tsx` | Featured tweet display |

---

## Custom Hooks

### `useDashboard`
```typescript
const { dashboard, history, loading, error, refetch } = useDashboard();
```
Fetches user dashboard data and portfolio history.

### `usePortfolio`
Portfolio form state and actions management.

---

## API Client (`lib/api.ts`)

```typescript
import { api } from '@/lib/api';

// Dashboard
api.getDashboard()

// Portfolio
api.getPortfolioHistory()
api.savePortfolio(data)
api.submitPortfolio()
api.deletePortfolio()

// Contributions
api.submitContribution(data)
api.getContributions(status?)
api.voteContribution(id, voteType)
```

---

## Constants (`constants/index.ts`)

### Guilds
```typescript
export const GUILDS = [
  { id: 'helpers', emoji: '🛡️', description: 'Community helpers' },
  { id: 'creators', emoji: '🎨', description: 'Content creators' },
  { id: 'artists', emoji: '🎭', description: 'Art and design' },
];
```

### Role Hierarchy
```typescript
export const ROLE_HIERARCHY = [
  'Droplet', 'Current', 'Tide', 'Wave', 'Tsunami', 'Allinliquid'
];
```

### Role Colors
```typescript
export const ROLE_COLORS = {
  'Droplet': '#4FC3F7',
  'Current': '#29B6F6',
  'Tide': '#0288D1',
  'Wave': '#01579B',
  'Tsunami': '#004D40',
  'Allinliquid': '#FFD700',
};
```

### Portfolio Statuses
```typescript
export const PORTFOLIO_STATUS = {
  draft: { label: 'DRAFT', color: '#6b7280', icon: '📝' },
  submitted: { label: 'UNDER REVIEW', color: '#f59e0b', icon: '⏳' },
  pending_vote: { label: 'PARLIAMENT VOTING', color: '#8b5cf6', icon: '🗳️' },
  approved: { label: 'APPROVED', color: '#10b981', icon: '✅' },
  rejected: { label: 'REJECTED', color: '#ef4444', icon: '❌' },
  promoted: { label: 'PROMOTED', color: '#10b981', icon: '🎉' },
};
```

### Menu Items
```typescript
export const MENU_ITEMS = [
  { label: 'Home', href: '/', number: '01' },
  { label: 'My Portfolio', href: '/portfolio', number: '02', requiresAuth: true },
  { label: 'All Portfolios', href: '/portfolios', number: '03' },
  { label: 'Contributions', href: '/contributions', number: '04' },
  { label: 'Stats', href: '/stats', number: '05' },
];
```

---

## CSS Files (`styles/`)

| File | Purpose | Lines |
|------|---------|-------|
| `variables.css` | CSS variables | 575 |
| `base.css` | Base styles | 1857 |
| `header.css` | Header/nav styles | 9291 |
| `parallax.css` | Parallax hero | 4819 |
| `ocean.css` | Ocean dive section | 8850 |
| `portfolio.css` | Portfolio page | 14823 |
| `portfolios-list.css` | All portfolios | 22296 |
| `contributions.css` | Contributions pages | 21860 |
| `stats.css` | Stats page | 7170 |
| `dashboard.css` | Dashboard styles | 6166 |
| `components.css` | Shared components | 20466 |

---

## Authentication Flow

1. User clicks "Login with Discord"
2. `next-auth` redirects to Discord OAuth
3. User authorizes app
4. Callback returns with session
5. Session contains: `user.id`, `user.name`, `user.image`

**Provider:** Discord OAuth via `next-auth`

---

## Key Features to Replicate

### 1. Animated Header Menu
- GSAP timeline animations
- Background panel stagger
- Menu link reveal animation
- Escape key handler

### 2. Parallax Hero
- Multi-layer parallax with ScrollTrigger
- Layer-based depth (yPercent offsets)
- Gradient fade overlay

### 3. Ocean Dive Visualization
- Scroll-based depth meter
- Role cards with branch connectors
- Floating particle system
- Progressive visibility on scroll

### 4. Portfolio System
- Multi-step form (guild → form → dashboard)
- Auto-save draft functionality
- Tweet selection with embedded preview
- Cooldown system for resubmission
- Status tracking (draft → approved)

### 5. Contribution Voting
- Embedded Twitter tweets
- Upvote/downvote system
- Vote count display
- Featured contributions

### 6. Stats Dashboard
- Recharts integration
- Period filters (day/week/month)
- Leaderboards
- Activity charts

---

## Environment Variables

```env
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret

DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret

NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Quick Start for New Project

```bash
# Create Next.js project
npx create-next-app@latest my-app --typescript --tailwind --app

# Install dependencies
npm install gsap @studio-freight/lenis lenis lucide-react next-auth react-tweet recharts

# Copy structure
# - /app for pages
# - /components for reusable
# - /constants for config
# - /hooks for custom hooks
# - /lib for utilities
# - /styles for CSS
```
