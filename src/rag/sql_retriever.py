"""
SQL-based RAG retriever using SQLite FTS5.

No AI costs - uses full-text search instead of embeddings.
"""

from typing import List, Optional
from dataclasses import dataclass

from src.utils import get_logger
from src.rag.sqlite_storage import get_message_storage, SearchResult

logger = get_logger(__name__)


@dataclass
class Document:
    """Document for RAG context."""
    content: str
    score: float
    type: str = "text"
    metadata: dict = None
    image_url: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SQLRetriever:
    """
    SQL-based retriever using FTS5 full-text search.
    
    Benefits:
    - Zero AI costs (no embedding API calls)
    - Fast keyword matching
    - Works offline
    - SQL flexibility
    """
    
    def __init__(
        self,
        ignored_categories: Optional[List[str]] = None,
        min_score: float = 0.1,
    ):
        """
        Initialize SQL retriever.
        
        Args:
            ignored_categories: Discord category IDs to exclude
            min_score: Minimum BM25 score threshold
        """
        self.storage = get_message_storage()
        self.ignored_categories = ignored_categories or []
        self.min_score = min_score
        
        logger.info(
            "sql_retriever_initialized",
            ignored_categories_count=len(self.ignored_categories),
        )
    
    async def retrieve(
        self,
        query: str,
        channel_id: Optional[str] = None,
        top_k: int = 5,
        include_images: bool = False,  # Kept for API compatibility
    ) -> List[Document]:
        """
        Retrieve relevant documents using FTS.
        
        Args:
            query: Search query
            channel_id: Channel ID to search in (None = all channels)
            top_k: Number of results
            include_images: Ignored (no image search in SQL mode)
            
        Returns:
            List of documents sorted by relevance
        """
        import time
        start_time = time.time()
        
        # Perform FTS search
        results = self.storage.search(
            query=query,
            channel_id=channel_id,
            category_ids_exclude=self.ignored_categories if self.ignored_categories else None,
            limit=top_k,
        )
        
        # Convert to Document objects
        documents = []
        for result in results:
            if result.score < self.min_score:
                continue
            
            msg = result.message
            
            # Build enriched content (same format as before)
            content = (
                f"Author: {msg.author_name} ({msg.author_display_name})\n"
                f"Channel: #{msg.channel_name}\n"
                f"Timestamp: {msg.timestamp}\n"
                f"---\n{msg.content}"
            )
            
            doc = Document(
                content=content,
                score=result.score,
                type="text",
                metadata={
                    "message_id": msg.message_id,
                    "channel_id": msg.channel_id,
                    "channel_name": msg.channel_name,
                    "author_id": msg.author_id,
                    "author_name": msg.author_name,
                    "timestamp": msg.timestamp,
                    "url": msg.url,
                    "snippet": result.snippet,
                },
            )
            documents.append(doc)
        
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "sql_retrieval_completed",
            query=query[:50],
            channel_id=channel_id,
            results=len(documents),
            latency_ms=round(latency_ms, 2),
        )
        
        return documents
    
    async def retrieve_all_channels(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Document]:
        """
        Retrieve from all channels.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            Documents from all channels
        """
        return await self.retrieve(
            query=query,
            channel_id=None,
            top_k=top_k,
        )
    
    def get_stats(self) -> dict:
        """Get storage statistics."""
        return self.storage.get_stats()
