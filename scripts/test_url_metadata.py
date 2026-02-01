"""
Test if URLs are properly stored in Qdrant.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import MultimodalEmbedder, HybridRetriever
from src.utils import get_config, setup_logging

setup_logging(log_level="INFO", json_format=False)


async def test_urls():
    """Test URL metadata."""
    print("\n🧪 Testing URL metadata in Qdrant...")
    print("=" * 60)
    
    config = get_config()
    
    # Initialize embedder
    embedder = MultimodalEmbedder(
        openai_api_key=config.embeddings.api_key,
        text_model=config.embeddings.model,
        clip_model=config.embeddings.clip_model,
        text_dimension=config.embeddings.dimension,
    )
    
    # Initialize retriever
    retriever = HybridRetriever(
        embedder=embedder,
        qdrant_url=config.vector_db.url,
        qdrant_path=config.vector_db.path,
        qdrant_api_key=config.vector_db.api_key,
        collection_prefix=config.vector_db.collection_prefix,
    )
    
    # Test query
    query = "Welcome to Arc"
    
    print(f"\n🔍 Query: {query}")
    print("-" * 60)
    
    results = await retriever.retrieve(
        query=query,
        channel_id="arc_docs",
        top_k=5,
    )
    
    if not results:
        print("❌ No results found!")
        return False
    
    print(f"\n✅ Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        title = result.metadata.get('title', 'Unknown')
        url = result.metadata.get('url')
        score = result.score
        
        print(f"{i}. {title}")
        print(f"   Score: {score:.3f}")
        
        if url:
            print(f"   ✅ URL: {url}")
        else:
            print(f"   ❌ URL: Not found")
        
        print()
    
    # Check if all results have URLs
    has_urls = all(r.metadata.get('url') for r in results)
    
    if has_urls:
        print("✅ ALL results have URLs!")
        return True
    else:
        print("⚠️ Some results are missing URLs")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_urls())
    sys.exit(0 if result else 1)
