import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
    ExternalLink, 
    ArrowLeft, 
    Share2, 
    Check, 
    Heart, 
    Repeat2, 
    Eye,
    MessageSquare,
    Users
} from 'lucide-react';
import { TweetCard } from '../components/TweetEmbed';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// X Logo Component
const XLogo = ({ size = 20 }) => (
    <img 
        src="/Xlogo.png" 
        alt="X" 
        style={{ width: size, height: size, objectFit: 'contain' }}
    />
);

// --- Status Badge Component ---
const StatusBadge = ({ status }) => {
    const statusConfig = {
        draft: { color: '#cbd5e1', bg: 'rgba(100, 116, 139, 0.2)', label: 'Draft' },
        submitted: { color: '#60a5fa', bg: 'rgba(59, 130, 246, 0.2)', label: 'Submitted' },
        pending_vote: { color: '#facc15', bg: 'rgba(234, 179, 8, 0.2)', label: 'Pending Vote' },
        approved: { color: '#4ade80', bg: 'rgba(34, 197, 94, 0.2)', label: 'Approved' },
        rejected: { color: '#f87171', bg: 'rgba(239, 68, 68, 0.2)', label: 'Rejected' },
        promoted: { color: '#c084fc', bg: 'rgba(168, 85, 247, 0.2)', label: 'Promoted' },
    };

    const config = statusConfig[status] || statusConfig.draft;

    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 16px',
                borderRadius: '9999px',
                backgroundColor: config.bg,
                border: `1px solid ${config.color}`,
                color: config.color,
                fontSize: '13px',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
            }}
        >
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: config.color }}></span>
            {config.label}
        </div>
    );
};

// --- Compact Stat Card for Sidebar ---
const CompactStatCard = ({ icon, value, label }) => (
    <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        padding: '16px',
        borderRadius: '12px',
        background: 'rgba(255, 255, 255, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        transition: 'background 0.2s',
    }}
    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
    onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'}
    >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#949494', marginBottom: '4px' }}>
            {icon}
            <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</span>
        </div>
        <span style={{ fontSize: '18px', fontWeight: 700, color: '#FFFFFF', fontFamily: 'monospace' }}>{value}</span>
    </div>
);

