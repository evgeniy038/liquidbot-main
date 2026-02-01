"""
Script to clear indexed messages from Qdrant vector database.

Usage:
    python clear_index.py               # Interactive mode (local)
    python clear_index.py --all         # Delete everything
    python clear_index.py --channels    # Delete only channel messages
    python clear_index.py --docs        # Delete only documentation
    
    # For remote Qdrant:
    python clear_index.py --url http://localhost:6333 --channels
"""

import argparse
from qdrant_client import QdrantClient


def main():
    parser = argparse.ArgumentParser(description="Clear indexed messages from Qdrant")
    parser.add_argument("--all", action="store_true", help="Delete all collections")
    parser.add_argument("--channels", action="store_true", help="Delete only channel collections")
    parser.add_argument("--docs", action="store_true", help="Delete only documentation collections")
    parser.add_argument("--url", default=None, help="Qdrant URL (for remote)")
    parser.add_argument("--path", default="./qdrant_storage", help="Qdrant local path (default)")
    
    args = parser.parse_args()
    
    # Connect to Qdrant (local or remote)
    if args.url:
        print(f"Connecting to Qdrant at {args.url}...")
        client = QdrantClient(url=args.url)
    else:
        print(f"Connecting to local Qdrant at {args.path}...")
        client = QdrantClient(path=args.path)
    
    # Get all collections
    collections = client.get_collections().collections
    
    if not collections:
        print("No collections found.")
        return
    
    print(f"\nFound {len(collections)} collection(s):")
    for collection in collections:
        # Get collection info for vector count
        info = client.get_collection(collection.name)
        vector_count = info.points_count if hasattr(info, 'points_count') else 0
        print(f"  - {collection.name} ({vector_count} vectors)")
    
    # Determine what to delete
    to_delete = []
    
    if args.all:
        to_delete = [c.name for c in collections]
        print("\n⚠️  Will delete ALL collections!")
    elif args.channels:
        # Channel collections start with "discord_bot_" followed by channel ID
        to_delete = [c.name for c in collections if c.name.startswith("discord_bot_")]
        print(f"\n⚠️  Will delete {len(to_delete)} channel collection(s) (Discord messages only)")
    elif args.docs:
        to_delete = [c.name for c in collections if "docs" in c.name.lower()]
        print(f"\n⚠️  Will delete {len(to_delete)} documentation collection(s)")
    else:
        # Interactive mode
        print("\nWhat would you like to delete?")
        print("1. All collections")
        print("2. Channel messages only")
        print("3. Documentation only")
        print("4. Cancel")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            to_delete = [c.name for c in collections]
        elif choice == "2":
            to_delete = [c.name for c in collections if c.name.startswith("discord_bot_")]
        elif choice == "3":
            to_delete = [c.name for c in collections if "liquid_docs" in c.name or "docs" in c.name]
        elif choice == "4":
            print("Cancelled.")
            return
        else:
            print("Invalid choice.")
            return
    
    if not to_delete:
        print("No collections to delete.")
        return
    
    # Confirm deletion
    print(f"\nCollections to delete:")
    for name in to_delete:
        print(f"  - {name}")
    
    confirm = input("\nAre you sure? Type 'yes' to confirm: ").strip().lower()
    
    if confirm != "yes":
        print("Cancelled.")
        return
    
    # Delete collections
    print("\nDeleting collections...")
    for name in to_delete:
        try:
            client.delete_collection(name)
            print(f"✅ Deleted: {name}")
        except Exception as e:
            print(f"❌ Failed to delete {name}: {e}")
    
    print(f"\n✅ Done! Deleted {len(to_delete)} collection(s).")
    print("\nNote: The bot will re-index messages on next startup if scrape_on_startup is enabled.")


if __name__ == "__main__":
    main()
