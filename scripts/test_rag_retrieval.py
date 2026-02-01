"""
Test RAG retrieval system.

Shows:
- How messages are indexed
- How vector search works
- How relevance filtering works
- What agent sees when answering
"""

import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.retriever import HybridRetriever
from src.rag.embedder import MultimodalEmbedder
from src.utils import get_config, get_logger

logger = get_logger(__name__)


async def test_retrieval():
    """Test RAG retrieval with real queries."""
    
    print("\n" + "="*80)
    print("🧪 RAG RETRIEVAL TEST".center(80))
    print("="*80 + "\n")
    
    # Load config
    config = get_config()
    
    # Initialize embedder
    print("🔧 Initializing embedder...")
    embedder = MultimodalEmbedder(
        openai_api_key=config.embeddings.api_key,
        text_model=config.embeddings.model,
        clip_model=config.embeddings.clip_model,
        text_dimension=config.embeddings.dimension,
        batch_size=config.embeddings.batch_size,
    )
    print("✅ Embedder ready\n")
    
    # Initialize retriever
    print("🔧 Initializing retriever...")
    retriever = HybridRetriever(
        embedder=embedder,
        qdrant_url=config.vector_db.url,
        qdrant_path=config.vector_db.path,
        qdrant_api_key=config.vector_db.api_key,
        collection_prefix=config.vector_db.collection_prefix,
        min_score=config.vector_db.retrieval.get('min_score', 0.3),
    )
    print("✅ Retriever ready\n")
    
    # Test queries
    test_queries = [
        {
            "query": "how to trade on Liquid?",
            "description": "Trading question (should find Liquid docs)",
        },
        {
            "query": "what is airdrop?",
            "description": "Crypto term (should find relevant messages)",
        },
        {
            "query": "check DM for guide",
            "description": "Scam-like message (should find similar scams)",
        },
        {
            "query": "hello everyone",
            "description": "Generic greeting (low relevance expected)",
        },
    ]
    
    for i, test in enumerate(test_queries, 1):
        print("\n" + "-"*80)
        print(f"TEST {i}: {test['description']}")
        print("-"*80)
        print(f"📝 Query: \"{test['query']}\"\n")
        
        try:
            # Get all available collections (channels)
            from src.rag.qdrant_singleton import get_qdrant_client
            qdrant = get_qdrant_client()
            collections = qdrant.get_collections().collections
            
            # Search across all collections
            all_results = []
            for collection in collections:
                # Extract channel_id from collection name
                channel_id = collection.name.replace(f"{config.vector_db.collection_prefix}_", "")
                
                try:
                    # Retrieve from this channel
                    channel_results = await retriever.retrieve(
                        query=test['query'],
                        channel_id=channel_id,
                        top_k=5,  # Top 5 per channel
                    )
                    all_results.extend(channel_results)
                except Exception as e:
                    # Skip empty or problematic collections
                    continue
            
            # Sort all results by score and take top 5
            all_results.sort(key=lambda x: x.score, reverse=True)
            results = all_results[:5]
            
            if not results:
                print("❌ No relevant messages found\n")
                continue
            
            print(f"✅ Found {len(results)} relevant messages:\n")
            
            for j, result in enumerate(results, 1):
                # Extract metadata
                content = result.content
                channel = result.metadata.get('channel_name', 'N/A')
                author = result.metadata.get('author_id', 'N/A')
                score = result.score
                
                # Truncate content
                content_preview = content[:150] + "..." if len(content) > 150 else content
                
                print(f"  {j}. 🎯 Score: {score:.4f} | Channel: #{channel}")
                print(f"     Content: {content_preview}")
                print(f"     Author ID: {author}\n")
            
            # Show filtering logic
            high_relevance = [r for r in results if r.score > 0.5]
            medium_relevance = [r for r in results if 0.3 < r.score <= 0.5]
            low_relevance = [r for r in results if r.score <= 0.3]
            
            print(f"📊 Relevance Distribution:")
            print(f"   🟢 High (>0.5): {len(high_relevance)} messages")
            print(f"   🟡 Medium (0.3-0.5): {len(medium_relevance)} messages")
            print(f"   🔴 Low (<0.3): {len(low_relevance)} messages")
            
            if config.vector_db.retrieval.get('min_score', 0.3) > 0:
                filtered_count = len([r for r in results if r.score >= config.vector_db.retrieval['min_score']])
                print(f"\n   🔍 After threshold ({config.vector_db.retrieval['min_score']}): {filtered_count} messages passed")
            
            print()
            
        except Exception as e:
            print(f"❌ Error during retrieval: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("🏁 TEST COMPLETED".center(80))
    print("="*80)
    
    # Summary
    print("\n📋 How RAG Works:\n")
    print("1️⃣  User asks question")
    print("2️⃣  Query → Embedding (vector)")
    print("3️⃣  Qdrant finds similar vectors (cosine similarity)")
    print("4️⃣  Re-ranker scores by relevance")
    print("5️⃣  Filter by threshold (min_score)")
    print("6️⃣  Return TOP-K most relevant")
    print("7️⃣  LLM uses context to answer")
    
    print("\n💡 Filtering:\n")
    print("  • Vector similarity: finds semantically similar")
    print("  • Re-ranking: improves precision")
    print("  • Score threshold: removes noise")
    print("  • TOP-K limit: prevents context overload")
    
    print("\n✅ Only high-quality relevant messages go to LLM!\n")


async def show_config():
    """Show retrieval configuration."""
    config = get_config()
    
    print("\n" + "="*80)
    print("⚙️  RETRIEVAL CONFIGURATION".center(80))
    print("="*80 + "\n")
    
    retrieval_config = config.vector_db.retrieval
    
    print(f"📊 Retrieval Settings:")
    print(f"   • top_k: {retrieval_config.get('top_k', 5)}")
    print(f"   • min_score: {retrieval_config.get('min_score', 0.3)}")
    print(f"   • hybrid_search: {retrieval_config.get('hybrid_search', True)}")
    print(f"   • alpha: {retrieval_config.get('alpha', 0.5)} (vector/keyword balance)")
    print(f"   • reranking: {retrieval_config.get('reranking', True)}")
    print(f"   • reranker_model: {retrieval_config.get('reranker_model', 'N/A')}")
    
    print("\n💡 What these mean:\n")
    print("  • top_k: Max number of results to return")
    print("  • min_score: Minimum similarity score (0-1)")
    print("  • hybrid_search: Combine vector + keyword search")
    print("  • alpha: 0=pure vector, 1=pure keyword, 0.5=balanced")
    print("  • reranking: Re-score results for better precision")
    
    print()


async def main():
    """Run all tests."""
    try:
        # Show config first
        await show_config()
        
        # Run retrieval test
        await test_retrieval()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
