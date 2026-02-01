import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Portfolio } from '../types';
import { MOCK_PORTFOLIO } from '../constants';
import StatusBadge from './StatusBadge';
import { 
  IconArrowLeft, 
  IconShare, 
  IconTwitter, 
  IconHeart, 
  IconRepeat, 
  IconEye, 
  IconExternalLink,
  IconMessage
} from './Icons';

// --- Sub-components ---

// Redesigned Compact Stat Card for Sidebar
const CompactStatCard: React.FC<{
  icon: React.ReactNode;
  value: string | number;
  label: string;
}> = ({ icon, value, label }) => (
  <div className="flex flex-col justify-center p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
    <div className="flex items-center gap-2 text-secondary mb-1">
      {React.isValidElement(icon) 
        ? React.cloneElement(icon as React.ReactElement<{ size?: number }>, { size: 14 })
        : icon}
      <span className="text-[10px] font-bold uppercase tracking-wider">{label}</span>
    </div>
    <span className="text-lg font-bold text-white font-mono">{value}</span>
  </div>
);

const TweetCard: React.FC<{
  tweet: Portfolio['sharedTweets'][0];
}> = ({ tweet }) => (
  <div className="glass-card flex flex-col h-full rounded-[20px] overflow-hidden hover:border-[#1DA1F2]/30 transition-colors duration-300">
    <div className="flex justify-between items-start mb-4">
      <div className="flex gap-3">
        <img 
          src={tweet.authorAvatar} 
          alt={tweet.authorName} 
          className="w-10 h-10 rounded-full object-cover border border-[#1DA1F2]/20"
        />
        <div className="flex flex-col">
          <span className="font-bold text-white leading-tight">{tweet.authorName}</span>
          <span className="text-sm text-secondary">@{tweet.authorHandle}</span>
        </div>
      </div>
      <IconTwitter size={20} color="#1DA1F2" />
    </div>
    
    <p className="text-gray-200 text-[15px] leading-relaxed mb-4 flex-grow">
      {tweet.content}
    </p>

    <div className="flex flex-col gap-3 mt-auto">
      <div className="text-xs text-secondary border-b border-[rgba(255,255,255,0.05)] pb-3">
        {tweet.date}
      </div>
      <div className="flex gap-6 text-secondary text-sm font-medium">
         <div className="flex items-center gap-2 group cursor-pointer hover:text-[#ef4444] transition-colors">
            <IconHeart color={undefined} /> 
            <span className="group-hover:text-[#ef4444]">{tweet.likes}</span>
         </div>
         <div className="flex items-center gap-2 group cursor-pointer hover:text-[#22c55e] transition-colors">
            <IconRepeat color={undefined} />
            <span className="group-hover:text-[#22c55e]">{tweet.retweets}</span>
         </div>
         <div className="flex items-center gap-2 group cursor-pointer hover:text-[#3b82f6] transition-colors">
            <IconMessage />
            <span>Reply</span>
         </div>
      </div>
    </div>
  </div>
);

const WorkCard: React.FC<{
  title: string;
  url: string;
  description?: string;
}> = ({ title, url, description }) => (
  <a 
    href={url} 
    target="_blank" 
    rel="noopener noreferrer"
    className="group glass-card p-6 flex flex-col gap-2 rounded-[20px] transition-all hover:border-primary/50 hover:shadow-[0_0_30px_rgba(237,237,255,0.05)]"
  >
    <div className="flex justify-between items-start">
      <h4 className="text-lg font-bold text-primary group-hover:underline underline-offset-4 decoration-1">{title}</h4>
      <IconExternalLink />
    </div>
    {description && <p className="text-sm text-secondary">{description}</p>}
    <span className="text-xs text-secondary/60 mt-2 truncate font-mono">{url}</span>
  </a>
);

// --- Main Page Component ---

