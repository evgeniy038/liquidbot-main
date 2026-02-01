"""
Check Qdrant database statistics.

Shows:
- Total collections
- Messages per collection
- Total messages
- Database size on disk
"""

import os
from pathlib import Path
from qdrant_client import QdrantClient


def get_dir_size(path: Path) -> int:
    """Get total size of directory in bytes."""
    total = 0
    for entry in path.rglob('*'):
        if entry.is_file():
            total += entry.stat().st_size
    return total


def format_size(bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"


def main():
    """Check Qdrant database statistics."""
    
    # Path to Qdrant storage
    db_path = Path("./qdrant_storage")
    
    if not db_path.exists():
        print("❌ Qdrant storage not found!")
        print(f"   Looking for: {db_path.absolute()}")
        return
    
    print("\n" + "="*80)
    print("📊 QDRANT DATABASE STATISTICS".center(80))
    print("="*80 + "\n")
    
    # Initialize client
    try:
        client = QdrantClient(path=str(db_path))
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        return
    
    # Get collections
    try:
        collections = client.get_collections().collections
    except Exception as e:
        print(f"❌ Failed to get collections: {e}")
        return
    
    if not collections:
        print("📭 No collections found (database is empty)\n")
        return
    
    # Stats per collection
    total_messages = 0
    print(f"📚 Collections: {len(collections)}\n")
    
    for collection in collections:
        try:
            count = client.count(collection.name).count
            total_messages += count
            
            # Extract channel ID from collection name
            channel_id = collection.name.replace("discord_bot_", "")
            
            print(f"  📁 {collection.name}")
            print(f"     Channel ID: {channel_id}")
            print(f"     Messages: {count:,}")
            print()
            
        except Exception as e:
            print(f"  ⚠️  Error counting {collection.name}: {e}\n")
    
    # Total messages
    print("-" * 80)
    print(f"📊 Total Messages: {total_messages:,}")
    
    # Database size on disk
    db_size = get_dir_size(db_path)
    print(f"💾 Database Size: {format_size(db_size)}")
    print(f"   Path: {db_path.absolute()}")
    
    # Average size per message
    if total_messages > 0:
        avg_size = db_size / total_messages
        print(f"📈 Average per Message: {format_size(avg_size)}")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
