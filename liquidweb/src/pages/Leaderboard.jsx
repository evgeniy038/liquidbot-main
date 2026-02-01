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
