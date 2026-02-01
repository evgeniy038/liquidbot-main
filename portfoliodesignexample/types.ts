export enum PortfolioStatus {
  Draft = 'draft',
  Submitted = 'submitted',
  PendingVote = 'pending_vote',
  Approved = 'approved',
  Rejected = 'rejected',
  Promoted = 'promoted'
}

export interface EngagementStats {
  likes: number;
  retweets: number;
  views: number;
  tweetsCount: number;
}

export interface Tweet {
  id: string;
  content: string;
  date: string;
  likes: number;
  retweets: number;
  authorName: string;
  authorHandle: string;
  authorAvatar: string;
}

export interface WorkLink {
  id: string;
  title: string;
  url: string;
  description?: string;
}

export interface Portfolio {
  discordId: string;
  username: string;
  bannerUrl?: string; // New field for profile banner
  avatarUrl?: string; // If null, generate gradient
  twitterHandle?: string;
  followersCount: number;
  targetGuild: string;
  createdAt: string;
  status: PortfolioStatus;
  stats: EngagementStats;
  otherWorks: WorkLink[];
  sharedTweets: Tweet[];
}