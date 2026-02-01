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
