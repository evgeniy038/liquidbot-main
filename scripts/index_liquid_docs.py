"""
Script to index Liquid documentation into Qdrant.

Indexes:
- liquid_docs/ (markdown files from scraper)
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
    """Index Liquid documentation."""
    # Setup logging
    setup_logging(log_level="INFO", json_format=False)
    
    logger.info("liquid_docs_indexing_started")
    
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
    
    # Index liquid_docs
    liquid_docs_path = Path("liquid_docs")
    if liquid_docs_path.exists():
        logger.info("indexing_liquid_docs", path=str(liquid_docs_path))
        
        md_files = list(liquid_docs_path.glob("*.md"))
        logger.info(f"found_{len(md_files)}_markdown_files")
        
        total_chunks = 0
        for md_file in md_files:
            try:
                logger.info("indexing_file", file=md_file.name)
                
                result = await indexer.index_document(
                    file_path=md_file,
                    channel_id="liquid_docs",
                    channel_name="Liquid Documentation",
                )
                
                total_chunks += result["chunks"]
                
                logger.info(
                    "file_indexed",
                    file=md_file.name,
                    chunks=result["chunks"],
                )
                
            except Exception as e:
                logger.error(
                    "file_indexing_failed",
                    file=md_file.name,
                    error=str(e),
                    exc_info=True,
                )
        
        logger.info(
            "liquid_docs_indexed",
            total_files=len(md_files),
            total_chunks=total_chunks,
        )
    else:
        logger.warning("liquid_docs_not_found", path=str(liquid_docs_path))
    
    # Close LLM client
    await llm_client.close()
    
    logger.info("liquid_docs_indexing_completed")
    print("\n✅ Liquid documentation indexed successfully!")
    print("   Use scripts/test_retrieval.py to test search")


if __name__ == "__main__":
    asyncio.run(main())
