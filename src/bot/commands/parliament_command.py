"""Parliament voting system with API polling."""

import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from typing import Optional
import httpx
import os
import yaml

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
PARLIAMENT_CHANNEL_ID = os.getenv("PARLIAMENT_CHANNEL_ID", "")

# Load config
with open("config/roles.yaml") as f:
    ROLES_CONFIG = yaml.safe_load(f)

# Vote thresholds
MIN_VOTES_REQUIRED = 5
APPROVAL_RATE_THRESHOLD = 0.6

# Role IDs for promotions (legacy community roles)
ROLE_IDS = {
    "Droplet": os.getenv("Droplet", "1445308513663324243"),
    "Current": os.getenv("Current", "1444006094283477085"),
    "Founding_Droplet": os.getenv("Founding_Droplet", "1069142027784171623"),
    "Tide": os.getenv("Tide", "1069140617239744572"),
    "Wave": os.getenv("Wave", "1068785740068159590"),
    "Tsunami": os.getenv("Tsunami", "957362763267702815"),
    "Allinliquid": os.getenv("Allinliquid", "1377229341418852402"),
}

def get_next_tier_role(guild_name: str, current_tier: int) -> tuple[str, str] | None:
    """Get the next tier role ID and name for a guild member.
    
    Returns (role_id, role_name) or None if no next tier exists.
    """
    guilds = ROLES_CONFIG.get("roles", {}).get("guilds", {})
    guild = guilds.get(guild_name.lower())
    
    if not guild:
        return None
    
    next_tier = current_tier + 1
    
    # Find the role with the next tier
    for role_name, role_data in guild.get("roles", {}).items():
        if role_data.get("tier") == next_tier:
            return (role_data.get("id"), role_name)
    
    return None


def get_guild_role_by_name(guild_name: str, role_name: str) -> str | None:
    """Get a role ID by guild and role name."""
    guilds = ROLES_CONFIG.get("roles", {}).get("guilds", {})
    guild = guilds.get(guild_name.lower())
    
    if not guild:
        return None
    
    role_data = guild.get("roles", {}).get(role_name.lower())
    return role_data.get("id") if role_data else None


