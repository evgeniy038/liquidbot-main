"""
Script to index Liquid platform info and community roles into Qdrant.

Indexes:
- docs/LIQUID_INFO.md (official links, platform overview, community roles)
- docs/LIQUID_LINKS.md (important links)
- docs/DISCORD_MEMBERS_INFO.md (team members info)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llm import OpenRouterClient
from src.rag import MultimodalEmbedder, MultimodalIndexer
from src.utils import get_config, get_logger, setup_logging

logger = get_logger(__name__)


async def main():
    """Index Liquid platform information."""
    # Setup logging
    setup_logging(log_level="INFO", json_format=False)
    
    logger.info("liquid_info_indexing_started")
    
    # Load config
    config = get_config()
    
    # Initialize components
    logger.info("initializing_components")
    
    embedder = MultimodalEmbedder(
        openai_api_key=config.embeddings.api_key,
        text_model=config.embeddings.model,
        clip_model=config.embeddings.clip_model,
        text_dimension=config.embeddings.dimension,
        batch_size=config.embeddings.batch_size,
        base_url=config.embeddings.base_url,  # Important for OpenRouter!
    )
    
    llm_client = OpenRouterClient(
        api_key=config.llm.api_key,
        model=config.llm.model,
    )
    
    indexer = MultimodalIndexer(
        embedder=embedder,
        llm_client=llm_client,
        qdrant_url=config.vector_db.url,
        qdrant_path=config.vector_db.path,
        qdrant_api_key=config.vector_db.api_key,
        collection_prefix=config.vector_db.collection_prefix,
    )
    
    # Index all Liquid info files
    files_to_index = [
        Path("docs/LIQUID_INFO.md"),
        Path("docs/LIQUID_LINKS.md"),
        Path("docs/DISCORD_MEMBERS_INFO.md"),
    ]
    
    total_chunks = 0
    
    for liquid_file in files_to_index:
        if liquid_file.exists():
            logger.info("indexing_liquid_file", file=str(liquid_file))
            
            try:
                result = await indexer.index_document(
                    file_path=liquid_file,
                    channel_id="liquid_docs",
                    channel_name="Liquid Platform Info",
                )
                
                logger.info(
                    "liquid_file_indexed",
                    file=liquid_file.name,
                    chunks=result["chunks"],
                )
                
                print(f"\n✅ {liquid_file.name} indexed successfully!")
                print(f"   Chunks: {result['chunks']}")
                
                total_chunks += result["chunks"]
                
            except Exception as e:
                logger.error(
                    "liquid_file_indexing_failed",
                    file=liquid_file.name,
                    error=str(e),
                    exc_info=True,
                )
                print(f"\n❌ Failed to index {liquid_file.name}")
                print(f"   Error: {str(e)}")
        else:
            logger.error("liquid_file_not_found", path=str(liquid_file))
            print(f"\n❌ File not found: {liquid_file}")
    
    print(f"\n📊 Summary:")
    print(f"   Total files: {len(files_to_index)}")
    print(f"   Total chunks: {total_chunks}")
    print(f"   Collection: liquid_docs")
    
    # Close LLM client
    await llm_client.close()
    
    logger.info("liquid_info_indexing_completed")
    print("\n🔍 Use scripts/test_retrieval.py to test search")


if __name__ == "__main__":
    asyncio.run(main())
