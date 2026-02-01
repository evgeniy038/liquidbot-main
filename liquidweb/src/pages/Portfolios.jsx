import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Check, X, Clock, AlertCircle, User, Eye, Filter, Send, ChevronDown, Twitter, ExternalLink, Heart, Repeat2, MessageSquare, Link as LinkIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { GuildBadge } from '../components/GuildSelect';
import { TweetCard } from '../components/TweetEmbed';
import { StatsCard } from '../components/StatsCharts';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// X Logo Component
const XLogo = ({ size = 20 }) => (
    <img 
        src="/Xlogo.png" 
        alt="X" 
        style={{ width: size, height: size, objectFit: 'contain' }}
    />
);

// Roles allowed to review portfolios
const REVIEWER_ROLES = [
    '1449066131741737175', // Guild Leader
    '1447972806339067925', // Parliament
    '1436799852171235472', // Staff
    '1436233268134678600', // Automata
    '1436217207825629277', // Moderator
];

const STATUS_COLORS = {
    draft: { bg: 'rgba(100, 116, 139, 0.2)', color: '#94a3b8', label: 'Draft' },
    submitted: { bg: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', label: 'Under Review' },
    pending_vote: { bg: 'rgba(168, 85, 247, 0.2)', color: '#a855f7', label: 'Parliament Vote' },
    approved: { bg: 'rgba(34, 197, 94, 0.2)', color: '#22c55e', label: 'Approved' },
    promoted: { bg: 'rgba(34, 197, 94, 0.2)', color: '#22c55e', label: 'Promoted' },
    rejected: { bg: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', label: 'Rejected' },
};

// Portfolio Card Component with hover actions
const PortfolioCard = ({ portfolio, twitterProfile, canReview, onNavigate, onReview, cardStyle }) => {
    const [isHovered, setIsHovered] = useState(false);
    const [reviewing, setReviewing] = useState(false);

    const handleReviewAction = async (e, action) => {
        e.stopPropagation();
        setReviewing(true);
        await onReview(action, portfolio.discord_id);
        setReviewing(false);
    };

    const showActions = canReview && portfolio.status === 'submitted' && isHovered;

    return (
        <div 
            style={{ 
                ...cardStyle, 
                cursor: 'pointer',
                transition: 'all 0.2s',
                position: 'relative',
                borderColor: isHovered ? 'var(--color-primary)' : 'var(--color-badge-border)',
            }}
            onClick={onNavigate}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Hover Actions Overlay */}
            {showActions && (
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(19, 19, 24, 0.95)',
                    borderRadius: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '12px',
                    zIndex: 10,
                    padding: '20px',
                }}>
                    <span style={{ fontSize: '14px', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>
                        Vote on this portfolio
                    </span>
                    <div style={{ display: 'flex', gap: '12px', width: '100%' }}>
                        <button
                            onClick={(e) => handleReviewAction(e, 'reject')}
                            disabled={reviewing}
                            style={{
                                flex: 1,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                padding: '12px 20px',
                                borderRadius: '12px',
                                background: 'rgba(239, 68, 68, 0.2)',
                                color: '#ef4444',
                                border: '1px solid rgba(239, 68, 68, 0.3)',
                                cursor: reviewing ? 'not-allowed' : 'pointer',
                                fontSize: '14px',
                                fontWeight: 600,
                                transition: 'all 0.2s',
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.3)'}
                            onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'}
                        >
                            <X size={18} />
                            Reject
                        </button>
                        <button
                            onClick={(e) => handleReviewAction(e, 'approve')}
                            disabled={reviewing}
                            style={{
                                flex: 1,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                padding: '12px 20px',
                                borderRadius: '12px',
                                background: 'rgba(34, 197, 94, 0.2)',
                                color: '#22c55e',
                                border: '1px solid rgba(34, 197, 94, 0.3)',
                                cursor: reviewing ? 'not-allowed' : 'pointer',
                                fontSize: '14px',
                                fontWeight: 600,
                                transition: 'all 0.2s',
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(34, 197, 94, 0.3)'}
                            onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(34, 197, 94, 0.2)'}
                        >
                            <Check size={18} />
                            Approve
                        </button>
                    </div>
                    <button
                        onClick={(e) => { e.stopPropagation(); onNavigate(); }}
                        style={{
                            marginTop: '8px',
                            padding: '8px 16px',
                            borderRadius: '8px',
                            background: 'transparent',
                            color: 'var(--color-text-secondary)',
                            border: '1px solid var(--color-badge-border)',
                            cursor: 'pointer',
                            fontSize: '13px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                        }}
                    >
                        <Eye size={14} />
                        View Details
                    </button>
                </div>
            )}

            {/* Card Content */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                {twitterProfile?.profile_picture ? (
                    <img 
                        src={twitterProfile.profile_picture.replace('_normal', '_400x400')} 
                        alt="" 
                        style={{ width: '48px', height: '48px', borderRadius: '50%', border: '2px solid var(--color-badge-border)' }} 
                    />
                ) : (
                    <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid var(--color-badge-border)' }}>
                        <XLogo size={24} />
                    </div>
                )}
                <div style={{ flex: 1 }}>
                    <h3 style={{ margin: 0, fontSize: '16px' }}>{twitterProfile?.name || portfolio.twitter_handle || portfolio.username}</h3>
                    <p style={{ margin: 0, fontSize: '13px', color: 'var(--color-text-secondary)' }}>
                        {portfolio.target_role || 'No guild'}
                    </p>
                </div>
                <span style={{
                    padding: '4px 10px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 500,
                    background: STATUS_COLORS[portfolio.status]?.bg || 'rgba(100, 116, 139, 0.2)',
                    color: STATUS_COLORS[portfolio.status]?.color || '#94a3b8',
                }}>
                    {STATUS_COLORS[portfolio.status]?.label || portfolio.status}
                </span>
            </div>
            
            {portfolio.twitter_handle && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
                    <XLogo size={14} />
                    @{portfolio.twitter_handle}
                </div>
            )}
            
            <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    {portfolio.tweets?.length || 0} tweets
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                        {portfolio.submitted_at ? new Date(portfolio.submitted_at).toLocaleDateString() : 'Draft'}
                    </span>
                    <a
                        href={`/portfolios/${portfolio.discord_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '4px 8px',
                            borderRadius: '6px',
                            background: 'rgba(255,255,255,0.05)',
                            color: 'var(--color-primary)',
                            fontSize: '11px',
                            textDecoration: 'none',
                            border: '1px solid var(--color-badge-border)',
                        }}
                        title="Open portfolio in new tab"
                    >
                        <LinkIcon size={12} />
                        Link
                    </a>
                </div>
            </div>
        </div>
    );
};

const Portfolios = () => {
    const navigate = useNavigate();
    const { user, isAuthenticated, loading: authLoading, login } = useAuth();
    const [loading, setLoading] = useState(true);
    const [portfolios, setPortfolios] = useState([]);
    const [filter, setFilter] = useState('submitted');
    const [selectedPortfolio, setSelectedPortfolio] = useState(null);
    const [reviewing, setReviewing] = useState(false);
    const [reviewMessage, setReviewMessage] = useState(null);
    const [error, setError] = useState('');
    const [tweetStats, setTweetStats] = useState(null);
    const [loadingStats, setLoadingStats] = useState(false);
    const [twitterProfile, setTwitterProfile] = useState(null);
    const [twitterProfiles, setTwitterProfiles] = useState({});

    // Check if user can review portfolios
    const canReview = user?.roles?.some(role => REVIEWER_ROLES.includes(role)) || false;

    useEffect(() => {
        if (isAuthenticated) {
            fetchPortfolios();
        } else if (!authLoading) {
            setLoading(false);
        }
    }, [isAuthenticated, authLoading, filter]);

    const fetchPortfolios = async () => {
        setLoading(true);
        try {
            const url = filter === 'all' 
                ? `${API_BASE}/api/portfolio/list/all`
                : `${API_BASE}/api/portfolio/list/all?status=${filter}`;
            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                // Fetch Twitter profiles first, then show portfolios
                const profiles = await fetchAllTwitterProfiles(data);
                setTwitterProfiles(profiles);
                setPortfolios(data);
            }
        } catch (err) {
            console.error('Failed to fetch portfolios:', err);
            setError('Failed to load portfolios');
        } finally {
            setLoading(false);
        }
    };

    const fetchAllTwitterProfiles = async (portfolioList) => {
        const handles = portfolioList
            .filter(p => p.twitter_handle)
            .map(p => p.twitter_handle);
        
        const uniqueHandles = [...new Set(handles)];
        
        // Fetch all profiles in parallel
        const results = await Promise.all(
            uniqueHandles.map(async (handle) => {
                try {
                    const res = await fetch(`${API_BASE}/api/twitter/profile/${handle}`);
                    if (res.ok) {
                        const data = await res.json();
                        return { handle, data };
                    }
                } catch (err) {
                    console.error(`Failed to fetch twitter profile for ${handle}:`, err);
                }
                return null;
            })
        );
        
        // Convert to object
        const profiles = {};
        results.filter(Boolean).forEach(({ handle, data }) => {
            profiles[handle] = data;
        });
        return profiles;
    };

    const fetchTweetStats = async (discordId) => {
        setLoadingStats(true);
        setTweetStats(null);
        try {
            const res = await fetch(`${API_BASE}/api/twitter/portfolio/${discordId}/stats`);
            if (res.ok) {
                const data = await res.json();
                setTweetStats(data);
            }
        } catch (err) {
            console.error('Failed to fetch tweet stats:', err);
        } finally {
            setLoadingStats(false);
        }
    };

    const fetchTwitterProfile = async (twitterHandle) => {
        if (!twitterHandle) return;
        try {
            const res = await fetch(`${API_BASE}/api/twitter/profile/${twitterHandle}`);
            if (res.ok) {
                const data = await res.json();
                setTwitterProfile(data);
            }
        } catch (err) {
            console.error('Failed to fetch twitter profile:', err);
        }
    };

    const handleSelectPortfolio = (portfolio) => {
        setSelectedPortfolio(portfolio);
        setTweetStats(null);
        // Use cached Twitter profile instead of re-fetching
        if (portfolio?.twitter_handle && twitterProfiles[portfolio.twitter_handle]) {
            setTwitterProfile(twitterProfiles[portfolio.twitter_handle]);
        } else {
            setTwitterProfile(null);
            if (portfolio?.twitter_handle) {
                fetchTwitterProfile(portfolio.twitter_handle);
            }
        }
        if (portfolio?.discord_id) {
            fetchTweetStats(portfolio.discord_id);
        }
    };

    const handleCloseModal = () => {
        setSelectedPortfolio(null);
        setTweetStats(null);
        setTwitterProfile(null);
        setReviewMessage(null);
    };

    const handleReview = async (action, discordId = null) => {
        const targetDiscordId = discordId || selectedPortfolio?.discord_id;
        if (!targetDiscordId) return;
        
        setReviewing(true);
        setReviewMessage(null);
        
        try {
            const res = await fetch(`${API_BASE}/api/portfolio/review`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    discord_id: targetDiscordId,
                    action,
                    reviewer_id: user?.id || 'Unknown',
                    feedback: '',
                }),
            });
            
            const data = await res.json();
            
            if (data.success) {
                setReviewMessage({
                    type: 'success',
                    text: action === 'approve' 
                        ? '✅ Portfolio sent to Parliament for voting!' 
                        : action === 'reject'
                        ? '❌ Portfolio rejected'
                        : '📝 Requested changes from user',
                });
                fetchPortfolios();
                if (selectedPortfolio) {
                    setTimeout(() => setSelectedPortfolio(null), 2000);
                }
            } else {
                setReviewMessage({ type: 'error', text: data.detail || 'Failed to review' });
            }
        } catch (err) {
            setReviewMessage({ type: 'error', text: 'Failed to submit review' });
        } finally {
            setReviewing(false);
        }
    };

    const cardStyle = {
        background: 'var(--color-card-bg)',
        borderRadius: '16px',
        padding: '20px',
        border: '1px solid var(--color-badge-border)',
        backdropFilter: 'blur(20px)',
    };

    if (loading || authLoading) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ width: '40px', height: '40px', border: '3px solid var(--color-primary)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
                    <p style={{ color: 'var(--color-text-secondary)' }}>Loading portfolios...</p>
                </div>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    if (!isAuthenticated) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px 40px', background: 'var(--color-bg)' }}>
                <div className="container" style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
                    <div style={{
                        margin: '0 auto 24px',
                        width: '80px',
                        height: '80px',
                        background: 'linear-gradient(135deg, rgba(237, 237, 255, 0.1) 0%, rgba(224, 223, 239, 0.05) 100%)',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '1px solid var(--color-badge-border)'
                    }}>
                        <FileText size={40} style={{ color: 'var(--color-primary)' }} />
                    </div>
                    <h1 style={{
                        fontSize: '48px',
                        margin: '0 0 16px',
                        fontWeight: 700,
                        letterSpacing: '-0.02em',
                        background: 'linear-gradient(180deg, #FFFFFF 0%, #949494 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                    }}>
                        Portfolio Review
                    </h1>
                    <p style={{ color: 'var(--color-text-secondary)', margin: 0, marginBottom: '32px', fontSize: '18px', maxWidth: '600px', marginInline: 'auto' }}>
                        Sign in to review portfolios
                    </p>
                    <button onClick={login} className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', padding: '14px 28px', fontSize: '15px' }}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
                        </svg>
                        Sign in with Discord
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="container" style={{ padding: '120px 20px 40px', maxWidth: '1200px', margin: '0 auto' }}>
            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: '60px' }}>
                <div style={{
                    margin: '0 auto 24px',
                    width: '80px',
                    height: '80px',
                    background: 'linear-gradient(135deg, rgba(237, 237, 255, 0.1) 0%, rgba(224, 223, 239, 0.05) 100%)',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid var(--color-badge-border)'
                }}>
                    <FileText size={40} style={{ color: 'var(--color-primary)' }} />
                </div>
                <h1 style={{
                    fontSize: '48px',
                    margin: '0 0 16px',
                    fontWeight: 700,
                    letterSpacing: '-0.02em',
                    background: 'linear-gradient(180deg, #FFFFFF 0%, #949494 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                }}>
                    Portfolio Review
                </h1>
                <p style={{ color: 'var(--color-text-secondary)', margin: 0, fontSize: '18px', maxWidth: '600px', marginInline: 'auto' }}>
                    Review and approve submitted portfolios for Parliament voting
                </p>
            </div>

            {/* Filter Tabs */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '32px', justifyContent: 'center' }}>
                <div style={{
                    background: 'var(--color-card-bg)',
                    padding: '6px',
                    borderRadius: '99px',
                    border: '1px solid var(--color-badge-border)',
                    display: 'inline-flex'
                }}>
                    {['submitted', 'pending_vote', 'all'].map((status) => (
                        <button
                            key={status}
                            className="btn"
                            style={{
                                padding: '8px 20px',
                                fontSize: '14px',
                                background: filter === status ? 'var(--color-primary)' : 'transparent',
                                color: filter === status ? 'var(--color-primary-text)' : 'var(--color-text-secondary)',
                                borderRadius: '99px',
                                boxShadow: filter === status ? '0 2px 10px rgba(237, 237, 255, 0.2)' : 'none',
                            }}
                            onClick={() => setFilter(status)}
                        >
                            {status === 'submitted' ? 'Pending Review' : 
                             status === 'pending_vote' ? 'In Voting' : 'All'}
                        </button>
                    ))}
                </div>
            </div>

            {/* Portfolio Grid */}
            {portfolios.length === 0 ? (
                <div style={{ ...cardStyle, textAlign: 'center', padding: '60px 20px' }}>
                    <FileText size={48} style={{ color: 'var(--color-text-secondary)', marginBottom: '16px' }} />
                    <p style={{ color: 'var(--color-text-secondary)' }}>No portfolios found</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(350px, 100%), 1fr))', gap: '20px' }}>
                    {portfolios.map((portfolio) => (
                        <PortfolioCard 
                            key={portfolio.id}
                            portfolio={portfolio}
                            twitterProfile={twitterProfiles[portfolio.twitter_handle]}
                            canReview={canReview}
                            onNavigate={() => navigate(`/portfolios/${portfolio.discord_id}`)}
                            onReview={handleReview}
                            cardStyle={cardStyle}
                        />
                    ))}
                </div>
            )}

            {/* Portfolio Detail Modal */}
            {selectedPortfolio && (
                <div 
                    style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(0, 0, 0, 0.8)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 1000,
                        padding: '20px',
                    }}
                    onClick={handleCloseModal}
                >
                    <div 
                        style={{
                            ...cardStyle,
                            maxWidth: '1100px',
                            width: '100%',
                            maxHeight: '90vh',
                            overflow: 'auto',
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Modal Header */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                            {/* Twitter Avatar */}
                            {twitterProfile?.profile_picture ? (
                                <img 
                                    src={twitterProfile.profile_picture.replace('_normal', '_400x400')} 
                                    alt="" 
                                    style={{ width: '64px', height: '64px', borderRadius: '50%', border: '2px solid #1DA1F2' }} 
                                />
                            ) : (
                                <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid var(--color-badge-border)' }}>
                                    <XLogo size={32} />
                                </div>
                            )}
                            <div style={{ flex: 1 }}>
                                <h2 style={{ margin: 0 }}>{twitterProfile?.name || selectedPortfolio.twitter_handle || selectedPortfolio.username}</h2>
                                {twitterProfile?.username && (
                                    <a 
                                        href={`https://twitter.com/${twitterProfile.username}`} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        style={{ fontSize: '14px', color: '#1DA1F2', textDecoration: 'none' }}
                                    >
                                        @{twitterProfile.username}
                                    </a>
                                )}
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '8px', flexWrap: 'wrap' }}>
                                    <span style={{
                                        padding: '4px 12px',
                                        borderRadius: '12px',
                                        fontSize: '13px',
                                        fontWeight: 500,
                                        background: STATUS_COLORS[selectedPortfolio.status]?.bg,
                                        color: STATUS_COLORS[selectedPortfolio.status]?.color,
                                    }}>
                                        {STATUS_COLORS[selectedPortfolio.status]?.label}
                                    </span>
                                    {selectedPortfolio.target_role && (
                                        <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
                                            Guild: {selectedPortfolio.target_role}
                                        </span>
                                    )}
                                    {twitterProfile?.followers > 0 && (
                                        <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                            <XLogo size={14} />
                                            {twitterProfile.followers.toLocaleString()} followers
                                        </span>
                                    )}
                                </div>
                            </div>
                            <button 
                                onClick={handleCloseModal}
                                style={{ background: 'transparent', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer', padding: '8px' }}
                            >
                                <X size={24} />
                            </button>
                            <a
                                href={`/portfolios/${selectedPortfolio.discord_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '6px',
                                    padding: '8px 14px',
                                    borderRadius: '8px',
                                    background: 'rgba(255,255,255,0.05)',
                                    color: 'var(--color-primary)',
                                    fontSize: '13px',
                                    textDecoration: 'none',
                                    border: '1px solid var(--color-badge-border)',
                                    fontWeight: 500,
                                }}
                                title="Open full portfolio page"
                            >
                                <ExternalLink size={14} />
                                View Page
                            </a>
                        </div>

                        {/* Twitter Stats Section */}
                        {tweetStats && tweetStats.tweet_count > 0 && (
                            <div style={{ marginBottom: '24px' }}>
                                <h3 style={{ margin: '0 0 16px', fontSize: '16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <XLogo size={18} />
                                    X Engagement
                                </h3>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                                    <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px', textAlign: 'center' }}>
                                        <Heart size={20} style={{ color: '#ef4444', marginBottom: '8px' }} />
                                        <div style={{ fontSize: '20px', fontWeight: 700 }}>{(tweetStats.total_likes || 0).toLocaleString()}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Likes</div>
                                    </div>
                                    <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px', textAlign: 'center' }}>
                                        <Repeat2 size={20} style={{ color: '#22c55e', marginBottom: '8px' }} />
                                        <div style={{ fontSize: '20px', fontWeight: 700 }}>{(tweetStats.total_retweets || 0).toLocaleString()}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Retweets</div>
                                    </div>
                                    <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px', textAlign: 'center' }}>
                                        <Eye size={20} style={{ color: '#3b82f6', marginBottom: '8px' }} />
                                        <div style={{ fontSize: '20px', fontWeight: 700 }}>{(tweetStats.total_views || 0).toLocaleString()}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Views</div>
                                    </div>
                                    <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px', textAlign: 'center' }}>
                                        <XLogo size={20} />
                                        <div style={{ fontSize: '20px', fontWeight: 700, marginTop: '8px' }}>{tweetStats.tweet_count || 0}</div>
                                        <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Tweets</div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {loadingStats && (
                            <div style={{ marginBottom: '24px', padding: '20px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                                Loading Twitter stats...
                            </div>
                        )}

                        {/* Portfolio Content */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                            {selectedPortfolio.twitter_handle && (
                                <div>
                                    <label style={{ fontSize: '12px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                        Twitter/X
                                    </label>
                                    <a 
                                        href={`https://x.com/${selectedPortfolio.twitter_handle}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-primary)', marginTop: '4px' }}
                                    >
                                        <XLogo size={16} />
                                        @{selectedPortfolio.twitter_handle}
                                        <ExternalLink size={14} />
                                    </a>
                                </div>
                            )}

                            {/* Tweet Embeds from API */}
                            {tweetStats?.tweets?.length > 0 && (
                                <div>
                                    <label style={{ fontSize: '12px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px', display: 'block' }}>
                                        Tweets ({tweetStats.tweets.length})
                                    </label>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(300px, 100%), 1fr))', gap: '16px' }}>
                                        {tweetStats.tweets.slice(0, 4).map((tweet, idx) => (
                                            <TweetCard key={idx} tweetUrl={tweet.url} useEmbed={true} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Fallback to portfolio tweets if no stats */}
                            {!tweetStats?.tweets?.length && selectedPortfolio.tweets?.length > 0 && (
                                <div>
                                    <label style={{ fontSize: '12px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px', display: 'block' }}>
                                        Shared Tweets ({selectedPortfolio.tweets.length})
                                    </label>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(300px, 100%), 1fr))', gap: '16px' }}>
                                        {selectedPortfolio.tweets.slice(0, 4).map((tweet, idx) => (
                                            <TweetCard key={idx} tweetUrl={tweet.tweet_url} useEmbed={true} />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Review Message */}
                        {reviewMessage && (
                            <div style={{
                                marginTop: '20px',
                                padding: '12px 16px',
                                borderRadius: '8px',
                                background: reviewMessage.type === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                                color: reviewMessage.type === 'success' ? '#22c55e' : '#ef4444',
                            }}>
                                {reviewMessage.text}
                            </div>
                        )}

                        {/* Review Actions - Only for authorized roles */}
                        {selectedPortfolio.status === 'submitted' && canReview && (
                            <div style={{ 
                                display: 'flex', 
                                gap: '12px', 
                                marginTop: '24px', 
                                paddingTop: '20px', 
                                borderTop: '1px solid var(--color-badge-border)' 
                            }}>
                                <button
                                    className="btn"
                                    style={{ 
                                        flex: 1, 
                                        background: 'rgba(239, 68, 68, 0.2)', 
                                        color: '#ef4444',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '8px',
                                    }}
                                    onClick={() => handleReview('reject')}
                                    disabled={reviewing}
                                >
                                    <X size={18} />
                                    Reject
                                </button>
                                <button
                                    className="btn"
                                    style={{ 
                                        flex: 1, 
                                        background: 'rgba(251, 191, 36, 0.2)', 
                                        color: '#fbbf24',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '8px',
                                    }}
                                    onClick={() => handleReview('request_changes')}
                                    disabled={reviewing}
                                >
                                    <AlertCircle size={18} />
                                    Request Changes
                                </button>
                                <button
                                    className="btn btn-primary"
                                    style={{ 
                                        flex: 1,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '8px',
                                    }}
                                    onClick={() => handleReview('approve')}
                                    disabled={reviewing}
                                >
                                    <Check size={18} />
                                    {reviewing ? 'Sending...' : 'Approve → Parliament'}
                                </button>
                            </div>
                        )}

                        {/* Message for non-reviewers */}
                        {selectedPortfolio.status === 'submitted' && !canReview && (
                            <div style={{ 
                                marginTop: '24px', 
                                paddingTop: '20px', 
                                borderTop: '1px solid var(--color-badge-border)',
                                textAlign: 'center',
                                color: 'var(--color-text-secondary)',
                                fontSize: '14px',
                            }}>
                                Only Guild Leaders, Parliament members, and Moderators can review portfolios.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Portfolios;
