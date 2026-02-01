# Changes delivered by Codex

This file contains the full contents of every file that was changed during the UI fixes.

## liquidweb/src/components/Hero.jsx

**Path**: `liquidweb/src/components/Hero.jsx`

```jsx
import React from 'react';

const Hero = () => {
    const badgeStyle = {
        background: 'var(--color-bg)',
        boxShadow: 'inset 1.2px 0.9px 2.7px 0px var(--color-badge-shadow)',
        borderRadius: '5px',
        padding: '5px 10px',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        color: 'var(--color-text)',
        fontFamily: '"Saans", "Inter", sans-serif',
        fontSize: '15px',
        fontWeight: 500,
        whiteSpace: 'nowrap',
        border: '1px solid var(--color-badge-border)'
    };

    const profileCardStyle = {
        background: 'var(--color-card-bg)',
        padding: '10px 10px 15px 10px',
        borderRadius: '12px',
        border: '1px solid var(--color-badge-border)',
        boxShadow: '0 10px 30px rgba(0,0,0,0.1)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px',
        width: '140px'
    };

    const profileNameStyle = {
        color: 'var(--color-text)',
        fontSize: '12px',
        fontWeight: 600,
        margin: 0
    };

    const profilePointsStyle = {
        color: 'var(--color-text-secondary)',
        fontSize: '10px',
        margin: 0
    };

    return (
        <section style={{
            position: 'relative',
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
            backgroundColor: 'var(--color-bg)',
        }}>
            {/* Text Container - Replaced with SVG */}
            <div
                className="hero-image-wrap"
                style={{
                    position: 'relative',
                    zIndex: 10,
                    width: '100%',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center'
                }}
            >
                <img
                    src="/images/community.svg"
                    alt="Liquid Community"
                    className="hero-image"
                    style={{
                        width: '100%',
                        maxWidth: '1400px',
                        height: 'auto',
                        display: 'block',
                        margin: '0 auto',
                        filter: 'var(--filter-invert, none)' /* For dark mode SVG handling if needed, though usually SVG paths are colored */
                    }}
                />
            </div>

            <style>{`
                 /* Responsive Image adjustments via CSS for cleaner handling than inline */
                 .hero-image-wrap {
                    width: 100%;
                    max-width: 1300px;
                    margin: 0 auto;
                    padding: 0 20px;
                    box-sizing: border-box;
                 }
                 .hero-image {
                    min-width: 0 !important; /* Override inline min-width if any */
                    width: 100% !important;
                    max-width: 100% !important;
                    height: auto;
                    object-fit: contain;
                    transform: none !important;
                 }
                 @media (min-width: 768px) {
                    .hero-image-wrap {
                        padding: 0 24px;
                    }
                 }
                 @media (min-width: 1200px) {
                    .hero-image-wrap {
                        padding: 0 32px;
                    }
                 }
                 [data-theme='light'] .hero-image {
                    filter: invert(1); /* Invert the white SVG text to black for light mode */
                 }
            `}</style>

        </section>
    );
};

export default Hero;
```

## liquidweb/src/components/Navbar.jsx

**Path**: `liquidweb/src/components/Navbar.jsx`

```jsx
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
    const [isMenuOpen, setIsMenuOpen] = React.useState(false);
    const location = useLocation();
    const { user, loading, login, logout, isAuthenticated } = useAuth();

    React.useEffect(() => {
        setIsMenuOpen(false);
    }, [location.pathname]);

    const isActive = (path) => location.pathname === path;

    const links = [
        { to: '/leaderboard', label: 'Leaderboard' },
        { to: '/portfolio', label: 'Portfolio' },
        { to: '/portfolios', label: 'Review' },
        { to: '/stats', label: 'Stats' },
    ];

    const navLinks = (
        <>
            {links.map((link) => (
                <Link
                    key={link.to}
                    to={link.to}
                    className="nav-link"
                    data-active={isActive(link.to) ? 'true' : 'false'}
                >
                    {link.label}
                </Link>
            ))}
        </>
    );

    const authControls = loading ? (
        <div style={{ width: '100px' }} />
    ) : isAuthenticated ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Link to="/portfolio" style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none' }}>
                {user.avatar_url ? (
                    <img
                        src={user.avatar_url}
                        alt={user.username}
                        style={{
                            width: '36px',
                            height: '36px',
                            borderRadius: '50%',
                            border: '2px solid var(--color-primary)',
                        }}
                    />
                ) : (
                    <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '50%',
                        background: 'var(--color-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: 600,
                        fontSize: '14px',
                    }}>
                        {user.username?.charAt(0).toUpperCase()}
                    </div>
                )}
                <span style={{ color: 'var(--color-text)', fontWeight: 500 }}>
                    {user.username}
                </span>
            </Link>
            <button
                onClick={logout}
                style={{
                    background: 'transparent',
                    border: '1px solid var(--color-badge-border)',
                    color: 'var(--color-text-secondary)',
                    padding: '8px 16px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                    e.target.style.borderColor = 'var(--color-primary)';
                    e.target.style.color = 'var(--color-primary)';
                }}
                onMouseLeave={(e) => {
                    e.target.style.borderColor = 'var(--color-badge-border)';
                    e.target.style.color = 'var(--color-text-secondary)';
                }}
            >
                Logout
            </button>
        </div>
    ) : (
        <button
            onClick={login}
            className="btn btn-primary"
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
            }}
        >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
            </svg>
            Login with Discord
        </button>
    );

    return (
        <nav
            className={`navbar ${isMenuOpen ? 'is-open' : ''}`}
            style={{
                padding: '20px 40px',
                position: 'fixed',
                width: '100%',
                top: '0',
                zIndex: 40,
                background: 'var(--color-bg)',
                borderBottom: '1px solid var(--color-badge-border)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'stretch',
            }}
        >
            <div className="nav-row">
                <div className="logo">
                    <Link to="/">
                        <img
                            src="/images/logo.png"
                            alt="Liquid"
                            style={{ width: '120px', display: 'block' }}
                        />
                    </Link>
                </div>

                <div className="center-links desktop-only">
                    {navLinks}
                </div>

                <div className="nav-right">
                    <div className="right-action desktop-only">
                        {authControls}
                    </div>
                    <button
                        className="burger mobile-only"
                        onClick={() => setIsMenuOpen((v) => !v)}
                        aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
                        style={{
                            background: 'transparent',
                            border: '1px solid var(--color-badge-border)',
                            color: 'var(--color-text)',
                            width: '44px',
                            height: '44px',
                            borderRadius: '12px',
                            fontSize: '22px',
                            cursor: 'pointer',
                            display: 'none',
                            alignItems: 'center',
                            justifyContent: 'center',
                        }}
                    >
                        ☰
                    </button>
                </div>
            </div>

            <div className="mobile-menu" aria-hidden={!isMenuOpen}>
                <div className="mobile-links">
                    {navLinks}
                </div>
                <div className="mobile-action">
                    {authControls}
                </div>
            </div>

            <style>{`
                .nav-row {
                    width: 100%;
                    display: grid;
                    grid-template-columns: auto 1fr auto;
                    align-items: center;
                    gap: 32px;
                }

                .center-links {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 32px;
                }

                .nav-right {
                    display: flex;
                    align-items: center;
                    justify-content: flex-end;
                    gap: 16px;
                }

                .mobile-menu {
                    display: none;
                }

                .mobile-links {
                    display: flex;
                    flex-direction: column;
                    gap: 18px;
                    align-items: center;
                    justify-content: center;
                    padding-top: 24px;
                }

                .mobile-action {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px 0 10px;
                }

                .nav-link {
                    font-weight: 500;
                    color: var(--color-text);
                    text-decoration: none;
                    opacity: 1;
                    transition: opacity 0.2s ease, color 0.2s ease;
                }

                .nav-link:hover {
                    opacity: 0.7;
                }

                .nav-link[data-active="true"] {
                    color: var(--color-text-secondary);
                    opacity: 1;
                }

                .nav-link[data-active="true"]:hover {
                    opacity: 0.85;
                }

                @media (max-width: 1200px) {
                    .navbar { padding: 15px 20px !important; }
                    .desktop-only { display: none !important; }
                    .nav-row { grid-template-columns: 1fr auto; gap: 16px; }
                    .burger { display: flex !important; }

                    .navbar.is-open .mobile-menu {
                        display: flex;
                        flex-direction: column;
                        border-top: 1px solid var(--color-badge-border);
                        margin-top: 12px;
                        padding-top: 8px;
                        max-height: calc(100vh - 88px);
                        overflow-y: auto;
                    }
                }
            `}</style>
        </nav>
    );
};

export default Navbar;
```

