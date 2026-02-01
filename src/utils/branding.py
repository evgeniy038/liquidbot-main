"""Branding constants for consistent embed styling."""

# Footer branding - used across all embeds
FOOTER_TEXT = "tryliquid.xyz"
FOOTER_ICON_URL = "https://i.imgur.com/mSMjmxY.png"

# Embed color
EMBED_COLOR = 0x6FC5EF


def get_footer_kwargs() -> dict:
    """Get footer kwargs for embed.set_footer()."""
    return {
        "text": FOOTER_TEXT,
        "icon_url": FOOTER_ICON_URL,
    }
