import React, { Suspense } from 'react';
import { Tweet } from 'react-tweet';
import { ExternalLink, Twitter } from 'lucide-react';

const extractTweetId = (urlOrId) => {
    if (!urlOrId) return null;
    if (/^\d+$/.test(urlOrId)) return urlOrId;
    const patterns = [
        /twitter\.com\/\w+\/status\/(\d+)/,
        /x\.com\/\w+\/status\/(\d+)/,
        /x\.com\/i\/status\/(\d+)/,
    ];
    for (const pattern of patterns) {
        const match = urlOrId.match(pattern);
        if (match) return match[1];
    }
    return null;
};

const extractUsername = (url) => {
    if (!url) return null;
    const match = url.match(/(?:twitter\.com|x\.com)\/(\w+)\/status/);
    return match ? match[1] : null;
};

const TweetSkeleton = () => (
    <div style={{
        background: 'var(--color-card-bg)',
        borderRadius: '16px',
        padding: '20px',
        border: '1px solid var(--color-badge-border)',
        minHeight: '200px',
    }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.1)',
                animation: 'pulse 1.5s infinite',
            }} />
            <div style={{ flex: 1 }}>
                <div style={{
                    width: '120px',
                    height: '14px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '4px',
                    marginBottom: '8px',
                    animation: 'pulse 1.5s infinite',
                }} />
                <div style={{
                    width: '80px',
                    height: '12px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '4px',
                    animation: 'pulse 1.5s infinite',
                }} />
            </div>
        </div>
        <div style={{
            width: '100%',
            height: '60px',
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '8px',
            animation: 'pulse 1.5s infinite',
        }} />
        <style>{`
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        `}</style>
    </div>
);

export const TweetEmbed = ({ tweetId }) => {
    if (!tweetId) return null;
    
    return (
        <div className="tweet-wrapper" style={{ width: '100%', maxWidth: '550px' }}>
            <Suspense fallback={<TweetSkeleton />}>
                <Tweet id={tweetId} />
            </Suspense>
        </div>
    );
};

export const TweetCard = ({ tweetUrl, showMetrics = true, useEmbed = false }) => {
    const tweetId = extractTweetId(tweetUrl);
    const username = extractUsername(tweetUrl);
    
    if (!tweetId) {
        return (
            <div style={{
                background: 'var(--color-card-bg)',
                borderRadius: '16px',
                padding: '20px',
                border: '1px solid var(--color-badge-border)',
                textAlign: 'center',
                color: 'var(--color-text-secondary)',
            }}>
                Invalid tweet URL
            </div>
        );
    }

    if (useEmbed) {
        return (
            <div className="tweet-wrapper" style={{ width: '100%', maxWidth: '550px' }}>
                <Suspense fallback={<TweetSkeleton />}>
                    <Tweet id={tweetId} />
                </Suspense>
            </div>
        );
    }

    const tweetLink = `https://x.com/${username || 'i'}/status/${tweetId}`;

    return (
        <a 
            href={tweetLink}
            target="_blank"
            rel="noopener noreferrer"
            style={{
                display: 'block',
                background: 'var(--color-card-bg)',
                borderRadius: '12px',
                border: '1px solid var(--color-badge-border)',
                padding: '16px',
                textDecoration: 'none',
                transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-primary)';
                e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--color-badge-border)';
                e.currentTarget.style.transform = 'translateY(0)';
            }}
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: 'rgba(29, 161, 242, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}>
                    <Twitter size={20} style={{ color: '#1DA1F2' }} />
                </div>
                <div style={{ flex: 1 }}>
                    <div style={{ 
                        color: 'var(--color-text)', 
                        fontWeight: 500,
                        fontSize: '14px',
                    }}>
                        @{username || 'tweet'}
                    </div>
                    <div style={{ 
                        color: 'var(--color-text-secondary)', 
                        fontSize: '12px',
                        marginTop: '2px',
                    }}>
                        Tweet ID: {tweetId.slice(-8)}...
                    </div>
                </div>
                <ExternalLink size={16} style={{ color: 'var(--color-text-secondary)' }} />
            </div>
        </a>
    );
};

export const TweetGrid = ({ tweets, columns = 2, useEmbed = false }) => {
    if (!tweets || tweets.length === 0) {
        return (
            <div style={{
                background: 'var(--color-card-bg)',
                borderRadius: '16px',
                padding: '40px',
                border: '1px solid var(--color-badge-border)',
                textAlign: 'center',
                color: 'var(--color-text-secondary)',
            }}>
                <Twitter size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
                <p style={{ margin: 0 }}>No tweets to display</p>
            </div>
        );
    }

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: useEmbed ? '1fr' : `repeat(${columns}, 1fr)`,
            gap: '16px',
        }}>
            {tweets.map((tweet, index) => (
                <TweetCard key={index} tweetUrl={tweet} useEmbed={useEmbed} />
            ))}
        </div>
    );
};

export const TweetEmbedGrid = ({ tweetIds, columns = 1 }) => {
    if (!tweetIds || tweetIds.length === 0) {
        return (
            <div style={{
                background: 'var(--color-card-bg)',
                borderRadius: '16px',
                padding: '40px',
                border: '1px solid var(--color-badge-border)',
                textAlign: 'center',
                color: 'var(--color-text-secondary)',
            }}>
                <Twitter size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
                <p style={{ margin: 0 }}>No tweets to display</p>
            </div>
        );
    }

    return (
        <div style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${columns}, 1fr)`,
            gap: '16px',
        }}>
            {tweetIds.map((tweetId) => (
                <TweetEmbed key={tweetId} tweetId={tweetId} />
            ))}
        </div>
    );
};

export default TweetCard;
