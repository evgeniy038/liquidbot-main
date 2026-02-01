import { Portfolio, PortfolioStatus } from './types';

export const MOCK_PORTFOLIO: Portfolio = {
  discordId: '123456789012345678',
  username: 'CryptoWizard',
  bannerUrl: 'https://images.unsplash.com/photo-1639762681485-074b7f938ba0?q=80&w=2832&auto=format&fit=crop',
  avatarUrl: 'https://images.unsplash.com/photo-1628157588553-5eeea00af15c?q=80&w=200&auto=format&fit=crop',
  twitterHandle: 'wizard_crypto',
  followersCount: 14500,
  targetGuild: 'Traders',
  createdAt: '2023-10-24',
  status: PortfolioStatus.Promoted,
  stats: {
    likes: 8432,
    retweets: 1205,
    views: 450000,
    tweetsCount: 142
  },
  otherWorks: [
    {
      id: '1',
      title: 'Alpha Analysis Dashboard',
      url: 'https://example.com/dashboard',
      description: 'Real-time market sentiment analysis tool built with Next.js.'
    },
    {
      id: '2',
      title: 'DeFi Strategy Guide',
      url: 'https://example.com/guide',
      description: 'Comprehensive PDF guide on yield farming strategies.'
    }
  ],
  sharedTweets: [
    {
      id: '101',
      content: 'Just deployed the new smart contract for the DAO. Gas optimization reduced costs by 40%. Huge win for the community! 🚀 #Ethereum #Solidity',
      date: 'Oct 24, 2023',
      likes: 450,
      retweets: 89,
      authorName: 'CryptoWizard',
      authorHandle: 'wizard_crypto',
      authorAvatar: 'https://images.unsplash.com/photo-1628157588553-5eeea00af15c?q=80&w=200&auto=format&fit=crop'
    },
    {
      id: '102',
      content: 'Market structure is looking bullish on the 4H timeframe. Watch for a retest of the key support level at $28k before the next leg up.',
      date: 'Oct 22, 2023',
      likes: 1200,
      retweets: 340,
      authorName: 'CryptoWizard',
      authorHandle: 'wizard_crypto',
      authorAvatar: 'https://images.unsplash.com/photo-1628157588553-5eeea00af15c?q=80&w=200&auto=format&fit=crop'
    },
    {
      id: '103',
      content: 'Collaboration is key in this space. Shoutout to the design team for these amazing new assets.',
      date: 'Oct 20, 2023',
      likes: 230,
      retweets: 45,
      authorName: 'CryptoWizard',
      authorHandle: 'wizard_crypto',
      authorAvatar: 'https://images.unsplash.com/photo-1628157588553-5eeea00af15c?q=80&w=200&auto=format&fit=crop'
    }
  ]
};