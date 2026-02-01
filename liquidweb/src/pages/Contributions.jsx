import React, { useState, useEffect } from 'react';
import { ThumbsUp, ThumbsDown, Plus, ExternalLink, Filter, Sparkles } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Contributions = () => {
    const { user, isAuthenticated, login } = useAuth();
    const [contributions, setContributions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        content_url: '',
        category: 'article',
    });
    const [submitting, setSubmitting] = useState(false);
    const [message, setMessage] = useState(null);

    const discordId = user?.discord_id || '';

    const categories = ['article', 'video', 'tool', 'design', 'tutorial', 'other'];

    useEffect(() => {
        fetchContributions();
    }, [filter]);

    const fetchContributions = async () => {
        try {
            let url = `${API_BASE}/api/contributions/`;
            if (filter !== 'all') {
                url += `?category=${filter}`;
            }
            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                setContributions(data);
            }
        } catch (err) {
            console.error('Failed to fetch contributions:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleVote = async (contributionId, voteType) => {
        if (!isAuthenticated) {
            setMessage({ type: 'error', text: 'Please login to vote' });
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/api/contributions/vote`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contribution_id: contributionId,
                    voter_discord_id: discordId,
                    vote_type: voteType,
                }),
            });
            if (res.ok) {
                fetchContributions();
            } else {
                const err = await res.json();
                setMessage({ type: 'error', text: err.detail || 'Failed to vote' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to vote' });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!isAuthenticated) {
            setMessage({ type: 'error', text: 'Please login to submit' });
            return;
        }

        setSubmitting(true);
        setMessage(null);

        try {
            const res = await fetch(`${API_BASE}/api/contributions/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...formData,
                    discord_id: discordId,
                }),
            });
            if (res.ok) {
                setMessage({ type: 'success', text: 'Contribution submitted!' });
                setShowForm(false);
                setFormData({ title: '', description: '', content_url: '', category: 'article' });
                fetchContributions();
            } else {
                const err = await res.json();
                setMessage({ type: 'error', text: err.detail || 'Failed to submit' });
            }
        } catch (err) {
            setMessage({ type: 'error', text: 'Failed to submit contribution' });
        } finally {
            setSubmitting(false);
        }
    };

    const cardStyle = {
        background: 'var(--color-card-bg)',
        borderRadius: '16px',
        padding: '20px',
        border: '1px solid var(--color-badge-border)',
    };

    const inputStyle = {
        width: '100%',
        padding: '12px 16px',
        borderRadius: '8px',
        border: '1px solid var(--color-badge-border)',
        background: 'var(--color-bg)',
        color: 'var(--color-text)',
        fontSize: '14px',
        fontFamily: 'inherit',
    };

    const categoryColors = {
        article: '#3b82f6',
        video: '#ef4444',
        tool: '#22c55e',
        design: '#a855f7',
        tutorial: '#eab308',
        other: '#64748b',
    };

    return (
        <div style={{ minHeight: '100vh', padding: '120px 20px 40px', background: 'var(--color-bg)' }}>
            <div className="container" style={{ maxWidth: '900px', margin: '0 auto' }}>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px', flexWrap: 'wrap', gap: '16px' }}>
                    <div>
                        <h1 style={{ fontSize: '28px', margin: '0 0 8px' }}>Contributions</h1>
                        <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
                            Community-submitted content and resources
                        </p>
                    </div>
                    {isAuthenticated ? (
                        <button
                            className="btn btn-primary"
                            onClick={() => setShowForm(!showForm)}
                            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                        >
                            <Plus size={18} />
                            Submit
                        </button>
                    ) : (
                        <button
                            className="btn btn-primary"
                            onClick={login}
                            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.36-.698.772-1.362 1.225-1.993a.076.076 0 0 0-.041-.107 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.12-.094.246-.194.372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
                            </svg>
                            Login to Submit
                        </button>
                    )}
                </div>

                {/* Message */}
                {message && (
                    <div style={{
                        padding: '12px 16px',
                        borderRadius: '8px',
                        marginBottom: '24px',
                        background: message.type === 'success' ? '#22c55e20' : '#ef444420',
                        color: message.type === 'success' ? '#22c55e' : '#ef4444',
                    }}>
                        {message.text}
                    </div>
                )}

                {/* Submit Form */}
                {showForm && (
                    <div style={{ ...cardStyle, marginBottom: '24px' }}>
                        <h3 style={{ margin: '0 0 16px' }}>Submit Contribution</h3>
                        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div>
                                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, fontSize: '14px' }}>Title</label>
                                <input
                                    type="text"
                                    style={inputStyle}
                                    placeholder="Title of your contribution"
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, fontSize: '14px' }}>Description</label>
                                <textarea
                                    style={{ ...inputStyle, minHeight: '80px', resize: 'vertical' }}
                                    placeholder="Describe your contribution..."
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    required
                                />
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, fontSize: '14px' }}>URL</label>
                                    <input
                                        type="url"
                                        style={inputStyle}
                                        placeholder="https://..."
                                        value={formData.content_url}
                                        onChange={(e) => setFormData({ ...formData, content_url: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, fontSize: '14px' }}>Category</label>
                                    <select
                                        style={inputStyle}
                                        value={formData.category}
                                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                                    >
                                        {categories.map(cat => (
                                            <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '12px' }}>
                                <button
                                    type="button"
                                    className="btn"
                                    style={{ background: 'var(--color-badge-border)', color: 'var(--color-text)' }}
                                    onClick={() => setShowForm(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={submitting}
                                >
                                    {submitting ? 'Submitting...' : 'Submit'}
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Filters */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
                    <button
                        className="btn"
                        style={{
                            padding: '8px 16px',
                            fontSize: '13px',
                            background: filter === 'all' ? 'var(--color-primary)' : 'var(--color-card-bg)',
                            color: filter === 'all' ? 'var(--color-primary-text)' : 'var(--color-text)',
                        }}
                        onClick={() => setFilter('all')}
                    >
                        All
                    </button>
                    {categories.map(cat => (
                        <button
                            key={cat}
                            className="btn"
                            style={{
                                padding: '8px 16px',
                                fontSize: '13px',
                                background: filter === cat ? categoryColors[cat] : 'var(--color-card-bg)',
                                color: filter === cat ? '#fff' : 'var(--color-text)',
                            }}
                            onClick={() => setFilter(cat)}
                        >
                            {cat.charAt(0).toUpperCase() + cat.slice(1)}
                        </button>
                    ))}
                </div>

                {/* Contributions List */}
                {loading ? (
                    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
                        Loading...
                    </div>
                ) : contributions.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
                        No contributions yet. Be the first to submit!
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        {contributions.map((contribution) => (
                            <div key={contribution.id} style={cardStyle}>
                                <div style={{ display: 'flex', gap: '16px' }}>
                                    {/* Vote Column */}
                                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', minWidth: '50px' }}>
                                        <button
                                            style={{
                                                background: 'none',
                                                border: 'none',
                                                cursor: 'pointer',
                                                padding: '4px',
                                                color: 'var(--color-text-secondary)',
                                            }}
                                            onClick={() => handleVote(contribution.id, 'upvote')}
                                        >
                                            <ThumbsUp size={20} />
                                        </button>
                                        <span style={{
                                            fontWeight: 700,
                                            fontSize: '16px',
                                            color: contribution.upvotes - contribution.downvotes > 0 ? '#22c55e' :
                                                   contribution.upvotes - contribution.downvotes < 0 ? '#ef4444' : 'var(--color-text)',
                                        }}>
                                            {contribution.upvotes - contribution.downvotes}
                                        </span>
                                        <button
                                            style={{
                                                background: 'none',
                                                border: 'none',
                                                cursor: 'pointer',
                                                padding: '4px',
                                                color: 'var(--color-text-secondary)',
                                            }}
                                            onClick={() => handleVote(contribution.id, 'downvote')}
                                        >
                                            <ThumbsDown size={20} />
                                        </button>
                                    </div>

                                    {/* Content */}
                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px', flexWrap: 'wrap' }}>
                                            <h3 style={{ margin: 0, fontSize: '16px' }}>{contribution.title}</h3>
                                            <span style={{
                                                padding: '2px 8px',
                                                borderRadius: '4px',
                                                fontSize: '11px',
                                                fontWeight: 500,
                                                background: categoryColors[contribution.category] + '20',
                                                color: categoryColors[contribution.category],
                                            }}>
                                                {contribution.category}
                                            </span>
                                            {contribution.is_featured && (
                                                <span style={{
                                                    padding: '2px 8px',
                                                    borderRadius: '4px',
                                                    fontSize: '11px',
                                                    fontWeight: 500,
                                                    background: '#eab30820',
                                                    color: '#eab308',
                                                }}>
                                                    ⭐ Featured
                                                </span>
                                            )}
                                        </div>
                                        <p style={{ margin: '0 0 12px', color: 'var(--color-text-secondary)', fontSize: '14px' }}>
                                            {contribution.description}
                                        </p>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
                                            <span>by {contribution.author_username || 'Unknown'}</span>
                                            <span>{new Date(contribution.created_at).toLocaleDateString()}</span>
                                            {contribution.content_url && (
                                                <a
                                                    href={contribution.content_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-primary)' }}
                                                >
                                                    <ExternalLink size={14} />
                                                    View
                                                </a>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Contributions;
