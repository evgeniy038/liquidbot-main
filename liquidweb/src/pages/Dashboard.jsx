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
