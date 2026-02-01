"""Guild and Quest commands."""

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Optional
import httpx
import os
import yaml

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# Load config
with open("config/roles.yaml") as f:
    ROLES_CONFIG = yaml.safe_load(f)

GUILDS = {
    "traders": {
        "name": "Traders Guild",
        "description": "For trading enthusiasts and market analysts",
        "emoji": "📈",
        "role_types": ["Analyst", "Trader", "Strategist"],
    },
    "content": {
        "name": "Content Guild", 
        "description": "For educators, creators, and shitposters",
        "emoji": "✍️",
        "role_types": ["Educator", "Creator", "Shitposter"],
    },
    "designers": {
        "name": "Designers Guild",
        "description": "For artists and visual creators",
        "emoji": "🎨",
        "role_types": ["Artist", "Designer", "Animator"],
    },
}


class QuestCreateModal(discord.ui.Modal, title="Create New Quest"):
    """Modal for creating a quest."""
    
    quest_title = discord.ui.TextInput(
        label="Quest Title",
        placeholder="Title for the quest",
        max_length=200,
        required=True,
    )
    
    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.paragraph,
        placeholder="Describe what needs to be done...",
        max_length=1000,
        required=True,
    )
    
    points = discord.ui.TextInput(
        label="Points Reward",
        placeholder="10",
        max_length=5,
        required=True,
    )
    
    deadline_days = discord.ui.TextInput(
        label="Deadline (days from now)",
        placeholder="7",
        max_length=3,
        required=False,
    )
    
    def __init__(self, guild_name: str, creator_id: str):
        super().__init__()
        self.guild_name = guild_name
        self.creator_id = creator_id
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            points = int(self.points.value)
            deadline = None
            if self.deadline_days.value:
                days = int(self.deadline_days.value)
                deadline = (datetime.utcnow() + timedelta(days=days)).isoformat()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/guilds/quests/create",
                    json={
                        "title": self.quest_title.value,
                        "description": self.description.value,
                        "guild_name": self.guild_name,
                        "points": points,
                        "deadline": deadline,
                        "creator_discord_id": self.creator_id,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    embed = discord.Embed(
                        title=f"✅ Quest Created: {self.quest_title.value}",
                        description=self.description.value,
                        color=discord.Color.green(),
                    )
                    embed.add_field(name="Points", value=str(points), inline=True)
                    embed.add_field(name="Guild", value=self.guild_name.title(), inline=True)
                    if deadline:
                        embed.add_field(name="Deadline", value=f"{self.deadline_days.value} days", inline=True)
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed to create quest: {response.text}", ephemeral=True)
        
        except ValueError:
            await interaction.followup.send("❌ Invalid points or deadline value", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


class QuestSubmitModal(discord.ui.Modal, title="Submit Quest Completion"):
    """Modal for submitting quest completion."""
    
    work_url = discord.ui.TextInput(
        label="Work URL",
        placeholder="Link to your completed work",
        max_length=500,
        required=True,
    )
    
    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.paragraph,
        placeholder="Describe what you did...",
        max_length=500,
        required=False,
    )
    
    def __init__(self, quest_id: int, discord_id: str):
        super().__init__()
        self.quest_id = quest_id
        self.discord_id = discord_id
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/guilds/quests/{self.quest_id}/submit",
                    json={
                        "discord_id": self.discord_id,
                        "work_url": self.work_url.value,
                        "description": self.description.value,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    await interaction.followup.send("✅ Quest submission received! A Guild Leader will review it.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


def _is_guild_leader(member: discord.Member) -> bool:
    """Check if member is a guild leader."""
    role_ids = [r.id for r in member.roles]
    staff_id = int(ROLES_CONFIG.get("roles", {}).get("Staff", "0"))
    
    # Check for guild leader role or staff
    return staff_id in role_ids or member.guild_permissions.administrator


def setup_guild_commands(bot: commands.Bot, config: dict):
    """Setup guild slash commands."""
    
    guild_group = app_commands.Group(name="guild", description="Guild commands")
    quest_group = app_commands.Group(name="quest", description="Quest commands")
    
    @guild_group.command(name="join", description="Join a guild")
    @app_commands.describe(
        guild="The guild to join",
        role_type="Your role type in the guild"
    )
    @app_commands.choices(guild=[
        app_commands.Choice(name="Traders Guild 📈", value="traders"),
        app_commands.Choice(name="Content Guild ✍️", value="content"),
        app_commands.Choice(name="Designers Guild 🎨", value="designers"),
    ])
    async def guild_join(interaction: discord.Interaction, guild: str, role_type: str):
        await interaction.response.defer(ephemeral=True)
        
        discord_id = str(interaction.user.id)
        guild_info = GUILDS.get(guild)
        
        if not guild_info:
            await interaction.followup.send("❌ Invalid guild", ephemeral=True)
            return
        
        # Validate role type
        valid_types = guild_info["role_types"]
        if role_type not in valid_types:
            await interaction.followup.send(
                f"❌ Invalid role type. Choose from: {', '.join(valid_types)}",
                ephemeral=True
            )
            return
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/guilds/join",
                    json={
                        "discord_id": discord_id,
                        "guild_name": guild,
                        "role_type": role_type,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    embed = discord.Embed(
                        title=f"{guild_info['emoji']} Welcome to {guild_info['name']}!",
                        description=f"You've joined as a **{role_type}**.\n\nCheck `/quest list` to see available quests!",
                        color=discord.Color.green(),
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    
                    # Assign guild role if configured
                    guild_roles = ROLES_CONFIG.get("roles", {}).get("guilds", {}).get(guild, {}).get("roles", {})
                    tier1_role = list(guild_roles.values())[0] if guild_roles else None
                    if tier1_role:
                        role = interaction.guild.get_role(int(tier1_role.get("id", 0)))
                        if role:
                            try:
                                await interaction.user.add_roles(role)
                            except:
                                pass
                else:
                    await interaction.followup.send(f"❌ Failed to join: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @guild_group.command(name="leave", description="Leave your current guild")
    async def guild_leave(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        discord_id = str(interaction.user.id)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/guilds/leave",
                    json={"discord_id": discord_id},
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    await interaction.followup.send("✅ You have left your guild.", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @guild_group.command(name="info", description="View your guild info and stats")
    async def guild_info(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        discord_id = str(interaction.user.id)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/guilds/member/{discord_id}",
                    timeout=30.0,
                )
                
                if response.status_code == 404:
                    await interaction.followup.send("❌ You're not in a guild. Use `/guild join` to join one!", ephemeral=True)
                    return
                
                data = response.json()
                guild_info = GUILDS.get(data["guild_name"], {})
                
                embed = discord.Embed(
                    title=f"{guild_info.get('emoji', '🏰')} Your Guild Info",
                    color=discord.Color.blue(),
                )
                embed.add_field(name="Guild", value=guild_info.get("name", data["guild_name"]), inline=True)
                embed.add_field(name="Role", value=data["role_type"], inline=True)
                embed.add_field(name="Tier", value=f"T{data['tier']}", inline=True)
                embed.add_field(name="Points", value=str(data["points"]), inline=True)
                embed.add_field(name="Quests Completed", value=str(data["quests_completed"]), inline=True)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @guild_group.command(name="leaderboard", description="View guild leaderboard")
    @app_commands.describe(guild="Guild to view leaderboard for")
    @app_commands.choices(guild=[
        app_commands.Choice(name="All Guilds", value="all"),
        app_commands.Choice(name="Traders Guild", value="traders"),
        app_commands.Choice(name="Content Guild", value="content"),
        app_commands.Choice(name="Designers Guild", value="designers"),
    ])
    async def guild_leaderboard(interaction: discord.Interaction, guild: str = "all"):
        await interaction.response.defer()
        
        try:
            async with httpx.AsyncClient() as client:
                params = {} if guild == "all" else {"guild": guild}
                response = await client.get(
                    f"{API_BASE_URL}/guilds/leaderboard",
                    params=params,
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if not data:
                        await interaction.followup.send("No guild members found.")
                        return
                    
                    embed = discord.Embed(
                        title=f"🏆 Guild Leaderboard" + (f" - {GUILDS.get(guild, {}).get('name', guild)}" if guild != "all" else ""),
                        color=discord.Color.gold(),
                    )
                    
                    for i, member in enumerate(data[:10], 1):
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                        embed.add_field(
                            name=f"{medal} {member['username']}",
                            value=f"**{member['points']}** pts | {member['quests_completed']} quests",
                            inline=False,
                        )
                    
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(f"❌ Failed to load leaderboard: {response.text}")
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")
    
    # Quest commands
    @quest_group.command(name="create", description="Create a new quest (Guild Leaders only)")
    @app_commands.describe(guild="Guild for this quest")
    @app_commands.choices(guild=[
        app_commands.Choice(name="Traders Guild", value="traders"),
        app_commands.Choice(name="Content Guild", value="content"),
        app_commands.Choice(name="Designers Guild", value="designers"),
    ])
    async def quest_create(interaction: discord.Interaction, guild: str):
        if not _is_guild_leader(interaction.user):
            await interaction.response.send_message("❌ Only Guild Leaders can create quests.", ephemeral=True)
            return
        
        modal = QuestCreateModal(guild, str(interaction.user.id))
        await interaction.response.send_modal(modal)
    
    @quest_group.command(name="list", description="List active quests")
    @app_commands.describe(guild="Filter by guild")
    @app_commands.choices(guild=[
        app_commands.Choice(name="All Guilds", value="all"),
        app_commands.Choice(name="Traders Guild", value="traders"),
        app_commands.Choice(name="Content Guild", value="content"),
        app_commands.Choice(name="Designers Guild", value="designers"),
    ])
    async def quest_list(interaction: discord.Interaction, guild: str = "all"):
        await interaction.response.defer()
        
        try:
            async with httpx.AsyncClient() as client:
                params = {} if guild == "all" else {"guild": guild}
                response = await client.get(
                    f"{API_BASE_URL}/guilds/quests",
                    params=params,
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    quests = response.json()
                    
                    if not quests:
                        await interaction.followup.send("No active quests found.")
                        return
                    
                    embed = discord.Embed(
                        title="📜 Active Quests",
                        color=discord.Color.blue(),
                    )
                    
                    for quest in quests[:10]:
                        guild_info = GUILDS.get(quest["guild_name"], {})
                        value = f"{quest['description'][:100]}...\n**Points:** {quest['points']}"
                        if quest.get("deadline"):
                            value += f"\n**Deadline:** {quest['deadline'][:10]}"
                        
                        embed.add_field(
                            name=f"{guild_info.get('emoji', '📋')} {quest['title']} (ID: {quest['id']})",
                            value=value,
                            inline=False,
                        )
                    
                    embed.set_footer(text="Use /quest submit <id> to submit your work")
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}")
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")
    
    @quest_group.command(name="submit", description="Submit quest completion")
    @app_commands.describe(quest_id="ID of the quest to submit for")
    async def quest_submit(interaction: discord.Interaction, quest_id: int):
        modal = QuestSubmitModal(quest_id, str(interaction.user.id))
        await interaction.response.send_modal(modal)
    
    @quest_group.command(name="review", description="Review pending quest submissions (Guild Leaders only)")
    async def quest_review(interaction: discord.Interaction):
        if not _is_guild_leader(interaction.user):
            await interaction.response.send_message("❌ Only Guild Leaders can review submissions.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/guilds/quests/submissions/pending",
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    submissions = response.json()
                    
                    if not submissions:
                        await interaction.followup.send("No pending submissions.", ephemeral=True)
                        return
                    
                    embed = discord.Embed(
                        title="📝 Pending Quest Submissions",
                        color=discord.Color.yellow(),
                    )
                    
                    for sub in submissions[:10]:
                        embed.add_field(
                            name=f"Submission #{sub['id']} - Quest: {sub['quest_title']}",
                            value=f"**User:** <@{sub['discord_id']}>\n**URL:** {sub['work_url']}\n**Use:** `/quest approve {sub['id']}` or `/quest reject {sub['id']}`",
                            inline=False,
                        )
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @quest_group.command(name="approve", description="Approve a quest submission (Guild Leaders only)")
    @app_commands.describe(submission_id="ID of the submission to approve")
    async def quest_approve(interaction: discord.Interaction, submission_id: int):
        if not _is_guild_leader(interaction.user):
            await interaction.response.send_message("❌ Only Guild Leaders can approve submissions.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/guilds/quests/submissions/{submission_id}/approve",
                    json={"reviewer_discord_id": str(interaction.user.id)},
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    await interaction.followup.send(f"✅ Submission approved! User awarded **{data['points']}** points.", ephemeral=True)
                    
                    # Notify user
                    try:
                        user = await interaction.client.fetch_user(int(data["discord_id"]))
                        if user:
                            await user.send(f"✅ Your quest submission was approved! You earned **{data['points']}** points.")
                    except:
                        pass
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    @quest_group.command(name="reject", description="Reject a quest submission (Guild Leaders only)")
    @app_commands.describe(
        submission_id="ID of the submission to reject",
        reason="Reason for rejection"
    )
    async def quest_reject(interaction: discord.Interaction, submission_id: int, reason: str = None):
        if not _is_guild_leader(interaction.user):
            await interaction.response.send_message("❌ Only Guild Leaders can reject submissions.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/guilds/quests/submissions/{submission_id}/reject",
                    json={
                        "reviewer_discord_id": str(interaction.user.id),
                        "feedback": reason,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    await interaction.followup.send("✅ Submission rejected.", ephemeral=True)
                    
                    # Notify user
                    try:
                        user = await interaction.client.fetch_user(int(data["discord_id"]))
                        if user:
                            msg = "❌ Your quest submission was rejected."
                            if reason:
                                msg += f"\n**Reason:** {reason}"
                            await user.send(msg)
                    except:
                        pass
                else:
                    await interaction.followup.send(f"❌ Failed: {response.text}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    # Register command groups
    bot.tree.add_command(guild_group)
    bot.tree.add_command(quest_group)
