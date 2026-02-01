"""
Test retrieval from indexed Arc documentation.

Usage:
    python scripts/test_retrieval.py "What is Arc blockchain?"
"""

import asyncio
import sys
from pathlib import Path

from src.rag import HybridRetriever, MultimodalEmbedder
from src.utils import get_config, get_logger, setup_logging

logger = get_logger(__name__)


async def main():
    """Test retrieval."""
    # Setup
    setup_logging(log_level="INFO", json_format=False)
    
    # Get query from command line
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_retrieval.py \"Your search query\"")
        sys.exit(1)
    
    query = sys.argv[1]
    print(f"\n🔍 Searching for: '{query}'")
    print("=" * 60)
    
    # Load config
    config = get_config()
    
    # Initialize components
    embedder = MultimodalEmbedder(
        openai_api_key=config.embeddings.api_key,
        text_model=config.embeddings.model,
        clip_model=config.embeddings.clip_model,
    )
    
    retriever = HybridRetriever(
        embedder=embedder,
        qdrant_url=config.vector_db.url,
        qdrant_path=config.vector_db.path,
        qdrant_api_key=config.vector_db.api_key,
        collection_prefix=config.vector_db.collection_prefix,
        min_score=0.3,
    )
    
    # Test retrieval from arc_docs
    print("\n📚 Searching Arc Documentation...")
    docs_results = await retriever.retrieve(
        query=query,
        channel_id="arc_docs",
        top_k=3,
        include_images=False,
    )
    
    if docs_results:
        print(f"\n✅ Found {len(docs_results)} results:\n")
        for i, doc in enumerate(docs_results, 1):
            print(f"Result {i} (score: {doc.score:.3f}):")
            print(f"Type: {doc.type}")
            print(f"Content: {doc.content[:200]}...")
            if doc.metadata.get("source"):
                print(f"Source: {doc.metadata['source']}")
            print("-" * 60)
    else:
        print("\n❌ No results found in arc_docs")
    
    # Test retrieval from arc_blogs
    print("\n📝 Searching Arc Blogs...")
    blog_results = await retriever.retrieve(
        query=query,
        channel_id="arc_blogs",
        top_k=2,
        include_images=False,
    )
    
    if blog_results:
        print(f"\n✅ Found {len(blog_results)} results:\n")
        for i, doc in enumerate(blog_results, 1):
            print(f"Result {i} (score: {doc.score:.3f}):")
            print(f"Type: {doc.type}")
            print(f"Content: {doc.content[:200]}...")
            if doc.metadata.get("source"):
                print(f"Source: {doc.metadata['source']}")
            print("-" * 60)
    else:
        print("\n❌ No results found in arc_blogs")
    
    print("\n✅ Retrieval test completed!")


if __name__ == "__main__":
    asyncio.run(main())
