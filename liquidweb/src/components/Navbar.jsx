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
