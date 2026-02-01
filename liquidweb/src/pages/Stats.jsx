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
