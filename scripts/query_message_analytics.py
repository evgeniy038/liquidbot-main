"""
CLI tool to query Discord message analytics.

Features:
- Top users by activity
- Top channels by activity
- Time-based analytics
- Message search
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics import MessageAnalytics
from src.utils import get_config, get_logger

logger = get_logger(__name__)


class AnalyticsCLI:
    """CLI for message analytics."""
    
    def __init__(self):
        """Initialize CLI."""
        config = get_config()
        self.analytics = MessageAnalytics(
            collection_prefix=config.vector_db.collection_prefix
        )
    
    def print_header(self, title: str):
        """Print formatted header."""
        print(f"\n{'='*80}")
        print(f"{title:^80}")
        print(f"{'='*80}\n")
    
    def top_users(self, limit: int = 10, channel_id: str = None):
        """Show top users by message count."""
        self.print_header("📊 TOP USERS BY ACTIVITY")
        
        users = self.analytics.get_top_users(limit=limit, channel_id=channel_id)
        
        if not users:
            print("No data found.")
            return
        
        print(f"{'Rank':<6} {'User ID':<20} {'Messages':<10}")
        print(f"{'-'*80}")
        
        for i, (user_id, count) in enumerate(users, 1):
            print(f"{i:<6} {user_id:<20} {count:<10}")
        
        print(f"\nTotal users: {len(users)}")
    
    def top_channels(self, limit: int = 10):
        """Show top channels by message count."""
        self.print_header("📊 TOP CHANNELS BY ACTIVITY")
        
        channels = self.analytics.get_top_channels(limit=limit)
        
        if not channels:
            print("No data found.")
            return
        
        print(f"{'Rank':<6} {'Channel Name':<30} {'Messages':<10}")
        print(f"{'-'*80}")
        
        for i, (channel_id, channel_name, count) in enumerate(channels, 1):
            print(f"{i:<6} #{channel_name:<29} {count:<10}")
        
        print(f"\nTotal channels: {len(channels)}")
    
    def user_details(self, user_id: str):
        """Show detailed user activity."""
        self.print_header(f"👤 USER ACTIVITY: {user_id}")
        
        activities = self.analytics.get_user_activity(user_id=user_id, limit=1)
        
        if not activities:
            print("No data found for this user.")
            return
        
        activity = activities[0]
        
        print(f"User ID: {activity.user_id}")
        print(f"Total Messages: {activity.message_count}")
        print(f"Active Channels: {len(activity.channels)}")
        print(f"Average Message Length: {activity.average_message_length:.1f} chars")
        print(f"First Message: {activity.first_message.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Last Message: {activity.last_message.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"\nChannels:")
        for channel in activity.channels:
            print(f"  - {channel}")
    
    def channel_details(self, channel_id: str):
        """Show detailed channel activity."""
        self.print_header(f"📺 CHANNEL ACTIVITY: {channel_id}")
        
        activities = self.analytics.get_channel_activity(channel_id=channel_id, limit=1)
        
        if not activities:
            print("No data found for this channel.")
            return
        
        activity = activities[0]
        
        print(f"Channel ID: {activity.channel_id}")
        print(f"Channel Name: #{activity.channel_name}")
        print(f"Total Messages: {activity.message_count}")
        print(f"Unique Users: {activity.unique_users}")
        print(f"Average Message Length: {activity.average_message_length:.1f} chars")
        print(f"First Message: {activity.first_message.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Last Message: {activity.last_message.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    def time_range_activity(self, days: int = 7, channel_id: str = None):
        """Show activity for time range."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        self.print_header(f"📅 ACTIVITY FOR LAST {days} DAYS")
        
        activity = self.analytics.get_activity_by_time_range(
            start_date=start_date,
            end_date=end_date,
            channel_id=channel_id,
        )
        
        if not activity:
            print("No data found for this time range.")
            return
        
        print(f"{'Date':<12} {'Messages':<10}")
        print(f"{'-'*80}")
        
        total_messages = 0
        for date, count in activity.items():
            print(f"{date:<12} {count:<10}")
            total_messages += count
        
        print(f"\nTotal messages: {total_messages}")
        print(f"Average per day: {total_messages / days:.1f}")
    
    def search_messages(self, query: str, limit: int = 10):
        """Search messages by content."""
        self.print_header(f"🔍 SEARCH RESULTS: '{query}'")
        
        results = self.analytics.search_messages(query=query, limit=limit)
        
        if not results:
            print("No messages found.")
            return
        
        print(f"Found {len(results)} message(s):\n")
        
        for i, msg in enumerate(results, 1):
            print(f"--- Message {i} ---")
            print(f"Author ID: {msg.get('author_id')}")
            print(f"Channel: #{msg.get('channel_name')}")
            print(f"Timestamp: {msg.get('timestamp')}")
            print(f"Content: {msg.get('content', '')[:200]}...")
            print(f"URL: {msg.get('url')}")
            print()
    
    def show_summary(self):
        """Show overall summary."""
        self.print_header("📊 MESSAGE ANALYTICS SUMMARY")
        
        # Get collections
        collections = self.analytics.get_all_collections()
        print(f"Total Collections: {len(collections)}")
        
        # Get top users
        print("\n🏆 Top 5 Users:")
        users = self.analytics.get_top_users(limit=5)
        for i, (user_id, count) in enumerate(users, 1):
            print(f"  {i}. User {user_id}: {count} messages")
        
        # Get top channels
        print("\n📺 Top 5 Channels:")
        channels = self.analytics.get_top_channels(limit=5)
        for i, (channel_id, channel_name, count) in enumerate(channels, 1):
            print(f"  {i}. #{channel_name}: {count} messages")
        
        # Get recent activity
        print("\n📅 Last 7 Days Activity:")
        activity = self.analytics.get_activity_by_time_range(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
        )
        total_week = sum(activity.values())
        print(f"  Total messages: {total_week}")
        print(f"  Average per day: {total_week / 7:.1f}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Query Discord message analytics"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Top users command
    top_users_parser = subparsers.add_parser("top-users", help="Show top users")
    top_users_parser.add_argument("--limit", type=int, default=10, help="Number of users")
    top_users_parser.add_argument("--channel", type=str, help="Filter by channel ID")
    
    # Top channels command
    top_channels_parser = subparsers.add_parser("top-channels", help="Show top channels")
    top_channels_parser.add_argument("--limit", type=int, default=10, help="Number of channels")
    
    # User details command
    user_parser = subparsers.add_parser("user", help="Show user details")
    user_parser.add_argument("user_id", type=str, help="User ID")
    
    # Channel details command
    channel_parser = subparsers.add_parser("channel", help="Show channel details")
    channel_parser.add_argument("channel_id", type=str, help="Channel ID")
    
    # Time range command
    time_parser = subparsers.add_parser("time-range", help="Show activity by time range")
    time_parser.add_argument("--days", type=int, default=7, help="Number of days")
    time_parser.add_argument("--channel", type=str, help="Filter by channel ID")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search messages")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument("--limit", type=int, default=10, help="Max results")
    
    # Summary command
    subparsers.add_parser("summary", help="Show overall summary")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = AnalyticsCLI()
    
    # Execute command
    try:
        if args.command == "top-users":
            cli.top_users(limit=args.limit, channel_id=args.channel)
        elif args.command == "top-channels":
            cli.top_channels(limit=args.limit)
        elif args.command == "user":
            cli.user_details(user_id=args.user_id)
        elif args.command == "channel":
            cli.channel_details(channel_id=args.channel_id)
        elif args.command == "time-range":
            cli.time_range_activity(days=args.days, channel_id=args.channel)
        elif args.command == "search":
            cli.search_messages(query=args.query, limit=args.limit)
        elif args.command == "summary":
            cli.show_summary()
        
    except Exception as e:
        logger.error("cli_error", error=str(e), exc_info=True)
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
