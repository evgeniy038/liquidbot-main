"""
Script to index Arc documentation into Qdrant.

Indexes:
- arc_docs/ (17 markdown files)
- arc_blogs/ (4 blog posts)
"""

import asyncio
from pathlib import Path

from src.llm import OpenRouterClient
from src.rag import MultimodalEmbedder, MultimodalIndexer
from src.utils import get_config, get_logger, setup_logging

logger = get_logger(__name__)


async def main():
    """Index Arc documentation."""
    # Setup logging
    setup_logging(log_level="INFO", json_format=False)
    
    logger.info("arc_docs_indexing_started")
    
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
    
    # Index arc_docs
    arc_docs_path = Path("arc_docs")
    if arc_docs_path.exists():
        logger.info("indexing_arc_docs", path=str(arc_docs_path))
        
        md_files = list(arc_docs_path.glob("*.md"))
        logger.info(f"found_{len(md_files)}_markdown_files")
        
        total_chunks = 0
        for md_file in md_files:
            try:
                logger.info("indexing_file", file=md_file.name)
                
                result = await indexer.index_document(
                    file_path=md_file,
                    channel_id="arc_docs",
                    channel_name="Arc Documentation",
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
            "arc_docs_indexed",
            total_files=len(md_files),
            total_chunks=total_chunks,
        )
    else:
        logger.warning("arc_docs_not_found", path=str(arc_docs_path))
    
    # Index arc_blogs
    arc_blogs_path = Path("arc_blogs")
    if arc_blogs_path.exists():
        logger.info("indexing_arc_blogs", path=str(arc_blogs_path))
        
        md_files = list(arc_blogs_path.glob("*.md"))
        logger.info(f"found_{len(md_files)}_blog_files")
        
        total_chunks = 0
        for md_file in md_files:
            try:
                logger.info("indexing_blog", file=md_file.name)
                
                result = await indexer.index_document(
                    file_path=md_file,
                    channel_id="arc_blogs",
                    channel_name="Arc Blogs",
                )
                
                total_chunks += result["chunks"]
                
                logger.info(
                    "blog_indexed",
                    file=md_file.name,
                    chunks=result["chunks"],
                )
                
            except Exception as e:
                logger.error(
                    "blog_indexing_failed",
                    file=md_file.name,
                    error=str(e),
                    exc_info=True,
                )
        
        logger.info(
            "arc_blogs_indexed",
            total_files=len(md_files),
            total_chunks=total_chunks,
        )
    else:
        logger.warning("arc_blogs_not_found", path=str(arc_blogs_path))
    
    # Close LLM client
    await llm_client.close()
    
    logger.info("arc_docs_indexing_completed")
    print("\n✅ Arc documentation indexed successfully!")
    print("   Use scripts/test_retrieval.py to test search")


if __name__ == "__main__":
    asyncio.run(main())