## liquidweb/src/pages/Portfolios.jsx

**Path**: `liquidweb/src/pages/Portfolios.jsx`

```jsx
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
```

## liquidweb/src/pages/Portfolio.jsx

**Path**: `liquidweb/src/pages/Portfolio.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Twitter, Link, Send, CheckCircle, XCircle, Clock, AlertCircle, User, ArrowLeft, ArrowRight, Trash2, Edit3, Image, ExternalLink, Trophy, Sparkles, Target, MessageSquare, Briefcase, Heart, Eye, Repeat2, Calendar as CalendarIcon, Activity as ActivityIcon, Share2, Copy, Check } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { GuildSelect, GuildBadge, GUILDS } from '../components/GuildSelect';
import { TweetCard } from '../components/TweetEmbed';
import { ActivityChart, StatsCard } from '../components/StatsCharts';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ROLE_COLORS = {
    'Droplet': '#4FC3F7',
    'Current': '#29B6F6',
    'Tide': '#0288D1',
    'Wave': '#01579B',
    'Tsunami': '#004D40',
    'Allinliquid': '#FFD700',
};

const ROLE_HIERARCHY = ['Droplet', 'Current', 'Tide', 'Wave', 'Tsunami', 'Allinliquid'];

const Portfolio = () => {
    const navigate = useNavigate();
    const { user, isAuthenticated, loading: authLoading, login } = useAuth();
    const [loading, setLoading] = useState(true);
    const [dashboard, setDashboard] = useState(null);
    const [step, setStep] = useState('guild');
    const [formTab, setFormTab] = useState('tweets');
    const [formData, setFormData] = useState({
        guild: '',
        twitter_username: '',
        top_content: '',
        other_works: [],
        proof_of_use: '',
        proof_images: [],
        selected_tweets: [],
    });
    const [newOtherWork, setNewOtherWork] = useState('');
    const [availableTweets, setAvailableTweets] = useState([]);
    const [newTweetUrl, setNewTweetUrl] = useState('');
    const [saving, setSaving] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [history, setHistory] = useState([]);
    const [tweetStats, setTweetStats] = useState(null);
    const [linkCopied, setLinkCopied] = useState(false);

    const discordId = user?.id || user?.discord_id || '';

    const getPortfolioUrl = () => {
        const baseUrl = window.location.origin;
        return `${baseUrl}/portfolios/${discordId}`;
    };

    const copyPortfolioLink = async () => {
        try {
            await navigator.clipboard.writeText(getPortfolioUrl());
            setLinkCopied(true);
            setTimeout(() => setLinkCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    useEffect(() => {
        if (discordId && isAuthenticated) {
            fetchDashboard();
        } else if (!authLoading) {
            setLoading(false);
        }
    }, [discordId, isAuthenticated, authLoading]);

    const fetchDashboard = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/user/${discordId}/dashboard`);
            if (res.ok) {
                const data = await res.json();
                setDashboard(data);

                // Get guild from guild_info
                const guildName = data.guild_info?.name || '';

                // Get tweets from recent_tweets
                const tweetsFromDb = data.recent_tweets || [];
                const tweetUrls = tweetsFromDb.map(t => t.tweet_url);

                // Set available tweets from database
                if (tweetUrls.length > 0) {
                    setAvailableTweets(tweetUrls);
                }

                // Try to get portfolio data for twitter_handle (404 is expected if no portfolio)
                let twitterHandle = '';
                try {
                    const portfolioRes = await fetch(`${API_BASE}/api/portfolio/${discordId}`);
                    if (portfolioRes.status === 404) {
                        // No portfolio exists - this is normal for new users
                        setFormData(prev => ({
                            ...prev,
                            guild: guildName || prev.guild,
                        }));
                    } else if (portfolioRes.ok) {
                        const portfolioData = await portfolioRes.json();
                        
                        // If portfolio is not draft, redirect to individual page
                        if (portfolioData.status && portfolioData.status !== 'draft') {
                            navigate(`/portfolios/${discordId}`);
                            return;
                        }
                        
                        twitterHandle = portfolioData.twitter_handle || '';

                        // Also get other portfolio fields
                        setFormData(prev => ({
                            ...prev,
                            guild: portfolioData.target_role || guildName || prev.guild,
                            twitter_username: twitterHandle || prev.twitter_username,
                            other_works: portfolioData.other_works || prev.other_works || [],
                            proof_of_use: portfolioData.notion_url || prev.proof_of_use,
                        }));
                    } else {
                        // No portfolio yet, just set guild
                        setFormData(prev => ({
                            ...prev,
                            guild: guildName || prev.guild,
                        }));
                    }
                } catch (portfolioErr) {
                    console.log('No existing portfolio');
                    setFormData(prev => ({
                        ...prev,
                        guild: guildName || prev.guild,
                    }));
                }

                // Always fetch tweet stats from portfolio tweets
                fetchTweetStats(discordId);

                // Determine step based on portfolio status
                if (data.portfolio_status && data.portfolio_status !== 'draft') {
                    setStep('dashboard');
                } else if (guildName) {
                    setStep('form');
                } else {
                    setStep('guild');
                }
            }
        } catch (err) {
            console.error('Failed to fetch dashboard:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchHistory = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/portfolio/${discordId}/history`);
            if (res.ok) {
                const data = await res.json();
                setHistory(data);
            }
        } catch (err) {
            console.error('Failed to fetch history:', err);
        }
    };

    const fetchTweetStats = async (userId) => {
        try {
            // Fetch stats from portfolio tweets via Twitter API
            const res = await fetch(`${API_BASE}/api/twitter/portfolio/${userId}/stats`);
            if (res.ok) {
                const data = await res.json();
                setTweetStats(data);
            }
        } catch (err) {
            console.error('Failed to fetch tweet stats:', err);
        }
    };

    const cleanTwitterUsername = (input) => {
        let username = input.trim();
        if (username.includes('x.com/') || username.includes('twitter.com/')) {
            username = username.split('/').pop()?.split('?')[0] || username;
        }
        return username.replace(/^@+/, '');
    };

    const extractTweetId = (url) => {
        if (/^\d+$/.test(url)) return url;
        const match = url.match(/status\/(\d+)/);
        return match ? match[1] : url;
    };

    const addTweetUrl = () => {
        if (!newTweetUrl.trim()) return;
        const tweetId = extractTweetId(newTweetUrl);
        if (tweetId && !availableTweets.includes(newTweetUrl)) {
            setAvailableTweets([...availableTweets, newTweetUrl]);
            setNewTweetUrl('');
        }
    };

    const removeTweet = (url) => {
        setAvailableTweets(availableTweets.filter(t => t !== url));
    };

    const ensureDraftExists = async () => {
        // First check if portfolio already exists and is editable
        try {
            const checkRes = await fetch(`${API_BASE}/api/portfolio/${discordId}`);
            if (checkRes.ok) {
                const data = await checkRes.json();
                // Check if portfolio is in an editable state
                const editableStatuses = ['draft', 'rejected'];
                if (!editableStatuses.includes(data.status)) {
                    setError(`Portfolio is ${data.status.replace('_', ' ')} - cannot edit`);
                    setStep('dashboard');
                    return false;
                }
                return true;
            }
            // 404 means no portfolio - will create below
        } catch (err) {
            // Network error - will try to create
        }

        // Create a new draft portfolio
        try {
            const res = await fetch(`${API_BASE}/api/portfolio/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    discord_id: discordId,
                    username: user?.username || user?.global_name || 'Unknown',
                }),
            });
            if (res.ok) {
                // Refresh dashboard to get new portfolio data
                await fetchDashboard();
                return true;
            }
            // 400 means portfolio already exists (race condition)
            return res.status === 400;
        } catch (err) {
            console.error('Failed to create draft:', err);
            return false;
        }
    };

    const handleSave = async () => {
        setError('');
        setSuccess('');

        // Validation - only require tweets
        if (formData.selected_tweets.length === 0) {
            setError('Please add at least one tweet to your portfolio');
            setFormTab('tweets');
            return;
        }
        if (availableTweets.length === 0) {
            setError('Please add at least one tweet');
            setFormTab('tweets');
            return;
        }

        setSaving(true);
        try {
            // Ensure draft portfolio exists first
            const canProceed = await ensureDraftExists();
            if (!canProceed) {
                setSaving(false);
                return;
            }

            // Map frontend fields to backend schema
            const tweetsData = availableTweets.map(url => ({
                tweet_url: url,
                tweet_id: extractTweetId(url),
            }));

            const dataToSave = {
                bio: null,
                twitter_handle: formData.twitter_username,
                achievements: null,
                notion_url: formData.proof_of_use || null,
                target_role: formData.guild,
                tweets: tweetsData,
                other_works: formData.other_works || [],
            };

            const res = await fetch(`${API_BASE}/api/portfolio/save?discord_id=${discordId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dataToSave),
            });
            if (res.ok) {
                setSuccess('Portfolio saved!');
                fetchDashboard();
            } else {
                const err = await res.json();
                setError(err.detail || 'Failed to save');
            }
        } catch (err) {
            setError('Failed to save portfolio');
        } finally {
            setSaving(false);
        }
    };

    const handleSubmitPortfolio = async () => {
        // Validate required fields
        if (!formData.twitter_username?.trim()) {
            setError('Please enter your Twitter username');
            setFormTab('tweets');
            return;
        }
        if (availableTweets.length === 0) {
            setError('Please add at least one tweet');
            setFormTab('tweets');
            return;
        }

        if (!confirm('Submit your portfolio for review? You won\'t be able to edit it until review is complete.')) return;

        setSubmitting(true);
        setError('');
        try {
            // First, ensure portfolio is editable
            const canProceed = await ensureDraftExists();
            if (!canProceed) {
                setSubmitting(false);
                return;
            }

            const tweetsData = availableTweets.map(url => ({
                tweet_url: url,
                tweet_id: extractTweetId(url),
            }));

            const dataToSave = {
                bio: null,
                twitter_handle: formData.twitter_username,
                achievements: null,
                notion_url: formData.proof_of_use || null,
                target_role: formData.guild,
                tweets: tweetsData,
                other_works: formData.other_works || [],
            };

            const saveRes = await fetch(`${API_BASE}/api/portfolio/save?discord_id=${discordId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dataToSave),
            });

            if (!saveRes.ok) {
                const err = await saveRes.json();
                setError(err.detail || 'Failed to save before submit');
                return;
            }

            // Then submit
            const res = await fetch(`${API_BASE}/api/portfolio/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ discord_id: discordId }),
            });
            if (res.ok) {
                // Redirect to portfolio page after successful submit
                navigate(`/portfolios/${discordId}`);
            } else {
                const err = await res.json();
                setError(err.detail || 'Failed to submit');
            }
        } catch (err) {
            setError('Failed to submit portfolio');
        } finally {
            setSubmitting(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to delete your portfolio? This cannot be undone.')) return;

        setDeleting(true);
        try {
            const res = await fetch(`${API_BASE}/api/portfolio/${discordId}`, {
                method: 'DELETE',
            });
            if (res.ok) {
                setDashboard(null);
                setFormData({
                    guild: '',
                    twitter_username: '',
                    top_content: '',
                    other_works: [],
                    proof_of_use: '',
                    proof_images: [],
                    selected_tweets: [],
                });
                setAvailableTweets([]);
                setStep('guild');
                setSuccess('Portfolio deleted');
            }
        } catch (err) {
            setError('Failed to delete portfolio');
        } finally {
            setDeleting(false);
        }
    };

    const cardStyle = {
        background: 'var(--color-card-bg)',
        borderRadius: '20px',
        padding: '32px',
        border: '1px solid var(--color-badge-border)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        backdropFilter: 'blur(20px)',
    };

    const inputStyle = {
        width: '100%',
        padding: '16px 20px',
        borderRadius: '12px',
        border: '1px solid var(--color-badge-border)',
        background: 'rgba(0,0,0,0.2)',
        color: 'var(--color-text)',
        fontSize: '15px',
        fontFamily: 'inherit',
        transition: 'all 0.2s',
    };

    const labelStyle = {
        display: 'block',
        marginBottom: '10px',
        fontWeight: 600,
        fontSize: '14px',
        color: 'var(--color-text-secondary)',
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
    };

    const statusColors = {
        draft: { bg: '#64748b20', color: '#64748b', icon: FileText },
        submitted: { bg: '#3b82f620', color: '#3b82f6', icon: Clock },
        pending_vote: { bg: '#eab30820', color: '#eab308', icon: AlertCircle },
        approved: { bg: '#22c55e20', color: '#22c55e', icon: CheckCircle },
        rejected: { bg: '#ef444420', color: '#ef4444', icon: XCircle },
        promoted: { bg: '#a855f720', color: '#a855f7', icon: CheckCircle },
    };

    if (authLoading) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ width: '40px', height: '40px', border: '3px solid var(--color-primary)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
                    <p style={{ color: 'var(--color-text-secondary)' }}>Loading...</p>
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
                        Portfolio
                    </h1>
                    <p style={{ color: 'var(--color-text-secondary)', margin: 0, marginBottom: '32px', fontSize: '18px', maxWidth: '600px', marginInline: 'auto' }}>
                        Connect with Discord to manage your portfolio
                    </p>
                    <button onClick={login} className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', padding: '14px 28px', fontSize: '15px' }}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
                        </svg>
                        Login with Discord
                    </button>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ color: 'var(--color-text-secondary)' }}>Loading...</div>
            </div>
        );
    }

    const portfolioStatus = dashboard?.portfolio?.status || 'draft';
    const StatusIcon = statusColors[portfolioStatus]?.icon || FileText;
    const canEdit = portfolioStatus === 'draft' || (portfolioStatus === 'rejected' && dashboard?.portfolio?.can_resubmit);
    const cooldown = dashboard?.portfolio?.cooldown;
    const currentRole = dashboard?.roles?.current || 'Droplet';
    const nextRole = dashboard?.roles?.next;

    const tabStyle = (active) => ({
        padding: '12px 24px',
        background: active ? 'var(--color-primary)' : 'transparent',
        color: active ? 'var(--color-primary-text)' : 'var(--color-text-secondary)',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer',
        fontWeight: 600,
        fontSize: '14px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        transition: 'all 0.2s',
    });

    return (
        <div style={{ minHeight: '100vh', padding: '120px 20px 40px', background: 'var(--color-bg)' }}>
            <div className="container" style={{ maxWidth: '900px', margin: '0 auto' }}>

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
                        <Briefcase size={40} style={{ color: 'var(--color-primary)' }} />
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
                        {step === 'dashboard' ? 'Your Portfolio' : 'Apply for Guild'}
                    </h1>
                    <p style={{ color: 'var(--color-text-secondary)', margin: 0, fontSize: '18px', maxWidth: '600px', marginInline: 'auto' }}>
                        Manage your contributions, showcase your work, and level up in the Liquid ecosystem.
                    </p>
                </div>

                {/* Messages */}
                {error && (
                    <div style={{ padding: '12px 16px', borderRadius: '8px', marginBottom: '24px', background: '#ef444420', color: '#ef4444' }}>
                        {error}
                    </div>
                )}
                {success && (
                    <div style={{ padding: '12px 16px', borderRadius: '8px', marginBottom: '24px', background: '#22c55e20', color: '#22c55e' }}>
                        {success}
                    </div>
                )}

                {/* ============ GUILD SELECTION STEP ============ */}
                {step === 'guild' && (
                    <div>
                        <div style={cardStyle}>
                            <GuildSelect
                                selected={formData.guild}
                                onSelect={(guild) => setFormData({ ...formData, guild })}
                            />
                            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '32px', paddingTop: '24px', borderTop: '1px solid var(--color-badge-border)' }}>
                                <button
                                    className="btn btn-primary"
                                    onClick={() => setStep('form')}
                                    disabled={!formData.guild}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 32px', fontSize: '16px' }}
                                >
                                    Continue
                                    <ArrowRight size={18} />
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* ============ FORM STEP ============ */}
                {step === 'form' && (
                    <div>
                        {/* Header */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                <button
                                    onClick={() => setStep('guild')}
                                    style={{
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid var(--color-badge-border)',
                                        cursor: 'pointer',
                                        color: 'var(--color-text)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px',
                                        padding: '8px 16px',
                                        borderRadius: '12px',
                                        fontSize: '14px',
                                        fontWeight: 500,
                                        transition: 'all 0.2s',
                                    }}
                                >
                                    <ArrowLeft size={16} /> Back
                                </button>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <h2 style={{ fontSize: '24px', margin: 0, fontWeight: 600 }}>Edit Portfolio</h2>
                                    {formData.guild && <GuildBadge guildId={formData.guild} size="small" />}
                                </div>
                            </div>
                        </div>

                        {/* Form Tabs */}
                        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '32px' }}>
                            <div style={{
                                display: 'flex',
                                gap: '4px',
                                background: 'var(--color-card-bg)',
                                padding: '6px',
                                borderRadius: '99px',
                                border: '1px solid var(--color-badge-border)',
                                width: 'fit-content'
                            }}>
                                <button
                                    style={{
                                        ...tabStyle(formTab === 'tweets'),
                                        borderRadius: '99px',
                                        padding: '10px 24px',
                                        boxShadow: formTab === 'tweets' ? '0 2px 10px rgba(237, 237, 255, 0.2)' : 'none',
                                    }}
                                    onClick={() => setFormTab('tweets')}
                                >
                                    <Twitter size={16} /> Your Tweets
                                </button>
                                <button
                                    style={{
                                        ...tabStyle(formTab === 'details'),
                                        borderRadius: '99px',
                                        padding: '10px 24px',
                                        boxShadow: formTab === 'details' ? '0 2px 10px rgba(237, 237, 255, 0.2)' : 'none',
                                    }}
                                    onClick={() => setFormTab('details')}
                                >
                                    <FileText size={16} /> Application Details
                                </button>
                            </div>
                        </div>

                        <div style={cardStyle}>
                            {/* Tweets Tab */}
                            {formTab === 'tweets' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                                    {/* Twitter Username */}
                                    <div>
                                        <label style={labelStyle}>
                                            <Twitter size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                                            Twitter/X Username
                                        </label>
                                        <input
                                            type="text"
                                            style={inputStyle}
                                            placeholder="username (without @)"
                                            value={formData.twitter_username}
                                            onChange={(e) => setFormData({ ...formData, twitter_username: cleanTwitterUsername(e.target.value) })}
                                        />
                                    </div>

                                    {/* Add Tweet URL */}
                                    <div>
                                        <label style={labelStyle}>Add Tweet URL</label>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <input
                                                type="text"
                                                style={{ ...inputStyle, flex: 1 }}
                                                placeholder="https://x.com/user/status/123456789"
                                                value={newTweetUrl}
                                                onChange={(e) => setNewTweetUrl(e.target.value)}
                                                onKeyDown={(e) => e.key === 'Enter' && addTweetUrl()}
                                            />
                                            <button className="btn btn-primary" onClick={addTweetUrl}>Add</button>
                                        </div>
                                    </div>

                                    {/* Tweet List */}
                                    <div>
                                        <label style={labelStyle}>Selected Tweets ({availableTweets.length})</label>
                                        {availableTweets.length === 0 ? (
                                            <div style={{ padding: '40px', textAlign: 'center', background: 'var(--color-bg)', borderRadius: '12px', color: 'var(--color-text-secondary)' }}>
                                                <Twitter size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
                                                <p style={{ margin: 0 }}>No tweets added yet. Add tweet URLs above.</p>
                                            </div>
                                        ) : (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                                {availableTweets.map((url, i) => (
                                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', background: 'var(--color-bg)', borderRadius: '8px' }}>
                                                        <Twitter size={16} style={{ color: '#1DA1F2' }} />
                                                        <span style={{ flex: 1, fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{url}</span>
                                                        <a href={url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-text-secondary)' }}>
                                                            <ExternalLink size={16} />
                                                        </a>
                                                        <button onClick={() => removeTweet(url)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }}>
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Top Content */}
                                    <div>
                                        <label style={labelStyle}>
                                            <Trophy size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                                            Top Content Highlights
                                        </label>
                                        <textarea
                                            style={{ ...inputStyle, minHeight: '100px', resize: 'vertical' }}
                                            placeholder="Links to your best content, threads, or contributions..."
                                            value={formData.top_content}
                                            onChange={(e) => setFormData({ ...formData, top_content: e.target.value })}
                                        />
                                    </div>
                                </div>
                            )}

                            {/* Details Tab */}
                            {formTab === 'details' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                                    {/* Other Works */}
                                    <div>
                                        <label style={labelStyle}>
                                            <ExternalLink size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                                            Other Works (optional)
                                        </label>
                                        <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
                                            Add links to your other work besides tweets (designs, articles, videos, etc.)
                                        </p>
                                        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                                            <input
                                                type="text"
                                                style={{ ...inputStyle, flex: 1 }}
                                                placeholder="https://..."
                                                value={newOtherWork}
                                                onChange={(e) => setNewOtherWork(e.target.value)}
                                                onKeyPress={(e) => {
                                                    if (e.key === 'Enter' && newOtherWork.trim()) {
                                                        setFormData({ ...formData, other_works: [...(formData.other_works || []), newOtherWork.trim()] });
                                                        setNewOtherWork('');
                                                    }
                                                }}
                                            />
                                            <button
                                                className="btn btn-primary"
                                                onClick={() => {
                                                    if (newOtherWork.trim()) {
                                                        setFormData({ ...formData, other_works: [...(formData.other_works || []), newOtherWork.trim()] });
                                                        setNewOtherWork('');
                                                    }
                                                }}
                                                disabled={!newOtherWork.trim()}
                                            >
                                                Add
                                            </button>
                                        </div>
                                        {formData.other_works && formData.other_works.length > 0 && (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                {formData.other_works.map((link, i) => (
                                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--color-badge-border)' }}>
                                                        <ExternalLink size={14} style={{ color: 'var(--color-primary)' }} />
                                                        <a href={link} target="_blank" rel="noopener noreferrer" style={{ flex: 1, color: 'var(--color-text)', textDecoration: 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{link}</a>
                                                        <button
                                                            onClick={() => setFormData({ ...formData, other_works: formData.other_works.filter((_, idx) => idx !== i) })}
                                                            style={{ background: 'transparent', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer', padding: '4px' }}
                                                        >
                                                            <Trash2 size={14} />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    {/* Proof of Use */}
                                    <div>
                                        <label style={labelStyle}>
                                            <Image size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                                            Proof of Use (optional)
                                        </label>
                                        <input
                                            type="text"
                                            style={inputStyle}
                                            placeholder="Link to screenshot showing Liquid usage"
                                            value={formData.proof_of_use}
                                            onChange={(e) => setFormData({ ...formData, proof_of_use: e.target.value })}
                                        />
                                    </div>
                                </div>
                            )}

                            {/* Form Actions - Different for each tab */}
                            <div style={{ display: 'flex', gap: '12px', marginTop: '24px', paddingTop: '24px', borderTop: '1px solid var(--color-badge-border)', justifyContent: 'flex-end' }}>
                                {formTab === 'tweets' ? (
                                    <button
                                        className="btn btn-primary"
                                        onClick={() => setFormTab('details')}
                                        style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 32px', fontSize: '16px' }}
                                    >
                                        Continue
                                        <ArrowRight size={18} />
                                    </button>
                                ) : (
                                    <>
                                        <button
                                            className="btn"
                                            style={{ background: 'var(--color-badge-border)', color: 'var(--color-text)' }}
                                            onClick={handleSave}
                                            disabled={saving}
                                        >
                                            {saving ? 'Saving...' : 'Save Draft'}
                                        </button>
                                        <button
                                            className="btn btn-primary"
                                            onClick={handleSubmitPortfolio}
                                            disabled={submitting || availableTweets.length === 0}
                                            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                        >
                                            <Send size={16} />
                                            {submitting ? 'Submitting...' : 'Submit for Review'}
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* ============ DASHBOARD STEP ============ */}
                {step === 'dashboard' && (
                    <div>
                        {/* Header with User Info */}
                        <div style={{ ...cardStyle, marginBottom: '24px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                                {user?.avatar_url ? (
                                    <img src={user.avatar_url} alt="" style={{ width: '80px', height: '80px', borderRadius: '50%', border: '3px solid var(--color-primary)' }} />
                                ) : (
                                    <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--color-primary) 0%, #8b5cf6 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '32px', fontWeight: 700, color: 'white' }}>
                                        {(user?.global_name || user?.username || 'U').charAt(0).toUpperCase()}
                                    </div>
                                )}
                                <div style={{ flex: 1 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                                        <h1 style={{ fontSize: '28px', margin: 0, fontWeight: 700 }}>{user?.global_name || user?.username || 'User'}</h1>
                                        {formData.guild && <GuildBadge guildId={formData.guild} size="small" />}
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                                        <span style={{
                                            padding: '4px 12px',
                                            borderRadius: '12px',
                                            background: `${ROLE_COLORS[currentRole] || '#64748b'}20`,
                                            color: ROLE_COLORS[currentRole] || '#64748b',
                                            fontSize: '13px',
                                            fontWeight: 500,
                                        }}>
                                            {currentRole}
                                        </span>
                                        {nextRole && (
                                            <span style={{ color: 'var(--color-text-secondary)', fontSize: '13px' }}>
                                                → Next: {nextRole}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                {/* Status Badge */}
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    padding: '8px 16px',
                                    borderRadius: '20px',
                                    background: statusColors[portfolioStatus]?.bg,
                                    color: statusColors[portfolioStatus]?.color,
                                }}>
                                    <StatusIcon size={16} />
                                    <span style={{ fontWeight: 500, fontSize: '13px' }}>{portfolioStatus.replace('_', ' ').toUpperCase()}</span>
                                </div>
                                {/* Share Button */}
                                <button
                                    onClick={copyPortfolioLink}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px',
                                        padding: '8px 16px',
                                        borderRadius: '20px',
                                        background: linkCopied ? '#22c55e20' : 'rgba(255,255,255,0.05)',
                                        color: linkCopied ? '#22c55e' : 'var(--color-text)',
                                        border: '1px solid',
                                        borderColor: linkCopied ? '#22c55e' : 'var(--color-badge-border)',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        fontWeight: 500,
                                        fontSize: '13px',
                                    }}
                                    title="Copy portfolio link"
                                >
                                    {linkCopied ? <Check size={16} /> : <Share2 size={16} />}
                                    {linkCopied ? 'Copied!' : 'Share'}
                                </button>
                            </div>
                        </div>

                        {/* Cooldown Warning */}
                        {cooldown && !dashboard?.portfolio?.can_resubmit && (
                            <div style={{ ...cardStyle, marginBottom: '24px', borderColor: '#f59e0b', background: '#f59e0b10' }}>
                                <h4 style={{ margin: '0 0 8px', color: '#f59e0b' }}>⏳ Cooldown Period</h4>
                                <p style={{ margin: 0, color: 'var(--color-text-secondary)' }}>
                                    You can resubmit in {cooldown.days_remaining} days and {cooldown.hours_remaining} hours
                                </p>
                            </div>
                        )}

                        {/* Discord Stats */}
                        {dashboard?.discord && (
                            <div style={{ marginBottom: '48px' }}>
                                <h3 style={{ margin: '0 0 24px', fontSize: '20px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <MessageSquare size={20} style={{ color: 'var(--color-primary)' }} />
                                    Discord Activity
                                </h3>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px' }}>
                                    <StatsCard
                                        label="Total Messages"
                                        value={dashboard.discord.message_count?.toLocaleString()}
                                        icon={MessageSquare}
                                    />
                                    <StatsCard
                                        label="Days Active"
                                        value={dashboard.discord.days_active?.toString()}
                                        icon={ActivityIcon}
                                    />
                                    <StatsCard
                                        label="Joined Date"
                                        value={dashboard.discord.first_message_date}
                                        icon={CalendarIcon}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Twitter Engagement Stats */}
                        {tweetStats && tweetStats.tweet_count > 0 && (
                            <div style={{ marginBottom: '48px' }}>
                                <h3 style={{ margin: '0 0 24px', fontSize: '20px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <Twitter size={20} style={{ color: '#1DA1F2' }} />
                                    Twitter Engagement
                                </h3>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
                                    <StatsCard
                                        label="Total Likes"
                                        value={(tweetStats.total_likes || 0).toLocaleString()}
                                        icon={Heart}
                                    />
                                    <StatsCard
                                        label="Retweets"
                                        value={(tweetStats.total_retweets || 0).toLocaleString()}
                                        icon={Repeat2}
                                    />
                                    <StatsCard
                                        label="Views"
                                        value={(tweetStats.total_views || 0).toLocaleString()}
                                        icon={Eye}
                                    />
                                    <StatsCard
                                        label="Tracked Tweets"
                                        value={tweetStats.tweet_count || 0}
                                        icon={Twitter}
                                    />
                                </div>
                                
                                {/* Display Tweet Embeds from API response */}
                                {tweetStats.tweets && tweetStats.tweets.length > 0 && (
                                    <div style={{ ...cardStyle, marginTop: '24px' }}>
                                        <h4 style={{ margin: '0 0 20px', fontSize: '16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <Twitter size={16} style={{ color: '#1DA1F2' }} />
                                            Your Tweets
                                        </h4>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(350px, 100%), 1fr))', gap: '16px' }}>
                                            {tweetStats.tweets.slice(0, 6).map((tweet, i) => (
                                                <TweetCard key={i} tweetUrl={tweet.url || `https://x.com/i/status/${tweet.tweet_id}`} useEmbed={true} />
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Portfolio Content */}
                        {dashboard?.portfolio?.data && (
                            <>
                                {/* Other Works */}
                                {dashboard.portfolio.data.other_works?.length > 0 && (
                                    <div style={{ ...cardStyle, marginBottom: '24px' }}>
                                        <h3 style={{ margin: '0 0 16px', fontSize: '18px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <ExternalLink size={18} style={{ color: '#10B981' }} />
                                            Other Works
                                        </h3>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                            {dashboard.portfolio.data.other_works.map((link, i) => (
                                                <a 
                                                    key={i}
                                                    href={link} 
                                                    target="_blank" 
                                                    rel="noopener noreferrer"
                                                    style={{ 
                                                        display: 'flex', 
                                                        alignItems: 'center', 
                                                        gap: '8px', 
                                                        padding: '12px 16px', 
                                                        background: 'rgba(0,0,0,0.2)', 
                                                        borderRadius: '8px', 
                                                        border: '1px solid var(--color-badge-border)',
                                                        color: 'var(--color-text)',
                                                        textDecoration: 'none',
                                                        transition: 'all 0.2s',
                                                    }}
                                                >
                                                    <ExternalLink size={14} style={{ color: 'var(--color-primary)' }} />
                                                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{link}</span>
                                                </a>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Selected Tweets with Embeds */}
                                {dashboard.portfolio.data.selected_tweets?.length > 0 && (
                                    <div style={{ ...cardStyle, marginBottom: '24px' }}>
                                        <h3 style={{ margin: '0 0 20px', fontSize: '18px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <Twitter size={18} style={{ color: '#1DA1F2' }} />
                                            Your Shared Tweets
                                        </h3>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(400px, 100%), 1fr))', gap: '20px' }}>
                                            {dashboard.portfolio.data.selected_tweets.slice(0, 6).map((tweetUrl, i) => (
                                                <TweetCard key={i} tweetUrl={tweetUrl} useEmbed={true} />
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}

                        {/* Status Messages for non-editable states */}
                        {(portfolioStatus === 'submitted' || portfolioStatus === 'pending_vote') && (
                            <div style={{
                                ...cardStyle,
                                marginBottom: '24px',
                                borderColor: portfolioStatus === 'pending_vote' ? '#8b5cf6' : '#3b82f6',
                                background: portfolioStatus === 'pending_vote' ? '#8b5cf610' : '#3b82f610'
                            }}>
                                <h4 style={{ margin: '0 0 8px', color: portfolioStatus === 'pending_vote' ? '#8b5cf6' : '#3b82f6' }}>
                                    {portfolioStatus === 'pending_vote' ? '🗳️ Voting in Progress' : '📋 Under Review'}
                                </h4>
                                <p style={{ margin: 0, color: 'var(--color-text-secondary)' }}>
                                    {portfolioStatus === 'pending_vote'
                                        ? 'Your portfolio has been approved and is now being voted on by Parliament members. You cannot make changes while voting is in progress.'
                                        : 'Your portfolio is being reviewed by a Guild Leader. You will be notified when a decision is made.'}
                                </p>
                            </div>
                        )}

                        {/* Actions - Only show for draft status */}
                        {portfolioStatus === 'draft' && (
                            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                                <button
                                    className="btn"
                                    onClick={() => setStep('form')}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <Edit3 size={16} /> Edit Portfolio
                                </button>
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSubmitPortfolio}
                                    disabled={submitting}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <Send size={16} /> Submit for Review
                                </button>
                                <button
                                    className="btn"
                                    onClick={handleDelete}
                                    disabled={deleting}
                                    style={{ background: '#ef444420', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <Trash2 size={16} /> {deleting ? 'Deleting...' : 'Delete Portfolio'}
                                </button>
                            </div>
                        )}
                        
                        {/* View Portfolio Link - Show for submitted portfolios */}
                        {portfolioStatus !== 'draft' && (
                            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                                <button
                                    className="btn btn-primary"
                                    onClick={() => navigate(`/portfolios/${discordId}`)}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <ExternalLink size={16} /> View Your Portfolio
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Portfolio;
```

## liquidweb/src/pages/Leaderboard.jsx

**Path**: `liquidweb/src/pages/Leaderboard.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { Trophy, Medal, TrendingUp, Users } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Leaderboard = () => {
    const [leaderboard, setLeaderboard] = useState([]);
    const [guildLeaderboard, setGuildLeaderboard] = useState([]);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState('global');
    const [guildFilter, setGuildFilter] = useState('all');

    useEffect(() => {
        fetchLeaderboards();
    }, []);

    const fetchLeaderboards = async () => {
        try {
            // Fetch global leaderboard
            const globalRes = await fetch(`${API_BASE}/api/user/leaderboard?limit=50`);
            if (globalRes.ok) {
                const data = await globalRes.json();
                setLeaderboard(data);
            }

            // Fetch guild leaderboard
            const guildRes = await fetch(`${API_BASE}/api/guilds/leaderboard?limit=50`);
            if (guildRes.ok) {
                const data = await guildRes.json();
                setGuildLeaderboard(data);
            }
        } catch (err) {
            console.error('Failed to fetch leaderboards:', err);
        } finally {
            setLoading(false);
        }
    };

    const cardStyle = {
        background: 'var(--color-card-bg)',
        borderRadius: '16px',
        border: '1px solid var(--color-badge-border)',
        overflow: 'hidden',
    };

    const getMedal = (rank) => {
        if (rank === 1) return { icon: '🥇', color: '#ffd700' };
        if (rank === 2) return { icon: '🥈', color: '#c0c0c0' };
        if (rank === 3) return { icon: '🥉', color: '#cd7f32' };
        return null;
    };

    const guildEmojis = {
        traders: '📈',
        content: '✍️',
        designers: '🎨',
    };

    const filteredGuildLeaderboard = guildFilter === 'all' 
        ? guildLeaderboard 
        : guildLeaderboard.filter(m => m.guild_name === guildFilter);

    return (
        <div style={{ minHeight: '100vh', padding: '120px 20px 40px', background: 'var(--color-bg)' }}>
            <div className="container" style={{ maxWidth: '1200px', margin: '0 auto' }}>
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
                        <Trophy size={40} style={{ color: 'var(--color-primary)' }} />
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
                        Leaderboard
                    </h1>
                    <p style={{ color: 'var(--color-text-secondary)', margin: 0, fontSize: '18px', maxWidth: '600px', marginInline: 'auto' }}>
                        Top contributors in the Liquid community
                    </p>
                </div>

                {/* Tabs */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', justifyContent: 'center' }}>
                    <button
                        className="btn"
                        style={{
                            padding: '10px 24px',
                            background: tab === 'global' ? 'var(--color-primary)' : 'var(--color-card-bg)',
                            color: tab === 'global' ? 'var(--color-primary-text)' : 'var(--color-text)',
                        }}
                        onClick={() => setTab('global')}
                    >
                        <TrendingUp size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                        Global
                    </button>
                    <button
                        className="btn"
                        style={{
                            padding: '10px 24px',
                            background: tab === 'guilds' ? 'var(--color-primary)' : 'var(--color-card-bg)',
                            color: tab === 'guilds' ? 'var(--color-primary-text)' : 'var(--color-text)',
                        }}
                        onClick={() => setTab('guilds')}
                    >
                        <Users size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                        Guilds
                    </button>
                </div>

                {/* Guild Filter */}
                {tab === 'guilds' && (
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', justifyContent: 'center', flexWrap: 'wrap' }}>
                        {['all', 'traders', 'content', 'designers'].map(g => (
                            <button
                                key={g}
                                className="btn"
                                style={{
                                    padding: '8px 16px',
                                    fontSize: '13px',
                                    background: guildFilter === g ? 'var(--color-primary)' : 'var(--color-card-bg)',
                                    color: guildFilter === g ? 'var(--color-primary-text)' : 'var(--color-text)',
                                }}
                                onClick={() => setGuildFilter(g)}
                            >
                                {g === 'all' ? 'All Guilds' : `${guildEmojis[g]} ${g.charAt(0).toUpperCase() + g.slice(1)}`}
                            </button>
                        ))}
                    </div>
                )}

                {loading ? (
                    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
                        Loading...
                    </div>
                ) : (
                    <div style={cardStyle}>
                        {/* Header Row */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: tab === 'global' ? '60px 1fr 100px 100px' : '60px 1fr 100px 100px 80px',
                            padding: '16px 20px',
                            borderBottom: '1px solid var(--color-badge-border)',
                            fontWeight: 600,
                            fontSize: '13px',
                            color: 'var(--color-text-secondary)',
                        }}>
                            <div>Rank</div>
                            <div>User</div>
                            <div style={{ textAlign: 'right' }}>Points</div>
                            <div style={{ textAlign: 'right' }}>{tab === 'global' ? 'Contributions' : 'Quests'}</div>
                            {tab === 'guilds' && <div style={{ textAlign: 'right' }}>Tier</div>}
                        </div>

                        {/* Rows */}
                        {(tab === 'global' ? leaderboard : filteredGuildLeaderboard).map((entry, index) => {
                            const rank = tab === 'global' ? entry.rank : index + 1;
                            const medal = getMedal(rank);
                            
                            return (
                                <div
                                    key={entry.discord_id + index}
                                    style={{
                                        display: 'grid',
                                        gridTemplateColumns: tab === 'global' ? '60px 1fr 100px 100px' : '60px 1fr 100px 100px 80px',
                                        padding: '16px 20px',
                                        borderBottom: '1px solid var(--color-badge-border)',
                                        alignItems: 'center',
                                        background: rank <= 3 ? `${medal?.color}08` : 'transparent',
                                    }}
                                >
                                    <div style={{ fontWeight: 600 }}>
                                        {medal ? (
                                            <span style={{ fontSize: '20px' }}>{medal.icon}</span>
                                        ) : (
                                            <span style={{ color: 'var(--color-text-secondary)' }}>#{rank}</span>
                                        )}
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        {entry.avatar_url ? (
                                            <img src={entry.avatar_url} alt="" style={{ width: '36px', height: '36px', borderRadius: '50%' }} />
                                        ) : (
                                            <div style={{
                                                width: '36px',
                                                height: '36px',
                                                borderRadius: '50%',
                                                background: 'var(--color-badge-border)',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                fontSize: '14px',
                                            }}>
                                                {entry.username?.charAt(0).toUpperCase() || '?'}
                                            </div>
                                        )}
                                        <div>
                                            <div style={{ fontWeight: 500 }}>{entry.username}</div>
                                            {tab === 'guilds' && (
                                                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                                                    {guildEmojis[entry.guild_name]} {entry.role_type}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    <div style={{ textAlign: 'right', fontWeight: 600, color: '#22c55e' }}>
                                        {entry.points}
                                    </div>
                                    <div style={{ textAlign: 'right', color: 'var(--color-text-secondary)' }}>
                                        {tab === 'global' ? entry.contributions : entry.quests_completed}
                                    </div>
                                    {tab === 'guilds' && (
                                        <div style={{ textAlign: 'right' }}>
                                            <span style={{
                                                padding: '4px 8px',
                                                borderRadius: '4px',
                                                fontSize: '12px',
                                                fontWeight: 600,
                                                background: entry.tier >= 3 ? '#a855f720' : entry.tier >= 2 ? '#3b82f620' : '#64748b20',
                                                color: entry.tier >= 3 ? '#a855f7' : entry.tier >= 2 ? '#3b82f6' : '#64748b',
                                            }}>
                                                T{entry.tier}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            );
                        })}

                        {(tab === 'global' ? leaderboard : filteredGuildLeaderboard).length === 0 && (
                            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                                No entries yet
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Leaderboard;
```

## liquidweb/src/pages/Stats.jsx

**Path**: `liquidweb/src/pages/Stats.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { Users, MessageSquare, TrendingUp, Activity, Calendar } from 'lucide-react';
import { ActivityChart, ContributorsChart, DistributionChart, StatsCard } from '../components/StatsCharts';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Stats = () => {
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState(null);
    const [period, setPeriod] = useState('week');

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/stats/dashboard`);
            if (res.ok) {
                const data = await res.json();
                setStats(data);
            }
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        } finally {
            setLoading(false);
        }
    };

    const periodButtons = ['day', 'week', 'month'];

    if (loading) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ width: '40px', height: '40px', border: '3px solid var(--color-primary)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
                    <p style={{ color: 'var(--color-text-secondary)' }}>Loading stats...</p>
                </div>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    const serverStats = stats?.server || {};
    const dailyMessages = stats?.daily_messages || [];
    const weeklyMessages = stats?.weekly_messages || [];
    const topContributors = stats?.top_contributors?.[period] || [];
    const portfolioDistribution = stats?.portfolio_distribution || [];

    return (
        <div style={{ minHeight: '100vh', padding: '120px 20px 40px', background: 'var(--color-bg)' }}>
            <div className="container" style={{ maxWidth: '1200px', margin: '0 auto' }}>
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
                        <Activity size={40} style={{ color: 'var(--color-primary)' }} />
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
                        Server Statistics
                    </h1>
                    <p style={{ color: 'var(--color-text-secondary)', margin: 0, fontSize: '18px', maxWidth: '600px', marginInline: 'auto' }}>
                        Real-time insights into community activity, trader engagement, and platform growth.
                    </p>
                </div>

                {/* Stats Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px', marginBottom: '48px' }}>
                    <StatsCard
                        label="Total Users"
                        value={serverStats.total_users?.toLocaleString() || '0'}
                        image="/images/community.svg"
                        icon={Users}
                    />
                    <StatsCard
                        label="Total Messages"
                        value={serverStats.total_messages?.toLocaleString() || '0'}
                        image="/images/Content_Orator.png"
                        icon={MessageSquare}
                    />
                    <StatsCard
                        label="Messages Today"
                        value={serverStats.messages_today?.toLocaleString() || '0'}
                        trend={serverStats.messages_trend}
                        image="/images/Content_Drip.png"
                        icon={TrendingUp}
                    />
                    <StatsCard
                        label="Active This Week"
                        value={serverStats.active_users_week?.toLocaleString() || '0'}
                        image="/images/Trader_Tide.png"
                        icon={Calendar}
                    />
                </div>

                {/* Period Filter */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '32px', justifyContent: 'center' }}>
                    <div style={{
                        background: 'var(--color-card-bg)',
                        padding: '6px',
                        borderRadius: '99px',
                        border: '1px solid var(--color-badge-border)',
                        display: 'inline-flex'
                    }}>
                        {periodButtons.map((p) => (
                            <button
                                key={p}
                                className="btn"
                                style={{
                                    padding: '8px 24px',
                                    fontSize: '14px',
                                    background: period === p ? 'var(--color-primary)' : 'transparent',
                                    color: period === p ? 'var(--color-primary-text)' : 'var(--color-text-secondary)',
                                    borderRadius: '99px', // Inner buttons are pills
                                    boxShadow: period === p ? '0 2px 10px rgba(237, 237, 255, 0.2)' : 'none',
                                }}
                                onClick={() => setPeriod(p)}
                            >
                                {p.charAt(0).toUpperCase() + p.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Charts Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(500px, 100%), 1fr))', gap: '24px', marginBottom: '48px' }}>
                    <ActivityChart
                        data={period === 'day' ? dailyMessages : weeklyMessages}
                        title="Message Activity"
                        dataKey="message_count"
                        xAxisKey="period"
                    />
                    <ContributorsChart
                        data={topContributors}
                        title={`Top Contributors (${period})`}
                    />
                </div>

                {/* Distribution */}
                {portfolioDistribution.length > 0 && (
                    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
                        <DistributionChart
                            data={portfolioDistribution}
                            title="Portfolio Status Distribution"
                        />
                    </div>
                )}

                {/* No Data State */}
                {!stats && (
                    <div style={{
                        background: 'var(--color-card-bg)',
                        borderRadius: 'var(--border-radius)',
                        padding: '80px',
                        border: '1px solid var(--color-badge-border)',
                        textAlign: 'center',
                    }}>
                        <Activity size={48} style={{ marginBottom: '24px', opacity: 0.2, color: 'var(--color-text)' }} />
                        <h3 style={{ margin: '0 0 12px', fontSize: '24px' }}>No Statistics Available</h3>
                        <p style={{ color: 'var(--color-text-secondary)', margin: 0, fontSize: '16px' }}>
                            Stats will appear here once there's community activity.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Stats;
```

## liquidweb/src/pages/Dashboard.jsx

**Path**: `liquidweb/src/pages/Dashboard.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { User, Award, Target, TrendingUp, Calendar, ExternalLink, MessageSquare, Zap, Crown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Dashboard = () => {
    const { user, isAuthenticated, loading: authLoading, login } = useAuth();
    const [loading, setLoading] = useState(true);
    const [userData, setUserData] = useState(null);
    const [error, setError] = useState(null);

    const discordId = user?.discord_id || '';

    useEffect(() => {
        if (discordId && isAuthenticated) {
            fetchDashboard();
        } else if (!authLoading) {
            setLoading(false);
        }
    }, [discordId, isAuthenticated, authLoading]);

    const fetchDashboard = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/user/${discordId}/dashboard`);
            if (res.ok) {
                const data = await res.json();
                setUserData(data);
            } else {
                setError('User not found');
            }
        } catch (err) {
            setError('Failed to load dashboard');
        } finally {
            setLoading(false);
        }
    };

    const cardStyle = {
        background: 'var(--color-card-bg)',
        borderRadius: '16px',
        padding: '24px',
        border: '1px solid var(--color-badge-border)',
    };

    const statCardStyle = {
        ...cardStyle,
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
    };

    if (authLoading) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ width: '40px', height: '40px', border: '3px solid var(--color-primary)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
                    <p style={{ color: 'var(--color-text-secondary)' }}>Loading...</p>
                </div>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    if (!isAuthenticated) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px 40px', background: 'var(--color-bg)' }}>
                <div className="container" style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
                    <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'var(--color-card-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
                        <User size={36} style={{ opacity: 0.5 }} />
                    </div>
                    <h1 style={{ fontSize: '32px', marginBottom: '12px', fontWeight: 600 }}>Dashboard</h1>
                    <p style={{ color: 'var(--color-text-secondary)', marginBottom: '32px', fontSize: '16px' }}>
                        Connect with Discord to view your stats and activity
                    </p>
                    <button onClick={login} className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', padding: '14px 28px', fontSize: '15px' }}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
                        </svg>
                        Login with Discord
                    </button>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ color: 'var(--color-text-secondary)' }}>Loading...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ color: '#ef4444' }}>{error}</div>
            </div>
        );
    }

    if (!userData) {
        return (
            <div style={{ minHeight: '100vh', padding: '120px 20px', background: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ color: 'var(--color-text-secondary)' }}>No data available</div>
            </div>
        );
    }

    const { user: userProfile, stats, portfolio_status, guild_info, recent_contributions, promotion_history } = userData;

    return (
        <div style={{ minHeight: '100vh', padding: '120px 20px 40px', background: 'var(--color-bg)' }}>
            <div className="container" style={{ maxWidth: '1200px', margin: '0 auto' }}>
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '40px' }}>
                    {userProfile.avatar_url ? (
                        <img src={userProfile.avatar_url} alt="" style={{ width: '80px', height: '80px', borderRadius: '50%' }} />
                    ) : (
                        <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'var(--color-card-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <User size={32} />
                        </div>
                    )}
                    <div>
                        <h1 style={{ fontSize: '28px', margin: 0 }}>{userProfile.username}</h1>
                        <p style={{ color: 'var(--color-text-secondary)', margin: '4px 0 0' }}>
                            Member since {new Date(userProfile.created_at).toLocaleDateString()}
                        </p>
                    </div>
                </div>

                {/* Stats Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
                    <div style={statCardStyle}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-secondary)' }}>
                            <TrendingUp size={18} />
                            <span>Points</span>
                        </div>
                        <div style={{ fontSize: '32px', fontWeight: 700 }}>{stats.contribution_points}</div>
                    </div>
                    <div style={statCardStyle}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-secondary)' }}>
                            <Award size={18} />
                            <span>Contributions</span>
                        </div>
                        <div style={{ fontSize: '32px', fontWeight: 700 }}>{stats.contributions_made}</div>
                    </div>
                    <div style={statCardStyle}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-secondary)' }}>
                            <Target size={18} />
                            <span>Quests</span>
                        </div>
                        <div style={{ fontSize: '32px', fontWeight: 700 }}>{stats.quests_completed}</div>
                    </div>
                    <div style={statCardStyle}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-secondary)' }}>
                            <Calendar size={18} />
                            <span>Messages</span>
                        </div>
                        <div style={{ fontSize: '32px', fontWeight: 700 }}>{stats.message_count}</div>
                    </div>
                </div>

                {/* Two Column Layout */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(350px, 100%), 1fr))', gap: '24px' }}>
                    {/* Portfolio Status */}
                    <div style={cardStyle}>
                        <h3 style={{ margin: '0 0 16px', fontSize: '18px' }}>Portfolio Status</h3>
                        {portfolio_status ? (
                            <div>
                                <div style={{
                                    display: 'inline-block',
                                    padding: '6px 12px',
                                    borderRadius: '20px',
                                    fontSize: '14px',
                                    fontWeight: 500,
                                    background: portfolio_status === 'promoted' ? '#22c55e20' :
                                               portfolio_status === 'pending_vote' ? '#eab30820' :
                                               portfolio_status === 'submitted' ? '#3b82f620' : '#64748b20',
                                    color: portfolio_status === 'promoted' ? '#22c55e' :
                                           portfolio_status === 'pending_vote' ? '#eab308' :
                                           portfolio_status === 'submitted' ? '#3b82f6' : '#64748b',
                                }}>
                                    {portfolio_status.replace('_', ' ').toUpperCase()}
                                </div>
                                <a href="/portfolio" style={{ display: 'block', marginTop: '16px', color: 'var(--color-primary)' }}>
                                    View Portfolio →
                                </a>
                            </div>
                        ) : (
                            <div>
                                <p style={{ color: 'var(--color-text-secondary)', margin: '0 0 16px' }}>
                                    No portfolio yet. Create one to apply for role promotion.
                                </p>
                                <a href="/portfolio" className="btn btn-primary" style={{ padding: '10px 20px', fontSize: '14px' }}>
                                    Create Portfolio
                                </a>
                            </div>
                        )}
                    </div>

                    {/* Guild Info */}
                    <div style={cardStyle}>
                        <h3 style={{ margin: '0 0 16px', fontSize: '18px' }}>Guild</h3>
                        {guild_info ? (
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                                    <span style={{ fontSize: '24px' }}>
                                        {guild_info.name === 'traders' ? '📈' : guild_info.name === 'content' ? '✍️' : '🎨'}
                                    </span>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{guild_info.name.charAt(0).toUpperCase() + guild_info.name.slice(1)} Guild</div>
                                        <div style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>{guild_info.role_type} • Tier {guild_info.tier}</div>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: '24px', marginTop: '16px' }}>
                                    <div>
                                        <div style={{ fontSize: '24px', fontWeight: 700 }}>{guild_info.points}</div>
                                        <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Points</div>
                                    </div>
                                    <div>
                                        <div style={{ fontSize: '24px', fontWeight: 700 }}>{guild_info.quests_completed}</div>
                                        <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Quests</div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
                                Not in a guild yet. Use <code>/guild join</code> in Discord!
                            </p>
                        )}
                    </div>

                    {/* Recent Contributions */}
                    <div style={cardStyle}>
                        <h3 style={{ margin: '0 0 16px', fontSize: '18px' }}>Recent Contributions</h3>
                        {recent_contributions.length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                {recent_contributions.slice(0, 5).map((c, i) => (
                                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                            <div style={{ fontWeight: 500 }}>{c.title}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{c.category}</div>
                                        </div>
                                        <div style={{ fontSize: '14px', color: '#22c55e' }}>+{c.upvotes}</div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>No contributions yet.</p>
                        )}
                    </div>

                    {/* Promotion History */}
                    <div style={cardStyle}>
                        <h3 style={{ margin: '0 0 16px', fontSize: '18px' }}>Promotion History</h3>
                        {promotion_history.length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                {promotion_history.map((p, i) => (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e' }} />
                                        <div>
                                            <div style={{ fontWeight: 500 }}>{p.from_role} → {p.to_role}</div>
                                            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                                                {new Date(p.promoted_at).toLocaleDateString()}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>No promotions yet.</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
```

## liquidweb/src/pages/PortfolioView.jsx

**Path**: `liquidweb/src/pages/PortfolioView.jsx`

```jsx
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
```
