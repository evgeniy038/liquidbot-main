"""
Usage statistics slash command for administrators.

Displays LLM API usage statistics from OpenRouter Analytics API.
"""

import discord
from discord import app_commands
from datetime import datetime, timedelta
import httpx

from src.analytics.usage_tracker import get_usage_tracker
from src.utils import get_logger, get_config

logger = get_logger(__name__)


class UsageCommand:
    """
    /usage slash command for viewing API usage statistics.
    
    Features:
    - Shows real usage from OpenRouter Analytics API
    - Displays costs and token usage
    - Shows per-model breakdown
    - Admin-only access
    """
    
    def __init__(self, bot: discord.Client):
        """
        Initialize usage command.
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.tracker = get_usage_tracker()
        self.config = get_config()
        
        # Silent init
    
    async def _fetch_openrouter_credits(self):
        """
        Fetch remaining credits from OpenRouter API.
        
        Returns:
            Dict with credit info or None if error
        """
        try:
            url = "https://openrouter.ai/api/v1/credits"
            headers = {
                "Authorization": f"Bearer {self.config.llm.api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            return {
                "total_credits": data.get("total_credits", 0),
                "credits_used": data.get("credits_used", 0),
                "credits_remaining": data.get("credits_remaining", 0),
            }
            
        except Exception as e:
            logger.error(
                "openrouter_credits_fetch_failed",
                error=str(e),
                exc_info=True,
            )
            return None
    
    async def _fetch_openrouter_analytics(self, days: int = 30):
        """
        Fetch usage statistics from OpenRouter Analytics API.
        
        NOTE: This requires a provisioning key, not a regular API key.
        
        Args:
            days: Number of days to fetch (max 30)
        
        Returns:
            Dict with aggregated statistics or None if error
        """
        # Check if we have provisioning key
        if not self.config.llm.provisioning_key:
            logger.debug(
                "openrouter_analytics_skipped",
                reason="no_provisioning_key"
            )
            return None
        
        try:
            url = "https://openrouter.ai/api/v1/activity"
            headers = {
                "Authorization": f"Bearer {self.config.llm.provisioning_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            # Aggregate data
            total_requests = 0
            total_prompt_tokens = 0
            total_completion_tokens = 0
            total_reasoning_tokens = 0
            total_cost = 0.0
            by_model = {}
            
            # Filter by date range
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()
            
            for item in data.get("data", []):
                # Parse date (handle both "YYYY-MM-DD" and "YYYY-MM-DD HH:MM:SS" formats)
                date_str = item["date"].split()[0] if " " in item["date"] else item["date"]
                item_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # Skip if outside date range
                if days > 0 and item_date < cutoff_date:
                    continue
                
                # Aggregate totals
                total_requests += int(item.get("requests", 0))
                total_prompt_tokens += int(item.get("prompt_tokens", 0))
                total_completion_tokens += int(item.get("completion_tokens", 0))
                total_reasoning_tokens += int(item.get("reasoning_tokens", 0))
                total_cost += float(item.get("usage", 0))  # usage is already in USD
                
                # Per-model breakdown
                model = item.get("model", "unknown")
                if model not in by_model:
                    by_model[model] = {
                        "requests": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cost_usd": 0.0,
                    }
                
                by_model[model]["requests"] += int(item.get("requests", 0))
                by_model[model]["prompt_tokens"] += int(item.get("prompt_tokens", 0))
                by_model[model]["completion_tokens"] += int(item.get("completion_tokens", 0))
                by_model[model]["cost_usd"] += float(item.get("usage", 0))
            
            # Usage is already in USD, no conversion needed
            total_cost_usd = total_cost
            
            return {
                "total_requests": total_requests,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_reasoning_tokens": total_reasoning_tokens,
                "total_cost_usd": total_cost_usd,
                "by_model": by_model,
            }
            
        except Exception as e:
            logger.error(
                "openrouter_analytics_fetch_failed",
                error=str(e),
                exc_info=True,
            )
            return None
    
    def create_command(self) -> app_commands.Command:
        """
        Create the /usage slash command.
        
        Returns:
            Command definition
        """
        @app_commands.command(
            name="usage",
            description="View LLM API usage statistics (Admin only)"
        )
        @app_commands.describe(
            period="Time period for statistics (default: 30 days)"
        )
        @app_commands.choices(period=[
            app_commands.Choice(name="Last 24 hours", value=1),
            app_commands.Choice(name="Last 7 days", value=7),
            app_commands.Choice(name="Last 30 days", value=30),
        ])
        async def usage_command(
            interaction: discord.Interaction,
            period: app_commands.Choice[int] = None
        ):
            """Display API usage statistics."""
            try:
                # Check if user has access (admin permission OR allowed role)
                allowed_role_ids = {1436799852171235472, 1436767320239243519}  # Staff, Mish
                user_role_ids = {role.id for role in interaction.user.roles}
                
                has_access = (
                    interaction.user.guild_permissions.administrator or
                    bool(user_role_ids & allowed_role_ids)
                )
                
                if not has_access:
                    await interaction.response.send_message(
                        "❌ This command is only available to administrators.",
                        ephemeral=True
                    )
                    return
                
                # Defer response as it might take a moment
                await interaction.response.defer(ephemeral=True)
                
                # Get period (default 30 days)
                days = period.value if period else 30
                period_name = period.name if period else "Last 30 days"
                
                # Try to get analytics from OpenRouter API (if provisioning key available)
                api_stats = await self._fetch_openrouter_analytics(days=days if days > 0 else 30)
                
                if api_stats:
                    # Use API data (most accurate)
                    embed = self._create_api_stats_embed(api_stats, period_name)
                else:
                    # Fallback to local tracker
                    stats = self.tracker.get_stats(days=days)
                    
                    # Try to get credits info from OpenRouter
                    credits_info = await self._fetch_openrouter_credits()
                    
                    # Create embed with local stats + credits info
                    embed = self._create_stats_embed(stats, period_name, credits_info)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                logger.info(
                    "usage_command_executed",
                    user_id=str(interaction.user.id),
                    period=days,
                )
                
            except Exception as e:
                logger.error(
                    "usage_command_error",
                    error=str(e),
                    exc_info=True,
                )
                try:
                    await interaction.followup.send(
                        "❌ Failed to retrieve usage statistics. Check logs for details.",
                        ephemeral=True
                    )
                except:
                    pass
        
        return usage_command
    
    def _create_stats_embed(self, stats, period_name: str, credits_info: dict = None) -> discord.Embed:
        """
        Create embed with usage statistics.
        
        Args:
            stats: UsageStats object from local tracker
            period_name: Human-readable period name
            credits_info: Optional credits info from OpenRouter API
        
        Returns:
            Discord embed with formatted statistics
        """
        # Calculate derived metrics
        total_tokens = stats.total_prompt_tokens + stats.total_completion_tokens
        cache_hit_rate = (
            (stats.total_cached_tokens / stats.total_prompt_tokens * 100)
            if stats.total_prompt_tokens > 0 else 0
        )
        avg_tokens_per_request = (
            total_tokens / stats.total_requests
            if stats.total_requests > 0 else 0
        )
        avg_cost_per_request = (
            stats.total_cost_usd / stats.total_requests
            if stats.total_requests > 0 else 0
        )
        
        # Create embed
        embed = discord.Embed(
            title="📊 llm api usage statistics",
            description=f"**period:** {period_name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Total requests
        embed.add_field(
            name="🔢 total requests",
            value=f"```{stats.total_requests:,}```",
            inline=True
        )
        
        # Total cost with better formatting
        if stats.total_cost_usd < 0.01:
            cost_str = f"${stats.total_cost_usd:.6f}"
        else:
            cost_str = f"${stats.total_cost_usd:.4f}"
        
        embed.add_field(
            name="💰 total cost",
            value=f"```{cost_str}```",
            inline=True
        )
        
        # Average cost per request
        if avg_cost_per_request < 0.001:
            avg_str = f"${avg_cost_per_request:.8f}"
        else:
            avg_str = f"${avg_cost_per_request:.6f}"
        
        embed.add_field(
            name="📉 avg cost/request",
            value=f"```{avg_str}```",
            inline=True
        )
        
        # Token usage
        embed.add_field(
            name="📝 token usage",
            value=(
                f"**input:** {stats.total_prompt_tokens:,}\n"
                f"**output:** {stats.total_completion_tokens:,}\n"
                f"**cached:** {stats.total_cached_tokens:,}\n"
                f"**total:** {total_tokens:,}"
            ),
            inline=False
        )
        
        # Cache efficiency
        embed.add_field(
            name="⚡ cache efficiency",
            value=(
                f"**hit rate:** {cache_hit_rate:.1f}%\n"
                f"**savings:** ${stats.cache_savings_usd:.4f}\n"
                f"**cached reads:** {stats.total_cached_tokens:,} tokens"
            ),
            inline=False
        )
        
        # Credits info (if available)
        if credits_info:
            credits_used_usd = credits_info["credits_used"] / 1_000_000
            credits_remaining_usd = credits_info["credits_remaining"] / 1_000_000
            
            embed.add_field(
                name="💳 openrouter credits",
                value=(
                    f"**used:** ${credits_used_usd:.4f}\n"
                    f"**remaining:** ${credits_remaining_usd:.4f}"
                ),
                inline=False
            )
        
        # Per-model breakdown (if available)
        if stats.by_model:
            model_info = []
            for model, model_stats in list(stats.by_model.items())[:3]:  # Top 3 models
                model_short = model.split("/")[-1] if "/" in model else model
                model_info.append(
                    f"**{model_short}:** {model_stats['requests']:,} reqs, "
                    f"${model_stats['cost_usd']:.6f}"
                )
            
            if model_info:
                embed.add_field(
                    name="🤖 top models",
                    value="\n".join(model_info),
                    inline=False
                )
        
        # Footer with period info
        if stats.period_start and stats.period_end:
            period_duration = stats.period_end - stats.period_start
            days = period_duration.days
            embed.set_footer(
                text=f"Period: {days} day{'s' if days != 1 else ''} • "
                     f"Pricing: Grok-4-Fast ($0.20/$0.50 per 1M tokens)"
            )
        
        return embed
    
    def _create_api_stats_embed(self, stats: dict, period_name: str) -> discord.Embed:
        """
        Create embed with usage statistics from OpenRouter Analytics API.
        
        Args:
            stats: Statistics dict from OpenRouter API
            period_name: Human-readable period name
        
        Returns:
            Discord embed with formatted statistics
        """
        total_tokens = stats["total_prompt_tokens"] + stats["total_completion_tokens"]
        avg_tokens_per_request = (
            total_tokens / stats["total_requests"]
            if stats["total_requests"] > 0 else 0
        )
        avg_cost_per_request = (
            stats["total_cost_usd"] / stats["total_requests"]
            if stats["total_requests"] > 0 else 0
        )
        
        # Create embed
        embed = discord.Embed(
            title="📊 llm api usage statistics",
            description=f"**Period:** {period_name}\n**Source:** OpenRouter Analytics API",
            color=discord.Color.green(),  # Green for API data
            timestamp=datetime.utcnow()
        )
        
        # Total requests
        embed.add_field(
            name="🔢 total requests",
            value=f"```{stats['total_requests']:,}```",
            inline=True
        )
        
        # Total cost with better formatting
        if stats['total_cost_usd'] < 0.01:
            cost_str = f"${stats['total_cost_usd']:.6f}"
        else:
            cost_str = f"${stats['total_cost_usd']:.4f}"
        
        embed.add_field(
            name="💰 total cost",
            value=f"```{cost_str}```",
            inline=True
        )
        
        # Average cost per request
        if avg_cost_per_request < 0.001:
            avg_str = f"${avg_cost_per_request:.8f}"
        else:
            avg_str = f"${avg_cost_per_request:.6f}"
        
        embed.add_field(
            name="📉 avg cost/request",
            value=f"```{avg_str}```",
            inline=True
        )
        
        # Token usage
        token_text = (
            f"**Input:** {stats['total_prompt_tokens']:,}\n"
            f"**Output:** {stats['total_completion_tokens']:,}\n"
        )
        
        if stats.get('total_reasoning_tokens', 0) > 0:
            token_text += f"**Reasoning:** {stats['total_reasoning_tokens']:,}\n"
        
        token_text += f"**Total:** {total_tokens:,}"
        
        embed.add_field(
            name="📝 token usage",
            value=token_text,
            inline=False
        )
        
        # Performance metrics
        embed.add_field(
            name="📊 Performance",
            value=(
                f"**Avg Tokens/Request:** {avg_tokens_per_request:.0f}\n"
                f"**Total Requests:** {stats['total_requests']:,}"
            ),
            inline=False
        )
        
        # Per-model breakdown (if available)
        if stats.get('by_model'):
            model_info = []
            # Sort by cost descending
            sorted_models = sorted(
                stats['by_model'].items(),
                key=lambda x: x[1]['cost_usd'],
                reverse=True
            )
            
            for model, model_stats in sorted_models[:3]:  # Top 3 models
                model_short = model.split("/")[-1] if "/" in model else model
                model_info.append(
                    f"**{model_short}:** {model_stats['requests']:,} reqs, "
                    f"${model_stats['cost_usd']:.6f}"
                )
            
            if model_info:
                embed.add_field(
                    name="🤖 top models",
                    value="\n".join(model_info),
                    inline=False
                )
        
        # Footer
        embed.set_footer(
            text=f"Live data from OpenRouter Analytics API • {period_name}"
        )
        
        return embed


def setup_usage_command(bot: discord.Client) -> app_commands.Command:
    """
    Setup and return the usage command.
    
    Args:
        bot: Discord bot instance
    
    Returns:
        Configured command
    """
    command_handler = UsageCommand(bot)
    return command_handler.create_command()