// --- Work Card Component (from portfoliodesignexample) ---
const WorkCard = ({ title, url, description }) => (
    <a 
        href={url} 
        target="_blank" 
        rel="noopener noreferrer"
        className="group"
        style={{
            background: '#1A1A23',
            borderRadius: '20px',
            border: '1px solid rgba(224, 223, 239, 0.1)',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            textDecoration: 'none',
            transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'rgba(237, 237, 255, 0.5)';
            e.currentTarget.style.boxShadow = '0 0 30px rgba(237, 237, 255, 0.05)';
        }}
        onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'rgba(224, 223, 239, 0.1)';
            e.currentTarget.style.boxShadow = 'none';
        }}
    >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <h4 style={{ 
                fontSize: '18px', 
                fontWeight: 700, 
                color: '#EDEDFF', 
                margin: 0,
                textDecoration: 'underline',
                textUnderlineOffset: '4px',
                textDecorationThickness: '1px',
            }}>{title}</h4>
            <ExternalLink size={20} style={{ color: '#10B981' }} />
        </div>
        {description && <p style={{ fontSize: '14px', color: '#949494', margin: 0 }}>{description}</p>}
        <span style={{ fontSize: '12px', color: 'rgba(148, 148, 148, 0.6)', marginTop: '8px', fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{url}</span>
    </a>
);

// --- Main Page Component ---
const PortfolioView = () => {
    const { userId } = useParams();
    const [portfolio, setPortfolio] = useState(null);
    const [twitterProfile, setTwitterProfile] = useState(null);
    const [tweetStats, setTweetStats] = useState(null);
    const [discordStats, setDiscordStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [linkCopied, setLinkCopied] = useState(false);

    const copyPortfolioLink = async () => {
        try {
            await navigator.clipboard.writeText(window.location.href);
            setLinkCopied(true);
            setTimeout(() => setLinkCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    useEffect(() => {
        fetchPortfolio();
    }, [userId]);

    const fetchPortfolio = async () => {
        try {
            setLoading(true);
            const res = await fetch(`${API_BASE}/api/portfolio/${userId}`);
            if (!res.ok) {
                throw new Error('Portfolio not found');
            }
            const data = await res.json();
            
            // Parse other_works if it's a JSON string
            if (data.other_works && typeof data.other_works === 'string') {
                try {
                    data.other_works = JSON.parse(data.other_works);
                } catch (e) {
                    data.other_works = [];
                }
            }
            
            setPortfolio(data);

            // Fetch Twitter profile (includes banner_url)
            if (data.twitter_handle) {
                try {
                    const twitterRes = await fetch(`${API_BASE}/api/twitter/profile/${data.twitter_handle}`);
                    if (twitterRes.ok) {
                        const twitterData = await twitterRes.json();
                        setTwitterProfile(twitterData);
                    }
                } catch (e) {
                    console.error('Failed to fetch Twitter profile:', e);
                }
            }

            // Fetch tweet stats
            try {
                const statsRes = await fetch(`${API_BASE}/api/twitter/portfolio/${userId}/stats`);
                if (statsRes.ok) {
                    const statsData = await statsRes.json();
                    setTweetStats(statsData);
                }
            } catch (e) {
                console.error('Failed to fetch tweet stats:', e);
            }

            // Fetch Discord user stats from messages.db
            try {
                const discordRes = await fetch(`${API_BASE}/api/user/${userId}/discord-stats`);
                if (discordRes.ok) {
                    const discordData = await discordRes.json();
                    setDiscordStats(discordData);
                }
            } catch (e) {
                console.error('Failed to fetch Discord stats:', e);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatNumber = (num) => {
        if (!num) return '0';
        return new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(num);
    };

    const glassCardStyle = {
        background: '#1A1A23',
        borderRadius: '20px',
        border: '1px solid rgba(224, 223, 239, 0.1)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        backdropFilter: 'blur(20px)',
    };

    if (loading) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ width: '40px', height: '40px', border: '3px solid var(--color-primary)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
                    <p style={{ color: 'var(--color-text-secondary)' }}>Loading portfolio...</p>
                </div>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    if (error || !portfolio) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px', background: 'var(--color-bg)' }}>
                <div style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
                    <div style={{ fontSize: '64px', marginBottom: '16px' }}>😕</div>
                    <h1 style={{ fontSize: '28px', marginBottom: '12px', color: 'var(--color-text)' }}>Portfolio Not Found</h1>
                    <p style={{ color: 'var(--color-text-secondary)', marginBottom: '24px' }}>
                        This portfolio doesn't exist or has been removed.
                    </p>
                    <Link to="/portfolios" style={{ color: 'var(--color-primary)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                        <ArrowLeft size={18} /> Back to Portfolios
                    </Link>
                </div>
            </div>
        );
    }

    const bannerUrl = twitterProfile?.banner_url;
    const otherWorks = Array.isArray(portfolio.other_works) ? portfolio.other_works : [];

    return (
        <div style={{ minHeight: '100vh', padding: '120px 20px 80px', background: 'var(--color-bg)', maxWidth: '1400px', margin: '0 auto' }}>
            
            {/* Navigation */}
            <nav style={{ marginBottom: '32px' }}>
                <Link 
                    to="/portfolios" 
                    style={{ 
                        display: 'inline-flex', 
                        alignItems: 'center', 
                        gap: '8px', 
                        color: 'var(--color-text-secondary)', 
                        textDecoration: 'none', 
                        fontSize: '14px',
                        fontWeight: 500,
                        transition: 'color 0.2s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-text)'}
                    onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-text-secondary)'}
                >
                    <span style={{ transition: 'transform 0.2s' }}><ArrowLeft size={16} /></span>
                    Back to Portfolios
                </Link>
            </nav>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '32px' }}>
                
                {/* Left Column - Main Content (8 cols) */}
                <div style={{ gridColumn: 'span 8', display: 'flex', flexDirection: 'column', gap: '32px' }}>
                    
                    {/* Header Card with Banner */}
                    <section style={{ ...glassCardStyle, padding: 0, overflow: 'hidden', position: 'relative' }}>
                        {/* Banner Image */}
                        <div style={{ height: '256px', width: '100%', position: 'relative', background: '#2a2a35' }}>
                            {bannerUrl ? (
                                <img 
                                    src={bannerUrl} 
                                    alt="Profile Banner" 
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                />
                            ) : (
                                <div style={{ width: '100%', height: '100%', background: 'linear-gradient(to right, #1e3a8a, #7c3aed, #1e293b)' }}></div>
                            )}
                            {/* Gradient overlay */}
                            <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: '96px', background: 'linear-gradient(to top, rgba(26, 26, 35, 0.8), transparent)' }}></div>
                        </div>

                        {/* Profile Info Section */}
                        <div style={{ padding: '0 32px 32px', position: 'relative' }}>
                            
                            <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                                
                                {/* Avatar (Overlapping) */}
                                <div style={{ position: 'relative', marginTop: '-64px', flexShrink: 0 }}>
                                    <div style={{ width: '128px', height: '128px', borderRadius: '50%', padding: '4px', background: '#1A1A23' }}>
                                        {twitterProfile?.profile_picture ? (
                                            <img 
                                                src={twitterProfile.profile_picture.replace('_normal', '_400x400')} 
                                                alt={portfolio.twitter_handle} 
                                                style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover', border: '4px solid #1A1A23' }}
                                            />
                                        ) : (
                                            <div style={{ 
                                                width: '100%', 
                                                height: '100%', 
                                                borderRadius: '50%', 
                                                border: '4px solid #1A1A23', 
                                                background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)', 
                                                display: 'flex', 
                                                alignItems: 'center', 
                                                justifyContent: 'center', 
                                                fontSize: '48px', 
                                                fontWeight: 700, 
                                                color: 'white' 
                                            }}>
                                                {(portfolio.twitter_handle || 'U').charAt(0).toUpperCase()}
                                            </div>
                                        )}
                                    </div>
                                    {/* Status Dot */}
                                    <div style={{ 
                                        position: 'absolute', 
                                        bottom: '8px', 
                                        right: '8px', 
                                        width: '24px', 
                                        height: '24px', 
                                        background: '#22c55e', 
                                        borderRadius: '50%', 
                                        border: '4px solid #1A1A23' 
                                    }} title={portfolio.status}></div>
                                </div>

                                {/* Desktop Actions */}
                                <div style={{ display: 'flex', flexGrow: 1, justifyContent: 'flex-end', paddingTop: '16px', gap: '12px', flexWrap: 'wrap' }}>
                                    <StatusBadge status={portfolio.status} />
                                    <button
                                        onClick={copyPortfolioLink}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '8px',
                                            padding: '8px 16px',
                                            borderRadius: '20px',
                                            background: linkCopied ? 'rgba(34, 197, 94, 0.2)' : '#2a2a35',
                                            color: linkCopied ? '#22c55e' : '#FFFFFF',
                                            border: '1px solid',
                                            borderColor: linkCopied ? '#22c55e' : 'rgba(255,255,255,0.05)',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s',
                                            fontWeight: 600,
                                            fontSize: '14px',
                                        }}
                                        onMouseEnter={(e) => !linkCopied && (e.currentTarget.style.background = '#343440')}
                                        onMouseLeave={(e) => !linkCopied && (e.currentTarget.style.background = '#2a2a35')}
                                    >
                                        {linkCopied ? 'Copied!' : 'Share'}
                                        {linkCopied ? <Check size={18} /> : <Share2 size={18} />}
                                    </button>
                                </div>
                            </div>

                            {/* Name and Details */}
                            <div style={{ marginTop: '12px' }}>
                                <h1 style={{ fontSize: '32px', fontWeight: 700, margin: '0 0 4px', letterSpacing: '-0.02em', color: '#FFFFFF' }}>
                                    {twitterProfile?.name || portfolio.twitter_handle || `User ${userId}`}
                                </h1>
                                
                                {portfolio.twitter_handle && (
                                    <a 
                                        href={`https://x.com/${portfolio.twitter_handle}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        style={{ 
                                            color: '#FFFFFF', 
                                            textDecoration: 'none', 
                                            display: 'inline-flex', 
                                            alignItems: 'center', 
                                            gap: '6px',
                                            fontWeight: 500,
                                            transition: 'opacity 0.2s'
                                        }}
                                        onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
                                        onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
                                    >
                                        <XLogo size={16} /> @{portfolio.twitter_handle}
                                    </a>
                                )}

                                {/* Metadata Grid */}
                                <div style={{ 
                                    marginTop: '20px', 
                                    display: 'flex', 
                                    flexWrap: 'wrap', 
                                    gap: '24px', 
                                    fontSize: '15px', 
                                    color: '#949494',
                                    borderTop: '1px solid rgba(255,255,255,0.05)',
                                    paddingTop: '20px'
                                }}>
                                    {twitterProfile?.followers && (
                                        <div>
                                            <span style={{ color: '#FFFFFF', fontWeight: 700 }}>{formatNumber(twitterProfile.followers)}</span> Followers
                                        </div>
                                    )}
                                    {portfolio.target_role && (
                                        <div>
                                            <span style={{ color: '#FFFFFF', fontWeight: 700, textTransform: 'capitalize' }}>{portfolio.target_role}</span> Guild
                                        </div>
                                    )}
                                    <div>
                                        Joined <span style={{ color: '#FFFFFF', fontWeight: 700 }}>{new Date(portfolio.created_at).toLocaleDateString()}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Contributions Section (Tweets with react-tweet embed) */}
                    {portfolio.tweets?.length > 0 && (
                        <section>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                                <div style={{ padding: '8px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '8px' }}>
                                    <XLogo size={24} />
                                </div>
                                <h3 style={{ fontSize: '20px', fontWeight: 700, margin: 0, color: '#FFFFFF' }}>Contributions</h3>
                            </div>
                            
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '24px' }}>
                                {portfolio.tweets.map((tweet, i) => (
                                    <TweetCard key={i} tweetUrl={tweet.tweet_url} useEmbed={true} />
                                ))}
                            </div>
                        </section>
                    )}
                </div>

                {/* Right Column - Sidebar (4 cols) */}
                <div style={{ gridColumn: 'span 4', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    
                    {/* Analytics Widget */}
                    {tweetStats && tweetStats.tweet_count > 0 && (
                        <section style={{ ...glassCardStyle, padding: '20px' }}>
                            <h3 style={{ 
                                fontSize: '18px', 
                                fontWeight: 700, 
                                margin: '0 0 16px',
                                fontFamily: 'Playfair Display, serif',
                                fontStyle: 'italic',
                                color: '#FFFFFF'
                            }}>
                                Analytics
                            </h3>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                                <CompactStatCard 
                                    icon={<Heart size={14} color="#ef4444" />} 
                                    value={formatNumber(tweetStats.total_likes)} 
                                    label="Likes" 
                                />
                                <CompactStatCard 
                                    icon={<Repeat2 size={14} color="#22c55e" />} 
                                    value={formatNumber(tweetStats.total_retweets)} 
                                    label="Retweets" 
                                />
                                <CompactStatCard 
                                    icon={<Eye size={14} color="#3b82f6" />} 
                                    value={formatNumber(tweetStats.total_views)} 
                                    label="Views" 
                                />
                                <CompactStatCard 
                                    icon={<XLogo size={14} />} 
                                    value={formatNumber(tweetStats.tweet_count)} 
                                    label="Tweets" 
                                />
                            </div>
                        </section>
                    )}

                    {/* Discord Stats */}
                    {discordStats && discordStats.message_count > 0 && (
                        <section style={{ ...glassCardStyle, padding: '20px' }}>
                            <h3 style={{ 
                                fontSize: '18px', 
                                fontWeight: 700, 
                                margin: '0 0 16px',
                                fontFamily: 'Playfair Display, serif',
                                fontStyle: 'italic',
                                color: '#FFFFFF'
                            }}>
                                Discord Activity
                            </h3>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                                <CompactStatCard 
                                    icon={<MessageSquare size={14} color="#a855f7" />} 
                                    value={formatNumber(discordStats.message_count)} 
                                    label="Messages" 
                                />
                                <CompactStatCard 
                                    icon={<Users size={14} color="#06b6d4" />} 
                                    value={formatNumber(discordStats.channels_active)} 
                                    label="Channels" 
                                />
                            </div>
                        </section>
                    )}

                    {/* Other Works */}
                    {otherWorks.length > 0 && (
                        <section style={{ position: 'sticky', top: '32px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                                <ExternalLink size={20} style={{ color: '#10B981' }} />
                                <h3 style={{ fontSize: '18px', fontWeight: 700, margin: 0, color: '#FFFFFF' }}>Other Works</h3>
                            </div>
                            
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                {otherWorks.map((work, i) => (
                                    <WorkCard 
                                        key={i}
                                        title={typeof work === 'string' ? 'Work Link' : (work.title || 'Work Link')}
                                        url={typeof work === 'string' ? work : work.url}
                                        description={typeof work === 'object' ? work.description : undefined}
                                    />
                                ))}
                            </div>
                        </section>
                    )}
                </div>
            </div>

            {/* Mobile responsive styles */}
            <style>{`
                @media (max-width: 1024px) {
                    div[style*="gridTemplateColumns: repeat(12, 1fr)"] {
                        grid-template-columns: 1fr !important;
                    }
                    div[style*="gridColumn: span 8"],
                    div[style*="gridColumn: span 4"] {
                        grid-column: span 1 !important;
                    }
                }
                @media (max-width: 768px) {
                    div[style*="gridTemplateColumns: repeat(2, 1fr)"] {
                        grid-template-columns: 1fr !important;
                    }
                }
            `}</style>
        </div>
    );
};

export default PortfolioView;
