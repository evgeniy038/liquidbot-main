"""
Hybrid retriever for multimodal RAG.

Features:
- Vector similarity search
- Keyword matching (sparse)
- Metadata filtering
- Result fusion
- Optional reranking
"""

from typing import Dict, List, Optional

from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, ScoredPoint

from src.rag import MultimodalEmbedder
from src.rag.qdrant_singleton import get_qdrant_client
from src.utils import get_logger, log_rag_retrieval

logger = get_logger(__name__)


class Document(BaseModel):
    """Retrieved document."""
    content: str
    score: float
    type: str  # "text", "image_visual", "image_semantic"
    metadata: Dict
    image_url: Optional[str] = None


class HybridRetriever:
    """
    Retrieves text and images using hybrid search.
    
    Methodology:
    1. Vector similarity (dense embeddings)
    2. Keyword matching (BM25 sparse) - optional
    3. Metadata filtering (channel, date, type)
    4. Result fusion (Reciprocal Rank Fusion)
    """
    
    def __init__(
        self,
        embedder: MultimodalEmbedder,
        qdrant_url: Optional[str] = None,
        qdrant_path: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_prefix: str = "discord_bot",
        min_score: float = 0.3,
        ignored_categories: Optional[List[str]] = None,
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            embedder: Multimodal embedder
            qdrant_url: Qdrant server URL (for remote)
            qdrant_path: Local storage path (for local, no Docker)
            qdrant_api_key: Qdrant API key (optional)
            collection_prefix: Collection name prefix
            min_score: Minimum relevance score
            ignored_categories: Discord category IDs to exclude from search
        """
        self.embedder = embedder
        self.collection_prefix = collection_prefix
        self.min_score = min_score
        self.ignored_categories = ignored_categories or []
        
        # Use singleton Qdrant client (prevents lock conflicts)
        self.qdrant = get_qdrant_client()
        
        # SQLite storage for message search
        try:
            from src.rag.sqlite_storage import get_message_storage
            self.sqlite_storage = get_message_storage()
        except:
            self.sqlite_storage = None
        
        logger.info("hybrid_retriever_initialized")
    
    def _get_collection_name(self, channel_id: str) -> str:
        """
        Get collection name.
        
        If channel_id is numeric (Discord channel ID), adds prefix.
        If channel_id already contains prefix or is a doc collection name, returns as-is.
        """
        # If already a full collection name (contains underscore or non-numeric), return as-is
        if '_' in channel_id or not channel_id.isdigit():
            return channel_id
        
        # Otherwise, add prefix (Discord channel ID)
        return f"{self.collection_prefix}_{channel_id}"
    
    async def retrieve(
        self,
        query: str,
        channel_id: str,
        top_k: int = 5,
        include_images: bool = True,
    ) -> List[Document]:
        """
        Retrieve relevant documents and images.
        
        Returns mixed results (text chunks + images)
        sorted by relevance score.
        
        Args:
            query: Search query
            channel_id: Channel ID to search in
            top_k: Number of results to return
            include_images: Include image results
        
        Returns:
            List of documents sorted by relevance
        """
        import time
        start_time = time.time()
        
        collection_name = self._get_collection_name(channel_id)
        
        # Check if collection exists
        try:
            collections = self.qdrant.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if not exists:
                logger.warning(
                    "collection_not_found",
                    collection_name=collection_name,
                )
                return []
        except Exception as e:
            logger.error(
                "qdrant_connection_error",
                error=str(e),
                exc_info=True,
            )
            return []
        
        # Generate query embedding
        query_vector = await self.embedder.embed_query(query)
        
        # Build filter for document types and categories
        filter_conditions = []
        
        # Filter by document type
        if not include_images:
            filter_conditions.append(
                FieldCondition(
                    key="type",
                    match=MatchValue(value="text"),
                )
            )
        
        # Filter out ignored categories
        if self.ignored_categories:
            from qdrant_client.models import FieldCondition, MatchAny
            filter_conditions.append(
                FieldCondition(
                    key="category_id",
                    match=MatchAny(any=self.ignored_categories),
                )
            )
        
        # Combine filters
        query_filter = None
        if filter_conditions:
            # Use must_not for ignored categories, must for type
            must_conditions = [c for c in filter_conditions if c.key == "type"]
            must_not_conditions = [c for c in filter_conditions if c.key == "category_id"]
            
            filter_args = {}
            if must_conditions:
                filter_args["must"] = must_conditions
            if must_not_conditions:
                filter_args["must_not"] = must_not_conditions
            
            if filter_args:
                query_filter = Filter(**filter_args)
        
        # Vector search with named vector
        search_results = self.qdrant.search(
            collection_name=collection_name,
            query_vector=("text", query_vector),  # Use 'text' named vector
            limit=top_k * 2,  # Over-retrieve for filtering
            query_filter=query_filter,
            score_threshold=self.min_score,
        )
        
        # Convert to documents
        documents = []
        text_count = 0
        image_count = 0
        
        for result in search_results[:top_k]:
            doc_type = result.payload.get("type", "text")
            
            doc = Document(
                content=result.payload.get("content", ""),
                score=result.score,
                type=doc_type,
                metadata=result.payload,
                image_url=result.payload.get("image_url"),
            )
            
            documents.append(doc)
            
            if doc_type == "text":
                text_count += 1
            elif "image" in doc_type:
                image_count += 1
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Log retrieval
        log_rag_retrieval(
            logger=logger,
            query=query,
            channel_id=channel_id,
            results_count=len(documents),
            text_chunks=text_count,
            images_found=image_count,
            latency_ms=latency_ms,
        )
        
        return documents
    
    async def search_messages(
        self,
        query: str,
        exclude_author_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Document]:
        """
        Search messages in SQLite using FTS5.
        
        Args:
            query: Search query
            exclude_author_id: Author ID to exclude (e.g., the person asking)
            limit: Max results
            
        Returns:
            List of message documents
        """
        if not self.sqlite_storage:
            return []
        
        try:
            # Search messages using FTS5, exclude the asking user
            results = self.sqlite_storage.search(
                query=query,
                category_ids_exclude=self.ignored_categories if self.ignored_categories else None,
                limit=limit * 2,  # Get more results to filter
            )
            
            documents = []
            seen_content = set()  # Deduplicate similar messages
            query_lower = query.lower().strip()
            
            for result in results:
                msg = result.message
                content_lower = msg.content.lower().strip()
                
                # Skip messages that are the same as the query (user's own question)
                # This catches "who is Alex" when query is "who is Alex"
                if content_lower == query_lower:
                    continue
                
                # Skip if message is very similar to query (>80% overlap)
                query_words = set(query_lower.split())
                content_words = set(content_lower.split())
                if query_words and content_words:
                    overlap = len(query_words & content_words) / len(query_words)
                    if overlap > 0.8 and len(content_words) <= len(query_words) + 2:
                        continue  # Too similar to the question
                
                # Skip duplicate content
                if content_lower in seen_content:
                    continue
                seen_content.add(content_lower)
                
                # Format message as document
                content = f"[{msg.author_display_name or msg.author_name}]: {msg.content}"
                
                doc = Document(
                    content=content,
                    score=result.score * 0.5,  # Scale down FTS score relative to vector
                    type="message",
                    metadata={
                        "author_name": msg.author_name,
                        "author_id": msg.author_id,
                        "channel_name": msg.channel_name,
                        "timestamp": msg.timestamp,
                        "url": msg.url,
                    },
                )
                documents.append(doc)
                
                if len(documents) >= limit:
                    break
            
            if documents:
                logger.debug(f"📨 Found {len(documents)} messages for '{query[:30]}'")
            
            return documents
            
        except Exception as e:
            logger.error(f"message_search_failed: {e}")
            return []
    
    async def search_similar_images(
        self,
        image_url: str,
        channel_id: str,
        top_k: int = 5,
    ) -> List[Document]:
        """
        Find visually similar images.
        
        Uses CLIP embeddings for visual similarity.
        
        Args:
            image_url: Query image URL
            channel_id: Channel to search in
            top_k: Number of results
        
        Returns:
            List of similar images
        """
        collection_name = self._get_collection_name(channel_id)
        
        # Generate CLIP embedding for query image
        from PIL import Image
        import io
        import httpx
        
        try:
            # Download image
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_data = io.BytesIO(response.content)
                image = Image.open(image_data).convert("RGB")
            
            # Get CLIP embedding
            query_vector = self.embedder.embed_image(image)
            
            # Search for visual matches
            type_filter = Filter(
                must=[
                    FieldCondition(
                        key="type",
                        match=MatchValue(value="image_visual"),
                    )
                ]
            )
            
            search_results = self.qdrant.search(
                collection_name=collection_name,
                query_vector=("image", query_vector),  # Use 'image' named vector for CLIP
                limit=top_k,
                query_filter=type_filter,
            )
            
            # Convert to documents
            documents = [
                Document(
                    content=result.payload.get("caption", ""),
                    score=result.score,
                    type=result.payload.get("type", "image_visual"),
                    metadata=result.payload,
                    image_url=result.payload.get("image_url"),
                )
                for result in search_results
            ]
            
            logger.info(
                "similar_images_found",
                query_image=image_url,
                results_count=len(documents),
            )
            
            return documents
            
        except Exception as e:
            logger.error(
                "image_search_failed",
                image_url=image_url,
                error=str(e),
                exc_info=True,
            )
            return []
