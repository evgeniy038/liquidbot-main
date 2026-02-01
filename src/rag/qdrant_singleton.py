"""
Singleton Qdrant client to avoid lock conflicts.
"""

from typing import Optional

from qdrant_client import QdrantClient

from src.utils import get_config, get_logger

logger = get_logger(__name__)

_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """
    Get singleton Qdrant client instance.
    
    Returns:
        Qdrant client instance
    """
    global _qdrant_client
    
    if _qdrant_client is None:
        config = get_config()
        
        if config.vector_db.path:
            # Local storage
            _qdrant_client = QdrantClient(path=config.vector_db.path)
            logger.info(
                "qdrant_client_initialized",
                mode="local",
                path=config.vector_db.path,
            )
        else:
            # Remote server
            _qdrant_client = QdrantClient(
                url=config.vector_db.url,
                api_key=config.vector_db.api_key,
            )
            logger.info(
                "qdrant_client_initialized",
                mode="remote",
                url=config.vector_db.url,
            )
    
    return _qdrant_client


def close_qdrant_client():
    """Close Qdrant client if exists."""
    global _qdrant_client
    
    if _qdrant_client is not None:
        _qdrant_client.close()
        _qdrant_client = None
        logger.info("qdrant_client_closed")
