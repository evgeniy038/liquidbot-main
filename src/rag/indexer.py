"""
Multimodal indexer for text and images.

Features:
- Text indexing with semantic chunking
- Image indexing with CLIP + vision-generated captions
- Dual representation for images (visual + semantic)
- Qdrant integration
"""

import asyncio
import hashlib
import io
from pathlib import Path
from typing import Dict, List, Optional, Union

import httpx
from PIL import Image
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams, NamedVector

from src.llm import OpenRouterClient
from src.rag import MultimodalEmbedder, add_context_header, semantic_chunk
from src.rag.qdrant_singleton import get_qdrant_client
from src.utils import get_logger, log_document_indexed

logger = get_logger(__name__)


class DocumentMetadata(BaseModel):
    """Metadata for indexed document."""
    message_id: Optional[str] = None
    channel_id: str
    channel_name: str
    category_id: Optional[str] = None  # Discord category ID (for filtering)
    guild_id: Optional[str] = None  # Discord server/guild ID
    author_id: Optional[str] = None
    author_roles: Optional[List[str]] = None  # List of role IDs
    timestamp: str
    title: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None  # URL from documentation or Discord message link


class MultimodalIndexer:
    """
    Indexes text and images into unified vector space.
    
    Strategy:
    - Text: Semantic chunking + OpenAI embeddings
    - Images: CLIP embeddings + vision-generated captions
    - Storage: Dual representation (visual + semantic)
    """
    
    def __init__(
        self,
        embedder: MultimodalEmbedder,
        llm_client: OpenRouterClient,
        qdrant_url: Optional[str] = None,
        qdrant_path: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_prefix: str = "discord_bot",
    ):
        """
        Initialize multimodal indexer.
        
        Args:
            embedder: Multimodal embedder instance
            llm_client: LLM client for caption generation
            qdrant_url: Qdrant server URL (for remote)
            qdrant_path: Local storage path (for local, no Docker)
            qdrant_api_key: Qdrant API key (optional)
            collection_prefix: Prefix for collection names
        """
        self.embedder = embedder
        self.llm_client = llm_client
        self.collection_prefix = collection_prefix
        
        # Use singleton Qdrant client (prevents lock conflicts)
        self.qdrant = get_qdrant_client()
        
        logger.info(
            "multimodal_indexer_initialized",
            collection_prefix=collection_prefix,
        )
    
    def _get_collection_name(self, channel_id: str) -> str:
        """Get collection name for channel."""
        return f"{self.collection_prefix}_{channel_id}"
    
    async def ensure_collection(
        self,
        channel_id: str,
        vector_size: int = 3072,
    ) -> None:
        """
        Ensure collection exists for channel.
        
        Args:
            channel_id: Channel ID
            vector_size: Vector dimension (default: 3072 for text-embedding-3-large)
        """
        collection_name = self._get_collection_name(channel_id)
        
        # Check if collection exists
        collections = self.qdrant.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        
        if not exists:
            # Create collection with named vectors for multimodal support
            # text: 3072 (text-embedding-3-large)
            # image: 768 (CLIP)
            try:
                # Try modern API (qdrant-client >= 1.8)
                self.qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config={
                        "text": VectorParams(
                            size=3072,
                            distance=Distance.COSINE,
                        ),
                        "image": VectorParams(
                            size=768,
                            distance=Distance.COSINE,
                        ),
                    },
                )
            except Exception as e:
                # Fallback: single vector config (text only)
                logger.warning(
                    "named_vectors_not_supported",
                    error=str(e),
                    fallback="single_vector",
                )
                self.qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=3072,
                        distance=Distance.COSINE,
                    ),
                )
            
            logger.info(
                "collection_created",
                collection_name=collection_name,
                text_dim=3072,
                image_dim=768,
            )
    
    def message_exists(
        self,
        message_id: str,
        channel_id: str,
    ) -> bool:
        """
        Check if message already exists in Qdrant.
        
        Args:
            message_id: Discord message ID
            channel_id: Channel ID
        
        Returns:
            True if message exists, False otherwise
        """
        try:
            collection_name = self._get_collection_name(channel_id)
            
            # Check if collection exists first
            collections = self.qdrant.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                # Collection doesn't exist = message doesn't exist
                return False
            
            # Generate point ID for first chunk (all chunks will share same base message_id)
            point_id = self._generate_point_id(f"{message_id}_0")
            
            # Try to retrieve the point
            result = self.qdrant.retrieve(
                collection_name=collection_name,
                ids=[point_id],
            )
            
            return len(result) > 0
            
        except Exception as e:
            # Any error = message doesn't exist
            logger.debug(
                "message_exists_check_failed",
                message_id=message_id,
                error=str(e),
            )
            return False
    
    async def index_text(
        self,
        text: str,
        metadata: DocumentMetadata,
        max_chunk_size: int = 500,
        overlap: int = 100,
    ) -> int:
        """
        Index text with semantic chunking.
        
        Process:
        1. Semantic chunking (context-aware)
        2. Add contextual headers
        3. Generate embeddings
        4. Upsert to vector DB with rich metadata
        
        Args:
            text: Text content to index
            metadata: Document metadata
            max_chunk_size: Maximum chunk size
            overlap: Overlap between chunks
        
        Returns:
            Number of chunks indexed
        """
        # Ensure collection exists
        await self.ensure_collection(metadata.channel_id)
        
        # Chunk text
        chunks = semantic_chunk(
            text=text,
            max_size=max_chunk_size,
            overlap=overlap,
        )
        
        if not chunks:
            logger.warning("no_chunks_created", text_length=len(text))
            return 0
        
        # Add context headers
        enriched_chunks = [
            add_context_header(chunk, metadata.model_dump())
            for chunk in chunks
        ]
        
        # Generate embeddings
        embeddings = await self.embedder.embed_texts(enriched_chunks)
        
        # Create points
        collection_name = self._get_collection_name(metadata.channel_id)
        points = []
        
        for i, (chunk, embedding) in enumerate(zip(enriched_chunks, embeddings)):
            point_id = self._generate_point_id(
                f"{metadata.message_id or 'doc'}_{i}"
            )
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector={"text": embedding},  # Named vector for text
                    payload={
                        "content": chunk,
                        "type": "text",
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        **metadata.model_dump(),
                    }
                )
            )
        
        # Upsert to Qdrant
        self.qdrant.upsert(
            collection_name=collection_name,
            points=points,
        )
        
        logger.info(
            "text_indexed",
            channel_id=metadata.channel_id,
            chunks_created=len(chunks),
            text_length=len(text),
        )
        
        return len(chunks)
    
    async def index_image(
        self,
        image_url: str,
        metadata: DocumentMetadata,
    ) -> bool:
        """
        Index image with dual representation.
        
        Creates two vectors:
        1. Visual: CLIP image embedding (exact visual match)
        2. Semantic: Caption embedding (text-based search)
        
        This allows both "find similar images" and 
        "find images about X" queries.
        
        Args:
            image_url: URL or path to image
            metadata: Document metadata
        
        Returns:
            True if successful
        """
        try:
            # Ensure collection exists
            await self.ensure_collection(metadata.channel_id)
            
            # Download image
            image = await self._download_image(image_url)
            
            # Generate CLIP visual embedding
            visual_embedding = self.embedder.embed_image(image)
            
            # Generate caption with vision LLM
            caption = await self.generate_caption(image_url)
            
            # Generate text embedding of caption
            semantic_embedding = await self.embedder.embed_text(caption)
            
            # Create points
            collection_name = self._get_collection_name(metadata.channel_id)
            message_id = metadata.message_id or "img"
            
            points = [
                # Visual representation (CLIP embedding 768d)
                PointStruct(
                    id=self._generate_point_id(f"{message_id}_img_visual"),
                    vector={"image": visual_embedding},  # Named vector for image
                    payload={
                        "type": "image_visual",
                        "image_url": image_url,
                        "caption": caption,
                        **metadata.model_dump(),
                    }
                ),
                # Semantic representation (text embedding 3072d)
                PointStruct(
                    id=self._generate_point_id(f"{message_id}_img_semantic"),
                    vector={"text": semantic_embedding},  # Named vector for text
                    payload={
                        "type": "image_semantic",
                        "image_url": image_url,
                        "caption": caption,
                        **metadata.model_dump(),
                    }
                ),
            ]
            
            # Upsert to Qdrant
            self.qdrant.upsert(
                collection_name=collection_name,
                points=points,
            )
            
            logger.info(
                "image_indexed",
                channel_id=metadata.channel_id,
                image_url=image_url,
                caption_length=len(caption),
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "image_indexing_failed",
                image_url=image_url,
                error=str(e),
                exc_info=True,
            )
            return False
    
    async def generate_caption(self, image_url: str) -> str:
        """
        Generate caption for image using vision LLM.
        
        Args:
            image_url: URL or path to image
        
        Returns:
            Image caption
        """
        try:
            # Check if vision model is available
            if not hasattr(self.llm_client, 'model') or 'vision' not in str(self.llm_client.model).lower():
                logger.warning(
                    "vision_model_not_configured",
                    current_model=getattr(self.llm_client, 'model', 'unknown'),
                    message="Skipping caption generation - model doesn't support vision. Configure llm.vision_model in config.yaml"
                )
                return "Image attachment"
            
            # Multimodal message with image
            response = await self.llm_client.chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this image concisely in 1-2 sentences. Focus on what's shown, not speculation."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],
                system_prompt="You are an expert at describing images accurately and concisely.",
                max_tokens=150,
                temperature=0.3,
            )
            
            caption = response.content.strip()
            
            logger.debug(
                "caption_generated",
                image_url=image_url,
                caption_length=len(caption),
            )
            
            return caption
            
        except httpx.HTTPStatusError as e:
            # Handle 412 and other HTTP errors gracefully
            if e.response.status_code == 412:
                logger.warning(
                    "vision_not_supported",
                    model=getattr(self.llm_client, 'model', 'unknown'),
                    message="Model doesn't support vision. Configure llm.vision_model in config.yaml with a vision-capable model (e.g., google/gemini-flash-1.5, openai/gpt-4-vision-preview)"
                )
            else:
                logger.warning(
                    "caption_generation_failed",
                    image_url=image_url[:100],
                    error=f"HTTP {e.response.status_code}",
                )
            return "Image attachment"
            
        except Exception as e:
            logger.warning(
                "caption_generation_failed",
                image_url=image_url[:100],
                error=str(e)[:200],
            )
            return "Image attachment"
    
    async def _download_image(
        self,
        image_url: str,
    ) -> Image.Image:
        """
        Download image from URL or load from path.
        
        Args:
            image_url: URL or file path
        
        Returns:
            PIL Image
        """
        # Check if local path
        if Path(image_url).exists():
            return Image.open(image_url).convert("RGB")
        
        # Download from URL
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()
            
            image_data = io.BytesIO(response.content)
            return Image.open(image_data).convert("RGB")
    
    def _generate_point_id(self, identifier: str) -> int:
        """
        Generate numeric point ID from string identifier.
        
        Args:
            identifier: String identifier
        
        Returns:
            Numeric ID (64-bit integer)
        """
        # Hash to 64-bit integer
        hash_bytes = hashlib.sha256(identifier.encode()).digest()
        return int.from_bytes(hash_bytes[:8], byteorder='big')
    
    def _extract_url_from_markdown(self, content: str) -> Optional[str]:
        """
        Extract URL from markdown file.
        Looks for **URL:** pattern in first few lines.
        """
        lines = content.split('\n')[:10]  # Check first 10 lines
        for line in lines:
            if line.strip().startswith('**URL:**'):
                # Extract URL after **URL:**
                url = line.split('**URL:**', 1)[1].strip()
                return url
        return None
    
    async def index_document(
        self,
        file_path: Union[str, Path],
        channel_id: str,
        channel_name: str,
    ) -> Dict[str, int]:
        """
        Index document from file (markdown, text).
        
        Args:
            file_path: Path to document
            channel_id: Channel ID for collection
            channel_name: Channel name for metadata
        
        Returns:
            Dict with indexing stats
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error("file_not_found", file_path=str(file_path))
            return {"chunks": 0, "images": 0}
        
        # Read content
        content = file_path.read_text(encoding="utf-8")
        
        # Extract URL from content
        doc_url = self._extract_url_from_markdown(content)
        
        # Create metadata
        metadata = DocumentMetadata(
            message_id=file_path.stem,
            channel_id=channel_id,
            channel_name=channel_name,
            timestamp=str(file_path.stat().st_mtime),
            title=file_path.stem.replace("_", " "),
            source=str(file_path),
            url=doc_url,
        )
        
        # Index text
        chunks_indexed = await self.index_text(content, metadata)
        
        logger.info(
            "document_indexed",
            file_path=str(file_path),
            chunks=chunks_indexed,
        )
        
        return {
            "chunks": chunks_indexed,
            "images": 0,
        }