class PortfolioVoteView(discord.ui.View):
    """Voting buttons for Portfolio submissions."""
    
    def __init__(self, discord_id: str, bot: commands.Bot):
        super().__init__(timeout=None)
        self.discord_id = discord_id
        self.bot = bot
    
    def _is_parliament_member(self, user: discord.Member) -> bool:
        """Check if user is a Parliament member."""
        parliament_roles = ROLES_CONFIG.get("roles", {}).get("whitelists", {}).get("nominators", [])
        user_role_ids = [str(r.id) for r in user.roles]
        return any(role_id in user_role_ids for role_id in parliament_roles) or user.guild_permissions.administrator
    
    async def _update_embed(self, interaction: discord.Interaction, approve_count: int, reject_count: int):
        """Update the embed with current vote counts."""
        message = interaction.message
        if not message or not message.embeds:
            return
        
        embed = message.embeds[0]
        total = approve_count + reject_count
        
        for i, field in enumerate(embed.fields):
            if "Votes" in field.name or "📊" in field.name:
                embed.set_field_at(
                    i,
                    name="📊 Votes",
                    value=f"✅ {approve_count} | ❌ {reject_count} | Total: {total}/5",
                    inline=True,
                )
                break
        
        await message.edit(embed=embed)
    
    async def _check_and_finalize(self, interaction: discord.Interaction):
        """Check if voting should be finalized."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/portfolio/vote-check/{self.discord_id}",
                    timeout=30.0,
                )
                
                if response.status_code != 200:
                    return
                
                data = response.json()
                
                if data.get("ready"):
                    approved = data["approved"]
                    
                    finalize_response = await client.post(
                        f"{API_BASE_URL}/portfolio/finalize",
                        params={"discord_id": self.discord_id, "approved": approved},
                        timeout=30.0,
                    )
                    
                    if finalize_response.status_code == 200:
                        result = finalize_response.json()
                        
                        message = interaction.message
                        if message:
                            embed = message.embeds[0] if message.embeds else discord.Embed()
                            
                            if approved:
                                embed.color = discord.Color.green()
                                embed.title = "✅ " + (embed.title or "Portfolio Approved")
                                
                                if result.get("to_role") and result["to_role"] in ROLE_IDS:
                                    role_id = ROLE_IDS.get(result["to_role"])
                                    if role_id:
                                        guild = interaction.guild
                                        member = guild.get_member(int(self.discord_id))
                                        role = guild.get_role(int(role_id))
                                        if member and role:
                                            try:
                                                await member.add_roles(role)
                                                embed.add_field(
                                                    name="🎖️ Promotion",
                                                    value=f"<@{self.discord_id}> promoted to **{result['to_role']}**!",
                                                    inline=False,
                                                )
                                                
                                                # Send DM to user
                                                try:
                                                    user = await self.bot.fetch_user(int(self.discord_id))
                                                    await user.send(
                                                        f"🎉 **Congratulations!** Your portfolio has been approved!\n\n"
                                                        f"Final Vote: ✅ {result['approve_count']} / ❌ {result['reject_count']}\n\n"
                                                        f"🎖️ **You have been promoted to {result['to_role']}!**"
                                                    )
                                                except:
                                                    pass
                                            except Exception as e:
                                                embed.add_field(name="⚠️ Error", value=f"Failed to assign role: {e}", inline=False)
                            else:
                                embed.color = discord.Color.red()
                                embed.title = "❌ " + (embed.title or "Portfolio Rejected")
                                embed.add_field(
                                    name="⏰ Cooldown",
                                    value="User can resubmit in 7 days",
                                    inline=True,
                                )
                                
                                # Send DM to user
                                try:
                                    user = await self.bot.fetch_user(int(self.discord_id))
                                    await user.send(
                                        f"❌ Your portfolio was not approved.\n\n"
                                        f"Final Vote: ✅ {result['approve_count']} / ❌ {result['reject_count']}\n\n"
                                        f"⏰ You may resubmit after **7 days**."
                                    )
                                except:
                                    pass
                            
                            for item in self.children:
                                item.disabled = True
                            
                            await message.edit(embed=embed, view=self)
        
        except Exception as e:
            print(f"Error finalizing portfolio vote: {e}")
    
    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅", custom_id="portfolio_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_parliament_member(interaction.user):
            await interaction.response.send_message("❌ Only Parliament members can vote.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/portfolio/vote",
                    params={
                        "discord_id": self.discord_id,
                        "voter_discord_id": str(interaction.user.id),
                        "vote_type": "approve",
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    await interaction.followup.send("✅ Vote recorded: Approve", ephemeral=True)
                    await self._update_embed(interaction, data["approve_count"], data["reject_count"])
                    await self._check_and_finalize(interaction)
                elif response.status_code == 400:
                    await interaction.followup.send("❌ You already voted on this portfolio.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="❌", custom_id="portfolio_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_parliament_member(interaction.user):
            await interaction.response.send_message("❌ Only Parliament members can vote.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/portfolio/vote",
                    params={
                        "discord_id": self.discord_id,
                        "voter_discord_id": str(interaction.user.id),
                        "vote_type": "reject",
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    await interaction.followup.send("✅ Vote recorded: Reject", ephemeral=True)
                    await self._update_embed(interaction, data["approve_count"], data["reject_count"])
                    await self._check_and_finalize(interaction)
                elif response.status_code == 400:
                    await interaction.followup.send("❌ You already voted on this portfolio.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class ParliamentVoteView(discord.ui.View):
    """Voting buttons for Parliament nominations."""
    
    def __init__(self, nomination_id: int, bot: commands.Bot):
        super().__init__(timeout=None)
        self.nomination_id = nomination_id
        self.bot = bot
    
    def _is_parliament_member(self, user: discord.Member) -> bool:
        """Check if user is a Parliament member."""
        parliament_roles = ROLES_CONFIG.get("roles", {}).get("whitelists", {}).get("nominators", [])
        user_role_ids = [str(r.id) for r in user.roles]
        return any(role_id in user_role_ids for role_id in parliament_roles) or user.guild_permissions.administrator
    
    async def _update_embed(self, interaction: discord.Interaction, approve_count: int, reject_count: int):
        """Update the embed with current vote counts."""
        message = interaction.message
        if not message or not message.embeds:
            return
        
        embed = message.embeds[0]
        total = approve_count + reject_count
        
        # Update fields
        for i, field in enumerate(embed.fields):
            if field.name == "Votes":
                embed.set_field_at(
                    i,
                    name="Votes",
                    value=f"✅ {approve_count} | ❌ {reject_count} | Total: {total}/{MIN_VOTES_REQUIRED}",
                    inline=False,
                )
                break
        else:
            embed.add_field(
                name="Votes",
                value=f"✅ {approve_count} | ❌ {reject_count} | Total: {total}/{MIN_VOTES_REQUIRED}",
                inline=False,
            )
        
        await message.edit(embed=embed)
    
    async def _check_and_finalize(self, interaction: discord.Interaction):
        """Check if voting should be finalized."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/parliament/check/{self.nomination_id}",
                    timeout=30.0,
                )
                
                if response.status_code != 200:
                    return
                
                data = response.json()
                
                if data["ready"]:
                    approved = data["approved"]
                    
                    # Finalize
                    finalize_response = await client.post(
                        f"{API_BASE_URL}/parliament/finalize/{self.nomination_id}",
                        params={"approved": approved},
                        timeout=30.0,
                    )
                    
                    if finalize_response.status_code == 200:
                        result = finalize_response.json()
                        
                        # Update message
                        message = interaction.message
                        if message:
                            embed = message.embeds[0] if message.embeds else discord.Embed()
                            
                            if approved:
                                embed.color = discord.Color.green()
                                embed.title = "✅ " + (embed.title or "Nomination Approved")
                                
                                # Assign role
                                if result.get("to_role"):
                                    role_id = ROLE_IDS.get(result["to_role"])
                                    if role_id:
                                        guild = interaction.guild
                                        member = guild.get_member(int(result["discord_id"]))
                                        role = guild.get_role(int(role_id))
                                        if member and role:
                                            try:
                                                await member.add_roles(role)
                                                embed.add_field(
                                                    name="Result",
                                                    value=f"<@{result['discord_id']}> has been promoted to **{result['to_role']}**!",
                                                    inline=False,
                                                )
                                            except Exception as e:
                                                embed.add_field(name="Error", value=f"Failed to assign role: {e}", inline=False)
                            else:
                                embed.color = discord.Color.red()
                                embed.title = "❌ " + (embed.title or "Nomination Rejected")
                                embed.add_field(
                                    name="Result",
                                    value=f"The nomination was rejected ({data['approval_rate']:.0%} approval rate, needed {APPROVAL_RATE_THRESHOLD:.0%})",
                                    inline=False,
                                )
                            
                            # Disable buttons
                            for item in self.children:
                                item.disabled = True
                            
                            await message.edit(embed=embed, view=self)
        
        except Exception as e:
            print(f"Error finalizing vote: {e}")
    
    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅", custom_id="parliament_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_parliament_member(interaction.user):
            await interaction.response.send_message("❌ Only Parliament members can vote.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/parliament/vote",
                    json={
                        "nomination_id": self.nomination_id,
                        "voter_discord_id": str(interaction.user.id),
                        "vote_type": "approve",
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    await interaction.followup.send("✅ Vote recorded: Approve", ephemeral=True)
                    await self._update_embed(interaction, data["approve_count"], data["reject_count"])
                    await self._check_and_finalize(interaction)
                elif response.status_code == 400:
                    await interaction.followup.send("❌ You already voted on this nomination.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="❌", custom_id="parliament_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._is_parliament_member(interaction.user):
            await interaction.response.send_message("❌ Only Parliament members can vote.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/parliament/vote",
                    json={
                        "nomination_id": self.nomination_id,
                        "voter_discord_id": str(interaction.user.id),
                        "vote_type": "reject",
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    await interaction.followup.send("✅ Vote recorded: Reject", ephemeral=True)
                    await self._update_embed(interaction, data["approve_count"], data["reject_count"])
                    await self._check_and_finalize(interaction)
                elif response.status_code == 400:
                    await interaction.followup.send("❌ You already voted on this nomination.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class ParliamentPoller:
    """Polls the API for pending nominations and creates voting messages."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.running = False
    
    async def start(self):
        """Start the polling loop."""
        self.running = True
        while self.running:
            await self.poll_pending()
            await asyncio.sleep(30)  # Poll every 30 seconds
    
    def stop(self):
        """Stop the polling loop."""
        self.running = False
    
    async def poll_pending(self):
        """Poll for pending nominations."""
        if not PARLIAMENT_CHANNEL_ID:
            return
        
        try:
            channel = self.bot.get_channel(int(PARLIAMENT_CHANNEL_ID))
            if not channel:
                return
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/parliament/pending",
                    timeout=30.0,
                )
                
                if response.status_code != 200:
                    return
                
                nominations = response.json()
                
                for nom in nominations:
                    # Create voting embed
                    embed = discord.Embed(
                        title=f"🏛️ Nomination: {nom['username']}",
                        description=f"**Promotion:** {nom['from_role']} → {nom['to_role']}",
                        color=discord.Color.blue(),
                    )
                    embed.add_field(name="User", value=f"<@{nom['discord_id']}>", inline=True)
                    if nom.get("reason"):
                        embed.add_field(name="Reason", value=nom["reason"], inline=False)
                    if nom.get("portfolio_url"):
                        embed.add_field(name="Portfolio", value=nom["portfolio_url"], inline=False)
                    embed.add_field(
                        name="Votes",
                        value=f"✅ 0 | ❌ 0 | Total: 0/{MIN_VOTES_REQUIRED}",
                        inline=False,
                    )
                    embed.add_field(
                        name="Requirements",
                        value=f"• Minimum {MIN_VOTES_REQUIRED} votes\n• {APPROVAL_RATE_THRESHOLD:.0%} approval rate needed",
                        inline=False,
                    )
                    
                    if nom.get("avatar_url"):
                        embed.set_thumbnail(url=nom["avatar_url"])
                    
                    embed.set_footer(text=f"Nomination ID: {nom['id']}")
                    
                    # Send message with voting buttons
                    view = ParliamentVoteView(nom["id"], self.bot)
                    message = await channel.send(embed=embed, view=view)
                    
                    # Mark as processed
                    await client.post(
                        f"{API_BASE_URL}/parliament/processed/{nom['id']}",
                        params={
                            "message_id": str(message.id),
                            "channel_id": str(channel.id),
                        },
                        timeout=30.0,
                    )
        
        except Exception as e:
            print(f"Error polling Parliament: {e}")


def setup_parliament_commands(bot: commands.Bot, config: dict):
    """Setup Parliament commands and polling."""
    
    poller = ParliamentPoller(bot)
    
    async def handle_portfolio_withdraw(interaction: discord.Interaction, discord_id: str):
        """Handle portfolio withdrawal by owner."""
        # Only the portfolio owner can withdraw
        if str(interaction.user.id) != discord_id:
            await interaction.response.send_message("❌ Only the portfolio owner can withdraw.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                # Delete the portfolio via API
                response = await client.delete(
                    f"{API_BASE_URL}/portfolio/{discord_id}",
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    await interaction.followup.send("✅ Portfolio withdrawn. You can create a new one.", ephemeral=True)
                    
                    # Update the Discord message
                    message = interaction.message
                    if message and message.embeds:
                        embed = message.embeds[0]
                        embed.color = discord.Color.dark_grey()
                        embed.title = "🗑️ " + (embed.title or "Portfolio Withdrawn")
                        embed.add_field(
                            name="Status",
                            value="This portfolio was withdrawn by the owner.",
                            inline=False,
                        )
                        
                        # Disable all buttons
                        view = discord.ui.View()
                        for comp in interaction.message.components:
                            for item in comp.children:
                                button = discord.ui.Button(
                                    label=item.label,
                                    style=item.style,
                                    disabled=True,
                                    emoji=item.emoji,
                                )
                                view.add_item(button)
                        await message.edit(embed=embed, view=view)
                else:
                    await interaction.followup.send(f"❌ Failed to withdraw: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    async def handle_portfolio_vote(interaction: discord.Interaction, discord_id: str, vote_type: str):
        """Handle portfolio vote from dynamic buttons."""
        # Check if user is Parliament member (role ID: 1447972806339067925)
        PARLIAMENT_ROLE_ID = ROLES_CONFIG.get("roles", {}).get("parliament", "1447972806339067925")
        user_role_ids = [str(r.id) for r in interaction.user.roles]
        is_parliament = PARLIAMENT_ROLE_ID in user_role_ids or interaction.user.guild_permissions.administrator
        
        if not is_parliament:
            await interaction.response.send_message("❌ Only <@&1447972806339067925> members can vote.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/portfolio/vote",
                    params={
                        "discord_id": discord_id,
                        "voter_discord_id": str(interaction.user.id),
                        "vote_type": vote_type,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    await interaction.followup.send(f"✅ Vote recorded: {vote_type.title()}", ephemeral=True)
                    
                    # Update button labels with vote counts
                    message = interaction.message
                    if message:
                        view = discord.ui.View(timeout=None)
                        for component in message.components:
                            for button in component.children:
                                custom_id = button.custom_id or ""
                                new_button = discord.ui.Button(
                                    style=button.style,
                                    custom_id=custom_id,
                                    disabled=False,
                                )
                                # Update labels with vote counts
                                if "approve" in custom_id:
                                    new_button.emoji = "✅"
                                    new_button.label = str(data['approve_count'])
                                elif "reject" in custom_id:
                                    new_button.emoji = "❌"
                                    new_button.label = str(data['reject_count'])
                                elif "withdraw" in custom_id:
                                    new_button.emoji = "🗑️"
                                    new_button.label = None
                                view.add_item(new_button)
                        await message.edit(view=view)
                    
                    # Check if voting should be finalized
                    check_response = await client.get(
                        f"{API_BASE_URL}/portfolio/vote-check/{discord_id}",
                        timeout=30.0,
                    )
                    if check_response.status_code == 200:
                        check_data = check_response.json()
                        if check_data.get("ready"):
                            approved = check_data["approved"]
                            finalize_response = await client.post(
                                f"{API_BASE_URL}/portfolio/finalize",
                                params={"discord_id": discord_id, "approved": approved},
                                timeout=30.0,
                            )
                            if finalize_response.status_code == 200:
                                result = finalize_response.json()
                                if message and message.embeds:
                                    embed = message.embeds[0]
                                    promoted_role_name = None
                                    if approved:
                                        embed.color = discord.Color.green()
                                        embed.title = "✅ " + (embed.title or "Portfolio Approved")
                                        
                                        # Get guild member info and assign next tier role
                                        if interaction.guild:
                                            member = interaction.guild.get_member(int(discord_id))
                                            if member:
                                                # Get guild member info from API
                                                guild_response = await client.get(
                                                    f"{API_BASE_URL}/guilds/member/{discord_id}",
                                                    timeout=30.0,
                                                )
                                                if guild_response.status_code == 200:
                                                    guild_data = guild_response.json()
                                                    guild_name = guild_data.get("guild_name")
                                                    current_tier = guild_data.get("tier", 0)
                                                    
                                                    # Get next tier role from roles.yaml
                                                    next_role = get_next_tier_role(guild_name, current_tier)
                                                    if next_role:
                                                        role_id, role_name = next_role
                                                        role = interaction.guild.get_role(int(role_id))
                                                        if role:
                                                            try:
                                                                await member.add_roles(role)
                                                                promoted_role_name = role_name.title()
                                                                embed.add_field(
                                                                    name="🎖️ Promotion",
                                                                    value=f"<@{discord_id}> promoted to **{promoted_role_name}** (Tier {current_tier + 1})!",
                                                                    inline=False,
                                                                )
                                                            except Exception as e:
                                                                embed.add_field(name="⚠️ Error", value=f"Failed to assign role: {e}", inline=False)
                                                elif result.get("to_role") and result["to_role"] in ROLE_IDS:
                                                    # Fallback to legacy role assignment
                                                    role_id = ROLE_IDS.get(result["to_role"])
                                                    if role_id:
                                                        role = interaction.guild.get_role(int(role_id))
                                                        if role:
                                                            try:
                                                                await member.add_roles(role)
                                                                promoted_role_name = result["to_role"]
                                                            except:
                                                                pass
                                    else:
                                        embed.color = discord.Color.red()
                                        embed.title = "❌ " + (embed.title or "Portfolio Rejected")
                                    
                                    # Disable buttons
                                    view = discord.ui.View()
                                    for comp in interaction.message.components:
                                        for item in comp.children:
                                            button = discord.ui.Button(
                                                label=item.label,
                                                style=item.style,
                                                disabled=True,
                                                emoji=item.emoji,
                                            )
                                            view.add_item(button)
                                    await message.edit(embed=embed, view=view)
                                    
                                    # Notify user
                                    try:
                                        user = await bot.fetch_user(int(discord_id))
                                        if approved:
                                            role_msg = f" You've been promoted to **{promoted_role_name}**!" if promoted_role_name else ""
                                            await user.send(f"🎉 Your portfolio was approved!{role_msg}")
                                        else:
                                            await user.send("❌ Your portfolio was not approved. You can resubmit in 7 days.")
                                    except:
                                        pass
                
                elif response.status_code == 400:
                    await interaction.followup.send("❌ You already voted on this portfolio.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="parliament_status", description="View Parliament voting status")
    async def parliament_status(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/parliament/pending",
                    timeout=30.0,
                )
                
                if response.status_code != 200:
                    await interaction.followup.send("❌ Failed to fetch status", ephemeral=True)
                    return
                
                pending = response.json()
                
                embed = discord.Embed(
                    title="🏛️ Parliament Status",
                    color=discord.Color.blue(),
                )
                embed.add_field(name="Pending Nominations", value=str(len(pending)), inline=True)
                embed.add_field(name="Min Votes Required", value=str(MIN_VOTES_REQUIRED), inline=True)
                embed.add_field(name="Approval Threshold", value=f"{APPROVAL_RATE_THRESHOLD:.0%}", inline=True)
                
                if pending:
                    names = [f"• {n['username']} ({n['from_role']} → {n['to_role']})" for n in pending[:5]]
                    embed.add_field(
                        name="Pending Votes",
                        value="\n".join(names),
                        inline=False,
                    )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    bot.tree.add_command(parliament_status)
    
    # Register persistent view
    bot.add_view(ParliamentVoteView(0, bot))
    
    # Add interaction listener for dynamic portfolio vote buttons
    async def portfolio_vote_listener(interaction: discord.Interaction):
        """Handle dynamic button interactions for portfolio voting."""
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = interaction.data.get("custom_id", "")
        
        # Handle portfolio vote buttons (sent by backend API)
        if custom_id.startswith("portfolio_vote_approve_"):
            discord_id = custom_id.replace("portfolio_vote_approve_", "")
            await handle_portfolio_vote(interaction, discord_id, "approve")
        elif custom_id.startswith("portfolio_vote_reject_"):
            discord_id = custom_id.replace("portfolio_vote_reject_", "")
            await handle_portfolio_vote(interaction, discord_id, "reject")
        elif custom_id.startswith("portfolio_withdraw_"):
            discord_id = custom_id.replace("portfolio_withdraw_", "")
            await handle_portfolio_withdraw(interaction, discord_id)
    
    bot.add_listener(portfolio_vote_listener, "on_interaction")
    
    # Start poller when bot is ready
    async def start_poller():
        await bot.wait_until_ready()
        asyncio.create_task(poller.start())
    
    asyncio.create_task(start_poller())
    
    return poller
