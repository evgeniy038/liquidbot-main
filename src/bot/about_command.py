"""
About command for server information with interactive buttons.

Provides an informational hub with sections for links, rules, and roles.
Users can click buttons to navigate between different information sections.
"""

from datetime import datetime
from typing import Dict, Optional
import discord
from discord.ui import Button, View
from src.utils import get_config, get_logger

logger = get_logger(__name__)


class NotificationPingsView(View):
    """View with notification ping toggle buttons."""
    
    # Role configurations: (custom_id, label, emoji, role_id)
    PING_ROLES = [
        ("ping:community_news", "community news", "📰", "1445433060400173086"),
        ("ping:events", "events", "🔔", "1444695708816117923"),
        ("ping:updates", "updates", "📡", "1445432034615890051"),
    ]
    
    def __init__(self, config=None):
        super().__init__(timeout=None)
        self.config = config
        
        # Add all ping buttons
        for custom_id, label, emoji, _ in self.PING_ROLES:
            self.add_item(Button(
                style=discord.ButtonStyle.secondary,  # Gray color
                label=label,
                emoji=emoji,
                custom_id=custom_id,
            ))
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Handle ping button clicks."""
        try:
            custom_id = interaction.data.get("custom_id", "")
            
            # Find the role config for this button
            role_config = None
            for cid, label, emoji, role_id in self.PING_ROLES:
                if cid == custom_id:
                    role_config = (label, emoji, role_id)
                    break
            
            if not role_config:
                return False
            
            label, emoji, role_id = role_config
            
            guild = interaction.guild
            if not guild:
                await interaction.response.send_message(
                    "❌ This command only works in a server.",
                    ephemeral=True,
                )
                return False
            
            role = guild.get_role(int(role_id))
            if not role:
                await interaction.response.send_message(
                    f"❌ {label} role not found.",
                    ephemeral=True,
                )
                return False
            
            member = interaction.user
            if not isinstance(member, discord.Member):
                member = guild.get_member(interaction.user.id)
            
            if not member:
                await interaction.response.send_message(
                    "❌ Could not find your member data.",
                    ephemeral=True,
                )
                return False
            
            # Toggle role
            if role in member.roles:
                await member.remove_roles(role, reason=f"{label} ping toggle")
                await interaction.response.send_message(
                    f"🔕 **{label}** disabled",
                    ephemeral=True,
                )
                logger.info(f"{label}_disabled | @{member.name}")
            else:
                await member.add_roles(role, reason=f"{label} ping toggle")
                await interaction.response.send_message(
                    f"{emoji} **{label}** enabled",
                    ephemeral=True,
                )
                logger.info(f"{label}_enabled | @{member.name}")
            
            return True
        
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage this role.",
                ephemeral=True,
            )
            return False
        except Exception as e:
            logger.error(f"ping_toggle_error: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Something went wrong. Please try again.",
                ephemeral=True,
            )
            return False


# Alias for backwards compatibility
EventsPingView = NotificationPingsView


class GuildsView(View):
    """View with guild selection buttons."""
    
    # Guild configurations: (custom_id, label, emoji, role_key)
    GUILDS = [
        ("guild:helpers", "Helpers Guild", "🛡️", "helpers"),
        ("guild:creators", "Creators Guild", "🎨", "creators"),
        ("guild:artists", "Artists Guild", "🎭", "artists"),
    ]
    
    def __init__(self, config=None):
        super().__init__(timeout=None)
        self.config = config
        
        # Add guild buttons
        for custom_id, label, emoji, _ in self.GUILDS:
            self.add_item(Button(
                style=discord.ButtonStyle.secondary,
                label=label,
                emoji=emoji,
                custom_id=custom_id,
            ))
    
    def _save_guild_assignment(self, user_id: int, guild_key: str) -> None:
        """Save user's guild assignment to database for website detection."""
        import sqlite3
        from pathlib import Path
        
        db_path = Path("bot_data.db")
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_guilds (
                    user_id TEXT PRIMARY KEY,
                    guild_key TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert or replace
            cursor.execute("""
                INSERT OR REPLACE INTO user_guilds (user_id, guild_key, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (str(user_id), guild_key))
            
            conn.commit()
            logger.info(f"Saved guild assignment | user_id={user_id} | guild={guild_key}")
        except Exception as e:
            logger.error(f"Error saving guild assignment: {e}")
        finally:
            if conn:
                conn.close()
    
    def _get_guild_roles(self, guild: discord.Guild) -> dict:
        """Get guild role IDs from config."""
        try:
            config = get_config()
            # Try to get roles from config
            roles_config = getattr(config, 'roles', None)
            if roles_config is None:
                # Fallback to hardcoded test server values from roles_test.yaml
                logger.info("Using hardcoded guild role IDs")
                return {
                    "helpers": "1448186201675665430",
                    "creators": "1448186354650583103",
                    "artists": "1448186290960072744",
                }
            guilds_config = roles_config.get("guilds", {})
            return {
                "helpers": guilds_config.get("helpers"),
                "creators": guilds_config.get("creators"),
                "artists": guilds_config.get("artists"),
            }
        except Exception as e:
            logger.error(f"Error getting guild roles config: {e}")
            # Fallback to hardcoded values
            return {
                "helpers": "1448186201675665430",
                "creators": "1448186354650583103",
                "artists": "1448186290960072744",
            }
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Handle guild button clicks."""
        try:
            custom_id = interaction.data.get("custom_id", "")
            logger.info(f"Guild button clicked | user={interaction.user.name} | button={custom_id}")
            
            # Find the guild config for this button
            guild_config = None
            for cid, label, emoji, role_key in self.GUILDS:
                if cid == custom_id:
                    guild_config = (label, emoji, role_key)
                    break
            
            if not guild_config:
                logger.warning(f"Unknown guild button: {custom_id}")
                return False
            
            label, emoji, role_key = guild_config
            
            guild = interaction.guild
            if not guild:
                await interaction.response.send_message(
                    "❌ This command only works in a server.",
                    ephemeral=True,
                )
                return False
            
            # Get all guild role IDs
            guild_roles = self._get_guild_roles(guild)
            target_role_id = guild_roles.get(role_key)
            
            if not target_role_id:
                await interaction.response.send_message(
                    f"❌ {label} role not configured.",
                    ephemeral=True,
                )
                return False
            
            target_role = guild.get_role(int(target_role_id))
            if not target_role:
                await interaction.response.send_message(
                    f"❌ {label} role not found.",
                    ephemeral=True,
                )
                return False
            
            member = interaction.user
            if not isinstance(member, discord.Member):
                member = guild.get_member(interaction.user.id)
            
            if not member:
                await interaction.response.send_message(
                    "❌ Could not find your member data.",
                    ephemeral=True,
                )
                return False
            
            # Check if user already has this guild role
            if target_role in member.roles:
                await interaction.response.send_message(
                    f"⚔️ You are already in **{label}**!",
                    ephemeral=True,
                )
                return True
            
            # Remove any existing guild roles first (only one guild at a time)
            roles_to_remove = []
            for key, rid in guild_roles.items():
                if rid and key != role_key:
                    existing_role = guild.get_role(int(rid))
                    if existing_role and existing_role in member.roles:
                        roles_to_remove.append(existing_role)
            
            # Remove old guild roles
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Switching guilds")
                old_names = ", ".join([r.name for r in roles_to_remove])
                logger.info(f"guild_removed | @{member.name} | removed: {old_names}")
            
            # Add new guild role
            await member.add_roles(target_role, reason=f"Joined {label}")
            
            # Save guild assignment to database for website detection
            self._save_guild_assignment(member.id, role_key)
            
            if roles_to_remove:
                await interaction.response.send_message(
                    f"⚔️ Welcome to **{label}**!\n"
                    f"*(Previous guild role removed)*",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"⚔️ Welcome to **{label}**!",
                    ephemeral=True,
                )
            
            logger.info(f"guild_joined | @{member.name} | {label}")
            return True
        
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage this role.",
                ephemeral=True,
            )
            return False
        except Exception as e:
            logger.error(f"guild_selection_error: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Something went wrong. Please try again.",
                ephemeral=True,
            )
            return False


class AboutView(View):
    """
    Interactive view with buttons for different information sections.
    
    Buttons:
    - Links: Official links and resources
    - Rules: Server rules
    - Roles: Role information and hierarchy
    """
    
    def __init__(self, config):
        """
        Initialize about view with buttons.
        
        Args:
            config: About command configuration
        """
        super().__init__(timeout=None)  # Persistent view
        self.config = config
        
        # Add buttons for each section with configurable emojis
        self.add_item(Button(
            style=discord.ButtonStyle.success,
            label="links",
            emoji=self._parse_emoji(config.button_emojis.get("links", "↗️")),
            custom_id="about:links",
        ))
        
        self.add_item(Button(
            style=discord.ButtonStyle.secondary,
            label="rules",
            emoji=self._parse_emoji(config.button_emojis.get("rules", "📜")),
            custom_id="about:rules",
        ))
    
    def _parse_emoji(self, emoji_str: str):
        """
        Parse emoji string to support both standard and custom emojis.
        
        Args:
            emoji_str: Emoji string (standard unicode or custom <:name:id>)
            
        Returns:
            Emoji string or PartialEmoji for custom emojis
        """
        # Custom emoji format: <:name:id> or <a:name:id>
        if emoji_str.startswith("<") and emoji_str.endswith(">"):
            # Parse custom emoji
            parts = emoji_str[1:-1].split(":")
            if len(parts) == 3:  # Format: <:name:id> or <a:name:id>
                animated = parts[0] == "a"
                name = parts[1]
                emoji_id = int(parts[2])
                return discord.PartialEmoji(name=name, id=emoji_id, animated=animated)
        
        # Standard unicode emoji
        return emoji_str
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        Handle button clicks.
        
        Args:
            interaction: Discord interaction from button click
            
        Returns:
            True to allow interaction
        """
        try:
            # Get section from custom_id (format: "about:section_name")
            section_id = interaction.data["custom_id"].split(":")[1]
            
            logger.info(
                "about_button_clicked",
                section=section_id,
                user_id=str(interaction.user.id),
                user_tag=str(interaction.user),
            )
            
            # Handle events ping role toggle
            if section_id == "events_ping":
                await self._handle_events_ping_toggle(interaction)
                return True
            
            # Build and send section embed
            embeds = self.build_section_embeds(section_id)
            
            # For roles section, add notification ping buttons
            if section_id == "roles":
                pings_view = self._build_notification_pings_view()
                await interaction.response.send_message(
                    embeds=embeds,
                    view=pings_view,
                    ephemeral=True,
                )
            # For guilds section, add guild selection buttons
            elif section_id == "guilds":
                guilds_view = self._build_guilds_view()
                await interaction.response.send_message(
                    embeds=embeds,
                    view=guilds_view,
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    embeds=embeds,
                    ephemeral=True,  # Only visible to user who clicked
                )
            
            return True
            
        except Exception as e:
            logger.error(
                "about_button_error",
                error=str(e),
                exc_info=True,
            )
            
            await interaction.response.send_message(
                "❌ Something went wrong. Please try again.",
                ephemeral=True,
            )
            
            return False
    
    def _build_notification_pings_view(self) -> View:
        """
        Build a view with notification ping toggle buttons.
        
        Returns:
            View with community news, events, and updates buttons
        """
        return NotificationPingsView()
    
    # Alias for backwards compatibility
    _build_events_ping_view = _build_notification_pings_view
    
    def _build_guilds_view(self) -> View:
        """
        Build a view with guild selection buttons.
        
        Returns:
            View with Helpers, Creators, and Artists guild buttons
        """
        return GuildsView()
    
    async def _handle_events_ping_toggle(self, interaction: discord.Interaction):
        """
        Toggle events ping role for user.
        
        Args:
            interaction: Discord interaction
        """
        try:
            # Get role ID from config
            events_config = getattr(self.config, 'events_ping', None)
            if not events_config:
                await interaction.response.send_message(
                    "❌ Events ping not configured.",
                    ephemeral=True,
                )
                return
            
            role_id = events_config.role_id
            if not role_id:
                await interaction.response.send_message(
                    "❌ Events ping role not configured.",
                    ephemeral=True,
                )
                return
            
            # Get the role from guild
            guild = interaction.guild
            if not guild:
                await interaction.response.send_message(
                    "❌ This command only works in a server.",
                    ephemeral=True,
                )
                return
            
            role = guild.get_role(int(role_id))
            if not role:
                await interaction.response.send_message(
                    "❌ Events ping role not found.",
                    ephemeral=True,
                )
                return
            
            member = interaction.user
            if not isinstance(member, discord.Member):
                member = guild.get_member(interaction.user.id)
            
            if not member:
                await interaction.response.send_message(
                    "❌ Could not find your member data.",
                    ephemeral=True,
                )
                return
            
            # Toggle role
            if role in member.roles:
                await member.remove_roles(role, reason="Events ping toggle via about command")
                await interaction.response.send_message(
                    f"🔕 **events pings disabled** - you will no longer receive event notifications.",
                    ephemeral=True,
                )
                logger.info(
                    "events_ping_disabled",
                    user_id=str(member.id),
                    user_tag=str(member),
                )
            else:
                await member.add_roles(role, reason="Events ping toggle via about command")
                await interaction.response.send_message(
                    f"🔔 **events pings enabled** - you will now receive event notifications!",
                    ephemeral=True,
                )
                logger.info(
                    "events_ping_enabled",
                    user_id=str(member.id),
                    user_tag=str(member),
                )
        
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to manage this role.",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(
                "events_ping_toggle_error",
                error=str(e),
                exc_info=True,
            )
            await interaction.response.send_message(
                "❌ Something went wrong. Please try again.",
                ephemeral=True,
            )
    
    def build_section_embeds(self, section_id: str) -> list[discord.Embed]:
        """
        Build embed(s) for a specific section.
        
        Args:
            section_id: Section identifier (links, rules, roles)
            
        Returns:
            List of embeds to display
        """
        embeds = []
        
        if section_id not in self.config.sections:
            logger.warning(
                "unknown_section_requested",
                section_id=section_id,
            )
            return [discord.Embed(
                color=0xFF0000,
                title="❌ Error",
                description="Unknown section requested.",
            )]
        
        section = self.config.sections[section_id]
        
        # Main section embed
        embed = discord.Embed(
            color=section.color,
            title=section.title,
            description=section.description,
        )
        
        # ✅ image works here
        
        embed.set_image(url=section.image_url)       
        
        embeds.append(embed)
        
        # Add additional embed if exists (e.g., "do not ask for roles")
        if hasattr(section, 'additional_embed') and section.additional_embed:
            additional = discord.Embed(
                color=section.additional_embed.color,
                title=section.additional_embed.title,
                description=section.additional_embed.description,
            )
            
            additional_cfg = section.additional_embed
            
            if getattr(additional_cfg, "image_url", None):
                additional.set_image(url=additional_cfg.image_url)
            
            embeds.append(additional)
        
        return embeds


class AboutCommand:
    """
    About command handler.
    
    Provides server information with interactive buttons.
    Only accessible by administrators and guild managers.
    """
    
    def __init__(self):
        """Initialize about command."""
        config = get_config()
        self.config = config.about_command
        self.enabled = self.config.enabled
        self.cooldown_seconds = self.config.cooldown_seconds
        
        # Cooldown tracking: {channel_id: last_use_timestamp}
        self.last_use: Dict[int, float] = {}
        
        # Silent init
    
    def can_use_command(self, member: discord.Member) -> bool:
        """
        Check if member can use the command.
        
        Args:
            member: Discord member
            
        Returns:
            True if member has permission
        """
        # Check for administrator or manage guild permission
        has_admin = member.guild_permissions.administrator
        has_manage = member.guild_permissions.manage_guild
        
        # Also allow command_access roles from config
        has_role = False
        try:
            config = get_config()
            command_access_roles = getattr(config, 'roles', {}).get("command_access", [])
            has_role = any(str(role.id) in command_access_roles for role in member.roles)
        except Exception as e:
            logger.warning(f"Error checking command_access roles: {e}")
        
        logger.info(f"!about permission check | user={member.name} | admin={has_admin} | manage={has_manage} | role_access={has_role}")
        
        return has_admin or has_manage or has_role
    
    def check_cooldown(self, channel_id: int) -> bool:
        """
        Check if command is on cooldown in this channel.
        
        Args:
            channel_id: Discord channel ID
            
        Returns:
            True if command can be used, False if on cooldown
        """
        now = datetime.now().timestamp()
        last_time = self.last_use.get(channel_id, 0)
        
        if now - last_time < self.cooldown_seconds:
            logger.debug(
                "about_command_on_cooldown",
                channel_id=channel_id,
                seconds_remaining=self.cooldown_seconds - (now - last_time),
            )
            return False
        
        # Update cooldown
        self.last_use[channel_id] = now
        return True
    
    def build_main_embed(self) -> discord.Embed:
        """
        Build main about embed.
        
        Returns:
            Main embed with server information
        """
        embed = discord.Embed(
            color=self.config.main.color,
            title=self.config.main.title,
            description=self.config.main.description,
        )
        
        # Add image if configured
        if self.config.main.image_url:
            embed.set_image(url=self.config.main.image_url)
        
        return embed
    
    async def handle_command(self, message: discord.Message) -> bool:
        """
        Handle !about command.
        
        Args:
            message: Discord message
            
        Returns:
            True if command was handled, False otherwise
        """
        try:
            if not self.enabled:
                return False
            
            # Check if message starts with !about
            if not message.content.strip().startswith("!about"):
                return False
            
            logger.info(f"!about command triggered | user={message.author.name} | channel={message.channel.id}")
            
            # Check permissions
            if not self.can_use_command(message.author):
                logger.warning(f"!about DENIED - no permission | user={message.author.name}")
                return False
            
            # Check cooldown
            if not self.check_cooldown(message.channel.id):
                logger.debug(
                    "about_command_cooldown_active",
                    channel_id=message.channel.id,
                )
                return False
            
            # Build main embed
            embed = self.build_main_embed()
            
            # Build view with buttons
            view = AboutView(self.config)
            
            # Send message
            await message.channel.send(
                embed=embed,
                view=view,
            )
            
            logger.info(
                "about_command_executed",
                user_id=str(message.author.id),
                user_tag=str(message.author),
                channel_id=message.channel.id,
                guild_id=message.guild.id if message.guild else None,
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "about_command_error",
                error=str(e),
                exc_info=True,
            )
            return False


class PingsCommand:
    """
    Pings command handler.
    
    Sends an embed with notification ping toggle buttons.
    Only accessible by administrators and guild managers.
    """
    
    def __init__(self):
        """Initialize pings command."""
        config = get_config()
        self.config = config.about_command
        self.enabled = self.config.enabled
    
    def can_use_command(self, member: discord.Member) -> bool:
        """Check if member can use the command."""
        return (
            member.guild_permissions.administrator or
            member.guild_permissions.manage_guild
        )
    
    def build_embed(self) -> discord.Embed:
        """Build pings embed."""
        embed = discord.Embed(
            color=0x5865F2,  # Discord blurple
            title="🔔 Notification Settings",
            description=(
                "Toggle your notification preferences below.\n\n"
                "**Available notifications:**\n"
                "• **📰 community news** — community announcements\n"
                "• **🔔 events** — upcoming events and activities\n"
                "• **📡 updates** — product and feature updates"
            ),
        )
        
        # Add footer from config
        if self.config.footer.text:
            footer_args = {"text": self.config.footer.text}
            if self.config.footer.icon_url:
                footer_args["icon_url"] = self.config.footer.icon_url
            embed.set_footer(**footer_args)
        
        return embed
    
    async def handle_command(self, message: discord.Message) -> bool:
        """Handle !pings command."""
        try:
            if not self.enabled:
                return False
            
            if not message.content.strip().startswith("!pings"):
                return False
            
            if not self.can_use_command(message.author):
                logger.debug(
                    "pings_command_no_permission",
                    user_id=str(message.author.id),
                )
                return False
            
            embed = self.build_embed()
            view = NotificationPingsView()
            
            await message.channel.send(
                embed=embed,
                view=view,
            )
            
            logger.info(
                "pings_command_executed",
                user_id=str(message.author.id),
                user_tag=str(message.author),
                channel_id=message.channel.id,
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "pings_command_error",
                error=str(e),
                exc_info=True,
            )
            return False