const PortfolioPage: React.FC = () => {
  const { discordId } = useParams<{ discordId: string }>();
  const portfolio = MOCK_PORTFOLIO;
  const [copied, setCopied] = useState(false);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(num);
  };

  return (
    <div className="min-h-screen pb-20 px-4 sm:px-6 md:px-8 max-w-7xl mx-auto pt-8">
      
      {/* 1. Navigation */}
      <nav className="mb-8">
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-secondary hover:text-white transition-colors text-[14px] font-medium group"
        >
          <span className="group-hover:-translate-x-1 transition-transform"><IconArrowLeft /></span>
          Back to Portfolios
        </Link>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column (Main Info) */}
        <div className="lg:col-span-8 flex flex-col gap-8">
          
          {/* 2. Header Card */}
          <section className="glass-card relative overflow-hidden rounded-[20px] p-0">
             {/* Banner Image */}
             <div className="h-48 md:h-64 w-full relative bg-[#2a2a35]">
               {portfolio.bannerUrl ? (
                 <img 
                   src={portfolio.bannerUrl} 
                   alt="Profile Banner" 
                   className="w-full h-full object-cover"
                 />
               ) : (
                 <div className="w-full h-full bg-gradient-to-r from-blue-900 via-purple-900 to-slate-900"></div>
               )}
               {/* Gradient overlay for text readability at bottom of banner (optional) */}
               <div className="absolute bottom-0 left-0 w-full h-24 bg-gradient-to-t from-[#1A1A23]/80 to-transparent"></div>
             </div>

             {/* Profile Info Section */}
             <div className="px-6 pb-6 md:px-8 md:pb-8 relative">
               
               <div className="flex flex-col md:flex-row gap-4 items-start">
                 
                 {/* Avatar (Overlapping) */}
                 <div className="relative -mt-[64px] shrink-0">
                    <div className="w-32 h-32 rounded-full p-1 bg-[#1A1A23]">
                      {portfolio.avatarUrl ? (
                        <img 
                          src={portfolio.avatarUrl} 
                          alt={portfolio.username} 
                          className="w-full h-full rounded-full object-cover border-4 border-[#1A1A23]"
                        />
                      ) : (
                        <div className="w-full h-full rounded-full border-4 border-[#1A1A23] bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-4xl font-bold text-white">
                          {portfolio.username.charAt(0)}
                        </div>
                      )}
                    </div>
                    {/* Status Dot */}
                    <div className="absolute bottom-2 right-2 w-6 h-6 bg-green-500 rounded-full border-4 border-[#1A1A23]" title={portfolio.status}></div>
                 </div>

                 {/* Top Right Actions (Desktop) - Positioned relative to flex container */}
                 <div className="hidden md:flex flex-grow justify-end pt-4 gap-3">
                    <StatusBadge status={portfolio.status} />
                    <button 
                         onClick={handleShare}
                         className="flex items-center gap-2 bg-[#2a2a35] hover:bg-[#343440] text-white px-4 py-2 rounded-[20px] transition-all text-sm font-semibold border border-white/5 active:scale-95"
                       >
                         {copied ? 'Copied!' : 'Share'}
                         <IconShare />
                    </button>
                 </div>
               </div>

               {/* Name and Details */}
               <div className="mt-3">
                  <div className="flex flex-col gap-1">
                    <h1 className="text-3xl font-bold text-white tracking-tight">{portfolio.username}</h1>
                    
                    {portfolio.twitterHandle && (
                      <a 
                        href={`https://twitter.com/${portfolio.twitterHandle}`} 
                        target="_blank" 
                        rel="noreferrer"
                        className="text-[#1DA1F2] hover:text-[#1a91da] font-medium inline-flex items-center gap-1 w-fit"
                      >
                        <IconTwitter size={16} /> @{portfolio.twitterHandle}
                      </a>
                    )}
                  </div>

                  {/* Metadata Grid */}
                  <div className="mt-5 flex flex-wrap gap-y-2 gap-x-6 text-[15px] text-secondary border-t border-white/5 pt-5">
                      <div className="flex items-center gap-2">
                         <span className="text-white font-bold">{formatNumber(portfolio.followersCount)}</span> Followers
                      </div>
                      <div className="flex items-center gap-2">
                         <span className="text-white font-bold capitalize">{portfolio.targetGuild}</span> Guild
                      </div>
                      <div className="flex items-center gap-2">
                         Joined <span className="text-white font-bold">{new Date(portfolio.createdAt).toLocaleDateString()}</span>
                      </div>
                  </div>

                  {/* Mobile Actions (Visible only on small screens) */}
                  <div className="flex md:hidden items-center gap-3 mt-6">
                     <StatusBadge status={portfolio.status} />
                     <button 
                       onClick={handleShare}
                       className="flex-grow flex justify-center items-center gap-2 bg-[#2a2a35] hover:bg-[#343440] text-white px-4 py-2 rounded-[20px] transition-all text-sm font-semibold border border-white/5 active:scale-95"
                     >
                       {copied ? 'Copied!' : 'Share'}
                       <IconShare />
                     </button>
                  </div>

               </div>
             </div>
          </section>

          {/* 3. Shared Tweets (Moved up to replace Analytics in main column) */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-[#1DA1F2]/10 rounded-lg">
                <IconTwitter color="#1DA1F2" size={24} />
              </div>
              <h3 className="text-xl font-bold text-white">Shared Tweets</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {portfolio.sharedTweets.map(tweet => (
                <TweetCard key={tweet.id} tweet={tweet} />
              ))}
            </div>
          </section>

        </div>

        {/* Right Column (Sidebar) */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          
          {/* 4. Compact Analytics Widget (New Location) */}
          <section className="glass-card p-5 rounded-[20px]">
             <h3 className="text-lg font-bold text-white mb-4 font-playfair italic">Analytics</h3>
             <div className="grid grid-cols-2 gap-3">
               <CompactStatCard 
                 icon={<IconHeart color="#ef4444" />} 
                 value={formatNumber(portfolio.stats.likes)} 
                 label="Likes" 
               />
               <CompactStatCard 
                 icon={<IconRepeat color="#22c55e" />} 
                 value={formatNumber(portfolio.stats.retweets)} 
                 label="Retweets" 
               />
               <CompactStatCard 
                 icon={<IconEye color="#3b82f6" />} 
                 value={formatNumber(portfolio.stats.views)} 
                 label="Views" 
               />
               <CompactStatCard 
                 icon={<IconTwitter color="#1DA1F2" />} 
                 value={formatNumber(portfolio.stats.tweetsCount)} 
                 label="Tweets" 
               />
             </div>
          </section>

          {/* 5. Other Works */}
          {portfolio.otherWorks.length > 0 && (
            <section className="sticky top-8">
              <div className="flex items-center gap-3 mb-4">
                 <IconExternalLink />
                 <h3 className="text-lg font-bold text-white">Other Works</h3>
              </div>
              
              <div className="flex flex-col gap-4">
                {portfolio.otherWorks.map(work => (
                  <WorkCard 
                    key={work.id} 
                    title={work.title} 
                    url={work.url} 
                    description={work.description} 
                  />
                ))}
              </div>
            </section>
          )}

        </div>

      </div>
    </div>
  );
};

export default PortfolioPage;