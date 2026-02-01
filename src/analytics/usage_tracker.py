"""
Usage statistics tracker for LLM API calls.

Tracks token usage, costs, and provides analytics.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json

from src.utils import get_logger

logger = get_logger(__name__)


class UsageStats:
    """Usage statistics container."""
    
    def __init__(self):
        self.total_requests: int = 0
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_cached_tokens: int = 0
        self.total_cost_usd: float = 0.0
        self.cache_savings_usd: float = 0.0
        self.by_model: Dict[str, Dict] = {}
        self.period_start: datetime = datetime.utcnow()
        self.period_end: datetime = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_cached_tokens": self.total_cached_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "cache_savings_usd": round(self.cache_savings_usd, 4),
            "by_model": self.by_model,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
        }


class UsageTracker:
    """
    Track LLM usage statistics across all requests.
    
    Features:
    - Real-time tracking
    - Per-model statistics
    - Cost calculation with correct Grok-4-Fast pricing
    - Cache savings tracking
    - Persistent storage
    """
    
    # Grok-4-Fast pricing (per 1M tokens)
    PRICING = {
        "x-ai/grok-4-fast": {
            "input_128k": 0.20,      # $0.20 per 1M tokens (≤128K)
            "input_above": 0.40,     # $0.40 per 1M tokens (>128K)
            "output_128k": 0.50,     # $0.50 per 1M tokens (≤128K)
            "output_above": 1.00,    # $1.00 per 1M tokens (>128K)
            "cache_read": 0.05,      # $0.05 per 1M tokens (any size)
        }
    }
    
    def __init__(self, storage_path: str = "data/usage_stats.json"):
        """
        Initialize usage tracker.
        
        Args:
            storage_path: Path to store usage statistics
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing stats or create new
        self.all_time_stats = self._load_stats()
        self.daily_stats: Dict[str, UsageStats] = {}
        
        # Silent init
    
    def _load_stats(self) -> UsageStats:
        """Load statistics from disk."""
        if not self.storage_path.exists():
            return UsageStats()
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            stats = UsageStats()
            stats.total_requests = data.get("total_requests", 0)
            stats.total_prompt_tokens = data.get("total_prompt_tokens", 0)
            stats.total_completion_tokens = data.get("total_completion_tokens", 0)
            stats.total_cached_tokens = data.get("total_cached_tokens", 0)
            stats.total_cost_usd = data.get("total_cost_usd", 0.0)
            stats.cache_savings_usd = data.get("cache_savings_usd", 0.0)
            stats.by_model = data.get("by_model", {})
            
            if "period_start" in data:
                stats.period_start = datetime.fromisoformat(data["period_start"])
            if "period_end" in data:
                stats.period_end = datetime.fromisoformat(data["period_end"])
            
            return stats
        except Exception as e:
            logger.error("failed_to_load_usage_stats", error=str(e))
            return UsageStats()
    
    def _save_stats(self):
        """Save statistics to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.all_time_stats.to_dict(), f, indent=2)
        except Exception as e:
            logger.error("failed_to_save_usage_stats", error=str(e))
    
    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int,
    ) -> tuple[float, float]:
        """
        Calculate cost and cache savings with correct pricing.
        
        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cached_tokens: Number of cached tokens (read from cache)
        
        Returns:
            Tuple of (total_cost, cache_savings)
        """
        if model not in self.PRICING:
            # Fallback to generic pricing if model not in list
            input_price = 0.20
            output_price = 0.50
            cache_price = 0.05
        else:
            pricing = self.PRICING[model]
            # Use 128k pricing (most requests are under 128k)
            input_price = pricing["input_128k"]
            output_price = pricing["output_128k"]
            cache_price = pricing["cache_read"]
        
        # Calculate costs (price per 1M tokens)
        uncached_tokens = prompt_tokens - cached_tokens
        
        # Cost of uncached input tokens
        input_cost = (uncached_tokens / 1_000_000) * input_price
        
        # Cost of cached tokens (cheaper)
        cache_cost = (cached_tokens / 1_000_000) * cache_price
        
        # Cost of output tokens
        output_cost = (completion_tokens / 1_000_000) * output_price
        
        # Total cost
        total_cost = input_cost + cache_cost + output_cost
        
        # Calculate cache savings (what we would have paid without cache)
        cache_savings = (cached_tokens / 1_000_000) * (input_price - cache_price)
        
        return total_cost, cache_savings
    
    def track_request(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
        cost_usd: Optional[float] = None,
    ):
        """
        Track a single LLM request.
        
        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cached_tokens: Number of cached tokens
            cost_usd: Actual cost (if provided by API)
        """
        # Calculate cost
        calculated_cost, cache_savings = self._calculate_cost(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=cached_tokens,
        )
        
        # Use provided cost if available, otherwise use calculated
        final_cost = cost_usd if cost_usd is not None else calculated_cost
        
        # Update all-time stats
        self.all_time_stats.total_requests += 1
        self.all_time_stats.total_prompt_tokens += prompt_tokens
        self.all_time_stats.total_completion_tokens += completion_tokens
        self.all_time_stats.total_cached_tokens += cached_tokens
        self.all_time_stats.total_cost_usd += final_cost
        self.all_time_stats.cache_savings_usd += cache_savings
        self.all_time_stats.period_end = datetime.utcnow()
        
        # Update per-model stats
        if model not in self.all_time_stats.by_model:
            self.all_time_stats.by_model[model] = {
                "requests": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cached_tokens": 0,
                "cost_usd": 0.0,
                "cache_savings_usd": 0.0,
            }
        
        model_stats = self.all_time_stats.by_model[model]
        model_stats["requests"] += 1
        model_stats["prompt_tokens"] += prompt_tokens
        model_stats["completion_tokens"] += completion_tokens
        model_stats["cached_tokens"] += cached_tokens
        model_stats["cost_usd"] += final_cost
        model_stats["cache_savings_usd"] += cache_savings
        
        # Update daily stats
        today = datetime.utcnow().date().isoformat()
        if today not in self.daily_stats:
            self.daily_stats[today] = UsageStats()
        
        daily = self.daily_stats[today]
        daily.total_requests += 1
        daily.total_prompt_tokens += prompt_tokens
        daily.total_completion_tokens += completion_tokens
        daily.total_cached_tokens += cached_tokens
        daily.total_cost_usd += final_cost
        daily.cache_savings_usd += cache_savings
        
        # Save to disk
        self._save_stats()
        
        logger.debug(
            "usage_tracked",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            cost_usd=round(final_cost, 6),
            cache_savings_usd=round(cache_savings, 6),
        )
    
    def get_stats(self, days: int = 30) -> UsageStats:
        """
        Get usage statistics for the last N days.
        
        Args:
            days: Number of days to include (0 = all time)
        
        Returns:
            UsageStats object
        """
        if days == 0:
            return self.all_time_stats
        
        # Aggregate daily stats for the period
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()
        period_stats = UsageStats()
        period_stats.period_start = datetime.combine(cutoff_date, datetime.min.time())
        period_stats.period_end = datetime.utcnow()
        
        for date_str, stats in self.daily_stats.items():
            date = datetime.fromisoformat(date_str).date()
            if date >= cutoff_date:
                period_stats.total_requests += stats.total_requests
                period_stats.total_prompt_tokens += stats.total_prompt_tokens
                period_stats.total_completion_tokens += stats.total_completion_tokens
                period_stats.total_cached_tokens += stats.total_cached_tokens
                period_stats.total_cost_usd += stats.total_cost_usd
                period_stats.cache_savings_usd += stats.cache_savings_usd
        
        return period_stats
    
    def reset_stats(self):
        """Reset all statistics."""
        self.all_time_stats = UsageStats()
        self.daily_stats = {}
        self._save_stats()
        logger.info("usage_stats_reset")


# Global singleton
_usage_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    """Get global usage tracker instance."""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker
