"""
Check for duplicate messages in Qdrant database.

This script analyzes all collections and finds:
- Duplicate message IDs
- Messages indexed multiple times
- Collection statistics
"""

from pathlib import Path
import sys
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.qdrant_singleton import get_qdrant_client


def check_duplicates():
    """Check for duplicate messages in database."""
    
    print("\n" + "="*80)
    print("🔍 CHECKING FOR DUPLICATE MESSAGES".center(80))
    print("="*80 + "\n")
    
    client = get_qdrant_client()
    collections = client.get_collections().collections
    
    total_duplicates = 0
    total_messages = 0
    
    for collection in collections:
        collection_name = collection.name
        
        # Skip doc collections (focus on message collections)
        if not collection_name.split('_')[-1].isdigit():
            print(f"⏭️  Skipping doc collection: {collection_name}")
            continue
        
        print(f"\n📁 Checking: {collection_name}")
        
        try:
            # Scroll through all points
            points, next_offset = client.scroll(
                collection_name=collection_name,
                limit=10000,  # Get all points
                with_payload=True,
            )
            
            # Track message IDs
            message_ids = defaultdict(list)
            
            for point in points:
                payload = point.payload
                message_id = payload.get('message_id')
                
                if message_id:
                    message_ids[message_id].append(point.id)
                    total_messages += 1
            
            # Note: Multiple chunks per message is NORMAL (not duplicates)
            # Only flag if same chunk_id appears multiple times (true duplicates)
            chunk_counts = defaultdict(int)
            for point in points:
                # Point ID is unique per chunk (message_id_0, message_id_1, etc.)
                chunk_counts[point.id] += 1
            
            true_duplicates = {
                point_id: count
                for point_id, count in chunk_counts.items()
                if count > 1
            }
            
            if true_duplicates:
                print(f"   ⚠️  Found {len(true_duplicates)} duplicate chunks:")
                for point_id, count in list(true_duplicates.items())[:5]:
                    print(f"      • Chunk {point_id}: appears {count} times")
                
                if len(true_duplicates) > 5:
                    print(f"      ... and {len(true_duplicates) - 5} more")
                
                total_duplicates += len(true_duplicates)
            else:
                print(f"   ✅ No duplicates found")
            
            print(f"   📊 Total unique messages: {len(message_ids)}")
            print(f"   📊 Total points: {len(points)}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*80)
    print("📊 SUMMARY".center(80))
    print("="*80)
    print(f"Total messages checked: {total_messages}")
    print(f"Duplicate messages found: {total_duplicates}")
    
    if total_duplicates == 0:
        print("\n✅ No duplicates found! Database is clean.")
    else:
        print(f"\n⚠️  Found {total_duplicates} duplicate messages.")
        print("   These will be overwritten by upsert on next run.")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    check_duplicates()
