"""Portfolio commands for role promotion system."""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import httpx
import os
import yaml

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# Load config
with open("config/roles.yaml") as f:
    ROLES_CONFIG = yaml.safe_load(f)


class PortfolioModal(discord.ui.Modal, title="Create Your Portfolio"):
    """Modal for creating/editing portfolio."""
    
    bio = discord.ui.TextInput(
        label="Bio",
        style=discord.TextStyle.paragraph,
        placeholder="Tell us about yourself and your contributions to the community...",
        max_length=1000,
        required=True,
    )
    
    twitter_handle = discord.ui.TextInput(
        label="Twitter/X Handle",
        placeholder="@yourhandle",
        max_length=50,
        required=True,
    )
    
    achievements = discord.ui.TextInput(
        label="Key Achievements",
        style=discord.TextStyle.paragraph,
        placeholder="List your key contributions and achievements...",
        max_length=1000,
        required=False,
    )
    
    notion_url = discord.ui.TextInput(
        label="Portfolio URL (Notion/Website)",
        placeholder="https://notion.so/your-portfolio",
        max_length=500,
        required=False,
    )
    
    def __init__(self, discord_id: str, target_role: str = None):
        super().__init__()
        self.discord_id = discord_id
        self.target_role = target_role
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                # Save portfolio data
                response = await client.post(
                    f"{API_BASE_URL}/portfolio/save",
                    params={"discord_id": self.discord_id},
                    json={
                        "bio": self.bio.value,
                        "twitter_handle": self.twitter_handle.value,
                        "achievements": self.achievements.value,
                        "notion_url": self.notion_url.value,
                        "target_role": self.target_role,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    embed = discord.Embed(
                        title="✅ Portfolio Saved",
                        description="Your portfolio has been saved as a draft.\n\nUse `/submit` when you're ready to submit for review.",
                        color=discord.Color.green(),
                    )
                    embed.add_field(name="Bio", value=self.bio.value[:200] + "..." if len(self.bio.value) > 200 else self.bio.value, inline=False)
                    embed.add_field(name="Twitter", value=self.twitter_handle.value, inline=True)
                    if self.target_role:
                        embed.add_field(name="Target Role", value=self.target_role, inline=True)
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed to save portfolio: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class ReviewFeedbackModal(discord.ui.Modal, title="Provide Feedback"):
    """Modal for reviewer feedback."""
    
    feedback = discord.ui.TextInput(
        label="Feedback",
        style=discord.TextStyle.paragraph,
        placeholder="Provide feedback for the user...",
        max_length=1000,
        required=True,
    )
    
    def __init__(self, discord_id: str, action: str, reviewer_id: str):
        super().__init__()
        self.discord_id = discord_id
        self.action = action
        self.reviewer_id = reviewer_id
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/portfolio/review",
                    json={
                        "discord_id": self.discord_id,
                        "reviewer_id": self.reviewer_id,
                        "action": self.action,
                        "feedback": self.feedback.value,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    action_text = {
                        "approve": "✅ Approved",
                        "reject": "❌ Rejected",
                        "request_changes": "⏸️ Changes Requested",
                    }.get(self.action, self.action)
                    
                    await interaction.followup.send(f"{action_text} - Feedback sent to user.", ephemeral=True)
                    
                    # Notify the user
                    try:
                        user = await interaction.client.fetch_user(int(self.discord_id))
                        if user:
                            embed = discord.Embed(
                                title=f"Portfolio Review: {action_text}",
                                description=self.feedback.value,
                                color=discord.Color.green() if self.action == "approve" else discord.Color.red() if self.action == "reject" else discord.Color.yellow(),
                            )
                            await user.send(embed=embed)
                    except:
                        pass
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class PortfolioReviewView(discord.ui.View):
    """Review buttons for portfolio submissions."""
    
    def __init__(self, discord_id: str, config: dict):
        super().__init__(timeout=None)
        self.discord_id = discord_id
        self.config = config
    
    def _has_permission(self, user: discord.Member) -> bool:
        """Check if user can review portfolios."""
        role_ids = [r.id for r in user.roles]
        moderator_id = int(ROLES_CONFIG.get("roles", {}).get("Moderator", "0"))
        staff_id = int(ROLES_CONFIG.get("roles", {}).get("Staff", "0"))
        
        return (
            moderator_id in role_ids or
            staff_id in role_ids or
            user.guild_permissions.administrator
        )
    
    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅", custom_id="portfolio_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._has_permission(interaction.user):
            await interaction.response.send_message("❌ You don't have permission to review portfolios.", ephemeral=True)
            return
        
        modal = ReviewFeedbackModal(self.discord_id, "approve", str(interaction.user.id))
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Request Changes", style=discord.ButtonStyle.secondary, emoji="⏸️", custom_id="portfolio_changes")
    async def request_changes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._has_permission(interaction.user):
            await interaction.response.send_message("❌ You don't have permission to review portfolios.", ephemeral=True)
            return
        
        modal = ReviewFeedbackModal(self.discord_id, "request_changes", str(interaction.user.id))
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="❌", custom_id="portfolio_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._has_permission(interaction.user):
            await interaction.response.send_message("❌ You don't have permission to review portfolios.", ephemeral=True)
            return
        
        modal = ReviewFeedbackModal(self.discord_id, "reject", str(interaction.user.id))
        await interaction.response.send_modal(modal)


def setup_portfolio_commands(bot: commands.Bot, config: dict):
    """Setup portfolio slash commands."""
    
    @app_commands.command(name="portfolio", description="Create or edit your portfolio for role promotion")
    @app_commands.describe(target_role="The role you're applying for")
    @app_commands.choices(target_role=[
        app_commands.Choice(name="Current", value="Current"),
        app_commands.Choice(name="Tide", value="Tide"),
        app_commands.Choice(name="Wave", value="Wave"),
        app_commands.Choice(name="Tsunami", value="Tsunami"),
    ])
    async def portfolio_cmd(interaction: discord.Interaction, target_role: str = None):
        discord_id = str(interaction.user.id)
        
        try:
            async with httpx.AsyncClient() as client:
                # Check for existing portfolio
                response = await client.get(f"{API_BASE_URL}/portfolio/{discord_id}", timeout=30.0)
                
                if response.status_code == 404:
                    # Create new portfolio
                    create_response = await client.post(
                        f"{API_BASE_URL}/portfolio/create",
                        json={
                            "discord_id": discord_id,
                            "username": interaction.user.display_name,
                        },
                        timeout=30.0,
                    )
                    
                    if create_response.status_code != 200:
                        await interaction.response.send_message(f"❌ Failed to create portfolio: {create_response.text}", ephemeral=True)
                        return
                
                elif response.status_code == 200:
                    data = response.json()
                    if data["status"] not in ["draft", "rejected"]:
                        await interaction.response.send_message(
                            f"❌ You already have a portfolio in status: **{data['status']}**\n\nUse `/portfolio_view` to see your current portfolio.",
                            ephemeral=True
                        )
                        return
                
                # Show the modal
                modal = PortfolioModal(discord_id, target_role)
                await interaction.response.send_modal(modal)
        
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="portfolio_view", description="View your portfolio and its status")
    async def portfolio_view_cmd(interaction: discord.Interaction):
        discord_id = str(interaction.user.id)
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/portfolio/{discord_id}", timeout=30.0)
                
                if response.status_code == 404:
                    await interaction.followup.send("❌ You don't have a portfolio yet. Use `/portfolio` to create one.", ephemeral=True)
                    return
                
                data = response.json()
                
                status_colors = {
                    "draft": discord.Color.light_grey(),
                    "submitted": discord.Color.blue(),
                    "pending_vote": discord.Color.yellow(),
                    "approved": discord.Color.green(),
                    "rejected": discord.Color.red(),
                    "promoted": discord.Color.gold(),
                }
                
                embed = discord.Embed(
                    title="📋 Your Portfolio",
                    color=status_colors.get(data["status"], discord.Color.default()),
                )
                embed.add_field(name="Status", value=data["status"].replace("_", " ").title(), inline=True)
                if data.get("target_role"):
                    embed.add_field(name="Target Role", value=data["target_role"], inline=True)
                if data.get("twitter_handle"):
                    embed.add_field(name="Twitter", value=data["twitter_handle"], inline=True)
                if data.get("bio"):
                    bio_preview = data["bio"][:300] + "..." if len(data["bio"]) > 300 else data["bio"]
                    embed.add_field(name="Bio", value=bio_preview, inline=False)
                if data.get("notion_url"):
                    embed.add_field(name="Portfolio URL", value=data["notion_url"], inline=False)
                if data.get("ai_score"):
                    embed.add_field(name="AI Score", value=f"{data['ai_score']}/100", inline=True)
                if data.get("review_feedback"):
                    embed.add_field(name="Reviewer Feedback", value=data["review_feedback"], inline=False)
                if data.get("rejection_reason"):
                    embed.add_field(name="Rejection Reason", value=data["rejection_reason"], inline=False)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="submit", description="Submit your portfolio for review")
    async def submit_cmd(interaction: discord.Interaction):
        discord_id = str(interaction.user.id)
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                # Check resubmit cooldown
                cooldown_response = await client.get(f"{API_BASE_URL}/portfolio/{discord_id}/can-resubmit", timeout=30.0)
                if cooldown_response.status_code == 200:
                    cooldown_data = cooldown_response.json()
                    if not cooldown_data["can_resubmit"]:
                        await interaction.followup.send(
                            f"❌ You cannot resubmit yet. Please wait **{cooldown_data['days_remaining']}** more days.",
                            ephemeral=True
                        )
                        return
                
                # Submit portfolio
                response = await client.post(
                    f"{API_BASE_URL}/portfolio/submit",
                    json={"discord_id": discord_id},
                    timeout=30.0,
                )
                
                if response.status_code != 200:
                    error_detail = response.json().get("detail", response.text)
                    await interaction.followup.send(f"❌ Failed to submit: {error_detail}", ephemeral=True)
                    return
                
                data = response.json()
                
                # Send to review channel
                review_channel_id = config.get("review_channel_id")
                if review_channel_id:
                    channel = interaction.client.get_channel(int(review_channel_id))
                    if channel:
                        embed = discord.Embed(
                            title="📋 New Portfolio Submission",
                            description=f"**User:** <@{discord_id}>\n**Target Role:** {data.get('target_role', 'Not specified')}",
                            color=discord.Color.blue(),
                        )
                        if data.get("bio"):
                            embed.add_field(name="Bio", value=data["bio"][:500], inline=False)
                        if data.get("twitter_handle"):
                            embed.add_field(name="Twitter", value=data["twitter_handle"], inline=True)
                        if data.get("notion_url"):
                            embed.add_field(name="Portfolio URL", value=data["notion_url"], inline=False)
                        
                        embed.set_footer(text=f"Discord ID: {discord_id}")
                        
                        view = PortfolioReviewView(discord_id, config)
                        await channel.send(embed=embed, view=view)
                
                await interaction.followup.send(
                    "✅ Your portfolio has been submitted for review!\n\nYou will be notified when a moderator reviews it.",
                    ephemeral=True
                )
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    # Register commands
    bot.tree.add_command(portfolio_cmd)
    bot.tree.add_command(portfolio_view_cmd)
    bot.tree.add_command(submit_cmd)
    
    # Register persistent view
    bot.add_view(PortfolioReviewView("", config))
