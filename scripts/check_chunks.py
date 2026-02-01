"""
Check chunk distribution in Qdrant database.

Shows:
- Messages with multiple chunks
- Chunk distribution
- Why messages != points
"""

from pathlib import Path
import sys
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.qdrant_singleton import get_qdrant_client


def check_chunks():
    """Check chunk distribution."""
    
    print("\n" + "="*80)
    print("🔍 CHUNK DISTRIBUTION ANALYSIS".center(80))
    print("="*80 + "\n")
    
    client = get_qdrant_client()
    collections = client.get_collections().collections
    
    total_messages = 0
    total_points = 0
    multi_chunk_messages = []
    
    for collection in collections:
        collection_name = collection.name
        
        # Skip doc collections
        if not collection_name.split('_')[-1].isdigit():
            continue
        
        print(f"\n📁 {collection_name}")
        
        try:
            # Scroll through all points
            points, _ = client.scroll(
                collection_name=collection_name,
                limit=10000,
                with_payload=True,
            )
            
            # Group by message_id
            messages = defaultdict(list)
            
            for point in points:
                payload = point.payload
                message_id = payload.get('message_id')
                
                if message_id:
                    messages[message_id].append({
                        'point_id': point.id,
                        'content_length': len(payload.get('content', '')),
                        'content_preview': payload.get('content', '')[:100],
                    })
            
            # Analyze
            unique_messages = len(messages)
            total_chunks = len(points)
            
            # Find messages with multiple chunks
            multi_chunks = {
                msg_id: chunks 
                for msg_id, chunks in messages.items()
                if len(chunks) > 1
            }
            
            print(f"   📊 Unique messages: {unique_messages}")
            print(f"   📦 Total chunks: {total_chunks}")
            print(f"   📈 Multi-chunk messages: {len(multi_chunks)}")
            
            if multi_chunks:
                print(f"\n   🔍 Messages with multiple chunks:")
                for msg_id, chunks in list(multi_chunks.items())[:3]:  # Show first 3
                    print(f"      • Message {msg_id}: {len(chunks)} chunks")
                    for i, chunk in enumerate(chunks):
                        print(f"         - Chunk {i}: {chunk['content_length']} chars")
                        print(f"           Preview: {chunk['content_preview']}...")
                
                if len(multi_chunks) > 3:
                    print(f"      ... and {len(multi_chunks) - 3} more")
            
            total_messages += unique_messages
            total_points += total_chunks
            multi_chunk_messages.extend(multi_chunks.keys())
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*80)
    print("📊 SUMMARY".center(80))
    print("="*80)
    print(f"Total unique messages: {total_messages}")
    print(f"Total chunks (points): {total_points}")
    print(f"Messages with multiple chunks: {len(multi_chunk_messages)}")
    print(f"Average chunks per message: {total_points / total_messages:.2f}")
    
    print("\n💡 Explanation:")
    print("   - Short messages (< 500 chars) = 1 chunk")
    print("   - Long messages (> 500 chars) = multiple chunks")
    print("   - This is NORMAL and improves search quality! ✅")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    check_chunks()
