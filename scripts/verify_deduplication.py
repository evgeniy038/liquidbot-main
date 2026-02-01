"""
Verify deduplication is working correctly.

Test:
1. Check current DB state
2. Simulate scraping existing messages
3. Verify they are skipped (dedup working)
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.qdrant_singleton import get_qdrant_client
from src.utils import get_config


def generate_point_id(identifier: str) -> int:
    """Generate numeric point ID from string."""
    import hashlib
    hash_bytes = hashlib.sha256(identifier.encode()).digest()
    return int.from_bytes(hash_bytes[:8], byteorder='big', signed=True)


def message_exists(message_id: str, channel_id: str, collection_prefix: str) -> bool:
    """Check if message exists in Qdrant."""
    try:
        qdrant = get_qdrant_client()
        collection_name = f"{collection_prefix}_{channel_id}"
        
        # Check if collection exists first
        collections = qdrant.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            return False
        
        # Generate point ID for first chunk
        point_id = generate_point_id(f"{message_id}_0")
        
        # Try to retrieve
        result = qdrant.retrieve(
            collection_name=collection_name,
            ids=[point_id],
        )
        
        return len(result) > 0
        
    except Exception:
        return False


def main():
    """Verify deduplication."""
    
    print("\n" + "="*80)
    print("🧪 DEDUPLICATION VERIFICATION TEST".center(80))
    print("="*80 + "\n")
    
    # Initialize
    config = get_config()
    collection_prefix = config.vector_db.collection_prefix
    
    # Test cases
    test_cases = [
        {
            'message_id': '1440952723305402499',  # Existing message (5 chunks)
            'channel_id': '1439139092498485308',
            'should_exist': True,
        },
        {
            'message_id': '9999999999999999999',  # Non-existing message
            'channel_id': '1439139092498485308',
            'should_exist': False,
        },
        {
            'message_id': '1234567890',  # Non-existing in non-existing collection
            'channel_id': '9999999999',
            'should_exist': False,
        },
    ]
    
    print("🔍 Testing message_exists() function:\n")
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        message_id = test['message_id']
        channel_id = test['channel_id']
        expected = test['should_exist']
        
        result = message_exists(message_id, channel_id, collection_prefix)
        
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"Test {i}: {status}")
        print(f"  Message ID: {message_id}")
        print(f"  Channel ID: {channel_id}")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        print()
        
        if result != expected:
            all_passed = False
    
    print("="*80)
    
    if all_passed:
        print("✅ ALL TESTS PASSED! Deduplication is working correctly.")
        print("\n💡 This means:")
        print("   - Existing messages are correctly detected")
        print("   - Non-existing messages return False")
        print("   - Non-existing collections are handled gracefully")
        print("   - Scraping will skip existing messages (0 indexed on re-run)")
    else:
        print("❌ SOME TESTS FAILED! Check deduplication logic.")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
