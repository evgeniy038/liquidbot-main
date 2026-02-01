"""
Start Qdrant in local mode (no Docker needed).

Uses Qdrant's local storage option.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient

def main():
    """Initialize local Qdrant storage."""
    
    # Create local storage directory
    storage_path = project_root / "qdrant_storage"
    storage_path.mkdir(exist_ok=True)
    
    print(f"🚀 Initializing Qdrant local storage at: {storage_path}")
    
    # Create client with local storage
    client = QdrantClient(path=str(storage_path))
    
    # List collections
    collections = client.get_collections().collections
    
    print(f"\n✅ Qdrant initialized successfully!")
    print(f"📊 Collections: {len(collections)}")
    
    if collections:
        for collection in collections:
            print(f"   - {collection.name}")
    else:
        print("   (No collections yet)")
    
    print(f"\n💡 Storage location: {storage_path}")
    print(f"💡 Use this in your code:")
    print(f"   client = QdrantClient(path='{storage_path}')")
    
    return str(storage_path)

if __name__ == "__main__":
    main()
