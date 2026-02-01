"""
Script to delete old collections and recreate with named vectors support.

This fixes the "could not broadcast" error by creating collections
with separate vector spaces for text (3072d) and images (768d).
"""

from qdrant_client import QdrantClient
from pathlib import Path

def main():
    print("="*80)
    print("Recreating Qdrant Collections with Named Vectors")
    print("="*80)
    
    # Connect to local Qdrant
    qdrant_path = Path("./qdrant_storage")
    
    if not qdrant_path.exists():
        print(f"\n✅ No existing storage found at {qdrant_path}")
        print("   Collections will be created fresh on first use")
        return
    
    print(f"\n📂 Connecting to Qdrant at: {qdrant_path}")
    client = QdrantClient(path=str(qdrant_path))
    
    # Get all collections
    try:
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if not collection_names:
            print("\n✅ No collections found - nothing to delete")
            return
        
        print(f"\n📋 Found {len(collection_names)} collections:")
        for name in collection_names:
            print(f"   - {name}")
        
        # Delete each collection
        print("\n🗑️  Deleting old collections...")
        for name in collection_names:
            try:
                client.delete_collection(name)
                print(f"   ✅ Deleted: {name}")
            except Exception as e:
                print(f"   ❌ Failed to delete {name}: {e}")
        
        print("\n" + "="*80)
        print("✅ Collections Deleted Successfully!")
        print("="*80)
        print("\nNext steps:")
        print("1. Restart the bot: python src/main.py")
        print("2. Bot will auto-create new collections with named vectors")
        print("3. Old messages will be re-indexed automatically")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nIf Qdrant is locked by another process:")
        print("1. Stop the bot (Ctrl+C)")
        print("2. Run this script again")
        print("3. Or manually delete: qdrant_storage/collection/*")

if __name__ == "__main__":
    main()
