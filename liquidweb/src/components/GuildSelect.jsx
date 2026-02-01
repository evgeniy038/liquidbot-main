import React from 'react';
import { Shield, Palette, PenTool, Check, TrendingUp } from 'lucide-react';

const GUILDS = [
    {
        id: 'traders',
        name: 'Traders Guild',
        emoji: '📈',
        icon: TrendingUp,
        image: '/images/Traders_Guild.png',
        description: 'Active traders and market analysts',
        color: '#3b82f6',
        requirements: [
            'Active trading history',
            'Share market analysis',
            'Participate in competitions',
        ],
    },
    {
        id: 'creators',
        name: 'Creators Guild',
        emoji: '✍️',
        icon: PenTool,
        image: '/images/Content_Orator.png',
        description: 'Content creators and writers',
        color: '#22c55e',
        requirements: [
            'Create educational content',
            'Write threads about Liquid',
            'Produce videos or tutorials',
        ],
    },
    {
        id: 'artists',
        name: 'Artists Guild',
        emoji: '🎨',
        icon: Palette,
        image: '/images/Artists_Guild.png',
        description: 'Designers and visual artists',
        color: '#a855f7',
        requirements: [
            'Create visual content and art',
            'Design graphics and memes',
            'Build community tools',
        ],
    },
];

export const GuildCard = ({ guild, selected, onSelect, disabled }) => {
    const Icon = guild.icon;
    const isSelected = selected === guild.id;

    return (
        <button
            onClick={() => !disabled && onSelect(guild.id)}
            disabled={disabled}
            style={{
                background: isSelected ? `${guild.color}15` : 'var(--color-card-bg)',
                borderRadius: '16px',
                padding: '24px',
                border: `2px solid ${isSelected ? guild.color : 'var(--color-badge-border)'}`,
                cursor: disabled ? 'not-allowed' : 'pointer',
                textAlign: 'left',
                transition: 'all 0.2s',
                opacity: disabled ? 0.6 : 1,
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            {isSelected && (
                <div style={{
                    position: 'absolute',
                    top: '12px',
                    right: '12px',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    background: guild.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 10,
                }}>
                    <Check size={14} color="white" />
                </div>
            )}
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
                <div style={{
                    width: '56px',
                    height: '56px',
                    borderRadius: '12px',
                    background: `${guild.color}20`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                }}>
                    {guild.image ? (
                        <img src={guild.image} alt={guild.name} style={{ width: '32px', height: '32px', objectFit: 'contain' }} />
                    ) : (
                        <Icon size={28} style={{ color: guild.color }} />
                    )}
                </div>
                <div>
                    <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--color-text)' }}>
                        {guild.name}
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
                        {guild.description}
                    </div>
                </div>
            </div>

            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--color-badge-border)' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)', marginBottom: '10px' }}>
                    Requirements
                </div>
                <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                    {guild.requirements.map((req, i) => (
                        <li key={i} style={{ marginBottom: '6px', fontSize: '13px', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'start', gap: '8px' }}>
                            <span style={{ color: guild.color, lineHeight: '1.4' }}>•</span>
                            <span>{req}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </button>
    );
};

export const GuildSelect = ({ selected, onSelect, disabled = false }) => {
    return (
        <div>
            <h3 style={{ margin: '0 0 8px', fontSize: '20px', fontWeight: 600 }}>Select Your Guild</h3>
            <p style={{ margin: '0 0 24px', color: 'var(--color-text-secondary)' }}>
                Choose the guild that best matches your contributions
            </p>
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '16px',
            }}>
                {GUILDS.map((guild) => (
                    <GuildCard
                        key={guild.id}
                        guild={guild}
                        selected={selected}
                        onSelect={onSelect}
                        disabled={disabled}
                    />
                ))}
            </div>
        </div>
    );
};

export const GuildBadge = ({ guildId, size = 'medium' }) => {
    const guild = GUILDS.find(g => g.id === guildId);
    if (!guild) return null;

    const sizes = {
        small: { padding: '4px 8px', fontSize: '12px', iconSize: 12 },
        medium: { padding: '6px 12px', fontSize: '13px', iconSize: 14 },
        large: { padding: '8px 16px', fontSize: '14px', iconSize: 16 },
    };

    const s = sizes[size] || sizes.medium;
    const Icon = guild.icon;

    return (
        <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: s.padding,
            borderRadius: '20px',
            background: `${guild.color}20`,
            color: guild.color,
            fontSize: s.fontSize,
            fontWeight: 500,
        }}>
            {guild.image ? (
                <img src={guild.image} alt="" style={{ width: s.iconSize, height: s.iconSize, objectFit: 'contain' }} />
            ) : (
                <Icon size={s.iconSize} />
            )}
            {guild.name}
        </div>
    );
};

export { GUILDS };
export default GuildSelect;
