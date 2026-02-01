import React from 'react';
import {
    AreaChart,
    Area,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,
} from 'recharts';

// Use the primary/accent colors from the design
const COLORS = ['#EDEDFF', '#E0DFEF', '#949494', '#666666', '#333333'];

const chartContainerStyle = {
    background: 'var(--color-card-bg)',
    borderRadius: 'var(--border-radius)',
    padding: '24px',
    border: '1px solid var(--color-badge-border)',
    boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
};

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div style={{
                background: 'rgba(19, 19, 24, 0.95)',
                border: '1px solid var(--color-badge-border)',
                borderRadius: '12px',
                padding: '12px 16px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                backdropFilter: 'blur(8px)',
            }}>
                <p style={{ margin: 0, fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>{label}</p>
                <p style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: 'var(--color-primary)' }}>
                    {payload[0].value.toLocaleString()}
                </p>
            </div>
        );
    }
    return null;
};

export const ActivityChart = ({ data, title, dataKey = 'count', xAxisKey = 'date' }) => {
    if (!data || data.length === 0) {
        return (
            <div style={chartContainerStyle}>
                <h4 style={{ margin: '0 0 20px', fontSize: '18px', fontWeight: 600, color: 'var(--color-text)' }}>{title}</h4>
                <div style={{ height: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-secondary)' }}>
                    No data available
                </div>
            </div>
        );
    }

    return (
        <div style={chartContainerStyle}>
            <h4 style={{ margin: '0 0 20px', fontSize: '18px', fontWeight: 600, color: 'var(--color-text)' }}>{title}</h4>
            <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorActivity" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis
                        dataKey={xAxisKey}
                        stroke="var(--color-text-secondary)"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                        dy={10}
                    />
                    <YAxis
                        stroke="var(--color-text-secondary)"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                        dx={-10}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 2 }} />
                    <Area
                        type="monotone"
                        dataKey={dataKey}
                        stroke="var(--color-primary)"
                        strokeWidth={3}
                        fillOpacity={1}
                        fill="url(#colorActivity)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export const ContributorsChart = ({ data, title }) => {
    if (!data || data.length === 0) {
        return (
            <div style={chartContainerStyle}>
                <h4 style={{ margin: '0 0 20px', fontSize: '18px', fontWeight: 600, color: 'var(--color-text)' }}>{title}</h4>
                <div style={{ height: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-secondary)' }}>
                    No data available
                </div>
            </div>
        );
    }

    return (
        <div style={chartContainerStyle}>
            <h4 style={{ margin: '0 0 20px', fontSize: '18px', fontWeight: 600, color: 'var(--color-text)' }}>{title}</h4>
            <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.slice(0, 10)} layout="vertical" margin={{ top: 5, right: 20, left: 60, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                    <XAxis type="number" stroke="var(--color-text-secondary)" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis
                        dataKey="username"
                        type="category"
                        stroke="var(--color-text-secondary)"
                        fontSize={12}
                        width={60}
                        tickLine={false}
                        axisLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                    <Bar dataKey="points" fill="var(--color-primary)" radius={[0, 4, 4, 0]} barSize={20} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

export const DistributionChart = ({ data, title }) => {
    if (!data || data.length === 0) {
        return (
            <div style={chartContainerStyle}>
                <h4 style={{ margin: '0 0 20px', fontSize: '18px', fontWeight: 600, color: 'var(--color-text)' }}>{title}</h4>
                <div style={{ height: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-secondary)' }}>
                    No data available
                </div>
            </div>
        );
    }

    return (
        <div style={chartContainerStyle}>
            <h4 style={{ margin: '0 0 20px', fontSize: '18px', fontWeight: 600, color: 'var(--color-text)' }}>{title}</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                <ResponsiveContainer width="50%" height={200}>
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={80}
                            paddingAngle={4}
                            dataKey="value"
                            stroke="none"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                </ResponsiveContainer>
                <div style={{ flex: 1 }}>
                    {data.map((item, index) => (
                        <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: COLORS[index % COLORS.length] }} />
                            <span style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>{item.name}</span>
                            <span style={{ fontSize: '14px', fontWeight: 600, marginLeft: 'auto', color: 'var(--color-text)' }}>{item.value}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export const StatsCard = ({ icon: Icon, image, label, value, trend, color = 'var(--color-text)' }) => (
    <div style={{
        background: 'var(--color-card-bg)',
        borderRadius: 'var(--border-radius)',
        padding: '24px',
        border: '1px solid var(--color-badge-border)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        transition: 'all 0.3s ease',
        cursor: 'default',
        backdropFilter: 'blur(20px)',
        position: 'relative',
        overflow: 'hidden',
    }}
        className="stats-card"
    >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            {image ? (
                <img src={image} alt={label} style={{ width: '24px', height: '24px', objectFit: 'contain' }} />
            ) : Icon ? (
                <Icon size={24} style={{ color: 'var(--color-text-secondary)' }} />
            ) : null}
            <span style={{ fontSize: '14px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>{label}</span>
        </div>
        <div style={{ fontSize: '36px', fontWeight: 700, color: 'var(--color-text)', letterSpacing: '-0.02em' }}>{value}</div>
        {trend && (
            <div style={{
                fontSize: '13px',
                marginTop: '8px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 8px',
                borderRadius: '99px',
                background: trend > 0 ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                color: trend > 0 ? '#4ade80' : '#f87171'
            }}>
                {trend > 0 ? '↑' : trend < 0 ? '↓' : ''} {Math.abs(trend)}%
            </div>
        )}
    </div>
);

export default { ActivityChart, ContributorsChart, DistributionChart, StatsCard };
